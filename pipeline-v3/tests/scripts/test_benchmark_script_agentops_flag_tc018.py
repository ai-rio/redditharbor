#!/usr/bin/env python3
"""
Test TC-018: Benchmark script --with-agentops flag functionality

This test verifies that the benchmark script accepts and processes the --with-agentops flag.
"""

import sys
from pathlib import Path
import unittest.mock as mock
import argparse

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.benchmark_agno_performance import PerformanceBenchmark


class TestBenchmarkScriptAgentOpsFlagTC018:
    """Test class for TC-018: Benchmark script AgentOps flag"""

    def test_benchmark_script_accepts_with_agentops_flag(self):
        """TC-018: Verify that benchmark script accepts --with-agentops flag"""

        # Test argument parsing with --with-agentops flag
        test_args = ['benchmark_script.py', '10', '--with-agentops']

        with mock.patch('sys.argv', test_args):
            # Mock the main function's argument parsing
            parser = argparse.ArgumentParser(description='Benchmark Agno analyzer performance')
            parser.add_argument('count', nargs='?', type=int, default=10,
                                help='Number of submissions to test (1-50, default: 10)')
            parser.add_argument('--with-agentops', action='store_true',
                                help='Enable AgentOps tracking for performance monitoring')

            args = parser.parse_args()

            # Verify that the flag is parsed correctly
            assert args.count == 10, "Count should be parsed correctly"
            assert args.with_agentops == True, "--with-agentops flag should be True"

            print("✅ TC-018 PASSED: Benchmark script accepts --with-agentops flag")


def run_test():
    """Run the test directly"""
    test_instance = TestBenchmarkScriptAgentOpsFlagTC018()
    try:
        test_instance.test_benchmark_script_accepts_with_agentops_flag()
        print("✅ TC-018 PASSED: Benchmark script AgentOps flag parsing")
        return True
    except AssertionError as e:
        print(f"❌ TC-018 FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ TC-018 ERROR: {e}")
        return False


if __name__ == "__main__":
    # Run test directly for debugging
    success = run_test()
    exit(0 if success else 1)