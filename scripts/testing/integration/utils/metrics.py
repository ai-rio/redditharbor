#!/usr/bin/env python3
"""
Metrics Collection Utilities

Collects and tracks metrics for integration testing:
- Processing time per submission
- Success/failure rates
- Cost per service
- Field coverage
- Memory usage
"""

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class ServiceMetrics:
    """Metrics for a single service execution."""
    service_name: str
    success: bool
    processing_time: float
    cost: float = 0.0
    tokens: int = 0
    error: Optional[str] = None
    fields_populated: List[str] = field(default_factory=list)


@dataclass
class SubmissionMetrics:
    """Metrics for a single submission enrichment."""
    submission_id: str
    status: str  # success, partial, failed
    total_time: float
    total_cost: float
    services_executed: int
    services_succeeded: int
    services_failed: int
    fields_populated: List[str] = field(default_factory=list)
    field_coverage: float = 0.0  # Percentage of expected fields populated
    service_metrics: List[ServiceMetrics] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class TestRunMetrics:
    """Aggregate metrics for entire test run."""
    test_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_time: float = 0.0

    # Submission counts
    submissions_total: int = 0
    submissions_success: int = 0
    submissions_partial: int = 0
    submissions_failed: int = 0

    # Success rates
    success_rate: float = 0.0

    # Performance
    avg_time_per_submission: float = 0.0
    throughput: float = 0.0  # submissions/minute
    peak_memory_mb: float = 0.0

    # Costs
    total_cost: float = 0.0
    avg_cost_per_submission: float = 0.0
    cost_by_service: Dict[str, float] = field(default_factory=dict)

    # Field coverage
    avg_field_coverage: float = 0.0
    fields_coverage_detail: Dict[str, float] = field(default_factory=dict)

    # Service stats
    service_success_rates: Dict[str, float] = field(default_factory=dict)
    service_avg_times: Dict[str, float] = field(default_factory=dict)

    # Submission details
    submission_metrics: List[SubmissionMetrics] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime to ISO format
        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data


