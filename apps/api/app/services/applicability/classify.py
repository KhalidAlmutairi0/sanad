"""LLM first-pass classification of a regulation article's applicability scope.

Produces a `llm_draft` RegulationApplicability. It NEVER feeds the production decision engine —
a human reviewer must confirm it (classify -> review queue -> human_reviewed). The model reads
the actual article text (from the verified cache), never the title/summary, and its output is
stored with a citation to the scope-defining article, so the classification itself is sourced.
"""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RegulationApplicability, RegulationVersion
from app.services.applicability.engine import APPLICABILITY_TYPES, PROSPECTIVE_ONLY
from app.services.audit import write_audit
from app.services.llm import LLMRequest, get_llm

ACTOR_ANALYSIS = "analysis"

APPLIC_SYSTEM = (
    "You are a senior Saudi regulatory analyst. Given ONE regulation article, classify how it "
    "applies to contracts that were ALREADY SIGNED before it took effect. Choose exactly one "
    "applicability_type: 'retroactive_with_deadline' (applies to all prior contracts, which must "
    "be amended by a stated deadline), 'prospective_only' (applies only to contracts signed on/"
    "after the effective date), or 'grandfathered' (prior contracts keep their existing term for "
    "their life; the update does not apply retroactively). Base the decision ONLY on the article "
    "text — never on the title. Output ONLY JSON: {\"applicability_type\": str, \"deadline_date\": "
    "\"YYYY-MM-DD\"|null, \"scope_quote\": str} where scope_quote is the exact sentence that "
    "defines the scope. If unclear, choose prospective_only."
)


def _offline_stub(text_ar: str) -> dict:
    # Deterministic stub: a penalty/deadline word hints retroactive; else prospective.
    retro = any(w in text_ar for w in ("خلال", "مهلة", "يجب توفيق", "تصحيح أوضاع", "قبل تاريخ"))
    return {
        "applicability_type": "retroactive_with_deadline" if retro else PROSPECTIVE_ONLY,
        "deadline_date": None,
        "scope_quote": text_ar[:160],
    }


def _parse_date(value: object) -> dt.date | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


async def classify_article(session: AsyncSession, regulation_version_id: uuid.UUID) -> RegulationApplicability:
    """Create/refresh the llm_draft applicability for an article. Idempotent per article."""
    rv = await session.get(RegulationVersion, regulation_version_id)
    if rv is None:
        raise ValueError("regulation_version not found")

    text = rv.article_text_ar
    req = LLMRequest(
        system_prompt=APPLIC_SYSTEM,
        instruction=f"Article {rv.article_ref}:\n{text}",
        untrusted_blocks=[],
        offline_stub=_offline_stub(text),
        max_tokens=400,
    )
    result = await get_llm().complete_json(req)
    if not isinstance(result, dict):
        result = _offline_stub(text)

    atype = result.get("applicability_type")
    if atype not in APPLICABILITY_TYPES:
        atype = PROSPECTIVE_ONLY
    deadline = _parse_date(result.get("deadline_date")) if atype == "retroactive_with_deadline" else None
    effective = rv.effective_date or rv.fetched_at.date()

    existing = (
        await session.execute(
            select(RegulationApplicability).where(
                RegulationApplicability.regulation_version_id == regulation_version_id
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        existing = RegulationApplicability(regulation_version_id=regulation_version_id)
        session.add(existing)
    existing.applicability_type = atype
    existing.effective_date = effective
    existing.deadline_date = deadline
    existing.classification_confidence = "llm_draft"
    existing.classification_citation_version_id = regulation_version_id  # self-cite the scope article
    existing.reviewed_by = None
    await session.flush()

    await write_audit(
        session, actor=ACTOR_ANALYSIS, action="applicability_classified",
        target=str(regulation_version_id), verdict="n-a",
        detail={"applicability_type": atype, "confidence": "llm_draft"},
    )
    return existing
