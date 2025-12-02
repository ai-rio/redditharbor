"""Tests for OpportunityService enrichment service.

This test suite ensures comprehensive coverage of the opportunity_service module,
testing initialization, enrichment logic, error handling, and statistics tracking.
"""

import logging
from unittest.mock import MagicMock

import pytest

from core.enrichment.opportunity_service import OpportunityService


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def mock_analyzer():
    """Mock OpportunityAnalyzerAgent for testing."""
    analyzer = MagicMock()
    analyzer.analyze_opportunity.return_value = {
        "opportunity_id": "test123",
        "title": "Test Opportunity",
        "subreddit": "test",
        "dimension_scores": {
            "market_demand": 75.0,
            "pain_intensity": 80.0,
            "monetization_potential": 70.0,
            "market_gap": 65.0,
            "technical_feasibility": 85.0,
            "simplicity_score": 70.0,
        },
        "final_score": 74.5,
        "priority": "⚡ Med-High Priority",
        "weights": {
            "market_demand": 0.20,
            "pain_intensity": 0.25,
            "monetization_potential": 0.20,
            "market_gap": 0.10,
            "technical_feasibility": 0.05,
            "simplicity_score": 0.20,
        },
        "core_functions": [
            "Task and resource management",
            "Reporting and insights",
        ],
        "function_count": 2,
        "timestamp": "2025-01-15T10:30:00",
    }
    return analyzer


@pytest.fixture
def valid_submission():
    """Valid submission data for testing."""
    return {
        "submission_id": "test123",
        "title": "Need better project management tool",
        "text": "Current tools are too complex and expensive. Looking for simpler solution.",
        "subreddit": "startups",
        "upvotes": 100,
        "num_comments": 50,
        "comments": [
            "I agree, existing solutions are terrible",
            "Would pay for a better alternative",
        ],
    }


# ===========================
# Initialization Tests
# ===========================


def test_init_with_defaults(mock_analyzer):
    """Test initialization with default configuration."""
    service = OpportunityService(mock_analyzer)

    assert service.analyzer == mock_analyzer
    assert service.config == {}
    assert service.stats == {"analyzed": 0, "skipped": 0, "copied": 0, "errors": 0}
    assert service.logger.name == "OpportunityService"


def test_init_with_custom_config(mock_analyzer):
    """Test initialization with custom configuration."""
    config = {"enable_logging": True, "batch_size": 100}
    service = OpportunityService(mock_analyzer, config=config)

    assert service.config == config
    assert service.config["enable_logging"] is True
    assert service.config["batch_size"] == 100


def test_init_stats_are_zero(mock_analyzer):
    """Test that statistics are initialized to zero."""
    service = OpportunityService(mock_analyzer)

    assert service.stats["analyzed"] == 0
    assert service.stats["skipped"] == 0
    assert service.stats["copied"] == 0
    assert service.stats["errors"] == 0


# ===========================
# Enrichment Tests
# ===========================


def test_successful_enrichment(mock_analyzer, valid_submission):
    """Test successful opportunity analysis."""
    service = OpportunityService(mock_analyzer)

    result = service.enrich(valid_submission)

    assert result["opportunity_id"] == "test123"
    assert result["final_score"] == 74.5
    assert result["priority"] == "⚡ Med-High Priority"
    assert len(result["core_functions"]) == 2
    assert service.stats["analyzed"] == 1
    assert service.stats["errors"] == 0

    # Verify analyzer was called with correct format
    mock_analyzer.analyze_opportunity.assert_called_once()
    call_args = mock_analyzer.analyze_opportunity.call_args[0][0]
    assert call_args["id"] == "test123"
    assert call_args["title"] == valid_submission["title"]
    assert call_args["text"] == valid_submission["text"]
    assert call_args["subreddit"] == "startups"
    assert call_args["engagement"]["upvotes"] == 100
    assert call_args["engagement"]["num_comments"] == 50


