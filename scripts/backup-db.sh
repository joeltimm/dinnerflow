#!/usr/bin/env bash
#
# backup-db.sh — Automated PostgreSQL backup with rotation.
#
# Dumps the dinnerflow database from the running Docker container,
# compresses with gzip, and rotates old backups.
#
# Retention:  7 daily backups  +  4 weekly backups (Sunday snapshots)
#
# Usage:
#   ./scripts/backup-db.sh                  # uses defaults
#   BACKUP_DIR=/mnt/nas/backups ./scripts/backup-db.sh   # custom backup dir
#
# Cron example (daily at 2:00 AM):
#   0 2 * * * /home/joel/dinnerflow/scripts/backup-db.sh >> /home/joel/dinnerflow/backups/backup.log 2>&1
#
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────

# Load .env for DB credentials if present
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

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
DAILY_RETENTION=7
WEEKLY_RETENTION=4

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DAY_OF_WEEK="$(date +%u)"  # 1=Monday, 7=Sunday

# ── Setup ────────────────────────────────────────────────────────────────────

mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ── Dump ─────────────────────────────────────────────────────────────────────

DUMP_FILE="$BACKUP_DIR/daily/${DB_NAME}_${TIMESTAMP}.sql.gz"

log "Starting backup of '$DB_NAME' from container '$DB_CONTAINER'..."

if ! docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --no-owner --no-acl \
    | gzip > "$DUMP_FILE"; then
    log "ERROR: pg_dump failed!"
    rm -f "$DUMP_FILE"
    exit 1
fi

DUMP_SIZE="$(du -h "$DUMP_FILE" | cut -f1)"
log "Backup complete: $DUMP_FILE ($DUMP_SIZE)"

# ── Weekly snapshot (copy Sunday's daily backup) ─────────────────────────────

if [[ "$DAY_OF_WEEK" -eq 7 ]]; then
    WEEKLY_FILE="$BACKUP_DIR/weekly/${DB_NAME}_weekly_${TIMESTAMP}.sql.gz"
    cp "$DUMP_FILE" "$WEEKLY_FILE"
    log "Weekly snapshot saved: $WEEKLY_FILE"
fi

# ── Rotation ─────────────────────────────────────────────────────────────────

# Keep only the N most recent daily backups
DAILY_COUNT=$(find "$BACKUP_DIR/daily" -name "*.sql.gz" -type f | wc -l)
if [[ "$DAILY_COUNT" -gt "$DAILY_RETENTION" ]]; then
    REMOVE_COUNT=$((DAILY_COUNT - DAILY_RETENTION))
    find "$BACKUP_DIR/daily" -name "*.sql.gz" -type f -printf '%T+ %p\n' \
        | sort | head -n "$REMOVE_COUNT" | awk '{print $2}' \
        | xargs rm -f
    log "Rotated $REMOVE_COUNT old daily backup(s)"
fi

# Keep only the N most recent weekly backups
WEEKLY_COUNT=$(find "$BACKUP_DIR/weekly" -name "*.sql.gz" -type f | wc -l)
if [[ "$WEEKLY_COUNT" -gt "$WEEKLY_RETENTION" ]]; then
    REMOVE_COUNT=$((WEEKLY_COUNT - WEEKLY_RETENTION))
    find "$BACKUP_DIR/weekly" -name "*.sql.gz" -type f -printf '%T+ %p\n' \
        | sort | head -n "$REMOVE_COUNT" | awk '{print $2}' \
        | xargs rm -f
    log "Rotated $REMOVE_COUNT old weekly backup(s)"
fi

log "Backup job finished. Daily: $(find "$BACKUP_DIR/daily" -name "*.sql.gz" | wc -l), Weekly: $(find "$BACKUP_DIR/weekly" -name "*.sql.gz" | wc -l)"
