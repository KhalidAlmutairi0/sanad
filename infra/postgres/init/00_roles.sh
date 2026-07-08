#!/bin/bash
# Bootstrap SANAD DB roles on first cluster init (runs as the postgres superuser).
# Two roles by design (database.md):
#   sanad_migrator -> owns DDL (Alembic connects as this).
#   sanad_app      -> runtime role for API + workers. The migration that creates the
#                     append-only tables revokes UPDATE/DELETE from this role.
# Passwords come from the environment; nothing is hardcoded.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
	CREATE ROLE ${SANAD_MIGRATOR_USER} LOGIN PASSWORD '${SANAD_MIGRATOR_PASSWORD}';
	CREATE ROLE ${SANAD_APP_USER} LOGIN PASSWORD '${SANAD_APP_PASSWORD}';

	-- Migrator owns the schema and all DDL.
	ALTER DATABASE ${POSTGRES_DB} OWNER TO ${SANAD_MIGRATOR_USER};
	GRANT ALL ON SCHEMA public TO ${SANAD_MIGRATOR_USER};

	-- App role connects and uses the schema; table-level grants are applied by the
	-- migration (so append-only INSERT+SELECT-only grants travel with the schema).
	GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${SANAD_APP_USER};
	GRANT USAGE ON SCHEMA public TO ${SANAD_APP_USER};
SQL

echo "SANAD roles created: ${SANAD_MIGRATOR_USER}, ${SANAD_APP_USER}"
