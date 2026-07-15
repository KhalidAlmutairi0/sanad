"""Corpus staleness computation (spec #7)."""
from __future__ import annotations

import datetime as dt

from app.services.corpus.staleness import staleness

NOW = dt.datetime(2026, 7, 15, tzinfo=dt.timezone.utc)


def test_never_reconciled_is_stale():
    assert staleness(None, NOW, 30) == (None, True)


def test_recent_is_fresh():
    d, stale = staleness(NOW - dt.timedelta(days=5), NOW, 30)
    assert d == 5 and stale is False


def test_beyond_threshold_is_stale():
    d, stale = staleness(NOW - dt.timedelta(days=45), NOW, 30)
    assert d == 45 and stale is True


def test_exactly_at_threshold_is_stale():
    d, stale = staleness(NOW - dt.timedelta(days=30), NOW, 30)
    assert d == 30 and stale is True
