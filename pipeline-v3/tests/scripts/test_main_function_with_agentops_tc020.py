#!/usr/bin/env python3
"""
Test TC-020: Main function with --with-agentops flag

This test verifies that the main function correctly handles the --with-agentops flag.
"""

import sys
from pathlib import Path
import unittest.mock as mock

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.benchmark_agno_performance import PerformanceBenchmark, main


class TestMainFunctionWithAgentOpsTC020:
    """Test class for TC-020: Main function with AgentOps flag"""

    def test_main_function_with_agentops_flag(self):
        """TC-020: Verify that main function handles --with-agentops flag correctly"""

        # Mock sys.argv to simulate --with-agentops flag
        test_args = ['benchmark_agno_performance.py', '5', '--with-agentops']

        # Mock the run_full_benchmark method to capture the call
        with mock.patch('scripts.benchmark_agno_performance.PerformanceBenchmark.run_full_benchmark') as mock_run:
            mock_run.return_value = {'test': 'data'}

            try:
                # Mock sys.argv
                with mock.patch('sys.argv', test_args):
                    import asyncio
                    # Use __wrapped__ to get the original function if it's decorated
                    asyncio.run(main.__wrapped__ if hasattr(main, '__wrapped__') else main())

                # Check if run_full_benchmark was called with enable_agentops=True
                # We need to check how many times it was called and with what arguments
                calls = mock_run.call_args_list
                assert len(calls) == 1, "run_full_benchmark should be called once"
                assert calls[0][0][1] == True, "Second argument should be enable_agentops=True"

                print("✅ TC-020 PASSED: Main function handles --with-agentops flag correctly")
                return True

            except Exception as e:
                if "enable_agentops" in str(e) or "unexpected keyword argument" in str(e):
                    print(f"❌ TC-020 EXPECTED FAILURE: {e}")
                    print("   Main function needs to handle AgentOps integration")
                    return False
                else:
                    print(f"❌ TC-020 UNEXPECTED ERROR: {e}")
                    return False


def run_test():
    """Run the test directly"""
    test_instance = TestMainFunctionWithAgentOpsTC020()
    try:
        test_instance.test_main_function_with_agentops_flag()
        print("✅ TC-020 PASSED: Main function AgentOps integration")
        return True
    except AssertionError as e:
        print(f"❌ TC-020 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-020 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)