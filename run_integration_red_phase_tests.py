#!/usr/bin/env python3
"""Run RED phase integration tests for database pipeline.

This script runs the integration tests that document the expected behavior
when OpportunityPipeline fetches from the actual `submissions` table.

Expected Result: All tests should FAIL (RED phase) due to:
1. Table mismatch: Code expects `app_opportunities`, DB has `submissions`
2. Column mismatch: Code expects `submission_id`, DB has `id` + `reddit_id`
3. Serialization errors: `ResolutionResult` not JSON serializable

Usage:
    python run_integration_red_phase_tests.py
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run RED phase integration tests."""
    # Get project root
    project_root = Path(__file__).parent

    # Test file path
    test_file = project_root / "tests" / "test_pipeline_database_integration.py"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1

    print("=" * 80)
    print("TDD RED PHASE - Database Pipeline Integration Tests")
    print("=" * 80)
    print()
    print("Running integration tests that verify OpportunityPipeline behavior")
    print("with the actual database schema...")
    print()
    print("Expected Result: FAIL (RED phase)")
    print("  - Table mismatch: app_opportunities vs submissions")
    print("  - Column mismatch: submission_id vs id/reddit_id")
    print("  - Serialization errors")
    print()
    print("=" * 80)
    print()

    # Run pytest with verbose output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback
        "-s",  # Show print statements
        "--color=yes",  # Colored output
    ]

    # Run the tests
    result = subprocess.run(cmd, cwd=project_root)

    print()
    print("=" * 80)
    print("RED Phase Test Results")
    print("=" * 80)

    if result.returncode == 0:
        print("✅ All tests PASSED")
        print()
        print("This means either:")
        print("  1. The GREEN phase implementation is complete")
        print("  2. The tests need to be updated to catch the failures")
        return 0
    else:
        print("❌ Tests FAILED (as expected in RED phase)")
        print()
        print("This confirms the known issues:")
        print("  1. DatabaseFetcher expects wrong table/columns")
        print("  2. Schema mismatches prevent pipeline from running")
        print("  3. Formatter cannot handle database schema")
        print()
        print("Next Steps:")
        print("  1. Fix DatabaseFetcher to support ORM mode")
        print("  2. Update formatters for dynamic schema handling")
        print("  3. Run tests again to verify GREEN phase")
        return 1


if __name__ == "__main__":
    sys.exit(main())
