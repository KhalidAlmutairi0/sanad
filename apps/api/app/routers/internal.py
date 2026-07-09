"""Internal service-to-service endpoints (api-contracts.md). Guarded by the internal
service token. Used when the sanitizer/agent run as fully separate processes; in the
compose topology the worker updates the DB directly, and this endpoint mirrors that path
for split deployments."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.deps import get_session, require_internal_token
from app.core.errors import SanadError
from app.models import Contract, MonitoringEvent, Regulation
from app.services.audit import ACTOR_RESEARCH_AGENT, ACTOR_SANITIZER, write_audit

router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal_token)])


class SanitizeComplete(BaseModel):
    contract_id: uuid.UUID
    sanitized_object_key: str
    status: str


@router.post("/sanitize-complete")
async def sanitize_complete(
    body: SanitizeComplete, session: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    contract = await session.get(Contract, body.contract_id)
    if not contract:
        raise SanadError("not_found")
    contract.sanitized_object_key = body.sanitized_object_key
    contract.status = body.status
    await write_audit(
        session, actor=ACTOR_SANITIZER, action="sanitize_succeeded",
        target=str(body.contract_id), verdict="allowed",
        detail={"sanitized_object_key": body.sanitized_object_key},
    )
    await session.commit()
    return {"status": "ok"}


class AgentCandidate(BaseModel):
    regulation_code: str
    article_ref: str
    article_text_ar: str
    source_url: str
    change_type: str  # new_article | amended | repealed


@router.post("/agent-candidate", status_code=202)
async def agent_candidate(
    body: AgentCandidate, session: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    """Research agent submits a fetched candidate to the human verification queue. Records a
    monitoring_events row only — NEVER writes to regulation_versions (that requires the human
    verify gate)."""
    regulation = (
        await session.execute(select(Regulation).where(Regulation.code == body.regulation_code))
    ).scalar_one_or_none()
    if not regulation:
        raise SanadError("not_found")
    event = MonitoringEvent(
        regulation_id=regulation.id,
        change_type=body.change_type if body.change_type in ("new_article", "amended", "repealed") else None,
        status="detected",
    )
    session.add(event)
    await write_audit(
        session, actor=ACTOR_RESEARCH_AGENT, action="agent_fetch",
        target=body.source_url, verdict="allowed",
        detail={"regulation_code": body.regulation_code, "article_ref": body.article_ref,
                "change_type": body.change_type},
    )
    await session.commit()
    return {"status": "queued"}
