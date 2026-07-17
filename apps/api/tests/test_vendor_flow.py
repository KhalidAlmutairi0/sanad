"""Vendor evaluation orchestration + API: extract→gate, results assembly, run-comparison trigger."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import VendorEvaluation, VendorSubmission
from app.services.vendor.gate import SAMA_OUTSOURCING_CHECKLIST
from app.services.vendor.orchestrate import compute_results, extract_and_gate


def _extraction(all_present: bool = True, vendor: str = "V") -> dict:
    fields = []
    for r in SAMA_OUTSOURCING_CHECKLIST:
        status = "present"
        if not all_present and r.requirement_id == "SAMA-OUTS-I":
            status = "missing"
        fields.append({"requirement_id": r.requirement_id, "status": status,
                       "source_citation": {"document_location": "p.2"}})
    return {"vendor_id": vendor, "compliance_fields": fields,
            "pricing_fields": {"base_cost": 100000, "contract_duration_months": 12, "currency": "SAR"},
            "feature_fields": [{"feature_category": "encryption", "included_or_addon": "included"}],
            "self_reported_background": {"label": "AS_CLAIMED_BY_VENDOR", "years_experience": 5},
            "security_flags": []}


@pytest.mark.asyncio
async def test_extract_and_gate_stores_json_and_passes(session: AsyncSession) -> None:
    ev = VendorEvaluation(title="RFP", status="comparing")
    session.add(ev)
    await session.flush()
    sub = VendorSubmission(evaluation_id=ev.id, vendor_name="Acme", status="uploaded",
                           raw_object_key="vendor/x/raw")
    session.add(sub)
    await session.flush()

    await extract_and_gate(session, sub, "a normal proposal text", actor="analysis")
    assert sub.status == "extracted"
    assert sub.extraction is not None and sub.extraction["self_reported_background"]["label"] == "AS_CLAIMED_BY_VENDOR"
    assert sub.stage1_passed is True  # offline stub extracts all-present


@pytest.mark.asyncio
async def test_compute_results_excludes_and_compares(session: AsyncSession) -> None:
    ev = VendorEvaluation(title="RFP", status="done")
    session.add(ev)
    await session.flush()
    good = VendorSubmission(evaluation_id=ev.id, vendor_name="Good", status="extracted",
                            raw_object_key="k1", extraction=_extraction(True, "Good"),
                            stage1_passed=True)
    bad = VendorSubmission(evaluation_id=ev.id, vendor_name="Bad", status="extracted",
                           raw_object_key="k2", extraction=_extraction(False, "Bad"),
                           stage1_passed=False)
    session.add_all([good, bad])
    await session.flush()

    res = compute_results(ev.title, ev.status, [good, bad])
    by_name = {v["vendor_name"]: v for v in res["vendors"]}
    assert by_name["Good"]["stage1_passed"] is True
    assert by_name["Bad"]["stage1_passed"] is False
    assert any(e["section"] == "I" for e in by_name["Bad"]["exclusions"])
    # Stage 2 only includes the passer, and never a composite score
    assert res["comparison"]["vendor_ids"] == ["Good"]
    assert res["comparison"]["composite_score"] is None
    assert res["banner"]


@pytest.mark.asyncio
async def test_run_comparison_requires_submissions_and_is_explicit(
    api_client: AsyncClient, session: AsyncSession, auth_headers: dict[str, str]
) -> None:
    created = await api_client.post("/api/v1/vendor-evaluations", headers=auth_headers,
                                    json={"title": "Cloud RFP"})
    assert created.status_code == 201, created.text
    eval_id = created.json()["id"]

    # no submissions yet -> run-comparison refused (explicit, never auto-runs)
    empty = await api_client.post(f"/api/v1/vendor-evaluations/{eval_id}/run-comparison", headers=auth_headers)
    assert empty.status_code in (400, 422)

    # add a submission directly (the API's add_submission mints a presigned upload URL, which
    # needs a reachable public MinIO — out of scope for this unit test).
    session.add(VendorSubmission(evaluation_id=uuid.UUID(eval_id), vendor_name="Acme",
                                 status="uploaded", raw_object_key="vendor/x/raw"))
    await session.flush()

    run = await api_client.post(f"/api/v1/vendor-evaluations/{eval_id}/run-comparison", headers=auth_headers)
    assert run.status_code == 202 and run.json()["status"] == "comparing"

    got = await api_client.get(f"/api/v1/vendor-evaluations/{eval_id}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["status"] == "comparing" and "banner" in got.json()
