"""contract low_ocr_confidence flag (spec #3)

Revision ID: 0011_low_ocr_confidence
Revises: 0010_obligation_prior_status
Create Date: 2026-07-15
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_low_ocr_confidence"
down_revision = "0010_obligation_prior_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contracts",
        sa.Column("low_ocr_confidence", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("contracts", "low_ocr_confidence")
