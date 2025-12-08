#!/usr/bin/env python3
"""
Test TC-007: Session End Return Value for end_analysis_session() method

This test is designed to fail initially since the end_analysis_session() method
doesn't exist yet.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

# Import the actual implementation
from transform.agno_analyzer import AgnoOpportunityAnalyzer


class TestEndAnalysisSessionTC007:
    """Test class for TC-007: Session End Return Value"""

    @pytest.fixture
    def analyzer_with_tracker(self):
        """Create analyzer with mock tracker"""
        mock_tracker = Mock()
        mock_tracker.end_session = AsyncMock()
        mock_tracker.get_session_summary = Mock(return_value={
            "session_id": "test-session-123",
            "status": "success",
            "duration": 5.2,
            "cost": 0.05,
            "operations": 3
        })

        with pytest.MonkeyPatch().context() as m:
            m.setattr('transform.agno_analyzer', 'get_tracker', lambda: mock_tracker)
            analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)
            analyzer.agentops_tracker = mock_tracker
            return analyzer

    @pytest.mark.asyncio
    async def test_end_session_return_value(self, analyzer_with_tracker):
        """TC-007: Test that end_analysis_session returns proper session summary"""
        # Arrange
        analyzer = analyzer_with_tracker

        # Act - This should fail initially because method doesn't exist
        result = await analyzer.end_analysis_session_async("success")

        # Assert - Expected behavior after implementation
        expected_summary = {
            "session_id": "test-session-123",
            "status": "success",
            "duration": 5.2,
            "cost": 0.05,
            "operations": 3
        }
        assert result == expected_summary
        assert result["status"] == "success"
        assert "session_id" in result
        assert "duration" in result
