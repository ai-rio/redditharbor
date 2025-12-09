#!/usr/bin/env python3
"""
Comprehensive test runner for pipeline quality filtering and performance tests
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_command(cmd, description="", timeout=300):
    """Run a command and return the result"""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}")

    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent.parent
        )
        end_time = time.time()
        duration = end_time - start_time

        print(f"Duration: {duration:.2f} seconds")
        print(f"Return code: {result.returncode}")

        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")

        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        return result.returncode == 0, duration

    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout} seconds")
        return False, timeout

    except Exception as e:
        print(f"Error running command: {e}")
        return False, 0

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Comprehensive test runner for pipeline tests")
    parser.add_argument("--quality-filtering", action="store_true", help="Run only quality filtering tests")
    parser.add_argument("--performance", action="store_true", help="Run only performance tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--fast", action="store_true", help="Run only fast tests (skip performance and slow tests)")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel", default=1)
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--file", help="Run specific test file")

    args = parser.parse_args()

    # Build pytest command
    pytest_cmd = ["python", "-m", "pytest"]

    # Add verbose flag
    if args.verbose:
        pytest_cmd.append("-v")

    # Add parallel execution
    if args.parallel > 1:
        pytest_cmd.extend(["-n", str(args.parallel)])

    # Add coverage if requested
    if args.coverage:
        pytest_cmd.extend([
            "--cov=orchestration",
            "--cov=models",
            "--cov=transform",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])

    # Determine test selection
    test_selection = []

    if args.file:
        # Run specific file
        test_selection.append(args.file)
    elif args.quality_filtering:
        test_selection.extend([
            "test_pipeline_orchestrator_quality_filtering.py",
            "test_analysis_quality_scoring.py"
        ])
        pytest_cmd.extend(["-m", "quality_filtering"])
    elif args.performance:
        test_selection.extend([
            "test_pipeline_performance.py"
        ])
        pytest_cmd.extend(["-m", "performance"])
    elif args.integration:
        pytest_cmd.extend(["-m", "integration"])
    elif args.fast:
        pytest_cmd.extend(["-m", "not slow and not performance"])
    elif args.pattern:
        pytest_cmd.extend(["-k", args.pattern])
    else:
        # Run all tests
        test_selection = ["tests/"]

    # Add test selection to command
    if test_selection:
        pytest_cmd.extend(test_selection)

    # Add additional pytest options
    pytest_cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])

    # Print test configuration
    print("Test Runner Configuration")
    print("=" * 50)
    print(f"Test selection: {test_selection if test_selection else 'All tests'}")
    print(f"Parallel workers: {args.parallel}")
    print(f"Coverage: {args.coverage}")
    print(f"Verbose: {args.verbose}")
    print(f"Pattern: {args.pattern if args.pattern else 'None'}")
    print(f"Fast only: {args.fast}")
    print("=" * 50)

    # Run the tests
    success, duration = run_command(
        pytest_cmd,
        description="Running pytest tests",
        timeout=1800  # 30 minutes timeout
    )

    if success:
        print(f"\n{'='*80}")
        print("✓ ALL TESTS PASSED!")
        print(f"Total duration: {duration:.2f} seconds")
        print(f"{'='*80}")
        return 0
    else:
        print(f"\n{'='*80}")
        print("✗ SOME TESTS FAILED!")
        print(f"Total duration: {duration:.2f} seconds")
        print(f"{'='*80}")
        return 1

def run_specific_test_suites():
    """Run specific test suites with detailed reporting"""
    test_suites = [
        {
            "name": "Quality Filtering Tests",
            "files": ["test_pipeline_orchestrator_quality_filtering.py"],
            "markers": ["quality_filtering"],
            "description": "Tests for quality filtering functionality"
        },
        {
            "name": "Analysis Quality Scoring Tests",
            "files": ["test_analysis_quality_scoring.py"],
            "markers": ["quality_filtering"],
            "description": "Tests for analysis result quality scoring"
        },
        {
            "name": "Performance Tests",
            "files": ["test_pipeline_performance.py"],
            "markers": ["performance"],
            "description": "Performance and load testing"
        },
        {
            "name": "Integration Tests",
            "files": [],
            "markers": ["integration"],
            "description": "End-to-end integration testing"
        }
    ]

    total_passed = 0
    total_failed = 0
    total_duration = 0

    for suite in test_suites:
        print(f"\n{'='*100}")
        print(f"Running Test Suite: {suite['name']}")
        print(f"Description: {suite['description']}")
        print(f"{'='*100}")

        # Build command for this suite
        cmd = ["python", "-m", "pytest", "-v"]

        if suite["files"]:
            cmd.extend(suite["files"])

        if suite["markers"]:
            cmd.extend(["-m", " or ".join(suite["markers"])])

        cmd.extend(["--tb=short", "--disable-warnings"])

        success, duration = run_command(cmd, description=suite["name"])
        total_duration += duration

        if success:
            total_passed += 1
            print(f"✓ {suite['name']} PASSED")
        else:
            total_failed += 1
            print(f"✗ {suite['name']} FAILED")

    print(f"\n{'='*100}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*100}")
    print(f"Total suites: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Total duration: {total_duration:.2f} seconds")

    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    # Check if we should run detailed test suites
    if "--suites" in sys.argv:
        sys.exit(run_specific_test_suites())
    else:
        sys.exit(main())
