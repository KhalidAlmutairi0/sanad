"""Corpus ingestion: load human-verified regulation articles into the append-only
evidence cache (`regulation_versions`). The human gate (AGENTS.md #5) is enforced here:
articles marked `verified: false` are refused, never inserted."""
from app.services.corpus.ingest import (
    CorpusArticle,
    CorpusRegulation,
    IngestStats,
    content_hash_for,
    ingest_regulation,
    parse_regulation_spec,
    validate_regulation,
)

__all__ = [
    "CorpusArticle",
    "CorpusRegulation",
    "IngestStats",
    "content_hash_for",
    "ingest_regulation",
    "parse_regulation_spec",
    "validate_regulation",
]
