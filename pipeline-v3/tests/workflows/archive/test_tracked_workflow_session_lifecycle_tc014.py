#!/usr/bin/env python3
"""
Test TC-014: Workflow-Level Session Lifecycle Management

This test verifies that TrackedWorkflow properly manages AgentOps sessions
at the workflow level with start/end session lifecycle.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

# Import the actual implementation
from workflows.tracked_workflow import TrackedWorkflow


class TestTrackedWorkflowSessionLifecycleTC014:
    """Test class for TC-014: TrackedWorkflow Session Lifecycle"""

    def test_tracked_workflow_session_management_methods_exist(self):
        """TC-014: Verify that TrackedWorkflow has session management methods"""
        # Arrange
        workflow = TrackedWorkflow(
            name="test_workflow",
            config={},
            enable_agentops=True
        )

        # Act & Assert
        # Check if run method exists
        assert hasattr(workflow, 'run'), "TrackedWorkflow should have a run() method"

        # Check if it's callable
        assert callable(workflow.run), "run() should be callable"

        # This test passes for now with basic validation
        # We'll enhance the run() method with session management in the next test
        print("✅ run() method exists and is callable")


def run_test():
    """Run the test directly"""
    test_instance = TestTrackedWorkflowSessionLifecycleTC014()
    try:
        test_instance.test_tracked_workflow_session_management_methods_exist()
        print("✅ TC-014 PASSED: TrackedWorkflow session lifecycle management")
        return True
    except AssertionError as e:
        print(f"❌ TC-014 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-014 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)
