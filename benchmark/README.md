# SANAD Benchmark Suite

Measures each feature against an **independent ground-truth answer key** and produces
slide-ready numbers for the pitch.

## The one rule: SANAD never grades its own output

Every metric in `metrics.py` takes `(predicted, truth)` where `truth` comes from a file in
`ground_truth/` that a **human** wrote — never from a model. A model scoring its own answer is
not a benchmark, it's a hallucination with a percentage sign.

Consequences of that rule, all enforced by construction:

- **No ground truth → no number.** A feature whose `ground_truth/<feature>.json` is marked
  `{"_meta": {"status": "pending_human_ground_truth"}}` is reported as *"Not yet benchmarked —
  no independent ground truth"* with the reason. An honest gap is safer in front of a bank's
  risk team than a fabricated 98%.
- **Test-set size + composition ship on the slide.** `synthetic` vs `real` is stated every
  time (`report.slide` → "Tested on: N cases (...)"). Synthetic datasets are for wiring and
  sanity only; you may not quote their numbers to a client until they're replaced with real,
  re-labeled cases.
- **High-confidence-wrong and disagreements are listed, never averaged away.** For high-stakes
  features (Sharia), a single wrong call stays individually visible
  (`agreement_rate` lists disagreements; `high_confidence_wrong` surfaces confident misses).
- **Every run is traceable.** `results/<feature>/<timestamp>.json` records the model/version and
  the raw per-item results, so any slide number traces back to specific items.

## Layout

```
metrics.py            pure metric functions (predicted, truth) -> dict; no model calls
report.py             slide() / pending_slide() markdown generators
run_benchmark.py      harness: load ground truth, mark pending, write results, print slides
ground_truth/         the answer keys (human-authored) + pending markers
results/<feature>/    per-run outputs (git-ignored)
tests/                pure tests for metrics + report + harness
```

## Run

```bash
python benchmark/run_benchmark.py            # all features
python benchmark/run_benchmark.py --feature contract_review --report
```

Features with real ground truth score against the live SANAD pipeline via an injected
`predict_fn` on the deployment where the pipeline runs; the checked-in harness surfaces the
dataset and the pending gaps.

## Adding a real dataset

1. Collect real cases (contracts, proposals, regulatory changes).
2. Have a **human** (a domain/Sharia expert where the stakes require it) write the answer key.
3. Replace the synthetic file; set `_meta.source = "real"` and `_meta.composition`.
4. Never let SANAD's own output become the ground truth for the next run.
