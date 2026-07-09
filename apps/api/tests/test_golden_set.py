"""Golden-set regression (test-plan §13). Exercises the REAL retrieval + citation engine
end to end against the seeded corpus and asserts each labeled clause is covered by findings
citing the expected regulation.

Gated: needs a seeded DB + the embedder service. Enable with RUN_GOLDEN=1; skips otherwise
so it never blocks the offline suite. This is the coverage proxy for finding precision; the
human-acceptance target (≥ 80%, plan.md) is tracked separately on real reviews.
"""
from __future__ import annotations

import json
import os
import pathlib

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Clause, Contract, Finding, Regulation, RegulationVersion, User
from app.services.analysis import generate_findings_for_contract
from app.services.extraction import segment_clauses
from app.services.retrieval import embed_texts

CASES = json.loads((pathlib.Path(__file__).parent / "golden" / "cases.json").read_text("utf-8"))

pytestmark = pytest.mark.skipif(not os.environ.get("RUN_GOLDEN"), reason="set RUN_GOLDEN=1 to run")


@pytest_asyncio.fixture
async def seeded_guard(session: AsyncSession) -> None:
    # Require both a seeded corpus and a reachable embedder; skip cleanly otherwise.
    has_corpus = (
        await session.execute(select(RegulationVersion.id).limit(1))
    ).scalar_one_or_none()
    if not has_corpus:
        pytest.skip("evidence cache is empty — run scripts/seed_regulations.py first")
    try:
        httpx.get(f"{get_settings().embedder_url.rstrip('/')}/health", timeout=5.0).raise_for_status()
    except Exception:
        pytest.skip("embedder service not reachable")


@pytest.mark.parametrize("case", CASES["cases"], ids=[c["name"] for c in CASES["cases"]])
async def test_golden_case_coverage(
    session: AsyncSession, seeded_guard: None, user: User, case: dict
) -> None:
    contract = Contract(
        title=case["name"], uploaded_by=user.id,
        raw_object_key=f"golden/{case['name']}", status="sanitized",
    )
    session.add(contract)
    await session.flush()

    segments = segment_clauses(case["contract_text"])
    texts = [s.text_ar or s.text_en or "" for s in segments]
    embeddings = await embed_texts(texts, input_type="passage")
    for seg, emb in zip(segments, embeddings):
        session.add(Clause(contract_id=contract.id, ordinal=seg.ordinal,
                           text_ar=seg.text_ar, text_en=seg.text_en, embedding=emb))
    await session.flush()

    await generate_findings_for_contract(session, contract.id)

    cited_codes = set(
        (
            await session.execute(
                select(Regulation.code)
                .join(RegulationVersion, RegulationVersion.regulation_id == Regulation.id)
                .join(Finding, Finding.regulation_version_id == RegulationVersion.id)
                .where(Finding.contract_id == contract.id)
            )
        ).scalars().all()
    )

    expected = set(case["expected_codes"])
    covered = expected & cited_codes
    coverage = len(covered) / len(expected) if expected else 1.0
    assert coverage >= CASES["min_coverage"], (
        f"{case['name']}: expected {sorted(expected)}, findings cited {sorted(cited_codes)}"
    )