def test_enrichment_with_content_field(mock_analyzer):
    """Test enrichment with 'content' instead of 'text' field."""
    submission = {
        "submission_id": "test456",
        "title": "Test Title",
        "content": "This uses content field instead of text",
        "subreddit": "test",
    }

    service = OpportunityService(mock_analyzer)
    result = service.enrich(submission)

    assert result["final_score"] == 74.5
    assert service.stats["analyzed"] == 1

    # Verify 'content' was mapped to 'text' for analyzer
    call_args = mock_analyzer.analyze_opportunity.call_args[0][0]
    assert call_args["text"] == "This uses content field instead of text"


def test_enrichment_with_missing_optional_fields(mock_analyzer):
    """Test enrichment with missing optional fields (upvotes, comments)."""
    submission = {
        "submission_id": "test789",
        "title": "Minimal Submission",
        "text": "Only required fields",
        "subreddit": "test",
    }

    service = OpportunityService(mock_analyzer)
    result = service.enrich(submission)

    assert result["final_score"] == 74.5
    assert service.stats["analyzed"] == 1

    # Verify defaults were applied
    call_args = mock_analyzer.analyze_opportunity.call_args[0][0]
    assert call_args["engagement"]["upvotes"] == 0
    assert call_args["engagement"]["num_comments"] == 0
    assert call_args["comments"] == []


def test_enrichment_with_invalid_comments_type(mock_analyzer, valid_submission):
    """Test enrichment handles non-list comments field gracefully."""
    valid_submission["comments"] = "Not a list"

    service = OpportunityService(mock_analyzer)
    result = service.enrich(valid_submission)

    assert result["final_score"] == 74.5
    assert service.stats["analyzed"] == 1

    # Verify comments was converted to empty list
    call_args = mock_analyzer.analyze_opportunity.call_args[0][0]
    assert call_args["comments"] == []


# ===========================
# Error Handling Tests
# ===========================


