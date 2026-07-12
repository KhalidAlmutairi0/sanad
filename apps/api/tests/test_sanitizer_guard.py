"""The production sanitizer guard: refuse SANITIZER_MODE=direct when APP_ENV=production.

Settings reads from the environment by alias (APP_ENV, SANITIZER_MODE), so the guard is
exercised by setting env vars, not by passing field-name kwargs (which pydantic-settings
ignores under alias config).
"""
from __future__ import annotations

import pytest

from app.core.config import Settings
from app.workers.main import assert_safe_sanitizer


def _settings(monkeypatch: pytest.MonkeyPatch, app_env: str, sanitizer_mode: str) -> Settings:
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("SANITIZER_MODE", sanitizer_mode)
    return Settings()


def test_production_direct_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings(monkeypatch, "production", "direct")
    with pytest.raises(RuntimeError, match="direct is forbidden in production"):
        assert_safe_sanitizer(settings)


def test_production_sandboxed_is_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    assert_safe_sanitizer(_settings(monkeypatch, "production", "sandboxed"))


def test_development_direct_is_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    # `direct` is a legitimate demo/dev fallback for hosts without user namespaces.
    assert_safe_sanitizer(_settings(monkeypatch, "local", "direct"))
