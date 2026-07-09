"""pgvector semantic search over the immutable evidence cache (regulation_versions)."""
from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Regulation, RegulationVersion
from app.services.retrieval.embedder import embed_texts


@dataclass
class Candidate:
    regulation_version_id: uuid.UUID
    regulation_code: str
    article_ref: str
    article_text_ar: str
    article_text_en: str | None
    source_url: str
    effective_date: dt.date | None
    distance: float


async def retrieve_candidates(
    session: AsyncSession,
    query_text: str,
    *,
    k: int = 5,
    regulation_code: str | None = None,
) -> list[Candidate]:
    [query_vec] = await embed_texts([query_text], input_type="query")

    distance = RegulationVersion.embedding.cosine_distance(query_vec).label("distance")
    stmt = (
        select(RegulationVersion, Regulation.code, distance)
        .join(Regulation, Regulation.id == RegulationVersion.regulation_id)
        .where(RegulationVersion.embedding.isnot(None))
        .order_by(distance)
        .limit(k)
    )
    if regulation_code:
        stmt = stmt.where(Regulation.code == regulation_code)

    rows = (await session.execute(stmt)).all()
    return [
        Candidate(
            regulation_version_id=rv.id,
            regulation_code=code,
            article_ref=rv.article_ref,
            article_text_ar=rv.article_text_ar,
            article_text_en=rv.article_text_en,
            source_url=rv.source_url,
            effective_date=rv.effective_date,
            distance=float(dist),
        )
        for rv, code, dist in rows
    ]
