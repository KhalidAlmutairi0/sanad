"""monitoring_diffs: raw unprocessed diffs from run-check, before token spend (spec #5)

Revision ID: 0009_monitoring_diffs
Revises: 0008_clause_retrieval_state
Create Date: 2026-07-15
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0009_monitoring_diffs"
down_revision = "0008_clause_retrieval_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A run-check produces these rows via pure text diff (zero LLM). They stay pending_review
    # until a reviewer promotes one (the token-spending step) or dismisses it. Distinct from
    # monitoring_events, which only exist once a change has been promoted.
    op.create_table(
        "monitoring_diffs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("regulation_id", UUID(as_uuid=True), sa.ForeignKey("regulations.id"), nullable=False),
        sa.Column("article_ref", sa.Text(), nullable=False),
        sa.Column("change_type", sa.Text(), nullable=False),  # new_article | amended | repealed
        sa.Column("live_text", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending_review"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_monitoring_diffs_status", "monitoring_diffs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_monitoring_diffs_status", table_name="monitoring_diffs")
    op.drop_table("monitoring_diffs")
