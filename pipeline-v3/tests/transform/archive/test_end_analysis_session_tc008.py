#!/usr/bin/env python3
"""
Test TC-008: Session End Error Handling for end_analysis_session() method

This test is designed to fail initially since the end_analysis_session() method
doesn't exist yet.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

# Import the actual implementation
from transform.agno_analyzer import AgnoOpportunityAnalyzer


class TestEndAnalysisSessionTC008:
    """Test class for TC-008: Session End Error Handling"""

    @pytest.fixture
    def analyzer_with_tracker(self):
        """Create analyzer with mock tracker that raises an exception"""
        mock_tracker = Mock()
        mock_tracker.end_session = AsyncMock(side_effect=Exception("Tracker connection failed"))

        with pytest.MonkeyPatch().context() as m:
            m.setattr('transform.agno_analyzer', 'get_tracker', lambda: mock_tracker)
            analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)
            analyzer.agentops_tracker = mock_tracker
            return analyzer

    @pytest.mark.asyncio
    async def test_end_session_error_handling(self, analyzer_with_tracker):
        """TC-008: Test error handling when tracker fails"""
        # Arrange
        analyzer = analyzer_with_tracker

        # Act & Assert - This should fail initially because method doesn't exist
        # but should handle errors gracefully after implementation
        with patch('transform.agno_analyzer.logger') as mock_logger:
            result = await analyzer.end_analysis_session_async("success")

            # Expected behavior after implementation:
            # Should log error but not crash
            mock_logger.error.assert_called()
            # Should return None or partial result
            assert result is not None
