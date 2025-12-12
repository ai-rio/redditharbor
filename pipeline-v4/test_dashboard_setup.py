#!/usr/bin/env python3
"""
Dashboard Setup Verification Script
Tests that all dashboard components are properly configured
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")

    try:
        import streamlit as st
        print("  ✓ streamlit imported")
    except ImportError as e:
        print(f"  ✗ streamlit import failed: {e}")
        return False

    try:
        import pandas as pd
        print("  ✓ pandas imported")
    except ImportError as e:
        print(f"  ✗ pandas import failed: {e}")
        return False

    try:
        from database import get_db_session
        print("  ✓ database module imported")
    except ImportError as e:
        print(f"  ✗ database import failed: {e}")
        return False

    try:
        from models.analysis import Opportunity
        print("  ✓ Opportunity model imported")
    except ImportError as e:
        print(f"  ✗ Opportunity model import failed: {e}")
        return False

    try:
        from sqlmodel import func, select
        print("  ✓ sqlmodel imported")
    except ImportError as e:
        print(f"  ✗ sqlmodel import failed: {e}")
        return False

    return True


def test_database():
    """Test database connectivity and data"""
    print("\nTesting database connection...")

    try:
        from sqlmodel import func, select

        from database import get_db_session
        from models.analysis import Opportunity

        with get_db_session() as session:
            # Test connection
            total_count = session.exec(
                select(func.count(Opportunity.id))
            ).one()
            print(f"  ✓ Database connected")
            print(f"  ✓ Total opportunities: {total_count}")

            # Test high-scoring query
            high_score_count = session.exec(
                select(func.count(Opportunity.id)).where(Opportunity.final_score >= 70)
            ).one()
            print(f"  ✓ High-scoring opportunities (70+): {high_score_count}")

            # Test average score
            avg_score = session.exec(
                select(func.avg(Opportunity.final_score))
            ).one() or 0.0
            print(f"  ✓ Average score: {avg_score:.1f}")

            # Test subreddit query
            subreddits = session.exec(
                select(Opportunity.subreddit).distinct()
            ).all()
            print(f"  ✓ Unique subreddits: {len(subreddits)}")

            # Test opportunity with full data
            if total_count > 0:
                opp = session.exec(
                    select(Opportunity).limit(1)
                ).first()

                if opp:
                    print(f"  ✓ Sample opportunity loaded (ID: {opp.id})")

                    # Check analysis data
                    if opp.analysis:
                        print(f"  ✓ Analysis data present")
                        if "app_idea" in opp.analysis:
                            print(f"  ✓ App idea data present")

                    # Check metrics data
                    if opp.metrics:
                        print(f"  ✓ Metrics data present")

            return True

    except Exception as e:
        print(f"  ✗ Database test failed: {e}")
        return False


def test_dashboard_files():
    """Test that dashboard files exist and are readable"""
    print("\nTesting dashboard files...")

    base_path = Path(__file__).parent / "dashboard"

    required_files = [
        "app.py",
        "pages/1_overview.py",
        "pages/2_detailed_view.py",
        "pages/3_comparison.py",
        "__init__.py",
        "README.md",
        "QUICK_START.md",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✓ {file_path} exists")
        else:
            print(f"  ✗ {file_path} missing")
            all_exist = False

    return all_exist


def test_run_script():
    """Test that run script exists and is executable"""
    print("\nTesting run script...")

    script_path = Path(__file__).parent / "run_dashboard.sh"

    if not script_path.exists():
        print(f"  ✗ run_dashboard.sh not found")
        return False

    print(f"  ✓ run_dashboard.sh exists")

    # Check if executable
    import os
    if os.access(script_path, os.X_OK):
        print(f"  ✓ run_dashboard.sh is executable")
    else:
        print(f"  ⚠ run_dashboard.sh is not executable (run: chmod +x run_dashboard.sh)")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("RedditHarbor Dashboard Setup Verification")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    results.append(("Dashboard Files", test_dashboard_files()))
    results.append(("Run Script", test_run_script()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed! Dashboard is ready to use.")
        print("\nTo start the dashboard, run:")
        print("  ./run_dashboard.sh")
        print("\nOr directly:")
        print("  streamlit run dashboard/app.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
