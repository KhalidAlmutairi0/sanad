"""arq worker entrypoint. Job functions are registered here as later deliverables land.

Retry policy (architecture.md 7c): max 3 attempts, exponential backoff. On final failure a
job writes an audit_log entry with a reason code and marks its entity `failed` — never a
silent drop. Sanitizer jobs are NOT retried on timeout/OOM (the file is quarantined).
"""
from __future__ import annotations

from arq.connections import RedisSettings

from app.core.config import Settings, get_settings
from app.core.queue import redis_settings
from app.workers.jobs.extract import extract_clauses
from app.workers.jobs.findings import generate_findings
from app.workers.jobs.idea import generate_idea_report_job
from app.workers.jobs.sanitize import sanitize_contract


def assert_safe_sanitizer(settings: Settings) -> None:
    """Fail fast if production would run the sanitizer without the no-network sandbox.

    `SANITIZER_MODE=direct` drops the containment guarantee (AGENTS.md #2). It is a demo
    fallback for hosts that forbid user namespaces; it must never run in production, where
    a silent downgrade previously logged a warning and continued. Refuse to start instead.
    """
    if settings.is_production and settings.sanitizer_mode.strip().lower() == "direct":
        raise RuntimeError(
            "SANITIZER_MODE=direct is forbidden in production (APP_ENV=production): the "
            "upload sanitizer would run without the no-network sandbox. Set "
            "SANITIZER_MODE=sandboxed and provision user namespaces, or fix APP_ENV."
        )


async def startup(ctx: dict) -> None:
    assert_safe_sanitizer(get_settings())
    ctx["ready"] = True


async def shutdown(ctx: dict) -> None:  # noqa: ARG001
    pass


class WorkerSettings:
    # Job types (architecture.md 7c).
    functions = [sanitize_contract, extract_clauses, generate_findings, generate_idea_report_job]
    on_startup = startup
    on_shutdown = shutdown
    max_tries = 3
    redis_settings: RedisSettings = redis_settings()
