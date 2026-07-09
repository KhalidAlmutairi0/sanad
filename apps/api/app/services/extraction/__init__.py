"""Clause segmentation over sanitized contract text."""
from app.services.extraction.segmenter import ClauseSegment, segment_clauses

__all__ = ["ClauseSegment", "segment_clauses"]
