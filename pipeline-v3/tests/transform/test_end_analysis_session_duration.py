#!/usr/bin/env python3
"""
TDD Test: end_analysis_session duration tracking

Following strict TDD principles: ONE failing test at a time.
"""

def test_end_analysis_session_returns_duration():
    """Test that end_analysis_session returns session duration"""
    from transform.agno_analyzer import AgnoOpportunityAnalyzer

    # Create analyzer instance
    analyzer = AgnoOpportunityAnalyzer()

    # Test that method can be called without error
    result = analyzer.end_analysis_session("success")

    # Current implementation doesn't track duration, so this should fail
    assert "duration" in result, "Result should contain duration key"