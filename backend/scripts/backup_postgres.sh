#!/bin/sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-activity_service}"
KEEP_DAYS="${KEEP_DAYS:-7}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="$BACKUP_DIR/${POSTGRES_DB}_${STAMP}.sql.gz"

PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  "$POSTGRES_DB" | gzip > "$FILE"

find "$BACKUP_DIR" -type f -name "${POSTGRES_DB}_*.sql.gz" -mtime +"$KEEP_DAYS" -delete

echo "Backup saved to $FILE"
