"""Retrieval: self-hosted embeddings + pgvector search. Embedding model is swappable
behind embedder.py; changing dimensions is a MAJOR migration (architecture.md 7b)."""
from app.services.retrieval.embedder import embed_texts
from app.services.retrieval.search import Candidate, retrieve_candidates

__all__ = ["embed_texts", "Candidate", "retrieve_candidates"]
