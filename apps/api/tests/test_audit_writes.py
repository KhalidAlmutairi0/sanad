"""Audit everything (AGENTS.md #6) + append-only enforcement at the DB grant level."""
from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog
from app.services.audit import write_audit


async def test_write_audit_inserts_row(session: AsyncSession) -> None:
    await write_audit(
        session, actor="analysis", action="score_computed",
        target="contract-x", verdict="n-a", detail={"score": 72},
    )
    rows = (
        await session.execute(select(AuditLog).where(AuditLog.action == "score_computed"))
    ).scalars().all()
    assert any(r.target == "contract-x" and r.detail_json == {"score": 72} for r in rows)


async def test_audit_log_is_append_only(session: AsyncSession) -> None:
    # The app role has INSERT+SELECT only; UPDATE must be denied at the privilege level.
    with pytest.raises((ProgrammingError, DBAPIError)):
        await session.execute(text("UPDATE audit_log SET action = 'tampered' WHERE false"))


async def test_regulation_versions_is_append_only(session: AsyncSession) -> None:
    with pytest.raises((ProgrammingError, DBAPIError)):
        await session.execute(text("UPDATE regulation_versions SET article_ref = 'x' WHERE false"))
    # A separate transaction is needed after the aborted one; the fixture rolls back.
