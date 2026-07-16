"""Per-source adapter contract for regulatory monitoring.

Saudi regulator sites differ structurally (HTML DOM shape, PDF vs HTML, Arabic encoding), so
fetching is NOT one generic crawler — each source has an adapter that knows its layout and how
to turn a page into article-level records. Everything downstream (hashing, diff, pgvector
storage, retrieval, the human verify gate) is source-agnostic and unchanged.

An adapter declares:
  * name           — matches the `adapter:` key in _sources.yaml
  * robots_status  — the checked robots.txt outcome (documentation of due diligence)
  * kind           — 'html' (fetched with the shared headless Chromium) or 'pdf'
  * content_selector — for html: the element to wait for before reading the DOM
  * parse(raw)     — raw page (html str or pdf bytes) -> [Article], split by article_ref
  * fetch_pdf(url) — pdf adapters only: fetch the document bytes

Adapters never write anything; they only produce candidate article text for the diff stage.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Article:
    """One regulation article: the unit of chunking, hashing, and citation."""

    article_ref: str
    text_ar: str


class SourceAdapter:
    name: str = ""
    robots_status: str = ""
    kind: str = "html"  # 'html' | 'pdf'
    content_selector: str | None = None  # html: element to wait for

    def parse(self, raw: str | bytes) -> list[Article]:
        raise NotImplementedError

    def fetch_pdf(self, url: str) -> bytes | None:
        raise NotImplementedError(f"{self.name}: fetch_pdf only applies to pdf adapters")
