"""Corpus staleness (spec #7): days since a regulation was last reconciled against its source,
and whether that exceeds the configured threshold. Pure + unit-testable."""
from __future__ import annotations

import datetime as dt


def staleness(
    last_reconciled_at: dt.datetime | None, now: dt.datetime, stale_days: int
) -> tuple[int | None, bool]:
    """Return (days_since_reconciled, stale). Never reconciled -> (None, True)."""
    if last_reconciled_at is None:
        return None, True
    days = (now - last_reconciled_at).days
    return days, days >= stale_days
