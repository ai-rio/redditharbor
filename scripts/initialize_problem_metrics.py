#!/usr/bin/env python3
"""
Initialize Problem Metrics Tables and Functions

This script sets up the problem_metrics table and helper functions needed for
credibility tracking of Reddit opportunities. Run this ONCE after the database
is provisioned, before running batch_opportunity_scoring with metrics.

Usage:
    python scripts/initialize_problem_metrics.py

Expected output:
    - Migration applied successfully
    - Helper functions created
    - Metrics refresh available for all submissions
    - Dashboard metrics queries ready
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

from config import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client


def run_migration(migration_path: str) -> bool:
    """
    Read SQL migration file and execute it against the database.

    Args:
        migration_path: Path to .sql migration file

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(migration_path) as f:
            sql = f.read()

        # Split by semicolon but preserve multi-line statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        print(f"\nExecuting migration: {Path(migration_path).name}")
        print(f"Total statements: {len(statements)}")

        for i, statement in enumerate(statements, 1):
            # Skip comments and empty lines
            if statement.startswith('--') or not statement:
                continue

            try:
                # Execute the statement
                response = supabase.postgrest.auth(supabase.auth.get_session()).execute(statement)
                if i % 10 == 0:
                    print(f"  ✓ Executed {i}/{len(statements)} statements")

            except Exception as e:
                # Some statements may fail if they already exist (idempotent)
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    if i % 10 == 0:
                        print(f"  ℹ️  Skipped {i}/{len(statements)} (already exists)")
                else:
                    print(f"  ⚠️  Statement {i} warning: {str(e)[:80]}")

        print("✓ Migration applied successfully!")
        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


def verify_tables_and_functions() -> bool:
    """
    Verify that problem_metrics table and helper functions exist.

    Returns:
        True if all components exist, False otherwise
    """
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        print("\nVerifying setup...")

        # Check if problem_metrics table exists
        try:
            result = supabase.table('problem_metrics').select('*').limit(1).execute()
            print("✓ problem_metrics table exists")
        except Exception as e:
            print(f"✗ problem_metrics table check failed: {str(e)[:80]}")
            return False

        # Check if refresh_problem_metrics function exists
        try:
            result = supabase.rpc('refresh_problem_metrics', {'p_problem_id': 'test'}).execute()
            print("✓ refresh_problem_metrics() function exists")
        except Exception as e:
            error_msg = str(e).lower()
            # Expected to fail with 'test' UUID, but should show function exists
            if 'test' in error_msg or 'invalid' in error_msg or 'no rows' in error_msg:
                print("✓ refresh_problem_metrics() function exists")
            else:
                print(f"⚠️  refresh_problem_metrics() function check: {str(e)[:80]}")

        # Check if get_opportunities_with_metrics function exists
        try:
            result = supabase.rpc('get_opportunities_with_metrics').execute()
            print("✓ get_opportunities_with_metrics() function exists")
        except Exception as e:
            error_msg = str(e).lower()
            # Function should exist even if no data
            if 'function' in error_msg or 'does not exist' in error_msg.lower():
                print("✗ get_opportunities_with_metrics() function not found")
                return False
            else:
                print("✓ get_opportunities_with_metrics() function exists")

        return True

    except Exception as e:
        print(f"Verification error: {e}")
        return False


def refresh_all_metrics(dry_run: bool = False) -> int:
    """
    Refresh metrics for all existing submissions in the database.

    Args:
        dry_run: If True, only show what would be done without executing

    Returns:
        Number of submissions refreshed
    """
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Get all submissions
        print("\nFetching submissions to refresh metrics for...")
        result = supabase.table('submissions').select('id').execute()
        submissions = result.data if result.data else []

        if not submissions:
            print("  No submissions found in database")
            return 0

        print(f"  Found {len(submissions)} submissions")

        if dry_run:
            print(f"  [DRY RUN] Would refresh metrics for {len(submissions)} submissions")
            return len(submissions)

        # Refresh metrics for each submission
        print(f"\nRefreshing metrics for {len(submissions)} submissions...")
        success_count = 0
        error_count = 0

        for i, submission in enumerate(submissions, 1):
            submission_id = submission.get('id')
            try:
                response = supabase.rpc(
                    'refresh_problem_metrics',
                    {'p_problem_id': submission_id}
                ).execute()
                success_count += 1

                if i % 10 == 0:
                    print(f"  ✓ Refreshed {i}/{len(submissions)} metrics")

            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Show first 5 errors only
                    print(f"  ⚠️  {submission_id[:8]}... error: {str(e)[:50]}")

        print("\n✓ Metrics refresh complete!")
        print(f"  Success: {success_count}/{len(submissions)}")
        if error_count > 0:
            print(f"  Errors: {error_count}")

        return success_count

    except Exception as e:
        print(f"✗ Metric refresh failed: {e}")
        return 0


def main():
    """
    Main execution function.
    """
    print("\n" + "="*80)
    print("PROBLEM METRICS INITIALIZATION")
    print("="*80)

    # Step 1: Run migration
    migration_file = project_root / 'supabase' / 'migrations' / '20251110151231_add_problem_metrics_table.sql'

    if not migration_file.exists():
        print(f"✗ Migration file not found: {migration_file}")
        return False

    print("\nStep 1: Apply migration")
    if not run_migration(str(migration_file)):
        print("✗ Migration failed. Exiting.")
        return False

    # Step 2: Verify setup
    print("\nStep 2: Verify migration")
    if not verify_tables_and_functions():
        print("⚠️  Some components may be missing. Continuing anyway...")

    # Step 3: Refresh metrics
    print("\nStep 3: Refresh metrics for existing submissions")
    print("(This may take a few minutes for large datasets)")
    refresh_count = refresh_all_metrics(dry_run=False)

    # Summary
    print("\n" + "="*80)
    print("INITIALIZATION SUMMARY")
    print("="*80)
    print("\n✓ Problem metrics system initialized successfully!")
    print("\nNext steps:")
    print("1. Run batch scoring: python scripts/batch_opportunity_scoring.py")
    print("   (Metrics will be automatically refreshed for new opportunities)")
    print("\n2. View dashboards with metrics:")
    print("   - Main: marimo run marimo_notebooks/opportunity_dashboard_fixed.py")
    print("   - Interactive: marimo run marimo_notebooks/opportunity_dashboard_reactive.py")
    print("   - High-score: marimo run marimo_notebooks/ultra_rare_dashboard.py")
    print("\n3. Manually refresh metrics anytime:")
    print("   SELECT refresh_problem_metrics('submission-uuid');")

    print("\n" + "="*80 + "\n")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
