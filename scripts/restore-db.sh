#!/usr/bin/env bash
#
# restore-db.sh — Restore a PostgreSQL backup into the dinnerflow database.
#
# WARNING: This drops and recreates the target database!
#
# Usage:
#   ./scripts/restore-db.sh backups/daily/dinnerflow_20260414_020000.sql.gz
#   ./scripts/restore-db.sh backups/weekly/dinnerflow_weekly_20260413_020000.sql.gz
#
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <backup-file.sql.gz>"
    echo "Example: $0 backups/daily/dinnerflow_20260414_020000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# ── Configuration ────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
if [[ -f "$PROJECT_DIR/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$PROJECT_DIR/.env"
    set +a
fi

DB_CONTAINER="${DB_CONTAINER:-dinner-db}"
DB_NAME="${DINNER_DB_NAME:-dinnerflow}"
DB_USER="${DINNER_DB_USER:-dinneruser}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ── Safety check ─────────────────────────────────────────────────────────────

echo ""
echo "  ╔════════════════════════════════════════════════════════════╗"
echo "  ║  WARNING: This will DROP and recreate '$DB_NAME'          ║"
echo "  ║  All current data will be replaced with the backup.       ║"
echo "  ╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  Backup file: $BACKUP_FILE"
echo "  Container:   $DB_CONTAINER"
echo "  Database:    $DB_NAME"
echo ""
read -rp "  Type 'yes' to proceed: " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

# ── Stop application services (keep DB running) ─────────────────────────────

log "Stopping application containers..."
cd "$PROJECT_DIR"
docker compose stop backend celery-worker celery-beat web 2>/dev/null || true

# ── Restore ──────────────────────────────────────────────────────────────────

log "Dropping and recreating database '$DB_NAME'..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
    2>/dev/null || true
docker exec "$DB_CONTAINER" dropdb -U "$DB_USER" --if-exists "$DB_NAME"
docker exec "$DB_CONTAINER" createdb -U "$DB_USER" "$DB_NAME"

log "Restoring from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" --quiet

log "Restore complete."

# ── Restart services ─────────────────────────────────────────────────────────

log "Restarting application containers..."
docker compose start backend celery-worker celery-beat web

log "All services restarted. Restore finished successfully."
