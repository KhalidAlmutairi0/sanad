from __future__ import annotations

import uuid

from pydantic import BaseModel


class LoginRequest(BaseModel):
    # Plain str, not EmailStr: login only matches against the stored address, and EmailStr
    # rejects reserved TLDs like `.local` (used by on-prem/demo accounts).
    email: str
    password: str


class UserPublic(BaseModel):
    id: uuid.UUID
    display_name: str
    role: str


class LoginResponse(BaseModel):
    token: str
    user: UserPublic
