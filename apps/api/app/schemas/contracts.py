from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, Field


class CreateContractRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)


class CreateContractResponse(BaseModel):
    id: uuid.UUID
    upload_url: str


class UploadedResponse(BaseModel):
    id: uuid.UUID
    status: str


class ContractListItem(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    readiness_score: int | None
    created_at: dt.datetime


class ContractList(BaseModel):
    items: list[ContractListItem]
    total: int


class FindingsSummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    pending: int = 0


class ContractDetail(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    readiness_score: int | None
    findings_summary: FindingsSummary
    ocr_used: bool = False


class ClauseItem(BaseModel):
    id: uuid.UUID
    ordinal: int
    text_ar: str | None
    text_en: str | None
    # spec #2: true when retrieval found nothing relevant (unassessed, not "clean").
    retrieval_insufficient: bool = False


class ClauseList(BaseModel):
    items: list[ClauseItem]
