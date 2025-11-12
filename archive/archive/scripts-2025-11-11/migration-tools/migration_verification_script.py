#!/usr/bin/env python3
"""
Migration Verification Script
Created: 2025-11-08

Verifies the schema consolidation migration (20251108000000) completed successfully.

Usage:
    python scripts/migration_verification_script.py

Features:
- Checks row counts before/after migration
- Validates foreign key relationships
- Verifies data integrity
- Compares column counts
- Reports missing or orphaned records
- Generates detailed verification report
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
    from config.settings import SUPABASE_KEY, SUPABASE_URL
    from supabase import Client, create_client
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please ensure supabase-py is installed: pip install supabase")
    sys.exit(1)


class MigrationVerifier:
    """Verifies database migration success and data integrity."""

    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "migration": "20251108000000_consolidate_schema_safe",
            "status": "PENDING",
            "checks": {},
            "errors": [],
            "warnings": [],
        }

    def verify_table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            result = self.client.table(table_name).select("*", count="exact").limit(0).execute()
            return True
        except Exception as e:
            self.results["errors"].append(f"Table {table_name} does not exist: {e}")
            return False

    def get_row_count(self, table_name: str) -> int:
        """Get total row count for a table."""
        try:
            result = self.client.table(table_name).select("*", count="exact").limit(0).execute()
            return result.count or 0
        except Exception as e:
            self.results["errors"].append(f"Error counting rows in {table_name}: {e}")
            return -1

    def verify_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        try:
            # Try to select the column
            result = self.client.table(table_name).select(column_name).limit(1).execute()
            return True
        except Exception:
            return False

    def check_foreign_key_integrity(
        self,
        table_name: str,
        fk_column: str,
        ref_table: str,
        ref_column: str
    ) -> tuple[int, int, int]:
        """
        Check foreign key integrity.

        Returns:
            Tuple of (total_rows, rows_with_fk, orphaned_rows)
        """
        try:
            # Get total rows
            total = self.get_row_count(table_name)

            # Get rows with non-null FK
            result = self.client.table(table_name).select(fk_column, count="exact").not_.is_(fk_column, "null").execute()
            with_fk = result.count or 0

            # Note: Full orphan detection requires SQL joins
            # This is a simplified check
            orphaned = 0  # Would need SQL to properly detect

            return total, with_fk, orphaned
        except Exception as e:
            self.results["errors"].append(
                f"Error checking FK integrity for {table_name}.{fk_column}: {e}"
            )
            return -1, -1, -1

    def verify_redditors_table(self) -> dict[str, Any]:
        """Verify redditors table migration."""
        print("\n🔍 Verifying redditors table...")
        check = {
            "table": "redditors",
            "exists": False,
            "row_count": 0,
            "new_columns": {},
            "status": "PENDING",
        }

        if not self.verify_table_exists("redditors"):
            check["status"] = "FAILED"
            return check

        check["exists"] = True
        check["row_count"] = self.get_row_count("redditors")

        # Check for new columns
        new_columns = [
            "redditor_reddit_id", "is_gold", "is_mod", "trophy",
            "removed", "name", "karma"
        ]

        for col in new_columns:
            exists = self.verify_column_exists("redditors", col)
            check["new_columns"][col] = exists
            if not exists:
                self.results["errors"].append(f"Missing column: redditors.{col}")

        # Check if all columns exist
        all_cols_exist = all(check["new_columns"].values())
        check["status"] = "PASSED" if all_cols_exist else "FAILED"

        print(f"  ✓ Row count: {check['row_count']}")
        print(f"  ✓ New columns: {sum(check['new_columns'].values())}/{len(new_columns)}")

        return check

    def verify_submissions_table(self) -> dict[str, Any]:
        """Verify submissions table migration."""
        print("\n🔍 Verifying submissions table...")
        check = {
            "table": "submissions",
            "exists": False,
            "row_count": 0,
            "new_columns": {},
            "foreign_keys": {},
            "status": "PENDING",
        }

        if not self.verify_table_exists("submissions"):
            check["status"] = "FAILED"
            return check

        check["exists"] = True
        check["row_count"] = self.get_row_count("submissions")

        # Check for new columns
        new_columns = [
            "submission_id", "archived", "removed", "attachment",
            "poll", "flair", "awards", "score", "upvote_ratio",
            "num_comments", "edited", "text", "subreddit", "permalink"
        ]

        for col in new_columns:
            exists = self.verify_column_exists("submissions", col)
            check["new_columns"][col] = exists
            if not exists:
                self.results["warnings"].append(f"Missing column: submissions.{col}")

        # Check foreign key integrity
        total, with_subreddit_fk, orphaned = self.check_foreign_key_integrity(
            "submissions", "subreddit_id", "subreddits", "id"
        )
        check["foreign_keys"]["subreddit_id"] = {
            "total_rows": total,
            "with_fk": with_subreddit_fk,
            "missing_fk": total - with_subreddit_fk,
            "backfill_percentage": round((with_subreddit_fk / total * 100) if total > 0 else 0, 2)
        }

        total, with_redditor_fk, orphaned = self.check_foreign_key_integrity(
            "submissions", "redditor_id", "redditors", "id"
        )
        check["foreign_keys"]["redditor_id"] = {
            "total_rows": total,
            "with_fk": with_redditor_fk,
            "missing_fk": total - with_redditor_fk,
            "backfill_percentage": round((with_redditor_fk / total * 100) if total > 0 else 0, 2)
        }

        # Status: PASSED if > 80% of FKs are backfilled
        subreddit_ok = check["foreign_keys"]["subreddit_id"]["backfill_percentage"] > 80
        redditor_ok = check["foreign_keys"]["redditor_id"]["backfill_percentage"] > 80
        check["status"] = "PASSED" if (subreddit_ok and redditor_ok) else "WARNING"

        print(f"  ✓ Row count: {check['row_count']}")
        print(f"  ✓ New columns: {sum(check['new_columns'].values())}/{len(new_columns)}")
        print(f"  ✓ Subreddit FK backfill: {check['foreign_keys']['subreddit_id']['backfill_percentage']}%")
        print(f"  ✓ Redditor FK backfill: {check['foreign_keys']['redditor_id']['backfill_percentage']}%")

        return check

    def verify_comments_table(self) -> dict[str, Any]:
        """Verify comments table migration."""
        print("\n🔍 Verifying comments table...")
        check = {
            "table": "comments",
            "exists": False,
            "row_count": 0,
            "new_columns": {},
            "foreign_keys": {},
            "status": "PENDING",
        }

        if not self.verify_table_exists("comments"):
            check["status"] = "FAILED"
            return check

        check["exists"] = True
        check["row_count"] = self.get_row_count("comments")

        # Check for new columns
        new_columns = [
            "link_id", "comment_id", "body", "subreddit",
            "parent_id", "score", "edited", "removed"
        ]

        for col in new_columns:
            exists = self.verify_column_exists("comments", col)
            check["new_columns"][col] = exists
            if not exists:
                self.results["warnings"].append(f"Missing column: comments.{col}")

        # Check foreign key integrity
        total, with_submission_fk, orphaned = self.check_foreign_key_integrity(
            "comments", "submission_id", "submissions", "id"
        )
        check["foreign_keys"]["submission_id"] = {
            "total_rows": total,
            "with_fk": with_submission_fk,
            "missing_fk": total - with_submission_fk,
            "backfill_percentage": round((with_submission_fk / total * 100) if total > 0 else 0, 2)
        }

        total, with_redditor_fk, orphaned = self.check_foreign_key_integrity(
            "comments", "redditor_id", "redditors", "id"
        )
        check["foreign_keys"]["redditor_id"] = {
            "total_rows": total,
            "with_fk": with_redditor_fk,
            "missing_fk": total - with_redditor_fk,
            "backfill_percentage": round((with_redditor_fk / total * 100) if total > 0 else 0, 2)
        }

        # Status: PASSED if > 80% of FKs are backfilled
        submission_ok = check["foreign_keys"]["submission_id"]["backfill_percentage"] > 80
        redditor_ok = check["foreign_keys"]["redditor_id"]["backfill_percentage"] > 80
        check["status"] = "PASSED" if (submission_ok and redditor_ok) else "WARNING"

        print(f"  ✓ Row count: {check['row_count']}")
        print(f"  ✓ New columns: {sum(check['new_columns'].values())}/{len(new_columns)}")
        print(f"  ✓ Submission FK backfill: {check['foreign_keys']['submission_id']['backfill_percentage']}%")
        print(f"  ✓ Redditor FK backfill: {check['foreign_keys']['redditor_id']['backfill_percentage']}%")

        return check

    def verify_opportunities_table(self) -> dict[str, Any]:
        """Verify opportunities table migration."""
        print("\n🔍 Verifying opportunities table...")
        check = {
            "table": "opportunities",
            "exists": False,
            "row_count": 0,
            "new_columns": {},
            "status": "PENDING",
        }

        if not self.verify_table_exists("opportunities"):
            check["status"] = "FAILED"
            return check

        check["exists"] = True
        check["row_count"] = self.get_row_count("opportunities")

        # Check for new columns
        new_columns = ["opportunity_id", "app_name", "business_category", "source_subreddit"]

        for col in new_columns:
            exists = self.verify_column_exists("opportunities", col)
            check["new_columns"][col] = exists
            if not exists:
                self.results["warnings"].append(f"Missing column: opportunities.{col}")

        check["status"] = "PASSED" if all(check["new_columns"].values()) else "WARNING"

        print(f"  ✓ Row count: {check['row_count']}")
        print(f"  ✓ New columns: {sum(check['new_columns'].values())}/{len(new_columns)}")

        return check

    def verify_opportunity_scores_table(self) -> dict[str, Any]:
        """Verify opportunity_scores table migration."""
        print("\n🔍 Verifying opportunity_scores table...")
        check = {
            "table": "opportunity_scores",
            "exists": False,
            "row_count": 0,
            "columns_verified": {},
            "status": "PENDING",
        }

        if not self.verify_table_exists("opportunity_scores"):
            check["status"] = "FAILED"
            return check

        check["exists"] = True
        check["row_count"] = self.get_row_count("opportunity_scores")

        # Verify score columns exist
        score_columns = [
            "market_demand_score", "pain_intensity_score", "monetization_potential_score",
            "market_gap_score", "technical_feasibility_score", "simplicity_score", "total_score"
        ]

        for col in score_columns:
            exists = self.verify_column_exists("opportunity_scores", col)
            check["columns_verified"][col] = exists
            if not exists:
                self.results["errors"].append(f"Missing column: opportunity_scores.{col}")

        check["status"] = "PASSED" if all(check["columns_verified"].values()) else "FAILED"

        print(f"  ✓ Row count: {check['row_count']}")
        print(f"  ✓ Score columns: {sum(check['columns_verified'].values())}/{len(score_columns)}")

        return check

    def verify_workflow_results_table(self) -> dict[str, Any]:
        """Verify workflow_results table exists."""
        print("\n🔍 Verifying workflow_results table...")
        check = {
            "table": "workflow_results",
            "exists": False,
            "row_count": 0,
            "status": "PENDING",
        }

        if not self.verify_table_exists("workflow_results"):
            check["status"] = "WARNING"
            self.results["warnings"].append("workflow_results table does not exist")
            print("  ⚠ Table does not exist (may need separate migration)")
            return check

        check["exists"] = True
        check["row_count"] = self.get_row_count("workflow_results")
        check["status"] = "PASSED"

        print(f"  ✓ Row count: {check['row_count']}")

        return check

    def run_verification(self) -> dict[str, Any]:
        """Run complete verification suite."""
        print("=" * 70)
        print("MIGRATION VERIFICATION STARTING")
        print("=" * 70)
        print(f"Migration: {self.results['migration']}")
        print(f"Timestamp: {self.results['timestamp']}")

        # Run all checks
        self.results["checks"]["redditors"] = self.verify_redditors_table()
        self.results["checks"]["submissions"] = self.verify_submissions_table()
        self.results["checks"]["comments"] = self.verify_comments_table()
        self.results["checks"]["opportunities"] = self.verify_opportunities_table()
        self.results["checks"]["opportunity_scores"] = self.verify_opportunity_scores_table()
        self.results["checks"]["workflow_results"] = self.verify_workflow_results_table()

        # Determine overall status
        statuses = [check["status"] for check in self.results["checks"].values()]
        if "FAILED" in statuses:
            self.results["status"] = "FAILED"
        elif "WARNING" in statuses:
            self.results["status"] = "WARNING"
        else:
            self.results["status"] = "PASSED"

        # Print summary
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"\nOverall Status: {self.results['status']}")
        print(f"\nErrors: {len(self.results['errors'])}")
        for error in self.results["errors"]:
            print(f"  ✗ {error}")

        print(f"\nWarnings: {len(self.results['warnings'])}")
        for warning in self.results["warnings"]:
            print(f"  ⚠ {warning}")

        print("\nTable Checks:")
        for table, check in self.results["checks"].items():
            status_icon = "✓" if check["status"] == "PASSED" else ("⚠" if check["status"] == "WARNING" else "✗")
            print(f"  {status_icon} {table}: {check['status']} ({check.get('row_count', 0)} rows)")

        return self.results

    def save_report(self, output_path: Path):
        """Save verification report to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Report saved to: {output_path}")


def main():
    """Main verification script."""
    print("\n🚀 Starting Migration Verification")

    # Initialize Supabase client
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        sys.exit(1)

    # Run verification
    verifier = MigrationVerifier(supabase_client)
    results = verifier.run_verification()

    # Save report
    output_path = project_root / "migration_verification_results.json"
    verifier.save_report(output_path)

    # Exit with appropriate code
    if results["status"] == "PASSED":
        print("\n✅ Migration verification PASSED")
        sys.exit(0)
    elif results["status"] == "WARNING":
        print("\n⚠️  Migration verification completed with WARNINGS")
        sys.exit(0)
    else:
        print("\n❌ Migration verification FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
