"""FastAPI dependencies: DB session, current user, role checks, internal service token."""
from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.errors import SanadError
from app.core.security import decode_access_token
from app.models import User


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise SanadError("unauthorized")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        raise SanadError("unauthorized")
    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError:
        raise SanadError("unauthorized")
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user or not user.is_active:
        raise SanadError("unauthorized")
    return user


def require_roles(*roles: str):
    """Dependency factory enforcing that the current user holds one of `roles`."""

    async def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise SanadError("forbidden")
        return user

    return _dep


async def require_internal_token(
    x_internal_token: str | None = Header(default=None),
) -> None:
    """Guards /internal/* endpoints called by sandbox workers (service role token)."""
    expected = get_settings().internal_service_token
    if not expected or x_internal_token != expected:
        raise SanadError("forbidden")
