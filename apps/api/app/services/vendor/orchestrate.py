"""Vendor evaluation orchestration: ties Sandbox 1 (extract) → Sandbox 2 (gate/compare).

extract_and_gate runs per submission (reads sanitized text, produces + stores the JSON, applies
the Stage-1 gate, audits every exclusion against its SAMA section). compute_results is pure — it
rebuilds the Stage-1 scorecards and the Stage-2 comparison from the STORED extraction JSON only,
so results are cheap to re-fetch and Sandbox 2 never re-touches raw text.
"""
from __future__ import annotations

from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import VendorSubmission
from app.services.audit import write_audit
from app.services.vendor.compare import build_comparison
from app.services.vendor.extract import extract_vendor
from app.services.vendor.gate import evaluate_gate

ACTOR_ANALYSIS = "analysis"

BANNER = (
    "يحدد هذا التقرير أفضل عقد بناءً على الامتثال التنظيمي والبيانات المذكورة في العروض. وهو ليس "
    "بديلاً عن التحقق المستقل من وضع المورد (المالي والأمني والمراجع)."
)


async def extract_and_gate(
    session: AsyncSession, submission: VendorSubmission, clean_text: str, *, actor: str
) -> None:
    """Sandbox 1 extract → store JSON → Stage-1 gate → stage1_passed. Audits each exclusion."""
    extraction = await extract_vendor(
        clean_text, vendor_id=submission.vendor_name, filename=submission.source_filename
    )
    gate = evaluate_gate(extraction.get("compliance_fields", []))
    submission.extraction = extraction
    submission.stage1_passed = gate.passed
    submission.status = "extracted"

    for exc in gate.exclusions:
        await write_audit(
            session, actor=actor, action="vendor_stage1_exclusion",
            target=str(submission.id), verdict="denied",
            detail={"vendor": submission.vendor_name, "requirement_id": exc.requirement_id,
                    "sama_section": exc.section, "reason": "mandatory_missing"},
        )
    for flag in extraction.get("security_flags", []):
        await write_audit(
            session, actor=actor, action="vendor_security_flag",
            target=str(submission.id), verdict="n-a",
            detail={"vendor": submission.vendor_name, "type": flag.get("type"),
                    "location": flag.get("location")},
        )


def _vendor_view(sub: VendorSubmission) -> dict:
    ext = sub.extraction or {}
    gate = evaluate_gate(ext.get("compliance_fields", []))
    return {
        "submission_id": str(sub.id),
        "vendor_name": sub.vendor_name,
        "status": sub.status,
        "stage1_passed": gate.passed if ext else None,
        "scorecard": [asdict(i) for i in gate.scorecard] if ext else [],
        "exclusions": [asdict(i) for i in gate.exclusions] if ext else [],
        "security_flag_count": len(ext.get("security_flags", [])),
    }


def compute_results(title: str, status: str, submissions: list[VendorSubmission]) -> dict:
    """Rebuild Stage-1 scorecards (all vendors) + Stage-2 comparison (passers only) from stored
    extractions. Pure; no raw text, no LLM."""
    vendors = [_vendor_view(s) for s in submissions]

    passers = [s for s in submissions if s.extraction and evaluate_gate(
        (s.extraction or {}).get("compliance_fields", [])).passed]
    comparison = None
    if passers:
        comp = build_comparison([
            {"vendor_id": s.vendor_name,
             "pricing_fields": (s.extraction or {}).get("pricing_fields", {}),
             "feature_fields": (s.extraction or {}).get("feature_fields", []),
             "self_reported_background": (s.extraction or {}).get("self_reported_background", {})}
            for s in passers
        ])
        comparison = {
            "vendor_ids": comp.vendor_ids,
            "rows": [asdict(r) for r in comp.rows],
            "currency_mismatch": comp.currency_mismatch,
            "composite_score": None,  # deltas only, never a single score
        }

    return {
        "title": title, "status": status, "banner": BANNER,
        "vendors": vendors,
        "comparison": comparison,
        # self-reported background is surfaced separately, always labeled as unverified claims.
        "self_reported": [
            {"vendor_name": s.vendor_name,
             "background": (s.extraction or {}).get("self_reported_background", {})}
            for s in submissions if s.extraction
        ],
    }
