"""Two-stage monitoring token gate (spec #5).

run-check must be free (no monitoring_events, no LLM) and only persist raw diffs;
promote-candidate is the token-spending step that creates the event. The browser fetch is
monkeypatched to inject canned live article maps, so no Chromium is needed.
"""
from __future__ import annotations

import datetime as dt
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MonitoringDiff, MonitoringEvent, Regulation, RegulationVersion, User
from app.services.monitoring import detection


async def _seed_reg(session: AsyncSession, code: str, verified_by: uuid.UUID) -> Regulation:
    reg = Regulation(code=code, name_ar="نظام", name_en="Law", authority="SAMA",
                     source_domain="laws.boe.gov.sa")
    session.add(reg)
    await session.flush()
    session.add(RegulationVersion(
        regulation_id=reg.id, article_ref="Article 1", article_text_ar="النص الأصلي.",
        source_url="https://laws.boe.gov.sa/x", content_hash=uuid.uuid4().hex,
        fetched_at=dt.datetime.now(dt.timezone.utc), verified_by=verified_by,
    ))
    await session.flush()
    return reg


@pytest.mark.asyncio
async def test_run_check_is_free_and_only_persists_diffs(
    api_client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict[str, str], monkeypatch
) -> None:
    reg = await _seed_reg(session, f"PDPL-{uuid.uuid4().hex[:6]}", user.id)
    headers = auth_headers  # seeded reviewer

    # One source that exists in the DB; inject a changed live article map (Article 1 amended).
    monkeypatch.setattr(detection, "load_sources",
                        lambda: [{"code": reg.code, "url": "https://laws.boe.gov.sa/x",
                                  "corpus_file": "x.yaml"}])
    monkeypatch.setattr(detection, "fetch_live_articles",
                        lambda sources: {reg.code: {"Article 1": "النص بعد التعديل الجديد."}})

    before_events = (await session.execute(select(func.count()).select_from(MonitoringEvent))).scalar_one()

    resp = await api_client.post("/api/v1/monitoring/run-check", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"] if "data" in resp.json() else resp.json()
    assert body["total_changes"] == 1

    # A diff was persisted, and NO monitoring_event was created (free stage).
    diffs = (await session.execute(select(MonitoringDiff).where(MonitoringDiff.status == "pending_review"))).scalars().all()
    assert len(diffs) == 1 and diffs[0].change_type == "amended"
    after_events = (await session.execute(select(func.count()).select_from(MonitoringEvent))).scalar_one()
    assert after_events == before_events

    # Staleness timestamp updated by the check.
    await session.refresh(reg)
    assert reg.last_reconciled_at is not None


@pytest.mark.asyncio
async def test_promote_candidate_creates_event_and_marks_diff(
    api_client: AsyncClient, session: AsyncSession, user: User, auth_headers: dict[str, str]
) -> None:
    reg = await _seed_reg(session, f"PDPL-{uuid.uuid4().hex[:6]}", user.id)
    headers = auth_headers  # seeded reviewer
    diff = MonitoringDiff(regulation_id=reg.id, article_ref="Article 9", change_type="new_article",
                          live_text="مادة جديدة.", source_url="https://laws.boe.gov.sa/x",
                          status="pending_review")
    session.add(diff)
    await session.flush()

    resp = await api_client.post("/api/v1/monitoring/promote-candidate",
                                 headers=headers, json={"diff_id": str(diff.id)})
    assert resp.status_code == 201, resp.text

    events = (await session.execute(select(MonitoringEvent).where(MonitoringEvent.regulation_id == reg.id))).scalars().all()
    assert len(events) == 1 and events[0].status == "detected"
    await session.refresh(diff)
    assert diff.status == "promoted"


@pytest.mark.asyncio
async def test_run_check_requires_reviewer_role(
    api_client: AsyncClient, sharia_headers: dict[str, str]
) -> None:
    resp = await api_client.post("/api/v1/monitoring/run-check", headers=sharia_headers)
    assert resp.status_code in (401, 403), resp.text
