#!/usr/bin/env bash
set -euo pipefail

PROJECT="barq-assessment"
DB_USER="barq_app"
DB_NAME="barq_tasks"
BACKUP_DIR="./backups"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_FILE="${BACKUP_DIR}/barq_tasks_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

echo "Backing up PostgreSQL database '${DB_NAME}' from project '${PROJECT}'..."
docker compose -p "$PROJECT" exec -T postgres \
  pg_dump -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"

if [ -s "$BACKUP_FILE" ]; then
  echo "Backup successful: $BACKUP_FILE ($(wc -l < "$BACKUP_FILE") lines)"
else
  echo "ERROR: backup file is empty" >&2
  exit 1
fi

ls -1t "${BACKUP_DIR}"/barq_tasks_*.sql | tail -n +6 | xargs -r rm --

echo "Latest backup: $BACKUP_FILE"
