"""Ministry of Justice (moj.gov.sa).

robots.txt: `User-agent: *` with no Disallow — automated access is permitted.

NOTE: primary law texts (e.g. the Civil Transactions Law) are already sourced via the BOE
adapter; MOJ's own site publishes judicial circulars/updates whose article-level DOM is NOT
yet verified. This adapter fetches the page (shared Chromium) and falls back to the heuristic
Arabic article splitter. It is registered but shipped DISABLED in _sources.yaml until its
selector/parse is verified against live pages.
"""
from __future__ import annotations

from app.services.monitoring.adapters._text import split_arabic_articles
from app.services.monitoring.adapters.base import Article, SourceAdapter


class MojAdapter(SourceAdapter):
    name = "moj"
    robots_status = "allowed — moj.gov.sa robots.txt has no Disallow for User-agent: *"
    kind = "html"
    content_selector = "main"  # unverified; adjust to the live article container before enabling

    def parse(self, raw: str | bytes) -> list[Article]:
        from lxml import html as lxml_html

        page = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        doc = lxml_html.fromstring(page)
        # Prefer the main content region; fall back to the whole document text.
        nodes = doc.xpath("//main") or [doc]
        text = "\n".join(n.text_content() for n in nodes)
        return split_arabic_articles(text)
