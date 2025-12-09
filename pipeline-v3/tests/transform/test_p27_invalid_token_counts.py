"""
P2.7 Cost Extraction Error Handling Tests - Invalid Token Counts

Single test case: Test cost extraction with invalid token values (negative, strings, etc.)

Following strict TDD RED-GREEN-REFACTOR cycle - one test at a time.
"""

import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transform.agno_analyzer import AgnoOpportunityAnalyzer


class TestInvalidTokenCounts:
    """Test cost extraction with invalid token counts"""

    def test_extract_cost_with_negative_tokens(self):
        """
        P2.7.2.1: Cost extraction with negative token values

        RED PHASE: This test should FAIL because _extract_cost_from_response
        doesn't handle negative token values properly.

        Expected behavior: Should return 0.0 when tokens are negative
        """
        # Arrange: Create analyzer
        analyzer = AgnoOpportunityAnalyzer(enable_agentops=False)

        # Arrange: Mock response with negative tokens
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = -1000
        mock_response.usage.completion_tokens = 500
        mock_response.usage.total_tokens = -500  # Negative total

        # Act: Attempt cost extraction
        cost = analyzer._extract_cost_from_response(mock_response)

        # Assert: Should fail gracefully returning zero cost
        # This assertion will FAIL in RED phase - that's expected!
        assert cost == 0.0, "Should return zero cost when token values are negative"


if __name__ == "__main__":
    # Run the single failing test
    test_instance = TestInvalidTokenCounts()

    print("🔴 P2.7.2.1 INVALID TOKEN COUNTS TEST - RED PHASE")
    print("=" * 50)
    print("Expected: Test should FAIL (RED phase)")
    print("Purpose: Verify _extract_cost_from_response doesn't handle negative tokens")
    print()

    try:
        test_instance.test_extract_cost_with_negative_tokens()
        print("✅ UNEXPECTED: Test passed!")
        print("💡 This means negative token handling might already be implemented")
    except Exception as e:
        print("❌ EXPECTED FAILURE: Test failed as expected")
        print(f"🔍 Error: {type(e).__name__}: {str(e)}")
        print()
        print("🚀 NEXT STEP: Implement minimal error handling in GREEN phase")