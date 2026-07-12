"""The production sanitizer guard: refuse SANITIZER_MODE=direct when APP_ENV=production."""
from __future__ import annotations

import pytest

from app.core.config import Settings
from app.workers.main import assert_safe_sanitizer


def _settings(**over: str) -> Settings:
    base = {"app_env": "production", "sanitizer_mode": "sandboxed"}
    base.update(over)
    return Settings(**base)


def test_production_direct_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="direct is forbidden in production"):
        assert_safe_sanitizer(_settings(sanitizer_mode="direct"))


def test_production_sandboxed_is_allowed() -> None:
    assert_safe_sanitizer(_settings(sanitizer_mode="sandboxed"))


def test_development_direct_is_allowed() -> None:
    # `direct` is a legitimate demo/dev fallback for hosts without user namespaces.
    assert_safe_sanitizer(_settings(app_env="local", sanitizer_mode="direct"))
