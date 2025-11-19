"""Tests for TrustService enrichment service.

This test suite ensures comprehensive coverage of the trust_service module,
testing initialization, trust validation, error handling, and statistics tracking.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from unittest.mock import MagicMock

import pytest

from core.enrichment.trust_service import TrustService


# ===========================
# Test Data Models
# ===========================


class TrustLevel(Enum):
    """Trust level enumeration for testing."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class TrustIndicators:
    """Mock trust indicators for testing."""

    subreddit_activity_score: float
    post_engagement_score: float
    community_health_score: float
    trend_velocity_score: float
    problem_validity_score: float
    discussion_quality_score: float
    ai_analysis_confidence: float
    overall_trust_score: float
    trust_level: TrustLevel
    trust_badges: list
    activity_constraints_met: bool
    quality_constraints_met: bool
    validation_timestamp: str
    validation_method: str


@dataclass
class ValidationResult:
    """Mock validation result for testing."""

    success: bool
    indicators: TrustIndicators


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def mock_validator():
    """Mock TrustValidationService for testing."""
    validator = MagicMock()

    # Create mock trust indicators
    indicators = TrustIndicators(
        subreddit_activity_score=75.0,
        post_engagement_score=80.0,
        community_health_score=70.0,
        trend_velocity_score=65.0,
        problem_validity_score=85.0,
        discussion_quality_score=78.0,
        ai_analysis_confidence=82.0,
        overall_trust_score=76.5,
        trust_level=TrustLevel.HIGH,
        trust_badges=["high_engagement", "strong_community"],
        activity_constraints_met=True,
        quality_constraints_met=True,
        validation_timestamp="2025-01-15T10:30:00",
        validation_method="comprehensive",
    )

    result = ValidationResult(success=True, indicators=indicators)
    validator.validate_opportunity_trust.return_value = result

    return validator


@pytest.fixture
def valid_submission():
    """Valid submission data for testing."""
    return {
        "submission_id": "test123",
        "title": "Need better project management tool",
        "text": "Current tools are too complex. Looking for simpler solution.",
        "subreddit": "startups",
        "upvotes": 150,
        "comments_count": 25,
        "created_utc": 1700000000,
    }


# ===========================
# Initialization Tests
# ===========================


def test_init_with_defaults(mock_validator):
    """Test initialization with default configuration."""
    service = TrustService(mock_validator)

    assert service.validator == mock_validator
    assert service.config == {}
    assert service.stats == {"analyzed": 0, "skipped": 0, "copied": 0, "errors": 0}
    assert service.logger.name == "TrustService"


def test_init_with_custom_config(mock_validator):
    """Test initialization with custom configuration."""
    config = {"activity_threshold": 30.0, "trust_weights": {"activity": 0.3}}
    service = TrustService(mock_validator, config=config)

    assert service.config == config
    assert service.config["activity_threshold"] == 30.0
    assert service.config["trust_weights"]["activity"] == 0.3


def test_init_stats_are_zero(mock_validator):
    """Test that statistics are initialized to zero."""
    service = TrustService(mock_validator)

    assert service.stats["analyzed"] == 0
    assert service.stats["skipped"] == 0
    assert service.stats["copied"] == 0
    assert service.stats["errors"] == 0


# ===========================
# Enrichment Tests
# ===========================


def test_successful_enrichment(mock_validator, valid_submission):
    """Test successful trust validation."""
    service = TrustService(mock_validator)

    result = service.enrich(valid_submission)

    assert result["overall_trust_score"] == 76.5
    assert result["trust_level"] == "high"
    assert result["subreddit_activity_score"] == 75.0
    assert result["post_engagement_score"] == 80.0
    assert result["trust_badges"] == ["high_engagement", "strong_community"]
    assert result["activity_constraints_met"] is True
    assert result["submission_id"] == "test123"
    assert service.stats["analyzed"] == 1
    assert service.stats["errors"] == 0

    # Verify validator was called
    mock_validator.validate_opportunity_trust.assert_called_once()


def test_enrichment_with_content_field(mock_validator):
    """Test enrichment with 'content' instead of 'text' field."""
    submission = {
        "submission_id": "test456",
        "title": "Test Title",
        "content": "This uses content field instead of text",
        "subreddit": "test",
        "upvotes": 100,
        "created_utc": 1700000000,
    }

    service = TrustService(mock_validator)
    result = service.enrich(submission)

    assert result["overall_trust_score"] == 76.5
    assert service.stats["analyzed"] == 1

    # Verify 'content' was mapped to 'text' for validator
    call_args = mock_validator.validate_opportunity_trust.call_args[0][0]
    assert call_args.text == "This uses content field instead of text"


