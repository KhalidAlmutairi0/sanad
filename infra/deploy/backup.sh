#!/usr/bin/env bash
# Nightly SANAD backup: Postgres logical dump + MinIO object store, with rotation.
# The Postgres dump is the critical asset (findings, citations, append-only audit_log and
# regulation_versions — the 5-year auditability promise). MinIO holds uploaded/sanitized
# files. Run as root (needs the docker socket). Installed as a systemd timer by bootstrap.sh.
#
# Env:
#   BACKUP_DIR   local destination           (default /var/backups/sanad)
#   KEEP_DAYS    rotation window in days      (default 14)
#   COMPOSE_PROJECT  docker compose project   (default sanad; volumes are <project>_<name>)
#   BACKUP_REMOTE    optional rclone target   (e.g. "offsite:sanad-backups"); if set and
#                    rclone is installed, the day's files are copied off the VM.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
INFRA_DIR=$(dirname "$SCRIPT_DIR")
BACKUP_DIR=${BACKUP_DIR:-/var/backups/sanad}
KEEP_DAYS=${KEEP_DAYS:-14}
PROJECT=${COMPOSE_PROJECT:-sanad}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)

DC="docker compose -f $INFRA_DIR/docker-compose.yml -f $INFRA_DIR/docker-compose.prod.yml"
mkdir -p "$BACKUP_DIR"

echo "[backup] Postgres dump -> db-$STAMP.sql.gz"
$DC exec -T postgres pg_dump -U postgres -d "${POSTGRES_DB:-sanad}" \
  | gzip > "$BACKUP_DIR/db-$STAMP.sql.gz"

echo "[backup] MinIO volume -> minio-$STAMP.tar.gz"
docker run --rm \
  -v "${PROJECT}_minio-data:/data:ro" \
  -v "$BACKUP_DIR:/backup" \
  alpine:3.20 tar czf "/backup/minio-$STAMP.tar.gz" -C /data .

echo "[backup] rotate: delete backups older than $KEEP_DAYS days"
find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'db-*.sql.gz' -o -name 'minio-*.tar.gz' \) \
  -mtime +"$KEEP_DAYS" -print -delete

if [[ -n "${BACKUP_REMOTE:-}" ]] && command -v rclone >/dev/null 2>&1; then
  echo "[backup] offsite copy -> $BACKUP_REMOTE"
  rclone copy "$BACKUP_DIR/db-$STAMP.sql.gz" "$BACKUP_REMOTE/"
  rclone copy "$BACKUP_DIR/minio-$STAMP.tar.gz" "$BACKUP_REMOTE/"
else
  echo "[backup] BACKUP_REMOTE unset or rclone missing — LOCAL ONLY. Configure an off-VM"
  echo "         copy before relying on this for disaster recovery (see docs/deploy.md)."
fi

echo "[backup] done: $BACKUP_DIR/db-$STAMP.sql.gz , minio-$STAMP.tar.gz"
