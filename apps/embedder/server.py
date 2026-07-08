"""Self-hosted embedding service — multilingual-e5-large (1024 dims).

Sovereignty requirement: legal text is embedded on-prem and never leaves the deployment.
e5 models expect instruction prefixes: "query: " for search queries, "passage: " for
documents. Callers pass input_type accordingly.
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

MODEL_NAME = os.environ.get("EMBEDDER_MODEL", "intfloat/multilingual-e5-large")
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "1024"))

app = FastAPI(title="SANAD Embedder", version="1.0.0")
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1)
    input_type: str = Field(default="passage", pattern="^(passage|query)$")


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    dim: int


@app.on_event("startup")
def _warm() -> None:
    _get_model()


@app.get("/health")
def health() -> dict[str, object]:
    ready = _model is not None
    return {"status": "ok" if ready else "loading", "model": MODEL_NAME, "dim": EMBEDDING_DIM}


@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest) -> EmbedResponse:
    model = _get_model()
    prefixed = [f"{req.input_type}: {t}" for t in req.texts]
    vectors = model.encode(prefixed, normalize_embeddings=True, convert_to_numpy=True)
    return EmbedResponse(embeddings=[v.tolist() for v in vectors], dim=EMBEDDING_DIM)
