"""Quarantined third-party corpus (Kaggle etc.): stored + searchable, but NEVER citable.

A finding can only cite official_fetch / human_verified text. Third-party imports carry the
unverified_third_party tier and are rejected by the citation gate until a human verifies them.
"""
from __future__ import annotations

import datetime as dt
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import SanadError
from app.models import AuditLog, Contract, Regulation, RegulationVersion, User
from app.services.citations import create_finding_guarded
from app.services.corpus.tiers import CITABLE_TIERS, UNVERIFIED_THIRD_PARTY


def test_third_party_is_not_citable():
    assert UNVERIFIED_THIRD_PARTY not in CITABLE_TIERS
    assert set(CITABLE_TIERS) == {"official_fetch", "human_verified"}


async def _third_party_version(session: AsyncSession, user: User) -> RegulationVersion:
    reg = Regulation(code=f"KAG-{uuid.uuid4().hex[:6]}", name_ar="مصدر خارجي", name_en="Third party",
                     authority="Kaggle", source_domain="kaggle.com")
    session.add(reg)
    await session.flush()
    rv = RegulationVersion(
        regulation_id=reg.id, article_ref="Article 1", article_text_ar="نص من مصدر غير موثّق.",
        source_url="https://kaggle.com/datasets/x", content_hash=uuid.uuid4().hex,
        fetched_at=dt.datetime.now(dt.timezone.utc), verified_by=user.id,
        verification_tier=UNVERIFIED_THIRD_PARTY,
    )
    session.add(rv)
    await session.flush()
    return rv


@pytest.mark.asyncio
async def test_gate_rejects_citation_of_quarantined_tier(
    session: AsyncSession, contract: Contract, user: User
) -> None:
    rv = await _third_party_version(session, user)
    with pytest.raises(SanadError) as exc:
        await create_finding_guarded(
            session, contract_id=contract.id, clause_id=None,
            regulation_version_id=rv.id,  # resolves, but tier is not citable
            title_ar="محاولة الاستشهاد بمصدر خارجي", title_en=None,
            explanation_ar=None, explanation_en=None,
            severity="high", category="regulatory", actor="analysis",
        )
    assert exc.value.code == "citation_required"

    audits = (
        await session.execute(select(AuditLog).where(AuditLog.action == "citation_rejected"))
    ).scalars().all()
    assert any((a.detail_json or {}).get("reason") == "uncitable_tier" for a in audits)
