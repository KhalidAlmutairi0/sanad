"""DB-free unit tests: clause segmentation + violation-cost extraction."""
from __future__ import annotations

from app.services.analysis.violation_cost import extract_violation_cost
from app.services.extraction import segment_clauses


def test_segment_splits_arabic_and_english_by_marker() -> None:
    text = (
        "المادة 1: تُعالَج البيانات الشخصية بموافقة صاحبها.\n"
        "المادة 2: يجوز نقل البيانات خارج المملكة وفق الضوابط.\n\n"
        "Article 3: The employer shall not exceed eight hours per day."
    )
    clauses = segment_clauses(text)
    assert len(clauses) == 3
    assert clauses[0].text_ar and clauses[0].text_en is None
    assert clauses[2].text_en and clauses[2].text_ar is None


def test_violation_cost_parses_arabic_word_amount() -> None:
    phrase, mn, mx = extract_violation_cost(
        "يعاقب بالسجن مدة لا تزيد على سنتين وبغرامة لا تزيد على ثلاثة ملايين ريال."
    )
    assert phrase is not None
    assert mx == 3_000_000.0


def test_violation_cost_none_for_non_penalty_article() -> None:
    phrase, mn, mx = extract_violation_cost("يستحق العامل إجازة سنوية واحد وعشرين يوماً.")
    assert phrase is None and mn is None and mx is None
