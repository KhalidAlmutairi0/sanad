"""Monitoring change detection (spec #5, free stage).

Pure text comparison between the live gazette and the committed corpus — NO LLM, zero tokens.
The browser fetch (spec #4) lives in scripts/playwright_fetch.py and is imported lazily so this
module (and its pure helpers) load without playwright/chromium installed.

`fetch_live_articles` is the only browser-touching function; tests monkeypatch it to inject
canned live article maps, so the whole run-check orchestration is exercised without a browser.
"""
from __future__ import annotations

import pathlib
import sys

import yaml

# scripts/ is copied to /app/scripts in the API image (see apps/api/Dockerfile). Resolve it
# relative to this file so both container and repo layouts work.
_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[3] / "scripts"
_SOURCES_PATH = _SCRIPTS_DIR / "seed_data" / "corpus" / "_sources.yaml"

CHANGE_TYPES = ("new_article", "amended", "repealed")


def _norm(text: str) -> str:
    return " ".join(text.split())


def load_sources() -> list[dict]:
    """[{code, url, corpus_file}] for every tracked law."""
    return yaml.safe_load(_SOURCES_PATH.read_text(encoding="utf-8"))["sources"]


def build_changes(committed: dict[str, str], live: dict[str, str]) -> list[dict]:
    """Pure diff between two article_ref -> text maps. Each change carries the text to show in
    the UI (the LIVE text for new/amended, the COMMITTED text for a repeal)."""
    changes: list[dict] = []
    for ref in sorted(set(live) - set(committed)):
        changes.append({"article_ref": ref, "change_type": "new_article", "text": live[ref]})
    for ref in sorted(set(committed) - set(live)):
        changes.append({"article_ref": ref, "change_type": "repealed", "text": committed[ref]})
    for ref in sorted(set(live) & set(committed)):
        if _norm(live[ref]) != _norm(committed[ref]):
            changes.append({"article_ref": ref, "change_type": "amended", "text": live[ref]})
    return changes


def fetch_live_articles(sources: list[dict]) -> dict[str, dict[str, str] | None]:
    """BLOCKING: fetch every source with one persistent headless Chromium and parse its
    articles into a {article_ref: text} map. Returns None for a source that failed to fetch
    (kept separate from an empty/'no change' result). Run via asyncio.to_thread — the
    playwright sync API cannot run inside the event loop.

    Lazily imports the scripts/ fetch layer; a missing browser surfaces as all-None (run-check
    reports "fetch failed") rather than crashing.
    """
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))
    try:
        from fetch_boe_law import parse_articles
        from playwright_fetch import BrowserFetcher
    except ImportError:
        return {s["code"]: None for s in sources}

    out: dict[str, dict[str, str] | None] = {}
    with BrowserFetcher() as fetcher:
        for src in sources:
            outcome = fetcher.fetch(src["url"])
            if outcome.error or outcome.html is None:
                out[src["code"]] = None
                continue
            out[src["code"]] = {
                a["article_ref"]: a["article_text_ar"] for a in parse_articles(outcome.html)
            }
    return out
