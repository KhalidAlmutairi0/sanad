"""Retrieval confidence tiers (spec #1).

The reranker emits an ORDERING only, not per-candidate scores, so the numeric confidence
signal is derived from the cosine distances the candidates already carry from vector search:

    sim(x)   = 1 - cosine_distance(x)          # absolute closeness of the cited article
    margin   = sim(selected) - sim(next_best)  # how clearly it beats the strongest competitor

Both are computed from the retrieval/rerank step, never from the generation model — a
low-confidence tier means "the retriever wasn't sure it surfaced the right article", which is
exactly the failure mode this guards against (a wrong-but-cited finding).

Tiers (thresholds are config, provisional until calibrated on the real distribution):
    uncertain : sim(selected) < confidence_min_sim              — barely relevant retrieval
    high      : sim >= confidence_high_sim AND margin >= min_margin — clearly on-point + dominant
    low       : everything in between                            — needs manual verification
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class Confidence:
    tier: str  # 'high' | 'low' | 'uncertain'
    score: float  # sim of the selected article, 0..1
    margin: float  # sim(selected) - sim(next_best); 0.0 when there is no competitor


def classify_confidence(
    selected_distance: float,
    next_best_distance: float | None,
    settings: Settings,
) -> Confidence:
    """Classify a finding's retrieval confidence from cosine distances.

    next_best_distance is None when the selected article was the only candidate (margin 0.0).
    """
    sim = 1.0 - selected_distance
    margin = 0.0 if next_best_distance is None else (1.0 - selected_distance) - (1.0 - next_best_distance)
    # margin simplifies to (next_best_distance - selected_distance) but is written via sim for clarity.

    if sim < settings.confidence_min_sim:
        tier = "uncertain"
    elif sim >= settings.confidence_high_sim and margin >= settings.confidence_min_margin:
        tier = "high"
    else:
        tier = "low"
    return Confidence(tier=tier, score=round(sim, 4), margin=round(margin, 4))
