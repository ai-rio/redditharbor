#!/usr/bin/env python3
"""
Test TC-013: Specific run() Method Override Check

This test verifies that TrackedWorkflow has specifically overridden the run() method
rather than just inheriting it from Workflow.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

# Import the actual implementation
from workflows.tracked_workflow import TrackedWorkflow


class TestTrackedWorkflowRunOverrideSpecificTC013:
    """Test class for TC-013: Specific run() Override Check"""

    def test_tracked_workflow_run_method_is_overridden(self):
        """TC-013: Verify that TrackedWorkflow has specifically overridden run() method"""
        # Arrange
        workflow = TrackedWorkflow(
            name="test_workflow",
            config={},
            enable_agentops=True
        )

        # Act & Assert
        # Check if run method exists and is defined in TrackedWorkflow class
        run_method = workflow.run

        # This test will fail initially because we haven't overridden run() yet
        # It should check that the method is defined in TrackedWorkflow, not inherited
        assert run_method.__qualname__.startswith('TrackedWorkflow.'), \
            "run() method should be defined in TrackedWorkflow class, not inherited from Workflow"

        # The test will fail until we implement the override
        print(f"run() method qualified name: {run_method.__qualname__}")


def run_test():
    """Run the test directly"""
    test_instance = TestTrackedWorkflowRunOverrideSpecificTC013()
    try:
        test_instance.test_tracked_workflow_run_method_is_overridden()
        print("✅ TC-013 PASSED: TrackedWorkflow run() method is specifically overridden")
        return True
    except AssertionError as e:
        print(f"❌ TC-013 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-013 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)
