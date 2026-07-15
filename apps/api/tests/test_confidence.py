"""Retrieval confidence tier classification (spec #1)."""
from __future__ import annotations

from app.core.config import get_settings
from app.services.retrieval.confidence import classify_confidence


def _s():
    return get_settings()


def test_high_when_close_and_dominant():
    # sim = 0.80 (dist 0.20), next-best sim 0.70 -> margin 0.10
    c = classify_confidence(0.20, 0.30, _s())
    assert c.tier == "high"
    assert c.score == 0.80
    assert round(c.margin, 2) == 0.10


def test_uncertain_when_barely_relevant():
    # sim = 0.55 (dist 0.45) is below the irrelevance floor regardless of margin
    c = classify_confidence(0.45, 0.90, _s())
    assert c.tier == "uncertain"


def test_low_when_relevant_but_no_margin():
    # sim = 0.75 (good) but next-best is just as close -> tiny margin -> low
    c = classify_confidence(0.25, 0.255, _s())
    assert c.tier == "low"


def test_low_when_middling_sim():
    # sim = 0.66 sits between min and high thresholds -> low even with margin
    c = classify_confidence(0.34, 0.60, _s())
    assert c.tier == "low"


def test_single_candidate_has_zero_margin():
    c = classify_confidence(0.20, None, _s())
    assert c.margin == 0.0
    # sim 0.80 >= high_sim but margin 0 < min_margin -> not high
    assert c.tier == "low"
