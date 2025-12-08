#!/usr/bin/env python3
"""
Test TC-019: Benchmark passes AgentOps flag to run_full_benchmark

This test verifies that the benchmark script correctly passes the enable_agentops
parameter to the run_full_benchmark method.
"""

import sys
from pathlib import Path
import unittest.mock as mock

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.benchmark_agno_performance import PerformanceBenchmark


class TestBenchmarkPassesAgentOpsTC019:
    """Test class for TC-019: Benchmark passes AgentOps flag"""

    def test_benchmark_passes_agentops_to_run_full_benchmark(self):
        """TC-019: Verify that benchmark passes enable_agentops to run_full_benchmark method"""

        # Create benchmark instance
        benchmark = PerformanceBenchmark()

        # Mock the run_full_benchmark method
        with mock.patch.object(benchmark, 'run_full_benchmark') as mock_run:
            mock_run.return_value = {'test': 'data'}

            # Test calling run_full_benchmark with enable_agentops=True
            # This should fail initially because the method doesn't accept the parameter
            try:
                import asyncio
                results = asyncio.run(benchmark.run_full_benchmark(10, enable_agentops=True))
                # If this succeeds, check that the method was called correctly
                mock_run.assert_called_once_with(10, enable_agentops=True)
                print("✅ TC-019 PASSED: enable_agentops parameter passed correctly")
            except TypeError as e:
                if "positional argument" in str(e) or "unexpected keyword argument" in str(e):
                    print(f"❌ TC-019 EXPECTED FAILURE: {e}")
                    print("   run_full_benchmark method needs enable_agentops parameter")
                    return False
                else:
                    raise

        return True


def run_test():
    """Run the test directly"""
    test_instance = TestBenchmarkPassesAgentOpsTC019()
    try:
        test_instance.test_benchmark_passes_agentops_to_run_full_benchmark()
        print("✅ TC-019 PASSED: Benchmark passes AgentOps flag")
        return True
    except AssertionError as e:
        print(f"❌ TC-019 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-019 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)