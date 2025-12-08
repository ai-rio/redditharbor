#!/usr/bin/env python3
"""
Test TC-007: Basic Inheritance for TrackedWorkflow from Agno's Workflow class

This test is designed to fail initially since the TrackedWorkflow class
doesn't inherit from Agno's Workflow class yet. This follows the TDD approach.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

# Import the actual implementation
from workflows.tracked_workflow import TrackedWorkflow


class TestTrackedWorkflowInheritanceTC007:
    """Test class for TC-007: TrackedWorkflow Inheritance"""

    def test_tracked_workflow_inherits_from_workflow(self):
        """TC-007: Verify that TrackedWorkflow inherits from Agno's Workflow class"""
        # Arrange
        workflow = TrackedWorkflow(
            name="test_workflow",
            config={},
            enable_agentops=False
        )

        # Act & Assert
        # Check if it inherits from Agno's Workflow class
        from agno.workflow import Workflow
        assert isinstance(workflow, Workflow), "TrackedWorkflow should inherit from Agno's Workflow class"


def run_test():
    """Run the test directly"""
    test_instance = TestTrackedWorkflowInheritanceTC007()
    try:
        test_instance.test_tracked_workflow_inherits_from_workflow()
        print("✅ TC-007 PASSED: TrackedWorkflow inherits from Agno Workflow")
        return True
    except AssertionError as e:
        print(f"❌ TC-007 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-007 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)
