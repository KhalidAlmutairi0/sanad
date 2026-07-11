"""extract_clauses job: sanitized text -> segmented clauses (with embeddings) -> DB,
then enqueue finding generation."""
from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.storage import get_minio
from app.models import Clause, Contract
from app.services.audit import ACTOR_ANALYSIS, write_audit
from app.services.extraction import segment_clauses
from app.services.retrieval import embed_texts

_settings = get_settings()


async def extract_clauses(ctx: dict, contract_id: str) -> str:
    cid = uuid.UUID(contract_id)
    async with SessionLocal() as session:
        contract = await session.get(Contract, cid)
        if not contract or contract.status != "sanitized" or not contract.sanitized_object_key:
            return "skipped"
        contract.status = "extracting"
        await session.commit()

        client = get_minio()
        resp = client.get_object(_settings.bucket_sanitized, contract.sanitized_object_key)
        try:
            text = resp.read().decode("utf-8")
        finally:
            resp.close()
            resp.release_conn()

        segments = segment_clauses(text)
        if segments:
            texts = [s.text_ar or s.text_en or "" for s in segments]
            embeddings = await embed_texts(texts, input_type="passage")
            for seg, emb in zip(segments, embeddings):
                session.add(
                    Clause(
                        contract_id=cid, ordinal=seg.ordinal,
                        text_ar=seg.text_ar, text_en=seg.text_en, embedding=emb,
                    )
                )
        await write_audit(
            session, actor=ACTOR_ANALYSIS, action="clauses_extracted",
            target=contract_id, verdict="n-a", detail={"count": len(segments)},
        )
        await session.commit()

    await ctx["redis"].enqueue_job("generate_findings", contract_id)
    return f"extracted:{len(segments)}"
