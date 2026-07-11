from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.core.errors import SanadError
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)) -> LoginResponse:
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
