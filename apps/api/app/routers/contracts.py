from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user, get_session
from app.core.errors import SanadError
from app.core.queue import get_queue
from app.core.storage import get_minio, presigned_put
from app.models import Clause, Contract, Finding, User
from app.schemas.contracts import (
    ClauseItem,
    ClauseList,
    ContractDetail,
    ContractList,
    ContractListItem,
    CreateContractRequest,
    CreateContractResponse,
    FindingsSummary,
    UploadedResponse,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/contracts", tags=["contracts"])
_settings = get_settings()


@router.post("", response_model=CreateContractResponse, status_code=201)
async def create_contract(
    body: CreateContractRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CreateContractResponse:
    contract_id = uuid.uuid4()
    raw_key = f"{contract_id}/raw"  # type detected from content at sanitize time
    session.add(
        Contract(
            id=contract_id,
            title=body.title,
            uploaded_by=user.id,
            raw_object_key=raw_key,
            status="uploaded",
        )
    )
    await session.commit()
    upload_url = presigned_put(_settings.bucket_quarantine, raw_key)
    return CreateContractResponse(id=contract_id, upload_url=upload_url)


@router.post("/{contract_id}/uploaded", response_model=UploadedResponse, status_code=202)
async def signal_uploaded(
    contract_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UploadedResponse:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise SanadError("not_found")

    # Idempotent: if the pipeline already started, return current status without re-queuing
    # (a duplicate /uploaded call must not spawn a second pipeline).
    if contract.status not in ("uploaded", "failed"):
        return UploadedResponse(id=contract_id, status=contract.status)

    # Validate size + type BEFORE touching the sanitizer (api-contracts.md upload constraints).
    client = get_minio()
    try:
        stat = client.stat_object(_settings.bucket_quarantine, contract.raw_object_key)
    except Exception:
        raise SanadError("not_found", "ما تم رفع الملف بعد", "No file uploaded yet")
    if stat.size > _settings.max_upload_mb * 1024 * 1024:
        contract.status = "failed"
        contract.failure_reason = "file_too_large"
        await write_audit(session, actor=str(user.id), action="sanitize_failed",
                          target=str(contract_id), verdict="denied",
                          detail={"reason": "file_too_large", "size": stat.size})
        await session.commit()
        raise SanadError("file_too_large")

    contract.status = "sanitizing"
    await write_audit(session, actor=str(user.id), action="contract_uploaded",
                      target=str(contract_id), verdict="n-a",
                      detail={"size": stat.size})
    await session.commit()

    queue = await get_queue()
    await queue.enqueue_job("sanitize_contract", str(contract_id))
    await queue.aclose()
    return UploadedResponse(id=contract_id, status="sanitizing")


@router.get("", response_model=ContractList)
async def list_contracts(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ContractList:
    total = (await session.execute(select(func.count()).select_from(Contract))).scalar_one()
    rows = (
        await session.execute(
            select(Contract).order_by(Contract.created_at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return ContractList(
        items=[
            ContractListItem(
                id=c.id, title=c.title, status=c.status,
                readiness_score=c.readiness_score, created_at=c.created_at,
            )
            for c in rows
        ],
        total=total,
    )


@router.get("/{contract_id}", response_model=ContractDetail)
async def get_contract(
    contract_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ContractDetail:
    contract = await session.get(Contract, contract_id)
    if not contract:
        raise SanadError("not_found")

    counts = (
        await session.execute(
            select(Finding.severity, Finding.review_status, func.count())
            .where(Finding.contract_id == contract_id)
            .group_by(Finding.severity, Finding.review_status)
        )
    ).all()
    summary = FindingsSummary()
    for severity, review_status, n in counts:
        setattr(summary, severity, getattr(summary, severity) + n)
        if review_status == "pending":
            summary.pending += n

    return ContractDetail(
        id=contract.id, title=contract.title, status=contract.status,
        readiness_score=contract.readiness_score, findings_summary=summary,
    )


@router.get("/{contract_id}/clauses", response_model=ClauseList)
async def get_clauses(
    contract_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ClauseList:
    rows = (
        await session.execute(
            select(Clause).where(Clause.contract_id == contract_id).order_by(Clause.ordinal)
        )
    ).scalars().all()
    return ClauseList(
        items=[ClauseItem(id=c.id, ordinal=c.ordinal, text_ar=c.text_ar, text_en=c.text_en) for c in rows]
    )
