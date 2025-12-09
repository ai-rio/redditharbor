"""
RED PHASE: Simple TDD test for session lifecycle error handling

This test creates a more realistic scenario where the workflow calls super().run()
but still fails, allowing us to test the error handling in the parent class.
"""

import pytest
from unittest.mock import Mock, patch
from agno.workflow import Workflow

from workflows.tracked_workflow import TrackedWorkflow


def test_tracked_workflow_ends_session_with_error_when_super_run_fails():
    """
    RED TEST: TrackedWorkflow should end session with error status when super().run() fails

    This test creates a workflow that calls super().run() but the parent workflow
    logic fails, testing the error handling in the finally block.
    """
    # Create a workflow that will fail during super().run() execution
    class FailingWorkflow(TrackedWorkflow):
        def run(self, *args, **kwargs):
            # Call super().run() which will execute the tracking logic
            # But then we'll make the underlying workflow fail
            # Simulate failure by raising an exception after calling super
            return super().run(*args, **kwargs)

    # Mock the tracker to capture the end_session call
    mock_tracker = Mock()
    mock_tracker.start_session.return_value = "test-session-id"

    # Mock the parent Workflow.run to raise an exception
    with patch('workflows.tracked_workflow.get_tracker', return_value=mock_tracker), \
         patch('agno.workflow.Workflow.run', side_effect=ValueError("Workflow execution failed")):

        workflow = FailingWorkflow(
            name="failing-workflow",
            enable_agentops=True
        )

        # Execute the workflow - it should raise an exception
        with pytest.raises(ValueError, match="Workflow execution failed"):
            workflow.run()

        # The session should be ended with error status
        mock_tracker.end_session.assert_called_once_with(
            status="error",
            metadata={"workflow_name": "failing-workflow"}
        )