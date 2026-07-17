"""Tests for the report/harness honesty guarantees: pending features never emit a number,
and every real slide states its test-set size + composition."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import report  # noqa: E402
import run_benchmark as rb  # noqa: E402


def test_pending_slide_has_no_number_and_states_the_gap():
    s = report.pending_slide("sharia", "needs a qualified Sharia advisor")
    assert "Not yet benchmarked" in s
    assert "needs a qualified Sharia advisor" in s
    assert "%" not in s


def test_slide_states_dataset_and_flags_notes():
    s = report.slide("contract_review", "2 cases (synthetic)", ["f1: 0.9"], notes=["synthetic only"])
    assert "Tested on: 2 cases (synthetic)" in s
    assert "⚠ synthetic only" in s


def test_is_pending_detects_marker():
    assert rb.is_pending({"_meta": {"status": "pending_human_ground_truth", "reason": "x"}}) == (True, "x")
    assert rb.is_pending(None)[0] is True
    assert rb.is_pending({"_meta": {"source": "synthetic"}, "cases": [{}]})[0] is False


def test_every_registered_feature_has_a_ground_truth_file():
    for feat, fname in rb.FEATURES.items():
        assert (rb.GROUND_TRUTH / fname).exists(), f"missing ground truth for {feat}"


def test_pending_features_carry_a_reason():
    # Sharia + monitoring must stay honest gaps until a human answer key exists.
    for feat in ("sharia", "continuous_monitoring"):
        pending, reason = rb.is_pending(rb.load_ground_truth(feat))
        assert pending and reason


def test_dataset_desc_reports_count_and_composition():
    gt = rb.load_ground_truth("contract_review")
    desc = rb.dataset_desc(gt)
    assert "cases" in desc and ("synthetic" in desc.lower())
