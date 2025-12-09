#!/usr/bin/env python3
"""
Test TC-004: Session End with Custom Tags for end_analysis_session() method

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


class TestEndAnalysisSessionTC004:
    """Test class for TC-004: Session End with Custom Tags"""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock AgentOps tracker for testing"""
        tracker = Mock()
        tracker.end_session = AsyncMock()
        return tracker

    @pytest.fixture
    def analyzer_with_tracker(self, mock_tracker):
        """Create analyzer with mock tracker"""
        with pytest.MonkeyPatch().context() as m:
            m.setattr('transform.agno_analyzer', 'get_tracker', lambda: mock_tracker)
            analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)
            analyzer.agentops_tracker = mock_tracker
            return analyzer

    @pytest.mark.asyncio
    async def test_end_session_with_custom_tags(self, analyzer_with_tracker, mock_tracker):
        """TC-004: Test session end with custom tags"""
        # Arrange
        analyzer = analyzer_with_tracker
        custom_tags = ["urgent", "high-priority", "manual-review"]

        # Act - This should fail initially because method doesn't exist
        result = await analyzer.end_analysis_session_async("success", tags=custom_tags)

        # Assert - Expected behavior after implementation
        assert mock_tracker.end_session.called
        # Verify custom tags were passed
        call_args = mock_tracker.end_session.call_args
        assert call_args[1]["tags"] == custom_tags
