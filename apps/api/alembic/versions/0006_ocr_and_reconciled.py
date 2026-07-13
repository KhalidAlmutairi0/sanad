"""OCR flag on contracts + reconciliation timestamp on regulations.

- contracts.ocr_used: the upload had no text layer and was OCR'd (surfaced as a badge; OCR
  text is noisier, so reviewers should know).
- regulations.last_reconciled_at: when the corpus for this regulation was last fetched/checked
  against the official source (staleness tracking, PLAN.md P1.8).

Revision ID: 0006_ocr_and_reconciled
Revises: 0005_verification_tier
Create Date: 2026-07-13
"""
from __future__ import annotations

from alembic import op

revision = "0006_ocr_and_reconciled"
down_revision = "0005_verification_tier"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE contracts ADD COLUMN ocr_used boolean NOT NULL DEFAULT false;
        ALTER TABLE regulations ADD COLUMN last_reconciled_at timestamptz;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE contracts DROP COLUMN IF EXISTS ocr_used;
        ALTER TABLE regulations DROP COLUMN IF EXISTS last_reconciled_at;
        """
    )
