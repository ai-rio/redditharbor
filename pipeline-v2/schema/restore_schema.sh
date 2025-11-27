#!/bin/bash

# RedditHarbor Schema Restore Script
# Usage: ./restore_schema.sh [options]
#
# Options:
#   --complete         Restore complete schema (default)
#   --critical-only    Restore only critical tables
#   --custom          Use custom binary format (faster)
#   --database NAME   Target database name (default: reddit)
#   --dry-run         Show commands without executing

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DUMPS_DIR="${SCRIPT_DIR}/dumps"
DATABASE_NAME="reddit"
TIMESTAMP="20251127_153034"
DRY_RUN=false
MODE="complete"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Help message
show_help() {
    cat << EOF
RedditHarbor Schema Restore Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --complete         Restore complete schema (default)
    --critical-only    Restore only critical tables (app_opportunities, redditor, submission, comment)
    --custom          Use custom binary format for faster restore
    --database NAME   Target database name (default: reddit)
    --dry-run         Show commands without executing
    --help            Show this help message

EXAMPLES:
    $0                           # Complete schema restore
    $0 --critical-only           # Critical tables only
    $0 --custom --database test  # Fast restore to test database
    $0 --dry-run                 # Preview commands

DISASTER RECOVERY:
    1. Ensure PostgreSQL is running: systemctl status postgresql
    2. Connect to database: psql -h 127.0.0.1 -p 54322 -U postgres -d postgres
    3. Run this script with appropriate options
    4. Verify restoration: psql -h 127.0.0.1 -p 54322 -U postgres -d reddit -c "\dt"

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --complete)
            MODE="complete"
            shift
            ;;
        --critical-only)
            MODE="critical"
            shift
            ;;
        --custom)
            MODE="custom"
            shift
            ;;
        --database)
            DATABASE_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1. Use --help for usage."
            ;;
    esac
done

# Validate environment
validate_environment() {
    info "Validating environment..."

    # Check if dumps directory exists
    if [[ ! -d "$DUMPS_DIR" ]]; then
        error "Dumps directory not found: $DUMPS_DIR"
    fi

    # Check PostgreSQL connection
    if ! PGPASSWORD=postgres psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "SELECT 1;" &>/dev/null; then
        error "Cannot connect to PostgreSQL. Check if server is running."
    fi

    # Check required tools
    for tool in psql pg_dump pg_restore; do
        if ! command -v "$tool" &> /dev/null; then
            error "Required tool not found: $tool"
        fi
    done

    log "Environment validation passed"
}

# Execute SQL command (or show if dry-run)
execute_sql() {
    local sql="$1"
    if [[ "$DRY_RUN" == "true" ]]; then
        info "Would execute: psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c \"$sql\""
    else
        PGPASSWORD=postgres psql -h 127.0.0.1 -p 54322 -U postgres -d postgres -c "$sql"
    fi
}

# Execute SQL file (or show if dry-run)
execute_sql_file() {
    local file="$1"
    local db="$2"
    if [[ "$DRY_RUN" == "true" ]]; then
        info "Would execute: psql -h 127.0.0.1 -p 54322 -U postgres -d $db -f $file"
    else
        PGPASSWORD=postgres psql -h 127.0.0.1 -p 54322 -U postgres -d "$db" -f "$file"
    fi
}

# Execute pg_restore (or show if dry-run)
execute_pg_restore() {
    local file="$1"
    local db="$2"
    if [[ "$DRY_RUN" == "true" ]]; then
        info "Would execute: pg_restore -h 127.0.0.1 -p 54322 -U postgres -d $db --clean --if-exists $file"
    else
        PGPASSWORD=postgres pg_restore -h 127.0.0.1 -p 54322 -U postgres -d "$db" --clean --if-exists "$file"
    fi
}

# Complete schema restore
restore_complete_schema() {
    log "Starting complete schema restore..."

    local schema_file="${DUMPS_DIR}/schema_with_constraints_${TIMESTAMP}.sql"

    if [[ ! -f "$schema_file" ]]; then
        error "Schema file not found: $schema_file"
    fi

    # Create database if it doesn't exist
    execute_sql "CREATE DATABASE $DATABASE_NAME;"

    # Restore schema
    info "Restoring complete schema from: $(basename "$schema_file")"
    execute_sql_file "$schema_file" "$DATABASE_NAME"

    log "Complete schema restore finished"
}

# Critical tables only restore
restore_critical_tables() {
    log "Starting critical tables restore..."

    local critical_file="${DUMPS_DIR}/critical_tables_schema_${TIMESTAMP}.sql"

    if [[ ! -f "$critical_file" ]]; then
        error "Critical tables file not found: $critical_file"
    fi

    # Create database if it doesn't exist
    execute_sql "CREATE DATABASE $DATABASE_NAME;"

    # Restore critical tables
    info "Restoring critical tables from: $(basename "$critical_file")"
    execute_sql_file "$critical_file" "$DATABASE_NAME"

    log "Critical tables restore finished"
}

# Custom format restore
restore_custom_schema() {
    log "Starting custom format schema restore..."

    local custom_file="${DUMPS_DIR}/schema_custom_${TIMESTAMP}.dump"

    if [[ ! -f "$custom_file" ]]; then
        error "Custom format file not found: $custom_file"
    fi

    # Create database if it doesn't exist
    execute_sql "CREATE DATABASE $DATABASE_NAME;"

    # Restore from custom format
    info "Restoring from custom format: $(basename "$custom_file")"
    execute_pg_restore "$custom_file" "$DATABASE_NAME"

    log "Custom format schema restore finished"
}

# Verify restoration
verify_restoration() {
    log "Verifying schema restoration..."

    local table_count
    table_count=$(PGPASSWORD=postgres psql -h 127.0.0.1 -p 54322 -U postgres -d "$DATABASE_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")

    if [[ "$DRY_RUN" == "true" ]]; then
        info "Would verify table count and core tables existence"
    else
        if [[ "$table_count" -gt 0 ]]; then
            log "Schema restoration verified: $table_count tables found"

            # Check for core tables
            local core_tables=("app_opportunities" "redditor" "submission" "comment")
            for table in "${core_tables[@]}"; do
                if PGPASSWORD=postgres psql -h 127.0.0.1 -p 54322 -U postgres -d "$DATABASE_NAME" -c "\d $table" &>/dev/null; then
                    log "Core table '$table' exists"
                else
                    warn "Core table '$table' not found"
                fi
            done
        else
            error "Schema restoration verification failed: No tables found"
        fi
    fi
}

# Main execution
main() {
    log "RedditHarbor Schema Restore Script Started"
    info "Mode: $MODE"
    info "Database: $DATABASE_NAME"
    info "Timestamp: $TIMESTAMP"

    if [[ "$DRY_RUN" == "true" ]]; then
        warn "DRY RUN MODE - No changes will be made"
    fi

    validate_environment

    case "$MODE" in
        "complete")
            restore_complete_schema
            ;;
        "critical")
            restore_critical_tables
            ;;
        "custom")
            restore_custom_schema
            ;;
        *)
            error "Invalid mode: $MODE"
            ;;
    esac

    verify_restoration

    log "Schema restore completed successfully"

    if [[ "$DRY_RUN" != "true" ]]; then
        info "Connect to verify: psql -h 127.0.0.1 -p 54322 -U postgres -d $DATABASE_NAME -c \"\\dt\""
    fi
}

# Trap interrupts
trap 'error "Script interrupted";' INT TERM

# Run main function
main "$@"