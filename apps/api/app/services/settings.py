"""Editable key/value settings. Used for admin-editable prompt guidance: the analyst
persona/intent an admin can rewrite, kept SEPARATE from the locked machine contract that
enforces JSON-only output and cite-by-index (Zero Unsourced Findings). The contract is
always appended in code and is never stored here, so a bad edit cannot break sourcing."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Setting

# Keys for the two editable guidance blocks.
CONTRACTS_GUIDANCE_KEY = "contracts_guidance"
IDEA_GUIDANCE_KEY = "idea_guidance"


async def get_setting(session: AsyncSession, key: str, default: str) -> str:
    row = (await session.execute(select(Setting).where(Setting.key == key))).scalar_one_or_none()
    if row is None or not row.value.strip():
        return default
    return row.value


async def set_setting(session: AsyncSession, key: str, value: str, user_id: uuid.UUID) -> None:
    stmt = (
        insert(Setting)
        .values(key=key, value=value, updated_by=user_id)
        .on_conflict_do_update(
            index_elements=[Setting.key],
            set_={"value": value, "updated_by": user_id, "updated_at": func.now()},
        )
    )
    await session.execute(stmt)
