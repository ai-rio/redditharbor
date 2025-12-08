#!/usr/bin/env python3
"""
Test TC-006: Integration Test for Cost Extraction into AgentOps Tracking Flow

This test verifies that extract_and_track_cost properly integrates with
the _extract_cost_from_response helper method.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import Mock

# Import the actual implementation
from transform.agno_analyzer import AgnoOpportunityAnalyzer


class TestCostExtractionIntegrationTC006:
    """Test class for TC-006: Cost Extraction Integration"""

    def test_extract_and_track_cost_uses_helper(self):
        """TC-006: Verify that extract_and_track_cost uses _extract_cost_from_response"""
        # Arrange
        analyzer = AgnoOpportunityAnalyzer()
        mock_response = Mock()
        mock_response.some_cost_data = 10.5

        # Mock the helper method to return a specific value
        analyzer._extract_cost_from_response = Mock(return_value=5.25)

        # Act
        result = analyzer.extract_and_track_cost("test_agent", mock_response)

        # Assert
        # Verify the helper method was called
        analyzer._extract_cost_from_response.assert_called_once_with(mock_response)

        # Verify the result contains expected structure
        assert isinstance(result, dict)
        assert result["agent"] == "test_agent"
        assert result["status"] == "extracted"
        assert result["cost"] == 5.25  # Should use the mocked return value


def run_test():
    """Run the test directly"""
    test_instance = TestCostExtractionIntegrationTC006()
    try:
        test_instance.test_extract_and_track_cost_uses_helper()
        print("✅ TC-006.1 PASSED: extract_and_track_cost uses helper method")
        return True
    except AssertionError as e:
        print(f"❌ TC-006.1 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-006.1 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)