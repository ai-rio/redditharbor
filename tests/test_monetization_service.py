"""Tests for MonetizationService enrichment service.

This test suite ensures comprehensive coverage of the monetization_service module,
testing initialization, enrichment logic, deduplication, error handling, and statistics.
"""

import logging
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from core.enrichment.monetization_service import MonetizationService


# ===========================
# Mock MonetizationAnalysis dataclass
# ===========================


@dataclass
class MockMonetizationAnalysis:
    """Mock MonetizationAnalysis dataclass for testing."""

    willingness_to_pay_score: float
    market_segment_score: float
    price_sensitivity_score: float
    revenue_potential_score: float
    customer_segment: str
    mentioned_price_points: list
    existing_payment_behavior: str
    urgency_level: str
    sentiment_toward_payment: str
    payment_friction_indicators: list
    llm_monetization_score: float
    confidence: float
    reasoning: str
    subreddit_multiplier: float


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def mock_analyzer():
    """Mock MonetizationAgnoAnalyzer for testing."""
    analyzer = MagicMock()
    analyzer.analyze.return_value = MockMonetizationAnalysis(
        willingness_to_pay_score=85.0,
        market_segment_score=75.0,
        price_sensitivity_score=70.0,
        revenue_potential_score=80.0,
        customer_segment="B2B",
        mentioned_price_points=["$50/month", "$500/year"],
        existing_payment_behavior="Active SaaS subscriber",
        urgency_level="High",
        sentiment_toward_payment="Positive",
        payment_friction_indicators=["Budget approval required"],
        llm_monetization_score=78.5,
        confidence=0.85,
        reasoning="Strong B2B signals with clear willingness to pay",
        subreddit_multiplier=1.2,
    )
    return analyzer


@pytest.fixture
def mock_skip_logic():
    """Mock AgnoSkipLogic for testing."""
    skip_logic = MagicMock()
    skip_logic.should_run_agno_analysis.return_value = (True, "No existing analysis")
    skip_logic.copy_agno_analysis.return_value = None
    skip_logic.update_concept_agno_stats.return_value = True

    # Mock concept manager
    mock_concept_manager = MagicMock()
    mock_concept_manager.get_concept_by_id.return_value = {
        "id": 1,
        "primary_submission_id": "primary_sub123",
    }
    skip_logic.concept_manager = mock_concept_manager

    return skip_logic


@pytest.fixture
def valid_submission():
    """Valid submission data for testing."""
    return {
        "submission_id": "test123",
        "title": "Looking for better budgeting solution",
        "text": "Willing to pay $50/month for app that solves this problem",
        "subreddit": "personalfinance",
        "business_concept_id": 1,
    }


# ===========================
# Initialization Tests
# ===========================


def test_init_with_defaults(mock_analyzer, mock_skip_logic):
    """Test initialization with default configuration."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)

    assert service.analyzer == mock_analyzer
    assert service.skip_logic == mock_skip_logic
    assert service.config == {}
    assert service.stats == {"analyzed": 0, "skipped": 0, "copied": 0, "errors": 0}
    assert service.enable_dedup is True
    assert service.logger.name == "MonetizationService"


def test_init_with_custom_config(mock_analyzer, mock_skip_logic):
    """Test initialization with custom configuration."""
    config = {"enable_deduplication": False, "keyword_monetization_score": 50.0}
    service = MonetizationService(mock_analyzer, mock_skip_logic, config=config)

    assert service.config == config
    assert service.enable_dedup is False


def test_init_stats_are_zero(mock_analyzer, mock_skip_logic):
    """Test that statistics are initialized to zero."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)

    assert service.stats["analyzed"] == 0
    assert service.stats["skipped"] == 0
    assert service.stats["copied"] == 0
    assert service.stats["errors"] == 0


# ===========================
# Enrichment Tests
# ===========================


