"""Readiness Score computation + Deal-breaker Radar. Both read reviewed findings only.

Score model (deterministic, auditable): start at 100 and subtract a severity weight for
each ACCEPTED finding. REJECTED findings were dismissed by the reviewer and do not
penalize. PENDING findings are excluded entirely — they cannot move the score
(invariant). Score is only computed once at least one finding has been reviewed."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contract, Finding
from app.services.audit import ACTOR_ANALYSIS, write_audit

REVIEWED = ("accepted", "rejected")
SEVERITY_WEIGHT = {"critical": 40, "high": 20, "medium": 8, "low": 3}


@dataclass
class ScoreResult:
    score: int | None
    reviewed_count: int
    accepted_count: int


async def compute_readiness_score(
    session: AsyncSession, contract_id: uuid.UUID, *, audit: bool = True
) -> ScoreResult:
    findings = (
        await session.execute(
            select(Finding.severity, Finding.review_status).where(
                Finding.contract_id == contract_id,
                Finding.review_status.in_(REVIEWED),  # reviewed-only, enforced in the query
            )
        )
    ).all()

    if not findings:
        return ScoreResult(score=None, reviewed_count=0, accepted_count=0)

    penalty = 0
    accepted = 0
    for severity, status in findings:
        if status == "accepted":
            accepted += 1
            penalty += SEVERITY_WEIGHT.get(severity, 8)
    score = max(0, 100 - penalty)

    contract = await session.get(Contract, contract_id)
    if contract is not None:
        contract.readiness_score = score

    if audit:
        await write_audit(
            session, actor=ACTOR_ANALYSIS, action="score_computed",
            target=str(contract_id), verdict="n-a",
            detail={"score": score, "reviewed": len(findings), "accepted": accepted},
        )
    return ScoreResult(score=score, reviewed_count=len(findings), accepted_count=accepted)


async def compute_radar(session: AsyncSession, contract_id: uuid.UUID) -> dict:
    """Deal-breaker Radar: GO / REVIEW / STOP from reviewed findings only. Up to 3 killers
    (accepted critical/high), most severe first."""
    accepted = (
        await session.execute(
            select(Finding)
            .where(Finding.contract_id == contract_id, Finding.review_status == "accepted")
        )
    ).scalars().all()

    killers = [f for f in accepted if f.severity in ("critical", "high")]
    killers.sort(key=lambda f: 0 if f.severity == "critical" else 1)

    if any(f.severity == "critical" for f in accepted):
        verdict = "STOP"
    elif killers:
        verdict = "REVIEW"
    else:
        verdict = "GO"
    return {"verdict": verdict, "killers": killers[:3]}
