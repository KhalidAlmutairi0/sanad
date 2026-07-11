"""Admin: manage the research-agent egress allowlist and query the audit log.
Admin role only. The allowlist file is the source the DNS watcher reads on the agent host;
the API manages its contents and audits every change."""
from __future__ import annotations

import datetime as dt
import os
import pathlib
import secrets
import uuid

import yaml
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session, require_roles
from app.core.errors import SanadError
from app.models import AuditLog, Invite, User
from app.services.analysis.findings import CONTRACTS_CONTRACT, CONTRACTS_GUIDANCE_DEFAULT
from app.services.analysis.idea_report import IDEA_CONTRACT, IDEA_GUIDANCE_DEFAULT
from app.services.audit import write_audit
from app.services.settings import (
    CONTRACTS_GUIDANCE_KEY,
    IDEA_GUIDANCE_KEY,
    get_setting,
    set_setting,
)

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWLIST_PATH = pathlib.Path(os.environ.get("ALLOWLIST_PATH", "/app/data/allowlist.yaml"))
DEFAULT_DOMAINS = [
    "sama.gov.sa", "sdaia.gov.sa", "zatca.gov.sa", "hrsd.gov.sa",
    "laws.boe.gov.sa", "api.openai.com",
]


class Allowlist(BaseModel):
    domains: list[str]


class AuditItem(BaseModel):
    actor: str
    action: str
    target: str | None
    verdict: str | None
    detail_json: dict | None
    at: dt.datetime


class AuditPage(BaseModel):
    items: list[AuditItem]
    total: int


class InviteCreate(BaseModel):
    role: str = "reviewer"  # reviewer | sharia_board | admin
    email: str | None = None
    note: str | None = None


class InviteItem(BaseModel):
    code: str
    role: str
    email: str | None
    used: bool
    created_at: dt.datetime


class InviteList(BaseModel):
    items: list[InviteItem]


class Prompts(BaseModel):
    # Editable analyst guidance (persona + intent).
    contracts_guidance: str
    idea_guidance: str
    # Read-only locked machine contract, shown so the admin sees what is always appended.
    contracts_contract: str | None = None
    idea_contract: str | None = None


class PromptsUpdate(BaseModel):
    contracts_guidance: str
    idea_guidance: str


def _read_allowlist() -> list[str]:
    if ALLOWLIST_PATH.exists():
        data = yaml.safe_load(ALLOWLIST_PATH.read_text(encoding="utf-8")) or {}
        return list(data.get("domains", DEFAULT_DOMAINS))
    return list(DEFAULT_DOMAINS)


@router.get("/allowlist", response_model=Allowlist)
async def get_allowlist(_: User = Depends(require_roles("admin"))) -> Allowlist:
    return Allowlist(domains=_read_allowlist())


@router.put("/allowlist", response_model=Allowlist)
async def put_allowlist(
    body: Allowlist,
    user: User = Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_session),
) -> Allowlist:
    domains = [d.strip().lower() for d in body.domains if d.strip()]
    ALLOWLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    ALLOWLIST_PATH.write_text(yaml.safe_dump({"domains": domains}, allow_unicode=True), encoding="utf-8")
    await write_audit(
        session, actor=str(user.id), action="allowlist_updated", verdict="n-a",
        detail={"count": len(domains), "domains": domains},
    )
    await session.commit()
    return Allowlist(domains=domains)


@router.get("/audit", response_model=AuditPage)
async def get_audit(
    actor: str | None = Query(default=None),
    action: str | None = Query(default=None),
    verdict: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_session),
) -> AuditPage:
    conds = []
    if actor:
        conds.append(AuditLog.actor == actor)
    if action:
        conds.append(AuditLog.action == action)
    if verdict:
        conds.append(AuditLog.verdict == verdict)

    total = (await session.execute(select(func.count()).select_from(AuditLog).where(*conds))).scalar_one()
    rows = (
        await session.execute(
            select(AuditLog).where(*conds).order_by(AuditLog.at.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return AuditPage(
        items=[
            AuditItem(actor=r.actor, action=r.action, target=r.target, verdict=r.verdict,
                      detail_json=r.detail_json, at=r.at)
            for r in rows
        ],
        total=total,
    )


@router.get("/prompts", response_model=Prompts)
async def get_prompts(
    _: User = Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_session),
) -> Prompts:
    return Prompts(
        contracts_guidance=await get_setting(session, CONTRACTS_GUIDANCE_KEY, CONTRACTS_GUIDANCE_DEFAULT),
        idea_guidance=await get_setting(session, IDEA_GUIDANCE_KEY, IDEA_GUIDANCE_DEFAULT),
        contracts_contract=CONTRACTS_CONTRACT,
        idea_contract=IDEA_CONTRACT,
    )


@router.post("/prompts", response_model=Prompts)
async def put_prompts(
    body: PromptsUpdate,
    user: User = Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_session),
) -> Prompts:
    contracts = body.contracts_guidance.strip()
    idea = body.idea_guidance.strip()
    if not contracts or not idea:
        raise SanadError("validation_failed", "النص لا يمكن أن يكون فارغاً", "Guidance cannot be empty")
    await set_setting(session, CONTRACTS_GUIDANCE_KEY, contracts, user.id)
    await set_setting(session, IDEA_GUIDANCE_KEY, idea, user.id)
    await write_audit(
        session, actor=str(user.id), action="prompts_updated", verdict="n-a",
        detail={"contracts_len": len(contracts), "idea_len": len(idea)},
    )
    await session.commit()
    return Prompts(
        contracts_guidance=contracts, idea_guidance=idea,
        contracts_contract=CONTRACTS_CONTRACT, idea_contract=IDEA_CONTRACT,
    )


@router.post("/invites", response_model=InviteItem, status_code=201)
async def create_invite(
    body: InviteCreate,
    user: User = Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_session),
) -> InviteItem:
    if body.role not in ("reviewer", "sharia_board", "admin"):
        raise SanadError("validation_failed")
    invite = Invite(
        code=secrets.token_urlsafe(6),
        role=body.role,
        email=(body.email.strip().lower() if body.email else None),
        note=body.note,
        created_by=user.id,
    )
    session.add(invite)
    await write_audit(
        session, actor=str(user.id), action="invite_created", verdict="n-a",
        detail={"role": body.role, "email": invite.email},
    )
    await session.commit()
    return InviteItem(code=invite.code, role=invite.role, email=invite.email, used=False, created_at=invite.created_at)


@router.get("/invites", response_model=InviteList)
async def list_invites(
    _: User = Depends(require_roles("admin")),
    session: AsyncSession = Depends(get_session),
) -> InviteList:
    rows = (await session.execute(select(Invite).order_by(Invite.created_at.desc()))).scalars().all()
    return InviteList(
        items=[InviteItem(code=i.code, role=i.role, email=i.email, used=i.used, created_at=i.created_at) for i in rows]
    )
