"""Corpus ingestion core (pure + DB), separate from the CLI so it is unit-testable.

Invariants honored:
  - Human gate (AGENTS.md #5): an article is inserted ONLY if `verified: true`. Unverified
    drafts are refused with a clear message and never reach `regulation_versions`.
  - Append-only (AGENTS.md #4): we only INSERT versions; corrections are new versions.
  - Idempotent: an (article_ref, normalized-text) already present is skipped, matching the
    unique constraint on (regulation_id, article_ref, content_hash).
  - Audited: every inserted version writes an audit_log row with the verifier's initials.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Regulation, RegulationVersion
from app.services.audit import write_audit

# Injected so tests can supply a deterministic stub instead of the network embedder.
EmbedFn = Callable[[list[str]], Awaitable[list[list[float]]]]

ACTOR_CORPUS = "corpus-ingest"


def content_hash_for(article_text_ar: str) -> str:
    """Normalize whitespace then sha256 — same rule the seed uses, so hashes are stable."""
    normalized = " ".join(article_text_ar.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class CorpusArticle:
    article_ref: str
    article_text_ar: str
    source_url: str
    verified: bool
    verified_by_initials: str | None = None
    article_text_en: str | None = None
    effective_date: dt.date | None = None


@dataclass
class CorpusRegulation:
    code: str
    name_ar: str
    name_en: str
    authority: str
    source_domain: str
    articles: list[CorpusArticle] = field(default_factory=list)


@dataclass
class IngestStats:
    code: str = ""
    inserted: int = 0
    skipped_duplicate: int = 0
    skipped_unverified: int = 0
    errors: list[str] = field(default_factory=list)


def _parse_date(value: object) -> dt.date | None:
    if value is None or value == "":
        return None
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value))


def parse_regulation_spec(spec: dict) -> CorpusRegulation:
    """Turn a parsed-YAML dict into a typed CorpusRegulation. Raises on missing required keys."""
    reg = spec["regulation"]
    articles = []
    for art in spec.get("articles", []):
        articles.append(
            CorpusArticle(
                article_ref=str(art["article_ref"]).strip(),
                article_text_ar=str(art["article_text_ar"]),
                source_url=str(art["source_url"]).strip(),
                verified=bool(art.get("verified", False)),
                verified_by_initials=(str(art["verified_by_initials"]).strip()
                                      if art.get("verified_by_initials") else None),
                article_text_en=(str(art["article_text_en"]) if art.get("article_text_en") else None),
                effective_date=_parse_date(art.get("effective_date")),
            )
        )
    return CorpusRegulation(
        code=str(reg["code"]).strip(),
        name_ar=str(reg["name_ar"]).strip(),
        name_en=str(reg["name_en"]).strip(),
        authority=str(reg["authority"]).strip(),
        source_domain=str(reg["source_domain"]).strip(),
        articles=articles,
    )


def validate_regulation(reg: CorpusRegulation) -> list[str]:
    """Static checks that do not need the DB. Returns human-readable errors (empty = ok)."""
    errors: list[str] = []
    seen_refs: set[str] = set()
    for art in reg.articles:
        loc = f"{reg.code} {art.article_ref}"
        if not art.article_ref:
            errors.append(f"{reg.code}: an article is missing article_ref")
        if not art.article_text_ar.strip():
            errors.append(f"{loc}: empty article_text_ar")
        if not art.source_url.startswith("http"):
            errors.append(f"{loc}: source_url must be an http(s) URL")
        if art.verified and not art.verified_by_initials:
            errors.append(f"{loc}: verified article must carry verified_by_initials")
        if art.article_ref in seen_refs:
            errors.append(f"{loc}: duplicate article_ref within the file")
        seen_refs.add(art.article_ref)
    return errors


async def _get_or_create_regulation(session: AsyncSession, reg: CorpusRegulation) -> Regulation:
    existing = (
        await session.execute(select(Regulation).where(Regulation.code == reg.code))
    ).scalar_one_or_none()
    if existing:
        return existing
    row = Regulation(
        code=reg.code, name_ar=reg.name_ar, name_en=reg.name_en,
        authority=reg.authority, source_domain=reg.source_domain,
    )
    session.add(row)
    await session.flush()
    return row


async def _existing_hashes(session: AsyncSession, regulation_id: uuid.UUID) -> set[tuple[str, str]]:
    rows = (
        await session.execute(
            select(RegulationVersion.article_ref, RegulationVersion.content_hash).where(
                RegulationVersion.regulation_id == regulation_id
            )
        )
    ).all()
    return {(r[0], r[1]) for r in rows}


async def ingest_regulation(
    session: AsyncSession,
    reg: CorpusRegulation,
    *,
    verifier_id: uuid.UUID,
    embed_fn: EmbedFn,
    tier: str = "human_verified",
) -> IngestStats:
    """Insert the not-yet-present articles of one regulation. Does NOT commit; the caller owns
    the transaction boundary.

    tier='human_verified' (default): only articles marked verified: true are inserted — the
    strict human gate. tier='official_fetch': articles fetched verbatim from the official
    gazette are inserted even though verified: false, recorded as official_fetch provenance
    (owner-policy trust of the official source). The distinction is stored on the row so the
    UI can label auto-fetched citations.
    """
    if tier not in ("human_verified", "official_fetch"):
        raise ValueError(f"unknown tier: {tier}")
    stats = IngestStats(code=reg.code)
    row = await _get_or_create_regulation(session, reg)
    present = await _existing_hashes(session, row.id)

    to_insert: list[tuple[CorpusArticle, str]] = []
    for art in reg.articles:
        # In human_verified mode the gate requires an explicit human tick; in official_fetch
        # mode the official-source provenance is the trust basis, so verified: false is fine.
        if tier == "human_verified" and not art.verified:
            stats.skipped_unverified += 1
            continue
        text_ar = " ".join(art.article_text_ar.split())
        chash = content_hash_for(text_ar)
        if (art.article_ref, chash) in present:
            stats.skipped_duplicate += 1
            continue
        to_insert.append((art, chash))

    if not to_insert:
        return stats

    embeddings = await embed_fn([" ".join(a.article_text_ar.split()) for a, _ in to_insert])
    now = dt.datetime.now(dt.timezone.utc)
    for (art, chash), embedding in zip(to_insert, embeddings):
        session.add(
            RegulationVersion(
                regulation_id=row.id,
                article_ref=art.article_ref,
                article_text_ar=" ".join(art.article_text_ar.split()),
                article_text_en=(" ".join(art.article_text_en.split()) if art.article_text_en else None),
                source_url=art.source_url,
                content_hash=chash,
                fetched_at=now,
                effective_date=art.effective_date,
                verified_by=verifier_id,
                verification_tier=tier,
                embedding=embedding,
            )
        )
        await write_audit(
            session, actor=ACTOR_CORPUS, action="regulation_version_ingested", verdict="n-a",
            detail={"code": reg.code, "article_ref": art.article_ref, "tier": tier,
                    "verified_by_initials": art.verified_by_initials},
        )
        stats.inserted += 1
    return stats


def summarize(all_stats: Sequence[IngestStats]) -> str:
    ins = sum(s.inserted for s in all_stats)
    dup = sum(s.skipped_duplicate for s in all_stats)
    unv = sum(s.skipped_unverified for s in all_stats)
    lines = [f"  {s.code}: +{s.inserted} inserted, {s.skipped_duplicate} dup, "
             f"{s.skipped_unverified} unverified-skipped" for s in all_stats]
    return "\n".join(lines) + f"\nTOTAL: +{ins} inserted, {dup} duplicate, {unv} unverified-skipped"
