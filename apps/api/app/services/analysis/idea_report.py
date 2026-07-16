"""Idea Check report generation — the SAME engine as contract findings (retrieval +
citations + human gate), different input. The PM idea is UNTRUSTED input; it is wrapped in
untrusted-data tags before any LLM call. Every claim cites a retrieved candidate by index;
citations are resolved server-side into idea_check_citations (no hallucinated sources)."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IdeaCheck, IdeaCheckCitation
from app.services.audit import ACTOR_ANALYSIS, write_audit
from app.services.citations import resolve_citation
from app.services.llm import LLMRequest, UntrustedBlock, get_llm
from app.services.retrieval import Candidate, retrieve_candidates
from app.services.settings import IDEA_GUIDANCE_KEY, get_setting

_RELEVANCE_MAX_DISTANCE = 0.5

# EDITABLE by admins (persona + analytical intent). Stored guidance overrides this default.
IDEA_GUIDANCE_DEFAULT = (
    "You are a Saudi regulatory compliance analyst. A product manager describes a feature "
    "idea. Using ONLY the numbered candidate articles from the verified evidence cache, "
    "produce a compliance report with four sections: applicable regulations, requirements, "
    "risks, open questions."
)

# LOCKED machine contract — always appended, never editable. Enforces cite-by-index and the
# JSON schema the pipeline needs (no hallucinated sources).
IDEA_CONTRACT = (
    "Every substantive claim must reference a candidate by index. Never invent an article or "
    "citation. Output ONLY JSON: "
    '{"report_ar": str, "report_en": str, "cited_indices": [int]}. report_ar is a full '
    "Arabic report; report_en is a full English report; never mix scripts within a line."
)


def _compose_system_prompt(guidance: str) -> str:
    return f"{guidance.strip()}\n\n{IDEA_CONTRACT}"


def _instruction(candidates: list[Candidate]) -> str:
    lines = ["Candidate articles (reference by index):"]
    for i, c in enumerate(candidates):
        lines.append(f"[{i}] {c.regulation_code} {c.article_ref}")
    return "\n".join(lines)


def _offline_stub(candidates: list[Candidate]) -> dict:
    relevant = [i for i, c in enumerate(candidates) if c.distance <= _RELEVANCE_MAX_DISTANCE]
    if not relevant:
        relevant = [0]
    refs_ar = "؛ ".join(f"{candidates[i].regulation_code} {candidates[i].article_ref}" for i in relevant)
    refs_en = "; ".join(f"{candidates[i].regulation_code} {candidates[i].article_ref}" for i in relevant)
    report_ar = (
        "الأنظمة المنطبقة: " + refs_ar + ".\n"
        "المتطلبات: يجب الالتزام بالمواد المذكورة أعلاه عند بناء هذه الميزة.\n"
        "المخاطر: قد ينشأ خطر عدم امتثال إذا خالفت الميزة أياً من المواد المستشهد بها.\n"
        "أسئلة مفتوحة: تحقق من نطاق البيانات ومكان المعالجة قبل البناء."
    )
    report_en = (
        "Applicable regulations: " + refs_en + ".\n"
        "Requirements: the feature must comply with the cited articles above.\n"
        "Risks: non-compliance risk arises if the feature conflicts with any cited article.\n"
        "Open questions: confirm data scope and processing location before building."
    )
    return {"report_ar": report_ar, "report_en": report_en, "cited_indices": relevant}


async def generate_idea_report(session: AsyncSession, idea_check_id: uuid.UUID) -> int:
    idea = await session.get(IdeaCheck, idea_check_id)
    if not idea or idea.status != "submitted":
        return 0

    # Idea-check citations must also rest on citable text only (no quarantined third-party).
    candidates = await retrieve_candidates(session, idea.idea_text, k=6, citable_only=True)
    if not candidates:
        idea.report_ar = "لا توجد مواد نظامية مطابقة في المخزن الحالي."
        idea.report_en = "No matching regulatory articles in the current cache."
        idea.status = "generated"
        await write_audit(
            session, actor=ACTOR_ANALYSIS, action="idea_report_generated",
            target=str(idea_check_id), verdict="n-a", detail={"citations": 0},
        )
        await session.commit()
        return 0

    guidance = await get_setting(session, IDEA_GUIDANCE_KEY, IDEA_GUIDANCE_DEFAULT)
    req = LLMRequest(
        system_prompt=_compose_system_prompt(guidance),
        instruction=_instruction(candidates),
        untrusted_blocks=[UntrustedBlock(source="pm_idea", content=idea.idea_text)]
        + [UntrustedBlock(source=f"candidate_article_{i}", content=c.article_text_ar) for i, c in enumerate(candidates)],
        offline_stub=_offline_stub(candidates),
        max_tokens=2000,
    )
    result = await get_llm().complete_json(req)
    if not isinstance(result, dict):
        result = _offline_stub(candidates)

    idea.report_ar = result.get("report_ar")
    idea.report_en = result.get("report_en")

    # Resolve cited indices -> regulation_version_ids (server-side; unresolvable ones dropped).
    cited = 0
    seen: set[uuid.UUID] = set()
    for idx in result.get("cited_indices", []):
        if not isinstance(idx, int) or idx < 0 or idx >= len(candidates):
            continue
        rvid = candidates[idx].regulation_version_id
        if rvid in seen or await resolve_citation(session, rvid) is None:
            continue
        seen.add(rvid)
        session.add(IdeaCheckCitation(idea_check_id=idea_check_id, regulation_version_id=rvid))
        cited += 1

    idea.status = "generated"
    await write_audit(
        session, actor=ACTOR_ANALYSIS, action="idea_report_generated",
        target=str(idea_check_id), verdict="n-a", detail={"citations": cited},
    )
    await session.commit()
    return cited
