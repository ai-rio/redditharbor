#!/usr/bin/env python3
"""
Pre-Migration Snapshot Script
Created: 2025-11-08

Captures current database state before migration execution.

Features:
- Captures row counts for all tables
- Records NULL FK counts
- Checks foreign key relationships
- Documents column lists
- Saves to migration_pre_state.json
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


class PreMigrationSnapshot:
    """Captures database state before migration."""

    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.snapshot: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "purpose": "Pre-migration database state snapshot",
            "tables": {},
        }

    def get_table_row_count(self, table_name: str) -> int:
        """Get total row count for a table."""
        try:
            result = self.client.table(table_name).select("*", count="exact").limit(0).execute()
            return result.count or 0
        except Exception as e:
            print(f"Warning: Could not count rows in {table_name}: {e}")
            return -1

    def get_null_count(self, table_name: str, column_name: str) -> int:
        """Get count of NULL values in a column."""
        try:
            result = self.client.table(table_name).select(column_name, count="exact").is_(column_name, "null").execute()
            return result.count or 0
        except Exception:
            # Column may not exist yet
            return -1

    def snapshot_table(self, table_name: str, fk_columns: list = None) -> dict[str, Any]:
        """Snapshot a single table."""
        print(f"Capturing snapshot: {table_name}...")

        snapshot = {
            "table": table_name,
            "row_count": self.get_table_row_count(table_name),
            "foreign_keys": {},
        }

        # Check FK null counts
        if fk_columns:
            for fk_col in fk_columns:
                null_count = self.get_null_count(table_name, fk_col)
                total = snapshot["row_count"]
                snapshot["foreign_keys"][fk_col] = {
                    "null_count": null_count,
                    "non_null_count": total - null_count if null_count >= 0 and total >= 0 else -1,
                    "total_rows": total,
                    "null_percentage": round((null_count / total * 100) if total > 0 else 0, 2)
                }

        return snapshot

    def capture_full_snapshot(self):
        """Capture snapshot of all relevant tables."""
        print("\n" + "=" * 70)
        print("PRE-MIGRATION SNAPSHOT")
        print("=" * 70)
        print(f"Timestamp: {self.snapshot['timestamp']}\n")

        # Redditors
        self.snapshot["tables"]["redditors"] = self.snapshot_table(
            "redditors",
            fk_columns=[]
        )

        # Subreddits
        self.snapshot["tables"]["subreddits"] = self.snapshot_table(
            "subreddits",
            fk_columns=[]
        )

        # Submissions
        self.snapshot["tables"]["submissions"] = self.snapshot_table(
            "submissions",
            fk_columns=["subreddit_id", "redditor_id"]
        )

        # Comments
        self.snapshot["tables"]["comments"] = self.snapshot_table(
            "comments",
            fk_columns=["submission_id", "redditor_id"]
        )

        # Opportunities
        self.snapshot["tables"]["opportunities"] = self.snapshot_table(
            "opportunities",
            fk_columns=["identified_from_submission_id"]
        )

        # Opportunity Scores
        self.snapshot["tables"]["opportunity_scores"] = self.snapshot_table(
            "opportunity_scores",
            fk_columns=["opportunity_id"]
        )

        # Workflow Results (may not exist)
        try:
            self.snapshot["tables"]["workflow_results"] = self.snapshot_table(
                "workflow_results",
                fk_columns=[]
            )
        except Exception:
            print("Note: workflow_results table does not exist (this is expected)")
            self.snapshot["tables"]["workflow_results"] = {
                "exists": False,
                "note": "Table not created yet"
            }

        # Print summary
        print("\n" + "=" * 70)
        print("SNAPSHOT SUMMARY")
        print("=" * 70)
        for table_name, data in self.snapshot["tables"].items():
            if isinstance(data.get("row_count"), int) and data["row_count"] >= 0:
                print(f"{table_name}: {data['row_count']} rows")
                if data.get("foreign_keys"):
                    for fk_name, fk_data in data["foreign_keys"].items():
                        print(f"  - {fk_name}: {fk_data['null_count']} NULL ({fk_data['null_percentage']}%)")
            else:
                print(f"{table_name}: Not accessible or does not exist")

    def save_snapshot(self, output_path: Path):
        """Save snapshot to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.snapshot, f, indent=2)
        print(f"\nSnapshot saved to: {output_path}")


def main():
    """Main snapshot script."""
    print("\nStarting pre-migration snapshot...")

    # Initialize Supabase client
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)

    # Capture snapshot
    snapshot = PreMigrationSnapshot(supabase_client)
    snapshot.capture_full_snapshot()

    # Save snapshot
    output_path = project_root / "migration_pre_state.json"
    snapshot.save_snapshot(output_path)

    print("\nPre-migration snapshot complete!")
    sys.exit(0)


if __name__ == "__main__":
    main()
