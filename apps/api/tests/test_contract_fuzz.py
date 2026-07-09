"""Schemathesis contract-fuzz harness (api-contracts.md §4 / test-plan.md API-01).

Property: the API's runtime responses conform to its own OpenAPI schema and never return an
unhandled 500 on generated input. Runs in-process against the ASGI app (no live server).

Scope now: the public, side-effect-free surface (health), plus a schema-publication guard.
To extend to authenticated, stateful fuzzing, register auth and point it at a seeded token
(see EXTENSION note at the bottom). Kept defensive so a schemathesis version/API change
skips rather than breaking collection.
"""
from __future__ import annotations

import pytest

schemathesis = pytest.importorskip("schemathesis")

from app.main import app  # noqa: E402


def test_openapi_declares_the_core_surface() -> None:
    # Guards against silent route/contract loss: documented endpoints must be published.
    paths = set(app.openapi()["paths"])
    expected = {
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/contracts",
        "/api/v1/contracts/{contract_id}/findings",
        "/api/v1/findings/{finding_id}/review",
        "/api/v1/idea-checks",
    }
    missing = expected - paths
    assert not missing, f"OpenAPI is missing documented endpoints: {sorted(missing)}"


def test_health_response_conforms_to_schema() -> None:
    # Fuzz-validate the one safe, unauthenticated operation against its declared schema.
    # Defensive: skip if this schemathesis version exposes a different operation API.
    try:
        schema = schemathesis.from_asgi("/openapi.json", app)
        operation = schema["/api/v1/health"]["GET"]
        case = operation.make_case()
    except Exception as exc:  # noqa: BLE001 — harness compatibility, not a product failure
        pytest.skip(f"schemathesis operation API differs here: {exc!r}")
    case.call_and_validate()


def _seed_reviewer_token() -> str | None:
    """Log in as the seeded reviewer through the ASGI app to obtain a real Bearer token.
    Returns None if the DB is not seeded (so the auth fuzz skips instead of failing)."""
    import os

    import anyio
    import httpx

    creds = {
        "email": os.environ.get("SEED_REVIEWER_EMAIL", "reviewer@sanad.local"),
        "password": os.environ.get("SEED_DEFAULT_PASSWORD", "sanad-dev-password"),
    }

    async def _run() -> str | None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/v1/auth/login", json=creds)
            return r.json().get("token") if r.status_code == 200 else None

    try:
        return anyio.run(_run)
    except Exception:  # noqa: BLE001 — no seeded DB reachable
        return None


def test_authenticated_read_surface_conforms() -> None:
    """Fuzz-validate the parameterless read endpoints under a real token. Skips if the DB is
    not seeded or if this schemathesis version exposes a different operation API; a genuine
    schema-conformance failure still surfaces (AssertionError is not swallowed)."""
    token = _seed_reviewer_token()
    if not token:
        pytest.skip("seeded reviewer login unavailable (DB not seeded)")
    headers = {"authorization": f"Bearer {token}"}
    for path in ("/api/v1/contracts", "/api/v1/idea-checks"):
        try:
            schema = schemathesis.from_asgi("/openapi.json", app)
            case = schema[path]["GET"].make_case()
        except (AttributeError, TypeError, KeyError) as exc:
            pytest.skip(f"schemathesis operation API differs here: {exc!r}")
        case.headers = headers
        case.call_and_validate()
