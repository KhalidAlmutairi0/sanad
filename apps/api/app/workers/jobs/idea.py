"""generate_idea_report job: cited compliance report over the evidence cache."""
from __future__ import annotations

import uuid

from app.core.db import SessionLocal
from app.services.analysis import generate_idea_report


async def generate_idea_report_job(ctx: dict, idea_check_id: str) -> str:  # noqa: ARG001
    async with SessionLocal() as session:
        cited = await generate_idea_report(session, uuid.UUID(idea_check_id))
    return f"idea_report:{cited}"
