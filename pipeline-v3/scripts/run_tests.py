#!/usr/bin/env python3
"""
Comprehensive test runner for AgnoOpportunityAnalyzer test suite
"""

import subprocess
import sys
import argparse
import os
from pathlib import Path
import json
from datetime import datetime


def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def run_unit_tests():
    """Run unit tests with coverage"""
    print("🧪 Running Unit Tests...")
    cmd = "python -m pytest tests/unit/ -v --cov=core/agents --cov-report=term-missing --cov-report=xml:coverage_unit.xml"
    return run_command(cmd)


def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running Integration Tests...")
    cmd = "python -m pytest tests/integration/ -v --cov=scripts/core --cov-report=term-missing --cov-report=xml:coverage_integration.xml"
    return run_command(cmd)


def run_performance_tests():
    """Run performance tests"""
    print("⚡ Running Performance Tests...")
    cmd = "python -m pytest tests/performance/ -v --benchmark-only --benchmark-sort=mean"
    return run_command(cmd)


def run_edge_case_tests():
    """Run edge case tests"""
    print("🔍 Running Edge Case Tests...")
    cmd = "python -m pytest tests/performance/test_edge_cases.py -v"
    return run_command(cmd)


def run_all_tests():
    """Run all tests"""
    print("🚀 Running All Tests...")
    print("=" * 50)

    # Track results
    results = {}
    total_tests = 0
    passed_tests = 0

    # Run unit tests
    print("\n1. Unit Tests")
    print("-" * 30)
    returncode, stdout, stderr = run_unit_tests()
    results['unit'] = {'returncode': returncode, 'stdout': stdout, 'stderr': stderr}
    total_tests += 1
    passed_tests += 1 if returncode == 0 else 0

    # Run integration tests
    print("\n2. Integration Tests")
    print("-" * 30)
    returncode, stdout, stderr = run_integration_tests()
    results['integration'] = {'returncode': returncode, 'stdout': stdout, 'stderr': stderr}
    total_tests += 1
    passed_tests += 1 if returncode == 0 else 0

    # Run performance tests
    print("\n3. Performance Tests")
    print("-" * 30)
    returncode, stdout, stderr = run_performance_tests()
    results['performance'] = {'returncode': returncode, 'stdout': stdout, 'stderr': stderr}
    total_tests += 1
    passed_tests += 1 if returncode == 0 else 0

    # Run edge case tests
    print("\n4. Edge Case Tests")
    print("-" * 30)
    returncode, stdout, stderr = run_edge_case_tests()
    results['edge_case'] = {'returncode': returncode, 'stdout': stdout, 'stderr': stderr}
    total_tests += 1
    passed_tests += 1 if returncode == 0 else 0

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    for test_type, result in results.items():
        status = "✅ PASSED" if result['returncode'] == 0 else "❌ FAILED"
        print(f"{test_type.upper():12} {status}")

        if result['returncode'] != 0:
            print(f"   Error: {result['stderr'].strip()}")

    print(f"\nTotal: {total_tests} test suites")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    # Generate test report
    generate_test_report(results)

    # Return overall success
    return passed_tests == total_tests


def generate_test_report(results):
    """Generate a comprehensive test report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.json"

    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {},
        'details': results
    }

    # Calculate summary
    total_suites = len(results)
    passed_suites = sum(1 for r in results.values() if r['returncode'] == 0)
    failed_suites = total_suites - passed_suites

    report['summary'] = {
        'total_test_suites': total_suites,
        'passed_test_suites': passed_suites,
        'failed_test_suites': failed_suites,
        'success_rate': (passed_suites / total_suites) * 100 if total_suites > 0 else 0
    }

    # Save report
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Test report saved to: {report_file}")


def run_specific_test(test_type):
    """Run a specific test type"""
    test_functions = {
        'unit': run_unit_tests,
        'integration': run_integration_tests,
        'performance': run_performance_tests,
        'edge_case': run_edge_case_tests,
        'all': run_all_tests
    }

    if test_type not in test_functions:
        print(f"❌ Unknown test type: {test_type}")
        print(f"Available types: {', '.join(test_functions.keys())}")
        return False

    returncode, stdout, stderr = test_functions[test_type]()

    if returncode == 0:
        print("✅ Tests passed!")
    else:
        print("❌ Tests failed!")
        print(f"Error: {stderr}")

    return returncode == 0


def main():
    parser = argparse.ArgumentParser(description='Run comprehensive test suite for AgnoOpportunityAnalyzer')
    parser.add_argument('test_type', nargs='?', default='all',
                        choices=['unit', 'integration', 'performance', 'edge_case', 'all'],
                        help='Type of tests to run (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Run tests with verbose output')
    parser.add_argument('--coverage', '-c', action='store_true',
                        help='Generate coverage report')

    args = parser.parse_args()

    # Change to the pipeline-v3 directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print("🏃 RedditHarbor AgnoOpportunityAnalyzer Test Suite")
    print(f"📁 Running tests in: {os.getcwd()}")
    print("=" * 60)

    success = run_specific_test(args.test_type)

    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()