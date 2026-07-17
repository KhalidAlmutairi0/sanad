"""Vendor evaluation API. Multi-file upload → explicit run-comparison (Sandbox 1 extract →
Sandbox 2 gate/compare). Distinct from single-contract review. run-comparison is the only step
that spends LLM tokens; results recompute cheaply from stored JSON."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user, get_session
from app.core.errors import SanadError
from app.core.queue import get_queue
from app.core.storage import get_minio, presigned_put
from app.models import User, VendorEvaluation, VendorSubmission
from app.schemas.vendor import (
    AddSubmissionRequest,
    AddSubmissionResponse,
    CreateEvaluationRequest,
    CreateEvaluationResponse,
    EvaluationList,
    EvaluationListItem,
    RunComparisonResponse,
)
from app.services.audit import write_audit
from app.services.vendor.orchestrate import compute_results

router = APIRouter(prefix="/vendor-evaluations", tags=["vendor"])
_settings = get_settings()


@router.post("", response_model=CreateEvaluationResponse, status_code=201)
async def create_evaluation(
    body: CreateEvaluationRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CreateEvaluationResponse:
    ev = VendorEvaluation(title=body.title, created_by=user.id, status="uploading")
    session.add(ev)
    await session.commit()
    return CreateEvaluationResponse(id=ev.id)


@router.post("/{evaluation_id}/submissions", response_model=AddSubmissionResponse, status_code=201)
async def add_submission(
    evaluation_id: uuid.UUID,
    body: AddSubmissionRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AddSubmissionResponse:
    ev = await session.get(VendorEvaluation, evaluation_id)
    if ev is None:
        raise SanadError("not_found")
    sub_id = uuid.uuid4()
    raw_key = f"vendor/{sub_id}/raw"
    session.add(VendorSubmission(
        id=sub_id, evaluation_id=evaluation_id, vendor_name=body.vendor_name,
        source_filename=body.filename, raw_object_key=raw_key, status="uploaded",
    ))
    await session.commit()
    return AddSubmissionResponse(id=sub_id, upload_url=presigned_put(_settings.bucket_quarantine, raw_key))


@router.post("/{evaluation_id}/run-comparison", response_model=RunComparisonResponse, status_code=202)
async def run_comparison(
    evaluation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RunComparisonResponse:
    """Explicit trigger — the user confirms the batch is complete + labeled. Enqueues the
    sandbox pipeline; must not run automatically on upload."""
    ev = await session.get(VendorEvaluation, evaluation_id)
    if ev is None:
        raise SanadError("not_found")
    count = (
        await session.execute(
            select(func.count()).select_from(VendorSubmission).where(
                VendorSubmission.evaluation_id == evaluation_id
            )
        )
    ).scalar_one()
    if count == 0:
        raise SanadError("validation_failed", "أضِف عروض الموردين قبل تشغيل المقارنة")

    ev.status = "comparing"
    await write_audit(session, actor=str(user.id), action="vendor_run_comparison",
                      target=str(evaluation_id), verdict="n-a", detail={"submissions": count})
    await session.commit()

    queue = await get_queue()
    await queue.enqueue_job("evaluate_vendor_batch", str(evaluation_id))
    await queue.aclose()
    return RunComparisonResponse(id=evaluation_id, status="comparing")


@router.get("", response_model=EvaluationList)
async def list_evaluations(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> EvaluationList:
    rows = (
        await session.execute(select(VendorEvaluation).order_by(VendorEvaluation.created_at.desc()))
    ).scalars().all()
    items = []
    for ev in rows:
        n = (
            await session.execute(
                select(func.count()).select_from(VendorSubmission).where(
                    VendorSubmission.evaluation_id == ev.id
                )
            )
        ).scalar_one()
        items.append(EvaluationListItem(id=ev.id, title=ev.title, status=ev.status,
                                        vendor_count=n, created_at=ev.created_at))
    return EvaluationList(items=items)


@router.get("/{evaluation_id}")
async def get_results(
    evaluation_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Stage-1 scorecards (all vendors) + Stage-2 comparison (passers). Recomputed from stored
    extraction JSON — no raw text, no LLM."""
    ev = await session.get(VendorEvaluation, evaluation_id)
    if ev is None:
        raise SanadError("not_found")
    subs = (
        await session.execute(
            select(VendorSubmission).where(VendorSubmission.evaluation_id == evaluation_id)
            .order_by(VendorSubmission.created_at)
        )
    ).scalars().all()
    results = compute_results(ev.title, ev.status, list(subs))
    results["evaluation_id"] = str(evaluation_id)
    return results
