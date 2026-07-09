from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: uuid.UUID
    display_name: str
    role: str


class LoginResponse(BaseModel):
    token: str
    user: UserPublic
