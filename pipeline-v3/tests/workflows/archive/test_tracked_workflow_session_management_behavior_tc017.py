#!/usr/bin/env python3
"""
Test TC-017: Actual Session Management Behavior Check

This test verifies that TrackedWorkflow's run() method actually implements
proper AgentOps session management behavior - not just method existence.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unittest.mock import Mock

import pytest

# Import the actual implementation
from workflows.tracked_workflow import TrackedWorkflow


class TestTrackedWorkflowSessionManagementBehaviorTC017:
    """Test class for TC-017: Actual Session Management Behavior"""

    def test_tracked_workflow_run_calls_start_and_end_session(self):
        """TC-017: Verify that TrackedWorkflow run() calls start_session and end_session when AgentOps is enabled"""
        # Arrange
        mock_tracker = Mock()
        mock_tracker.start_session.return_value = "test_session_123"
        mock_tracker.end_session.return_value = {"status": "success"}

        # Create workflow with AgentOps enabled and inject mock tracker
        workflow = TrackedWorkflow(
            name="test_workflow",
            config={},
            enable_agentops=True
        )
        workflow.agentops_tracker = mock_tracker

        # Act
        try:
            workflow.run()
        except Exception:
            # We expect this to fail because parent run() isn't implemented
            # But we should still see session management calls
            pass

        # Assert
        # This should fail initially because run() just has 'pass'
        # After implementation, it should call both start_session and end_session
        mock_tracker.start_session.assert_called_once_with(
            session_name="test_workflow",
            tags=["workflow", "tracked_workflow"]
        )

        # end_session should be called in finally block, even if parent run() fails
        mock_tracker.end_session.assert_called_once_with(
            status="success",
            metadata={"workflow_name": "test_workflow"}
        )


def run_test():
    """Run the test directly"""
    test_instance = TestTrackedWorkflowSessionManagementBehaviorTC017()
    try:
        test_instance.test_tracked_workflow_run_calls_start_and_end_session()
        print("✅ TC-017 PASSED: TrackedWorkflow session management behavior")
        return True
    except AssertionError as e:
        print(f"❌ TC-017 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-017 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)
