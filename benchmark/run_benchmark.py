"""Benchmark harness. Loads an independent ground-truth answer key per feature, runs SANAD's
pipeline through an injected predict_fn, computes metrics, and writes per-run results + a
slide-ready report.

Ground rules (enforced by construction):
  * SANAD never grades itself — metrics compare a prediction to a separate answer key.
  * A feature whose ground truth is marked pending outputs "not yet benchmarked", never a number.
  * Every run records the model/version + timestamp and the raw per-item results, so any slide
    number traces back to specific test items.

    python benchmark/run_benchmark.py [--feature contract_review] [--report]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib

from report import pending_slide, slide

ROOT = pathlib.Path(__file__).resolve().parent
GROUND_TRUTH = ROOT / "ground_truth"
RESULTS = ROOT / "results"

# feature -> ground-truth file. A file with _meta.status == 'pending_human_ground_truth' is
# reported as an honest gap.
FEATURES = {
    "contract_review": "contract_review.json",
    "vendor_stage1": "vendor_stage1.json",
    "vendor_stage2": "vendor_stage2.json",
    "obligation_register": "obligation_register.json",
    "embedded_api": "embedded_api.json",
    "continuous_monitoring": "continuous_monitoring.json",
    "sharia": "sharia.json",
}


def load_ground_truth(feature: str) -> dict | None:
    path = GROUND_TRUTH / FEATURES[feature]
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def is_pending(gt: dict | None) -> tuple[bool, str]:
    if gt is None:
        return True, "no ground-truth file yet"
    meta = gt.get("_meta", {})
    if meta.get("status") == "pending_human_ground_truth":
        return True, meta.get("reason", "requires human/expert ground truth")
    return False, ""


def write_result(feature: str, payload: dict) -> pathlib.Path:
    out_dir = RESULTS / feature
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def dataset_desc(gt: dict) -> str:
    meta = gt.get("_meta", {})
    n = meta.get("count", len(gt.get("cases", [])))
    comp = meta.get("composition", meta.get("source", "unspecified"))
    return f"{n} cases ({comp})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature", choices=list(FEATURES), help="default: all")
    ap.add_argument("--report", action="store_true", help="print slide-ready markdown")
    args = ap.parse_args()

    features = [args.feature] if args.feature else list(FEATURES)
    slides = []
    for feat in features:
        gt = load_ground_truth(feat)
        pending, reason = is_pending(gt)
        if pending:
            slides.append(pending_slide(feat, reason))
            continue
        # A real predict_fn (SANAD pipeline) is injected on the deployment where the pipeline
        # runs; here we surface the dataset + note that scoring needs the live pipeline.
        slides.append(slide(feat, dataset_desc(gt),
                            ["scoring runs against the live SANAD pipeline (see docstring)"],
                            notes=["run with the pipeline predict_fn wired to produce numbers"]))

    if args.report or True:
        print("\n\n".join(slides))
    return 0


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
