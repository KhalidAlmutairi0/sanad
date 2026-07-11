"""Editable app settings (key/value) — used for admin-editable prompt guidance.

Revision ID: 0004_settings
Revises: 0003_invites
Create Date: 2026-07-11
"""
from __future__ import annotations

import re

from alembic import op

from app.core.config import get_settings

revision = "0004_settings"
down_revision = "0003_invites"
branch_labels = None
depends_on = None

_APP_ROLE = get_settings().app_user
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", _APP_ROLE):
    raise ValueError(f"Invalid app role identifier: {_APP_ROLE!r}")


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE settings (
            key text PRIMARY KEY,
            value text NOT NULL,
            updated_by uuid REFERENCES users(id),
            updated_at timestamptz NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON settings TO {_APP_ROLE}")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS settings CASCADE")
