"""Regulatory monitoring feed + the human verification gate. Verifying a detected change
appends a new, immutable regulation_versions row (verified_by = the human caller)."""
from __future__ import annotations

import datetime as dt
import hashlib
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session, require_roles
from app.core.errors import SanadError
from app.models import MonitoringEvent, Regulation, RegulationVersion, User
from app.services.audit import write_audit
from app.services.retrieval import embed_texts

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class EventItem(BaseModel):
    id: uuid.UUID
    regulation_code: str
    change_type: str | None
    detected_at: dt.datetime
    impact_summary_ar: str | None
    status: str
    new_version_id: uuid.UUID | None


class EventList(BaseModel):
    items: list[EventItem]


class VersionPayload(BaseModel):
    article_ref: str
    article_text_ar: str
    article_text_en: str | None = None
    source_url: str
    effective_date: dt.date | None = None


class VerifyRequest(BaseModel):
    regulation_version: VersionPayload


class VerifyResponse(BaseModel):
    regulation_version_id: uuid.UUID
    status: str


@router.get("/events", response_model=EventList)
async def list_events(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> EventList:
    rows = (
        await session.execute(
            select(MonitoringEvent, Regulation.code)
            .join(Regulation, Regulation.id == MonitoringEvent.regulation_id)
            .order_by(MonitoringEvent.detected_at.desc())
        )
    ).all()
    return EventList(
        items=[
            EventItem(
                id=e.id, regulation_code=code, change_type=e.change_type,
                detected_at=e.detected_at, impact_summary_ar=e.impact_summary_ar,
                status=e.status, new_version_id=e.new_version_id,
            )
            for e, code in rows
        ]
    )


@router.post("/events/{event_id}/verify", response_model=VerifyResponse, status_code=201)
async def verify_event(
    event_id: uuid.UUID,
    body: VerifyRequest,
    user: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> VerifyResponse:
    event = await session.get(MonitoringEvent, event_id)
    if not event:
        raise SanadError("not_found")
    if event.status == "verified":
        raise SanadError("review_conflict")

    p = body.regulation_version
    text_ar = " ".join(p.article_text_ar.split())
    content_hash = hashlib.sha256(text_ar.encode("utf-8")).hexdigest()
    [embedding] = await embed_texts([text_ar], input_type="passage")

    version = RegulationVersion(
        regulation_id=event.regulation_id,
        article_ref=p.article_ref,
        article_text_ar=text_ar,
        article_text_en=p.article_text_en,
        source_url=p.source_url,
        content_hash=content_hash,
        fetched_at=dt.datetime.now(dt.timezone.utc),
        effective_date=p.effective_date,
        verified_by=user.id,  # the human gate
        embedding=embedding,
    )
    session.add(version)
    await session.flush()

    event.new_version_id = version.id
    event.status = "verified"
    await write_audit(
        session, actor=str(user.id), action="regulation_version_verified",
        target=str(version.id), verdict="allowed",
        detail={"event_id": str(event_id), "article_ref": p.article_ref},
    )
    await session.commit()
    return VerifyResponse(regulation_version_id=version.id, status="verified")