def test_successful_enrichment(mock_analyzer, mock_skip_logic, valid_submission):
    """Test successful monetization analysis."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)

    result = service.enrich(valid_submission)

    assert result["llm_monetization_score"] == 78.5
    assert result["customer_segment"] == "B2B"
    assert result["willingness_to_pay_score"] == 85.0
    assert result["submission_id"] == "test123"
    assert result["business_concept_id"] == 1
    assert service.stats["analyzed"] == 1
    assert service.stats["errors"] == 0

    # Verify analyzer was called with correct parameters
    mock_analyzer.analyze.assert_called_once()
    call_kwargs = mock_analyzer.analyze.call_args[1]
    assert call_kwargs["text"] == valid_submission["text"]
    assert call_kwargs["subreddit"] == "personalfinance"


def test_enrichment_with_content_field(mock_analyzer, mock_skip_logic):
    """Test enrichment with 'content' instead of 'text' field."""
    submission = {
        "submission_id": "test456",
        "title": "Test",
        "content": "This uses content field",
        "subreddit": "test",
    }

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(submission)

    assert result["llm_monetization_score"] == 78.5
    assert service.stats["analyzed"] == 1

    # Verify 'content' was mapped to 'text' for analyzer
    call_kwargs = mock_analyzer.analyze.call_args[1]
    assert call_kwargs["text"] == "This uses content field"


def test_enrichment_with_keyword_score(mock_analyzer, mock_skip_logic, valid_submission):
    """Test enrichment passes keyword_monetization_score to analyzer."""
    valid_submission["keyword_monetization_score"] = 65.0

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    assert result["llm_monetization_score"] == 78.5
    assert service.stats["analyzed"] == 1

    # Verify keyword score was passed
    call_kwargs = mock_analyzer.analyze.call_args[1]
    assert call_kwargs["keyword_monetization_score"] == 65.0


def test_enrichment_with_deduplication_disabled(
    mock_analyzer, mock_skip_logic, valid_submission
):
    """Test enrichment with deduplication disabled."""
    config = {"enable_deduplication": False}
    service = MonetizationService(mock_analyzer, mock_skip_logic, config=config)

    result = service.enrich(valid_submission)

    assert result["llm_monetization_score"] == 78.5
    assert service.stats["analyzed"] == 1

    # Skip logic should not be called
    mock_skip_logic.should_run_agno_analysis.assert_not_called()


# ===========================
# Deduplication Tests
# ===========================


def test_deduplication_skips_and_copies_successfully(
    mock_analyzer, mock_skip_logic, valid_submission
):
    """Test deduplication: skip analysis and copy from primary."""
    # Setup: skip logic says don't run, and copy succeeds
    mock_skip_logic.should_run_agno_analysis.return_value = (
        False,
        "Concept already has analysis",
    )
    mock_skip_logic.copy_agno_analysis.return_value = {
        "llm_monetization_score": 80.0,
        "customer_segment": "B2B",
        "copied_from_primary": True,
    }

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    assert result["llm_monetization_score"] == 80.0
    assert result["copied_from_primary"] is True
    assert service.stats["copied"] == 1
    assert service.stats["analyzed"] == 0

    # Analyzer should not be called
    mock_analyzer.analyze.assert_not_called()

    # Copy should be called with correct parameters
    mock_skip_logic.copy_agno_analysis.assert_called_once_with(
        "primary_sub123", "test123", 1
    )


def test_deduplication_skips_but_copy_fails(
    mock_analyzer, mock_skip_logic, valid_submission
):
    """Test deduplication: skip analysis but copy fails, so skip."""
    # Setup: skip logic says don't run, but copy returns None
    mock_skip_logic.should_run_agno_analysis.return_value = (
        False,
        "Concept already has analysis",
    )
    mock_skip_logic.copy_agno_analysis.return_value = None

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["skipped"] == 1
    assert service.stats["copied"] == 0
    assert service.stats["analyzed"] == 0


def test_deduplication_no_business_concept(mock_analyzer, mock_skip_logic):
    """Test that missing business_concept_id triggers fresh analysis."""
    submission = {
        "submission_id": "test789",
        "title": "Test",
        "text": "No business concept",
        "subreddit": "test",
        # No business_concept_id
    }

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(submission)

    assert result["llm_monetization_score"] == 78.5
    assert service.stats["analyzed"] == 1

    # Skip logic should not be called when no concept ID
    mock_skip_logic.should_run_agno_analysis.assert_not_called()


def test_deduplication_updates_concept_stats(
    mock_analyzer, mock_skip_logic, valid_submission
):
    """Test that concept stats are updated after fresh analysis."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    assert service.stats["analyzed"] == 1

    # Verify update_concept_agno_stats was called
    mock_skip_logic.update_concept_agno_stats.assert_called_once()
    call_args = mock_skip_logic.update_concept_agno_stats.call_args[0]
    assert call_args[0] == 1  # concept_id
    assert isinstance(call_args[1], dict)  # analysis dict


# ===========================
# Error Handling Tests
# ===========================


