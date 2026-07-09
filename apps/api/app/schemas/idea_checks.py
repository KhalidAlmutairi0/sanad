from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class SubmitIdeaRequest(BaseModel):
    idea_text: str = Field(min_length=10, max_length=5000)


class SubmitIdeaResponse(BaseModel):
    id: uuid.UUID
    status: str


class IdeaCitation(BaseModel):
    regulation_version_id: uuid.UUID
    regulation_code: str
    article_ref: str
    source_url: str


class IdeaCheckDetail(BaseModel):
    id: uuid.UUID
    idea_text: str
    status: str
    report_ar: str | None
    report_en: str | None
    citations: list[IdeaCitation]
    reviewed_by: uuid.UUID | None


class IdeaListItem(BaseModel):
    id: uuid.UUID
    status: str


class IdeaList(BaseModel):
    items: list[IdeaListItem]
    total: int


class IdeaReviewRequest(BaseModel):
    decision: str = "reviewed"
    notes_ar: str | None = None


class IdeaReviewResponse(BaseModel):
    id: uuid.UUID
    status: str
