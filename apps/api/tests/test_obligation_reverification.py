"""Obligation reverification hold (spec #6).

Promoting a change to an article puts obligations citing it on hold (pending_reverification,
prior status saved); verifying the change releases the hold back to the prior status.
"""
from __future__ import annotations

import datetime as dt
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Obligation, Regulation, RegulationVersion, User
from app.services.monitoring.obligations import (
    flag_pending_reverification,
    resolve_pending_reverification,
)


async def _seed_obligation(session: AsyncSession, user: User, status: str) -> tuple[Obligation, Regulation]:
    reg = Regulation(code=f"PDPL-{uuid.uuid4().hex[:6]}", name_ar="نظام", name_en="Law",
                     authority="SDAIA", source_domain="sdaia.gov.sa")
    session.add(reg)
    await session.flush()
    rv = RegulationVersion(
        regulation_id=reg.id, article_ref="Article 30", article_text_ar="نص.",
        source_url="https://sdaia.gov.sa/x", content_hash=uuid.uuid4().hex,
        fetched_at=dt.datetime.now(dt.timezone.utc), verified_by=user.id,
    )
    session.add(rv)
    await session.flush()
    ob = Obligation(regulation_version_id=rv.id, title_ar="التزام", status=status, owner_id=user.id)
    session.add(ob)
    await session.flush()
    return ob, reg


@pytest.mark.asyncio
async def test_flag_puts_obligation_on_hold_and_saves_prior(session: AsyncSession, user: User) -> None:
    ob, reg = await _seed_obligation(session, user, "in_progress")
    n = await flag_pending_reverification(session, reg.id, "Article 30")
    assert n == 1
    await session.refresh(ob)
    assert ob.status == "pending_reverification"
    assert ob.prior_status == "in_progress"  # owner untouched (additive)
    assert ob.owner_id == user.id


@pytest.mark.asyncio
async def test_resolve_restores_prior_status(session: AsyncSession, user: User) -> None:
    ob, reg = await _seed_obligation(session, user, "met")
    await flag_pending_reverification(session, reg.id, "Article 30")
    n = await resolve_pending_reverification(session, reg.id, "Article 30")
    assert n == 1
    await session.refresh(ob)
    assert ob.status == "met" and ob.prior_status is None


@pytest.mark.asyncio
async def test_flag_is_idempotent(session: AsyncSession, user: User) -> None:
    ob, reg = await _seed_obligation(session, user, "open")
    assert await flag_pending_reverification(session, reg.id, "Article 30") == 1
    # second flag does not re-stash 'pending_reverification' as the prior status
    assert await flag_pending_reverification(session, reg.id, "Article 30") == 0
    await session.refresh(ob)
    assert ob.prior_status == "open"


@pytest.mark.asyncio
async def test_unrelated_article_not_flagged(session: AsyncSession, user: User) -> None:
    ob, reg = await _seed_obligation(session, user, "open")
    assert await flag_pending_reverification(session, reg.id, "Article 99") == 0
    await session.refresh(ob)
    assert ob.status == "open"