def test_enrichment_with_invalid_input(mock_analyzer, mock_skip_logic):
    """Test enrichment with missing required fields."""
    invalid_submission = {"title": "Missing required fields"}

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(invalid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0
    mock_analyzer.analyze.assert_not_called()


def test_enrichment_with_analyzer_error(
    mock_analyzer, mock_skip_logic, valid_submission
):
    """Test error handling when analyzer raises exception."""
    mock_analyzer.analyze.side_effect = Exception("Analyzer failure")

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0


def test_enrichment_with_skip_logic_error(
    mock_analyzer, mock_skip_logic, valid_submission
):
    """Test error handling when skip logic raises exception."""
    mock_skip_logic.should_run_agno_analysis.side_effect = Exception("Skip logic error")

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1


def test_enrichment_with_copy_error(mock_analyzer, mock_skip_logic, valid_submission):
    """Test error handling when copy operation raises exception."""
    mock_skip_logic.should_run_agno_analysis.return_value = (False, "Skip analysis")
    mock_skip_logic.copy_agno_analysis.side_effect = Exception("Copy error")

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1


def test_get_primary_submission_id_error(mock_analyzer, mock_skip_logic, valid_submission):
    """Test error handling when getting primary submission ID fails."""
    mock_skip_logic.should_run_agno_analysis.return_value = (False, "Skip analysis")
    mock_skip_logic.concept_manager.get_concept_by_id.side_effect = Exception(
        "Concept error"
    )

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    # Should skip since primary ID retrieval failed
    assert result == {}
    assert service.stats["skipped"] == 1


# ===========================
# Validation Tests
# ===========================


def test_validate_input_valid_submission(mock_analyzer, mock_skip_logic):
    """Test validation with valid submission."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    submission = {
        "submission_id": "test123",
        "title": "Test Title",
        "text": "Test content",
        "subreddit": "test",
    }

    assert service.validate_input(submission) is True


def test_validate_input_with_content_field(mock_analyzer, mock_skip_logic):
    """Test validation accepts 'content' instead of 'text'."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    submission = {
        "submission_id": "test123",
        "title": "Test Title",
        "content": "Using content field",
        "subreddit": "test",
    }

    assert service.validate_input(submission) is True


def test_validate_input_missing_submission_id(mock_analyzer, mock_skip_logic):
    """Test validation fails with missing submission_id."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    submission = {"title": "Test", "text": "Content", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_missing_title(mock_analyzer, mock_skip_logic):
    """Test validation fails with missing title."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    submission = {"submission_id": "test", "text": "Content", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_missing_subreddit(mock_analyzer, mock_skip_logic):
    """Test validation fails with missing subreddit."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    submission = {"submission_id": "test", "title": "Test", "text": "Content"}

    assert service.validate_input(submission) is False


def test_validate_input_missing_text_and_content(mock_analyzer, mock_skip_logic):
    """Test validation fails with missing both text and content."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    submission = {"submission_id": "test", "title": "Test", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_empty_text(mock_analyzer, mock_skip_logic):
    """Test validation fails with empty text."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    submission = {
        "submission_id": "test",
        "title": "Test",
        "text": "",
        "subreddit": "test",
    }

    assert service.validate_input(submission) is False


def test_validate_input_with_extra_fields(mock_analyzer, mock_skip_logic):
    """Test validation doesn't fail with extra fields."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    submission = {
        "submission_id": "test",
        "title": "Test",
        "text": "Content",
        "subreddit": "test",
        "business_concept_id": 1,
        "keyword_monetization_score": 70.0,
    }

    assert service.validate_input(submission) is True


# ===========================
# Statistics Tests
# ===========================


def test_statistics_tracking(mock_analyzer, mock_skip_logic, valid_submission):
    """Test statistics are tracked correctly."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)

    # Process valid submissions
    service.enrich(valid_submission)
    service.enrich(valid_submission)

    stats = service.get_statistics()
    assert stats["analyzed"] == 2
    assert stats["errors"] == 0


def test_statistics_after_copy(mock_analyzer, mock_skip_logic, valid_submission):
    """Test statistics track copy operations correctly."""
    mock_skip_logic.should_run_agno_analysis.return_value = (False, "Skip")
    mock_skip_logic.copy_agno_analysis.return_value = {"score": 80}

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    service.enrich(valid_submission)

    stats = service.get_statistics()
    assert stats["copied"] == 1
    assert stats["analyzed"] == 0


def test_statistics_after_skip(mock_analyzer, mock_skip_logic, valid_submission):
    """Test statistics track skip operations correctly."""
    mock_skip_logic.should_run_agno_analysis.return_value = (False, "Skip")
    mock_skip_logic.copy_agno_analysis.return_value = None  # Copy fails

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    service.enrich(valid_submission)

    stats = service.get_statistics()
    assert stats["skipped"] == 1
    assert stats["analyzed"] == 0
    assert stats["copied"] == 0


def test_get_statistics_returns_copy(mock_analyzer, mock_skip_logic):
    """Test that get_statistics returns a copy."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)

    stats1 = service.get_statistics()
    stats2 = service.get_statistics()

    assert stats1 == stats2
    assert stats1 is not stats2


def test_reset_statistics(mock_analyzer, mock_skip_logic, valid_submission):
    """Test statistics can be reset."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)

    service.enrich(valid_submission)
    assert service.stats["analyzed"] == 1

    service.reset_statistics()

    assert service.stats["analyzed"] == 0
    assert service.stats["errors"] == 0


# ===========================
# get_service_name() Tests
# ===========================


def test_get_service_name(mock_analyzer, mock_skip_logic):
    """Test service name is correct."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)

    assert service.get_service_name() == "MonetizationService"


