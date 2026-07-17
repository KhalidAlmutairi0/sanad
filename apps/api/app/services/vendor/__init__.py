"""Vendor evaluation — dual-sandbox: Sandbox 1 extracts (raw text), Sandbox 2 gates/compares
(JSON only). This package is the Sandbox-2 side: no code path here reads a raw document."""
from app.services.vendor.compare import Comparison, annualized_tco, build_comparison
from app.services.vendor.gate import SAMA_OUTSOURCING_CHECKLIST, GateResult, evaluate_gate

__all__ = [
    "SAMA_OUTSOURCING_CHECKLIST", "GateResult", "evaluate_gate",
    "Comparison", "annualized_tco", "build_comparison",
]
