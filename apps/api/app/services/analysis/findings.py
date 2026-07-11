"""LLM finding generation. The model selects among retrieved candidate articles BY INDEX;
the citation (regulation_version_id) is resolved server-side, so a citation cannot be
hallucinated. Every finding then passes the citation gate before it is written."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clause, Contract
from app.services.analysis.violation_cost import extract_violation_cost
from app.services.audit import write_audit
from app.services.citations import create_finding_guarded
from app.services.llm import LLMRequest, UntrustedBlock, get_llm
from app.services.retrieval import Candidate, retrieve_candidates
from app.services.settings import CONTRACTS_GUIDANCE_KEY, get_setting

ACTOR_ANALYSIS = "analysis"
_SEVERITIES = {"critical", "high", "medium", "low"}
_CATEGORIES = {"regulatory", "sharia"}
# Beyond this cosine distance a candidate is treated as irrelevant (no forced finding).
_RELEVANCE_MAX_DISTANCE = 0.42

# EDITABLE by admins (persona + analytical intent). Stored guidance overrides this default.
CONTRACTS_GUIDANCE_DEFAULT = (
    "You are a senior Saudi regulatory compliance analyst. You are given ONE contract "
    "clause and a numbered list of candidate regulation articles retrieved from a verified "
    "evidence cache. Decide whether the clause conflicts with, or fails to satisfy, any "
    "candidate article."
)

# LOCKED machine contract — always appended, never editable. Enforces Zero Unsourced
# Findings (cite by index, no invented citations) and the JSON schema the parser needs.
CONTRACTS_CONTRACT = (
    "Rules: (1) Only cite a candidate by its given index. Never invent an article, number, "
    "or citation. (2) If the clause raises no issue against any candidate, return an empty "
    "JSON array. (3) Base every explanation strictly on the cited article's text. (4) Output "
    "ONLY a JSON array, no prose. Each element: "
    '{"candidate_index": int, "severity": "critical|high|medium|low", '
    '"category": "regulatory", "title_ar": str, "title_en": str, "explanation_ar": str, '
    '"explanation_en": str}. Arabic and English fields are separate, never mixed.'
)


def _compose_system_prompt(guidance: str) -> str:
    return f"{guidance.strip()}\n\n{CONTRACTS_CONTRACT}"


def _instruction(candidates: list[Candidate]) -> str:
    lines = [
        "Analyze the contract clause (in the untrusted-data block) against these candidate "
        "articles. Refer to them only by index:",
    ]
    for i, c in enumerate(candidates):
        lines.append(f"[{i}] {c.regulation_code} {c.article_ref}")
    return "\n".join(lines)


def _untrusted_blocks(clause_text: str, candidates: list[Candidate]) -> list[UntrustedBlock]:
    blocks = [UntrustedBlock(source="contract_clause", content=clause_text)]
    for i, c in enumerate(candidates):
        blocks.append(
            UntrustedBlock(source=f"candidate_article_{i}", content=c.article_text_ar)
        )
    return blocks


def _offline_stub(candidates: list[Candidate]) -> list[dict]:
    """Deterministic finding used when no real model is configured (keeps the slice
    runnable + tests deterministic). Flags the clause against its nearest candidate only if
    that candidate is semantically close; penalty-bearing articles are rated higher."""
    top = candidates[0]
    if top.distance > _RELEVANCE_MAX_DISTANCE:
        return []
    penalty = any(w in top.article_text_ar for w in ("عقوبة", "غرامة", "السجن"))
    severity = "high" if penalty else "medium"
    return [
        {
            "candidate_index": 0,
            "severity": severity,
            "category": "regulatory",
            "title_ar": f"احتمال تعارض مع {top.regulation_code} {top.article_ref}",
            "title_en": f"Possible conflict with {top.regulation_code} {top.article_ref}",
            "explanation_ar": (
                f"يتطلب هذا البند مراجعة في ضوء {top.regulation_code} {top.article_ref}. "
                f"يستند التقييم إلى نص المادة المستشهد بها."
            ),
            "explanation_en": (
                f"This clause requires review in light of {top.regulation_code} "
                f"{top.article_ref}, based on the cited article text."
            ),
        }
    ]


def _coerce(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if not isinstance(item, dict) or "candidate_index" not in item:
            continue
        item["severity"] = item.get("severity") if item.get("severity") in _SEVERITIES else "medium"
        item["category"] = item.get("category") if item.get("category") in _CATEGORIES else "regulatory"
        out.append(item)
    return out


async def generate_findings_for_contract(session: AsyncSession, contract_id: uuid.UUID) -> int:
    contract = await session.get(Contract, contract_id)
    if not contract or contract.status not in ("extracting", "sanitized", "reviewing"):
        return 0

    clauses = (
        await session.execute(select(Clause).where(Clause.contract_id == contract_id).order_by(Clause.ordinal))
    ).scalars().all()

    provider = get_llm()
    guidance = await get_setting(session, CONTRACTS_GUIDANCE_KEY, CONTRACTS_GUIDANCE_DEFAULT)
    system_prompt = _compose_system_prompt(guidance)
    total = 0
    for clause in clauses:
        clause_text = clause.text_ar or clause.text_en
        if not clause_text:
            continue
        candidates = await retrieve_candidates(session, clause_text, k=4)
        if not candidates:
            continue

        req = LLMRequest(
            system_prompt=system_prompt,
            instruction=_instruction(candidates),
            untrusted_blocks=_untrusted_blocks(clause_text, candidates),
            offline_stub=_offline_stub(candidates),
            max_tokens=1500,
        )
        drafts = _coerce(await provider.complete_json(req))

        for draft in drafts:
            idx = draft.get("candidate_index")
            if not isinstance(idx, int) or idx < 0 or idx >= len(candidates):
                await write_audit(
                    session, actor=ACTOR_ANALYSIS, action="citation_rejected",
                    target=str(contract_id), verdict="denied",
                    detail={"reason": "candidate_index_out_of_range", "clause_id": str(clause.id)},
                )
                continue
            cand = candidates[idx]
            phrase, vmin, vmax = extract_violation_cost(cand.article_text_ar)
            await create_finding_guarded(
                session,
                contract_id=contract_id,
                clause_id=clause.id,
                regulation_version_id=cand.regulation_version_id,
                title_ar=draft.get("title_ar") or f"تعارض مع {cand.regulation_code} {cand.article_ref}",
                title_en=draft.get("title_en"),
                explanation_ar=draft.get("explanation_ar"),
                explanation_en=draft.get("explanation_en"),
                severity=draft["severity"],
                category=draft["category"],
                violation_cost_ar=draft.get("violation_cost_ar") or phrase,
                violation_cost_min=vmin,
                violation_cost_max=vmax,
                actor=ACTOR_ANALYSIS,
            )
            total += 1

    contract.status = "reviewing"
    await write_audit(
        session, actor=ACTOR_ANALYSIS, action="findings_generated",
        target=str(contract_id), verdict="n-a", detail={"count": total},
    )
    await session.commit()
    return total
