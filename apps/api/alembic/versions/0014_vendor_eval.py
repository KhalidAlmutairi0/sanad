"""vendor evaluation: vendor_evaluations + vendor_submissions

Revision ID: 0014_vendor_eval
Revises: 0013_applicability
Create Date: 2026-07-17

extraction holds the Sandbox-1 JSON only (compliance/pricing/features/background/security_flags).
Sandbox-2 (gate/compare) reads that JSON; no raw document text is ever stored here.
"""
from __future__ import annotations

import re

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.config import get_settings

revision = "0014_vendor_eval"
down_revision = "0013_applicability"
branch_labels = None
depends_on = None

_APP_ROLE = get_settings().app_user
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", _APP_ROLE):
    raise ValueError(f"Invalid app role identifier: {_APP_ROLE!r}")


def upgrade() -> None:
    op.create_table(
        "vendor_evaluations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text(), nullable=False),  # RFP label
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="uploading"),  # uploading|comparing|done
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "vendor_submissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("evaluation_id", UUID(as_uuid=True),
                  sa.ForeignKey("vendor_evaluations.id"), nullable=False),
        sa.Column("vendor_name", sa.Text(), nullable=False),
        sa.Column("source_filename", sa.Text(), nullable=True),
        sa.Column("raw_object_key", sa.Text(), nullable=True),      # minio quarantine key
        sa.Column("extraction", JSONB(), nullable=True),            # Sandbox-1 schema JSON
        sa.Column("stage1_passed", sa.Boolean(), nullable=True),    # null until compared
        sa.Column("status", sa.Text(), nullable=False, server_default="uploaded"),  # uploaded|extracted|failed
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_vendor_sub_eval", "vendor_submissions", ["evaluation_id"])
    for t in ("vendor_evaluations", "vendor_submissions"):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO {_APP_ROLE}")


def downgrade() -> None:
    op.drop_index("ix_vendor_sub_eval", table_name="vendor_submissions")
    op.drop_table("vendor_submissions")
    op.drop_table("vendor_evaluations")
