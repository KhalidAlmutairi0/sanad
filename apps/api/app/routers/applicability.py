"""Contract Applicability Engine (spec: regulatory-applicability detection).

Determines, per existing contract, whether a regulatory update applies and what action is due.
Only HUMAN-REVIEWED applicability classifications feed the buckets; llm_draft ones surface as a
'pending_review' count, never as actionable findings — a wrong 'grandfathered' call could make a
bank miss a real remediation deadline. Every finding carries the triggering article, the matched
clause, and the citation that proves the applicability_type (Zero Unsourced Findings).
"""
from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session, require_roles
from app.core.errors import SanadError
from app.models import Clause, Contract, Regulation, RegulationApplicability, RegulationVersion, User
from app.schemas.applicability import (
    ApplicabilityDraft,
    ApplicabilityFinding,
    ArticleRef,
    ClauseRef,
    ContractApplicability,
    ReviewQueue,
    ReviewRequest,
)
from app.services.applicability.classify import classify_article
from app.services.applicability.engine import (
    APPLICABILITY_TYPES,
    EXEMPT_GRANDFATHERED,
    NEEDS_REMEDIATION,
    evaluate,
)
from app.services.audit import write_audit
from app.services.retrieval import retrieve_candidates

router = APIRouter(prefix="/applicability", tags=["applicability"])


async def _article_ref(session: AsyncSession, rv_id: uuid.UUID | None) -> ArticleRef | None:
    if rv_id is None:
        return None
    row = (
        await session.execute(
            select(RegulationVersion, Regulation.code)
            .join(Regulation, Regulation.id == RegulationVersion.regulation_id)
            .where(RegulationVersion.id == rv_id)
        )
    ).first()
    if row is None:
        return None
    rv, code = row
    return ArticleRef(regulation_version_id=rv.id, regulation_code=code,
                      article_ref=rv.article_ref, source_url=rv.source_url)


def _draft(a: RegulationApplicability, source: ArticleRef, cite: ArticleRef | None) -> ApplicabilityDraft:
    return ApplicabilityDraft(
        id=a.id, source_article=source, applicability_type=a.applicability_type,
        effective_date=a.effective_date, deadline_date=a.deadline_date,
        classification_confidence=a.classification_confidence, classification_citation=cite,
    )


