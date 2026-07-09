"""Segment sanitized contract text into clauses.

Heuristic (no LLM): split on clause/article markers (Arabic + English) and blank lines,
then attach each segment's text to text_ar or text_en based on its dominant script. Arabic
and English are never mixed on one clause field (bilingual rule)."""
from __future__ import annotations

import re
from dataclasses import dataclass

# Lines that begin a new clause. Arabic: المادة / البند / ordinal words / numbered.
_MARKERS = re.compile(
    r"^(?:\s*(?:المادة|البند|الفصل|الشرط)\b"
    r"|\s*(?:أولاً|ثانياً|ثالثاً|رابعاً|خامساً)\b"
    r"|\s*(?:Article|Section|Clause)\b"
    r"|\s*\d{1,3}\s*[.)\-–]"
    r"|\s*\([A-Za-z0-9٠-٩]{1,3}\))",
    re.IGNORECASE,
)

_ARABIC = re.compile(r"[؀-ۿ]")
_MIN_CHARS = 15


@dataclass
class ClauseSegment:
    ordinal: int
    text_ar: str | None
    text_en: str | None


def _is_arabic(text: str) -> bool:
    ar = len(_ARABIC.findall(text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return ar >= latin


def _split_raw(text: str) -> list[str]:
    lines = text.splitlines()
    segments: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            block = " ".join(ln.strip() for ln in current if ln.strip())
            if len(block) >= _MIN_CHARS:
                segments.append(block)
            current.clear()

    for line in lines:
        if not line.strip():
            flush()
            continue
        if _MARKERS.match(line) and current:
            flush()
        current.append(line)
    flush()

    # Fallback: if nothing segmented (e.g. one wall of text), split by sentence-ish chunks.
    if not segments and text.strip():
        chunks = re.split(r"(?<=[.۔])\s+", text.strip())
        segments = [c.strip() for c in chunks if len(c.strip()) >= _MIN_CHARS]
    return segments


def segment_clauses(text: str) -> list[ClauseSegment]:
    result: list[ClauseSegment] = []
    for i, block in enumerate(_split_raw(text), start=1):
        if _is_arabic(block):
            result.append(ClauseSegment(ordinal=i, text_ar=block, text_en=None))
        else:
            result.append(ClauseSegment(ordinal=i, text_ar=None, text_en=block))
    return result
