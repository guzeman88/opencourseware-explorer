#!/usr/bin/env bash
# backup_db.sh — PostgreSQL backup to a local directory or S3-compatible bucket.
#
# Usage:
#   ./backup_db.sh                      # local backup to ./backups/
#   S3_BUCKET=s3://my-bucket ./backup_db.sh   # stream directly to S3
#
# Required env:
#   DATABASE_URL   postgresql://user:pass@host:port/dbname
#
# Optional env:
#   BACKUP_DIR     local output directory   (default: ./backups)
#   S3_BUCKET      s3://bucket/prefix       (requires awscli in PATH)
#   RETAIN_DAYS    delete local files older than N days (default: 7)

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-$(dirname "$0")/backups}"
RETAIN_DAYS="${RETAIN_DAYS:-7}"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
FILENAME="opencourseware_${TIMESTAMP}.pgdump"

# ── Require DATABASE_URL ──────────────────────────────────────────────────────
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set." >&2
  exit 1
fi

# Strip driver prefix so pg_dump can parse it
DB_URL="${DATABASE_URL/postgresql+asyncpg:\/\//postgresql://}"
DB_URL="${DB_URL/postgres+asyncpg:\/\//postgresql://}"

echo "[backup] Starting backup at ${TIMESTAMP}"

# ── Run pg_dump ───────────────────────────────────────────────────────────────
if [[ -n "${S3_BUCKET:-}" ]]; then
  # Stream directly to S3 (no local disk usage)
  echo "[backup] Streaming to ${S3_BUCKET}/${FILENAME}"
  pg_dump --format=custom --no-owner --no-privileges "${DB_URL}" \
    | aws s3 cp - "${S3_BUCKET}/${FILENAME}"
  echo "[backup] S3 upload complete: ${S3_BUCKET}/${FILENAME}"
else
  # Write to local directory
  mkdir -p "${BACKUP_DIR}"
  OUT="${BACKUP_DIR}/${FILENAME}"
  pg_dump --format=custom --no-owner --no-privileges "${DB_URL}" \
    --file="${OUT}"
  echo "[backup] Written to ${OUT} ($(du -sh "${OUT}" | cut -f1))"

  # ── Prune old backups ─────────────────────────────────────────────────────
  find "${BACKUP_DIR}" -name "opencourseware_*.pgdump" \
    -mtime "+${RETAIN_DAYS}" -delete
  echo "[backup] Pruned backups older than ${RETAIN_DAYS} days"
fi

echo "[backup] Done."
