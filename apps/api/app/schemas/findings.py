from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel


class Citation(BaseModel):
    """Never null on a finding — a finding without a resolvable citation cannot exist."""

    regulation_version_id: uuid.UUID
    regulation_code: str
    article_ref: str
    article_text_ar: str
    source_url: str
    effective_date: dt.date | None


class FindingItem(BaseModel):
    id: uuid.UUID
    clause_id: uuid.UUID | None
    title_ar: str
    title_en: str | None
    explanation_ar: str | None
    explanation_en: str | None
    severity: str
    category: str
    violation_cost_ar: str | None
    violation_cost_min: float | None
    violation_cost_max: float | None
    review_status: str
    citation: Citation


class FindingList(BaseModel):
    items: list[FindingItem]


class ExplainResponse(BaseModel):
    explanation_ar: str | None
    explanation_en: str | None
    citation: Citation


class ReviewRequest(BaseModel):
    decision: str  # 'accepted' | 'rejected'


class ReviewResponse(BaseModel):
    id: uuid.UUID
    review_status: str
    reviewed_at: dt.datetime | None


class RadarKiller(BaseModel):
    finding_id: uuid.UUID
    title_ar: str
    severity: str
    citation: Citation


class RadarResponse(BaseModel):
    verdict: str  # GO | REVIEW | STOP
    killers: list[RadarKiller]
