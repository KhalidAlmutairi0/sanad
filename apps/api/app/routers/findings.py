from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session, require_roles
from app.core.errors import SanadError
from app.models import Contract, Finding, Regulation, RegulationVersion, User
from app.schemas.findings import (
    Citation,
    ExplainResponse,
    FindingItem,
    FindingList,
    RadarKiller,
    RadarResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.services.audit import write_audit
from app.services.scoring import compute_readiness_score
from app.services.scoring.score import compute_radar

router = APIRouter(tags=["findings"])

_SEVERITY_RANK = case(
    {"critical": 0, "high": 1, "medium": 2, "low": 3},
    value=Finding.severity,
    else_=4,
)


def _citation(rv: RegulationVersion, code: str) -> Citation:
    return Citation(
        regulation_version_id=rv.id,
        regulation_code=code,
        article_ref=rv.article_ref,
        article_text_ar=rv.article_text_ar,
        source_url=rv.source_url,
        effective_date=rv.effective_date,
    )


def _item(f: Finding, rv: RegulationVersion, code: str) -> FindingItem:
    return FindingItem(
        id=f.id,
        clause_id=f.clause_id,
        title_ar=f.title_ar,
        title_en=f.title_en,
        explanation_ar=f.explanation_ar,
        explanation_en=f.explanation_en,
        severity=f.severity,
        category=f.category,
        violation_cost_ar=f.violation_cost_ar,
        violation_cost_min=float(f.violation_cost_min) if f.violation_cost_min is not None else None,
        violation_cost_max=float(f.violation_cost_max) if f.violation_cost_max is not None else None,
        review_status=f.review_status,
        citation=_citation(rv, code),
    )


@router.get("/contracts/{contract_id}/findings", response_model=FindingList)
async def list_findings(
    contract_id: uuid.UUID,
    status: str | None = Query(default=None, pattern="^(pending|accepted|rejected)$"),
    severity: str | None = Query(default=None, pattern="^(critical|high|medium|low)$"),
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FindingList:
    stmt = (
        select(Finding, RegulationVersion, Regulation.code)
        .join(RegulationVersion, RegulationVersion.id == Finding.regulation_version_id)
        .join(Regulation, Regulation.id == RegulationVersion.regulation_id)
        .where(Finding.contract_id == contract_id)
        .order_by(_SEVERITY_RANK, Finding.created_at)
    )
    if status:
        stmt = stmt.where(Finding.review_status == status)
    if severity:
        stmt = stmt.where(Finding.severity == severity)

    rows = (await session.execute(stmt)).all()
    return FindingList(items=[_item(f, rv, code) for f, rv, code in rows])


@router.get("/findings/{finding_id}/explain", response_model=ExplainResponse)
async def explain_finding(
    finding_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ExplainResponse:
    row = (
        await session.execute(
            select(Finding, RegulationVersion, Regulation.code)
            .join(RegulationVersion, RegulationVersion.id == Finding.regulation_version_id)
            .join(Regulation, Regulation.id == RegulationVersion.regulation_id)
            .where(Finding.id == finding_id)
        )
    ).first()
    if not row:
        raise SanadError("not_found")
    f, rv, code = row
    return ExplainResponse(
        explanation_ar=f.explanation_ar,
        explanation_en=f.explanation_en,
        citation=_citation(rv, code),
    )


@router.post("/findings/{finding_id}/review", response_model=ReviewResponse)
async def review_finding(
    finding_id: uuid.UUID,
    body: ReviewRequest,
    user: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> ReviewResponse:
    if body.decision not in ("accepted", "rejected"):
        raise SanadError("validation_failed")
    finding = await session.get(Finding, finding_id)
    if not finding:
        raise SanadError("not_found")
    # A finding is decided once; re-deciding is a conflict, not a silent overwrite.
    if finding.review_status != "pending":
        raise SanadError("review_conflict")

    finding.review_status = body.decision
    finding.reviewed_by = user.id
    finding.reviewed_at = dt.datetime.now(dt.timezone.utc)
    await write_audit(
        session, actor=str(user.id), action="finding_reviewed",
        target=str(finding.contract_id), verdict="n-a",
        detail={"finding_id": str(finding_id), "decision": body.decision},
    )

    # Reviewed-only score recompute (writes its own score_computed audit).
    await compute_readiness_score(session, finding.contract_id)

    # Contract is 'reviewed' once nothing is left pending.
    pending = (
        await session.execute(
            select(func.count()).select_from(Finding).where(
                Finding.contract_id == finding.contract_id,
                Finding.review_status == "pending",
            )
        )
    ).scalar_one()
    contract = await session.get(Contract, finding.contract_id)
    if contract is not None:
        contract.status = "reviewed" if pending == 0 else "reviewing"

    await session.commit()
    return ReviewResponse(
        id=finding.id, review_status=finding.review_status, reviewed_at=finding.reviewed_at
    )


@router.get("/contracts/{contract_id}/radar", response_model=RadarResponse)
async def contract_radar(
    contract_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RadarResponse:
    radar = await compute_radar(session, contract_id)
    killers = []
    for f in radar["killers"]:
        row = (
            await session.execute(
                select(RegulationVersion, Regulation.code)
                .join(Regulation, Regulation.id == RegulationVersion.regulation_id)
                .where(RegulationVersion.id == f.regulation_version_id)
            )
        ).first()
        if not row:
            continue
        rv, code = row
        killers.append(
            RadarKiller(finding_id=f.id, title_ar=f.title_ar, severity=f.severity, citation=_citation(rv, code))
        )
    return RadarResponse(verdict=radar["verdict"], killers=killers)
