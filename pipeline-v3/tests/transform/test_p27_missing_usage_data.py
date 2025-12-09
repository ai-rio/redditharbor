"""
P2.7 Cost Extraction Error Handling Tests - Missing Usage Data

Single test case: Test cost extraction when usage data is missing from API response.

This is the FIRST test case in P2.7 series, following strict TDD RED-GREEN-REFACTOR cycle.
"""

import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transform.agno_analyzer import AgnoOpportunityAnalyzer


class TestMissingUsageData:
    """Test cost extraction with missing usage data"""

    def test_extract_cost_with_missing_usage_data(self):
        """
        P2.7.1: Cost extraction with missing usage data

        RED PHASE: This test should FAIL because _extract_cost_from_response
        doesn't handle missing usage attribute properly.

        Expected behavior: Should return 0.0 when usage data is missing
        """
        # Arrange: Create analyzer
        analyzer = AgnoOpportunityAnalyzer(enable_agentops=False)

        # Arrange: Mock response without usage attribute
        mock_response = Mock(spec=object)
        # Ensure usage attribute doesn't exist
        if hasattr(mock_response, 'usage'):
            delattr(mock_response, 'usage')

        # Act: Attempt cost extraction
        cost = analyzer._extract_cost_from_response(mock_response)

        # Assert: Should fail gracefully returning zero cost
        # This assertion will FAIL in RED phase - that's expected!
        assert cost == 0.0, "Should return zero cost when usage data is missing"


if __name__ == "__main__":
    # Run the single failing test
    test_instance = TestMissingUsageData()

    print("🔴 P2.7.1 MISSING USAGE DATA TEST - RED PHASE")
    print("=" * 50)
    print("Expected: Test should FAIL (RED phase)")
    print("Purpose: Verify _extract_cost_from_response doesn't handle missing usage")
    print()

    try:
        test_instance.test_extract_cost_with_missing_usage_data()
        print("✅ UNEXPECTED: Test passed!")
        print("💡 This means the error handling might already be implemented")
    except Exception as e:
        print("❌ EXPECTED FAILURE: Test failed as expected")
        print(f"🔍 Error: {type(e).__name__}: {str(e)}")
        print()
        print("🚀 NEXT STEP: Implement minimal error handling in GREEN phase")