"""Ingest the human-verified regulatory corpus into regulation_versions (with embeddings).

Reads one YAML file per regulation from scripts/seed_data/corpus/ (see corpus/README.md for
the format). Only articles marked `verified: true` are inserted — the human gate. Idempotent:
re-running skips articles already present.

Run inside the api container (has DB + embedder):
    docker compose -f infra/docker-compose.yml run --rm -e PYTHONPATH=/app api \
        python scripts/ingest_regulations.py [--dry-run] [PATH]

PATH defaults to scripts/seed_data/corpus/ (a directory) but may be a single .yaml file.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import pathlib
import sys

import yaml
from sqlalchemy import select

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.core.db import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import User  # noqa: E402
from app.services.corpus import (  # noqa: E402
    IngestStats,
    ingest_regulation,
    parse_regulation_spec,
    validate_regulation,
)
from app.services.corpus.ingest import summarize  # noqa: E402
from app.services.retrieval import embed_texts  # noqa: E402

DEFAULT_DIR = pathlib.Path(__file__).resolve().parent / "seed_data" / "corpus"
VERIFIER_EMAIL = os.environ.get("CORPUS_VERIFIER_EMAIL", "corpus-verifier@sanad.local")
VERIFIER_NAME = os.environ.get("CORPUS_VERIFIER_NAME", "Corpus Verifier")
VERIFIER_PASSWORD = os.environ.get("SEED_DEFAULT_PASSWORD", "sanad-dev-password")
# Distinct system account for official-fetch ingestion — never a human, so verified_by is
# honest: official_fetch rows are attributed to the fetch service, not a person.
FETCH_EMAIL = "official-fetch@sanad.local"
FETCH_NAME = "Official Gazette Fetch"


def _yaml_files(path: pathlib.Path) -> list[pathlib.Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.glob("*.yaml") if p.name != "README.md")


async def _embed(texts: list[str]) -> list[list[float]]:
    return await embed_texts(texts, input_type="passage")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest verified regulatory corpus")
    parser.add_argument("path", nargs="?", default=str(DEFAULT_DIR))
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse + validate + count only; no DB writes, no embeddings")
    parser.add_argument("--trust-official-source", action="store_true",
                        help="Ingest verbatim-fetched articles under the 'official_fetch' tier "
                             "even if verified: false (owner-policy trust of the official gazette). "
                             "Rows are labeled official_fetch so the UI shows them as auto-fetched.")
    args = parser.parse_args()

    root = pathlib.Path(args.path)
    files = _yaml_files(root)
    if not files:
        print(f"No .yaml corpus files found under {root}")
        return 1

    regs = []
    errors = []
    for f in files:
        spec = yaml.safe_load(f.read_text(encoding="utf-8"))
        reg = parse_regulation_spec(spec)
        file_errors = validate_regulation(reg)
        errors.extend(f"{f.name}: {e}" for e in file_errors)
        regs.append(reg)

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    if args.dry_run:
        print("DRY RUN — validation passed. Per regulation (verified / total articles):")
        total_v = total_a = 0
        for reg in regs:
            v = sum(1 for a in reg.articles if a.verified)
            total_v += v
            total_a += len(reg.articles)
            print(f"  {reg.code}: {v} verified / {len(reg.articles)} total")
        print(f"TOTAL: {total_v} verified / {total_a} total ready to ingest")
        return 0

    tier = "official_fetch" if args.trust_official_source else "human_verified"
    email = FETCH_EMAIL if args.trust_official_source else VERIFIER_EMAIL
    name = FETCH_NAME if args.trust_official_source else VERIFIER_NAME

    async with SessionLocal() as session:
        verifier = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if verifier is None:
            verifier = User(email=email, display_name=name, role="service",
                            password_hash=hash_password(VERIFIER_PASSWORD))
            session.add(verifier)
            await session.flush()

        all_stats: list[IngestStats] = []
        for reg in regs:
            stats = await ingest_regulation(session, reg, verifier_id=verifier.id,
                                            embed_fn=_embed, tier=tier)
            all_stats.append(stats)
        await session.commit()

    print(f"Tier: {tier}")

    print("Ingest complete:")
    print(summarize(all_stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
