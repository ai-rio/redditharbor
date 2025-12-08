#!/usr/bin/env python3
"""
TDD Step 1: Write a test that fails for AgentOps decorators
"""

def test_trace_decorator_exists():
    """Test that trace decorator exists and can be applied"""
    from monitoring.agentops_decorators import trace

    @trace(name="test_operation")
    def test_function():
        return "test_result"

    # This should fail: trace decorator not implemented
    result = test_function()
    assert result == "test_result", "Function should return its result"

if __name__ == "__main__":
    try:
        test_trace_decorator_exists()
        print("Test passed - trace decorator works correctly!")
    except AssertionError as e:
        print(f"Test failed as expected: {e}")
    except Exception as e:
        print(f"Other error: {e}")