#!/bin/bash

# RedditHarbor Complete Database Backup Script
# Generated: 2025-12-03 19:01:41
# Database: reddit_harbor (localhost:54322)
# Purpose: Complete database backup with schema and data

set -euo pipefail

# Configuration
DB_HOST="127.0.0.1"
DB_PORT="54322"
DB_NAME="reddit_harbor"
DB_USER="postgres"
BACKUP_DIR="/home/carlos/projects/redditharbor-core-functions-fix/scripts/database/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="reddit_harbor_complete_${TIMESTAMP}.sql"
SCHEMA_FILE="reddit_harbor_schema_${TIMESTAMP}.sql"
DATA_FILE="reddit_harbor_data_${TIMESTAMP}.sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Function to check if database is accessible
check_database() {
    log "Checking database connectivity..."
    if PGPASSWORD="" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" > /dev/null 2>&1; then
        success "Database is accessible"
        return 0
    else
        error "Cannot connect to database ${DB_NAME} at ${DB_HOST}:${DB_PORT}"
        return 1
    fi
}

# Function to get database size
get_database_size() {
    local size=$(PGPASSWORD="" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT pg_size_pretty(pg_database_size('${DB_NAME}'));")
    echo "${size// /}"
}

# Function to backup schema only
backup_schema() {
    log "Creating schema backup..."
    local schema_file="${BACKUP_DIR}/${SCHEMA_FILE}"

    PGPASSWORD="" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --schema=public \
        --schema=auth \
        --schema=storage \
        --schema=extensions \
        --schema=graphql \
        --schema=realtime \
        --schema=supabase_functions \
        --schema=vault \
        --schema=_realtime \
        --schema=net \
        --schema=app_opportunities \
        --schema=app_opportunities_staging \
        --schema=public_staging \
        --schema-only \
        --no-owner \
        --no-privileges \
        --verbose \
        --file="${schema_file}"

    if [ $? -eq 0 ]; then
        success "Schema backup completed: ${schema_file}"
        return 0
    else
        error "Schema backup failed"
        return 1
    fi
}

# Function to backup data only
backup_data() {
    log "Creating data backup..."
    local data_file="${BACKUP_DIR}/${DATA_FILE}"

    PGPASSWORD="" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --schema=public \
        --schema=auth \
        --schema=storage \
        --data-only \
        --no-owner \
        --no-privileges \
        --verbose \
        --exclude-table='public._dlt_*' \
        --exclude-table='auth.sessions' \
        --exclude-table='auth.refresh_tokens' \
        --file="${data_file}"

    if [ $? -eq 0 ]; then
        success "Data backup completed: ${data_file}"
        return 0
    else
        error "Data backup failed"
        return 1
    fi
}

# Function to backup specific key tables with data
backup_key_tables() {
    log "Creating key tables backup..."
    local key_tables_file="${BACKUP_DIR}/reddit_harbor_key_tables_${TIMESTAMP}.sql"

    cat > "${key_tables_file}" << EOF
-- RedditHarbor Key Tables Data Backup
-- Generated: $(date)
-- Tables: submissions, opportunities, competitive_landscape, market_validations, monetization_patterns

-- Start transaction
BEGIN;

EOF

    # Backup key tables
    for table in submissions opportunities competitive_landscape market_validations monetization_patterns; do
        log "Backing up table: public.${table}"
        PGPASSWORD="" pg_dump \
            -h "${DB_HOST}" \
            -p "${DB_PORT}" \
            -U "${DB_USER}" \
            -d "${DB_NAME}" \
            --data-only \
            --no-owner \
            --no-privileges \
            --table="public.${table}" \
            >> "${key_tables_file}"

        echo "" >> "${key_tables_file}"
    done

    cat >> "${key_tables_file}" << EOF

-- Commit transaction
COMMIT;

-- Key tables backup completed
EOF

    if [ $? -eq 0 ]; then
        success "Key tables backup completed: ${key_tables_file}"
        return 0
    else
        error "Key tables backup failed"
        return 1
    fi
}

# Function to create complete backup
backup_complete() {
    log "Creating complete backup..."
    local complete_file="${BACKUP_DIR}/${BACKUP_FILE}"

    PGPASSWORD="" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --verbose \
        --format=custom \
        --compress=9 \
        --file="${complete_file}"

    if [ $? -eq 0 ]; then
        success "Complete backup created: ${complete_file}"
        return 0
    else
        error "Complete backup failed"
        return 1
    fi
}

# Function to generate backup report
generate_report() {
    log "Generating backup report..."
    local report_file="${BACKUP_DIR}/backup_report_${TIMESTAMP}.txt"

    cat > "${report_file}" << EOF
RedditHarbor Database Backup Report
=====================================
Generated: $(date)
Database: ${DB_NAME}
Host: ${DB_HOST}:${DB_PORT}

Backup Files Created:
--------------------
1. Schema Only: ${SCHEMA_FILE}
2. Data Only: ${DATA_FILE}
3. Key Tables: reddit_harbor_key_tables_${TIMESTAMP}.sql
4. Complete Backup: ${BACKUP_FILE}

Database Statistics:
-------------------
Size: $(get_database_size)

Table Row Counts:
-----------------
EOF

    # Add row counts for important tables
    echo "$(PGPASSWORD="" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "
SELECT
    schemaname || '.' || tablename as table_name,
    n_live_tup as row_count,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_stat_user_tables
WHERE schemaname IN ('public', 'auth', 'storage')
AND n_live_tup > 0
ORDER BY n_live_tup DESC;
" 2>/dev/null || echo "No data in tables")" >> "${report_file}"

    cat >> "${report_file}" << EOF

Backup Sizes:
-------------
$(ls -lh "${BACKUP_DIR}"/*${TIMESTAMP}* 2>/dev/null || echo "No backup files found")

Backup Summary:
---------------
- Schema backup: Contains all table structures, indexes, constraints
- Data backup: Contains all data except temporary/session tables
- Key tables: Focused backup of RedditHarbor core tables
- Complete backup: Full database dump in compressed format

To restore:
----------
1. Schema only: psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} < ${SCHEMA_FILE}
2. Data only: psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} < ${DATA_FILE}
3. Complete: pg_restore -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} ${BACKUP_FILE}

Backup completed successfully!
EOF

    success "Backup report generated: ${report_file}"
}

# Function to cleanup old backups (keep last 7 days)
cleanup_old_backups() {
    log "Cleaning up old backups (keeping last 7 days)..."
    find "${BACKUP_DIR}" -name "reddit_harbor_*" -type f -mtime +7 -delete 2>/dev/null || true
    success "Old backups cleaned up"
}

# Main execution
main() {
    log "Starting RedditHarbor database backup..."
    log "Timestamp: ${TIMESTAMP}"

    # Check database connectivity
    if ! check_database; then
        exit 1
    fi

    # Display database size
    log "Database size: $(get_database_size)"

    # Create backups
    local backup_success=true

    if ! backup_schema; then
        backup_success=false
    fi

    if ! backup_data; then
        backup_success=false
    fi

    if ! backup_key_tables; then
        backup_success=false
    fi

    if ! backup_complete; then
        backup_success=false
    fi

    # Generate report
    generate_report

    # Cleanup old backups
    cleanup_old_backups

    # Final status
    if [ "${backup_success}" = true ]; then
        success "All backups completed successfully!"
        log "Backup location: ${BACKUP_DIR}"
        exit 0
    else
        error "Some backups failed. Check the logs above."
        exit 1
    fi
}

# Run main function
main "$@"