"""
RED PHASE: TDD test for improved session lifecycle error handling

This test is intentionally written to FAIL initially, exposing the missing
error handling in AgentOps-Agno session lifecycle operations.

Following TDD red-green-refactor discipline:
1. RED: Write failing test that exposes missing error handling
2. GREEN: Implement minimal fix to make test pass
3. REFACTOR: Improve implementation while keeping tests green
"""

import pytest
from unittest.mock import Mock, patch

from workflows.tracked_workflow import TrackedWorkflow


def test_tracked_workflow_ends_session_with_error_status_on_failure():
    """
    RED TEST: TrackedWorkflow should end session with error status when workflow fails

    Current Issue: In tracked_workflow.py line 105, the finally block always
    calls end_session(status="success") even when the workflow failed.
    This provides incorrect session status information.

    Expected: Should end session with error status when super().run() raises exception
    """
    # Create a workflow that will fail during execution
    class FailingWorkflow(TrackedWorkflow):
        def run(self, *args, **kwargs):
            # Call super().run() to trigger the tracking logic
            # The mock will raise an exception in the parent's run()
            return super().run(*args, **kwargs)

    # Mock the tracker to capture the end_session call
    mock_tracker = Mock()
    mock_tracker.start_session.return_value = "test-session-id"

    # Patch get_tracker and the parent Workflow.run to simulate failure
    with patch('workflows.tracked_workflow.get_tracker', return_value=mock_tracker), \
         patch('agno.workflow.Workflow.run', side_effect=ValueError("Workflow execution failed")):

        workflow = FailingWorkflow(
            name="failing-workflow",
            enable_agentops=True
        )

        # Debug: Check the tracker setup
        print(f"workflow.agentops_tracker: {workflow.agentops_tracker}")
        print(f"mock_tracker: {mock_tracker}")
        print(f"workflow.enable_agentops: {workflow.enable_agentops}")
        print(f"hasattr(workflow, 'agentops_tracker'): {hasattr(workflow, 'agentops_tracker')}")

        # Verify the tracker was set correctly
        assert workflow.agentops_tracker is mock_tracker
        assert workflow.enable_agentops is True

        # Debug: Check the exact conditions in the run method
        print(f"Before run - enable_agentops: {workflow.enable_agentops}")
        print(f"Before run - hasattr(agentops_tracker): {hasattr(workflow, 'agentops_tracker')}")
        print(f"Before run - agentops_tracker is not None: {workflow.agentops_tracker is not None}")

        # Execute the workflow - it should raise an exception
        with pytest.raises(ValueError, match="Workflow execution failed"):
            workflow.run()

        # Debug: Check what methods were called on the tracker
        print(f"start_session called: {mock_tracker.start_session.called}")
        print(f"end_session called: {mock_tracker.end_session.called}")
        print(f"mock_tracker method calls: {mock_tracker.method_calls}")
        print(f"mock_tracker call_count: {mock_tracker.call_count}")

        # The session should be ended with error status, not success
        mock_tracker.end_session.assert_called_once_with(
            status="error",  # This should be "error", not "success"
            metadata={"workflow_name": "failing-workflow"}
        )

        # Currently this test will FAIL because the implementation incorrectly
        # uses status="success" in the finally block regardless of outcome