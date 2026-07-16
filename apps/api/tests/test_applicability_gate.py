"""Applicability human gate: LLM produces llm_draft; only human review makes it actionable."""
from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RegulationApplicability, RegulationVersion
from app.services.applicability.classify import classify_article


@pytest.mark.asyncio
async def test_classify_creates_llm_draft_not_actionable(
    session: AsyncSession, regulation_version: RegulationVersion
) -> None:
    a = await classify_article(session, regulation_version.id)
    assert a.classification_confidence == "llm_draft"
    assert a.applicability_type in ("retroactive_with_deadline", "prospective_only", "grandfathered")
    assert a.reviewed_by is None
    # self-cited the scope article by default
    assert a.classification_citation_version_id == regulation_version.id


@pytest.mark.asyncio
async def test_review_requires_valid_citation_and_promotes(
    api_client: AsyncClient, session: AsyncSession, auth_headers: dict[str, str],
    regulation_version: RegulationVersion,
) -> None:
    a = await classify_article(session, regulation_version.id)
    await session.commit()

    # bogus citation is rejected (Zero Unsourced: the classification must be sourced)
    import uuid
    bad = await api_client.post(
        f"/api/v1/applicability/{a.id}/review", headers=auth_headers,
        json={"applicability_type": "prospective_only", "effective_date": "2026-01-01",
              "classification_citation_version_id": str(uuid.uuid4())},
    )
    assert bad.status_code == 422 or bad.json().get("error", {}).get("code") == "validation_failed"

    ok = await api_client.post(
        f"/api/v1/applicability/{a.id}/review", headers=auth_headers,
        json={"applicability_type": "retroactive_with_deadline", "effective_date": "2026-01-01",
              "deadline_date": "2026-06-30",
              "classification_citation_version_id": str(regulation_version.id)},
    )
    assert ok.status_code == 200, ok.text

    await session.refresh(a)
    assert a.classification_confidence == "human_reviewed"
    assert a.reviewed_by is not None
    assert a.applicability_type == "retroactive_with_deadline"
    assert a.deadline_date == dt.date(2026, 6, 30)


@pytest.mark.asyncio
async def test_review_queue_lists_only_drafts(
    api_client: AsyncClient, session: AsyncSession, auth_headers: dict[str, str],
    regulation_version: RegulationVersion,
) -> None:
    await classify_article(session, regulation_version.id)
    await session.commit()
    resp = await api_client.get("/api/v1/applicability/review-queue", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    assert any(str(i["source_article"]["regulation_version_id"]) == str(regulation_version.id)
               and i["classification_confidence"] == "llm_draft" for i in items)
