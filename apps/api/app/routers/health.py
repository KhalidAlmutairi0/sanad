"""GET /health — no auth. Used by compose healthchecks and on-prem monitoring."""
from __future__ import annotations

from arq import create_pool
from fastapi import APIRouter
from sqlalchemy import text

from app.core.db import engine
from app.core.queue import redis_settings
from app.core.storage import storage_healthy

router = APIRouter()


async def _db_ok() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _queue_ok() -> bool:
    try:
        pool = await create_pool(redis_settings())
        await pool.ping()
        await pool.aclose()
        return True
    except Exception:
        return False


@router.get("/health")
async def health() -> dict[str, object]:
    db = await _db_ok()
    queue = await _queue_ok()
    storage = storage_healthy()
    return {"status": "ok" if (db and queue and storage) else "degraded",
            "db": db, "storage": storage, "queue": queue}
