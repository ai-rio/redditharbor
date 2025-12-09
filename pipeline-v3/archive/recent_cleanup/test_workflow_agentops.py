#!/usr/bin/env python3
"""
TDD Step 2: Write a test that fails for AgentOps integration in workflow
"""

def test_workflow_supports_agentops():
    """Test that TrackedWorkflow supports AgentOps tracking"""
    from workflows.tracked_workflow import TrackedWorkflow

    workflow = TrackedWorkflow(
        name="test_workflow",
        config={},
        enable_agentops=True
    )

    # This should fail: AgentOps not supported
    assert hasattr(workflow, 'agentops_tracker'), "agentops_tracker should exist"

if __name__ == "__main__":
    try:
        test_workflow_supports_agentops()
        print("Test passed - TrackedWorkflow AgentOps works correctly!")
    except AssertionError as e:
        print(f"Test failed as expected: {e}")
    except Exception as e:
        print(f"Other error: {e}")