def test_enrichment_with_num_comments_field(mock_validator, valid_submission):
    """Test enrichment with 'num_comments' instead of 'comments_count'."""
    submission = valid_submission.copy()
    del submission["comments_count"]
    submission["num_comments"] = 30

    service = TrustService(mock_validator)
    result = service.enrich(submission)

    assert result["overall_trust_score"] == 76.5
    assert service.stats["analyzed"] == 1

    # Verify num_comments was used
    call_args = mock_validator.validate_opportunity_trust.call_args[0][0]
    assert call_args.comments_count == 30


def test_enrichment_with_missing_optional_fields(mock_validator):
    """Test enrichment with missing optional fields (text, comments_count)."""
    submission = {
        "submission_id": "test789",
        "title": "Minimal Submission",
        "subreddit": "test",
        "upvotes": 50,
        "created_utc": 1700000000,
    }

    service = TrustService(mock_validator)
    result = service.enrich(submission)

    assert result["overall_trust_score"] == 76.5
    assert service.stats["analyzed"] == 1

    # Verify defaults were applied
    call_args = mock_validator.validate_opportunity_trust.call_args[0][0]
    assert call_args.text == ""
    assert call_args.comments_count == 0


def test_enrichment_with_ai_analysis(mock_validator, valid_submission):
    """Test enrichment with AI analysis included."""
    valid_submission["ai_analysis"] = {
        "confidence": 0.85,
        "analysis": "High quality opportunity",
    }

    service = TrustService(mock_validator)
    result = service.enrich(valid_submission)

    assert result["overall_trust_score"] == 76.5
    assert service.stats["analyzed"] == 1

    # Verify ai_analysis was passed through
    call_args = mock_validator.validate_opportunity_trust.call_args[0][0]
    assert call_args.ai_analysis is not None
    assert call_args.ai_analysis["confidence"] == 0.85


def test_enrichment_with_config_overrides(mock_validator, valid_submission):
    """Test enrichment with config overrides (activity_threshold, trust_weights)."""
    config = {"activity_threshold": 35.0, "trust_weights": {"activity": 0.4}}
    service = TrustService(mock_validator, config=config)

    result = service.enrich(valid_submission)

    assert result["overall_trust_score"] == 76.5
    assert service.stats["analyzed"] == 1

    # Verify config was passed to validator
    call_args = mock_validator.validate_opportunity_trust.call_args[0][0]
    assert call_args.activity_threshold == 35.0
    assert call_args.trust_weights == {"activity": 0.4}


# ===========================
# Error Handling Tests
# ===========================


