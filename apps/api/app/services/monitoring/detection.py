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
    """Enabled tracked sources [{code, url, adapter, ...}]. Sources default to enabled; set
    `enabled: false` in _sources.yaml to register an adapter without it running in run-check
    (e.g. a new adapter pending live-structure verification). `adapter` defaults to 'boe'."""
    raw = yaml.safe_load(_SOURCES_PATH.read_text(encoding="utf-8"))["sources"]
    out = []
    for s in raw:
        if not s.get("enabled", True):
            continue
        s.setdefault("adapter", "boe")
        out.append(s)
    return out


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
    """BLOCKING: fetch every source via its per-source adapter and parse into a
    {article_ref: text} map. Returns None for a source that failed to fetch or has no adapter
    (kept separate from an empty/'no change' result). Run via asyncio.to_thread — the playwright
    sync API cannot run inside the event loop.

    HTML sources share one persistent headless Chromium (waiting on each adapter's selector);
    PDF sources fetch their own bytes. The browser layer is imported lazily so a deployment
    without playwright/chromium degrades to all-None ('fetch failed') rather than crashing.
    """
    from app.services.monitoring.adapters import get_adapter

    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))

    out: dict[str, dict[str, str] | None] = {}
    html_sources = [s for s in sources if (a := get_adapter(s.get("adapter", "boe"))) and a.kind == "html"]
    other_sources = [s for s in sources if s not in html_sources]

    if html_sources:
        try:
            from playwright_fetch import BrowserFetcher
        except ImportError:
            for s in html_sources:
                out[s["code"]] = None
        else:
            with BrowserFetcher() as fetcher:
                for src in html_sources:
                    adapter = get_adapter(src.get("adapter", "boe"))
                    outcome = fetcher.fetch(src["url"], content_selector=adapter.content_selector)
                    if outcome.error or outcome.html is None:
                        out[src["code"]] = None
                        continue
                    out[src["code"]] = {a.article_ref: a.text_ar for a in adapter.parse(outcome.html)}

    for src in other_sources:
        adapter = get_adapter(src.get("adapter", "boe"))
        if adapter is None or adapter.kind != "pdf":
            out[src["code"]] = None
            continue
        raw = adapter.fetch_pdf(src["url"])
        out[src["code"]] = None if raw is None else {a.article_ref: a.text_ar for a in adapter.parse(raw)}
    return out
