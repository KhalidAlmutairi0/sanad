"""ORM table definitions. Mirrors docs/database.md exactly."""
from __future__ import annotations

import datetime as dt
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

EMBEDDING_DIM = 1024


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())


def _created_at() -> Mapped[dt.datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = _created_at()


class Regulation(Base):
    __tablename__ = "regulations"
    id: Mapped[uuid.UUID] = _pk()
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    authority: Mapped[str] = mapped_column(Text, nullable=False)
    source_domain: Mapped[str] = mapped_column(Text, nullable=False)
    last_reconciled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = _created_at()


class RegulationVersion(Base):
    """APPEND-ONLY. App role has INSERT+SELECT only (enforced by DB grant)."""

    __tablename__ = "regulation_versions"
    id: Mapped[uuid.UUID] = _pk()
    regulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regulations.id"), nullable=False)
    article_ref: Mapped[str] = mapped_column(Text, nullable=False)
    article_text_ar: Mapped[str] = mapped_column(Text, nullable=False)
    article_text_en: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_date: Mapped[dt.date | None] = mapped_column(Date)
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("regulation_versions.id"))
    verified_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    # human_verified (a person reconciled the text) | official_fetch (parsed verbatim from the
    # official gazette, not yet human-reviewed). Surfaced on citations so auto-fetched text is
    # visibly labeled.
    verification_tier: Mapped[str] = mapped_column(Text, nullable=False, server_default="human_verified")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    created_at: Mapped[dt.datetime] = _created_at()


class Contract(Base):
    __tablename__ = "contracts"
    id: Mapped[uuid.UUID] = _pk()
    title: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    raw_object_key: Mapped[str] = mapped_column(Text, nullable=False)
    sanitized_object_key: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="uploaded")
    readiness_score: Mapped[int | None] = mapped_column(Integer)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    ocr_used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # spec #3: an OCR'd page scored below the confidence floor — flag for manual verification.
    low_ocr_confidence: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # When the contract was signed — drives the applicability engine (prior vs. new contract).
    signed_date: Mapped[dt.date | None] = mapped_column(Date)
    created_at: Mapped[dt.datetime] = _created_at()
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Clause(Base):
    __tablename__ = "clauses"
    id: Mapped[uuid.UUID] = _pk()
    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    text_ar: Mapped[str | None] = mapped_column(Text)
    text_en: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    # spec #2: set when retrieval surfaced no relevant article for this clause (assessed=false,
    # distinct from "assessed, no issue"). Must not count as a reviewed/assessed clause.
    retrieval_insufficient: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=func.false())
    created_at: Mapped[dt.datetime] = _created_at()


class Finding(Base):
    """The citation gate: regulation_version_id is NOT NULL (DB-enforced)."""

    __tablename__ = "findings"
    id: Mapped[uuid.UUID] = _pk()
    contract_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    clause_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clauses.id"))
    regulation_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulation_versions.id"), nullable=False
    )
    title_ar: Mapped[str] = mapped_column(Text, nullable=False)
    title_en: Mapped[str | None] = mapped_column(Text)
    explanation_ar: Mapped[str | None] = mapped_column(Text)
    explanation_en: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    violation_cost_ar: Mapped[str | None] = mapped_column(Text)
    violation_cost_min: Mapped[float | None] = mapped_column(Numeric)
    violation_cost_max: Mapped[float | None] = mapped_column(Numeric)
    # Retrieval confidence (spec #1): tier drives UI treatment; match_score/match_margin are
    # the raw cosine signals stored for threshold calibration. 'high' default keeps legacy rows.
    confidence_tier: Mapped[str] = mapped_column(Text, nullable=False, server_default="high")
    match_score: Mapped[float | None] = mapped_column(Float)
    match_margin: Mapped[float | None] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = _created_at()


class IdeaCheck(Base):
    __tablename__ = "idea_checks"
    id: Mapped[uuid.UUID] = _pk()
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    idea_text: Mapped[str] = mapped_column(Text, nullable=False)
    report_ar: Mapped[str | None] = mapped_column(Text)
    report_en: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="submitted")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[dt.datetime] = _created_at()


class IdeaCheckCitation(Base):
    __tablename__ = "idea_check_citations"
    idea_check_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("idea_checks.id"), primary_key=True
    )
    regulation_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulation_versions.id"), primary_key=True
    )


class Obligation(Base):
    __tablename__ = "obligations"
    id: Mapped[uuid.UUID] = _pk()
    regulation_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulation_versions.id"), nullable=False
    )
    title_ar: Mapped[str] = mapped_column(Text, nullable=False)
    title_en: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    due_date: Mapped[dt.date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="open")
    # spec #6: when the cited article is flagged amended (promote-candidate), status becomes
    # 'pending_reverification' and the pre-hold status is saved here to restore on resolve.
    prior_status: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = _created_at()


class MonitoringEvent(Base):
    __tablename__ = "monitoring_events"
    id: Mapped[uuid.UUID] = _pk()
    regulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regulations.id"), nullable=False)
    new_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("regulation_versions.id")
    )
    change_type: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    impact_summary_ar: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="detected")
    created_at: Mapped[dt.datetime] = _created_at()


class RegulationApplicability(Base):
    """Mutable classification of ONE regulation article's applicability scope (spec: applicability
    engine). Moves llm_draft -> human_reviewed via the review gate; only human_reviewed feeds the
    production decision engine. Never stored on append-only regulation_versions."""

    __tablename__ = "regulation_applicability"
    id: Mapped[uuid.UUID] = _pk()
    regulation_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulation_versions.id"), nullable=False, unique=True
    )
    applicability_type: Mapped[str] = mapped_column(Text, nullable=False)
    effective_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    deadline_date: Mapped[dt.date | None] = mapped_column(Date)
    classification_confidence: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="llm_draft"
    )
    classification_citation_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("regulation_versions.id")
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[dt.datetime] = _created_at()


class MonitoringDiff(Base):
    """Raw, unprocessed diff from a run-check (spec #5): produced by pure text comparison
    (zero LLM). Stays pending_review until a reviewer promotes it (the token-spending step,
    which creates a MonitoringEvent) or dismisses it."""

    __tablename__ = "monitoring_diffs"
    id: Mapped[uuid.UUID] = _pk()
    regulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regulations.id"), nullable=False)
    article_ref: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(Text, nullable=False)  # new_article|amended|repealed
    live_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending_review")
    created_at: Mapped[dt.datetime] = _created_at()


class Invite(Base):
    __tablename__ = "invites"
    id: Mapped[uuid.UUID] = _pk()
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    used_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[dt.datetime] = _created_at()


class Setting(Base):
    """Editable key/value app settings (e.g. admin-editable prompt guidance)."""

    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AuditLog(Base):
    """APPEND-ONLY. App role has INSERT+SELECT only (enforced by DB grant)."""

    __tablename__ = "audit_log"
    id: Mapped[uuid.UUID] = _pk()
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target: Mapped[str | None] = mapped_column(Text)
    verdict: Mapped[str | None] = mapped_column(Text)
    detail_json: Mapped[dict | None] = mapped_column(JSONB)
    at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
