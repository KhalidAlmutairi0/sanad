"""Bureau of Experts / National legislation database (laws.boe.gov.sa).

This is the primary, VERIFIED adapter — it powers the 14 laws already in the corpus and is the
site the "National Center for Legislation" function actually resolves to. robots.txt permits
/BoeLaws/ law pages with Crawl-delay: 10 (honored by the shared fetcher). Articles render in
`div.article_item` with an `h3.center` header (المادة X); amendment-history popups are dropped.

Parsing reuses scripts/fetch_boe_law.parse_articles (the battle-tested lxml parser) so behaviour
is byte-identical to the existing pipeline.
"""
from __future__ import annotations

import pathlib
import sys

from app.services.monitoring.adapters.base import Article, SourceAdapter

_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[4] / "scripts"


class BoeAdapter(SourceAdapter):
    name = "boe"
    robots_status = "allowed — laws.boe.gov.sa permits /BoeLaws/ pages, Crawl-delay: 10 (honored)"
    kind = "html"
    content_selector = "div.article_item"

    def parse(self, raw: str | bytes) -> list[Article]:
        if str(_SCRIPTS_DIR) not in sys.path:
            sys.path.insert(0, str(_SCRIPTS_DIR))
        from fetch_boe_law import parse_articles

        html = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        return [Article(a["article_ref"], a["article_text_ar"]) for a in parse_articles(html)]
