"""AuthN / AuthZ (test-plan §3b: SEC-10..16)."""
from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models import Contract, Finding, RegulationVersion, User


async def test_protected_endpoint_without_token_is_401(api_client: AsyncClient) -> None:
    resp = await api_client.post("/api/v1/idea-checks", json={"idea_text": "x" * 20})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


async def test_tampered_jwt_is_rejected(api_client: AsyncClient, auth_headers: dict) -> None:
    bad = {"authorization": auth_headers["authorization"] + "tamper"}
    resp = await api_client.get("/api/v1/contracts", headers=bad)
    assert resp.status_code == 401


async def test_role_enforced_on_review(
    api_client: AsyncClient,
    sharia_headers: dict,
    session: AsyncSession,
    contract: Contract,
    regulation_version: RegulationVersion,
) -> None:
    # sharia_board is not allowed to review regulatory findings (require_roles reviewer/admin).
    f = Finding(
        contract_id=contract.id, regulation_version_id=regulation_version.id,
        title_ar="t", severity="high", category="regulatory",
    )
    session.add(f)
    await session.flush()
    resp = await api_client.post(
        f"/api/v1/findings/{f.id}/review", headers=sharia_headers, json={"decision": "accepted"}
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


async def test_login_wrong_password_is_unauthorized(
    api_client: AsyncClient, session: AsyncSession
) -> None:
    u = User(
        email=f"login-{uuid.uuid4()}@sanad.local", display_name="U", role="reviewer",
        password_hash=hash_password("correct-horse"),
    )
    session.add(u)
    await session.flush()
    resp = await api_client.post(
        "/api/v1/auth/login", json={"email": u.email, "password": "wrong"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


def test_password_hash_is_bcrypt_not_plaintext() -> None:
    h = hash_password("s3cret-value")
    assert h != "s3cret-value"
    assert h.startswith("$2")  # bcrypt
    assert verify_password("s3cret-value", h)
    assert not verify_password("wrong", h)
