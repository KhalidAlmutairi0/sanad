"""Corpus ingestion: human gate (unverified refused), idempotency, verified_by set."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from app.models import RegulationVersion, User
from app.services.corpus import (
    CorpusArticle,
    CorpusRegulation,
    ingest_regulation,
    validate_regulation,
)


async def _stub_embed(texts: list[str]) -> list[list[float]]:
    # Deterministic 1024-dim vectors; no network.
    return [[0.01] * 1024 for _ in texts]


def _reg() -> CorpusRegulation:
    return CorpusRegulation(
        code=f"TESTREG-{uuid.uuid4().hex[:6]}",
        name_ar="نظام تجريبي",
        name_en="Test Regulation",
        authority="SDAIA",
        source_domain="sdaia.gov.sa",
        articles=[
            CorpusArticle(
                article_ref="Article 1",
                article_text_ar="نص المادة الأولى الموثّقة.",
                source_url="https://laws.boe.gov.sa/x1",
                verified=True,
                verified_by_initials="KA",
            ),
            CorpusArticle(
                article_ref="Article 2",
                article_text_ar="مسودة غير موثّقة.",
                source_url="https://laws.boe.gov.sa/x2",
                verified=False,
            ),
        ],
    )


async def _verifier(session) -> User:
    u = User(email=f"v-{uuid.uuid4()}@sanad.local", display_name="V", role="admin", password_hash="x")
    session.add(u)
    await session.flush()
    return u


@pytest.mark.asyncio
async def test_unverified_article_is_refused(session) -> None:
    reg = _reg()
    verifier = await _verifier(session)
    stats = await ingest_regulation(session, reg, verifier_id=verifier.id, embed_fn=_stub_embed)
    assert stats.inserted == 1  # only Article 1 (verified)
    assert stats.skipped_unverified == 1  # Article 2 refused

    inserted = [r for r in (await session.execute(select(RegulationVersion))).scalars()
                if r.verified_by == verifier.id]
    assert len(inserted) == 1
    assert inserted[0].article_ref == "Article 1"
    assert inserted[0].verified_by == verifier.id


@pytest.mark.asyncio
async def test_ingest_is_idempotent(session) -> None:
    reg = _reg()
    verifier = await _verifier(session)
    before = (await session.execute(select(func.count()).select_from(RegulationVersion))).scalar_one()

    s1 = await ingest_regulation(session, reg, verifier_id=verifier.id, embed_fn=_stub_embed)
    s2 = await ingest_regulation(session, reg, verifier_id=verifier.id, embed_fn=_stub_embed)
    after = (await session.execute(select(func.count()).select_from(RegulationVersion))).scalar_one()

    assert s1.inserted == 1
    assert s2.inserted == 0 and s2.skipped_duplicate == 1
    assert after - before == 1  # second run inserted nothing


def test_validate_flags_verified_without_initials() -> None:
    reg = _reg()
    reg.articles[0].verified_by_initials = None
    errors = validate_regulation(reg)
    assert any("verified_by_initials" in e for e in errors)
