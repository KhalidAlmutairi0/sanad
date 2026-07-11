"""Obligation Register. Every obligation is bound to a source article version (citation)."""
from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session, require_roles
from app.core.errors import SanadError
from app.models import Obligation, Regulation, RegulationVersion, User
from app.services.audit import write_audit

router = APIRouter(prefix="/obligations", tags=["obligations"])


class ObligationCitation(BaseModel):
    regulation_version_id: uuid.UUID
    regulation_code: str
    article_ref: str
    source_url: str


class ObligationItem(BaseModel):
    id: uuid.UUID
    title_ar: str
    title_en: str | None
    owner_id: uuid.UUID | None
    due_date: dt.date | None
    status: str
    citation: ObligationCitation


class ObligationList(BaseModel):
    items: list[ObligationItem]


class AssignRequest(BaseModel):
    owner_id: uuid.UUID
    due_date: dt.date


class AssignResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    due_date: dt.date


@router.get("", response_model=ObligationList)
async def list_obligations(
    status: str | None = Query(default=None, pattern="^(open|in_progress|met|overdue)$"),
    owner_id: uuid.UUID | None = Query(default=None),
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ObligationList:
    stmt = (
        select(Obligation, RegulationVersion, Regulation.code)
        .join(RegulationVersion, RegulationVersion.id == Obligation.regulation_version_id)
        .join(Regulation, Regulation.id == RegulationVersion.regulation_id)
        .order_by(Obligation.due_date.nulls_last(), Obligation.created_at)
    )
    if status:
        stmt = stmt.where(Obligation.status == status)
    if owner_id:
        stmt = stmt.where(Obligation.owner_id == owner_id)
    rows = (await session.execute(stmt)).all()
    return ObligationList(
        items=[
            ObligationItem(
                id=o.id, title_ar=o.title_ar, title_en=o.title_en, owner_id=o.owner_id,
                due_date=o.due_date, status=o.status,
                citation=ObligationCitation(
                    regulation_version_id=rv.id, regulation_code=code,
                    article_ref=rv.article_ref, source_url=rv.source_url,
                ),
            )
            for o, rv, code in rows
        ]
    )


@router.post("/{obligation_id}/assign", response_model=AssignResponse)
async def assign(
    obligation_id: uuid.UUID,
    body: AssignRequest,
    user: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> AssignResponse:
    obligation = await session.get(Obligation, obligation_id)
    if not obligation:
        raise SanadError("not_found")
    obligation.owner_id = body.owner_id
    obligation.due_date = body.due_date
    if obligation.status == "open":
        obligation.status = "in_progress"
    await write_audit(
        session, actor=str(user.id), action="obligation_assigned",
        target=str(obligation_id), verdict="n-a",
        detail={"owner_id": str(body.owner_id), "due_date": str(body.due_date)},
    )
    await session.commit()
    return AssignResponse(id=obligation.id, owner_id=body.owner_id, due_date=body.due_date)
