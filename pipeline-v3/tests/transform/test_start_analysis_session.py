#!/usr/bin/env python3
"""
TDD Test: start_analysis_session method

This test follows TDD principles:
1. Write a failing test that describes desired behavior
2. Run it to confirm failure
3. Implement minimal code to make it pass
"""

def test_start_analysis_session_method_exists():
    """Test that start_analysis_session method exists and can be called"""
    from transform.agno_analyzer import AgnoOpportunityAnalyzer

    # Create analyzer instance
    analyzer = AgnoOpportunityAnalyzer()

    # Test that method exists
    assert hasattr(analyzer, 'start_analysis_session'), "start_analysis_session method should exist"

    # Test that method can be called without error
    analyzer.start_analysis_session("test-session", ["test-tag"])

if __name__ == "__main__":
    try:
        test_start_analysis_session_method_exists()
        print("✅ Test passed: start_analysis_session method exists and works")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")
