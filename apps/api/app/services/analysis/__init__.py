"""Analysis: LLM finding generation over retrieved evidence. Every finding cites a
provided candidate BY INDEX; the regulation_version_id is resolved server-side from the
trusted candidate list, so the model cannot invent a citation (Zero Unsourced Findings)."""
from app.services.analysis.findings import generate_findings_for_contract
from app.services.analysis.idea_report import generate_idea_report

__all__ = ["generate_findings_for_contract", "generate_idea_report"]
