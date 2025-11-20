#!/usr/bin/env python3
"""
Report Generation Utilities

Generates console and JSON reports for integration testing results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .metrics import TestRunMetrics


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_cost(cost: float) -> str:
    """Format cost in dollars."""
    return f"${cost:.4f}"


def format_percentage(value: float) -> str:
    """Format percentage value."""
    return f"{value:.1f}%"


def generate_console_report(metrics: TestRunMetrics) -> str:
    """
    Generate console report from metrics.

    Args:
        metrics: Test run metrics

    Returns:
        Formatted console report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"{metrics.test_name.upper()} - TEST RESULTS")
    lines.append("=" * 80)
    lines.append("")

    # Test overview
    lines.append("TEST OVERVIEW")
    lines.append("-" * 80)
    lines.append(f"Start Time: {metrics.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if metrics.end_time:
        lines.append(f"End Time: {metrics.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Total Duration: {format_duration(metrics.total_time)}")
    lines.append("")

    # Submission results
    lines.append("SUBMISSION RESULTS")
    lines.append("-" * 80)
    lines.append(f"Total Submissions: {metrics.submissions_total}")
    lines.append(f"Successful: {metrics.submissions_success} ({format_percentage(metrics.success_rate)})")
    lines.append(f"Partial: {metrics.submissions_partial}")
    lines.append(f"Failed: {metrics.submissions_failed}")
    lines.append("")

    # Performance metrics
    lines.append("PERFORMANCE METRICS")
    lines.append("-" * 80)
    lines.append(f"Avg Time per Submission: {format_duration(metrics.avg_time_per_submission)}")
    lines.append(f"Throughput: {metrics.throughput:.2f} submissions/minute")
    if metrics.peak_memory_mb > 0:
        lines.append(f"Peak Memory Usage: {metrics.peak_memory_mb:.1f} MB")
    lines.append("")

    # Cost metrics
    lines.append("COST ANALYSIS")
    lines.append("-" * 80)
    lines.append(f"Total Cost: {format_cost(metrics.total_cost)}")
    lines.append(f"Avg Cost per Submission: {format_cost(metrics.avg_cost_per_submission)}")
    lines.append("")
    lines.append("Cost by Service:")
    for service_name, cost in sorted(metrics.cost_by_service.items()):
        lines.append(f"  - {service_name}: {format_cost(cost)}")
    lines.append("")

    # Field coverage
    lines.append("FIELD COVERAGE")
    lines.append("-" * 80)
    lines.append(f"Average Field Coverage: {format_percentage(metrics.avg_field_coverage)}")
    lines.append("")
    lines.append("Field Population Rates (top 10):")
    sorted_fields = sorted(metrics.fields_coverage_detail.items(), key=lambda x: x[1], reverse=True)
    for field_name, coverage in sorted_fields[:10]:
        lines.append(f"  - {field_name}: {format_percentage(coverage)}")
    lines.append("")

    # Service statistics
    lines.append("SERVICE STATISTICS")
    lines.append("-" * 80)
    for service_name in sorted(metrics.service_success_rates.keys()):
        success_rate = metrics.service_success_rates.get(service_name, 0)
        avg_time = metrics.service_avg_times.get(service_name, 0)
        cost = metrics.cost_by_service.get(service_name, 0)
        lines.append(f"{service_name}:")
        lines.append(f"  Success Rate: {format_percentage(success_rate)}")
        lines.append(f"  Avg Time: {format_duration(avg_time)}")
        lines.append(f"  Total Cost: {format_cost(cost)}")
    lines.append("")

    # Success criteria check
    lines.append("SUCCESS CRITERIA")
    lines.append("-" * 80)
    lines.append(f"✓ All submissions processed: {metrics.submissions_total > 0}")
    lines.append(f"{'✓' if metrics.success_rate >= 100 else '✗'} Success rate >= 100%: {format_percentage(metrics.success_rate)}")
    lines.append(f"{'✓' if metrics.avg_field_coverage >= 90 else '✗'} Field coverage >= 90%: {format_percentage(metrics.avg_field_coverage)}")
    lines.append(f"{'✓' if metrics.avg_cost_per_submission <= 0.20 else '✗'} Cost per submission <= $0.20: {format_cost(metrics.avg_cost_per_submission)}")
    lines.append("")

    # Overall status
    overall_success = (
        metrics.submissions_total > 0
        and metrics.success_rate >= 100
        and metrics.avg_field_coverage >= 90
        and metrics.avg_cost_per_submission <= 0.20
    )

    lines.append("=" * 80)
    if overall_success:
        lines.append("✅ TEST PASSED - All success criteria met")
    else:
        lines.append("❌ TEST FAILED - Some success criteria not met")
    lines.append("=" * 80)

    return "\n".join(lines)


def save_json_report(metrics: TestRunMetrics, output_path: Path):
    """
    Save metrics as JSON report.

    Args:
        metrics: Test run metrics
        output_path: Path to save JSON report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = metrics.to_dict()

    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=2)


def load_json_report(report_path: Path) -> Dict[str, Any]:
    """
    Load JSON report from file.

    Args:
        report_path: Path to JSON report

    Returns:
        Report data dictionary
    """
    with open(report_path, "r") as f:
        return json.load(f)


def generate_comparison_report(unified_metrics: TestRunMetrics, monolith_metrics: TestRunMetrics) -> str:
    """
    Generate comparison report between unified and monolith pipelines.

    Args:
        unified_metrics: Metrics from unified pipeline
        monolith_metrics: Metrics from monolith pipeline

    Returns:
        Formatted comparison report
    """
    lines = []
    lines.append("=" * 80)
    lines.append("UNIFIED VS MONOLITH COMPARISON REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Processing results
    lines.append("PROCESSING RESULTS")
    lines.append("-" * 80)
    lines.append(f"{'Metric':<40} {'Monolith':<15} {'Unified':<15} {'Diff':<10}")
    lines.append("-" * 80)

    # Submissions processed
    lines.append(f"{'Submissions Processed':<40} {monolith_metrics.submissions_success:<15} {unified_metrics.submissions_success:<15}")

    # Success rate
    monolith_success = monolith_metrics.success_rate
    unified_success = unified_metrics.success_rate
    success_diff = unified_success - monolith_success
    lines.append(f"{'Success Rate':<40} {format_percentage(monolith_success):<15} {format_percentage(unified_success):<15} {success_diff:+.1f}%")

    # Performance comparison
    lines.append("")
    lines.append("PERFORMANCE COMPARISON")
    lines.append("-" * 80)

    monolith_time = monolith_metrics.avg_time_per_submission
    unified_time = unified_metrics.avg_time_per_submission
    time_diff_pct = ((unified_time - monolith_time) / monolith_time * 100) if monolith_time > 0 else 0
    lines.append(f"{'Avg Time per Submission':<40} {format_duration(monolith_time):<15} {format_duration(unified_time):<15} {time_diff_pct:+.1f}%")

    monolith_throughput = monolith_metrics.throughput
    unified_throughput = unified_metrics.throughput
    throughput_diff_pct = ((unified_throughput - monolith_throughput) / monolith_throughput * 100) if monolith_throughput > 0 else 0
    lines.append(f"{'Throughput (sub/min)':<40} {monolith_throughput:<15.2f} {unified_throughput:<15.2f} {throughput_diff_pct:+.1f}%")

    # Cost comparison
    lines.append("")
    lines.append("COST COMPARISON")
    lines.append("-" * 80)

    monolith_cost = monolith_metrics.avg_cost_per_submission
    unified_cost = unified_metrics.avg_cost_per_submission
    cost_diff_pct = ((unified_cost - monolith_cost) / monolith_cost * 100) if monolith_cost > 0 else 0
    lines.append(f"{'Avg Cost per Submission':<40} {format_cost(monolith_cost):<15} {format_cost(unified_cost):<15} {cost_diff_pct:+.1f}%")

    # Success criteria
    lines.append("")
    lines.append("EQUIVALENCE CRITERIA")
    lines.append("-" * 80)

    performance_acceptable = abs(time_diff_pct) <= 20  # Within 20%
    cost_acceptable = abs(cost_diff_pct) <= 10  # Within 10%

    lines.append(f"{'Performance within 20%':<40} {('✓ YES' if performance_acceptable else '✗ NO'):<15} ({time_diff_pct:+.1f}%)")
    lines.append(f"{'Cost within 10%':<40} {('✓ YES' if cost_acceptable else '✗ NO'):<15} ({cost_diff_pct:+.1f}%)")

    lines.append("")
    lines.append("=" * 80)
    if performance_acceptable and cost_acceptable:
        lines.append("✅ EQUIVALENCE VALIDATED - Unified pipeline matches monolith")
    else:
        lines.append("⚠️  REVIEW REQUIRED - Performance or cost differences exceed tolerance")
    lines.append("=" * 80)

    return "\n".join(lines)
