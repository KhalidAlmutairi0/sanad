"""Contract Readiness Score — computed ONLY over human-reviewed findings (AGENTS.md #5).
Pending findings never affect the score."""
from app.services.scoring.score import compute_readiness_score

__all__ = ["compute_readiness_score"]
