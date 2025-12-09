#!/usr/bin/env python3
"""
Quick test to demonstrate the specific failure that requires end_analysis_session method
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from transform.agno_analyzer import AgnoOpportunityAnalyzer


def test_specific_method_requirements():
    """Test that demonstrates exactly what the method should do"""
    analyzer = AgnoOpportunityAnalyzer()

    # This should fail with AttributeError showing method is missing
    try:
        result = analyzer.end_analysis_session("success")
        print(f"Method exists and returned: {result}")

        # Test that it returns a dictionary
        if not isinstance(result, dict):
            print(f"ERROR: Expected dict, got {type(result)}")
            return False

        # Test that it contains the status
        if "status" not in result:
            print("ERROR: Expected 'status' key in result")
            return False

        print("SUCCESS: Method exists and works as expected")
        return True

    except AttributeError as e:
        print(f"SPECIFIC FAILURE: {e}")
        print("This shows we need to implement end_analysis_session method that:")
        print("1. Takes a status parameter")
        print("2. Returns a dictionary with at least the status")
        return False

if __name__ == "__main__":
    test_specific_method_requirements()
