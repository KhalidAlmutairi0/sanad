"""Invite codes for user registration (admin-issued).

Revision ID: 0003_invites
Revises: 0002_core_schema
Create Date: 2026-07-11
"""
from __future__ import annotations

import re

from alembic import op

from app.core.config import get_settings

revision = "0003_invites"
down_revision = "0002_core_schema"
branch_labels = None
depends_on = None

_APP_ROLE = get_settings().app_user
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", _APP_ROLE):
    raise ValueError(f"Invalid app role identifier: {_APP_ROLE!r}")


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE invites (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            code text UNIQUE NOT NULL,
            role text NOT NULL,
            email text,                         -- optional: bind the invite to one email
            note text,
            used boolean NOT NULL DEFAULT false,
            used_by uuid REFERENCES users(id),
            created_by uuid REFERENCES users(id),
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_invites_role CHECK (role IN ('reviewer','sharia_board','admin'))
        );
        CREATE INDEX ix_invites_code ON invites (code);
        """
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON invites TO {_APP_ROLE}")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS invites CASCADE")
