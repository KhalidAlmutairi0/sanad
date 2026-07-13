"""The "news" checker: re-fetch each tracked law from the official gazette and report which
articles are NEW, REMOVED, or CHANGED versus the committed corpus. This is the detection
half of monitoring — it never auto-writes the citation store; changes are surfaced for a
human to verify (AGENTS.md #5), then ingested as new versions (append-only).

Run periodically (cron / the arq worker). Respects the gazette's 10s crawl-delay between
laws. Exit code 0 = no changes, 1 = changes detected (so a scheduler can alert).

    python scripts/check_law_updates.py [--json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_boe_law import CRAWL_DELAY_SECONDS, fetch, parse_articles  # noqa: E402

CORPUS_DIR = pathlib.Path(__file__).resolve().parent / "seed_data" / "corpus"
SOURCES = CORPUS_DIR / "_sources.yaml"


def _by_ref(articles: list[dict]) -> dict[str, str]:
    return {a["article_ref"]: " ".join(a["article_text_ar"].split()) for a in articles}


def diff_law(src: dict) -> dict:
    corpus_path = CORPUS_DIR / src["corpus_file"]
    committed = _by_ref(yaml.safe_load(corpus_path.read_text(encoding="utf-8"))["articles"])
    live = _by_ref(parse_articles(fetch(src["url"])))

    added = sorted(set(live) - set(committed))
    removed = sorted(set(committed) - set(live))
    changed = sorted(r for r in set(live) & set(committed) if live[r] != committed[r])
    return {"code": src["code"], "added": added, "removed": removed, "changed": changed,
            "live_count": len(live), "committed_count": len(committed)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    sources = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))["sources"]
    results = []
    for i, src in enumerate(sources):
        if i:
            time.sleep(CRAWL_DELAY_SECONDS)
        try:
            results.append(diff_law(src))
        except Exception as e:  # noqa: BLE001 — report, never crash the whole run
            results.append({"code": src["code"], "error": str(e)})

    any_change = any(r.get("added") or r.get("removed") or r.get("changed") for r in results)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if r.get("error"):
                print(f"{r['code']}: ERROR {r['error']}")
            elif r["added"] or r["removed"] or r["changed"]:
                print(f"{r['code']}: CHANGES — +{len(r['added'])} new, "
                      f"-{len(r['removed'])} removed, ~{len(r['changed'])} changed "
                      f"(live {r['live_count']} vs committed {r['committed_count']})")
                for ref in r["changed"]:
                    print(f"    changed: {ref}")
                for ref in r["added"]:
                    print(f"    new: {ref}")
            else:
                print(f"{r['code']}: no changes ({r['committed_count']} articles)")
    return 1 if any_change else 0


if __name__ == "__main__":
    raise SystemExit(main())
