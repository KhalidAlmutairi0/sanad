"""Batch-fetch every law in the registry (_sources.yaml) from the official gazette into
verbatim corpus YAML. Honors the 10s crawl-delay between laws. Resumable: pass --skip-existing
to skip laws whose corpus file already exists.

    python scripts/fetch_all_laws.py [--only CODE1,CODE2] [--skip-existing]
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_boe_law import CRAWL_DELAY_SECONDS, write_corpus  # noqa: E402

CORPUS_DIR = pathlib.Path(__file__).resolve().parent / "seed_data" / "corpus"
SOURCES = CORPUS_DIR / "_sources.yaml"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated codes to fetch (default: all)")
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()

    sources = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))["sources"]
    only = set(args.only.split(",")) if args.only else None

    fetched = 0
    for i, src in enumerate(sources):
        if only and src["code"] not in only:
            continue
        out = CORPUS_DIR / src["corpus_file"]
        if args.skip_existing and out.exists():
            print(f"skip (exists): {src['code']}")
            continue
        if fetched:
            time.sleep(CRAWL_DELAY_SECONDS)  # polite between laws
        try:
            n = write_corpus(src["url"], src["code"], src["name_ar"], src["name_en"],
                             src["authority"], str(out))
            print(f"{src['code']}: {n} articles -> {src['corpus_file']}")
        except Exception as e:  # noqa: BLE001 — report and continue the batch
            print(f"{src['code']}: FAILED — {e}", file=sys.stderr)
        fetched += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
