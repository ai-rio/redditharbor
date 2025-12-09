#!/usr/bin/env python3
"""
Test P1.1 (RED Phase): Real cost extraction from Agno API responses

Single test: Test extracting cost from OpenRouter response structure
This test will fail initially because the functionality is not implemented.
"""

import sys
import os
from unittest.mock import Mock

# Add pipeline-v3 directory to path
pipeline_v3_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, pipeline_v3_root)

# Now import the modules
from transform.agno_analyzer import AgnoOpportunityAnalyzer


def test_extract_cost_from_openrouter_response():
    """Test extracting cost from OpenRouter API response structure"""
    # Create analyzer with cost tracking enabled
    analyzer = AgnoOpportunityAnalyzer(
        enable_agentops=True,
        model="openai/gpt-4o-mini"
    )

    # Mock OpenRouter response structure with usage data
    mock_response = Mock()
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    mock_response.model = "openai/gpt-4o-mini"

    # Extract cost
    cost_info = analyzer.extract_and_track_cost("test_agent", mock_response)

    # Verify cost extraction
    assert cost_info is not None
    assert cost_info["agent"] == "test_agent"
    assert cost_info["status"] == "extracted"
    assert "cost" in cost_info
    assert cost_info["cost"] > 0

    # Verify cost calculation based on OpenRouter pricing for gpt-4o-mini
    # Expected: (150 * $0.15/1M) + (75 * $0.60/1M) = $0.0000525
    expected_cost = (150 * 0.15 / 1000000) + (75 * 0.60 / 1000000)
    assert abs(cost_info["cost"] - expected_cost) < 0.00001


if __name__ == "__main__":
    # Run the test to see it fail
    test_extract_cost_from_openrouter_response()
    print("✓ Test passed!")