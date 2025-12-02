#!/usr/bin/env python3
"""
RedditHarbor Final Migration Cleanup

This script handles the final cleanup after the main migration:
1. Fix view definitions with correct table references
2. Remove remaining legacy tables safely
3. Remove redundant backup tables
4. Generate final clean schema documentation

Author: Data Engineer
Date: 2025-11-18
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import asyncpg

from config.settings import get_database_config


class FinalMigrationCleanup:
    """Final cleanup operations after main migration"""

    def __init__(self):
        self.db_config = get_database_config()
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.cleanup_log = []

    def log(self, level: str, message: str, table: str = None):
        """Log cleanup activity"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'table': table,
            'message': message
        }
        self.cleanup_log.append(log_entry)

        table_str = f"[{table}] " if table else ""
        print(f"{timestamp}: {level.upper()} {table_str}{message}")

    async def get_connection(self):
        """Get database connection"""
        config = {
            'host': self.db_config['host'],
            'port': self.db_config['port'],
            'user': self.db_config['user'],
            'password': self.db_config['password'],
            'database': self.db_config['database']
        }
        return await asyncpg.connect(**config)

    async def drop_view_safely(self, conn: asyncpg.Connection, view_name: str):
        """Safely drop a view if it exists"""
        try:
            await conn.execute(f"DROP VIEW IF EXISTS {view_name} CASCADE")
            self.log("SUCCESS", f"Dropped view: {view_name}")
            return True
        except Exception as e:
            self.log("ERROR", f"Failed to drop view {view_name}: {e!s}")
            return False

    async def create_clean_unified_view(self, conn: asyncpg.Connection):
        """Create a clean unified opportunity view"""
        try:
            # First drop any existing problematic views
            await self.drop_view_safely(conn, "app_opportunities_legacy")
            await self.drop_view_safely(conn, "opportunities_legacy")
            await self.drop_view_safely(conn, "workflow_results_legacy")
            await self.drop_view_safely(conn, "migration_validation_report")

            # Create a clean unified view
            await conn.execute("""
                CREATE OR REPLACE VIEW opportunities_unified_view AS
                SELECT
                    id,
                    title,
                    problem_statement,
                    target_audience,
                    app_concept,
                    core_functions,
                    value_proposition,
                    target_user,
                    monetization_model,
                    trust_score,
                    trust_badge,
                    trust_level,
                    activity_score,
                    engagement_level,
                    trend_velocity,
                    problem_validity,
                    discussion_quality,
                    ai_confidence_level,
                    opportunity_score,
                    dimension_scores,
                    opportunity_assessment_score,
                    status,
                    created_at,
                    updated_at
                FROM opportunities_unified
                ORDER BY opportunity_score DESC NULLS LAST;
            """)

            self.log("SUCCESS", "Created clean unified view: opportunities_unified_view")
            return True

        except Exception as e:
            self.log("ERROR", f"Failed to create unified view: {e!s}")
            return False

    async def cleanup_remaining_backup_tables(self, conn: asyncpg.Connection):
        """Remove remaining redundant backup tables"""
        try:
            # Get current backup tables
            backup_tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename LIKE '%backup_20251118_%'
                ORDER BY tablename
            """)

            # Keep only the 074449 backup (the latest)
            tables_to_remove = []
            tables_to_keep = []

            for table_row in backup_tables:
                table_name = table_row['tablename']
                if '074449' in table_name:
                    tables_to_keep.append(table_name)
                else:
                    tables_to_remove.append(table_name)

            self.log("INFO", f"Keeping {len(tables_to_keep)} latest backup tables")
            self.log("INFO", f"Removing {len(tables_to_remove)} older backup tables")

            # Remove older backup tables
            removed_count = 0
            for table_name in tables_to_remove:
                try:
                    # Create backup of backup (safety)
                    backup_file = await self.create_backup(conn, table_name)

                    # Drop the backup table
                    await conn.execute(f"DROP TABLE {table_name} CASCADE")
                    self.log("SUCCESS", f"Removed old backup table: {table_name}")
                    removed_count += 1

                except Exception as e:
                    self.log("ERROR", f"Failed to remove backup table {table_name}: {e!s}")

            self.log("SUCCESS", f"Removed {removed_count} old backup tables, kept {len(tables_to_keep)} latest")
            return removed_count

        except Exception as e:
            self.log("ERROR", f"Failed to cleanup backup tables: {e!s}")
            return 0

    async def create_backup(self, conn: asyncpg.Connection, table_name: str) -> str:
        """Create a backup of table data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{table_name}_final_cleanup_{timestamp}.json"

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

    async def remove_legacy_opportunities_safely(self, conn: asyncpg.Connection):
        """Remove the remaining opportunities table safely"""
        try:
            # Check if opportunities table exists and has data
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'opportunities'
                )
            """)

            if not table_exists:
                self.log("INFO", "Legacy opportunities table already removed")
                return True

            # Check data counts
            legacy_count = await conn.fetchval("SELECT COUNT(*) FROM opportunities")
            unified_count = await conn.fetchval("SELECT COUNT(*) FROM opportunities_unified")

            self.log("INFO", f"Legacy opportunities: {legacy_count} rows")
            self.log("INFO", f"Unified opportunities: {unified_count} rows")

            if legacy_count > 0:
                self.log("WARNING", "Legacy table has data, creating full backup before removal")
                backup_file = await self.create_backup(conn, "opportunities")

                # If unified table is empty, we might want to migrate the data
                if unified_count == 0:
                    self.log("WARNING", "Unified table is empty but legacy has data - review needed")
                    # For now, keep the legacy table for safety
                    return False

            # Drop the legacy table if unified has data or legacy is empty
            if unified_count > 0 or legacy_count == 0:
                await conn.execute("DROP TABLE opportunities CASCADE")
                self.log("SUCCESS", "Removed legacy opportunities table")
                return True
            else:
                self.log("WARNING", "Keeping legacy opportunities table for data safety")
                return False

        except Exception as e:
            self.log("ERROR", f"Failed to remove legacy opportunities table: {e!s}")
            return False

    async def generate_final_schema_report(self, conn: asyncpg.Connection):
        """Generate final clean schema documentation"""
        try:
            # Get final table list
            all_tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            table_names = [row['tablename'] for row in all_tables]

            # Get all views
            all_views = await conn.fetch("""
                SELECT table_name, view_definition
                FROM information_schema.views
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            # Categorize tables
            core_tables = ['redditors', 'submissions', 'comments', 'subreddits']
            unified_tables = ['opportunities_unified', 'opportunity_assessments']
            backup_tables = [t for t in table_names if 'backup' in t]
            other_tables = [t for t in table_names if t not in core_tables + unified_tables + backup_tables]

            # Generate schema report
            schema_report = {
                'generated_at': datetime.now().isoformat(),
                'total_tables': len(table_names),
                'total_views': len(all_views),
                'table_categories': {
                    'core_reddit_tables': {
                        'count': len(core_tables),
                        'tables': core_tables
                    },
                    'unified_opportunity_tables': {
                        'count': len(unified_tables),
                        'tables': unified_tables
                    },
                    'backup_tables': {
                        'count': len(backup_tables),
                        'tables': backup_tables
                    },
                    'other_tables': {
                        'count': len(other_tables),
                        'tables': other_tables
                    }
                },
                'views': {
                    'count': len(all_views),
                    'view_names': [view['table_name'] for view in all_views]
                },
                'migration_success': {
                    'original_table_count': 59,
                    'final_table_count': len(table_names),
                    'tables_removed': 59 - len(table_names),
                    'reduction_percentage': round((59 - len(table_names)) / 59 * 100, 1)
                }
            }

            # Save schema report
            report_file = f"final_schema_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(schema_report, f, indent=2, default=str)

            self.log("SUCCESS", f"Final schema report: {report_file}")
            self.log("SUCCESS", f"Schema reduction: {59 - len(table_names)} tables removed ({schema_report['migration_success']['reduction_percentage']}%)")

            return schema_report, report_file

        except Exception as e:
            self.log("ERROR", f"Failed to generate schema report: {e!s}")
            return None, None

    async def execute_cleanup(self):
        """Execute the complete final cleanup"""
        try:
            self.log("INFO", "Starting RedditHarbor Final Migration Cleanup")

            conn = await self.get_connection()

            # Step 1: Fix views and create clean unified view
            await self.create_clean_unified_view(conn)

            # Step 2: Remove remaining backup tables
            backup_removed = await self.cleanup_remaining_backup_tables(conn)

            # Step 3: Remove legacy opportunities table safely
            legacy_removed = await self.remove_legacy_opportunities_safely(conn)

            # Step 4: Generate final schema report
            schema_report, report_file = await self.generate_final_schema_report(conn)

            # Generate cleanup report
            cleanup_report = {
                'cleanup_completed': datetime.now().isoformat(),
                'backup_tables_removed': backup_removed,
                'legacy_tables_removed': legacy_removed,
                'schema_report': schema_report,
                'cleanup_log': self.cleanup_log
            }

            cleanup_report_file = f"final_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(cleanup_report_file, 'w') as f:
                json.dump(cleanup_report, f, indent=2, default=str)

            await conn.close()

            self.log("SUCCESS", "Final cleanup completed successfully!")
            self.log("INFO", f"Cleanup report: {cleanup_report_file}")

            return True, cleanup_report_file

        except Exception as e:
            self.log("ERROR", f"Final cleanup failed: {e!s}")
            return False, None


async def main():
    """Main execution function"""
    print("RedditHarbor Final Migration Cleanup")
    print("=" * 50)
    print("Completing the migration cleanup process")
    print("=" * 50)

    cleanup = FinalMigrationCleanup()

    try:
        success, report_file = await cleanup.execute_cleanup()

        if success:
            print("\n" + "=" * 50)
            print("FINAL CLEANUP COMPLETED SUCCESSFULLY")
            print("=" * 50)
            print(f"Report: {report_file}")
            sys.exit(0)
        else:
            print("\n" + "=" * 50)
            print("FINAL CLEANUP FAILED - Check logs for details")
            print("=" * 50)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nCleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    asyncio.run(main())
