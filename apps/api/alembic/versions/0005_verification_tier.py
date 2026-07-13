"""Verification tier on regulation_versions.

Records HOW an article's text was verified:
  - human_verified: a person reconciled it against the official source (AGENTS.md #5).
  - official_fetch: parsed verbatim from the official gazette by the fetch tool, NOT yet
    human-reviewed. Usable by owner policy, but surfaced to users as auto-fetched.

Existing rows are human_verified (the seed corpus went through the human gate).

Revision ID: 0005_verification_tier
Revises: 0004_settings
Create Date: 2026-07-13
"""
from __future__ import annotations

from alembic import op

revision = "0005_verification_tier"
down_revision = "0004_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE regulation_versions
            ADD COLUMN verification_tier text NOT NULL DEFAULT 'human_verified';
        ALTER TABLE regulation_versions
            ADD CONSTRAINT ck_regver_tier
            CHECK (verification_tier IN ('human_verified','official_fetch'));
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE regulation_versions DROP CONSTRAINT IF EXISTS ck_regver_tier;
        ALTER TABLE regulation_versions DROP COLUMN IF EXISTS verification_tier;
        """
    )
