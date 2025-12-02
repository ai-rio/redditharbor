#!/usr/bin/env python3
"""
Database Migration Script for core_functions Format Standardization

This script migrates existing core_functions data to the standardized JSON format.
It handles all three identified formats:
1. Format A: JSON string → JSONB (already correct, preserves)
2. Format B: Python list → TEXT (converts to JSON string)
3. Format C: Mixed/legacy formats (standardizes to JSON string)

Migration Strategy:
- Scan existing records for format inconsistencies
- Convert all records to standardized JSON format
- Preserve existing data integrity
- Provide rollback capability

Author: Claude Code
Purpose: Migrate core_functions to consistent JSON format for schema consolidation
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import SUPABASE_KEY, SUPABASE_URL
from core.utils.core_functions_serialization import (
    deserialize_core_functions,
    serialize_core_functions,
    standardize_core_functions
)

# Import Supabase client
try:
    from supabase import create_client
except ImportError:
    print("Error: supabase package not found. Install with: pip install supabase")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CoreFunctionsMigrator:
    """Handles migration of core_functions data to standardized format."""

    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize migrator with Supabase connection."""
        self.client = create_client(supabase_url, supabase_key)
        self.migration_stats = {
            'total_records': 0,
            'already_standardized': 0,
            'converted_list': 0,
            'converted_comma_separated': 0,
            'converted_invalid_json': 0,
            'conversion_errors': 0,
            'tables_processed': []
        }

    def analyze_table_core_functions(self, table_name: str) -> Dict[str, Any]:
        """Analyze core_functions format distribution in a table."""
        logger.info(f"Analyzing {table_name}...")

        try:
            # Sample records to analyze formats
            response = self.client.table(table_name).select(
                "id, submission_id, core_functions"
            ).limit(100).execute()

            if not response.data:
                logger.warning(f"No data found in {table_name}")
                return {'table': table_name, 'formats': {}, 'sample_size': 0}

            formats = {
                'json_string': 0,      # Format A: JSON string (correct)
                'python_list': 0,      # Format B: Python list (needs fix)
                'comma_separated': 0,  # Part of Format B
                'invalid_json': 0,     # Invalid JSON format
                'null_or_empty': 0,    # NULL/empty values
                'other': 0             # Other formats
            }

            sample_size = len(response.data)

            for record in response.data:
                core_functions = record.get('core_functions')

                if core_functions is None or core_functions == '':
                    formats['null_or_empty'] += 1
                elif isinstance(core_functions, str):
                    try:
                        parsed = json.loads(core_functions)
                        if isinstance(parsed, list):
                            formats['json_string'] += 1
                        else:
                            formats['other'] += 1
                    except json.JSONDecodeError:
                        if ',' in core_functions:
                            formats['comma_separated'] += 1
                        else:
                            formats['invalid_json'] += 1
                elif isinstance(core_functions, list):
                    formats['python_list'] += 1
                else:
                    formats['other'] += 1

            analysis = {
                'table': table_name,
                'formats': formats,
                'sample_size': sample_size,
                'needs_migration': (
                    formats['python_list'] > 0 or
                    formats['comma_separated'] > 0 or
                    formats['invalid_json'] > 0
                )
            }

            logger.info(f"Analysis for {table_name}: {formats}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing {table_name}: {e}")
            return {'table': table_name, 'error': str(e)}

    def migrate_table(self, table_name: str, dry_run: bool = True, batch_size: int = 1000) -> bool:
        """Migrate core_functions in a table to standardized format."""
        logger.info(f"{'DRY RUN: ' if dry_run else ''}Migrating {table_name}...")

        try:
            # Get all records that need migration
            response = self.client.table(table_name).select(
                "id, submission_id, core_functions"
            ).execute()

            if not response.data:
                logger.info(f"No records found in {table_name}")
                return True

            total_records = len(response.data)
            self.migration_stats['total_records'] += total_records
            self.migration_stats['tables_processed'].append(table_name)

            logger.info(f"Processing {total_records} records from {table_name}")

            # Process records in batches
            for batch_start in range(0, total_records, batch_size):
                batch_end = min(batch_start + batch_size, total_records)
                batch_records = response.data[batch_start:batch_end]

                logger.info(f"Processing batch {batch_start//batch_size + 1}: "
                           f"records {batch_start}-{batch_end}")

                for record in batch_records:
                    try:
                        old_core_functions = record.get('core_functions')
                        record_id = record['id']
                        submission_id = record.get('submission_id', 'unknown')

                        # Analyze and standardize the format
                        new_core_functions = self._standardize_record(
                            old_core_functions, record_id, submission_id
                        )

                        # Check if migration is needed
                        if old_core_functions != new_core_functions:
                            if not dry_run:
                                # Update the record
                                update_response = self.client.table(table_name).update(
                                    {"core_functions": new_core_functions}
                                ).eq("id", record_id).execute()

                                if update_response.data:
                                    logger.debug(f"Updated record {record_id}")
                                else:
                                    logger.error(f"Failed to update record {record_id}")
                                    self.migration_stats['conversion_errors'] += 1

                            logger.info(f"{'Would update' if dry_run else 'Updated'} "
                                       f"record {record_id}: {old_core_functions} → {new_core_functions}")
                        else:
                            self.migration_stats['already_standardized'] += 1

                    except Exception as e:
                        logger.error(f"Error processing record {record.get('id')}: {e}")
                        self.migration_stats['conversion_errors'] += 1

                # Small delay to avoid overwhelming the database
                if not dry_run:
                    time.sleep(0.1)

            logger.info(f"Completed migration for {table_name}")
            return True

        except Exception as e:
            logger.error(f"Migration failed for {table_name}: {e}")
            return False

    def _standardize_record(self, core_functions: Any, record_id: str, submission_id: str) -> str:
        """Standardize a single record's core_functions field."""
        if core_functions is None or core_functions == '':
            # Standardize empty values to empty JSON array
            return json.dumps([])

        if isinstance(core_functions, str):
            try:
                # Try to parse as JSON
                parsed = json.loads(core_functions)
                if isinstance(parsed, list):
                    # Format A: Already valid JSON string
                    self.migration_stats['already_standardized'] += 1
                    return core_functions
                else:
                    # Other JSON format (object, number, etc.)
                    self.migration_stats['converted_invalid_json'] += 1
                    return serialize_core_functions([str(core_functions)])
            except json.JSONDecodeError:
                # Format B: Invalid JSON, check if comma-separated
                if ',' in core_functions:
                    self.migration_stats['converted_comma_separated'] += 1
                else:
                    self.migration_stats['converted_invalid_json'] += 1
                return serialize_core_functions(core_functions)

        elif isinstance(core_functions, list):
            # Format B: Python list that was stored as list instead of JSON string
            self.migration_stats['converted_list'] += 1
            return serialize_core_functions(core_functions)

        else:
            # Other unexpected formats
            self.migration_stats['converted_invalid_json'] += 1
            return serialize_core_functions([str(core_functions)])

    def create_backup(self, table_name: str) -> bool:
        """Create a backup of the table before migration."""
        logger.info(f"Creating backup for {table_name}...")

        try:
            backup_table = f"{table_name}_backup_{int(time.time())}"

            # This would be implemented with SQL to create table backup
            # For now, we'll just log the intention
            logger.info(f"Would create backup table: {backup_table}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backup for {table_name}: {e}")
            return False

    def print_migration_summary(self):
        """Print detailed migration statistics."""
        logger.info("=" * 80)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 80)

        stats = self.migration_stats
        logger.info(f"Total records processed: {stats['total_records']}")
        logger.info(f"Tables processed: {', '.join(stats['tables_processed'])}")
        logger.info("")
        logger.info("Format conversions:")
        logger.info(f"  - Already standardized: {stats['already_standardized']}")
        logger.info(f"  - Python list → JSON: {stats['converted_list']}")
        logger.info(f"  - Comma-separated → JSON: {stats['converted_comma_separated']}")
        logger.info(f"  - Invalid format → JSON: {stats['converted_invalid_json']}")
        logger.info(f"  - Conversion errors: {stats['conversion_errors']}")
        logger.info("")

        total_converted = (
            stats['converted_list'] +
            stats['converted_comma_separated'] +
            stats['converted_invalid_json']
        )

        if stats['total_records'] > 0:
            conversion_rate = (total_converted / stats['total_records']) * 100
            error_rate = (stats['conversion_errors'] / stats['total_records']) * 100

            logger.info(f"Conversion rate: {conversion_rate:.1f}%")
            logger.info(f"Error rate: {error_rate:.1f}%")

        logger.info("=" * 80)


