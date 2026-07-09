from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session, require_roles
from app.core.errors import SanadError
from app.core.queue import get_queue
from app.models import IdeaCheck, IdeaCheckCitation, Regulation, RegulationVersion, User
from app.schemas.idea_checks import (
    IdeaCheckDetail,
    IdeaCitation,
    IdeaList,
    IdeaListItem,
    IdeaReviewRequest,
    IdeaReviewResponse,
    SubmitIdeaRequest,
    SubmitIdeaResponse,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/idea-checks", tags=["idea-checks"])


@router.post("", response_model=SubmitIdeaResponse, status_code=202)
async def submit_idea(
    body: SubmitIdeaRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubmitIdeaResponse:
    idea = IdeaCheck(submitted_by=user.id, idea_text=body.idea_text, status="submitted")
    session.add(idea)
    await session.flush()  # populate idea.id
    await write_audit(
        session, actor=str(user.id), action="idea_check_submitted",
        target=str(idea.id), verdict="n-a",
    )
    await session.commit()

    queue = await get_queue()
    await queue.enqueue_job("generate_idea_report_job", str(idea.id))
    await queue.aclose()
    return SubmitIdeaResponse(id=idea.id, status="submitted")


@router.get("", response_model=IdeaList)
async def list_ideas(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> IdeaList:
    total = (await session.execute(select(func.count()).select_from(IdeaCheck))).scalar_one()
    rows = (
        await session.execute(
            select(IdeaCheck).order_by(IdeaCheck.created_at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return IdeaList(items=[IdeaListItem(id=i.id, status=i.status) for i in rows], total=total)


@router.get("/{idea_id}", response_model=IdeaCheckDetail)
async def get_idea(
    idea_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> IdeaCheckDetail:
    idea = await session.get(IdeaCheck, idea_id)
    if not idea:
        raise SanadError("not_found")

    rows = (
        await session.execute(
            select(RegulationVersion, Regulation.code)
            .join(IdeaCheckCitation, IdeaCheckCitation.regulation_version_id == RegulationVersion.id)
            .join(Regulation, Regulation.id == RegulationVersion.regulation_id)
            .where(IdeaCheckCitation.idea_check_id == idea_id)
        )
    ).all()
    citations = [
        IdeaCitation(
            regulation_version_id=rv.id,
            regulation_code=code,
            article_ref=rv.article_ref,
            source_url=rv.source_url,
        )
        for rv, code in rows
    ]
    return IdeaCheckDetail(
        id=idea.id, idea_text=idea.idea_text, status=idea.status,
        report_ar=idea.report_ar, report_en=idea.report_en,
        citations=citations, reviewed_by=idea.reviewed_by,
    )


@router.post("/{idea_id}/review", response_model=IdeaReviewResponse)
async def review_idea(
    idea_id: uuid.UUID,
    body: IdeaReviewRequest,
    user: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> IdeaReviewResponse:
    idea = await session.get(IdeaCheck, idea_id)
    if not idea:
        raise SanadError("not_found")
    if idea.status != "generated":
        raise SanadError("review_conflict")
    idea.status = "reviewed"
    idea.reviewed_by = user.id
    await write_audit(
        session, actor=str(user.id), action="idea_check_reviewed",
        target=str(idea_id), verdict="n-a",
        detail={"notes_ar": body.notes_ar} if body.notes_ar else None,
    )
    await session.commit()
    return IdeaReviewResponse(id=idea.id, status="reviewed")
