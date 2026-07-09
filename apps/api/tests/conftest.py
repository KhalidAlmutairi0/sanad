"""Test fixtures. Each test runs inside a transaction that is rolled back, so nothing is
committed — this also respects the append-only grants (no DELETE needed for cleanup).

Requires the app database to be reachable (run via `docker compose run --rm api pytest`).
"""
from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import engine
from app.core.security import create_access_token
from app.models import Clause, Contract, Regulation, RegulationVersion, User


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    conn = await engine.connect()
    trans = await conn.begin()
    # join_transaction_mode="create_savepoint" makes endpoint-level session.commit() operate
    # on a savepoint, so the outer rollback still undoes everything (isolated, even for code
    # paths that commit). Append-only tables need no DELETE for cleanup this way.
    sess = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
    try:
        yield sess
    finally:
        await sess.close()
        await trans.rollback()
        await conn.close()


@pytest_asyncio.fixture
async def api_client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """In-process ASGI client whose DB dependency is the transactional test session."""
    from app.core.deps import get_session as dep_get_session
    from app.main import app

    async def _override() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[dep_get_session] = _override
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.pop(dep_get_session, None)


@pytest_asyncio.fixture
async def auth_headers(user: User) -> dict[str, str]:
    """Bearer header for the seeded reviewer user (resolves via the same test session)."""
    token = create_access_token(user_id=str(user.id), role=user.role)
    return {"authorization": f"Bearer {token}"}


async def make_user(session: AsyncSession, role: str) -> User:
    u = User(
        email=f"{role}-{uuid.uuid4()}@sanad.local",
        display_name=f"Test {role}",
        role=role,
        password_hash="x",
    )
    session.add(u)
    await session.flush()
    return u


def headers_for(u: User) -> dict[str, str]:
    return {"authorization": f"Bearer {create_access_token(user_id=str(u.id), role=u.role)}"}


@pytest_asyncio.fixture
async def sharia_headers(session: AsyncSession) -> dict[str, str]:
    return headers_for(await make_user(session, "sharia_board"))


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    u = User(
        email=f"reviewer-{uuid.uuid4()}@sanad.local",
        display_name="Test Reviewer",
        role="reviewer",
        password_hash="x",
    )
    session.add(u)
    await session.flush()
    return u


@pytest_asyncio.fixture
async def regulation_version(session: AsyncSession, user: User) -> RegulationVersion:
    reg = Regulation(
        code=f"PDPL-{uuid.uuid4().hex[:6]}",
        name_ar="نظام حماية البيانات الشخصية",
        name_en="Personal Data Protection Law",
        authority="SDAIA",
        source_domain="sdaia.gov.sa",
    )
    session.add(reg)
    await session.flush()
    rv = RegulationVersion(
        regulation_id=reg.id,
        article_ref="Article 35",
        article_text_ar="يعاقب بغرامة لا تزيد على ثلاثة ملايين ريال.",
        source_url="https://sdaia.gov.sa/x",
        content_hash=uuid.uuid4().hex,
        fetched_at=dt.datetime.now(dt.timezone.utc),
        verified_by=user.id,
    )
    session.add(rv)
    await session.flush()
    return rv


@pytest_asyncio.fixture
async def contract(session: AsyncSession, user: User) -> Contract:
    c = Contract(
        title="Test Contract",
        uploaded_by=user.id,
        raw_object_key=f"{uuid.uuid4()}/raw",
        status="reviewing",
    )
    session.add(c)
    await session.flush()
    return c
