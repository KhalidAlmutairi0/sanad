"""One-off: bulk-fetch a list of BOE laws [[uuid, title], ...] into verbatim corpus YAML.

Codes are assigned BOE001.. in list order; name_ar is the catalog title. Honors the 10s
crawl-delay. Resumable (skips laws whose YAML already exists). Laws that yield no articles
(agreements, JS-rendered pages, error pages) are reported FAILED and skipped.

    python scripts/fetch_bulk_boe.py <new_laws.json>
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_boe_law import CRAWL_DELAY_SECONDS, write_corpus  # noqa: E402

CORPUS = pathlib.Path(__file__).resolve().parent / "seed_data" / "corpus"


def main() -> int:
    new = json.load(open(sys.argv[1], encoding="utf-8"))
    ok = fail = 0
    fetched = 0
    for i, (uuid, title) in enumerate(new):
        code = f"BOE{i + 1:03d}"
        name = title.replace("-->", "").strip()
        out = CORPUS / f"{code}.yaml"
        if out.exists():
            continue
        if fetched:
            time.sleep(CRAWL_DELAY_SECONDS)
        fetched += 1
        url = f"https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/{uuid}/1"
        try:
            n = write_corpus(url, code, name, "", "—", str(out))
            print(f"{code} {name[:45]}: {n} articles", flush=True)
            ok += 1
        except Exception as e:  # noqa: BLE001 — report + continue the batch
            print(f"{code} {name[:45]}: FAILED — {e}", flush=True)
            fail += 1
    print(f"DONE ok={ok} fail={fail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
