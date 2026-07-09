"""Health reflects real dependency status (test-plan §11 REL-01). No live deps needed —
the per-dependency checks are patched to simulate outages."""
from __future__ import annotations

import pytest

from app.routers import health


async def test_health_ok_when_all_up(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _true() -> bool:
        return True

    monkeypatch.setattr(health, "_db_ok", _true)
    monkeypatch.setattr(health, "_queue_ok", _true)
    monkeypatch.setattr(health, "storage_healthy", lambda: True)
    body = await health.health()
    assert body == {"status": "ok", "db": True, "storage": True, "queue": True}


async def test_health_degraded_when_db_down(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _false() -> bool:
        return False

    async def _true() -> bool:
        return True

    monkeypatch.setattr(health, "_db_ok", _false)
    monkeypatch.setattr(health, "_queue_ok", _true)
    monkeypatch.setattr(health, "storage_healthy", lambda: True)
    body = await health.health()
    assert body["status"] == "degraded"
    assert body["db"] is False
