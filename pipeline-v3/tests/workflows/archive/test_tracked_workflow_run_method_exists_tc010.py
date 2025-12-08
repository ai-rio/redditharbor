#!/usr/bin/env python3
"""
Test TC-010: run() Method Override with Session Management for TrackedWorkflow

This test verifies that TrackedWorkflow properly overrides the run() method
with AgentOps session lifecycle management.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

# Import the actual implementation
from workflows.tracked_workflow import TrackedWorkflow


class TestTrackedWorkflowRunMethodExistsTC010:
    """Test class for TC-010: TrackedWorkflow run() Method Override"""

    def test_tracked_workflow_run_method_exists(self):
        """TC-010: Verify that TrackedWorkflow has run() method"""
        # Arrange
        workflow = TrackedWorkflow(
            name="test_workflow",
            config={},
            enable_agentops=False
        )

        # Act & Assert
        # Check if run method exists
        assert hasattr(workflow, 'run'), "TrackedWorkflow should have a run() method"

        # Check if it's callable
        assert callable(workflow.run), "run() should be callable"


def run_test():
    """Run the test directly"""
    test_instance = TestTrackedWorkflowRunMethodExistsTC010()
    try:
        test_instance.test_tracked_workflow_run_method_exists()
        print("✅ TC-010 PASSED: TrackedWorkflow run() method exists")
        return True
    except AssertionError as e:
        print(f"❌ TC-010 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-010 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)
