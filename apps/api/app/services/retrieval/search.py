"""pgvector semantic search over the immutable evidence cache (regulation_versions)."""
from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Regulation, RegulationVersion
from app.services.corpus.tiers import CITABLE_TIERS
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
    rerank_enabled: bool | None = None,
    citable_only: bool = False,
) -> list[Candidate]:
    """Retrieve the top-k regulation articles for a query.

    When reranking is on (config `rerank_enabled`, default true), a wider cosine net of
    `rerank_fetch_k` candidates is retrieved and an LLM reorders them by direct relevance,
    then the top k are returned — precision that raw cosine loses at corpus scale.

    citable_only=True restricts to tiers a finding may cite (excludes quarantined third-party
    text). Finding generation sets this; evidence search leaves it False so all corpus text is
    searchable.
    """
    settings = get_settings()
    use_rerank = settings.rerank_enabled if rerank_enabled is None else rerank_enabled
    fetch_k = max(k, settings.rerank_fetch_k) if use_rerank else k

    [query_vec] = await embed_texts([query_text], input_type="query")

    distance = RegulationVersion.embedding.cosine_distance(query_vec).label("distance")
    stmt = (
        select(RegulationVersion, Regulation.code, distance)
        .join(Regulation, Regulation.id == RegulationVersion.regulation_id)
        .where(RegulationVersion.embedding.isnot(None))
        .order_by(distance)
        .limit(fetch_k)
    )
    if citable_only:
        stmt = stmt.where(RegulationVersion.verification_tier.in_(CITABLE_TIERS))
    if regulation_code:
        stmt = stmt.where(Regulation.code == regulation_code)

    rows = (await session.execute(stmt)).all()
    candidates = [
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
    if use_rerank and len(candidates) > 1:
        from app.services.retrieval.reranker import rerank

        return await rerank(query_text, candidates, top_n=k)
    return candidates[:k]
