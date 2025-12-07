#!/usr/bin/env python3
"""
TDD Step 1: Write a test that fails for tracked workflow classes
"""

def test_tracked_workflow_exists():
    """Test that TrackedWorkflow exists and can be instantiated"""
    from workflows.tracked_workflow import TrackedWorkflow

    # This should fail: TrackedWorkflow not implemented
    workflow = TrackedWorkflow(name="test_workflow", config={})
    assert workflow is not None, "TrackedWorkflow should be created"

if __name__ == "__main__":
    try:
        test_tracked_workflow_exists()
        print("Test passed - TrackedWorkflow works correctly!")
    except AssertionError as e:
        print(f"Test failed as expected: {e}")
    except Exception as e:
        print(f"Other error: {e}")