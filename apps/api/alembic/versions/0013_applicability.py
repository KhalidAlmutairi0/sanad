"""contract applicability: regulation_applicability + contracts.signed_date

Revision ID: 0013_applicability
Revises: 0012_third_party_tier
Create Date: 2026-07-16

Applicability is a MUTABLE classification of a regulation article (llm_draft -> human_reviewed),
so it lives in its own table — never on append-only regulation_versions. Every classification
must cite the article that defines its scope (classification_citation_version_id) before it can
be human_reviewed; the app enforces that, this schema permits null only for the draft stage.
"""
from __future__ import annotations

import re

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

from app.core.config import get_settings

revision = "0013_applicability"
down_revision = "0012_third_party_tier"
branch_labels = None
depends_on = None

_APP_ROLE = get_settings().app_user
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", _APP_ROLE):
    raise ValueError(f"Invalid app role identifier: {_APP_ROLE!r}")


def upgrade() -> None:
    op.add_column("contracts", sa.Column("signed_date", sa.Date(), nullable=True))

    op.create_table(
        "regulation_applicability",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # The classified article (source_article).
        sa.Column("regulation_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("regulation_versions.id"), nullable=False, unique=True),
        sa.Column("applicability_type", sa.Text(), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("deadline_date", sa.Date(), nullable=True),
        sa.Column("classification_confidence", sa.Text(), nullable=False, server_default="llm_draft"),
        # The article whose text defines the applicability scope (required before human_reviewed).
        sa.Column("classification_citation_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("regulation_versions.id"), nullable=True),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "applicability_type IN ('retroactive_with_deadline','prospective_only','grandfathered')",
            name="ck_applic_type",
        ),
        sa.CheckConstraint(
            "classification_confidence IN ('llm_draft','human_reviewed')",
            name="ck_applic_confidence",
        ),
    )
    op.create_index("ix_applic_confidence", "regulation_applicability", ["classification_confidence"])
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON regulation_applicability TO {_APP_ROLE}"
    )


def downgrade() -> None:
    op.drop_index("ix_applic_confidence", table_name="regulation_applicability")
    op.drop_table("regulation_applicability")
    op.drop_column("contracts", "signed_date")
