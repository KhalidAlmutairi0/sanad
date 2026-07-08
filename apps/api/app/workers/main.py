"""arq worker entrypoint. Job functions are registered here as later deliverables land.

Retry policy (architecture.md 7c): max 3 attempts, exponential backoff. On final failure a
job writes an audit_log entry with a reason code and marks its entity `failed` — never a
silent drop. Sanitizer jobs are NOT retried on timeout/OOM (the file is quarantined).
"""
from __future__ import annotations

from arq.connections import RedisSettings

from app.core.queue import redis_settings


async def startup(ctx: dict) -> None:
    ctx["ready"] = True


async def shutdown(ctx: dict) -> None:  # noqa: ARG001
    pass


class WorkerSettings:
    functions: list = []  # populated by deliverables 5, 6, 9
    on_startup = startup
    on_shutdown = shutdown
    max_tries = 3
    redis_settings: RedisSettings = redis_settings()
