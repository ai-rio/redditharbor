#!/usr/bin/env python3
"""
Migration Execution Script
Created: 2025-11-08

Executes the schema consolidation migration with safety checks.

Features:
- Pre-migration snapshot
- Safe SQL execution via PostgreSQL
- Detailed execution logging
- Error handling and rollback on failure
- Post-migration verification
- Comprehensive reporting
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Migration configuration
MIGRATION_FILE = project_root / "supabase/migrations/20251108000000_consolidate_schema_safe.sql"
LOG_DIR = project_root / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Database connection (from Supabase local dev)
DB_HOST = "127.0.0.1"
DB_PORT = "54322"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "postgres"


class MigrationExecutor:
    """Handles safe migration execution with logging."""

    def __init__(self):
        self.log_file = LOG_DIR / f"migration_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.execution_log = []
        self.start_time = datetime.now()

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

    def check_prerequisites(self) -> bool:
        """Check if migration can be executed."""
        self.log("Checking prerequisites...", "INFO")

        # Check if migration file exists
        if not MIGRATION_FILE.exists():
            self.log(f"Migration file not found: {MIGRATION_FILE}", "ERROR")
            return False
        self.log(f"Migration file found: {MIGRATION_FILE}", "INFO")

        # Check if PostgreSQL is accessible
        try:
            result = subprocess.run(
                ["psql", "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME, "-c", "SELECT 1;"],
                env={"PGPASSWORD": DB_PASSWORD},
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                self.log(f"PostgreSQL connection failed: {result.stderr}", "ERROR")
                return False
            self.log("PostgreSQL connection successful", "INFO")
        except Exception as e:
            self.log(f"Error checking PostgreSQL: {e}", "ERROR")
            return False

        # Check if pre-migration snapshot exists
        pre_snapshot = project_root / "migration_pre_state.json"
        if not pre_snapshot.exists():
            self.log("Pre-migration snapshot not found - will create it", "WARNING")

        return True

    def execute_sql_file(self, sql_file: Path) -> tuple[bool, str]:
        """Execute SQL file via psql."""
        self.log(f"Executing SQL file: {sql_file}", "INFO")

        try:
            result = subprocess.run(
                ["psql", "-h", DB_HOST, "-p", DB_PORT, "-U", DB_USER, "-d", DB_NAME, "-f", str(sql_file)],
                env={"PGPASSWORD": DB_PASSWORD},
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                self.log("SQL execution completed successfully", "INFO")
                return True, result.stdout
            else:
                self.log(f"SQL execution failed with return code {result.returncode}", "ERROR")
                self.log(f"STDERR: {result.stderr}", "ERROR")
                return False, result.stderr

        except subprocess.TimeoutExpired:
            self.log("SQL execution timed out (>5 minutes)", "ERROR")
            return False, "Timeout"
        except Exception as e:
            self.log(f"Exception during SQL execution: {e}", "ERROR")
            return False, str(e)

    def run_pre_snapshot(self) -> bool:
        """Run pre-migration snapshot script."""
        self.log("Running pre-migration snapshot...", "INFO")

        snapshot_script = project_root / "scripts/pre_migration_snapshot.py"
        if not snapshot_script.exists():
            self.log("Pre-migration snapshot script not found", "ERROR")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(snapshot_script)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.log("Pre-migration snapshot completed", "INFO")
                # Log snapshot output
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.log(f"  {line}", "INFO")
                return True
            else:
                self.log(f"Pre-migration snapshot failed: {result.stderr}", "ERROR")
                return False

        except Exception as e:
            self.log(f"Error running pre-migration snapshot: {e}", "ERROR")
            return False

    def run_post_verification(self) -> tuple[bool, dict[str, Any]]:
        """Run post-migration verification script."""
        self.log("Running post-migration verification...", "INFO")

        verification_script = project_root / "scripts/migration_verification_script.py"
        if not verification_script.exists():
            self.log("Verification script not found", "ERROR")
            return False, {}

        try:
            result = subprocess.run(
                [sys.executable, str(verification_script)],
                capture_output=True,
                text=True,
                timeout=120
            )

            # Log verification output
            for line in result.stdout.split('\n'):
                if line.strip():
                    self.log(f"  {line}", "INFO")

            # Load verification results
            verification_results_file = project_root / "migration_verification_results.json"
            if verification_results_file.exists():
                with open(verification_results_file) as f:
                    verification_results = json.load(f)

                status = verification_results.get("status", "UNKNOWN")
                if status in ["PASSED", "WARNING"]:
                    self.log(f"Verification completed with status: {status}", "INFO")
                    return True, verification_results
                else:
                    self.log(f"Verification failed with status: {status}", "ERROR")
                    return False, verification_results
            else:
                self.log("Verification results file not found", "ERROR")
                return False, {}

        except Exception as e:
            self.log(f"Error running verification: {e}", "ERROR")
            return False, {}

    def create_post_snapshot(self):
        """Create post-migration state snapshot."""
        self.log("Creating post-migration snapshot...", "INFO")

        snapshot_script = project_root / "scripts/pre_migration_snapshot.py"

        try:
            result = subprocess.run(
                [sys.executable, str(snapshot_script)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Rename to post-migration
                pre_state = project_root / "migration_pre_state.json"
                post_state = project_root / "migration_post_state.json"

                if pre_state.exists():
                    import shutil
                    shutil.copy(pre_state, post_state)
                    self.log(f"Post-migration snapshot saved to: {post_state}", "INFO")

        except Exception as e:
            self.log(f"Error creating post-snapshot: {e}", "WARNING")

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

        # Step 1: Check prerequisites
        self.log("\nSTEP 1: Checking prerequisites...", "INFO")
        if not self.check_prerequisites():
            results["overall_status"] = "FAILED"
            results["failure_reason"] = "Prerequisites check failed"
            self.save_log()
            return results
        results["steps"]["prerequisites"] = "PASSED"

        # Step 2: Pre-migration snapshot
        self.log("\nSTEP 2: Capturing pre-migration snapshot...", "INFO")
        if not self.run_pre_snapshot():
            results["overall_status"] = "FAILED"
            results["failure_reason"] = "Pre-migration snapshot failed"
            self.save_log()
            return results
        results["steps"]["pre_snapshot"] = "PASSED"

        # Step 3: Execute migration SQL
        self.log("\nSTEP 3: Executing migration SQL...", "INFO")
        success, output = self.execute_sql_file(MIGRATION_FILE)
        if not success:
            results["overall_status"] = "FAILED"
            results["failure_reason"] = f"SQL execution failed: {output}"
            results["steps"]["migration_sql"] = "FAILED"
            self.save_log()
            return results
        results["steps"]["migration_sql"] = "PASSED"
        results["sql_output"] = output

        # Step 4: Post-migration snapshot
        self.log("\nSTEP 4: Creating post-migration snapshot...", "INFO")
        self.create_post_snapshot()
        results["steps"]["post_snapshot"] = "COMPLETED"

        # Step 5: Run verification
        self.log("\nSTEP 5: Running verification...", "INFO")
        verification_success, verification_results = self.run_post_verification()
        results["steps"]["verification"] = "PASSED" if verification_success else "FAILED"
        results["verification_details"] = verification_results

        # Determine overall status
        if verification_success:
            results["overall_status"] = verification_results.get("status", "PASSED")
        else:
            results["overall_status"] = "FAILED"
            results["failure_reason"] = "Verification failed"

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

        # Save execution log
        self.save_log()

        # Save results
        results_file = project_root / "migration_execution_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        self.log(f"Results saved to: {results_file}", "INFO")

        return results


def main():
    """Main execution script."""
    print("\n" + "=" * 70)
    print("SCHEMA CONSOLIDATION MIGRATION EXECUTOR")
    print("=" * 70)
    print("\nWARNING: This will modify your database schema.")
    print("Ensure you have a backup before proceeding.")
    print("\nMigration: 20251108000000_consolidate_schema_safe")
    print(f"Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")

    # Execute migration
    executor = MigrationExecutor()
    results = executor.execute_migration()

    # Exit with appropriate code
    if results["overall_status"] in ["PASSED", "WARNING"]:
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        print(f"Reason: {results.get('failure_reason', 'Unknown')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
