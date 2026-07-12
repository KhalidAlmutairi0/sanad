"""Auth rate limiting (slowapi). Protects /auth/login and /auth/register from brute force.

The app sits behind Caddy, so the real client IP is in X-Forwarded-For; fall back to the
socket peer when the header is absent (direct/local calls). In-memory storage is sufficient
for the single-instance on-prem deployment; move to Redis if the API is ever scaled out.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.errors import SanadError


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip)


async def rate_limit_handler(_: Request, __: Exception):
    # Return SANAD's standard bilingual envelope instead of slowapi's default body.
    return SanadError("rate_limited").to_response()
