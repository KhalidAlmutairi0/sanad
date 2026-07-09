"""Citation gate — a finding cannot exist without a resolvable citation (AGENTS.md #1).

Two layers enforce this: the DB NOT NULL FK on findings.regulation_version_id, AND this
application gate, which verifies the referenced version actually resolves in the evidence
cache before any finding is written. A blocked draft is audited as citation_rejected."""
from app.services.citations.gate import create_finding_guarded, resolve_citation

__all__ = ["create_finding_guarded", "resolve_citation"]
