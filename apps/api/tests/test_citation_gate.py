"""Zero Unsourced Findings (AGENTS.md #1): a finding cannot exist without a resolvable
citation. Enforced at BOTH the DB (NOT NULL FK) and the application gate."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import SanadError
from app.models import AuditLog, Contract, Finding, RegulationVersion
from app.services.citations import create_finding_guarded


async def test_db_rejects_finding_without_citation(session: AsyncSession, contract: Contract) -> None:
    session.add(
        Finding(
            contract_id=contract.id,
            regulation_version_id=None,  # violates NOT NULL
            title_ar="بدون مصدر",
            severity="high",
            category="regulatory",
        )
    )
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_gate_rejects_unresolvable_citation(session: AsyncSession, contract: Contract) -> None:
    with pytest.raises(SanadError) as exc:
        await create_finding_guarded(
            session,
            contract_id=contract.id,
            clause_id=None,
            regulation_version_id=uuid.uuid4(),  # does not exist in the cache
            title_ar="مصدر غير موجود",
            title_en=None,
            explanation_ar=None,
            explanation_en=None,
            severity="high",
            category="regulatory",
            actor="analysis",
        )
    assert exc.value.code == "citation_required"

    # The rejection is audited as an incident.
    audits = (
        await session.execute(select(AuditLog).where(AuditLog.action == "citation_rejected"))
    ).scalars().all()
    assert any(a.target == str(contract.id) for a in audits)


async def test_gate_accepts_resolvable_citation(
    session: AsyncSession, contract: Contract, regulation_version: RegulationVersion
) -> None:
    finding = await create_finding_guarded(
        session,
        contract_id=contract.id,
        clause_id=None,
        regulation_version_id=regulation_version.id,
        title_ar="تعارض مع المادة",
        title_en="Conflict",
        explanation_ar="شرح",
        explanation_en="explanation",
        severity="critical",
        category="regulatory",
        actor="analysis",
    )
    assert finding.regulation_version_id == regulation_version.id
    assert finding.review_status == "pending"
