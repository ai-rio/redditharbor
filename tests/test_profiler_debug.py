#!/usr/bin/env python3
"""
Simple debug test to verify profiler integration without complex mocking.
This will help identify the actual behavior and import issues.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_import_and_basic_functionality():
    """Test basic import and function availability."""

    print("=== Testing Import and Basic Functionality ===")

    # Try importing the module
    try:
        from scripts.core import batch_opportunity_scoring
        print("✅ Successfully imported batch_opportunity_scoring module")
    except ImportError as e:
        print(f"❌ Failed to import batch_opportunity_scoring: {e}")
        return False

    # Check if the functions exist
    functions_to_check = [
        'should_run_profiler_analysis',
        'copy_profiler_from_primary',
        'update_concept_profiler_stats',
        'process_batch'
    ]

    for func_name in functions_to_check:
        if hasattr(batch_opportunity_scoring, func_name):
            print(f"✅ Function {func_name} exists")
        else:
            print(f"❌ Function {func_name} not found")
            return False

    return True

def test_function_callability():
    """Test if functions can be called directly."""

    print("\n=== Testing Function Callability ===")

    from scripts.core import batch_opportunity_scoring

    # Mock submission
    mock_submission = {
        "id": "test-123",
        "title": "Test",
        "text": "Test text"
    }

    # Mock supabase
    mock_supabase = MagicMock()

    # Test should_run_profiler_analysis with simple mock
    with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_func:
        mock_func.return_value = (False, None)

        # Call the function
        result = batch_opportunity_scoring.should_run_profiler_analysis(mock_submission, mock_supabase)

        print(f"✅ should_run_profiler_analysis called, returned: {result}")
        print(f"✅ Mock was called {mock_func.call_count} times")
        print(f"✅ Mock called with: {mock_func.call_args}")

    return True

def test_process_batch_minimal():
    """Test process_batch with minimal setup to see actual call paths."""

    print("\n=== Testing Process Batch Minimal Setup ===")

    from scripts.core import batch_opportunity_scoring

    # Mock submission
    mock_submission = {
        "id": "test-123",
        "title": "Test Submission",
        "text": "Test text content",
        "subreddit": "test",
        "score": 100,
        "num_comments": 25,
        "sentiment_score": 0.8,
        "monetization_potential": 75.0,
    }

    # Mock agent that returns high score to trigger profiling
    mock_agent = MagicMock()
    mock_agent.analyze_opportunity.return_value = {
        "final_score": 85.0,
        "monetization_potential": 75.0,
        "confidence_score": 0.85,
        "reasoning": "Test reasoning"
    }

    # Mock profiler
    mock_profiler = MagicMock()
    mock_profiler.generate_app_profile_with_evidence.return_value = {
        "app_concept": "Test Concept",
        "cost_tracking": {"total_cost_usd": 0.001, "total_tokens": 50}
    }

    # Test with direct function mocking
    with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_should_run, \
         patch.object(batch_opportunity_scoring, 'copy_profiler_from_primary') as mock_copy, \
         patch.object(batch_opportunity_scoring, 'update_concept_profiler_stats') as mock_update_stats, \
         patch.object(batch_opportunity_scoring, 'format_submission_for_agent') as mock_format:

        # Set up mocks
        mock_should_run.return_value = (False, None)  # Fresh profiling needed
        mock_format.return_value = {
            "id": "test-123",
            "title": "Test Submission",
            "text": "Test text content",
            "subreddit": "test",
            "engagement": 125,
            "comments": 25,
            "sentiment_score": 0.8,
            "db_id": "test-123",
        }

        # Call process_batch
        try:
            results, _, _, _ = batch_opportunity_scoring.process_batch(
                submissions=[mock_submission],
                agent=mock_agent,
                batch_number=1,
                llm_profiler=mock_profiler,
                ai_profile_threshold=40.0,
                supabase=MagicMock()
            )

            print("✅ process_batch completed successfully")
            print(f"✅ should_run_profiler_analysis called {mock_should_run.call_count} times")
            print(f"✅ copy_profiler_from_primary called {mock_copy.call_count} times")
            print(f"✅ update_concept_profiler_stats called {mock_update_stats.call_count} times")
            print(f"✅ format_submission_for_agent called {mock_format.call_count} times")

            # Check call arguments
            if mock_should_run.called:
                print(f"✅ should_run_profiler_analysis called with: {mock_should_run.call_args}")

            if mock_update_stats.called:
                print(f"✅ update_concept_profiler_stats called with: {mock_update_stats.call_args}")

            return True

        except Exception as e:
            print(f"❌ process_batch failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_different_mocking_approaches():
    """Test different mocking approaches to find the right one."""

    print("\n=== Testing Different Mocking Approaches ===")

    # Approach 1: Patch by module path
    print("\n--- Approach 1: Patch by module path ---")
    try:
        with patch('scripts.core.batch_opportunity_scoring.should_run_profiler_analysis') as mock_func:
            mock_func.return_value = (True, "test-concept")

            # Import after patching
            from scripts.core import batch_opportunity_scoring

            result = batch_opportunity_scoring.should_run_profiler_analysis({}, MagicMock())
            print(f"✅ Module path patching worked, result: {result}")
            print(f"✅ Mock called: {mock_func.called}")

    except Exception as e:
        print(f"❌ Module path patching failed: {e}")

    # Approach 2: Patch object
    print("\n--- Approach 2: Patch object ---")
    try:
        from scripts.core import batch_opportunity_scoring

        with patch.object(batch_opportunity_scoring, 'should_run_profiler_analysis') as mock_func:
            mock_func.return_value = (True, "test-concept")

            result = batch_opportunity_scoring.should_run_profiler_analysis({}, MagicMock())
            print(f"✅ Object patching worked, result: {result}")
            print(f"✅ Mock called: {mock_func.called}")

    except Exception as e:
        print(f"❌ Object patching failed: {e}")

    return True

if __name__ == "__main__":
    print("Starting Profiler Integration Debug Tests...")

    success = True

    # Run tests in sequence
    success &= test_import_and_basic_functionality()
    success &= test_function_callability()
    success &= test_process_batch_minimal()
    success &= test_different_mocking_approaches()

    if success:
        print("\n🎉 All debug tests passed!")
    else:
        print("\n❌ Some debug tests failed!")

    print("\n=== Debug Test Summary ===")
    print("This test helps identify:")
    print("1. Import issues")
    print("2. Function availability")
    print("3. Mocking approach that works")
    print("4. Actual call patterns in process_batch")