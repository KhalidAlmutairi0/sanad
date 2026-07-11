"""Evidence cache (read-only). Resolve a stored article version, or semantic-search the
cache. Immutable: no write endpoints here (api-contracts.md)."""
from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.core.errors import SanadError
from app.models import Regulation, RegulationVersion, User
from app.services.retrieval import retrieve_candidates

router = APIRouter(prefix="/evidence", tags=["evidence"])


class VersionDetail(BaseModel):
    regulation_version_id: uuid.UUID
    regulation_code: str
    article_ref: str
    article_text_ar: str
    article_text_en: str | None
    source_url: str
    content_hash: str
    fetched_at: dt.datetime
    effective_date: dt.date | None
    supersedes_id: uuid.UUID | None
    verified_by: uuid.UUID


class SearchItem(BaseModel):
    regulation_version_id: uuid.UUID
    regulation_code: str
    article_ref: str
    snippet_ar: str
    score: float


class SearchResponse(BaseModel):
    items: list[SearchItem]


@router.get("/versions/{regulation_version_id}", response_model=VersionDetail)
async def get_version(
    regulation_version_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> VersionDetail:
    row = (
        await session.execute(
            select(RegulationVersion, Regulation.code)
            .join(Regulation, Regulation.id == RegulationVersion.regulation_id)
            .where(RegulationVersion.id == regulation_version_id)
        )
    ).first()
    if not row:
        raise SanadError("not_found")
    rv, code = row
    return VersionDetail(
        regulation_version_id=rv.id, regulation_code=code, article_ref=rv.article_ref,
        article_text_ar=rv.article_text_ar, article_text_en=rv.article_text_en,
        source_url=rv.source_url, content_hash=rv.content_hash, fetched_at=rv.fetched_at,
        effective_date=rv.effective_date, supersedes_id=rv.supersedes_id, verified_by=rv.verified_by,
    )


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(min_length=2),
    regulation_code: str | None = Query(default=None),
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    candidates = await retrieve_candidates(session, q, k=8, regulation_code=regulation_code)
    items = [
        SearchItem(
            regulation_version_id=c.regulation_version_id,
            regulation_code=c.regulation_code,
            article_ref=c.article_ref,
            snippet_ar=(c.article_text_ar[:160] + ("…" if len(c.article_text_ar) > 160 else "")),
            score=round(max(0.0, 1.0 - c.distance), 4),  # cosine similarity proxy
        )
        for c in candidates
    ]
    return SearchResponse(items=items)
