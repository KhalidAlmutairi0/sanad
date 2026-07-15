"""Regulatory monitoring feed + the human verification gate. Verifying a detected change
appends a new, immutable regulation_versions row (verified_by = the human caller)."""
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session, require_roles
from app.core.errors import SanadError
from app.models import MonitoringDiff, MonitoringEvent, Regulation, RegulationVersion, User
from app.services.monitoring import detection
from app.services.monitoring.obligations import (
    flag_pending_reverification,
    resolve_pending_reverification,
)
from app.services.audit import write_audit
from app.services.llm import LLMRequest, get_llm
from app.services.retrieval import embed_texts

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class EventItem(BaseModel):
    id: uuid.UUID
    regulation_code: str
    change_type: str | None
    detected_at: dt.datetime
    impact_summary_ar: str | None
    status: str
    new_version_id: uuid.UUID | None


class EventList(BaseModel):
    items: list[EventItem]


class VersionPayload(BaseModel):
    article_ref: str
    article_text_ar: str
    article_text_en: str | None = None
    source_url: str
    effective_date: dt.date | None = None


class VerifyRequest(BaseModel):
    regulation_version: VersionPayload


class VerifyResponse(BaseModel):
    regulation_version_id: uuid.UUID
    status: str


@router.get("/events", response_model=EventList)
async def list_events(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> EventList:
    rows = (
        await session.execute(
            select(MonitoringEvent, Regulation.code)
            .join(Regulation, Regulation.id == MonitoringEvent.regulation_id)
            .order_by(MonitoringEvent.detected_at.desc())
        )
    ).all()
    return EventList(
        items=[
            EventItem(
                id=e.id, regulation_code=code, change_type=e.change_type,
                detected_at=e.detected_at, impact_summary_ar=e.impact_summary_ar,
                status=e.status, new_version_id=e.new_version_id,
            )
            for e, code in rows
        ]
    )


@router.post("/events/{event_id}/verify", response_model=VerifyResponse, status_code=201)
async def verify_event(
    event_id: uuid.UUID,
    body: VerifyRequest,
    user: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> VerifyResponse:
    event = await session.get(MonitoringEvent, event_id)
    if not event:
        raise SanadError("not_found")
    if event.status == "verified":
        raise SanadError("review_conflict")

    p = body.regulation_version
    text_ar = " ".join(p.article_text_ar.split())
    content_hash = hashlib.sha256(text_ar.encode("utf-8")).hexdigest()
    [embedding] = await embed_texts([text_ar], input_type="passage")

    version = RegulationVersion(
        regulation_id=event.regulation_id,
        article_ref=p.article_ref,
        article_text_ar=text_ar,
        article_text_en=p.article_text_en,
        source_url=p.source_url,
        content_hash=content_hash,
        fetched_at=dt.datetime.now(dt.timezone.utc),
        effective_date=p.effective_date,
        verified_by=user.id,  # the human gate
        embedding=embedding,
    )
    session.add(version)
    await session.flush()

    event.new_version_id = version.id
    event.status = "verified"

    # spec #6: release the reverification hold on obligations for this article (restore prior
    # status; never auto-advance to met/open).
    released = await resolve_pending_reverification(session, event.regulation_id, p.article_ref)

    await write_audit(
        session, actor=str(user.id), action="regulation_version_verified",
        target=str(version.id), verdict="allowed",
        detail={"event_id": str(event_id), "article_ref": p.article_ref,
                "obligations_released": released},
    )
    await session.commit()
    return VerifyResponse(regulation_version_id=version.id, status="verified")


# ── Two-stage token gate (spec #5) ──────────────────────────────────────────────────────────
# run-check: pure fetch + diff, ZERO tokens. promote-candidate: the LLM step that costs tokens.

class DiffItem(BaseModel):
    id: uuid.UUID
    regulation_code: str
    article_ref: str
    change_type: str
    live_text: str
    source_url: str
    status: str


class DiffList(BaseModel):
    items: list[DiffItem]


class RunCheckSource(BaseModel):
    code: str
    changes: int
    error: str | None = None


class RunCheckResponse(BaseModel):
    sources_checked: int
    changed_sources: int
    total_changes: int
    sources: list[RunCheckSource]


class PromoteRequest(BaseModel):
    diff_id: uuid.UUID


async def _committed_text_by_ref(session: AsyncSession, regulation_id: uuid.UUID) -> dict[str, str]:
    """Latest committed article text per article_ref for a regulation (the cited text)."""
    rows = (
        await session.execute(
            select(RegulationVersion.article_ref, RegulationVersion.article_text_ar,
                   RegulationVersion.fetched_at)
            .where(RegulationVersion.regulation_id == regulation_id)
            .order_by(RegulationVersion.fetched_at.asc())
        )
    ).all()
    # Ascending order means the last write per ref wins -> the most recent version.
    return {ref: text for ref, text, _ in rows}


@router.get("/diffs", response_model=DiffList)
async def list_diffs(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DiffList:
    """Unprocessed diffs awaiting a promote decision — the pending state, distinct from the
    monitoring_events feed."""
    rows = (
        await session.execute(
            select(MonitoringDiff, Regulation.code)
            .join(Regulation, Regulation.id == MonitoringDiff.regulation_id)
            .where(MonitoringDiff.status == "pending_review")
            .order_by(MonitoringDiff.created_at.desc())
        )
    ).all()
    return DiffList(
        items=[
            DiffItem(id=d.id, regulation_code=code, article_ref=d.article_ref,
                     change_type=d.change_type, live_text=d.live_text, source_url=d.source_url,
                     status=d.status)
            for d, code in rows
        ]
    )


@router.post("/run-check", response_model=RunCheckResponse)
async def run_check(
    user: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> RunCheckResponse:
    """FREE stage: fetch every tracked source (headless Chromium) and diff against the committed
    corpus by pure text comparison. Zero LLM, zero tokens. Persists raw diffs as pending_review;
    never creates a monitoring_event and never calls the research agent."""
    sources = detection.load_sources()
    regs = {
        r.code: r
        for r in (await session.execute(select(Regulation))).scalars().all()
    }
    # Browser fetch is blocking (playwright sync API) — run it off the event loop.
    live_by_code = await asyncio.to_thread(detection.fetch_live_articles, sources)

    summaries: list[RunCheckSource] = []
    total_changes = 0
    changed_sources = 0
    for src in sources:
        code = src["code"]
        reg = regs.get(code)
        if reg is None:
            summaries.append(RunCheckSource(code=code, changes=0, error="not_ingested"))
            continue
        live = live_by_code.get(code)
        if live is None:
            summaries.append(RunCheckSource(code=code, changes=0, error="fetch_failed"))
            continue

        # A check ran against the source (staleness tracking, spec #5/#7) even if unchanged.
        reg.last_reconciled_at = dt.datetime.now(dt.timezone.utc)

        committed = await _committed_text_by_ref(session, reg.id)
        changes = detection.build_changes(committed, live)

        # Idempotent per run: clear this regulation's prior pending diffs, re-insert current ones.
        existing = (
            await session.execute(
                select(MonitoringDiff).where(
                    MonitoringDiff.regulation_id == reg.id,
                    MonitoringDiff.status == "pending_review",
                )
            )
        ).scalars().all()
        for stale in existing:
            await session.delete(stale)
        for ch in changes:
            session.add(MonitoringDiff(
                regulation_id=reg.id, article_ref=ch["article_ref"], change_type=ch["change_type"],
                live_text=ch["text"], source_url=src["url"], status="pending_review",
            ))
        if changes:
            changed_sources += 1
            total_changes += len(changes)
        summaries.append(RunCheckSource(code=code, changes=len(changes)))

    await write_audit(
        session, actor=str(user.id), action="monitoring_check_run", target="corpus",
        verdict="n-a",
        detail={"sources": len(sources), "changed_sources": changed_sources,
                "total_changes": total_changes, "tokens": 0},
    )
    await session.commit()
    return RunCheckResponse(
        sources_checked=len(sources), changed_sources=changed_sources,
        total_changes=total_changes, sources=summaries,
    )


_IMPACT_SYSTEM = (
    "You are a Saudi regulatory analyst. Given one changed regulation article, write a concise "
    "Arabic impact summary (<=40 words) describing what changed and which obligations it may "
    "affect. Output ONLY the Arabic summary text, no preamble."
)


@router.post("/promote-candidate", response_model=EventItem, status_code=201)
async def promote_candidate(
    body: PromoteRequest,
    user: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> EventItem:
    """TOKEN-SPENDING stage: the reviewer promotes one reviewed diff into a monitoring_event.
    THIS invokes the LLM (research agent) to produce the impact summary — the only step here
    that costs tokens. Never writes regulation_versions (that still needs the verify gate)."""
    diff = await session.get(MonitoringDiff, body.diff_id)
    if diff is None or diff.status != "pending_review":
        raise SanadError("not_found")

    reg = await session.get(Regulation, diff.regulation_id)
    req = LLMRequest(
        system_prompt=_IMPACT_SYSTEM,
        instruction=(
            f"Regulation: {reg.code if reg else ''} — article {diff.article_ref}\n"
            f"Change type: {diff.change_type}"
        ),
        untrusted_blocks=[],
        offline_stub=f"تحديث ({diff.change_type}) على {reg.code if reg else ''} {diff.article_ref}.",
        max_tokens=200,
    )
    impact = (await get_llm().complete(req)).strip() or None

    event = MonitoringEvent(
        regulation_id=diff.regulation_id, change_type=diff.change_type,
        impact_summary_ar=impact, status="detected",
    )
    session.add(event)
    diff.status = "promoted"
    await session.flush()

    # spec #6: obligations citing this article must not keep looking current during the gap.
    held = await flag_pending_reverification(session, diff.regulation_id, diff.article_ref)

    # Attributable token-spend record for this feature (the counter, spec #5).
    await write_audit(
        session, actor=str(user.id), action="monitoring_promote", target=str(event.id),
        verdict="allowed",
        detail={"diff_id": str(diff.id), "regulation_code": reg.code if reg else None,
                "article_ref": diff.article_ref, "change_type": diff.change_type,
                "obligations_held": held},
    )
    await session.commit()
    return EventItem(
        id=event.id, regulation_code=reg.code if reg else "", change_type=event.change_type,
        detected_at=event.detected_at, impact_summary_ar=event.impact_summary_ar,
        status=event.status, new_version_id=event.new_version_id,
    )
