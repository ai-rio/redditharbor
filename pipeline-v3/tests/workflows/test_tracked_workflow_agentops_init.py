#!/usr/bin/env python3
"""
TDD Test: TrackedWorkflow AgentOps Tracker Initialization

RED PHASE - Test 1: Verify tracker is initialized when enable_agentops=True

This is the critical test that should FAIL with the current implementation
where line 31 sets tracker to None instead of calling get_tracker().
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from workflows.tracked_workflow import TrackedWorkflow


class TestTrackedWorkflowAgentOpsInit:
    """Test AgentOps tracker initialization in TrackedWorkflow"""

    def test_tracker_initialized_when_agentops_enabled(self):
        """
        CRITICAL TEST: Verify tracker is properly initialized when enable_agentops=True

        Current bug: Line 31 in tracked_workflow.py sets self.agentops_tracker = None
        Expected: Should call get_tracker() and assign the result
        """
        # Arrange
        mock_tracker = Mock()
        mock_tracker.start_session = Mock(return_value="session_123")
        mock_tracker.end_session = Mock()
        mock_tracker.track_event = Mock()

        # Act
        with patch('workflows.tracked_workflow.get_tracker', return_value=mock_tracker):
            workflow = TrackedWorkflow(name="test_workflow", enable_agentops=True)

            # Assert - This should FAIL because tracker is currently set to None
            assert workflow.enable_agentops is True, "enable_agentops should be True"
            assert hasattr(workflow, 'agentops_tracker'), "Should have agentops_tracker attribute"
            assert workflow.agentops_tracker is not None, "BUG: Tracker is None but should be initialized!"
            assert workflow.agentops_tracker == mock_tracker, "Tracker should be the mock tracker"


if __name__ == "__main__":
    print("🚀 RED PHASE - Test 1: Tracker should be initialized when enable_agentops=True")
    print("=" * 80)
    print("Current bug: Line 31 sets self.agentops_tracker = None")
    print("Expected: Should call get_tracker() and store result")
    print("=" * 80)

    test_instance = TestTrackedWorkflowAgentOpsInit()
    try:
        test_instance.test_tracker_initialized_when_agentops_enabled()
        print("✅ Test PASSED - Bug is fixed!")
        exit(0)
    except AssertionError as e:
        print(f"❌ Test FAILED (Expected): {e}")
        print()
        print("This failure confirms the bug:")
        print("  - Line 31: self.agentops_tracker = None")
        print("  - Should be: self.agentops_tracker = get_tracker()")
        exit(1)
    except Exception as e:
        print(f"💥 Test ERROR: {e}")
        exit(1)
