#!/usr/bin/env python3
"""
TDD Test: end_analysis_session method - Single Test

Following strict TDD principles: ONE failing test at a time.
"""

def test_end_analysis_session_method_exists():
    """Test that end_analysis_session method exists and can be called"""
    from transform.agno_analyzer import AgnoOpportunityAnalyzer

    # Create analyzer instance
    analyzer = AgnoOpportunityAnalyzer()

    # Test that method exists
    assert hasattr(analyzer, 'end_analysis_session'), "end_analysis_session method should exist"

    # Test that method can be called without error
    result = analyzer.end_analysis_session("success")

    # Test that it returns something (current implementation returns just {"status": status})
    assert isinstance(result, dict), "Should return a dictionary"
    assert "status" in result, "Should contain status key"

    # NEW TEST: Should return session_id (this will fail since current impl doesn't have this)
    assert "session_id" in result, "Result should contain session_id key"


if __name__ == "__main__":
    try:
        test_end_analysis_session_method_exists()
        print("✅ Test passed: end_analysis_session method exists and works")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")