# ===========================
# log_statistics() Tests
# ===========================


def test_log_statistics_does_not_raise(mock_analyzer, mock_skip_logic, caplog):
    """Test that log_statistics doesn't raise errors."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)
    service.stats["analyzed"] = 5

    # Should not raise
    service.log_statistics()


def test_log_statistics_logs_correct_message(mock_analyzer, mock_skip_logic, caplog):
    """Test that log_statistics logs the correct message."""
    caplog.set_level(logging.INFO)

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    service.stats["analyzed"] = 5
    service.stats["copied"] = 2
    service.stats["skipped"] = 1

    service.log_statistics()

    # Check log contains service name and stats
    assert "MonetizationService" in caplog.text
    assert "Analyzed: 5" in caplog.text
    assert "Copied: 2" in caplog.text
    assert "Skipped: 1" in caplog.text


# ===========================
# Integration Tests
# ===========================


def test_full_workflow(mock_analyzer, mock_skip_logic, valid_submission):
    """Test complete workflow with multiple operations."""
    service = MonetizationService(mock_analyzer, mock_skip_logic)

    # Process valid submission (fresh analysis)
    result1 = service.enrich(valid_submission)
    assert result1["llm_monetization_score"] == 78.5
    assert service.stats["analyzed"] == 1

    # Process duplicate (skip and copy)
    mock_skip_logic.should_run_agno_analysis.return_value = (False, "Has analysis")
    mock_skip_logic.copy_agno_analysis.return_value = {"score": 78.5}

    result2 = service.enrich(valid_submission)
    assert result2["score"] == 78.5
    assert service.stats["copied"] == 1

    # Process invalid submission
    result3 = service.enrich({"title": "Invalid"})
    assert result3 == {}
    assert service.stats["errors"] == 1

    # Check final statistics
    stats = service.get_statistics()
    assert stats["analyzed"] == 1
    assert stats["copied"] == 1
    assert stats["errors"] == 1


def test_multiple_service_instances_independent(
    mock_analyzer, mock_skip_logic, valid_submission
):
    """Test that multiple service instances have independent stats."""
    service1 = MonetizationService(mock_analyzer, mock_skip_logic)
    service2 = MonetizationService(mock_analyzer, mock_skip_logic)

    service1.enrich(valid_submission)
    service2.enrich({"title": "Invalid"})

    assert service1.stats["analyzed"] == 1
    assert service1.stats["errors"] == 0
    assert service2.stats["analyzed"] == 0
    assert service2.stats["errors"] == 1


# ===========================
# Edge Cases
# ===========================


def test_analyzer_returns_b2c_segment(mock_analyzer, mock_skip_logic, valid_submission):
    """Test handling of B2C market segment analysis."""
    mock_analyzer.analyze.return_value = MockMonetizationAnalysis(
        willingness_to_pay_score=70.0,
        market_segment_score=80.0,
        price_sensitivity_score=60.0,
        revenue_potential_score=65.0,
        customer_segment="B2C",
        mentioned_price_points=["$10/month"],
        existing_payment_behavior="Occasional app buyer",
        urgency_level="Medium",
        sentiment_toward_payment="Neutral",
        payment_friction_indicators=["Price sensitivity"],
        llm_monetization_score=68.0,
        confidence=0.75,
        reasoning="B2C indicators with moderate willingness to pay",
        subreddit_multiplier=1.0,
    )

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    assert result["customer_segment"] == "B2C"
    assert result["llm_monetization_score"] == 68.0
    assert service.stats["analyzed"] == 1


def test_analyzer_returns_mixed_segment(mock_analyzer, mock_skip_logic, valid_submission):
    """Test handling of Mixed market segment analysis."""
    mock_analyzer.analyze.return_value = MockMonetizationAnalysis(
        willingness_to_pay_score=75.0,
        market_segment_score=70.0,
        price_sensitivity_score=65.0,
        revenue_potential_score=72.0,
        customer_segment="Mixed",
        mentioned_price_points=["$20/month"],
        existing_payment_behavior="Both personal and business use",
        urgency_level="Medium",
        sentiment_toward_payment="Positive",
        payment_friction_indicators=[],
        llm_monetization_score=72.0,
        confidence=0.80,
        reasoning="Mixed B2B/B2C indicators",
        subreddit_multiplier=1.1,
    )

    service = MonetizationService(mock_analyzer, mock_skip_logic)
    result = service.enrich(valid_submission)

    assert result["customer_segment"] == "Mixed"
    assert result["llm_monetization_score"] == 72.0
    assert service.stats["analyzed"] == 1
