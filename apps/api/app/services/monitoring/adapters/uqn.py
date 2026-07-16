"""Umm Al-Qura — the official Saudi gazette (uqn.gov.sa).

robots.txt: `User-agent: *` disallows only /*page=, /*redirect=, /ajax/ (query pagination) and
blocks a few named bots; gazette content is permitted. Twitterbot Crawl-delay is 25, so a
conservative delay is used for this source.

This is the only PDF source: gazette issues are published as PDFs. This adapter fetches the PDF
(stdlib urllib, identifying UA — no browser) and extracts text with pypdf, then falls back to
the heuristic Arabic article splitter. Gazette PDFs are ISSUE-based (many regulations per
issue), so clean article-level segmentation needs a dedicated pass — this adapter is registered
but shipped DISABLED until that segmentation is verified. If pypdf is unavailable it returns [].
"""
from __future__ import annotations

import io
import urllib.request

from app.services.monitoring.adapters._text import split_arabic_articles
from app.services.monitoring.adapters.base import Article, SourceAdapter

_UA = "SANAD-compliance-research/1.0 (regulatory corpus; contact: khalid.a.almutairi0@gmail.com)"
CRAWL_DELAY_SECONDS = 25  # honor the gazette's most conservative published crawl-delay


class UqnAdapter(SourceAdapter):
    name = "uqn"
    robots_status = "allowed — uqn.gov.sa permits content (avoid ?page=/?redirect=/ajax); crawl-delay 25"
    kind = "pdf"
    content_selector = None

    def fetch_pdf(self, url: str) -> bytes | None:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 — official gazette host
                return r.read()
        except Exception:  # noqa: BLE001 — one bad fetch must not abort the run
            return None

    def parse(self, raw: str | bytes) -> list[Article]:
        if not isinstance(raw, (bytes, bytearray)):
            return []
        try:
            from pypdf import PdfReader
        except ImportError:
            return []
        try:
            reader = PdfReader(io.BytesIO(bytes(raw)))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:  # noqa: BLE001 — malformed PDF -> no articles rather than crash
            return []
        return split_arabic_articles(text)
