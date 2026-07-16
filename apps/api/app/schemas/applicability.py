from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel


class ArticleRef(BaseModel):
    regulation_version_id: uuid.UUID
    regulation_code: str
    article_ref: str
    source_url: str


class ApplicabilityDraft(BaseModel):
    id: uuid.UUID
    source_article: ArticleRef
    applicability_type: str
    effective_date: dt.date
    deadline_date: dt.date | None
    classification_confidence: str
    classification_citation: ArticleRef | None


class ReviewQueue(BaseModel):
    items: list[ApplicabilityDraft]


class ReviewRequest(BaseModel):
    applicability_type: str
    effective_date: dt.date
    deadline_date: dt.date | None = None
    # Required to become human_reviewed — the article that defines the applicability scope.
    classification_citation_version_id: uuid.UUID


class ClauseRef(BaseModel):
    clause_id: uuid.UUID
    ordinal: int
    text_ar: str | None


class ApplicabilityFinding(BaseModel):
    flag: str
    due_date: dt.date | None
    source_article: ArticleRef       # the triggering regulation article
    classification_citation: ArticleRef | None  # proves the applicability_type is sourced
    clause: ClauseRef | None         # the contract clause that matched (or None)


class ContractApplicability(BaseModel):
    contract_id: uuid.UUID
    signed_date: dt.date | None
    needs_remediation: list[ApplicabilityFinding]  # sorted by nearest deadline
    grandfathered: list[ApplicabilityFinding]
    compliant: list[ApplicabilityFinding]
    pending_review: int  # llm_draft classifications not yet actionable
