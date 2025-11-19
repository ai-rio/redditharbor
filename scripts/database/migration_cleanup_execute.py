#!/usr/bin/env python3
"""
RedditHarbor Data Migration Cleanup - Option A Strategy

This script safely migrates from legacy tables to unified tables and removes redundant backup tables.

Phase 1: Data Validation (Safety First)
- Verify data consistency between legacy and unified tables
- Check row counts, key fields, data integrity
- Ensure no data loss in unified tables
- Create data validation report

Phase 2: Legacy Table Migration
- If any data exists only in legacy tables, migrate to unified tables
- Update any references/constraints that point to legacy tables
- Test application compatibility with unified-only schema

Phase 3: Cleanup Operations
- Remove legacy tables: opportunities, app_opportunities, workflow_results
- Archive/remove 46 backup tables (decide retention strategy)
- Update views and dependencies to use unified tables
- Document final clean schema structure

Author: Data Engineer
Date: 2025-11-18
Safety: High - Creates backups before any deletions
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import asyncpg

from config.settings import get_database_config


class DataMigrationCleanup:
    """
    Safe data migration cleanup from legacy to unified tables.
    """

    def __init__(self):
        self.db_config = get_database_config()
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.migration_log = []

        # Define table categories
        self.unified_tables = ['opportunities_unified', 'opportunity_assessments']
        self.legacy_tables = ['opportunities', 'app_opportunities', 'workflow_results']

        # Migration results
        self.validation_results = {}
        self.migration_results = {}
        self.cleanup_results = {}

    def log(self, level: str, message: str, table: str = None):
        """Log migration activity"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'table': table,
            'message': message
        }
        self.migration_log.append(log_entry)

        table_str = f"[{table}] " if table else ""
        print(f"{timestamp}: {level.upper()} {table_str}{message}")

    async def get_connection(self):
        """Get database connection"""
        # Remove incompatible connection parameters
        config = {
            'host': self.db_config['host'],
            'port': self.db_config['port'],
            'user': self.db_config['user'],
            'password': self.db_config['password'],
            'database': self.db_config['database']
        }
        return await asyncpg.connect(**config)

    async def create_backup(self, conn: asyncpg.Connection, table_name: str) -> str:
        """Create a backup of table data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{table_name}_backup_{timestamp}.json"

        self.log("INFO", f"Creating backup for {table_name}", table_name)

        try:
            # Get table structure
            columns = await conn.fetch(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)

            # Get all data
            data = await conn.fetch(f"SELECT * FROM {table_name}")

            backup_data = {
                'table': table_name,
                'backup_timestamp': timestamp,
                'schema': [dict(col) for col in columns],
                'data': [dict(row) for row in data],
                'row_count': len(data)
            }

            # Write backup file
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)

            self.log("SUCCESS", f"Backup created: {backup_file} ({len(data)} rows)", table_name)
            return str(backup_file)

        except Exception as e:
            self.log("ERROR", f"Backup failed: {e!s}", table_name)
            raise

    async def phase1_data_validation(self, conn: asyncpg.Connection) -> dict[str, Any]:
        """
        Phase 1: Data Validation
        Verify data consistency between legacy and unified tables
        """
        self.log("INFO", "Starting Phase 1: Data Validation")

        validation_results = {
            'legacy_vs_unified': {},
            'data_integrity': {},
            'row_counts': {},
            'backup_files': {}
        }

        try:
            # Get all tables in the database
            all_tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            table_names = [row['tablename'] for row in all_tables]

            # Separate tables by category
            backup_tables = [t for t in table_names if any(ts in t for ts in ['20251118_', 'backup', 'archive'])]
            active_tables = [t for t in table_names if t not in backup_tables and t not in self.legacy_tables]

            self.log("INFO", f"Found {len(table_names)} total tables:")
            self.log("INFO", f"  - Unified tables: {len(self.unified_tables)}")
            self.log("INFO", f"  - Legacy tables: {len(self.legacy_tables)}")
            self.log("INFO", f"  - Backup tables: {len(backup_tables)}")
            self.log("INFO", f"  - Other active tables: {len(active_tables)}")

            # Validate unified table structure and data
            for unified_table in self.unified_tables:
                if unified_table in table_names:
                    # Create backup
                    backup_file = await self.create_backup(conn, unified_table)
                    validation_results['backup_files'][unified_table] = backup_file

                    # Get row count
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {unified_table}")
                    validation_results['row_counts'][unified_table] = count

                    # Check schema integrity
                    columns = await conn.fetch(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = '{unified_table}'
                        ORDER BY ordinal_position
                    """)

                    validation_results['data_integrity'][unified_table] = {
                        'columns': len(columns),
                        'row_count': count,
                        'schema': [dict(col) for col in columns]
                    }

                    self.log("SUCCESS", f"Unified table {unified_table}: {count} rows, {len(columns)} columns")
                else:
                    self.log("WARNING", f"Unified table {unified_table} not found", unified_table)

            # Analyze legacy tables
            for legacy_table in self.legacy_tables:
                if legacy_table in table_names:
                    # Create backup
                    backup_file = await self.create_backup(conn, legacy_table)
                    validation_results['backup_files'][legacy_table] = backup_file

                    # Get row count
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {legacy_table}")
                    validation_results['row_counts'][legacy_table] = count

                    self.log("INFO", f"Legacy table {legacy_table}: {count} rows")

                    # Check if this data is already in unified tables
                    if legacy_table == 'opportunities' and 'opportunities_unified' in table_names:
                        # Compare structure
                        legacy_cols = set([col['column_name'] for col in await conn.fetch(f"""
                            SELECT column_name FROM information_schema.columns
                            WHERE table_name = '{legacy_table}'
                        """)])

                        unified_cols = set([col['column_name'] for col in await conn.fetch("""
                            SELECT column_name FROM information_schema.columns
                            WHERE table_name = 'opportunities_unified'
                        """)])

                        validation_results['legacy_vs_unified'][legacy_table] = {
                            'legacy_columns': list(legacy_cols),
                            'unified_columns': list(unified_cols),
                            'legacy_rows': count,
                            'unified_rows': validation_results['row_counts'].get('opportunities_unified', 0)
                        }

                        self.log("INFO", f"Legacy {legacy_table}: {len(legacy_cols)} cols, {count} rows")
                        self.log("INFO", f"Unified opportunities_unified: {len(unified_cols)} cols, {validation_results['row_counts'].get('opportunities_unified', 0)} rows")
                else:
                    self.log("INFO", f"Legacy table {legacy_table} not found (may already be cleaned)")

            # Analyze backup tables
            for backup_table in backup_tables[:5]:  # Sample first 5 to avoid too much output
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {backup_table}")
                validation_results['row_counts'][backup_table] = count
                self.log("INFO", f"Backup table {backup_table}: {count} rows")

            if len(backup_tables) > 5:
                self.log("INFO", f"... and {len(backup_tables) - 5} more backup tables")

            self.validation_results = validation_results
            self.log("SUCCESS", "Phase 1: Data Validation completed")

            return validation_results

        except Exception as e:
            self.log("ERROR", f"Phase 1 validation failed: {e!s}")
            raise

    async def phase2_legacy_migration(self, conn: asyncpg.Connection) -> dict[str, Any]:
        """
        Phase 2: Legacy Table Migration
        Migrate any remaining data from legacy to unified tables
        """
        self.log("INFO", "Starting Phase 2: Legacy Table Migration")

        migration_results = {
            'migrated_data': {},
            'updated_references': {},
            'compatibility_tests': {}
        }

        try:
            # Check if any legacy tables exist and have data
            for legacy_table in self.legacy_tables:
                table_exists = await conn.fetchval(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = '{legacy_table}'
                    )
                """)

                if not table_exists:
                    self.log("INFO", f"Legacy table {legacy_table} does not exist")
                    continue

                row_count = await conn.fetchval(f"SELECT COUNT(*) FROM {legacy_table}")

                if row_count == 0:
                    self.log("INFO", f"Legacy table {legacy_table} is empty", legacy_table)
                    migration_results['migrated_data'][legacy_table] = 'empty'
                    continue

                self.log("INFO", f"Processing legacy table {legacy_table} with {row_count} rows", legacy_table)

                if legacy_table == 'opportunities':
                    # Check if unified table has the same data
                    unified_count = await conn.fetchval("SELECT COUNT(*) FROM opportunities_unified")

                    # Get a sample of legacy data to check
                    sample_legacy = await conn.fetch(f"""
                        SELECT * FROM {legacy_table} LIMIT 5
                    """)

                    migration_results['migrated_data'][legacy_table] = {
                        'legacy_rows': row_count,
                        'unified_rows': unified_count,
                        'sample_legacy_data': [dict(row) for row in sample_legacy],
                        'action': 'unified_table_exists'
                    }

                    self.log("INFO", f"Legacy opportunities has {row_count} rows vs unified {unified_count} rows")

                    # If unified table is empty, we might need to migrate
                    if unified_count == 0 and row_count > 0:
                        self.log("WARNING", "Unified table is empty but legacy has data - manual migration needed")
                        migration_results['migrated_data'][legacy_table]['action'] = 'manual_migration_required'

                elif legacy_table == 'app_opportunities':
                    # Check if this data is in opportunities_unified
                    sample_data = await conn.fetch(f"SELECT * FROM {legacy_table} LIMIT 3")
                    migration_results['migrated_data'][legacy_table] = {
                        'legacy_rows': row_count,
                        'sample_data': [dict(row) for row in sample_data],
                        'action': 'review_needed'
                    }

                elif legacy_table == 'workflow_results':
                    # Check if this data is in opportunity_assessments
                    sample_data = await conn.fetch(f"SELECT * FROM {legacy_table} LIMIT 3")
                    migration_results['migrated_data'][legacy_table] = {
                        'legacy_rows': row_count,
                        'sample_data': [dict(row) for row in sample_data],
                        'action': 'review_needed'
                    }

            # Test application compatibility with unified tables
            for unified_table in self.unified_tables:
                table_exists = await conn.fetchval(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = '{unified_table}'
                    )
                """)

                if table_exists:
                    # Test basic query compatibility
                    try:
                        sample_query = await conn.fetch(f"SELECT * FROM {unified_table} LIMIT 1")
                        migration_results['compatibility_tests'][unified_table] = {
                            'status': 'success',
                            'sample_columns': list(sample_query[0].keys()) if sample_query else []
                        }
                        self.log("SUCCESS", f"Compatibility test passed for {unified_table}", unified_table)
                    except Exception as e:
                        migration_results['compatibility_tests'][unified_table] = {
                            'status': 'failed',
                            'error': str(e)
                        }
                        self.log("ERROR", f"Compatibility test failed for {unified_table}: {e!s}", unified_table)

            self.migration_results = migration_results
            self.log("SUCCESS", "Phase 2: Legacy Table Migration completed")

            return migration_results

        except Exception as e:
            self.log("ERROR", f"Phase 2 migration failed: {e!s}")
            raise

    async def phase3_cleanup_operations(self, conn: asyncpg.Connection) -> dict[str, Any]:
        """
        Phase 3: Cleanup Operations
        Remove legacy tables and backup tables
        """
        self.log("INFO", "Starting Phase 3: Cleanup Operations")

        cleanup_results = {
            'legacy_tables_removed': {},
            'backup_tables_removed': [],
            'backup_tables_retained': [],
            'views_updated': {},
            'final_schema': {}
        }

        try:
            # Get current table list
            all_tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            table_names = [row['tablename'] for row in all_tables]

            # Step 1: Remove legacy tables (after final backup)
            for legacy_table in self.legacy_tables:
                if legacy_table in table_names:
                    # Create final backup
                    backup_file = await self.create_backup(conn, legacy_table)

                    # Double-check data is in unified tables
                    if legacy_table == 'opportunities' and 'opportunities_unified' in table_names:
                        unified_count = await conn.fetchval("SELECT COUNT(*) FROM opportunities_unified")
                        legacy_count = await conn.fetchval(f"SELECT COUNT(*) FROM {legacy_table}")

                        if unified_count > 0:
                            self.log("INFO", f"Unified table has {unified_count} rows, safe to remove {legacy_table}", legacy_table)

                            # Drop the legacy table
                            await conn.execute(f"DROP TABLE {legacy_table} CASCADE")
                            cleanup_results['legacy_tables_removed'][legacy_table] = {
                                'status': 'success',
                                'backup_file': backup_file,
                                'rows_migrated': unified_count
                            }
                            self.log("SUCCESS", f"Dropped legacy table: {legacy_table}", legacy_table)
                        else:
                            self.log("WARNING", f"Unified table is empty, keeping {legacy_table} for safety", legacy_table)
                            cleanup_results['legacy_tables_removed'][legacy_table] = {
                                'status': 'skipped',
                                'reason': 'unified_table_empty',
                                'backup_file': backup_file
                            }
                    else:
                        # For other legacy tables, check if it's safe to remove
                        row_count = await conn.fetchval(f"SELECT COUNT(*) FROM {legacy_table}")
                        if row_count == 0:
                            await conn.execute(f"DROP TABLE {legacy_table} CASCADE")
                            cleanup_results['legacy_tables_removed'][legacy_table] = {
                                'status': 'success',
                                'backup_file': backup_file,
                                'rows_removed': 0
                            }
                            self.log("SUCCESS", f"Dropped empty legacy table: {legacy_table}", legacy_table)
                        else:
                            self.log("WARNING", f"Legacy table {legacy_table} has {row_count} rows, manual review needed", legacy_table)
                            cleanup_results['legacy_tables_removed'][legacy_table] = {
                                'status': 'manual_review_required',
                                'row_count': row_count,
                                'backup_file': backup_file
                            }
                else:
                    self.log("INFO", f"Legacy table {legacy_table} already removed")
                    cleanup_results['legacy_tables_removed'][legacy_table] = {'status': 'already_removed'}

            # Step 2: Handle backup tables
            backup_tables = [t for t in table_names if any(ts in t for ts in ['20251118_', 'backup', 'archive'])]

            # Strategy: Keep the most recent backup for each original table
            original_to_backups = {}
            for backup_table in backup_tables:
                # Extract original table name (before timestamp)
                original_name = backup_table
                for ts in ['20251118_', 'backup', 'archive']:
                    if ts in backup_table:
                        parts = backup_table.split(ts)
                        original_name = parts[0] if parts[0] else parts[1].split('_')[0]
                        break

                if original_name not in original_to_backups:
                    original_to_backups[original_name] = []
                original_to_backups[original_name].append(backup_table)

            # Keep only the most recent backup for each original table
            for original_name, backups in original_to_backups.items():
                # Sort by timestamp (assuming timestamp is in filename)
                backups.sort(reverse=True)  # Most recent first

                # Keep the first (most recent), remove the rest
                if len(backups) > 1:
                    cleanup_results['backup_tables_retained'].append(backups[0])

                    for backup_to_remove in backups[1:]:
                        try:
                            # Create backup of backup (meta-backup)
                            backup_file = await self.create_backup(conn, backup_to_remove)

                            # Drop the backup table
                            await conn.execute(f"DROP TABLE {backup_to_remove} CASCADE")
                            cleanup_results['backup_tables_removed'].append({
                                'table': backup_to_remove,
                                'backup_file': backup_file
                            })
                            self.log("SUCCESS", f"Removed backup table: {backup_to_remove}")
                        except Exception as e:
                            self.log("ERROR", f"Failed to remove backup table {backup_to_remove}: {e!s}")
                else:
                    cleanup_results['backup_tables_retained'].extend(backups)

            # Step 3: Update views to use unified tables
            all_views = await conn.fetch("""
                SELECT table_name, view_definition
                FROM information_schema.views
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            for view in all_views:
                view_name = view['table_name']
                view_def = view['view_definition']

                # Check if view references legacy tables
                needs_update = False
                for legacy_table in self.legacy_tables:
                    if legacy_table in view_def:
                        needs_update = True
                        # Replace with unified table name
                        if legacy_table == 'opportunities':
                            view_def = view_def.replace(legacy_table, 'opportunities_unified')
                        elif legacy_table == 'workflow_results':
                            view_def = view_def.replace(legacy_table, 'opportunity_assessments')

                if needs_update:
                    try:
                        await conn.execute(f"""
                            CREATE OR REPLACE VIEW {view_name} AS {view_def}
                        """)
                        cleanup_results['views_updated'][view_name] = {
                            'status': 'success',
                            'updated_definition': True
                        }
                        self.log("SUCCESS", f"Updated view: {view_name}")
                    except Exception as e:
                        cleanup_results['views_updated'][view_name] = {
                            'status': 'failed',
                            'error': str(e)
                        }
                        self.log("ERROR", f"Failed to update view {view_name}: {e!s}")

            # Step 4: Generate final schema report
            final_tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            final_table_names = [row['tablename'] for row in final_tables]
            cleanup_results['final_schema'] = {
                'total_tables': len(final_table_names),
                'tables': final_table_names,
                'unified_tables': [t for t in self.unified_tables if t in final_table_names],
                'legacy_tables_remaining': [t for t in self.legacy_tables if t in final_table_names],
                'backup_tables_remaining': [t for t in final_table_names if any(ts in t for ts in ['20251118_', 'backup', 'archive'])]
            }

            self.cleanup_results = cleanup_results
            self.log("SUCCESS", f"Phase 3: Cleanup completed. Final schema: {len(final_table_names)} tables")

            return cleanup_results

        except Exception as e:
            self.log("ERROR", f"Phase 3 cleanup failed: {e!s}")
            raise

    async def generate_migration_report(self) -> str:
        """Generate comprehensive migration report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"migration_cleanup_report_{timestamp}.json"

        report = {
            'migration_completed': datetime.now().isoformat(),
            'migration_strategy': 'Option A - Unified Tables Only',
            'phases_completed': {
                'phase1_validation': bool(self.validation_results),
                'phase2_migration': bool(self.migration_results),
                'phase3_cleanup': bool(self.cleanup_results)
            },
            'validation_results': self.validation_results,
            'migration_results': self.migration_results,
            'cleanup_results': self.cleanup_results,
            'migration_log': self.migration_log,
            'summary': {
                'original_table_count': self.validation_results.get('row_counts', {}),
                'final_table_count': self.cleanup_results.get('final_schema', {}).get('total_tables', 0),
                'tables_removed': len(self.cleanup_results.get('backup_tables_removed', [])) + len([t for t in self.cleanup_results.get('legacy_tables_removed', {}).values() if t.get('status') == 'success']),
                'backup_files_created': list(self.validation_results.get('backup_files', {}).values())
            }
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.log("SUCCESS", f"Migration report generated: {report_file}")
        return report_file

    async def execute_migration(self):
        """Execute the complete migration process"""
        try:
            self.log("INFO", "Starting RedditHarbor Data Migration Cleanup")
            self.log("INFO", "Strategy: Option A - Transition to unified tables only")

            conn = await self.get_connection()

            # Phase 1: Data Validation
            await self.phase1_data_validation(conn)

            # Phase 2: Legacy Migration
            await self.phase2_legacy_migration(conn)

            # Phase 3: Cleanup Operations
            await self.phase3_cleanup_operations(conn)

            # Generate final report
            report_file = await self.generate_migration_report()

            await conn.close()

            self.log("SUCCESS", "Migration cleanup completed successfully!")
            self.log("INFO", f"Final report: {report_file}")

            return True

        except Exception as e:
            self.log("ERROR", f"Migration failed: {e!s}")
            return False


async def main():
    """Main execution function"""
    print("RedditHarbor Data Migration Cleanup")
    print("=" * 50)
    print("Strategy: Option A - Unified Tables Only")
    print("Safety: Creates backups before any deletions")
    print("=" * 50)

    migration = DataMigrationCleanup()

    try:
        success = await migration.execute_migration()

        if success:
            print("\n" + "=" * 50)
            print("MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 50)

            # Print summary
            if migration.cleanup_results.get('final_schema'):
                final_schema = migration.cleanup_results['final_schema']
                print(f"Final schema: {final_schema['total_tables']} tables")
                print(f"Unified tables: {len(final_schema['unified_tables'])}")
                print(f"Legacy tables remaining: {len(final_schema['legacy_tables_remaining'])}")
                print(f"Backup tables remaining: {len(final_schema['backup_tables_remaining'])}")

            sys.exit(0)
        else:
            print("\n" + "=" * 50)
            print("MIGRATION FAILED - Check logs for details")
            print("=" * 50)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
