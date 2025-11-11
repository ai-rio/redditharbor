#!/usr/bin/env python3
"""
Migration Execution Script (Python-based)
Created: 2025-11-08

Executes the schema consolidation migration using Python libraries.
No psql dependency required.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

# Migration configuration
MIGRATION_FILE = project_root / "supabase/migrations/20251108000000_consolidate_schema_safe.sql"
LOG_DIR = project_root / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Database connection (from Supabase local dev)
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "54322",
    "user": "postgres",
    "password": "postgres",
    "database": "postgres"
}


class MigrationExecutor:
    """Handles safe migration execution with logging."""

    def __init__(self):
        self.log_file = LOG_DIR / f"migration_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.execution_log = []
        self.start_time = datetime.now()
        self.conn = None

    def log(self, message: str, level: str = "INFO"):
        """Log message to both console and file."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.execution_log.append(log_entry)

    def save_log(self):
        """Save execution log to file."""
        with open(self.log_file, 'w') as f:
            f.write("\n".join(self.execution_log))
        self.log(f"Execution log saved to: {self.log_file}")

    def connect_db(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.log("Database connection established", "INFO")
            return True
        except Exception as e:
            self.log(f"Database connection failed: {e}", "ERROR")
            return False

    def execute_sql(self, sql: str) -> tuple[bool, str]:
        """Execute SQL command."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
            cursor.close()
            return True, "Success"
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def execute_migration(self) -> dict[str, Any]:
        """Execute complete migration workflow."""
        self.log("=" * 70, "INFO")
        self.log("MIGRATION EXECUTION STARTING", "INFO")
        self.log("=" * 70, "INFO")
        self.log("Migration: 20251108000000_consolidate_schema_safe", "INFO")
        self.log(f"Timestamp: {self.start_time.isoformat()}", "INFO")

        results = {
            "migration_id": "20251108000000_consolidate_schema_safe",
            "start_time": self.start_time.isoformat(),
            "steps": {},
            "overall_status": "PENDING",
        }

        # Step 1: Connect to database
        self.log("\nSTEP 1: Connecting to database...", "INFO")
        if not self.connect_db():
            results["overall_status"] = "FAILED"
            results["failure_reason"] = "Database connection failed"
            self.save_log()
            return results
        results["steps"]["database_connection"] = "PASSED"

        # Step 2: Pre-migration snapshot
        self.log("\nSTEP 2: Capturing pre-migration snapshot...", "INFO")
        pre_snapshot = self.capture_snapshot()
        results["pre_snapshot"] = pre_snapshot
        results["steps"]["pre_snapshot"] = "PASSED"

        # Step 3: Execute migration SQL
        self.log("\nSTEP 3: Executing migration SQL...", "INFO")
        if not MIGRATION_FILE.exists():
            results["overall_status"] = "FAILED"
            results["failure_reason"] = f"Migration file not found: {MIGRATION_FILE}"
            self.save_log()
            return results

        with open(MIGRATION_FILE) as f:
            migration_sql = f.read()

        self.log(f"Read {len(migration_sql)} characters from migration file", "INFO")

        success, output = self.execute_sql(migration_sql)
        if not success:
            results["overall_status"] = "FAILED"
            results["failure_reason"] = f"SQL execution failed: {output}"
            results["steps"]["migration_sql"] = "FAILED"
            self.save_log()
            return results
        results["steps"]["migration_sql"] = "PASSED"

        # Step 4: Post-migration snapshot
        self.log("\nSTEP 4: Creating post-migration snapshot...", "INFO")
        post_snapshot = self.capture_snapshot()
        results["post_snapshot"] = post_snapshot
        results["steps"]["post_snapshot"] = "PASSED"

        # Step 5: Compare snapshots
        self.log("\nSTEP 5: Comparing snapshots...", "INFO")
        comparison = self.compare_snapshots(pre_snapshot, post_snapshot)
        results["snapshot_comparison"] = comparison
        results["steps"]["snapshot_comparison"] = "PASSED"

        # Step 6: Validate migration
        self.log("\nSTEP 6: Validating migration...", "INFO")
        validation = self.validate_migration()
        results["validation"] = validation
        results["steps"]["validation"] = "PASSED" if validation["status"] == "PASSED" else "FAILED"

        # Determine overall status
        if all(step == "PASSED" for step in results["steps"].values()):
            results["overall_status"] = "PASSED"
        else:
            results["overall_status"] = "FAILED"

        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration

        # Final summary
        self.log("\n" + "=" * 70, "INFO")
        self.log("MIGRATION EXECUTION COMPLETED", "INFO")
        self.log("=" * 70, "INFO")
        self.log(f"Overall Status: {results['overall_status']}", "INFO")
        self.log(f"Duration: {duration:.2f} seconds", "INFO")

        # Close connection
        if self.conn:
            self.conn.close()

        # Save execution log
        self.save_log()

        # Save results
        results_file = project_root / "migration_execution_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        self.log(f"Results saved to: {results_file}", "INFO")

        return results

    def capture_snapshot(self) -> dict[str, Any]:
        """Capture current database state."""
        snapshot = {}

        tables = ["redditors", "subreddits", "submissions", "comments", "opportunities", "opportunity_scores"]

        for table in tables:
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                cursor.close()
                snapshot[table] = {"row_count": count}
                self.log(f"  {table}: {count} rows", "INFO")
            except Exception as e:
                snapshot[table] = {"error": str(e)}
                self.log(f"  {table}: Error - {e}", "WARNING")

        return snapshot

    def compare_snapshots(self, pre: dict, post: dict) -> dict[str, Any]:
        """Compare pre and post migration snapshots."""
        comparison = {}

        for table in pre.keys():
            if table in post:
                pre_count = pre[table].get("row_count", -1)
                post_count = post[table].get("row_count", -1)

                if pre_count >= 0 and post_count >= 0:
                    diff = post_count - pre_count
                    comparison[table] = {
                        "pre_count": pre_count,
                        "post_count": post_count,
                        "difference": diff,
                        "data_loss": diff < 0
                    }

                    if diff < 0:
                        self.log(f"  WARNING: {table} lost {abs(diff)} rows!", "WARNING")
                    elif diff == 0:
                        self.log(f"  {table}: No data loss ({pre_count} rows)", "INFO")
                    else:
                        self.log(f"  {table}: Gained {diff} rows ({pre_count} -> {post_count})", "INFO")

        return comparison

    def validate_migration(self) -> dict[str, Any]:
        """Validate migration success."""
        validation = {
            "status": "PASSED",
            "checks": {},
            "errors": [],
            "warnings": []
        }

        # Check migration validation view
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM migration_validation_report")
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            cursor.close()

            validation["checks"]["migration_validation_report"] = []
            for row in rows:
                row_dict = dict(zip(column_names, row))
                validation["checks"]["migration_validation_report"].append(row_dict)
                self.log(f"  {row_dict['table_name']}: {row_dict}", "INFO")

        except Exception as e:
            validation["errors"].append(f"Could not query migration_validation_report: {e}")
            validation["status"] = "FAILED"
            self.log(f"  Error querying validation report: {e}", "ERROR")

        # Check for new columns in submissions
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'submissions'
                AND column_name IN ('submission_id', 'archived', 'subreddit', 'permalink')
            """)
            columns = [row[0] for row in cursor.fetchall()]
            cursor.close()

            validation["checks"]["submissions_new_columns"] = columns
            self.log(f"  New submissions columns found: {len(columns)}/4", "INFO")

        except Exception as e:
            validation["errors"].append(f"Could not check submissions columns: {e}")
            self.log(f"  Error checking submissions columns: {e}", "WARNING")

        return validation


def main():
    """Main execution script."""
    print("\n" + "=" * 70)
    print("SCHEMA CONSOLIDATION MIGRATION EXECUTOR")
    print("=" * 70)
    print("\nMigration: 20251108000000_consolidate_schema_safe")
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    # Execute migration
    executor = MigrationExecutor()
    results = executor.execute_migration()

    # Save detailed reports
    pre_state_file = project_root / "migration_pre_state.json"
    with open(pre_state_file, 'w') as f:
        json.dump(results.get("pre_snapshot", {}), f, indent=2)
    print(f"\nPre-state saved to: {pre_state_file}")

    post_state_file = project_root / "migration_post_state.json"
    with open(post_state_file, 'w') as f:
        json.dump(results.get("post_snapshot", {}), f, indent=2)
    print(f"Post-state saved to: {post_state_file}")

    comparison_file = project_root / "migration_results.json"
    with open(comparison_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Full results saved to: {comparison_file}")

    # Exit with appropriate code
    if results["overall_status"] == "PASSED":
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        print(f"Reason: {results.get('failure_reason', 'Unknown')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
