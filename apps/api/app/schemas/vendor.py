from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel


class CreateEvaluationRequest(BaseModel):
    title: str


class CreateEvaluationResponse(BaseModel):
    id: uuid.UUID


class AddSubmissionRequest(BaseModel):
    vendor_name: str
    filename: str | None = None


class AddSubmissionResponse(BaseModel):
    id: uuid.UUID
    upload_url: str


class RunComparisonResponse(BaseModel):
    id: uuid.UUID
    status: str


class EvaluationListItem(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    vendor_count: int
    created_at: dt.datetime


class EvaluationList(BaseModel):
    items: list[EvaluationListItem]
