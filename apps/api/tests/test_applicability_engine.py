"""Applicability decision engine — every branch (correctness-critical)."""
from __future__ import annotations

import datetime as dt

import pytest

from app.services.applicability.engine import (
    ALREADY_COMPLIANT,
    EXEMPT_GRANDFATHERED,
    MUST_COMPLY,
    NEEDS_REMEDIATION,
    NOT_APPLICABLE,
    evaluate,
)

EFF = dt.date(2026, 1, 1)
DEAD = dt.date(2026, 6, 30)
BEFORE = dt.date(2025, 6, 1)
AFTER = dt.date(2026, 3, 1)


def test_retroactive_prior_contract_needs_remediation_with_deadline():
    d = evaluate(BEFORE, "retroactive_with_deadline", EFF, deadline_date=DEAD)
    assert d.flag == NEEDS_REMEDIATION and d.due_date == DEAD


def test_retroactive_new_contract_already_compliant():
    d = evaluate(AFTER, "retroactive_with_deadline", EFF, deadline_date=DEAD)
    assert d.flag == ALREADY_COMPLIANT and d.due_date is None


def test_retroactive_on_effective_date_is_already_compliant():
    # signed exactly on effective_date is NOT "before" -> already compliant
    d = evaluate(EFF, "retroactive_with_deadline", EFF, deadline_date=DEAD)
    assert d.flag == ALREADY_COMPLIANT


def test_prospective_new_contract_must_comply():
    assert evaluate(AFTER, "prospective_only", EFF).flag == MUST_COMPLY


def test_prospective_on_effective_date_must_comply():
    assert evaluate(EFF, "prospective_only", EFF).flag == MUST_COMPLY


def test_prospective_prior_contract_not_applicable():
    assert evaluate(BEFORE, "prospective_only", EFF).flag == NOT_APPLICABLE


def test_grandfathered_prior_with_matching_term_is_exempt():
    d = evaluate(BEFORE, "grandfathered", EFF, clause_matches_prior_term=True)
    assert d.flag == EXEMPT_GRANDFATHERED


def test_grandfathered_prior_without_matching_term_not_applicable():
    # prior contract but it does NOT contain the protected prior term
    d = evaluate(BEFORE, "grandfathered", EFF, clause_matches_prior_term=False)
    assert d.flag == NOT_APPLICABLE


def test_grandfathered_new_contract_must_comply():
    d = evaluate(AFTER, "grandfathered", EFF, clause_matches_prior_term=True)
    assert d.flag == MUST_COMPLY


def test_unknown_type_raises():
    with pytest.raises(ValueError):
        evaluate(AFTER, "nonsense", EFF)
