"""Pure tests for benchmark metrics. No model calls, no I/O — deterministic answer keys."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import metrics  # noqa: E402


def test_prf_perfect_and_partial():
    assert metrics.prf({"a", "b"}, {"a", "b"}) == {
        "precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 2, "fp": 0, "fn": 0}
    r = metrics.prf({"a", "x"}, {"a", "b"})
    assert r["tp"] == 1 and r["fp"] == 1 and r["fn"] == 1
    assert r["precision"] == 0.5 and r["recall"] == 0.5


def test_prf_empty_never_divides_by_zero():
    assert metrics.prf(set(), set()) == {
        "precision": 0.0, "recall": 0.0, "f1": 0.0, "tp": 0, "fp": 0, "fn": 0}


def test_label_accuracy_scores_only_truth_keys_and_lists_wrong():
    pred = {"I": "present", "K": "present", "N": "present"}
    truth = {"I": "present", "K": "missing"}
    r = metrics.label_accuracy(pred, truth)
    assert r["n"] == 2 and r["accuracy"] == 0.5 and r["wrong"] == ["K"]


def test_citation_accuracy_only_over_shared_keys():
    r = metrics.citation_accuracy({"f1": "SAMA-K", "f2": "SAMA-Z"}, {"f1": "SAMA-K", "f3": "SAMA-Q"})
    assert r["n"] == 1 and r["citation_accuracy"] == 1.0


def test_false_negative_rate_mandatory_is_the_scary_one():
    # truly missing = {K, Q}; we only flagged K -> we missed Q -> 0.5
    assert metrics.false_negative_rate_mandatory({"K"}, {"K", "Q"}) == 0.5
    assert metrics.false_negative_rate_mandatory(set(), set()) == 0.0


def test_percentiles():
    r = metrics.percentiles([10, 20, 30, 40, 100])
    assert r["n"] == 5 and r["p50"] == 30 and r["p95"] == 100
    assert metrics.percentiles([]) == {"p50": None, "p95": None, "n": 0}


def test_agreement_rate_lists_disagreements_individually():
    pred = {"c1": "compliant", "c2": "compliant", "c3": "non_compliant"}
    truth = {"c1": "compliant", "c2": "non_compliant", "c3": "non_compliant"}
    r = metrics.agreement_rate(pred, truth)
    assert r["disagreements"] == ["c2"] and r["n"] == 3


def test_high_confidence_wrong_surfaces_confident_misses():
    items = [
        {"id": 1, "confidence": "high", "correct": True},
        {"id": 2, "confidence": "high", "correct": False},
        {"id": 3, "confidence": "low", "correct": False},
    ]
    got = metrics.high_confidence_wrong(items)
    assert [i["id"] for i in got] == [2]
