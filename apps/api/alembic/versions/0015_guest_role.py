"""add 'guest' to the users.role CHECK constraint (public demo access)

Revision ID: 0015_guest_role
Revises: 0014_vendor_eval
Create Date: 2026-07-17

The guest role is a read/analyze demo identity: it can run Contract Review + Idea Check but is
never granted the corpus-mutating (monitoring verify/promote) or admin endpoints.
"""
from __future__ import annotations

from alembic import op

revision = "0015_guest_role"
down_revision = "0014_vendor_eval"
branch_labels = None
depends_on = None

_OLD = "role IN ('reviewer','sharia_board','admin','service')"
_NEW = "role IN ('reviewer','sharia_board','admin','service','guest')"


def upgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT ck_users_role")
    op.execute(f"ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK ({_NEW})")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT ck_users_role")
    op.execute(f"ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK ({_OLD})")
