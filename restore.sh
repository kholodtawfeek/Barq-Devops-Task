#!/usr/bin/env bash
set -euo pipefail

PROJECT="barq-assessment"
DB_USER="barq_app"
DB_NAME="barq_tasks"
BACKUP_DIR="./backups"

BACKUP_FILE="${1:-}"
if [ -z "$BACKUP_FILE" ]; then
  BACKUP_FILE=$(ls -1t "${BACKUP_DIR}"/barq_tasks_*.sql | head -n1)
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERROR: backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

echo "Restoring '${BACKUP_FILE}' into database '${DB_NAME}'..."

docker compose -p "$PROJECT" exec -T postgres \
  psql -U "$DB_USER" -d "$DB_NAME" -c "DROP TABLE IF EXISTS records;"

docker compose -p "$PROJECT" exec -T postgres \
  psql -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"

echo "Restore complete from: $BACKUP_FILE"

echo "Verifying record count:"
docker compose -p "$PROJECT" exec -T postgres \
  psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM records;"
