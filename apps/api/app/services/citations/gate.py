"""The citation gate. Every finding is created through create_finding_guarded()."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import SanadError
from app.models import Finding, RegulationVersion
from app.services.audit import write_audit
from app.services.corpus.tiers import CITABLE_TIERS


async def resolve_citation(
    session: AsyncSession, regulation_version_id: uuid.UUID | None
) -> RegulationVersion | None:
    """Return the cited version if it resolves in the evidence cache, else None."""
    if regulation_version_id is None:
        return None
    return await session.get(RegulationVersion, regulation_version_id)


async def create_finding_guarded(
    session: AsyncSession,
    *,
    contract_id: uuid.UUID,
    clause_id: uuid.UUID | None,
    regulation_version_id: uuid.UUID | None,
    title_ar: str,
    title_en: str | None,
    explanation_ar: str | None,
    explanation_en: str | None,
    severity: str,
    category: str,
    violation_cost_ar: str | None = None,
    violation_cost_min: float | None = None,
    violation_cost_max: float | None = None,
    confidence_tier: str = "high",
    match_score: float | None = None,
    match_margin: float | None = None,
    actor: str,
) -> Finding:
    """Insert a finding ONLY if its citation resolves. Otherwise audit citation_rejected
    and raise — this must never happen in normal flow (it means an unsourced claim was
    attempted, treated as an incident)."""
    version = await resolve_citation(session, regulation_version_id)
    if version is None:
        await write_audit(
            session, actor=actor, action="citation_rejected",
            target=str(contract_id), verdict="denied",
            detail={
                "reason": "citation_required",
                "clause_id": str(clause_id) if clause_id else None,
                "attempted_version_id": str(regulation_version_id) if regulation_version_id else None,
            },
        )
        await session.flush()
        raise SanadError("citation_required")

    # Backstop: quarantined third-party text (e.g. Kaggle) is searchable but never citable.
    # Retrieval already excludes it from the finding candidate list; this is defense in depth.
    if version.verification_tier not in CITABLE_TIERS:
        await write_audit(
            session, actor=actor, action="citation_rejected",
            target=str(contract_id), verdict="denied",
            detail={
                "reason": "uncitable_tier",
                "verification_tier": version.verification_tier,
                "clause_id": str(clause_id) if clause_id else None,
                "attempted_version_id": str(regulation_version_id),
            },
        )
        await session.flush()
        raise SanadError("citation_required")

    finding = Finding(
        contract_id=contract_id,
        clause_id=clause_id,
        regulation_version_id=version.id,
        title_ar=title_ar,
        title_en=title_en,
        explanation_ar=explanation_ar,
        explanation_en=explanation_en,
        severity=severity,
        category=category,
        violation_cost_ar=violation_cost_ar,
        violation_cost_min=violation_cost_min,
        violation_cost_max=violation_cost_max,
        confidence_tier=confidence_tier,
        match_score=match_score,
        match_margin=match_margin,
        review_status="pending",
    )
    session.add(finding)
    await session.flush()
    return finding
