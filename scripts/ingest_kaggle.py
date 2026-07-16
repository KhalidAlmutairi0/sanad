"""Ingest a third-party (e.g. Kaggle) legal dataset into the corpus as QUARANTINED text.

Rows are stored under the `unverified_third_party` tier: embedded and searchable in the
evidence store, but the citation gate + retrieval filter keep them OUT of findings/idea-check
citations until a human verifies each against the official source (which promotes the tier).
This lets you grow retrieval coverage from lower-provenance data WITHOUT weakening Zero
Unsourced Findings.

Provenance is preserved: source_url falls back to the dataset URL so every row is traceable.

Input: a CSV with (at least) an article text column. Column names are configurable.
    --code-col       regulation code   (default: derive one code for the whole file via --code)
    --ref-col        article ref        (default: row index)
    --text-col       Arabic article text (REQUIRED content)
    --source-col     per-row source url  (default: --dataset-url)

Download the dataset first (needs your Kaggle token ~/.kaggle/kaggle.json):
    kaggle datasets download -d <owner>/<slug> -p /tmp/kag --unzip

Run inside the api container (has DB + embedder):
    docker compose -f infra/docker-compose.yml run --rm -e PYTHONPATH=/app api \
        python scripts/ingest_kaggle.py /tmp/kag/data.csv \
        --code SAUDI-BOG --name-ar "قضايا ديوان المظالم" --text-col text \
        --dataset-url https://www.kaggle.com/datasets/<owner>/<slug> [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import pathlib
import sys

from sqlalchemy import select

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.core.db import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import User  # noqa: E402
from app.services.corpus import ingest_regulation, parse_regulation_spec, validate_regulation  # noqa: E402
from app.services.corpus.ingest import summarize  # noqa: E402
from app.services.corpus.tiers import UNVERIFIED_THIRD_PARTY  # noqa: E402
from app.services.retrieval import embed_texts  # noqa: E402

# System account: third-party rows are attributed to the import service, never a person, so
# verified_by is honest (nothing here has been human-verified).
IMPORT_EMAIL = "third-party-import@sanad.local"
IMPORT_NAME = "Third-Party Import"
IMPORT_PASSWORD = "sanad-dev-password"


async def _embed(texts: list[str]) -> list[list[float]]:
    batch, out = 16, []
    for i in range(0, len(texts), batch):
        out.extend(await embed_texts(texts[i:i + batch], input_type="passage"))
    return out


def _rows_to_spec(path: pathlib.Path, args: argparse.Namespace) -> dict:
    articles = []
    with path.open(encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            text = (row.get(args.text_col) or "").strip()
            if not text:
                continue
            articles.append({
                "article_ref": (row.get(args.ref_col) or f"row-{i + 1}").strip() if args.ref_col else f"row-{i + 1}",
                "article_text_ar": text,
                "source_url": (row.get(args.source_col) or args.dataset_url) if args.source_col else args.dataset_url,
                "verified": False,
            })
    return {
        "regulation": {"code": args.code, "name_ar": args.name_ar, "name_en": args.name_en,
                       "authority": args.authority, "source_domain": args.source_domain},
        "articles": articles,
    }


async def main() -> int:
    p = argparse.ArgumentParser(description="Ingest a third-party dataset as quarantined corpus")
    p.add_argument("csv_path")
    p.add_argument("--code", required=True, help="regulation code for the whole file")
    p.add_argument("--name-ar", required=True)
    p.add_argument("--name-en", default="")
    p.add_argument("--authority", default="Third party")
    p.add_argument("--source-domain", default="kaggle.com")
    p.add_argument("--dataset-url", required=True, help="dataset URL — provenance / source_url fallback")
    p.add_argument("--text-col", required=True)
    p.add_argument("--ref-col", default="")
    p.add_argument("--source-col", default="")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    spec = _rows_to_spec(pathlib.Path(args.csv_path), args)
    reg = parse_regulation_spec(spec)
    errors = validate_regulation(reg)
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"Parsed {len(reg.articles)} articles for {reg.code} (tier: {UNVERIFIED_THIRD_PARTY}).")
    if args.dry_run:
        print("DRY RUN — no DB writes.")
        return 0

    async with SessionLocal() as session:
        importer = (
            await session.execute(select(User).where(User.email == IMPORT_EMAIL))
        ).scalar_one_or_none()
        if importer is None:
            importer = User(email=IMPORT_EMAIL, display_name=IMPORT_NAME, role="service",
                            password_hash=hash_password(IMPORT_PASSWORD))
            session.add(importer)
            await session.flush()

        stats = await ingest_regulation(
            session, reg, verifier_id=importer.id, embed_fn=_embed, tier=UNVERIFIED_THIRD_PARTY
        )
        await session.commit()

    print(f"Tier: {UNVERIFIED_THIRD_PARTY} (quarantined — searchable, NOT citable)")
    print(summarize([stats]))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
