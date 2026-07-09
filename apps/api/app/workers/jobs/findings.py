"""generate_findings job: run LLM finding generation (through the citation gate) over a
contract's clauses, then leave the contract in 'reviewing' for the human gate."""
from __future__ import annotations

import uuid

from app.core.db import SessionLocal
from app.services.analysis import generate_findings_for_contract


async def generate_findings(ctx: dict, contract_id: str) -> str:  # noqa: ARG001
    async with SessionLocal() as session:
        count = await generate_findings_for_contract(session, uuid.UUID(contract_id))
    return f"findings:{count}"
