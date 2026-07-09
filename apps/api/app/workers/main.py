"""arq worker entrypoint. Job functions are registered here as later deliverables land.

Retry policy (architecture.md 7c): max 3 attempts, exponential backoff. On final failure a
job writes an audit_log entry with a reason code and marks its entity `failed` — never a
silent drop. Sanitizer jobs are NOT retried on timeout/OOM (the file is quarantined).
"""
from __future__ import annotations

from arq.connections import RedisSettings

from app.core.queue import redis_settings
from app.workers.jobs.extract import extract_clauses
from app.workers.jobs.findings import generate_findings
from app.workers.jobs.idea import generate_idea_report_job
from app.workers.jobs.sanitize import sanitize_contract


async def startup(ctx: dict) -> None:
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
