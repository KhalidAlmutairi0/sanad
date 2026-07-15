"""OCR mean-confidence aggregation (spec #3). Browser/Tesseract-free — pure list math."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from extract import _mean_confidence  # noqa: E402


def test_mean_of_valid_confidences():
    assert _mean_confidence([95, 90, 85]) == 90.0


def test_ignores_minus_one_and_blanks():
    # Tesseract emits -1 for non-text boxes; strings arrive from image_to_data DICT.
    assert _mean_confidence(["-1", "80", "90", "", None]) == 85.0


def test_empty_is_zero():
    assert _mean_confidence([]) == 0.0


def test_all_invalid_is_zero():
    assert _mean_confidence(["-1", "-1"]) == 0.0
