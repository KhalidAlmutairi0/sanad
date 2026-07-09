"""Database-level guarantees (test-plan §5: DB-03/04/06/08)."""
from __future__ import annotations

import datetime as dt
import hashlib
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contract, Finding, Regulation, RegulationVersion, User


async def _regulation(session: AsyncSession) -> Regulation:
    reg = Regulation(
        code=f"R-{uuid.uuid4().hex[:6]}", name_ar="ن", name_en="R",
        authority="A", source_domain="x.gov.sa",
    )
    session.add(reg)
    await session.flush()
    return reg


async def test_duplicate_article_version_is_rejected(session: AsyncSession, user: User) -> None:
    # DB-03: unique (regulation_id, article_ref, content_hash) — same bytes never stored twice.
    reg = await _regulation(session)
    text = "نص المادة."
    h = hashlib.sha256(text.encode()).hexdigest()
    common = dict(
        regulation_id=reg.id, article_ref="Article 1", article_text_ar=text,
        source_url="https://x.gov.sa", content_hash=h,
        fetched_at=dt.datetime.now(dt.timezone.utc), verified_by=user.id,
    )
    session.add(RegulationVersion(**common))
    await session.flush()
    session.add(RegulationVersion(**common))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_finding_with_bad_contract_fk_is_rejected(
    session: AsyncSession, regulation_version: RegulationVersion
) -> None:
    # DB-04: FK integrity on findings.contract_id.
    session.add(
        Finding(
            contract_id=uuid.uuid4(),  # no such contract
            regulation_version_id=regulation_version.id,
            title_ar="t", severity="high", category="regulatory",
        )
    )
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_invalid_enum_is_rejected_by_check(
    session: AsyncSession, contract: Contract, regulation_version: RegulationVersion
) -> None:
    # DB-06: named CHECK constraints on enums.
    session.add(
        Finding(
            contract_id=contract.id, regulation_version_id=regulation_version.id,
            title_ar="t", severity="catastrophic", category="regulatory",  # invalid severity
        )
    )
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_arabic_text_round_trips_nfc_stable_hash(session: AsyncSession, user: User) -> None:
    # DB-08: Arabic stored + read back identically; content_hash stable.
    reg = await _regulation(session)
    text = "تُعالَج البيانات الشخصية بموافقة صاحبها."
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rv = RegulationVersion(
        regulation_id=reg.id, article_ref="Article 5", article_text_ar=text,
        source_url="https://x.gov.sa", content_hash=h,
        fetched_at=dt.datetime.now(dt.timezone.utc), verified_by=user.id,
    )
    session.add(rv)
    await session.flush()
    # Read the column value straight back from the DB (round-trip), not the cached ORM attr.
    stored = (
        await session.execute(
            select(RegulationVersion.article_text_ar).where(RegulationVersion.id == rv.id)
        )
    ).scalar_one()
    assert stored == text
    assert hashlib.sha256(stored.encode("utf-8")).hexdigest() == h
