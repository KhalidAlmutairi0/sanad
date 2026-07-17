"""Stage 2 — vendor comparison (pure, JSON-only). Runs only on vendors that passed Stage 1.

Normalizes pricing to an annualized total cost of ownership, maps features to a shared taxonomy,
and produces a side-by-side table of DELTAS. Deliberately NO single composite score — the system
surfaces differences; the human makes the tradeoff. Operates only on Sandbox-1 JSON.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Recurring-fee period -> occurrences per year.
_PERIOD_PER_YEAR = {"monthly": 12, "quarterly": 4, "semiannual": 2, "annual": 1, "yearly": 1}

# Shared feature taxonomy (extracted feature_category maps onto this; unknowns -> 'other').
FEATURE_TAXONOMY = (
    "data_residency", "encryption", "access_control", "audit_logging", "sla_uptime",
    "incident_response", "business_continuity", "reporting", "integration_api", "support", "other",
)


def annual_recurring(recurring_fees: list[dict] | None) -> float:
    """Sum recurring fees converted to an annual figure. Unknown periods count as annual (×1)."""
    total = 0.0
    for fee in recurring_fees or []:
        amount = fee.get("amount")
        if not isinstance(amount, (int, float)):
            continue
        per_year = _PERIOD_PER_YEAR.get(str(fee.get("period", "")).lower(), 1)
        total += float(amount) * per_year
    return total


@dataclass
class NormalizedCost:
    annualized_tco: float | None
    currency: str | None
    breakdown: dict


def annualized_tco(pricing: dict | None) -> NormalizedCost:
    """Annualized total cost of ownership: (setup + base, amortized over the term) + annual
    recurring. Returns None when there's not enough data to compute — never a guessed number."""
    if not pricing:
        return NormalizedCost(None, None, {})
    base = pricing.get("base_cost")
    setup = pricing.get("setup_cost")
    months = pricing.get("contract_duration_months")
    rec = annual_recurring(pricing.get("recurring_fees"))

    one_time = (float(base) if isinstance(base, (int, float)) else 0.0) + \
               (float(setup) if isinstance(setup, (int, float)) else 0.0)
    years = (months / 12) if isinstance(months, (int, float)) and months else None

    if years:
        tco = one_time / years + rec  # amortize one-time over the term, add annual recurring
    elif rec or one_time:
        tco = rec + one_time  # no term given -> annual recurring + one-time as-is
    else:
        tco = None
    return NormalizedCost(
        annualized_tco=round(tco, 2) if tco is not None else None,
        currency=pricing.get("currency"),
        breakdown={"one_time": one_time, "annual_recurring": rec, "term_years": years},
    )


def map_feature(category: str | None) -> str:
    c = (category or "").strip().lower()
    return c if c in FEATURE_TAXONOMY else "other"


@dataclass
class ComparisonRow:
    dimension: str
    values: dict          # vendor_id -> value
    delta_note: str | None = None  # e.g. cheapest/most-expensive, or currency-mismatch warning


@dataclass
class Comparison:
    vendor_ids: list[str]
    rows: list[ComparisonRow]
    currency_mismatch: bool = False
    composite_score: None = field(default=None, init=False)  # explicitly none — deltas only


def build_comparison(vendors: list[dict]) -> Comparison:
    """vendors: [{vendor_id, pricing_fields, feature_fields, self_reported_background}, ...]
    (all Stage-1 passers). Returns a dimensions×vendors table of deltas."""
    ids = [v.get("vendor_id", f"vendor-{i}") for i, v in enumerate(vendors)]
    rows: list[ComparisonRow] = []

    # Pricing: annualized TCO per vendor.
    costs = {vid: annualized_tco(v.get("pricing_fields")) for vid, v in zip(ids, vendors)}
    tco_vals = {vid: c.annualized_tco for vid, c in costs.items()}
    currencies = {c.currency for c in costs.values() if c.currency}
    mismatch = len(currencies) > 1
    comparable = {k: v for k, v in tco_vals.items() if v is not None}
    delta = None
    if comparable and not mismatch:
        cheapest = min(comparable, key=comparable.get)
        delta = f"الأقل تكلفة: {cheapest}"
    elif mismatch:
        delta = "عملات مختلفة — لا يمكن المقارنة المباشرة دون سعر صرف"
    rows.append(ComparisonRow("التكلفة السنوية (TCO)", tco_vals, delta))

    # Contract terms.
    rows.append(ComparisonRow("مدة العقد (شهور)",
                              {vid: (v.get("pricing_fields") or {}).get("contract_duration_months")
                               for vid, v in zip(ids, vendors)}))
    rows.append(ComparisonRow("تجديد تلقائي",
                              {vid: (v.get("pricing_fields") or {}).get("auto_renewal")
                               for vid, v in zip(ids, vendors)}))

    # Features: presence per taxonomy category.
    per_vendor_feats: dict[str, dict[str, str]] = {}
    for vid, v in zip(ids, vendors):
        m: dict[str, str] = {}
        for feat in v.get("feature_fields") or []:
            m[map_feature(feat.get("feature_category"))] = feat.get("included_or_addon", "not_offered")
        per_vendor_feats[vid] = m
    covered = sorted({cat for fm in per_vendor_feats.values() for cat in fm})
    for cat in covered:
        rows.append(ComparisonRow(
            f"ميزة: {cat}",
            {vid: per_vendor_feats[vid].get(cat, "not_offered") for vid in ids},
        ))

    return Comparison(vendor_ids=ids, rows=rows, currency_mismatch=mismatch)
