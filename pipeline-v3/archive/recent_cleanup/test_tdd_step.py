#!/usr/bin/env python3
"""
TDD Step 1: Write a test that fails
"""

def test_start_analysis_session_exists():
    """Test that start_analysis_session method exists"""
    from transform.agno_analyzer import AgnoOpportunityAnalyzer

    # This should fail - method doesn't exist yet
    analyzer = AgnoOpportunityAnalyzer()

    # This line should fail because method doesn't exist
    assert hasattr(analyzer, 'start_analysis_session'), "start_analysis_session method should exist"

if __name__ == "__main__":
    try:
        test_start_analysis_session_exists()
        print("Test passed - method exists!")
    except AssertionError as e:
        print(f"Test failed as expected: {e}")
    except Exception as e:
        print(f"Other error: {e}")