@router.post("/classify/{regulation_version_id}", response_model=ApplicabilityDraft, status_code=201)
async def classify(
    regulation_version_id: uuid.UUID,
    user: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> ApplicabilityDraft:
    """LLM first pass → llm_draft. Does NOT make the classification actionable."""
    try:
        a = await classify_article(session, regulation_version_id)
    except ValueError:
        raise SanadError("not_found")
    await session.commit()
    source = await _article_ref(session, a.regulation_version_id)
    cite = await _article_ref(session, a.classification_citation_version_id)
    return _draft(a, source, cite)


@router.get("/review-queue", response_model=ReviewQueue)
async def review_queue(
    _: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> ReviewQueue:
    rows = (
        await session.execute(
            select(RegulationApplicability)
            .where(RegulationApplicability.classification_confidence == "llm_draft")
            .order_by(RegulationApplicability.created_at.desc())
        )
    ).scalars().all()
    items = []
    for a in rows:
        source = await _article_ref(session, a.regulation_version_id)
        cite = await _article_ref(session, a.classification_citation_version_id)
        if source:
            items.append(_draft(a, source, cite))
    return ReviewQueue(items=items)


@router.post("/{applicability_id}/review", response_model=ApplicabilityDraft)
async def review(
    applicability_id: uuid.UUID,
    body: ReviewRequest,
    user: User = Depends(require_roles("reviewer", "admin")),
    session: AsyncSession = Depends(get_session),
) -> ApplicabilityDraft:
    """Human confirms the classification. Requires a scope citation; promotes to human_reviewed
    so it can affect live contracts."""
    a = await session.get(RegulationApplicability, applicability_id)
    if a is None:
        raise SanadError("not_found")
    if body.applicability_type not in APPLICABILITY_TYPES:
        raise SanadError("validation_failed", "نوع الانطباق غير صالح")
    # The scope citation must resolve to a real article (Zero Unsourced: the classification
    # itself is sourced, not inferred).
    cite = await session.get(RegulationVersion, body.classification_citation_version_id)
    if cite is None:
        raise SanadError("validation_failed", "استشهاد نطاق الانطباق غير موجود")

    a.applicability_type = body.applicability_type
    a.effective_date = body.effective_date
    a.deadline_date = body.deadline_date if body.applicability_type == "retroactive_with_deadline" else None
    a.classification_citation_version_id = body.classification_citation_version_id
    a.classification_confidence = "human_reviewed"
    a.reviewed_by = user.id
    await write_audit(
        session, actor=str(user.id), action="applicability_reviewed",
        target=str(a.regulation_version_id), verdict="allowed",
        detail={"applicability_type": a.applicability_type},
    )
    await session.commit()
    source = await _article_ref(session, a.regulation_version_id)
    cite_ref = await _article_ref(session, a.classification_citation_version_id)
    return _draft(a, source, cite_ref)


@router.get("/contract/{contract_id}", response_model=ContractApplicability)
async def contract_applicability(
    contract_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ContractApplicability:
    """The three buckets for one contract. Only human_reviewed classifications are evaluated;
    llm_draft ones are counted as pending_review."""
    contract = await session.get(Contract, contract_id)
    if contract is None:
        raise SanadError("not_found")

    pending = (
        await session.execute(
            select(func.count()).select_from(RegulationApplicability).where(
                RegulationApplicability.classification_confidence == "llm_draft"
            )
        )
    ).scalar_one()

    needs: list[ApplicabilityFinding] = []
    grand: list[ApplicabilityFinding] = []
    compliant: list[ApplicabilityFinding] = []

    if contract.signed_date is not None:
        clauses = (
            await session.execute(select(Clause).where(Clause.contract_id == contract_id).order_by(Clause.ordinal))
        ).scalars().all()

        seen: set[tuple[uuid.UUID, uuid.UUID | None]] = set()
        for clause in clauses:
            text = clause.text_ar or clause.text_en
            if not text:
                continue
            candidates = await retrieve_candidates(session, text, k=4, citable_only=True)
            for cand in candidates:
                appl = (
                    await session.execute(
                        select(RegulationApplicability).where(
                            RegulationApplicability.regulation_version_id == cand.regulation_version_id,
                            RegulationApplicability.classification_confidence == "human_reviewed",
                        )
                    )
                ).scalar_one_or_none()
                if appl is None:
                    continue
                key = (cand.regulation_version_id, clause.id)
                if key in seen:
                    continue
                seen.add(key)

                # MVP proxy: a clause that retrieved this article addresses its subject, so for a
                # grandfather rule we treat the prior term as present. Human review refines this.
                decision = evaluate(
                    contract.signed_date, appl.applicability_type, appl.effective_date,
                    deadline_date=appl.deadline_date, clause_matches_prior_term=True,
                )
                source = await _article_ref(session, cand.regulation_version_id)
                cite = await _article_ref(session, appl.classification_citation_version_id)
                finding = ApplicabilityFinding(
                    flag=decision.flag, due_date=decision.due_date, source_article=source,
                    classification_citation=cite,
                    clause=ClauseRef(clause_id=clause.id, ordinal=clause.ordinal, text_ar=clause.text_ar),
                )
                if decision.flag == NEEDS_REMEDIATION:
                    needs.append(finding)
                elif decision.flag == EXEMPT_GRANDFATHERED:
                    grand.append(finding)
                else:
                    compliant.append(finding)

    needs.sort(key=lambda f: f.due_date or dt.date.max)  # nearest deadline first, None last
    return ContractApplicability(
        contract_id=contract_id, signed_date=contract.signed_date,
        needs_remediation=needs, grandfathered=grand, compliant=compliant, pending_review=pending,
    )
