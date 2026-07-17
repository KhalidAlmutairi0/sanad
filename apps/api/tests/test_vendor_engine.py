"""Vendor evaluation Sandbox-2 engine: gate (Stage 1) + comparison (Stage 2). Pure, JSON-only."""
from __future__ import annotations

from app.services.vendor.compare import annual_recurring, annualized_tco, build_comparison, map_feature
from app.services.vendor.gate import SAMA_OUTSOURCING_CHECKLIST, evaluate_gate

MANDATORY = [r.requirement_id for r in SAMA_OUTSOURCING_CHECKLIST if r.mandatory]


def _all_present() -> list[dict]:
    return [{"requirement_id": r.requirement_id, "status": "present",
             "source_citation": {"document_location": "p.3 §2"}}
            for r in SAMA_OUTSOURCING_CHECKLIST]


def test_gate_passes_when_all_present():
    res = evaluate_gate(_all_present())
    assert res.passed and res.exclusions == []
    assert len(res.scorecard) == len(SAMA_OUTSOURCING_CHECKLIST)


def test_gate_excludes_on_missing_mandatory():
    fields = [f for f in _all_present() if f["requirement_id"] != "SAMA-OUTS-I"]
    fields.append({"requirement_id": "SAMA-OUTS-I", "status": "missing"})
    res = evaluate_gate(fields)
    assert not res.passed
    assert any(e.requirement_id == "SAMA-OUTS-I" for e in res.exclusions)


def test_gate_absent_mandatory_is_treated_missing():
    fields = [f for f in _all_present() if f["requirement_id"] != "SAMA-OUTS-K"]
    res = evaluate_gate(fields)  # K absent from extraction
    assert not res.passed and any(e.section == "K" for e in res.exclusions)


def test_gate_missing_non_mandatory_still_passes():
    fields = [f for f in _all_present() if f["requirement_id"] != "SAMA-OUTS-G"]
    fields.append({"requirement_id": "SAMA-OUTS-G", "status": "missing"})
    assert evaluate_gate(fields).passed  # G is not mandatory


def test_gate_weak_mandatory_does_not_exclude():
    fields = [f for f in _all_present() if f["requirement_id"] != "SAMA-OUTS-N"]
    fields.append({"requirement_id": "SAMA-OUTS-N", "status": "weak"})
    res = evaluate_gate(fields)
    assert res.passed
    assert any(s.section == "N" and s.status == "weak" for s in res.scorecard)


def test_gate_ignores_unknown_requirement():
    fields = _all_present() + [{"requirement_id": "NOT-A-SAMA-SECTION", "status": "present"}]
    assert len(evaluate_gate(fields).scorecard) == len(SAMA_OUTSOURCING_CHECKLIST)


def test_annual_recurring_periods():
    assert annual_recurring([{"amount": 100, "period": "monthly"}]) == 1200
    assert annual_recurring([{"amount": 100, "period": "quarterly"}]) == 400
    assert annual_recurring([{"amount": 100, "period": "weird"}]) == 100  # unknown -> annual


def test_annualized_tco_amortizes_one_time():
    p = {"base_cost": 120000, "setup_cost": 0, "contract_duration_months": 24,
         "recurring_fees": [{"amount": 1000, "period": "monthly"}], "currency": "SAR"}
    c = annualized_tco(p)
    assert c.annualized_tco == 72000.0 and c.currency == "SAR"  # 120000/2 + 12000


def test_annualized_tco_none_when_no_data():
    assert annualized_tco({}).annualized_tco is None
    assert annualized_tco(None).annualized_tco is None


def test_map_feature_taxonomy():
    assert map_feature("encryption") == "encryption"
    assert map_feature("some-vendor-specific-thing") == "other"


def test_comparison_no_composite_score_and_flags_cheapest():
    vendors = [
        {"vendor_id": "A", "pricing_fields": {"base_cost": 100000, "contract_duration_months": 12, "currency": "SAR"}},
        {"vendor_id": "B", "pricing_fields": {"base_cost": 60000, "contract_duration_months": 12, "currency": "SAR"}},
    ]
    comp = build_comparison(vendors)
    assert comp.composite_score is None  # deltas only, never a single score
    tco_row = next(r for r in comp.rows if "TCO" in r.dimension)
    assert "B" in (tco_row.delta_note or "")  # B is cheaper


def test_comparison_flags_currency_mismatch():
    vendors = [
        {"vendor_id": "A", "pricing_fields": {"base_cost": 100000, "contract_duration_months": 12, "currency": "SAR"}},
        {"vendor_id": "B", "pricing_fields": {"base_cost": 60000, "contract_duration_months": 12, "currency": "USD"}},
    ]
    comp = build_comparison(vendors)
    assert comp.currency_mismatch is True
