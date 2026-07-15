"""clause retrieval_insufficient flag (spec #2)

Revision ID: 0008_clause_retrieval_insufficient
Revises: 0007_finding_confidence
Create Date: 2026-07-15
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_clause_retrieval_insufficient"
down_revision = "0007_finding_confidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clauses",
        sa.Column("retrieval_insufficient", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("clauses", "retrieval_insufficient")
