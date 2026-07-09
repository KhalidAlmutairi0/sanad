"""Core schema — every table in docs/database.md.

Encodes two invariants at the DB level:
  1. findings.regulation_version_id is NOT NULL FK -> regulation_versions (citation gate).
  2. regulation_versions + audit_log are append-only: the app role gets INSERT+SELECT
     only (no UPDATE/DELETE). Corrections are new versions via supersedes_id.

Revision ID: 0002_core_schema
Revises: 0001_extensions
Create Date: 2026-07-08
"""
from __future__ import annotations

import re

from alembic import op

from app.core.config import get_settings

revision = "0002_core_schema"
down_revision = "0001_extensions"
branch_labels = None
depends_on = None

# App role name comes from env (config-driven, not a literal). Validate it is a plain
# SQL identifier before interpolating into GRANT/REVOKE (defense-in-depth, not user input).
_APP_ROLE = get_settings().app_user
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", _APP_ROLE):
    raise ValueError(f"Invalid app role identifier: {_APP_ROLE!r}")

APPEND_ONLY_TABLES = ("regulation_versions", "audit_log")
CRUD_TABLES = (
    "users", "regulations", "contracts", "clauses", "findings",
    "idea_checks", "idea_check_citations", "obligations", "monitoring_events",
)


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE users (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            email text UNIQUE NOT NULL,
            display_name text NOT NULL,
            role text NOT NULL,
            is_active boolean NOT NULL DEFAULT true,
            password_hash text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_users_role CHECK (role IN ('reviewer','sharia_board','admin','service'))
        );

        CREATE TABLE regulations (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            code text UNIQUE NOT NULL,
            name_ar text NOT NULL,
            name_en text NOT NULL,
            authority text NOT NULL,
            source_domain text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        );

        -- APPEND-ONLY immutable evidence cache. No UPDATE/DELETE grant to the app role.
        CREATE TABLE regulation_versions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            regulation_id uuid NOT NULL REFERENCES regulations(id),
            article_ref text NOT NULL,
            article_text_ar text NOT NULL,
            article_text_en text,
            source_url text NOT NULL,
            content_hash text NOT NULL,
            fetched_at timestamptz NOT NULL,
            effective_date date,
            supersedes_id uuid REFERENCES regulation_versions(id),
            verified_by uuid NOT NULL REFERENCES users(id),
            embedding vector(1024),
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_regver_article_hash UNIQUE (regulation_id, article_ref, content_hash)
        );
        CREATE INDEX ix_regver_reg_article ON regulation_versions (regulation_id, article_ref);
        CREATE INDEX ix_regver_embedding ON regulation_versions
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

        CREATE TABLE contracts (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            title text NOT NULL,
            uploaded_by uuid REFERENCES users(id),
            raw_object_key text NOT NULL,
            sanitized_object_key text,
            status text NOT NULL DEFAULT 'uploaded',
            readiness_score int,
            failure_reason text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_contracts_status CHECK (status IN
                ('uploaded','sanitizing','sanitized','extracting','reviewing','reviewed','failed')),
            CONSTRAINT ck_contracts_score CHECK (readiness_score IS NULL OR readiness_score BETWEEN 0 AND 100)
        );

        CREATE TABLE clauses (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            contract_id uuid NOT NULL REFERENCES contracts(id),
            ordinal int NOT NULL,
            text_ar text,
            text_en text,
            embedding vector(1024),
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_clauses_contract_ordinal ON clauses (contract_id, ordinal);
        CREATE INDEX ix_clauses_embedding ON clauses
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

        -- The citation gate lives here: regulation_version_id is NOT NULL.
        CREATE TABLE findings (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            contract_id uuid NOT NULL REFERENCES contracts(id),
            clause_id uuid REFERENCES clauses(id),
            regulation_version_id uuid NOT NULL REFERENCES regulation_versions(id),
            title_ar text NOT NULL,
            title_en text,
            explanation_ar text,
            explanation_en text,
            severity text NOT NULL,
            category text NOT NULL,
            violation_cost_ar text,
            violation_cost_min numeric,
            violation_cost_max numeric,
            review_status text NOT NULL DEFAULT 'pending',
            reviewed_by uuid REFERENCES users(id),
            reviewed_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_findings_severity CHECK (severity IN ('critical','high','medium','low')),
            CONSTRAINT ck_findings_category CHECK (category IN ('regulatory','sharia')),
            CONSTRAINT ck_findings_review CHECK (review_status IN ('pending','accepted','rejected'))
        );
        CREATE INDEX ix_findings_contract_review ON findings (contract_id, review_status);
        CREATE INDEX ix_findings_regver ON findings (regulation_version_id);

        CREATE TABLE idea_checks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            submitted_by uuid REFERENCES users(id),
            idea_text text NOT NULL,
            report_ar text,
            report_en text,
            status text NOT NULL DEFAULT 'submitted',
            reviewed_by uuid REFERENCES users(id),
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_idea_status CHECK (status IN ('submitted','generated','reviewed'))
        );

        CREATE TABLE idea_check_citations (
            idea_check_id uuid NOT NULL REFERENCES idea_checks(id),
            regulation_version_id uuid NOT NULL REFERENCES regulation_versions(id),
            PRIMARY KEY (idea_check_id, regulation_version_id)
        );

        CREATE TABLE obligations (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            regulation_version_id uuid NOT NULL REFERENCES regulation_versions(id),
            title_ar text NOT NULL,
            title_en text,
            owner_id uuid REFERENCES users(id),
            due_date date,
            status text NOT NULL DEFAULT 'open',
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_oblig_status CHECK (status IN ('open','in_progress','met','overdue'))
        );

        CREATE TABLE monitoring_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            regulation_id uuid NOT NULL REFERENCES regulations(id),
            new_version_id uuid REFERENCES regulation_versions(id),
            change_type text,
            detected_at timestamptz NOT NULL DEFAULT now(),
            impact_summary_ar text,
            status text NOT NULL DEFAULT 'detected',
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_monev_change CHECK (change_type IS NULL OR change_type IN
                ('new_article','amended','repealed')),
            CONSTRAINT ck_monev_status CHECK (status IN ('detected','verified','notified'))
        );

        -- APPEND-ONLY audit log. No UPDATE/DELETE grant to the app role.
        CREATE TABLE audit_log (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            actor text NOT NULL,
            action text NOT NULL,
            target text,
            verdict text,
            detail_json jsonb,
            at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_audit_actor_at ON audit_log (actor, at);
        CREATE INDEX ix_audit_action_at ON audit_log (action, at);

        -- contracts.updated_at maintained by trigger.
        CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        CREATE TRIGGER trg_contracts_updated_at BEFORE UPDATE ON contracts
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )

    # --- App role grants: append-only vs CRUD ---------------------------------
    for table in CRUD_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {_APP_ROLE}")
    for table in APPEND_ONLY_TABLES:
        # Enforce append-only at the privilege level: INSERT + SELECT only.
        op.execute(f"GRANT SELECT, INSERT ON {table} TO {_APP_ROLE}")
        op.execute(f"REVOKE UPDATE, DELETE, TRUNCATE ON {table} FROM {_APP_ROLE}")


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS monitoring_events, obligations, idea_check_citations,
            idea_checks, findings, clauses, contracts, audit_log,
            regulation_versions, regulations, users CASCADE;
        DROP FUNCTION IF EXISTS set_updated_at() CASCADE;
        """
    )
