"""Retrieval sufficiency check (spec #2).

Distinguishes "this clause is clean" from "the retriever found nothing useful for this
clause". If the best candidate's cosine distance is beyond the relevance threshold (or there
are no candidates at all), retrieval is insufficient: the clause was never actually assessed
against a relevant article, so it must be flagged rather than silently yielding zero findings.
"""
from __future__ import annotations


def is_retrieval_insufficient(best_distance: float | None, max_distance: float) -> bool:
    """True when nothing relevant was retrieved for the clause.

    best_distance is the smallest cosine distance among the retrieved candidates, or None
    when retrieval returned nothing.
    """
    return best_distance is None or best_distance > max_distance
