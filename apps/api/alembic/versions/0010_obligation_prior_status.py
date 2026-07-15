"""obligation prior_status for reverification hold (spec #6)

Revision ID: 0010_obligation_prior_status
Revises: 0009_monitoring_diffs
Create Date: 2026-07-15

obligations is an existing granted table, so ALTER inherits the app role's grants — no new
GRANT needed. prior_status stores the status to restore when a reverification resolves.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_obligation_prior_status"
down_revision = "0009_monitoring_diffs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("obligations", sa.Column("prior_status", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("obligations", "prior_status")
