"""Heuristic Arabic article splitter for sources without the clean BOE `div.article_item`
markup. Splits a flat block of legal text on `المادة …` headers into article-level records.

This is a best-effort segmenter for adapters whose live DOM/PDF structure is not yet verified;
it is deliberately conservative and unit-tested. Adapters that ship a precise per-site parser
should prefer that over this fallback.
"""
from __future__ import annotations

import re

from app.services.monitoring.adapters.base import Article

# "المادة" + a short ordinal/number label (up to a colon, period, or newline).
_ARTICLE_HEADER = re.compile(r"(المادة\s+[^\n:.]{1,40})")


def split_arabic_articles(text: str) -> list[Article]:
    parts = _ARTICLE_HEADER.split(text)
    articles: list[Article] = []
    # parts = [preamble, header1, body1, header2, body2, ...]
    for i in range(1, len(parts) - 1, 2):
        ref = " ".join(parts[i].split())
        # The header regex stops before the ':'/'.' separator, so strip it off the body head.
        body = " ".join(parts[i + 1].split()).lstrip(":：.،؛- ").strip()
        if ref and body:
            articles.append(Article(article_ref=ref, text_ar=body))
    return articles