class MetricsCollector:
    """Collects and aggregates metrics during test execution."""

    def __init__(self, test_name: str):
        """Initialize metrics collector."""
        self.test_name = test_name
        self.start_time = datetime.now()
        self.submission_metrics: List[SubmissionMetrics] = []
        self.service_timings: Dict[str, List[float]] = {}
        self.service_costs: Dict[str, List[float]] = {}
        self.service_success_counts: Dict[str, int] = {}
        self.service_failure_counts: Dict[str, int] = {}

    def record_submission(self, metrics: SubmissionMetrics):
        """Record metrics for a completed submission."""
        self.submission_metrics.append(metrics)

        # Aggregate service metrics
        for service_metric in metrics.service_metrics:
            service_name = service_metric.service_name

            # Track timings
            if service_name not in self.service_timings:
                self.service_timings[service_name] = []
            self.service_timings[service_name].append(service_metric.processing_time)

            # Track costs
            if service_name not in self.service_costs:
                self.service_costs[service_name] = []
            self.service_costs[service_name].append(service_metric.cost)

            # Track success/failure
            if service_name not in self.service_success_counts:
                self.service_success_counts[service_name] = 0
                self.service_failure_counts[service_name] = 0

            if service_metric.success:
                self.service_success_counts[service_name] += 1
            else:
                self.service_failure_counts[service_name] += 1

    def generate_report(self) -> TestRunMetrics:
        """Generate aggregate metrics report."""
        end_time = datetime.now()
        total_time = (end_time - self.start_time).total_seconds()

        # Count submission outcomes
        submissions_total = len(self.submission_metrics)
        submissions_success = sum(1 for m in self.submission_metrics if m.status == "success")
        submissions_partial = sum(1 for m in self.submission_metrics if m.status == "partial")
        submissions_failed = sum(1 for m in self.submission_metrics if m.status == "failed")

        # Calculate success rate
        success_rate = (submissions_success / submissions_total * 100) if submissions_total > 0 else 0.0

        # Calculate performance metrics
        avg_time = sum(m.total_time for m in self.submission_metrics) / submissions_total if submissions_total > 0 else 0.0
        throughput = (submissions_total / total_time * 60) if total_time > 0 else 0.0

        # Calculate cost metrics
        total_cost = sum(m.total_cost for m in self.submission_metrics)
        avg_cost = total_cost / submissions_total if submissions_total > 0 else 0.0

        # Calculate cost by service
        cost_by_service = {}
        for service_name, costs in self.service_costs.items():
            cost_by_service[service_name] = sum(costs)

        # Calculate field coverage
        avg_field_coverage = sum(m.field_coverage for m in self.submission_metrics) / submissions_total if submissions_total > 0 else 0.0

        # Calculate field coverage detail (which fields are populated most often)
        field_counts: Dict[str, int] = {}
        for metrics in self.submission_metrics:
            for field_name in metrics.fields_populated:
                field_counts[field_name] = field_counts.get(field_name, 0) + 1

        fields_coverage_detail = {
            field: (count / submissions_total * 100) if submissions_total > 0 else 0.0
            for field, count in field_counts.items()
        }

        # Calculate service success rates
        service_success_rates = {}
        for service_name in self.service_success_counts:
            total = self.service_success_counts[service_name] + self.service_failure_counts.get(service_name, 0)
            success_rate_service = (self.service_success_counts[service_name] / total * 100) if total > 0 else 0.0
            service_success_rates[service_name] = success_rate_service

        # Calculate service average times
        service_avg_times = {
            service_name: sum(timings) / len(timings) if timings else 0.0
            for service_name, timings in self.service_timings.items()
        }

        return TestRunMetrics(
            test_name=self.test_name,
            start_time=self.start_time,
            end_time=end_time,
            total_time=total_time,
            submissions_total=submissions_total,
            submissions_success=submissions_success,
            submissions_partial=submissions_partial,
            submissions_failed=submissions_failed,
            success_rate=success_rate,
            avg_time_per_submission=avg_time,
            throughput=throughput,
            total_cost=total_cost,
            avg_cost_per_submission=avg_cost,
            cost_by_service=cost_by_service,
            avg_field_coverage=avg_field_coverage,
            fields_coverage_detail=fields_coverage_detail,
            service_success_rates=service_success_rates,
            service_avg_times=service_avg_times,
            submission_metrics=self.submission_metrics,
        )


# Expected enrichment fields for coverage calculation
EXPECTED_ENRICHMENT_FIELDS = [
    # Opportunity analysis
    "opportunity_score",
    "final_score",
    "dimension_scores",
    "priority",
    "core_functions",
    "problem_description",
    "target_market",

    # Profiler
    "profession",
    "ai_profile",
    "evidence_based",
    "confidence",

    # Monetization
    "monetization_score",
    "monetization_methods",
    "willingness_to_pay_score",
    "customer_segment",
    "price_sensitivity_score",
    "revenue_potential_score",

    # Trust
    "trust_level",
    "overall_trust_score",
    "trust_badges",
    "activity_validation_score",
    "problem_authenticity_score",
    "solution_readiness_score",

    # Market validation
    "market_validation_score",
    "market_data_quality",
    "competitor_count",
    "market_size_estimate",
    "similar_launches_count",
    "validation_reasoning",
]


def calculate_field_coverage(enriched_submission: Dict[str, Any]) -> tuple[float, List[str]]:
    """
    Calculate field coverage percentage.

    Args:
        enriched_submission: Enriched submission dictionary

    Returns:
        Tuple of (coverage_percentage, list_of_populated_fields)
    """
    populated_fields = []

    for field in EXPECTED_ENRICHMENT_FIELDS:
        value = enriched_submission.get(field)
        # Check if field is populated (not None, not empty string, not empty list)
        if value is not None and value != "" and value != []:
            populated_fields.append(field)

    coverage = (len(populated_fields) / len(EXPECTED_ENRICHMENT_FIELDS) * 100) if EXPECTED_ENRICHMENT_FIELDS else 0.0

    return coverage, populated_fields
