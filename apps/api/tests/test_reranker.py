"""Reranker ordering logic: applies model ranking, dedupes, and appends dropped candidates."""
from __future__ import annotations

import datetime as dt
import uuid

from app.services.retrieval.reranker import _apply_ranking
from app.services.retrieval.search import Candidate


def _cand(ref: str) -> Candidate:
    return Candidate(
        regulation_version_id=uuid.uuid4(),
        regulation_code="PDPL",
        article_ref=ref,
        article_text_ar=f"text {ref}",
        article_text_en=None,
        source_url="https://x",
        effective_date=None,
        distance=0.1,
    )


def test_ranking_reorders() -> None:
    cands = [_cand("A"), _cand("B"), _cand("C")]
    out = _apply_ranking(cands, [2, 0, 1])
    assert [c.article_ref for c in out] == ["C", "A", "B"]


def test_ranking_dedupes_and_appends_dropped() -> None:
    cands = [_cand("A"), _cand("B"), _cand("C")]
    # model repeats 1 and omits 2 → dedupe, then append the dropped candidate in cosine order
    out = _apply_ranking(cands, [1, 1, 0])
    assert [c.article_ref for c in out] == ["B", "A", "C"]


def test_ranking_ignores_out_of_range() -> None:
    cands = [_cand("A"), _cand("B")]
    out = _apply_ranking(cands, [5, 0, -1, 1])
    assert [c.article_ref for c in out] == ["A", "B"]
