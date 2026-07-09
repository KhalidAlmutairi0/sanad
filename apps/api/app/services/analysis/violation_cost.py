"""Extract a statutory fine range from a cited article's text (Violation Cost).

The number comes FROM the violated article itself (PRD feature 3), never invented. Handles
Arabic digit amounts and common word-scales (ألف/آلاف, مليون/ملايين). Returns (min, max) as
best-effort; either may be None. The human-readable phrase is kept verbatim separately.
"""
from __future__ import annotations

import re

# Arabic-Indic digits -> ASCII.
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_WORD_UNITS = {
    "مليون": 1_000_000, "ملايين": 1_000_000, "مليونين": 2_000_000,
    "ألف": 1_000, "آلاف": 1_000, "الف": 1_000,
}
_WORD_NUMS = {
    "واحد": 1, "مليونين": 2, "اثنين": 2, "اثنان": 2, "ثلاثة": 3, "أربعة": 4, "خمسة": 5,
    "ستة": 6, "سبعة": 7, "ثمانية": 8, "تسعة": 9, "عشرة": 10,
}
_FINE_HINT = re.compile(r"(?:غرامة|ريال)")


def _word_amount(text: str) -> int | None:
    tokens = text.split()
    for i, tok in enumerate(tokens):
        if tok in _WORD_UNITS:
            scale = _WORD_UNITS[tok]
            if tok == "مليونين":
                return scale
            mult = 1
            if i > 0 and tokens[i - 1] in _WORD_NUMS:
                mult = _WORD_NUMS[tokens[i - 1]]
            return mult * scale
    return None


def extract_violation_cost(article_text_ar: str) -> tuple[str | None, float | None, float | None]:
    """Return (phrase, min, max). phrase is the fine sentence verbatim, or None if the
    article carries no monetary penalty."""
    if not _FINE_HINT.search(article_text_ar):
        return (None, None, None)

    # The sentence mentioning the penalty (verbatim), for display.
    phrase = None
    for sentence in re.split(r"[.؟!\n]", article_text_ar):
        if "غرامة" in sentence or "ريال" in sentence:
            phrase = sentence.strip()
            break

    scope = phrase or article_text_ar
    normalized = scope.translate(_AR_DIGITS)
    digit_amounts = [float(m.replace(",", "")) for m in re.findall(r"\d[\d,]{2,}", normalized)]
    word_amount = _word_amount(scope)

    amounts = digit_amounts + ([float(word_amount)] if word_amount else [])
    if not amounts:
        return (phrase, None, None)
    return (phrase, min(amounts), max(amounts))