def test_enrichment_with_invalid_input(mock_validator):
    """Test enrichment with missing required fields."""
    invalid_submission = {"title": "Missing required fields"}

    service = TrustService(mock_validator)
    result = service.enrich(invalid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0
    mock_validator.validate_opportunity_trust.assert_not_called()


def test_enrichment_with_validator_error(mock_validator, valid_submission):
    """Test error handling when validator raises exception."""
    mock_validator.validate_opportunity_trust.side_effect = Exception(
        "Validator failure"
    )

    service = TrustService(mock_validator)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0


def test_enrichment_with_validation_failure(mock_validator, valid_submission):
    """Test handling when validator returns unsuccessful result."""
    mock_validator.validate_opportunity_trust.return_value = ValidationResult(
        success=False, indicators=None
    )

    service = TrustService(mock_validator)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0


def test_enrichment_with_none_indicators(mock_validator, valid_submission):
    """Test handling when validator returns None indicators."""
    mock_validator.validate_opportunity_trust.return_value = ValidationResult(
        success=True, indicators=None
    )

    service = TrustService(mock_validator)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0


# ===========================
# Validation Tests
# ===========================


def test_validate_input_valid_submission(mock_validator):
    """Test validation with valid submission."""
    service = TrustService(mock_validator)
    submission = {
        "submission_id": "test123",
        "title": "Test Title",
        "subreddit": "test",
        "upvotes": 100,
        "created_utc": 1700000000,
    }

    assert service.validate_input(submission) is True


def test_validate_input_missing_submission_id(mock_validator):
    """Test validation fails with missing submission_id."""
    service = TrustService(mock_validator)
    submission = {
        "title": "Test",
        "subreddit": "test",
        "upvotes": 100,
        "created_utc": 1700000000,
    }

    assert service.validate_input(submission) is False


def test_validate_input_missing_title(mock_validator):
    """Test validation fails with missing title."""
    service = TrustService(mock_validator)
    submission = {
        "submission_id": "test",
        "subreddit": "test",
        "upvotes": 100,
        "created_utc": 1700000000,
    }

    assert service.validate_input(submission) is False


def test_validate_input_missing_subreddit(mock_validator):
    """Test validation fails with missing subreddit."""
    service = TrustService(mock_validator)
    submission = {
        "submission_id": "test",
        "title": "Test",
        "upvotes": 100,
        "created_utc": 1700000000,
    }

    assert service.validate_input(submission) is False


def test_validate_input_missing_upvotes(mock_validator):
    """Test validation fails with missing upvotes."""
    service = TrustService(mock_validator)
    submission = {
        "submission_id": "test",
        "title": "Test",
        "subreddit": "test",
        "created_utc": 1700000000,
    }

    assert service.validate_input(submission) is False


def test_validate_input_missing_created_utc(mock_validator):
    """Test validation fails with missing created_utc."""
    service = TrustService(mock_validator)
    submission = {
        "submission_id": "test",
        "title": "Test",
        "subreddit": "test",
        "upvotes": 100,
    }

    assert service.validate_input(submission) is False


def test_validate_input_with_extra_fields(mock_validator):
    """Test validation doesn't fail with extra fields."""
    service = TrustService(mock_validator)
    submission = {
        "submission_id": "test",
        "title": "Test",
        "subreddit": "test",
        "upvotes": 100,
        "created_utc": 1700000000,
        "extra1": "value1",
        "extra2": "value2",
    }

    assert service.validate_input(submission) is True


# ===========================
# Statistics Tests
# ===========================


def test_statistics_tracking(mock_validator, valid_submission):
    """Test statistics are tracked correctly."""
    service = TrustService(mock_validator)

    # Process valid submissions
    service.enrich(valid_submission)
    service.enrich(valid_submission)

    stats = service.get_statistics()
    assert stats["analyzed"] == 2
    assert stats["errors"] == 0
    assert stats["skipped"] == 0
    assert stats["copied"] == 0


def test_statistics_after_errors(mock_validator, valid_submission):
    """Test statistics track errors correctly."""
    service = TrustService(mock_validator)

    # First succeeds
    service.enrich(valid_submission)

    # Second fails
    mock_validator.validate_opportunity_trust.side_effect = Exception("Error")
    service.enrich(valid_submission)

    # Third fails validation
    service.enrich({"title": "Invalid"})

    stats = service.get_statistics()
    assert stats["analyzed"] == 1
    assert stats["errors"] == 2


def test_get_statistics_returns_copy(mock_validator):
    """Test that get_statistics returns a copy."""
    service = TrustService(mock_validator)

    stats1 = service.get_statistics()
    stats2 = service.get_statistics()

    assert stats1 == stats2
    assert stats1 is not stats2


def test_reset_statistics(mock_validator, valid_submission):
    """Test statistics can be reset."""
    service = TrustService(mock_validator)

    service.enrich(valid_submission)
    assert service.stats["analyzed"] == 1

    service.reset_statistics()

    assert service.stats["analyzed"] == 0
    assert service.stats["errors"] == 0


# ===========================
# get_service_name() Tests
# ===========================


def test_get_service_name(mock_validator):
    """Test service name is correct."""
    service = TrustService(mock_validator)

    assert service.get_service_name() == "TrustService"


# ===========================
# log_statistics() Tests
# ===========================


def test_log_statistics_does_not_raise(mock_validator, caplog):
    """Test that log_statistics doesn't raise errors."""
    service = TrustService(mock_validator)
    service.stats["analyzed"] = 5

    # Should not raise
    service.log_statistics()


def test_log_statistics_logs_correct_message(mock_validator, caplog):
    """Test that log_statistics logs the correct message."""
    caplog.set_level(logging.INFO)

    service = TrustService(mock_validator)
    service.stats["analyzed"] = 5
    service.stats["errors"] = 1

    service.log_statistics()

    # Check log contains service name and stats
    assert "TrustService" in caplog.text
    assert "Analyzed: 5" in caplog.text
    assert "Errors: 1" in caplog.text


# ===========================
# Integration Tests
# ===========================


def test_full_workflow(mock_validator, valid_submission):
    """Test complete workflow with multiple operations."""
    service = TrustService(mock_validator)

    # Process multiple valid submissions
    result1 = service.enrich(valid_submission)
    result2 = service.enrich(valid_submission)

    assert result1["overall_trust_score"] == 76.5
    assert result2["overall_trust_score"] == 76.5
    assert service.stats["analyzed"] == 2

    # Process invalid submission
    result3 = service.enrich({"title": "Missing fields"})
    assert result3 == {}
    assert service.stats["errors"] == 1

    # Check final statistics
    stats = service.get_statistics()
    assert stats["analyzed"] == 2
    assert stats["errors"] == 1


def test_multiple_service_instances_independent(mock_validator, valid_submission):
    """Test that multiple service instances have independent stats."""
    service1 = TrustService(mock_validator)
    service2 = TrustService(mock_validator)

    service1.enrich(valid_submission)
    service2.enrich({"title": "Invalid"})

    assert service1.stats["analyzed"] == 1
    assert service1.stats["errors"] == 0
    assert service2.stats["analyzed"] == 0
    assert service2.stats["errors"] == 1


# ===========================
# Edge Cases
# ===========================


def test_validator_returns_very_high_trust(mock_validator, valid_submission):
    """Test handling of very high trust level."""
    indicators = TrustIndicators(
        subreddit_activity_score=95.0,
        post_engagement_score=98.0,
        community_health_score=92.0,
        trend_velocity_score=90.0,
        problem_validity_score=96.0,
        discussion_quality_score=94.0,
        ai_analysis_confidence=93.0,
        overall_trust_score=94.5,
        trust_level=TrustLevel.VERY_HIGH,
        trust_badges=["verified", "high_engagement", "strong_community", "trending"],
        activity_constraints_met=True,
        quality_constraints_met=True,
        validation_timestamp="2025-01-15T10:30:00",
        validation_method="comprehensive",
    )

    mock_validator.validate_opportunity_trust.return_value = ValidationResult(
        success=True, indicators=indicators
    )

    service = TrustService(mock_validator)
    result = service.enrich(valid_submission)

    assert result["overall_trust_score"] == 94.5
    assert result["trust_level"] == "very_high"
    assert len(result["trust_badges"]) == 4
    assert service.stats["analyzed"] == 1


def test_validator_returns_low_trust(mock_validator, valid_submission):
    """Test handling of low trust level."""
    indicators = TrustIndicators(
        subreddit_activity_score=25.0,
        post_engagement_score=30.0,
        community_health_score=20.0,
        trend_velocity_score=15.0,
        problem_validity_score=28.0,
        discussion_quality_score=22.0,
        ai_analysis_confidence=26.0,
        overall_trust_score=24.5,
        trust_level=TrustLevel.LOW,
        trust_badges=[],
        activity_constraints_met=False,
        quality_constraints_met=False,
        validation_timestamp="2025-01-15T10:30:00",
        validation_method="comprehensive",
    )

    mock_validator.validate_opportunity_trust.return_value = ValidationResult(
        success=True, indicators=indicators
    )

    service = TrustService(mock_validator)
    result = service.enrich(valid_submission)

    assert result["overall_trust_score"] == 24.5
    assert result["trust_level"] == "low"
    assert result["trust_badges"] == []
    assert result["activity_constraints_met"] is False
    assert result["quality_constraints_met"] is False
    assert service.stats["analyzed"] == 1


def test_format_validation_request_helper(mock_validator, valid_submission):
    """Test _format_validation_request helper method."""
    service = TrustService(mock_validator)

    result = service._format_validation_request(valid_submission)

    assert result.submission_id == "test123"
    assert result.subreddit == "startups"
    assert result.upvotes == 150
    assert result.comments_count == 25
    assert result.created_utc == 1700000000
    assert result.text == valid_submission["text"]
    assert result.title == valid_submission["title"]
    assert result.ai_analysis is None


def test_format_validation_request_with_config(mock_validator, valid_submission):
    """Test _format_validation_request passes config overrides."""
    config = {"activity_threshold": 40.0, "trust_weights": {"engagement": 0.5}}
    service = TrustService(mock_validator, config=config)

    result = service._format_validation_request(valid_submission)

    assert result.activity_threshold == 40.0
    assert result.trust_weights == {"engagement": 0.5}
