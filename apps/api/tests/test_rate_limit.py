"""Auth endpoints are rate-limited (brute-force protection)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_is_rate_limited(api_client: AsyncClient) -> None:
    from app.core.ratelimit import limiter

    limiter.enabled = True
    body = {"email": "nobody@sanad.local", "password": "wrong"}
    statuses = []
    for _ in range(6):
        r = await api_client.post("/api/v1/auth/login", json=body)
        statuses.append(r.status_code)

    # First 5 are allowed through to normal auth handling (401 for bad creds); the 6th trips
    # the limiter and returns the SANAD envelope with the stable rate_limited code.
    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429
    last = await api_client.post("/api/v1/auth/login", json=body)
    assert last.json()["error"]["code"] == "rate_limited"
