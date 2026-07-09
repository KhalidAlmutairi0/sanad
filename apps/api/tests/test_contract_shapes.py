"""Contract conformance against api-contracts.md (concrete assertions).

Covers: the bilingual error envelope + stable codes, pagination shape, and the hard
guarantee that a finding's `citation` is never null. Complements the schemathesis fuzz
harness (test_contract_fuzz.py), which explores the schema more broadly.
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contract, Finding, RegulationVersion


async def test_error_envelope_on_missing_auth(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/contracts")
    assert resp.status_code == 401
    body = resp.json()
    assert set(body["error"]) == {"code", "message_ar", "message_en"}
    assert body["error"]["code"] == "unauthorized"
    # Bilingual, never a single mixed-script string.
    assert body["error"]["message_ar"] and body["error"]["message_en"]


async def test_health_shape(api_client: AsyncClient) -> None:
    resp = await api_client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) >= {"status", "db", "storage", "queue"}


async def test_contracts_list_is_paginated(
    api_client: AsyncClient, auth_headers: dict, contract: Contract
) -> None:
    resp = await api_client.get("/api/v1/contracts?limit=10&offset=0", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and "total" in body
    assert isinstance(body["total"], int)


async def test_finding_citation_is_never_null(
    api_client: AsyncClient,
    auth_headers: dict,
    session: AsyncSession,
    contract: Contract,
    regulation_version: RegulationVersion,
) -> None:
    session.add(
        Finding(
            contract_id=contract.id,
            regulation_version_id=regulation_version.id,
            title_ar="تعارض", severity="high", category="regulatory",
        )
    )
    await session.flush()

    resp = await api_client.get(f"/api/v1/contracts/{contract.id}/findings", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items, "expected at least one finding"
    for item in items:
        assert item["citation"] is not None
        assert item["citation"]["regulation_version_id"]
        assert item["citation"]["article_ref"]
