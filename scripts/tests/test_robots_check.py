"""robots.txt evaluator + allowlist check (pure, network-free)."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from check_allowlist_robots import check_domain  # noqa: E402
from robots_check import path_allowed  # noqa: E402


def test_no_disallow_allows_everything():
    assert path_allowed("User-agent: *\n", "/anything") is True


def test_empty_disallow_allows_everything():
    assert path_allowed("User-agent: *\nDisallow:", "/x") is True


def test_disallow_root_blocks_everything():
    assert path_allowed("User-agent: *\nDisallow: /", "/x") is False


def test_prefix_disallow_blocks_only_that_path():
    robots = "User-agent: *\nDisallow: /search/\nDisallow: /ajax/"
    assert path_allowed(robots, "/BoeLaws/Laws/x") is True
    assert path_allowed(robots, "/search/results") is False


def test_allow_overrides_longer_disallow():
    robots = "User-agent: *\nDisallow: /docs/\nAllow: /docs/public/"
    assert path_allowed(robots, "/docs/private") is False
    assert path_allowed(robots, "/docs/public/x") is True


def test_named_agent_group_falls_back_to_star():
    robots = "User-agent: Baiduspider\nDisallow: /\n\nUser-agent: *\nDisallow: /ajax/"
    # our generic UA uses the '*' group, not the Baidu block
    assert path_allowed(robots, "/", user_agent="SANAD-bot") is True
    assert path_allowed(robots, "/ajax/x", user_agent="SANAD-bot") is False


def test_check_domain_reports_disallowed():
    r = check_domain("example.gov.sa", "/x", "User-agent: *\nDisallow: /")
    assert r["allowed"] is False


def test_check_domain_missing_robots_is_allowed_unknown():
    r = check_domain("example.gov.sa", "/x", None)
    assert r["allowed"] is None
