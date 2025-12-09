"""
RED PHASE: TDD test for _workflow_session attribute initialization

This is the first minimal test to expose the missing _workflow_session attribute.
Following strict TDD discipline - write failing test first, then implement minimal fix.
"""

import pytest
from workflows.tracked_workflow import TrackedWorkflow


def test_tracked_workflow_has_workflow_session_attribute():
    """
    RED TEST: TrackedWorkflow should have _workflow_session attribute initialized

    This test should FAIL because _workflow_session attribute is missing from __init__
    """
    # Arrange & Act
    workflow = TrackedWorkflow(name="test_workflow", enable_agentops=True)

    # Assert - This should FAIL with AttributeError
    assert hasattr(workflow, '_workflow_session'), "TrackedWorkflow should have _workflow_session attribute"
    assert workflow._workflow_session is not None, "_workflow_session should be initialized"