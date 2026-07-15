"""Obligation reverification hold (spec #6).

When a cited article is flagged as changed (promote-candidate creates a monitoring_event),
obligations bound to any version of that (regulation, article_ref) must not keep silently
looking current: their status moves to 'pending_reverification' and the prior status is saved.
When a reviewer verifies the change (a human_verified version is written), the hold resolves
back to the prior status — never auto-advanced to met/open without reviewer input.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Obligation, RegulationVersion

PENDING_REVERIFICATION = "pending_reverification"


async def _obligations_for_article(
    session: AsyncSession, regulation_id: uuid.UUID, article_ref: str
) -> list[Obligation]:
    version_ids = select(RegulationVersion.id).where(
        RegulationVersion.regulation_id == regulation_id,
        RegulationVersion.article_ref == article_ref,
    )
    return list(
        (
            await session.execute(
                select(Obligation).where(Obligation.regulation_version_id.in_(version_ids))
            )
        ).scalars().all()
    )


async def flag_pending_reverification(
    session: AsyncSession, regulation_id: uuid.UUID, article_ref: str
) -> int:
    """Put every obligation citing this article on hold. Additive: keeps owner/due_date and
    stashes the current status in prior_status. Idempotent — already-held rows are skipped."""
    count = 0
    for ob in await _obligations_for_article(session, regulation_id, article_ref):
        if ob.status == PENDING_REVERIFICATION:
            continue
        ob.prior_status = ob.status
        ob.status = PENDING_REVERIFICATION
        count += 1
    return count


async def resolve_pending_reverification(
    session: AsyncSession, regulation_id: uuid.UUID, article_ref: str
) -> int:
    """Release the hold once the change is human-verified: restore prior_status. Does not
    advance to met/open on its own — it only undoes the hold."""
    count = 0
    for ob in await _obligations_for_article(session, regulation_id, article_ref):
        if ob.status != PENDING_REVERIFICATION:
            continue
        ob.status = ob.prior_status or "open"
        ob.prior_status = None
        count += 1
    return count
