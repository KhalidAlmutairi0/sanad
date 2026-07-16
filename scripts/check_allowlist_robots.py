"""Continuous (on-demand) robots.txt check for the source/egress allowlist.

For every tracked source domain, fetch its live robots.txt and confirm automated access to the
content path is still permitted. This is the "keep checking النطاقات المسموح بها" guard: run it
before enabling a source and periodically after, so a regulator flipping to Disallow is caught
rather than silently violated. Scheduling stays manual (no cron) — this is a runnable check.

Exit code 0 = all still allowed; 1 = at least one domain now disallows (so a scheduler/CI can
alert). Respects a polite delay between domains.

    python scripts/check_allowlist_robots.py [--json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from robots_check import path_allowed  # noqa: E402

_UA = "SANAD-compliance-research/1.0 (regulatory corpus; contact: khalid.a.almutairi0@gmail.com)"
_DELAY_SECONDS = 5

# domain -> a representative content path we actually fetch from it.
TRACKED = {
    "laws.boe.gov.sa": "/BoeLaws/Laws/LawDetails/",
    "moj.gov.sa": "/ar/SystemsAndRegulations",
    "cma.gov.sa": "/en/RulesRegulations/Regulations/",
    "uqn.gov.sa": "/",
    "sama.gov.sa": "/",  # tracked for egress; SAMA rulebook is handled separately (Disallow:/)
}


def _fetch_robots(domain: str) -> str | None:
    url = f"https://{domain}/robots.txt"
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 — fixed official hosts
            return r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001 — unreachable robots is reported, not fatal
        return None if False else f"__ERROR__:{type(e).__name__}"


def check_domain(domain: str, path: str, robots_text: str | None) -> dict:
    if robots_text is None:
        return {"domain": domain, "allowed": None, "note": "no robots.txt (treat as allowed)"}
    if robots_text.startswith("__ERROR__:"):
        return {"domain": domain, "allowed": None, "note": robots_text}
    allowed = path_allowed(robots_text, path, _UA) and path_allowed(robots_text, path, "*")
    return {"domain": domain, "allowed": allowed, "path": path}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = []
    for i, (domain, path) in enumerate(TRACKED.items()):
        if i:
            time.sleep(_DELAY_SECONDS)
        results.append(check_domain(domain, path, _fetch_robots(domain)))

    disallowed = [r for r in results if r["allowed"] is False]
    if args.json:
        print(json.dumps({"results": results, "disallowed": [r["domain"] for r in disallowed]},
                         ensure_ascii=False, indent=2))
    else:
        for r in results:
            state = "DISALLOWED" if r["allowed"] is False else ("allowed" if r["allowed"] else "unknown")
            print(f"{r['domain']:20} {state}  {r.get('note', r.get('path', ''))}")
        if disallowed:
            print(f"\n⚠ {len(disallowed)} domain(s) now DISALLOW automation — do not fetch: "
                  + ", ".join(r["domain"] for r in disallowed))
    return 1 if disallowed else 0


if __name__ == "__main__":
    raise SystemExit(main())
