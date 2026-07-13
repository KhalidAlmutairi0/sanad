"""Retrieval eval harness (PLAN.md P1.5): measure hit@k of the retriever over the live
corpus, so reranker/threshold changes are judged by numbers, not feel.

For each gold query it runs retrieve_candidates(q, k=20) and checks whether the expected
article (by code + article_ref substring) appears in the top-1/5/10/20. Reports hit@k and
writes a dated report. Run inside the api container against the live DB:

    docker compose ... run --rm -e PYTHONPATH=/app api python -m tests.eval.retrieval_eval
"""
from __future__ import annotations

import asyncio
import datetime as dt
import pathlib

import yaml

from app.core.db import SessionLocal
from app.services.retrieval import retrieve_candidates

HERE = pathlib.Path(__file__).resolve().parent
QUERIES = HERE / "queries.yaml"
KS = (1, 5, 10, 20)


def _matches(cand, expect_code: str, expect_ref: str) -> bool:
    if cand.regulation_code != expect_code:
        return False
    return expect_ref in cand.article_ref if expect_ref else True


async def main() -> None:
    gold = yaml.safe_load(QUERIES.read_text(encoding="utf-8"))["queries"]
    hits = {k: 0 for k in KS}
    lines = []
    async with SessionLocal() as session:
        for g in gold:
            cands = await retrieve_candidates(session, g["q"], k=max(KS))
            rank = next((i + 1 for i, c in enumerate(cands)
                         if _matches(c, g["expect_code"], g.get("expect_ref", ""))), None)
            for k in KS:
                if rank is not None and rank <= k:
                    hits[k] += 1
            top = f"{cands[0].regulation_code} {cands[0].article_ref}" if cands else "-"
            lines.append(f"  rank={rank if rank else '>20':<4} [{g['expect_code']} {g.get('expect_ref','*')}] "
                         f"top1={top} :: {g['q'][:50]}")

    n = len(gold)
    report = [f"Retrieval eval — {dt.date.today()} — {n} queries", ""]
    report += lines + [""]
    report += [f"  hit@{k}: {hits[k]}/{n} = {hits[k]/n:.0%}" for k in KS]
    text = "\n".join(report)
    print(text)
    out = HERE / f"report-{dt.date.today()}.md"
    out.write_text(text + "\n", encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    asyncio.run(main())
