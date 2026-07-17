# NOTE: no `from __future__ import annotations` here. slowapi's @limiter.limit wraps the
# endpoint, and FastAPI then cannot resolve stringized body annotations against this module's
# globals — it would mis-read `body: LoginRequest` as a query param (422). Real annotations
# keep the Pydantic body working under the rate-limit decorator.
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

import secrets

from app.core.deps import get_session
from app.core.errors import SanadError
from app.core.ratelimit import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Invite, User
from app.schemas.auth import LoginRequest, LoginResponse, UserPublic
from app.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])

# Shared demo identity for public "try it now" access. Role is reviewer, so it can run
# Contract Review + Idea Check but never reaches admin / source-verification endpoints.
GUEST_EMAIL = "guest@sanad.local"


class RegisterRequest(BaseModel):
    email: str
    password: str
    code: str
    display_name: str | None = None


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, session: AsyncSession = Depends(get_session)) -> LoginResponse:
    user = (
        await session.execute(select(User).where(User.email == str(body.email)))
    ).scalar_one_or_none()
    # Same error whether the email is unknown or the password is wrong (no user enumeration).
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise SanadError("unauthorized", "بيانات الدخول غير صحيحة", "Your email or password is incorrect")
    token = create_access_token(user_id=str(user.id), role=user.role)
    return LoginResponse(
        token=token,
        user=UserPublic(id=user.id, display_name=user.display_name, role=user.role),
    )


@router.post("/guest", response_model=LoginResponse)
@limiter.limit("20/minute")
async def guest(request: Request, session: AsyncSession = Depends(get_session)) -> LoginResponse:
    """Public demo access: sign in as the shared guest reviewer (created on first use).
    No password is accepted from the client; the account is provisioned server-side."""
    user = (
        await session.execute(select(User).where(User.email == GUEST_EMAIL))
    ).scalar_one_or_none()
    if not user:
        user = User(
            email=GUEST_EMAIL,
            display_name="ضيف تجريبي",
            role="guest",
            password_hash=hash_password(secrets.token_urlsafe(32)),
        )
        session.add(user)
        await session.flush()
        await write_audit(session, actor=str(user.id), action="guest_provisioned", verdict="n-a",
                          detail={"role": "guest"})
        await session.commit()
    if not user.is_active:
        raise SanadError("unauthorized", "الوصول التجريبي معطّل حالياً", "Guest access is disabled")
    token = create_access_token(user_id=str(user.id), role=user.role)
    return LoginResponse(
        token=token,
        user=UserPublic(id=user.id, display_name=user.display_name, role=user.role),
    )


@router.post("/register", response_model=LoginResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, session: AsyncSession = Depends(get_session)) -> LoginResponse:
    email = body.email.strip().lower()
    invite = (
        await session.execute(select(Invite).where(Invite.code == body.code, Invite.used == False))  # noqa: E712
    ).scalar_one_or_none()
    if not invite:
        raise SanadError("validation_failed", "رمز الدعوة غير صالح أو مستخدم", "Invalid or already used invite code")
    if invite.email and invite.email != email:
        raise SanadError("validation_failed", "هذا الرمز مخصّص لبريد آخر", "This code is for a different email")
    exists = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if exists:
        raise SanadError("validation_failed", "الحساب موجود مسبقاً", "An account with this email already exists")
    if len(body.password) < 6:
        raise SanadError("validation_failed", "كلمة المرور قصيرة", "Password is too short")

    user = User(
        email=email,
        display_name=body.display_name or email.split("@")[0],
        role=invite.role,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.flush()
    invite.used = True
    invite.used_by = user.id
    await write_audit(session, actor=str(user.id), action="user_registered", verdict="n-a",
                      detail={"role": invite.role, "via_code": True})
    await session.commit()

    token = create_access_token(user_id=str(user.id), role=user.role)
    return LoginResponse(
        token=token,
        user=UserPublic(id=user.id, display_name=user.display_name, role=user.role),
    )
