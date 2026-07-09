"""Client for the self-hosted multilingual-e5-large embedding service.

e5 convention: documents use input_type="passage", search queries use "query".
Legal text is embedded on-prem and never leaves the deployment (sovereignty, 7b).
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings

_settings = get_settings()


async def embed_texts(texts: list[str], input_type: str = "passage") -> list[list[float]]:
    if input_type not in ("passage", "query"):
        raise ValueError("input_type must be 'passage' or 'query'")
    if not texts:
        return []
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{_settings.embedder_url.rstrip('/')}/embed",
            json={"texts": texts, "input_type": input_type},
        )
        resp.raise_for_status()
        data = resp.json()
    vectors = data["embeddings"]
    if vectors and len(vectors[0]) != _settings.embedding_dim:
        raise ValueError(
            f"Embedder returned dim {len(vectors[0])}, expected {_settings.embedding_dim}"
        )
    return vectors
