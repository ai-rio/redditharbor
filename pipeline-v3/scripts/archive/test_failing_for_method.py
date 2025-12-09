#!/usr/bin/env python3
"""
Single failing test that requires end_analysis_session method
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from transform.agno_analyzer import AgnoOpportunityAnalyzer


def test_end_analysis_session_method_required():
    """Test that demonstrates the need for end_analysis_session method"""
    # Arrange
    analyzer = AgnoOpportunityAnalyzer()

    # Act & Assert - This should fail initially
    assert hasattr(analyzer, 'end_analysis_session'), "Method should exist"

    # Test method behavior
    result = analyzer.end_analysis_session("success")
    assert isinstance(result, dict), "Should return dictionary"

if __name__ == "__main__":
    try:
        test_end_analysis_session_method_required()
        print("PASS: Test passed")
    except Exception as e:
        print(f"FAIL: {e}")
