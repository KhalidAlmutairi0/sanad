"""LLM reranker (PLAN.md P1.6). Cosine similarity over e5 embeddings retrieves a wide net of
candidate articles; at 1600+ articles raw top-k often ranks a broadly-similar article above
the precisely-applicable one. This reranks the net by asking the LLM to order candidates by
direct relevance to the clause, then keeps the top N.

The clause is UNTRUSTED (it comes from an uploaded contract), so it is wrapped in the
untrusted-data delimiters via the LLM gateway. Candidate article text is from the verified
cache (trusted) and is truncated for the ranking prompt. Offline/stub returns cosine order,
so tests and no-model deployments keep working deterministically.
"""
from __future__ import annotations

from app.services.llm import LLMRequest, UntrustedBlock, get_llm
from app.services.retrieval.search import Candidate

RERANK_SYSTEM = (
    "You are a Saudi legal retrieval ranker. Given a contract clause and a numbered list of "
    "candidate regulation articles, rank the candidates by how DIRECTLY each one governs or "
    "conflicts with the clause — the single most on-point article first. Judge only on the "
    "provided text. Output ONLY JSON: {\"ranking\": [indices, most relevant first]}. Include "
    "every index exactly once."
)

# Per-candidate snippet length for the ranking prompt. Shrinks as the net grows so a wide
# net (needed for recall at corpus scale) still fits comfortably in context.
def _snippet_len(n: int) -> int:
    if n <= 25:
        return 500
    if n <= 60:
        return 300
    return 200


def _instruction(candidates: list[Candidate]) -> str:
    snip = _snippet_len(len(candidates))
    lines = ["Candidate articles (rank by relevance to the clause in the untrusted-data block):"]
    for i, c in enumerate(candidates):
        text = " ".join(c.article_text_ar.split())[:snip]
        lines.append(f"[{i}] {c.regulation_code} {c.article_ref}: {text}")
    return "\n".join(lines)


def _apply_ranking(candidates: list[Candidate], ranking: list) -> list[Candidate]:
    seen: set[int] = set()
    ordered: list[Candidate] = []
    for idx in ranking:
        if isinstance(idx, int) and 0 <= idx < len(candidates) and idx not in seen:
            seen.add(idx)
            ordered.append(candidates[idx])
    # Append any candidate the model dropped, preserving original (cosine) order.
    for i, c in enumerate(candidates):
        if i not in seen:
            ordered.append(c)
    return ordered


async def rerank(query_text: str, candidates: list[Candidate], *, top_n: int) -> list[Candidate]:
    if len(candidates) <= 1:
        return candidates[:top_n]
    req = LLMRequest(
        system_prompt=RERANK_SYSTEM,
        instruction=_instruction(candidates),
        untrusted_blocks=[UntrustedBlock(source="contract_clause", content=query_text)],
        offline_stub={"ranking": list(range(len(candidates)))},  # cosine order when no model
        # Output is a JSON list of every index; ~8 tokens/index plus headroom so a wide net
        # is never truncated (which would break JSON parsing).
        max_tokens=max(256, len(candidates) * 8 + 64),
    )
    try:
        result = await get_llm().complete_json(req)
        ranking = result.get("ranking", []) if isinstance(result, dict) else []
    except ValueError:
        # Model returned unparseable output — fall back to cosine order rather than fail the
        # whole retrieval. Rerank is a precision boost, not a correctness requirement.
        ranking = []
    return _apply_ranking(candidates, ranking)[:top_n]
