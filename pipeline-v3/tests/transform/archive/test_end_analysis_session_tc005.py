#!/usr/bin/env python3
"""
Test TC-005: Session End without Active Session for end_analysis_session() method

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


class TestEndAnalysisSessionTC005:
    """Test class for TC-005: Session End without Active Session"""

    @pytest.mark.asyncio
    async def test_end_session_without_active_session(self):
        """TC-005: Test ending session when no active session exists"""
        # Arrange
        mock_tracker = Mock()
        analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)
        analyzer.agentops_tracker = mock_tracker

        # Act & Assert - This should fail initially because method doesn't exist
        with pytest.raises(ValueError, match="No active session to end"):
            await analyzer.end_analysis_session_async("success")
