"""Benchmark metrics (pure). Every number a slide shows is computed here from a prediction and
an INDEPENDENT ground-truth answer key — SANAD never grades its own output.

All functions are deterministic and take (predicted, truth); none call a model.
"""
from __future__ import annotations

import math


def prf(predicted: set, truth: set) -> dict:
    """Precision / recall / F1 for set detection (e.g. which clauses were found)."""
    tp = len(predicted & truth)
    fp = len(predicted - truth)
    fn = len(truth - predicted)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
            "tp": tp, "fp": fp, "fn": fn}


def label_accuracy(predicted: dict, truth: dict) -> dict:
    """Per-item label agreement (e.g. clause status present|weak|missing)."""
    keys = set(truth)
    correct = sum(1 for k in keys if predicted.get(k) == truth[k])
    return {"accuracy": round(correct / len(keys), 4) if keys else 0.0, "n": len(keys),
            "wrong": sorted(k for k in keys if predicted.get(k) != truth[k])}


def citation_accuracy(predicted: dict[str, str], truth: dict[str, str]) -> dict:
    """% of findings whose cited section matches the ground-truth section."""
    keys = set(truth) & set(predicted)
    correct = sum(1 for k in keys if predicted[k] == truth[k])
    return {"citation_accuracy": round(correct / len(keys), 4) if keys else 0.0, "n": len(keys)}


def false_negative_rate_mandatory(predicted_missing: set, truth_missing: set) -> float:
    """Of the clauses that are TRULY missing (highest-stakes), the fraction we failed to flag."""
    if not truth_missing:
        return 0.0
    missed = truth_missing - predicted_missing
    return round(len(missed) / len(truth_missing), 4)


def percentiles(latencies_ms: list[float]) -> dict:
    """p50 / p95 latency."""
    if not latencies_ms:
        return {"p50": None, "p95": None, "n": 0}
    s = sorted(latencies_ms)

    def pct(p: float) -> float:
        idx = min(len(s) - 1, max(0, math.ceil(p / 100 * len(s)) - 1))
        return s[idx]

    return {"p50": pct(50), "p95": pct(95), "n": len(s)}


def agreement_rate(predicted: dict, truth: dict) -> dict:
    """Agreement with an expert answer key (e.g. Sharia). Disagreements are listed individually,
    NOT averaged away — a single wrong call must stay visible."""
    keys = set(truth)
    disagreements = sorted(k for k in keys if predicted.get(k) != truth[k])
    agree = len(keys) - len(disagreements)
    return {"agreement_rate": round(agree / len(keys), 4) if keys else 0.0,
            "disagreements": disagreements, "n": len(keys)}


def high_confidence_wrong(items: list[dict], *, confidence_key: str = "confidence",
                          correct_key: str = "correct", threshold: str = "high") -> list[dict]:
    """The most demo-damaging cases: SANAD was confident but wrong. Flagged, not hidden."""
    return [i for i in items if i.get(confidence_key) == threshold and not i.get(correct_key)]
