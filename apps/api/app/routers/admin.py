"""Admin: manage the research-agent egress allowlist and query the audit log.
Admin role only. The allowlist file is the source the DNS watcher reads on the agent host;
the API manages its contents and audits every change."""
from __future__ import annotations

import datetime as dt
import os
import pathlib

import yaml
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session, require_roles
from app.models import AuditLog, User
from app.services.audit import write_audit

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
