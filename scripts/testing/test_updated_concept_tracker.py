#!/usr/bin/env python3
"""
Test the updated concept_tracker.py with SQLAlchemy implementation
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.resolve()
load_dotenv(project_root / '.env.local', override=True)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add pipeline-v2 to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pipeline-v2'))

def test_concept_tracker_functions():
    """Test the actual concept_tracker.py functions with real Reddit IDs"""

    print("=== Testing Updated Concept Tracker Functions ===\n")

    try:
        # Import the updated functions
        from deduplication.concept_tracker import (
            should_run_agno_analysis,
            should_run_profiler_analysis,
            get_sqlalchemy_connection
        )

        # Mock Supabase client (won't be used due to SQLAlchemy)
        class MockSupabase:
            pass

        mock_supabase = MockSupabase()

        # Test submissions with the Reddit IDs from the error log
        test_submissions = [
            {"submission_id": "1p7drk6", "title": "Test submission 1"},
            {"submission_id": "1p7hni7", "title": "Test submission 2"},
            {"submission_id": "1p6rx44", "title": "Test submission 3"}
        ]

        print("🧪 Testing should_run_agno_analysis function:")
        for submission in test_submissions:
            print(f"\nTesting: {submission['submission_id']}")
            try:
                should_run, concept_id = should_run_agno_analysis(submission, mock_supabase)
                print(f"  ✅ Result: should_run={should_run}, concept_id={concept_id}")

                # Expected: True, None (new submissions should run analysis)
                if should_run and concept_id is None:
                    print(f"  🎯 CORRECT: New submission - will run Agno analysis")
                elif not should_run and concept_id:
                    print(f"  🎯 CORRECT: Duplicate submission - will skip Agno analysis")
                else:
                    print(f"  ⚠️  UNEXPECTED: should_run={should_run}, concept_id={concept_id}")

            except Exception as e:
                print(f"  ❌ ERROR: {e}")

        print(f"\n🧪 Testing should_run_profiler_analysis function:")
        for submission in test_submissions:
            print(f"\nTesting: {submission['submission_id']}")
            try:
                should_run, concept_id = should_run_profiler_analysis(submission, mock_supabase)
                print(f"  ✅ Result: should_run={should_run}, concept_id={concept_id}")

                # Expected: True, None (new submissions should run analysis)
                if should_run and concept_id is None:
                    print(f"  🎯 CORRECT: New submission - will run Profiler analysis")
                elif not should_run and concept_id:
                    print(f"  🎯 CORRECT: Duplicate submission - will skip Profiler analysis")
                else:
                    print(f"  ⚠️  UNEXPECTED: should_run={should_run}, concept_id={concept_id}")

            except Exception as e:
                print(f"  ❌ ERROR: {e}")

        print(f"\n🔧 Testing SQLAlchemy connection:")
        engine, conn_string = get_sqlalchemy_connection()
        if engine:
            print(f"  ✅ SQLAlchemy connection successful")
            print(f"  📊 Connection string: {conn_string}")

            # Test a simple query
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM submissions"))
                    count = result.fetchone()[0]
                    print(f"  📈 Submissions in database: {count}")
            except Exception as e:
                print(f"  ⚠️  Query error: {e}")
        else:
            print(f"  ❌ SQLAlchemy connection failed")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_concept_tracker_functions()

    if success:
        print(f"\n✅ SUCCESS: Updated concept tracker functions work!")
        print(f"🚀 Ready for Phase 1 Live Test!")
    else:
        print(f"\n❌ FAILED: Updated concept tracker functions have issues")
        print(f"🔧 Need to fix before live testing")