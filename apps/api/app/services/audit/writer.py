"""Append-only audit log writer."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog

# Non-user actors (database.md: actor is a user id, 'research-agent', or 'sanitizer').
ACTOR_SANITIZER = "sanitizer"
ACTOR_RESEARCH_AGENT = "research-agent"
ACTOR_ANALYSIS = "analysis"  # automated analysis-env pipeline (extraction, findings, scoring)

# Stable action names. Mirrors api-contracts.md examples; extend deliberately.
ACTIONS = {
    "contract_uploaded",
    "sanitize_started",
    "sanitize_succeeded",
    "sanitize_failed",
    "clauses_extracted",
    "findings_generated",
    "citation_rejected",  # citation gate blocked a draft finding (should never happen)
    "finding_reviewed",
    "score_computed",
    "idea_check_submitted",
    "idea_report_generated",
    "idea_check_reviewed",
    "agent_fetch",
    "egress_denied",
    "allowlist_updated",
    "regulation_version_verified",
}


async def write_audit(
    session: AsyncSession,
    *,
    actor: str,
    action: str,
    target: str | None = None,
    verdict: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """Insert one audit row. Flushes within the caller's transaction so the audit entry
    and the state change commit atomically. Never swallow: callers must not wrap this in a
    bare except that hides failures."""
    session.add(
        AuditLog(
            actor=actor,
            action=action,
            target=target,
            verdict=verdict,
            detail_json=detail,
        )
    )
    await session.flush()
