#!/usr/bin/env python3
"""
TDD Step 3: Write a test that fails for cost tracking integration in workflow
"""

def test_workflow_tracks_cost():
    """Test that TrackedWorkflow tracks execution cost"""
    from workflows.tracked_workflow import TrackedWorkflow
    from monitoring.cost_tracker import CostTracker

    workflow = TrackedWorkflow(
        name="test_workflow",
        config={},
        cost_tracker=CostTracker()
    )

    # This should fail: cost tracking not implemented
    assert hasattr(workflow, 'cost_tracker'), "cost_tracker should be available"
    workflow.track_cost(1.5, "llm_call")
    assert workflow.cost_tracker.get_total_cost() == 1.5, "Cost should be tracked"

if __name__ == "__main__":
    try:
        test_workflow_tracks_cost()
        print("Test passed - TrackedWorkflow cost tracking works correctly!")
    except AssertionError as e:
        print(f"Test failed as expected: {e}")
    except Exception as e:
        print(f"Other error: {e}")