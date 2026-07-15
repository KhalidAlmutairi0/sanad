"""Retrieval sufficiency check (spec #2)."""
from __future__ import annotations

from app.services.retrieval.relevance import is_retrieval_insufficient

MAX = 0.42


def test_no_candidates_is_insufficient():
    assert is_retrieval_insufficient(None, MAX) is True


def test_best_beyond_threshold_is_insufficient():
    assert is_retrieval_insufficient(0.50, MAX) is True


def test_best_within_threshold_is_sufficient():
    assert is_retrieval_insufficient(0.20, MAX) is False


def test_exactly_at_threshold_is_sufficient():
    # boundary: distance == max is still relevant (only strictly-beyond is insufficient)
    assert is_retrieval_insufficient(0.42, MAX) is False
