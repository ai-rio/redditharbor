#!/usr/bin/env python3
"""
Phase 5 Test Runner for Agno Integration

Comprehensive test execution for production validation
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Phase5TestRunner:
    """Runner for Phase 5 comprehensive test suite"""

    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        self.reports_dir = project_root / "test_reports" / "phase5"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_all_tests(self) -> dict[str, Any]:
        """
        Run all Phase 5 tests and generate comprehensive report

        Returns:
            Dictionary with all test results and summary
        """
        print("=" * 80)
        print("Phase 5: Agno Integration Production Testing")
        print("=" * 80)
        print(f"Started at: {self.start_time.isoformat()}")
        print()

        # Define test suites
        test_suites = [
            {
                "name": "A/B Comparison Tests",
                "module": "tests.integration.test_agno_ab_comparison",
                "description": "Validate quality improvements vs LiteLLM baseline",
                "critical": True
            },
            {
                "name": "Performance Benchmarks",
                "module": "tests.integration.test_agno_benchmarks",
                "description": "Validate latency, throughput, and cost targets",
                "critical": True
            },
            {
                "name": "Failure Recovery Tests",
                "module": "tests.integration.test_agno_failure_recovery",
                "description": "Validate graceful degradation and error handling",
                "critical": True
            }
        ]

        # Run each test suite
        for suite in test_suites:
            print(f"\n{'-' * 60}")
            print(f"Running: {suite['name']}")
            print(f"Description: {suite['description']}")
            print(f"Critical: {'Yes' if suite['critical'] else 'No'}")
            print(f"{'-' * 60}")

            result = self._run_test_suite(suite)
            self.test_results[suite['name']] = result

            # Print immediate results
            self._print_suite_results(suite['name'], result)

            # If critical test failed, ask whether to continue
            if suite['critical'] and not result['passed']:
                print(f"\n⚠️  CRITICAL TEST FAILED: {suite['name']}")
                response = input("Continue with remaining tests? (y/N): ")
                if response.lower() != 'y':
                    print("\nStopping test execution due to critical failure.")
                    break

        # Generate comprehensive report
        report = self._generate_comprehensive_report()
        self._save_report(report)

        # Print final summary
        self._print_final_summary(report)

        return report

    def _run_test_suite(self, suite: dict[str, Any]) -> dict[str, Any]:
        """
        Run a single test suite

        Args:
            suite: Test suite configuration

        Returns:
            Dictionary with test results
        """
        suite_start_time = time.time()

        # Prepare pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            suite['module'],
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={self.reports_dir / f'{suite['name'].lower().replace(' ', '_')}_report.json'}"
        ]

        # Run pytest
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )

            # Parse results
            suite_result = {
                "passed": result.returncode == 0,
                "duration": time.time() - suite_start_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "test_file": suite['module']
            }

            # Try to load JSON report for detailed results
            json_file = self.reports_dir / f"{suite['name'].lower().replace(' ', '_')}_report.json"
            if json_file.exists():
                with open(json_file) as f:
                    json_report = json.load(f)
                    suite_result["summary"] = json_report.get("summary", {})
                    suite_result["tests"] = json_report.get("tests", [])
            else:
                suite_result["summary"] = {}
                suite_result["tests"] = []

            return suite_result

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "duration": time.time() - suite_start_time,
                "stdout": "",
                "stderr": "Test execution timed out after 30 minutes",
                "returncode": -1,
                "test_file": suite['module'],
                "summary": {},
                "tests": []
            }

        except Exception as e:
            return {
                "passed": False,
                "duration": time.time() - suite_start_time,
                "stdout": "",
                "stderr": str(e),
                "returncode": -2,
                "test_file": suite['module'],
                "summary": {},
                "tests": []
            }

    def _print_suite_results(self, suite_name: str, result: dict[str, Any]):
        """Print results for a test suite"""
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"\n{status} - {suite_name}")
        print(f"Duration: {result['duration']:.1f}s")

        if 'summary' in result and result['summary']:
            summary = result['summary']
            if 'passed' in summary and 'failed' in summary and 'total' in summary:
                print(f"Tests: {summary['passed']} passed, {summary['failed']} failed, {summary['total']} total")

        if not result['passed'] and result['stderr']:
            print(f"Error: {result['stderr'][:200]}...")

    def _generate_comprehensive_report(self) -> dict[str, Any]:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        # Calculate overall statistics
        total_suites = len(self.test_results)
        passed_suites = sum(1 for r in self.test_results.values() if r['passed'])
        critical_suites = sum(
            1 for suite, result in self.test_results.items()
            if result['passed'] or not any(s['name'] == suite and s['critical'] for s in [
                {"name": "A/B Comparison Tests", "critical": True},
                {"name": "Performance Benchmarks", "critical": True},
                {"name": "Failure Recovery Tests", "critical": True}
            ])
        )

        # Collect detailed metrics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        all_test_files = []

        for suite_name, result in self.test_results.items():
            if 'summary' in result and result['summary']:
                summary = result['summary']
                total_tests += summary.get('total', 0)
                total_passed += summary.get('passed', 0)
                total_failed += summary.get('failed', 0)

            if 'tests' in result:
                for test in result['tests']:
                    all_test_files.append({
                        "suite": suite_name,
                        "name": test.get('name', 'Unknown'),
                        "outcome": test.get('outcome', 'unknown')
                    })

        # Generate success criteria validation
        success_criteria = self._validate_success_criteria()

        return {
            "test_execution": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": total_duration,
                "duration_formatted": f"{total_duration//60:.0f}m {total_duration%60:.0f}s"
            },
            "summary": {
                "total_suites": total_suites,
                "passed_suites": passed_suites,
                "failed_suites": total_suites - passed_suites,
                "critical_suites_passed": critical_suites,
                "success_rate": passed_suites / total_suites if total_suites > 0 else 0
            },
            "test_metrics": {
                "total_tests": total_tests,
                "passed_tests": total_passed,
                "failed_tests": total_failed,
                "test_success_rate": total_passed / total_tests if total_tests > 0 else 0
            },
            "suite_results": self.test_results,
            "all_tests": all_test_files,
            "success_criteria": success_criteria,
            "phase5_validation": {
                "ready_for_production": passed_suites == total_suites and success_criteria['all_met'],
                "critical_issues": self._identify_critical_issues(),
                "recommendations": self._generate_recommendations()
            }
        }

    def _validate_success_criteria(self) -> dict[str, Any]:
        """Validate Phase 5 success criteria"""
        criteria = {
            "quality_improvement_85_percent": self._check_quality_improvement(),
            "false_positive_reduction_60_percent": self._check_false_positive_reduction(),
            "p95_latency_under_5s": self._check_latency_target(),
            "cost_per_analysis_under_0_005": self._check_cost_target(),
            "throughput_over_100_per_hour": self._check_throughput_target(),
            "failure_recovery_rate_80_percent": self._check_failure_recovery()
        }

        criteria_met = sum(1 for passed in criteria.values() if passed)
        criteria['all_met'] = criteria_met == len(criteria)
        criteria['met_count'] = criteria_met
        criteria['total_count'] = len(criteria)

        return criteria

    def _check_quality_improvement(self) -> bool:
        """Check if 85% quality improvement target met"""
        # This would parse the A/B test report
        ab_report_file = self.reports_dir / "a/b_comparison_tests_report.json"
        if ab_report_file.exists():
            try:
                with open(ab_report_file) as f:
                    report = json.load(f)
                    # Check if report shows 85% improvement
                    quality_metrics = report.get('quality_metrics', {})
                    improvement = quality_metrics.get('viability_improvement', 0)
                    return improvement >= 0.85
            except:
                pass
        return False

    def _check_false_positive_reduction(self) -> bool:
        """Check if 60% false positive reduction target met"""
        # Similar to quality improvement check
        ab_report_file = self.reports_dir / "a/b_comparison_tests_report.json"
        if ab_report_file.exists():
            try:
                with open(ab_report_file) as f:
                    report = json.load(f)
                    quality_metrics = report.get('quality_metrics', {})
                    reduction = quality_metrics.get('false_positive_reduction', 0)
                    return reduction >= 0.60
            except:
                pass
        return False

    def _check_latency_target(self) -> bool:
        """Check if P95 latency under 5s target met"""
        benchmark_file = self.reports_dir / "performance_benchmarks_report.json"
        if benchmark_file.exists():
            try:
                with open(benchmark_file) as f:
                    report = json.load(f)
                    test_results = report.get('test_results', {})
                    single_latency = test_results.get('single_latency', {})
                    p95_latency = single_latency.get('p95', float('inf'))
                    return p95_latency <= 5.0
            except:
                pass
        return False

    def _check_cost_target(self) -> bool:
        """Check if cost per analysis under $0.005 target met"""
        benchmark_file = self.reports_dir / "performance_benchmarks_report.json"
        if benchmark_file.exists():
            try:
                with open(benchmark_file) as f:
                    report = json.load(f)
                    test_results = report.get('test_results', {})
                    cost_validation = test_results.get('cost_validation', {})
                    avg_cost = cost_validation.get('avg_cost', float('inf'))
                    return avg_cost <= 0.005
            except:
                pass
        return False

    def _check_throughput_target(self) -> bool:
        """Check if throughput >100/hour target met"""
        benchmark_file = self.reports_dir / "performance_benchmarks_report.json"
        if benchmark_file.exists():
            try:
                with open(benchmark_file) as f:
                    report = json.load(f)
                    test_results = report.get('test_results', {})
                    throughput = test_results.get('throughput', {})
                    throughput_rate = throughput.get('throughput_per_hour', 0)
                    return throughput_rate >= 100
            except:
                pass
        return False

    def _check_failure_recovery(self) -> bool:
        """Check if 80% failure recovery rate met"""
        recovery_file = self.reports_dir / "failure_recovery_tests_report.json"
        if recovery_file.exists():
            try:
                with open(recovery_file) as f:
                    report = json.load(f)
                    summary = report.get('summary', {})
                    recovery_rate = summary.get('recovery_rate', 0)
                    return recovery_rate >= 0.80
            except:
                pass
        return False

    def _identify_critical_issues(self) -> list[str]:
        """Identify critical issues preventing production deployment"""
        issues = []

        # Check for failed test suites
        for suite_name, result in self.test_results.items():
            if not result['passed']:
                issues.append(f"Test suite failed: {suite_name}")

        # Check success criteria
        criteria = self._validate_success_criteria()
        if not criteria['all_met']:
            for criterion, passed in criteria.items():
                if criterion != 'all_met' and not passed:
                    issues.append(f"Success criterion not met: {criterion}")

        return issues

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Analyze test results
        for suite_name, result in self.test_results.items():
            if not result['passed']:
                if "A/B" in suite_name:
                    recommendations.append("Review agent prompts and consensus logic for quality improvements")
                elif "Performance" in suite_name:
                    recommendations.append("Optimize agent orchestration for better performance")
                elif "Failure" in suite_name:
                    recommendations.append("Enhance error handling and fallback mechanisms")

        # Check specific criteria
        criteria = self._validate_success_criteria()
        if not criteria['p95_latency_under_5s']:
            recommendations.append("Implement parallel agent execution to reduce latency")
        if not criteria['throughput_over_100_per_hour']:
            recommendations.append("Optimize batch processing for higher throughput")
        if not criteria['cost_per_analysis_under_0_005']:
            recommendations.append("Reduce prompt sizes or use cheaper models where appropriate")

        if not recommendations:
            recommendations.append("All tests passed - ready for production deployment!")

        return recommendations

    def _save_report(self, report: dict[str, Any]):
        """Save comprehensive report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"phase5_comprehensive_report_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Also save latest report
        latest_file = self.reports_dir / "phase5_latest_report.json"
        with open(latest_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Report saved to: {report_file}")

    def _print_final_summary(self, report: dict[str, Any]):
        """Print final test execution summary"""
        print("\n" + "=" * 80)
        print("PHASE 5 TEST EXECUTION SUMMARY")
        print("=" * 80)

        # Overall results
        summary = report['summary']
        print("\n📊 OVERALL RESULTS:")
        print(f"  Test Suites: {summary['passed_suites']}/{summary['total_suites']} passed")
        print(f"  Success Rate: {summary['success_rate']:.1%}")
        print(f"  Critical Suites: {summary['critical_suites_passed']}/{summary['total_suites']} passed")

        # Success criteria
        criteria = report['success_criteria']
        print("\n✅ SUCCESS CRITERIA:")
        print(f"  Met: {criteria['met_count']}/{criteria['total_count']}")
        for criterion, passed in criteria.items():
            if criterion not in ['all_met', 'met_count', 'total_count']:
                status = "✓" if passed else "✗"
                print(f"  {status} {criterion.replace('_', ' ').title()}")

        # Production readiness
        validation = report['phase5_validation']
        print("\n🚀 PRODUCTION READINESS:")
        print(f"  Ready for Production: {'YES' if validation['ready_for_production'] else 'NO'}")

        if validation['critical_issues']:
            print("\n⚠️  CRITICAL ISSUES:")
            for issue in validation['critical_issues']:
                print(f"  - {issue}")

        if validation['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in validation['recommendations']:
                print(f"  - {rec}")

        print(f"\n⏱️  Total Execution Time: {report['test_execution']['duration_formatted']}")
        print("=" * 80)


def main():
    """Main entry point"""
    # Check if we're in the right directory
    if not Path("pipeline-v3").exists():
        print("Error: Must run from project root directory")
        sys.exit(1)

    # Install required dependencies if needed
    print("Checking dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "pytest-json-report",
        "pytest"
    ], capture_output=True)

    # Run tests
    runner = Phase5TestRunner()
    report = runner.run_all_tests()

    # Exit with appropriate code
    if report['phase5_validation']['ready_for_production']:
        print("\n✅ Phase 5 testing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Phase 5 testing failed - review issues before production deployment")
        sys.exit(1)


if __name__ == "__main__":
    main()
