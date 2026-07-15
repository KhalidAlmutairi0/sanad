"""Pure-logic tests for the Playwright fetch layer + diff (spec #4).

Browser-free: exercises the routing predicate, the crawl-delay guard, and the set diff. The
real Chromium fetch is validated as an integration step on the deployment, not in unit tests.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from check_law_updates import compute_diff  # noqa: E402
from playwright_fetch import BLOCKED_RESOURCE_TYPES, BrowserFetcher, should_block  # noqa: E402


def test_should_block_heavy_assets():
    for rt in ("image", "font", "stylesheet", "media"):
        assert should_block(rt) is True
    assert BLOCKED_RESOURCE_TYPES == {"image", "font", "stylesheet", "media"}


def test_should_not_block_document_or_data():
    for rt in ("document", "script", "xhr", "fetch"):
        assert should_block(rt) is False


def test_fetch_without_context_manager_raises():
    # Guards against calling fetch() before __enter__ opened the browser (no playwright needed).
    with pytest.raises(RuntimeError):
        BrowserFetcher().fetch("https://laws.boe.gov.sa/x")


def test_respect_delay_first_call_no_sleep():
    f = BrowserFetcher(crawl_delay=10)
    assert f._last_fetch == 0.0
    f._respect_delay()  # first call must not block; just stamps the clock
    assert f._last_fetch > 0.0


def test_compute_diff_added_removed_changed():
    committed = {"1": "alpha", "2": "beta", "3": "gamma"}
    live = {"2": "beta", "3": "gamma-CHANGED", "4": "delta"}
    d = compute_diff("PDPL", committed, live)
    assert d["added"] == ["4"]
    assert d["removed"] == ["1"]
    assert d["changed"] == ["3"]
    assert d["live_count"] == 3 and d["committed_count"] == 3


def test_compute_diff_no_changes():
    m = {"1": "a", "2": "b"}
    d = compute_diff("LABOR", m, dict(m))
    assert d["added"] == [] and d["removed"] == [] and d["changed"] == []
