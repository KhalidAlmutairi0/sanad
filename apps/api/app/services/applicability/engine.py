"""Contract applicability decision engine (pure, fully unit-tested).

Given a contract's signed_date and a regulation article's HUMAN-REVIEWED applicability
classification, decide whether the update applies to that contract and what action is required.
The logic is deliberately trivial and deterministic — the hard/risky part is classifying the
applicability_type (see services/applicability/classify.py + the human gate), NOT this engine.
A wrong 'grandfathered' call could make a bank miss a real remediation deadline, so every flag
this returns is carried to the UI alongside its sources; nothing here is inferred.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

# applicability_type values
RETROACTIVE_WITH_DEADLINE = "retroactive_with_deadline"
PROSPECTIVE_ONLY = "prospective_only"
GRANDFATHERED = "grandfathered"
APPLICABILITY_TYPES = (RETROACTIVE_WITH_DEADLINE, PROSPECTIVE_ONLY, GRANDFATHERED)

# flags
NEEDS_REMEDIATION = "NEEDS_REMEDIATION"
ALREADY_COMPLIANT = "ALREADY_COMPLIANT"
MUST_COMPLY = "MUST_COMPLY"
NOT_APPLICABLE = "NOT_APPLICABLE"
EXEMPT_GRANDFATHERED = "EXEMPT_GRANDFATHERED"


@dataclass(frozen=True)
class Decision:
    flag: str
    due_date: dt.date | None = None  # set only for NEEDS_REMEDIATION


def evaluate(
    signed_date: dt.date,
    applicability_type: str,
    effective_date: dt.date,
    *,
    deadline_date: dt.date | None = None,
    clause_matches_prior_term: bool = False,
) -> Decision:
    """Return the applicability Decision for one (contract, regulation-article) pair.

    clause_matches_prior_term: whether the contract already contains the prior term the
    grandfather clause protects (only consulted for GRANDFATHERED).
    """
    if applicability_type == RETROACTIVE_WITH_DEADLINE:
        if signed_date < effective_date:
            return Decision(NEEDS_REMEDIATION, due_date=deadline_date)
        return Decision(ALREADY_COMPLIANT)

    if applicability_type == PROSPECTIVE_ONLY:
        if signed_date >= effective_date:
            return Decision(MUST_COMPLY)
        return Decision(NOT_APPLICABLE)

    if applicability_type == GRANDFATHERED:
        if signed_date < effective_date and clause_matches_prior_term:
            return Decision(EXEMPT_GRANDFATHERED)
        if signed_date >= effective_date:
            return Decision(MUST_COMPLY)
        return Decision(NOT_APPLICABLE)

    raise ValueError(f"unknown applicability_type: {applicability_type!r}")
