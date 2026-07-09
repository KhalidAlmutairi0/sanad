"""Article change detection. Compares a freshly fetched article against the last stored
content hash. Differ failures must alert, never silently pass (plan.md risk table)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DiffResult:
    changed: bool
    change_type: str | None  # new_article | amended | repealed | None


def diff_article(*, stored_hash: str | None, new_hash: str, new_text: str) -> DiffResult:
    if stored_hash is None:
        return DiffResult(changed=True, change_type="new_article")
    if not new_text.strip():
        # Empty fetch is suspicious (site structure change) — flag as repealed candidate,
        # never treat as "no change".
        return DiffResult(changed=True, change_type="repealed")
    if new_hash != stored_hash:
        return DiffResult(changed=True, change_type="amended")
    return DiffResult(changed=False, change_type=None)
