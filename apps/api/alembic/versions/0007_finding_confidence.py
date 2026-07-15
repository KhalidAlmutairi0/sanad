"""finding retrieval-confidence tier + raw signals (spec #1)

Revision ID: 0007_finding_confidence
Revises: 0006_ocr_and_reconciled
Create Date: 2026-07-15
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_finding_confidence"
down_revision = "0006_ocr_and_reconciled"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing rows default to 'high' so current behaviour (all findings count on accept) is
    # unchanged. match_score/match_margin are the instrumentation columns — nullable, queryable
    # to calibrate the tier thresholds against the real distribution.
    op.add_column(
        "findings",
        sa.Column("confidence_tier", sa.Text(), nullable=False, server_default="high"),
    )
    op.add_column("findings", sa.Column("match_score", sa.Float(), nullable=True))
    op.add_column("findings", sa.Column("match_margin", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("findings", "match_margin")
    op.drop_column("findings", "match_score")
    op.drop_column("findings", "confidence_tier")
