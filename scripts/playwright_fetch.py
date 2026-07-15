"""Playwright-based fetch for monitoring detection (spec #4).

Gazette pages (laws.boe.gov.sa) and some regulator sites block plain HTTP clients by request
signature, and often populate article content after the initial load. This replaces the raw
urllib/httpx fetch used by the detection loop with one persistent headless Chromium:

  * a single browser + context reused across every tracked law in a run (not relaunched per URL)
  * sequential fetching that enforces the crawl-delay between requests
  * heavy assets (images, fonts, css, media) blocked via request routing — only DOM text is read
  * wait_for_selector on the actual article-content selector before reading content (not just
    networkidle), because the gazette renders articles after first paint
  * each URL wrapped so one source timing out or changing markup never aborts the whole run;
    fetch failures are reported on a separate channel from "content changed"
  * a realistic user agent and ar-SA locale on the context

Everything downstream (parse_articles, diffing, candidate submission, the human-verify gate,
staleness timestamps) is unchanged — only the fetch mechanism differs.

The `playwright` import is lazy so the pure helpers (and the modules that import this one) work
without the browser installed; only `BrowserFetcher.__enter__` requires it.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

CRAWL_DELAY_SECONDS = 10
DEFAULT_CONTENT_SELECTOR = "div.article_item"  # matches parse_articles() in fetch_boe_law.py
# Resource types with no bearing on article text — aborted to keep the fetch light.
BLOCKED_RESOURCE_TYPES = frozenset({"image", "font", "stylesheet", "media"})
USER_AGENT = (
    "SANAD-compliance-research/1.0 (regulatory corpus; contact: khalid.a.almutairi0@gmail.com)"
)
LOCALE = "ar-SA"


def should_block(resource_type: str) -> bool:
    """True for asset types we abort during routing (pure, unit-testable)."""
    return resource_type in BLOCKED_RESOURCE_TYPES


@dataclass
class FetchOutcome:
    """A fetch result. `error` is set (and `html` None) on failure — a distinct channel from a
    successful fetch that later diffs as changed, so failures are never read as content changes."""

    url: str
    html: str | None
    error: str | None


class BrowserFetcher:
    """Context manager owning one headless Chromium for a whole detection run.

    with BrowserFetcher() as fetcher:
        for url in urls:
            outcome = fetcher.fetch(url)
    """

    def __init__(
        self,
        *,
        content_selector: str = DEFAULT_CONTENT_SELECTOR,
        crawl_delay: float = CRAWL_DELAY_SECONDS,
        nav_timeout_ms: int = 30000,
    ) -> None:
        self._content_selector = content_selector
        self._crawl_delay = crawl_delay
        self._nav_timeout_ms = nav_timeout_ms
        self._last_fetch = 0.0
        self._pw = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "BrowserFetcher":
        from playwright.sync_api import sync_playwright  # lazy: only needed to actually fetch

        self._pw = sync_playwright().start()
        # --no-sandbox / --disable-dev-shm-usage: required when Chromium runs in a container.
        self._browser = self._pw.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        self._context = self._browser.new_context(user_agent=USER_AGENT, locale=LOCALE)
        self._context.route("**/*", self._route)
        return self

    def __exit__(self, *exc: object) -> None:
        for closer in (self._context, self._browser):
            try:
                if closer is not None:
                    closer.close()
            except Exception:  # noqa: BLE001 — teardown must never mask the real error
                pass
        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:  # noqa: BLE001
                pass

    def _route(self, route) -> None:  # noqa: ANN001 — playwright Route
        if should_block(route.request.resource_type):
            route.abort()
        else:
            route.continue_()

    def _respect_delay(self) -> None:
        """Enforce sequential fetching with the crawl-delay (no-op before the first fetch)."""
        if self._last_fetch:
            elapsed = time.monotonic() - self._last_fetch
            if elapsed < self._crawl_delay:
                time.sleep(self._crawl_delay - elapsed)
        self._last_fetch = time.monotonic()

    def fetch(self, url: str) -> FetchOutcome:
        if self._context is None:
            raise RuntimeError("BrowserFetcher must be used as a context manager")
        self._respect_delay()
        page = self._context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self._nav_timeout_ms)
            page.wait_for_selector(self._content_selector, timeout=self._nav_timeout_ms)
            return FetchOutcome(url=url, html=page.content(), error=None)
        except Exception as e:  # noqa: BLE001 — one bad source must not abort the run
            return FetchOutcome(url=url, html=None, error=f"{type(e).__name__}: {e}")
        finally:
            try:
                page.close()
            except Exception:  # noqa: BLE001
                pass
