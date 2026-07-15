"""The "news" checker: re-fetch each tracked law from the official gazette and report which
articles are NEW, REMOVED, or CHANGED versus the committed corpus. This is the detection
half of monitoring — it never auto-writes the citation store; changes are surfaced for a
human to verify (AGENTS.md #5), then ingested as new versions (append-only).

Run periodically (cron / the arq worker). The crawl-delay is enforced by the Playwright fetcher
(spec #4). Exit code 0 = no changes, 1 = changes detected (so a scheduler can alert).

    python scripts/check_law_updates.py [--json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_boe_law import parse_articles  # noqa: E402
from playwright_fetch import BrowserFetcher  # noqa: E402

CORPUS_DIR = pathlib.Path(__file__).resolve().parent / "seed_data" / "corpus"
SOURCES = CORPUS_DIR / "_sources.yaml"


def _by_ref(articles: list[dict]) -> dict[str, str]:
    return {a["article_ref"]: " ".join(a["article_text_ar"].split()) for a in articles}


def compute_diff(code: str, committed: dict[str, str], live: dict[str, str]) -> dict:
    """Pure set diff between committed and live article maps (no I/O, unit-testable)."""
    added = sorted(set(live) - set(committed))
    removed = sorted(set(committed) - set(live))
    changed = sorted(r for r in set(live) & set(committed) if live[r] != committed[r])
    return {"code": code, "added": added, "removed": removed, "changed": changed,
            "live_count": len(live), "committed_count": len(committed)}


def diff_law(src: dict, live_html: str) -> dict:
    corpus_path = CORPUS_DIR / src["corpus_file"]
    committed = _by_ref(yaml.safe_load(corpus_path.read_text(encoding="utf-8"))["articles"])
    live = _by_ref(parse_articles(live_html))
    return compute_diff(src["code"], committed, live)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    sources = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))["sources"]
    results = []
    # One persistent headless Chromium for the whole run; fetch enforces the crawl-delay and
    # returns fetch failures on a channel separate from diff results.
    with BrowserFetcher() as fetcher:
        for src in sources:
            outcome = fetcher.fetch(src["url"])
            if outcome.error or outcome.html is None:
                results.append({"code": src["code"], "error": outcome.error or "empty response"})
                continue
            try:
                results.append(diff_law(src, outcome.html))
            except Exception as e:  # noqa: BLE001 — a parse failure must not crash the run
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
