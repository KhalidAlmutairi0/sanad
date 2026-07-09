"""INV-08: the research agent can NEVER write regulation_versions directly. Its candidate
submission only queues a monitoring_events row; entry into the evidence cache requires the
human verify gate (verified_by set by a person)."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import MonitoringEvent, Regulation, RegulationVersion


async def test_agent_candidate_does_not_write_evidence_cache(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    token = get_settings().internal_service_token
    if not token:
        pytest.skip("INTERNAL_SERVICE_TOKEN not configured in this environment")

    reg = Regulation(
        code=f"PDPL-{uuid.uuid4().hex[:6]}",
        name_ar="نظام", name_en="Law", authority="SDAIA", source_domain="sdaia.gov.sa",
    )
    session.add(reg)
    await session.flush()

    before_versions = (
        await session.execute(select(func.count()).select_from(RegulationVersion))
    ).scalar_one()
    before_events = (
        await session.execute(select(func.count()).select_from(MonitoringEvent))
    ).scalar_one()

    resp = await api_client.post(
        "/api/v1/internal/agent-candidate",
        headers={"x-internal-token": token},
        json={
            "regulation_code": reg.code,
            "article_ref": "Article 99",
            "article_text_ar": "نص مُقترح من الوكيل لم يُتحقق منه بعد.",
            "source_url": "https://sdaia.gov.sa/x",
            "change_type": "amended",
        },
    )
    assert resp.status_code == 202, resp.text

    after_versions = (
        await session.execute(select(func.count()).select_from(RegulationVersion))
    ).scalar_one()
    after_events = (
        await session.execute(select(func.count()).select_from(MonitoringEvent))
    ).scalar_one()

    # The cache is untouched; only a verification-queue event was created.
    assert after_versions == before_versions
    assert after_events == before_events + 1


async def test_agent_candidate_requires_internal_token(api_client: AsyncClient) -> None:
    resp = await api_client.post(
        "/api/v1/internal/agent-candidate",
        json={
            "regulation_code": "PDPL", "article_ref": "Article 1",
            "article_text_ar": "x", "source_url": "https://sdaia.gov.sa/x",
            "change_type": "amended",
        },
    )
    assert resp.status_code == 403