def test_enrichment_with_invalid_input(mock_analyzer):
    """Test enrichment with missing required fields."""
    invalid_submission = {"title": "Missing required fields"}

    service = OpportunityService(mock_analyzer)
    result = service.enrich(invalid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0
    mock_analyzer.analyze_opportunity.assert_not_called()


def test_enrichment_with_analyzer_error(mock_analyzer, valid_submission):
    """Test error handling when analyzer raises exception."""
    mock_analyzer.analyze_opportunity.side_effect = Exception("Analyzer failure")

    service = OpportunityService(mock_analyzer)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0


def test_enrichment_with_empty_result(mock_analyzer, valid_submission):
    """Test handling when analyzer returns empty result."""
    mock_analyzer.analyze_opportunity.return_value = {}

    service = OpportunityService(mock_analyzer)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0


def test_enrichment_with_missing_final_score(mock_analyzer, valid_submission):
    """Test handling when analyzer returns result without final_score."""
    mock_analyzer.analyze_opportunity.return_value = {"opportunity_id": "test"}

    service = OpportunityService(mock_analyzer)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0


def test_enrichment_with_none_result(mock_analyzer, valid_submission):
    """Test handling when analyzer returns None."""
    mock_analyzer.analyze_opportunity.return_value = None

    service = OpportunityService(mock_analyzer)
    result = service.enrich(valid_submission)

    assert result == {}
    assert service.stats["errors"] == 1
    assert service.stats["analyzed"] == 0


# ===========================
# Validation Tests
# ===========================


def test_validate_input_valid_submission(mock_analyzer):
    """Test validation with valid submission."""
    service = OpportunityService(mock_analyzer)
    submission = {
        "submission_id": "test123",
        "title": "Test Title",
        "text": "Test content",
        "subreddit": "test",
    }

    assert service.validate_input(submission) is True


def test_validate_input_with_content_field(mock_analyzer):
    """Test validation accepts 'content' instead of 'text'."""
    service = OpportunityService(mock_analyzer)
    submission = {
        "submission_id": "test123",
        "title": "Test Title",
        "content": "Using content field",
        "subreddit": "test",
    }

    assert service.validate_input(submission) is True


def test_validate_input_missing_submission_id(mock_analyzer):
    """Test validation fails with missing submission_id."""
    service = OpportunityService(mock_analyzer)
    submission = {"title": "Test", "text": "Content", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_missing_title(mock_analyzer):
    """Test validation fails with missing title."""
    service = OpportunityService(mock_analyzer)
    submission = {"submission_id": "test", "text": "Content", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_missing_subreddit(mock_analyzer):
    """Test validation fails with missing subreddit."""
    service = OpportunityService(mock_analyzer)
    submission = {"submission_id": "test", "title": "Test", "text": "Content"}

    assert service.validate_input(submission) is False


def test_validate_input_missing_text_and_content(mock_analyzer):
    """Test validation fails with missing both text and content."""
    service = OpportunityService(mock_analyzer)
    submission = {"submission_id": "test", "title": "Test", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_empty_text(mock_analyzer):
    """Test validation fails with empty text."""
    service = OpportunityService(mock_analyzer)
    submission = {
        "submission_id": "test",
        "title": "Test",
        "text": "",
        "subreddit": "test",
    }

    assert service.validate_input(submission) is False


def test_validate_input_with_extra_fields(mock_analyzer):
    """Test validation doesn't fail with extra fields."""
    service = OpportunityService(mock_analyzer)
    submission = {
        "submission_id": "test",
        "title": "Test",
        "text": "Content",
        "subreddit": "test",
        "extra1": "value1",
        "extra2": "value2",
    }

    assert service.validate_input(submission) is True


# ===========================
# Statistics Tests
# ===========================


def test_statistics_tracking(mock_analyzer, valid_submission):
    """Test statistics are tracked correctly."""
    service = OpportunityService(mock_analyzer)

    # Process valid submissions
    service.enrich(valid_submission)
    service.enrich(valid_submission)

    stats = service.get_statistics()
    assert stats["analyzed"] == 2
    assert stats["errors"] == 0
    assert stats["skipped"] == 0
    assert stats["copied"] == 0


def test_statistics_after_errors(mock_analyzer, valid_submission):
    """Test statistics track errors correctly."""
    service = OpportunityService(mock_analyzer)

    # First succeeds
    service.enrich(valid_submission)

    # Second fails
    mock_analyzer.analyze_opportunity.side_effect = Exception("Error")
    service.enrich(valid_submission)

    # Third fails validation
    service.enrich({"title": "Invalid"})

    stats = service.get_statistics()
    assert stats["analyzed"] == 1
    assert stats["errors"] == 2


def test_get_statistics_returns_copy(mock_analyzer):
    """Test that get_statistics returns a copy."""
    service = OpportunityService(mock_analyzer)

    stats1 = service.get_statistics()
    stats2 = service.get_statistics()

    assert stats1 == stats2
    assert stats1 is not stats2


def test_reset_statistics(mock_analyzer, valid_submission):
    """Test statistics can be reset."""
    service = OpportunityService(mock_analyzer)

    service.enrich(valid_submission)
    assert service.stats["analyzed"] == 1

    service.reset_statistics()

    assert service.stats["analyzed"] == 0
    assert service.stats["errors"] == 0


# ===========================
# get_service_name() Tests
# ===========================


def test_get_service_name(mock_analyzer):
    """Test service name is correct."""
    service = OpportunityService(mock_analyzer)

    assert service.get_service_name() == "OpportunityService"


# ===========================
# log_statistics() Tests
# ===========================


def test_log_statistics_does_not_raise(mock_analyzer, caplog):
    """Test that log_statistics doesn't raise errors."""
    service = OpportunityService(mock_analyzer)
    service.stats["analyzed"] = 5

    # Should not raise
    service.log_statistics()


def test_log_statistics_logs_correct_message(mock_analyzer, caplog):
    """Test that log_statistics logs the correct message."""
    caplog.set_level(logging.INFO)

    service = OpportunityService(mock_analyzer)
    service.stats["analyzed"] = 5
    service.stats["errors"] = 1

    service.log_statistics()

    # Check log contains service name and stats
    assert "OpportunityService" in caplog.text
    assert "Analyzed: 5" in caplog.text
    assert "Errors: 1" in caplog.text


# ===========================
# Integration Tests
# ===========================


def test_full_workflow(mock_analyzer, valid_submission):
    """Test complete workflow with multiple operations."""
    service = OpportunityService(mock_analyzer)

    # Process multiple valid submissions
    result1 = service.enrich(valid_submission)
    result2 = service.enrich(valid_submission)

    assert result1["final_score"] == 74.5
    assert result2["final_score"] == 74.5
    assert service.stats["analyzed"] == 2

    # Process invalid submission
    result3 = service.enrich({"title": "Missing fields"})
    assert result3 == {}
    assert service.stats["errors"] == 1

    # Check final statistics
    stats = service.get_statistics()
    assert stats["analyzed"] == 2
    assert stats["errors"] == 1


def test_multiple_service_instances_independent(mock_analyzer, valid_submission):
    """Test that multiple service instances have independent stats."""
    service1 = OpportunityService(mock_analyzer)
    service2 = OpportunityService(mock_analyzer)

    service1.enrich(valid_submission)
    service2.enrich({"title": "Invalid"})

    assert service1.stats["analyzed"] == 1
    assert service1.stats["errors"] == 0
    assert service2.stats["analyzed"] == 0
    assert service2.stats["errors"] == 1


# ===========================
# Edge Cases
# ===========================


def test_analyzer_returns_high_score_opportunity(mock_analyzer, valid_submission):
    """Test handling of high-priority opportunity."""
    mock_analyzer.analyze_opportunity.return_value = {
        "opportunity_id": "high_priority",
        "title": "High Priority Opportunity",
        "subreddit": "test",
        "dimension_scores": {
            "market_demand": 95.0,
            "pain_intensity": 90.0,
            "monetization_potential": 85.0,
            "market_gap": 80.0,
            "technical_feasibility": 90.0,
            "simplicity_score": 85.0,
        },
        "final_score": 88.5,
        "priority": "🔥 High Priority",
        "core_functions": ["Core feature", "Analytics", "Integration"],
        "function_count": 3,
        "timestamp": "2025-01-15T10:30:00",
    }

    service = OpportunityService(mock_analyzer)
    result = service.enrich(valid_submission)

    assert result["final_score"] == 88.5
    assert result["priority"] == "🔥 High Priority"
    assert len(result["core_functions"]) == 3
    assert service.stats["analyzed"] == 1


def test_analyzer_returns_single_function(mock_analyzer, valid_submission):
    """Test handling when analyzer returns single core function."""
    mock_analyzer.analyze_opportunity.return_value = {
        "opportunity_id": "simple",
        "title": "Simple Opportunity",
        "subreddit": "test",
        "dimension_scores": {},
        "final_score": 60.0,
        "priority": "📊 Medium Priority",
        "core_functions": ["Single core feature"],
        "function_count": 1,
        "timestamp": "2025-01-15T10:30:00",
    }

    service = OpportunityService(mock_analyzer)
    result = service.enrich(valid_submission)

    assert result["final_score"] == 60.0
    assert len(result["core_functions"]) == 1
    assert service.stats["analyzed"] == 1


def test_format_analyzer_input_helper(mock_analyzer):
    """Test _format_analyzer_input helper method."""
    service = OpportunityService(mock_analyzer)

    submission = {
        "submission_id": "test123",
        "title": "Test",
        "text": "Content here",
        "subreddit": "test",
        "upvotes": 50,
        "num_comments": 25,
        "comments": ["Comment 1", "Comment 2"],
    }

    formatted = service._format_analyzer_input(submission)

    assert formatted["id"] == "test123"
    assert formatted["title"] == "Test"
    assert formatted["text"] == "Content here"
    assert formatted["subreddit"] == "test"
    assert formatted["engagement"]["upvotes"] == 50
    assert formatted["engagement"]["num_comments"] == 25
    assert formatted["comments"] == ["Comment 1", "Comment 2"]
