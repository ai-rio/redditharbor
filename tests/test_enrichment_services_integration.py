"""Integration tests for enrichment services coordination.

This module tests how enrichment services work together in a coordinated pipeline,
validating that they can process submissions sequentially and maintain consistent
data flow between services.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock problematic dependencies before importing services
sys.modules['litellm'] = MagicMock()
sys.modules['agno'] = MagicMock()
sys.modules['json_repair'] = MagicMock()
sys.modules['agentops'] = MagicMock()
sys.modules['browser_use'] = MagicMock()

from core.enrichment.opportunity_service import OpportunityService
from core.enrichment.profiler_service import ProfilerService
from core.enrichment.monetization_service import MonetizationService
from core.enrichment.trust_service import TrustService


# ===========================
# Fixtures - Sample Data
# ===========================


@pytest.fixture
def sample_submission():
    """Sample submission for integration testing."""
    return {
        "submission_id": "integration_test_001",
        "title": "Need better project management tool for startups",
        "text": "Current tools like Asana and Monday are too complex and expensive. "
        "Looking for a simpler solution that focuses on core features. "
        "Would pay $20/month for something that just works.",
        "content": None,  # Some submissions use 'text', some use 'content'
        "subreddit": "startups",
        "upvotes": 250,
        "comments_count": 45,
        "num_comments": 45,  # Alternative field name
        "created_utc": 1700000000,
        "comments": [
            "I totally agree, existing solutions are overkill",
            "Would definitely pay for a simpler alternative",
            "This is a real pain point in our team",
        ],
    }


@pytest.fixture
def mock_opportunity_analyzer():
    """Mock OpportunityAnalyzerAgent."""
    analyzer = MagicMock()
    analyzer.analyze_opportunity.return_value = {
        "opportunity_id": "integration_test_001",
        "title": "Need better project management tool for startups",
        "subreddit": "startups",
        "dimension_scores": {
            "market_demand": 78.0,
            "pain_intensity": 85.0,
            "monetization_potential": 72.0,
            "market_gap": 68.0,
            "technical_feasibility": 82.0,
            "simplicity_score": 75.0,
        },
        "final_score": 76.5,
        "priority": "🔥 High Priority",
        "core_functions": ["Task management", "Team collaboration", "Progress tracking"],
        "function_count": 3,
        "timestamp": "2025-01-15T10:30:00",
        "analysis_summary": "Strong opportunity with clear pain point and monetization path",
    }
    return analyzer


@pytest.fixture
def mock_profiler():
    """Mock EnhancedLLMProfiler."""
    profiler = MagicMock()
    profiler.generate_profile.return_value = {
        "app_name": "SimpleProject",
        "tagline": "Streamlined project management for small teams",
        "core_functions": ["Task management", "Team collaboration", "Progress tracking"],
        "target_audience": "Startup founders and small teams (5-20 people)",
        "unique_value": "Simplicity and affordability vs complex enterprise tools",
        "evidence_based": True,
        "confidence_score": 0.85,
    }
    return profiler


@pytest.fixture
def mock_profiler_skip_logic():
    """Mock ProfilerSkipLogic."""
    skip_logic = MagicMock()
    skip_logic.should_run_profiler_analysis.return_value = (
        True,
        "No existing profile found",
    )
    skip_logic.update_concept_profiler_stats.return_value = True
    return skip_logic


@pytest.fixture
def mock_monetization_analyzer():
    """Mock MonetizationAgnoAnalyzer."""
    analyzer = MagicMock()
    analyzer.analyze.return_value = {
        "revenue_streams": [
            {"type": "subscription", "confidence": 0.9, "monthly_revenue": 20},
            {"type": "freemium", "confidence": 0.7, "conversion_rate": 0.05},
        ],
        "pricing_model": "tiered_subscription",
        "monetization_score": 78.0,
        "business_model": "SaaS",
        "market_size": "SMB project management",
        "competition_level": "high",
        "recommended_price_point": "$15-25/month",
    }
    return analyzer


@pytest.fixture
def mock_agno_skip_logic():
    """Mock AgnoSkipLogic."""
    skip_logic = MagicMock()
    skip_logic.should_run_agno_analysis.return_value = (
        True,
        "No existing monetization analysis",
    )
    skip_logic.update_concept_agno_stats.return_value = True
    return skip_logic


@pytest.fixture
def mock_trust_validator():
    """Mock TrustValidationService."""
    from dataclasses import dataclass
    from enum import Enum

    class TrustLevel(Enum):
        HIGH = "high"

    @dataclass
    class TrustIndicators:
        subreddit_activity_score: float = 80.0
        post_engagement_score: float = 85.0
        community_health_score: float = 75.0
        trend_velocity_score: float = 70.0
        problem_validity_score: float = 88.0
        discussion_quality_score: float = 82.0
        ai_analysis_confidence: float = 85.0
        overall_trust_score: float = 80.7
        trust_level: TrustLevel = TrustLevel.HIGH
        trust_badges: list = None
        activity_constraints_met: bool = True
        quality_constraints_met: bool = True
        validation_timestamp: str = "2025-01-15T10:30:00"
        validation_method: str = "comprehensive"

        def __post_init__(self):
            if self.trust_badges is None:
                self.trust_badges = ["high_engagement", "strong_community"]

    @dataclass
    class ValidationResult:
        success: bool
        indicators: TrustIndicators

    validator = MagicMock()
    result = ValidationResult(success=True, indicators=TrustIndicators())
    validator.validate_opportunity_trust.return_value = result

    return validator


# ===========================
# Integration Tests
# ===========================


def test_opportunity_service_integration(mock_opportunity_analyzer, sample_submission):
    """Test OpportunityService processes submission correctly."""
    service = OpportunityService(mock_opportunity_analyzer)

    result = service.enrich(sample_submission)

    assert result["opportunity_id"] == "integration_test_001"
    assert result["final_score"] == 76.5
    assert result["priority"] == "🔥 High Priority"
    assert len(result["core_functions"]) == 3
    assert result["function_count"] == 3
    assert service.stats["analyzed"] == 1
    assert service.stats["errors"] == 0


def test_profiler_service_integration(
    mock_profiler, mock_profiler_skip_logic, sample_submission
):
    """Test ProfilerService processes submission correctly."""
    service = ProfilerService(mock_profiler, mock_profiler_skip_logic)

    result = service.enrich(sample_submission)

    assert result["app_name"] == "SimpleProject"
    assert result["tagline"] == "Streamlined project management for small teams"
    assert len(result["core_functions"]) == 3
    assert result["evidence_based"] is True
    assert result["confidence_score"] == 0.85
    assert service.stats["analyzed"] == 1
    assert service.stats["errors"] == 0


def test_monetization_service_integration(
    mock_monetization_analyzer, mock_agno_skip_logic, sample_submission
):
    """Test MonetizationService processes submission correctly."""
    service = MonetizationService(
        mock_monetization_analyzer, mock_agno_skip_logic
    )

    result = service.enrich(sample_submission)

    assert result["monetization_score"] == 78.0
    assert result["pricing_model"] == "tiered_subscription"
    assert result["business_model"] == "SaaS"
    assert len(result["revenue_streams"]) == 2
    assert result["recommended_price_point"] == "$15-25/month"
    assert service.stats["analyzed"] == 1
    assert service.stats["errors"] == 0


def test_trust_service_integration(mock_trust_validator, sample_submission):
    """Test TrustService processes submission correctly."""
    service = TrustService(mock_trust_validator)

    result = service.enrich(sample_submission)

    assert result["overall_trust_score"] == 80.7
    assert result["trust_level"] == "high"
    assert result["subreddit_activity_score"] == 80.0
    assert result["post_engagement_score"] == 85.0
    assert result["activity_constraints_met"] is True
    assert service.stats["analyzed"] == 1
    assert service.stats["errors"] == 0


def test_full_pipeline_integration(
    mock_opportunity_analyzer,
    mock_profiler,
    mock_profiler_skip_logic,
    mock_monetization_analyzer,
    mock_agno_skip_logic,
    mock_trust_validator,
    sample_submission,
):
    """Test full pipeline with all services processing sequentially."""
    # Initialize all services
    opportunity_service = OpportunityService(mock_opportunity_analyzer)
    profiler_service = ProfilerService(mock_profiler, mock_profiler_skip_logic)
    monetization_service = MonetizationService(
        mock_monetization_analyzer, mock_agno_skip_logic
    )
    trust_service = TrustService(mock_trust_validator)

    # Simulate pipeline processing
    enriched_submission = sample_submission.copy()

    # Step 1: Opportunity Analysis
    opportunity_result = opportunity_service.enrich(enriched_submission)
    assert opportunity_result["final_score"] == 76.5
    enriched_submission["opportunity_analysis"] = opportunity_result

    # Step 2: AI Profiling (for high-scoring opportunities)
    if opportunity_result["final_score"] >= 60.0:
        profiler_result = profiler_service.enrich(enriched_submission)
        assert profiler_result["app_name"] == "SimpleProject"
        enriched_submission["ai_profile"] = profiler_result

    # Step 3: Monetization Analysis
    monetization_result = monetization_service.enrich(enriched_submission)
    assert monetization_result["monetization_score"] == 78.0
    enriched_submission["monetization_analysis"] = monetization_result

    # Step 4: Trust Validation
    trust_result = trust_service.enrich(enriched_submission)
    assert trust_result["overall_trust_score"] == 80.7
    enriched_submission["trust_validation"] = trust_result

    # Verify all services processed successfully
    assert opportunity_service.stats["analyzed"] == 1
    assert profiler_service.stats["analyzed"] == 1
    assert monetization_service.stats["analyzed"] == 1
    assert trust_service.stats["analyzed"] == 1

    # Verify enriched submission has all components
    assert "opportunity_analysis" in enriched_submission
    assert "ai_profile" in enriched_submission
    assert "monetization_analysis" in enriched_submission
    assert "trust_validation" in enriched_submission


def test_pipeline_error_handling(
    mock_opportunity_analyzer,
    mock_profiler,
    mock_profiler_skip_logic,
    sample_submission,
):
    """Test pipeline handles errors gracefully without breaking."""
    opportunity_service = OpportunityService(mock_opportunity_analyzer)
    profiler_service = ProfilerService(mock_profiler, mock_profiler_skip_logic)

    # Simulate opportunity analysis success
    opportunity_result = opportunity_service.enrich(sample_submission)
    assert opportunity_result["final_score"] == 76.5

    # Simulate profiler error
    mock_profiler.generate_profile.side_effect = Exception("Profiler API error")

    profiler_result = profiler_service.enrich(sample_submission)
    assert profiler_result == {}
    assert profiler_service.stats["errors"] == 1

    # Verify opportunity analysis was not affected
    assert opportunity_service.stats["analyzed"] == 1
    assert opportunity_service.stats["errors"] == 0


def test_pipeline_with_deduplication(
    mock_profiler,
    mock_profiler_skip_logic,
    mock_monetization_analyzer,
    mock_agno_skip_logic,
    sample_submission,
):
    """Test pipeline with deduplication skip logic."""
    # Configure skip logic to skip both analyses
    mock_profiler_skip_logic.should_run_profiler_analysis.return_value = (
        False,
        "Duplicate concept",
    )
    mock_profiler_skip_logic.copy_profiler_analysis.return_value = {
        "app_name": "SimpleProject (copied)",
        "core_functions": ["Task management"],
        "copied_from": "primary_submission_id",
    }

    mock_agno_skip_logic.should_run_agno_analysis.return_value = (
        False,
        "Duplicate concept",
    )
    mock_agno_skip_logic.copy_agno_analysis.return_value = {
        "monetization_score": 75.0,
        "copied_from": "primary_submission_id",
    }

    # Add business_concept_id to submission
    sample_submission["business_concept_id"] = 123

    # Initialize services
    profiler_service = ProfilerService(mock_profiler, mock_profiler_skip_logic)
    monetization_service = MonetizationService(
        mock_monetization_analyzer, mock_agno_skip_logic
    )

    # Process with deduplication
    profiler_result = profiler_service.enrich(sample_submission)
    monetization_result = monetization_service.enrich(sample_submission)

    # Verify results were copied, not freshly generated
    assert "copied_from" in profiler_result
    assert "copied_from" in monetization_result

    # Verify statistics tracked correctly
    assert profiler_service.stats["copied"] == 1
    assert profiler_service.stats["analyzed"] == 0
    assert monetization_service.stats["copied"] == 1
    assert monetization_service.stats["analyzed"] == 0

    # Verify original analyzers were NOT called
    mock_profiler.generate_profile.assert_not_called()
    mock_monetization_analyzer.analyze.assert_not_called()


def test_pipeline_statistics_aggregation(
    mock_opportunity_analyzer,
    mock_profiler,
    mock_profiler_skip_logic,
    sample_submission,
):
    """Test statistics can be aggregated across services."""
    opportunity_service = OpportunityService(mock_opportunity_analyzer)
    profiler_service = ProfilerService(mock_profiler, mock_profiler_skip_logic)

    # Process multiple submissions
    for i in range(3):
        sub = sample_submission.copy()
        sub["submission_id"] = f"test_{i}"
        opportunity_service.enrich(sub)
        profiler_service.enrich(sub)

    # Get statistics
    opp_stats = opportunity_service.get_statistics()
    prof_stats = profiler_service.get_statistics()

    # Verify counts
    assert opp_stats["analyzed"] == 3
    assert prof_stats["analyzed"] == 3

    # Calculate aggregate statistics
    total_analyzed = opp_stats["analyzed"] + prof_stats["analyzed"]
    total_errors = opp_stats["errors"] + prof_stats["errors"]

    assert total_analyzed == 6
    assert total_errors == 0


def test_service_independence(
    mock_opportunity_analyzer, mock_profiler, mock_profiler_skip_logic
):
    """Test services can operate independently without affecting each other."""
    service1 = OpportunityService(mock_opportunity_analyzer)
    service2 = ProfilerService(mock_profiler, mock_profiler_skip_logic)

    submission1 = {
        "submission_id": "test1",
        "title": "Test 1",
        "text": "Content 1",
        "subreddit": "test",
    }

    submission2 = {
        "submission_id": "test2",
        "title": "Test 2",
        "text": "Content 2",
        "subreddit": "test",
    }

    # Process different submissions with different services
    result1 = service1.enrich(submission1)
    result2 = service2.enrich(submission2)

    # Verify both succeeded
    assert result1["final_score"] == 76.5
    assert result2["app_name"] == "SimpleProject"

    # Verify statistics are independent
    assert service1.stats["analyzed"] == 1
    assert service2.stats["analyzed"] == 1


# ===========================
# Performance & Edge Cases
# ===========================


def test_pipeline_with_missing_fields(
    mock_opportunity_analyzer, mock_profiler, mock_profiler_skip_logic
):
    """Test pipeline handles missing optional fields gracefully."""
    minimal_submission = {
        "submission_id": "minimal_test",
        "title": "Minimal Submission",
        "text": "Only required fields",
        "subreddit": "test",
    }

    opportunity_service = OpportunityService(mock_opportunity_analyzer)
    profiler_service = ProfilerService(mock_profiler, mock_profiler_skip_logic)

    # Both should process successfully despite missing optional fields
    opp_result = opportunity_service.enrich(minimal_submission)
    prof_result = profiler_service.enrich(minimal_submission)

    assert opp_result["final_score"] == 76.5
    assert prof_result["app_name"] == "SimpleProject"


def test_pipeline_service_reuse(mock_opportunity_analyzer, sample_submission):
    """Test service can be reused for multiple submissions."""
    service = OpportunityService(mock_opportunity_analyzer)

    # Process multiple submissions with same service instance
    results = []
    for i in range(5):
        sub = sample_submission.copy()
        sub["submission_id"] = f"reuse_test_{i}"
        result = service.enrich(sub)
        results.append(result)

    # Verify all processed successfully
    assert len(results) == 5
    assert all(r["final_score"] == 76.5 for r in results)
    assert service.stats["analyzed"] == 5
