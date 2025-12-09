#!/usr/bin/env python3
"""
Test TC-008: Basic Structure for TrackedWorkflow

This test verifies the basic structure of TrackedWorkflow class to ensure
it can be properly extended to inherit from Agno's Workflow class.
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

# Import the actual implementation
from workflows.tracked_workflow import TrackedWorkflow


class TestTrackedWorkflowBasicTC008:
    """Test class for TC-008: TrackedWorkflow Basic Structure"""

    def test_tracked_workflow_basic_structure(self):
        """TC-008: Verify basic TrackedWorkflow structure"""
        # Arrange & Act
        workflow = TrackedWorkflow(
            name="test_workflow",
            config={"key": "value"},
            enable_agentops=True,
            cost_tracker=None
        )

        # Assert
        # Basic attributes exist
        assert workflow.name == "test_workflow"
        assert workflow.config == {"key": "value"}
        assert workflow.enable_agentops == True
        assert workflow.cost_tracker is None
