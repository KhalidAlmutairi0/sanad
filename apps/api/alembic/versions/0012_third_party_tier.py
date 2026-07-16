"""allow unverified_third_party verification tier (quarantined corpus)

Revision ID: 0012_third_party_tier
Revises: 0011_low_ocr_confidence
Create Date: 2026-07-16

Widens ck_regver_tier so third-party (e.g. Kaggle) imports can be STORED and searched but never
cited — the citation gate + retrieval filter enforce non-citability; this only permits the row.
"""
from __future__ import annotations

from alembic import op

revision = "0012_third_party_tier"
down_revision = "0011_low_ocr_confidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE regulation_versions DROP CONSTRAINT ck_regver_tier")
    op.execute(
        "ALTER TABLE regulation_versions ADD CONSTRAINT ck_regver_tier "
        "CHECK (verification_tier IN ('human_verified','official_fetch','unverified_third_party'))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE regulation_versions DROP CONSTRAINT ck_regver_tier")
    op.execute(
        "ALTER TABLE regulation_versions ADD CONSTRAINT ck_regver_tier "
        "CHECK (verification_tier IN ('human_verified','official_fetch'))"
    )