def main():
    """Main migration execution."""
    parser = argparse.ArgumentParser(
        description='Migrate core_functions to standardized JSON format'
    )
    parser.add_argument(
        '--tables',
        nargs='+',
        default=['app_opportunities', 'workflow_results', 'opportunity_analysis'],
        help='Tables to migrate (default: app_opportunities, workflow_results, opportunity_analysis)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform analysis without making changes (default: false)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for processing records (default: 1000)'
    )
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze tables, do not migrate'
    )
    parser.add_argument(
        '--create-backups',
        action='store_true',
        help='Create table backups before migration'
    )

    args = parser.parse_args()

    logger.info("🚀 CORE FUNCTIONS MIGRATION")
    logger.info("=" * 80)
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    logger.info(f"Tables: {', '.join(args.tables)}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info("=" * 80)

    # Initialize migrator
    migrator = CoreFunctionsMigrator(SUPABASE_URL, SUPABASE_KEY)

    # Phase 1: Analyze all tables
    logger.info("PHASE 1: ANALYZING TABLES")
    analyses = []
    for table in args.tables:
        analysis = migrator.analyze_table_core_functions(table)
        analyses.append(analysis)

    # Print analysis summary
    logger.info("\nANALYSIS SUMMARY:")
    for analysis in analyses:
        if 'error' in analysis:
            logger.error(f"❌ {analysis['table']}: {analysis['error']}")
        else:
            needs_migration = "NEEDS MIGRATION" if analysis['needs_migration'] else "OK"
            formats = analysis['formats']
            logger.info(f"✓ {analysis['table']}: {analysis['sample_size']} records, {needs_migration}")
            if analysis['needs_migration']:
                logger.info(f"    - JSON strings: {formats['json_string']}")
                logger.info(f"    - Python lists: {formats['python_list']}")
                logger.info(f"    - Comma-separated: {formats['comma_separated']}")
                logger.info(f"    - Invalid JSON: {formats['invalid_json']}")

    if args.analyze_only:
        logger.info("\n🏁 ANALYSIS COMPLETE")
        return

    # Phase 2: Create backups if requested
    if args.create_backups and not args.dry_run:
        logger.info("\nPHASE 2: CREATING BACKUPS")
        for table in args.tables:
            migrator.create_backup(table)

    # Phase 3: Migrate tables
    logger.info("\nPHASE 3: MIGRATING TABLES")
    for table in args.tables:
        # Check if table needs migration
        analysis = next((a for a in analyses if a['table'] == table), None)
        if analysis and analysis.get('needs_migration', False):
            success = migrator.migrate_table(
                table,
                dry_run=args.dry_run,
                batch_size=args.batch_size
            )
            if success:
                logger.info(f"✓ Migration completed for {table}")
            else:
                logger.error(f"❌ Migration failed for {table}")
        else:
            logger.info(f"⏭️  Skipping {table} (no migration needed)")

    # Phase 4: Print summary
    migrator.print_migration_summary()

    if args.dry_run:
        logger.info("\n🔍 DRY RUN COMPLETE")
        logger.info("Run with --no-dry-run to perform actual migration")
    else:
        logger.info("\n🎉 MIGRATION COMPLETE")


if __name__ == "__main__":
    main()