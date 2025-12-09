"""
Test extract_and_track_cost method for P1.4 implementation
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from transform.agno_analyzer import AgnoOpportunityAnalyzer
from models.cost_tracking import CostTracking


class TestExtractAndTrackCost:
    """Test suite for extract_and_track_cost method"""

    def test_extract_and_track_cost_with_agno_response(self):
        """Test cost extraction from Agno API response with usage data"""
        # Setup analyzer
        analyzer = AgnoOpportunityAnalyzer(enable_agentops=False)

        # Mock Agno response with token usage
        mock_response = Mock()
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 1000
        mock_response.usage.completion_tokens = 500
        mock_response.usage.total_tokens = 1500
        mock_response.model = "anthropic/claude-haiku-4.5"

        # Call the method
        result = analyzer.extract_and_track_cost(mock_response, "WTP Analyst")

        # Assertions
        assert result["agent"] == "WTP Analyst"
        assert result["status"] == "success"
        assert "cost" in result
        assert result["cost"]["total_cost_usd"] == 0.0035

    def test_extract_and_track_cost_handles_missing_usage_data(self):
        """Test graceful handling when response lacks usage data"""
        analyzer = AgnoOpportunityAnalyzer(enable_agentops=False)

        # Mock response without usage data
        mock_response = Mock()
        del mock_response.usage  # Remove usage attribute

        # Call the method
        result = analyzer.extract_and_track_cost(mock_response, "Price Point")

        # Should handle gracefully with zero cost
        assert result["agent"] == "Price Point"
        assert result["status"] == "success"
        assert result["cost"]["total_cost_usd"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])