"""Readiness Score computes ONLY over reviewed findings (AGENTS.md #5). Pending findings
never move the score; rejected findings do not penalize."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contract, Finding, RegulationVersion
from app.services.scoring import compute_readiness_score


def _finding(contract, rv, severity, status) -> Finding:
    return Finding(
        contract_id=contract.id,
        regulation_version_id=rv.id,
        title_ar="ملاحظة",
        severity=severity,
        category="regulatory",
        review_status=status,
    )


async def test_score_ignores_pending_counts_reviewed_only(
    session: AsyncSession, contract: Contract, regulation_version: RegulationVersion
) -> None:
    session.add_all([
        _finding(contract, regulation_version, "critical", "accepted"),  # -40
        _finding(contract, regulation_version, "high", "pending"),       # excluded
        _finding(contract, regulation_version, "low", "rejected"),       # no penalty
        _finding(contract, regulation_version, "medium", "accepted"),    # -8
    ])
    await session.flush()

    result = await compute_readiness_score(session, contract.id)
    assert result.score == 52  # 100 - 40 - 8
    assert result.reviewed_count == 3  # the pending one is excluded
    assert result.accepted_count == 2


async def test_score_none_when_nothing_reviewed(
    session: AsyncSession, contract: Contract, regulation_version: RegulationVersion
) -> None:
    session.add(_finding(contract, regulation_version, "critical", "pending"))
    await session.flush()

    result = await compute_readiness_score(session, contract.id)
    assert result.score is None
    assert result.reviewed_count == 0


async def test_radar_review_when_accepted_high_but_no_critical(
    session: AsyncSession, contract: Contract, regulation_version: RegulationVersion
) -> None:
    # Covers the REVIEW branch: an accepted high (no critical) → REVIEW, 1 killer.
    from app.services.scoring.score import compute_radar

    session.add(_finding(contract, regulation_version, "high", "accepted"))
    await session.flush()
    radar = await compute_radar(session, contract.id)
    assert radar["verdict"] == "REVIEW"
    assert len(radar["killers"]) == 1
