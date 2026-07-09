"""API behaviour + edge cases (test-plan §4 API-06/07, §12 edge)."""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contract, Finding, RegulationVersion


async def test_uploaded_is_idempotent_once_pipeline_started(
    api_client: AsyncClient, auth_headers: dict, contract: Contract
) -> None:
    # contract fixture is already 'reviewing'; a duplicate /uploaded must not re-queue.
    resp = await api_client.post(f"/api/v1/contracts/{contract.id}/uploaded", headers=auth_headers)
    assert resp.status_code == 202
    assert resp.json()["status"] == "reviewing"


async def test_review_conflict_on_double_decision(
    api_client: AsyncClient,
    auth_headers: dict,
    session: AsyncSession,
    contract: Contract,
    regulation_version: RegulationVersion,
) -> None:
    f = Finding(
        contract_id=contract.id, regulation_version_id=regulation_version.id,
        title_ar="t", severity="critical", category="regulatory",
    )
    session.add(f)
    await session.flush()

    first = await api_client.post(
        f"/api/v1/findings/{f.id}/review", headers=auth_headers, json={"decision": "accepted"}
    )
    assert first.status_code == 200
    second = await api_client.post(
        f"/api/v1/findings/{f.id}/review", headers=auth_headers, json={"decision": "rejected"}
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "review_conflict"


async def test_contract_with_zero_findings_summary_and_radar_go(
    api_client: AsyncClient, auth_headers: dict, contract: Contract
) -> None:
    detail = await api_client.get(f"/api/v1/contracts/{contract.id}", headers=auth_headers)
    assert detail.status_code == 200
    summary = detail.json()["findings_summary"]
    assert summary == {"critical": 0, "high": 0, "medium": 0, "low": 0, "pending": 0}

    radar = await api_client.get(f"/api/v1/contracts/{contract.id}/radar", headers=auth_headers)
    assert radar.status_code == 200
    body = radar.json()
    assert body["verdict"] == "GO"
    assert body["killers"] == []


async def test_score_stop_radar_after_accepting_critical(
    api_client: AsyncClient,
    auth_headers: dict,
    session: AsyncSession,
    contract: Contract,
    regulation_version: RegulationVersion,
) -> None:
    f = Finding(
        contract_id=contract.id, regulation_version_id=regulation_version.id,
        title_ar="حرج", severity="critical", category="regulatory",
    )
    session.add(f)
    await session.flush()
    await api_client.post(
        f"/api/v1/findings/{f.id}/review", headers=auth_headers, json={"decision": "accepted"}
    )
    radar = await api_client.get(f"/api/v1/contracts/{contract.id}/radar", headers=auth_headers)
    assert radar.json()["verdict"] == "STOP"
    detail = await api_client.get(f"/api/v1/contracts/{contract.id}", headers=auth_headers)
    assert detail.json()["readiness_score"] == 60  # 100 - 40 (one accepted critical)
