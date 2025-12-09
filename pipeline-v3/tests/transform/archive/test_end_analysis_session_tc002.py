#!/usr/bin/env python3
"""
Test TC-002: Session End with Success Status for end_analysis_session() method

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


class TestEndAnalysisSessionTC002:
    """Test class for TC-002: Session End with Success Status"""

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
    async def test_end_session_with_success_status(self, analyzer_with_tracker, mock_tracker):
        """TC-002: Test session end with success status"""
        # Arrange
        analyzer = analyzer_with_tracker

        # Act - This should fail initially since method doesn't exist
        result = await analyzer.end_analysis_session_async("success")

        # Assert - Expected behavior after implementation
        assert mock_tracker.end_session.called
        mock_tracker.end_session.assert_called_once_with("success")


def run_test():
    """Run the test directly"""
    import asyncio

    async def run_async_test():
        test_instance = TestEndAnalysisSessionTC002()
        mock_tracker = Mock()
        mock_tracker.end_session = AsyncMock()

        # Create analyzer with mock
        analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)
        analyzer.agentops_tracker = mock_tracker

        try:
            await test_instance.test_end_session_with_success_status(analyzer, mock_tracker)
            print("✅ TC-002 PASSED: Session end with success status")
            return True
        except AssertionError as e:
            print(f"❌ TC-002 FAILED: {e}")
            return False
        except Exception as e:
            print(f"❌ TC-002 ERROR: {e}")
            return False

    try:
        success = asyncio.run(run_async_test())
        return success
    except Exception as e:
        print(f"❌ TC-002 ERROR running test: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)
