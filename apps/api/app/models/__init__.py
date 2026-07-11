"""SQLAlchemy ORM models — mirror docs/database.md. Schema truth is the Alembic
migration; these map it for the app. Append-only tables are enforced at the DB grant
level (the app role cannot UPDATE/DELETE regulation_versions or audit_log)."""
from app.models.tables import (
    AuditLog,
    Clause,
    Contract,
    Finding,
    IdeaCheck,
    IdeaCheckCitation,
    Invite,
    MonitoringEvent,
    Obligation,
    Regulation,
    RegulationVersion,
    User,
)

__all__ = [
    "AuditLog",
    "Clause",
    "Contract",
    "Finding",
    "IdeaCheck",
    "IdeaCheckCitation",
    "Invite",
    "MonitoringEvent",
    "Obligation",
    "Regulation",
    "RegulationVersion",
    "User",
]
