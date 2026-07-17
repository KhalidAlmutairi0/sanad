"""Stage 1 — SAMA outsourcing compliance gate (pure, JSON-only).

Runs inside "Sandbox 2": it sees ONLY the structured compliance_fields extracted by Sandbox 1,
never raw document text, so nothing here can be steered by injection hidden in a proposal.

The gate is built on SAMA's Rules on Outsourcing (Sections G–Q). The real SAMA article text is
not yet in the corpus (SAMA is robots-blocked; supplied separately), so each requirement carries
its section reference and findings are flagged `sama_source_pending=True` until that text is
ingested — at which point the citation resolves to the actual rule. The checklist STRUCTURE is
sourced (named SAMA sections); only the verbatim text is pending.
"""
from __future__ import annotations

from dataclasses import dataclass, field

STATUS_PRESENT = "present"
STATUS_WEAK = "weak"
STATUS_MISSING = "missing"
_VALID_STATUS = {STATUS_PRESENT, STATUS_WEAK, STATUS_MISSING}


@dataclass(frozen=True)
class Requirement:
    requirement_id: str      # e.g. SAMA-OUTS-I
    section: str             # SAMA section letter
    description_ar: str
    mandatory: bool          # a mandatory section that is MISSING auto-excludes the vendor


# SAMA Rules on Outsourcing checklist. Governance sections (G, H) are recommended; the
# contractual / security / risk / continuity / access-audit sections are mandatory.
SAMA_OUTSOURCING_CHECKLIST: tuple[Requirement, ...] = (
    Requirement("SAMA-OUTS-G", "G", "متطلبات رفع التقارير", mandatory=False),
    Requirement("SAMA-OUTS-H", "H", "تقييم خيارات الإسناد", mandatory=False),
    Requirement("SAMA-OUTS-I", "I", "الترتيبات التعاقدية", mandatory=True),
    Requirement("SAMA-OUTS-K", "K", "سرية البيانات وأمنها", mandatory=True),
    Requirement("SAMA-OUTS-L", "L", "الرقابة على الإسناد ومتابعته", mandatory=True),
    Requirement("SAMA-OUTS-M", "M", "تقييم المخاطر", mandatory=True),
    Requirement("SAMA-OUTS-N", "N", "إدارة استمرارية الأعمال", mandatory=True),
    Requirement("SAMA-OUTS-O", "O", "الوصول إلى البيانات", mandatory=True),
    Requirement("SAMA-OUTS-P", "P", "المتابعة والإشراف", mandatory=True),
    Requirement("SAMA-OUTS-Q", "Q", "ترتيبات التدقيق", mandatory=True),
)
_BY_ID = {r.requirement_id: r for r in SAMA_OUTSOURCING_CHECKLIST}


@dataclass
class ScorecardItem:
    requirement_id: str
    section: str
    description_ar: str
    mandatory: bool
    status: str            # present | weak | missing (missing = absent from extraction too)
    document_location: str | None  # where in the VENDOR doc it was found (Sandbox 1 citation)
    sama_source_pending: bool = True  # real SAMA rule text not yet ingested


@dataclass
class GateResult:
    passed: bool
    scorecard: list[ScorecardItem]
    exclusions: list[ScorecardItem] = field(default_factory=list)  # mandatory + missing


def evaluate_gate(compliance_fields: list[dict]) -> GateResult:
    """Evaluate one vendor's extracted compliance_fields against the SAMA checklist.

    A mandatory section that is missing (or absent from the extraction) excludes the vendor.
    'weak' is reported on the scorecard but does not auto-exclude (per spec). Unknown
    requirement_ids in the input are ignored — the checklist is the authority, not the document.
    """
    by_req: dict[str, dict] = {}
    for f in compliance_fields:
        rid = f.get("requirement_id")
        if rid in _BY_ID:
            by_req[rid] = f  # last one wins if duplicated

    scorecard: list[ScorecardItem] = []
    exclusions: list[ScorecardItem] = []
    for req in SAMA_OUTSOURCING_CHECKLIST:
        f = by_req.get(req.requirement_id)
        status = f.get("status") if f and f.get("status") in _VALID_STATUS else STATUS_MISSING
        loc = None
        if f and isinstance(f.get("source_citation"), dict):
            loc = f["source_citation"].get("document_location")
        item = ScorecardItem(
            requirement_id=req.requirement_id, section=req.section,
            description_ar=req.description_ar, mandatory=req.mandatory,
            status=status, document_location=loc,
        )
        scorecard.append(item)
        if req.mandatory and status == STATUS_MISSING:
            exclusions.append(item)

    return GateResult(passed=len(exclusions) == 0, scorecard=scorecard, exclusions=exclusions)
