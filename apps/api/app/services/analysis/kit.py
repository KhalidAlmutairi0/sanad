"""LLM generation for the Negotiation Kit (redraft + justification) and the upgraded
Explain It (plain-language, generated strictly from the cited article). Both wrap the clause
and article text as untrusted data and carry a deterministic offline stub."""
from __future__ import annotations

from app.services.llm import LLMRequest, UntrustedBlock, get_llm

_KIT_SYSTEM = (
    "You are a Saudi legal counsel. Given a contract clause and the exact regulation article "
    "it conflicts with, (1) redraft the clause so it complies with that article, and (2) write "
    "a short justification letter that cites the article. Base everything on the cited article "
    "only; invent nothing. Output ONLY JSON: {\"redrafted_clause_ar\", \"redrafted_clause_en\", "
    "\"justification_letter_ar\", \"justification_letter_en\"}. Arabic and English are separate."
)

_EXPLAIN_SYSTEM = (
    "You are a Saudi compliance analyst. Explain, in plain simple language, why a contract "
    "clause conflicts with the given regulation article. Use only the article's content. Output "
    "ONLY JSON: {\"explanation_ar\", \"explanation_en\"}. Keep each to 2 short sentences."
)


async def generate_kit(*, clause_text: str, article_text: str, code: str, article_ref: str) -> dict:
    stub = {
        "redrafted_clause_ar": (
            f"يلتزم الطرفان بما يتوافق مع {code} {article_ref}، وأي إجراء مخالف يخضع للضوابط "
            f"النظامية المقررة قبل تنفيذه."
        ),
        "redrafted_clause_en": (
            f"The parties shall comply with {code} {article_ref}; any conflicting action is "
            f"subject to the required statutory controls before it is carried out."
        ),
        "justification_letter_ar": (
            f"تستند هذه الصياغة إلى {code} {article_ref}. نطلب تعديل البند بما يتوافق معها لتفادي "
            f"المخالفة النظامية."
        ),
        "justification_letter_en": (
            f"This wording is grounded in {code} {article_ref}. We request amending the clause "
            f"to comply with it and avoid a regulatory breach."
        ),
    }
    req = LLMRequest(
        system_prompt=_KIT_SYSTEM,
        instruction=f"Cited article: {code} {article_ref}. Redraft the clause and write the letter.",
        untrusted_blocks=[
            UntrustedBlock(source="contract_clause", content=clause_text or ""),
            UntrustedBlock(source="regulation_article", content=article_text),
        ],
        offline_stub=stub,
        max_tokens=1200,
    )
    result = await get_llm().complete_json(req)
    return result if isinstance(result, dict) else stub


async def generate_explanation(*, article_text: str, code: str, article_ref: str, title: str) -> dict:
    stub = {
        "explanation_ar": (
            f"هذا البند يخالف {code} {article_ref}. باختصار، المادة تشترط ضوابط لم يلتزم بها البند."
        ),
        "explanation_en": (
            f"This clause conflicts with {code} {article_ref}. In short, the article requires "
            f"controls the clause does not meet."
        ),
    }
    req = LLMRequest(
        system_prompt=_EXPLAIN_SYSTEM,
        instruction=f"Finding: {title}. Cited article: {code} {article_ref}.",
        untrusted_blocks=[UntrustedBlock(source="regulation_article", content=article_text)],
        offline_stub=stub,
        max_tokens=500,
    )
    result = await get_llm().complete_json(req)
    return result if isinstance(result, dict) else stub
