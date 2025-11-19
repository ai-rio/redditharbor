"""Tests for BaseEnrichmentService abstract class.

This test suite ensures 100% coverage of the base_service module,
testing all abstract methods, concrete methods, and validation logic.
"""

import pytest

from core.enrichment.base_service import BaseEnrichmentService


# ===========================
# Test Implementation
# ===========================


class ConcreteService(BaseEnrichmentService):
    """Concrete implementation for testing abstract class."""

    def enrich(self, submission):
        """Test implementation of enrich method."""
        if not self.validate_input(submission):
            self.stats["errors"] += 1
            return {}

        self.stats["analyzed"] += 1
        return {"result": "success", "data": submission.get("title")}

    def get_service_name(self):
        """Test implementation of get_service_name method."""
        return "ConcreteService"


# ===========================
# Initialization Tests
# ===========================


def test_init_with_defaults():
    """Test initialization with default configuration."""
    service = ConcreteService()

    assert service.config == {}
    assert service.stats == {"analyzed": 0, "skipped": 0, "copied": 0, "errors": 0}
    assert service.logger.name == "ConcreteService"


def test_init_with_custom_config():
    """Test initialization with custom configuration."""
    config = {"enable_deduplication": False, "batch_size": 100}
    service = ConcreteService(config=config)

    assert service.config == config
    assert service.config["enable_deduplication"] is False
    assert service.config["batch_size"] == 100


def test_init_stats_are_zero():
    """Test that statistics are initialized to zero."""
    service = ConcreteService()

    assert service.stats["analyzed"] == 0
    assert service.stats["skipped"] == 0
    assert service.stats["copied"] == 0
    assert service.stats["errors"] == 0


# ===========================
# Abstract Method Tests
# ===========================


def test_abstract_enrich_must_be_implemented():
    """Test that enrich() must be implemented by subclasses."""
    # Cannot instantiate abstract class without implementing abstract methods
    with pytest.raises(TypeError):

        class IncompleteService(BaseEnrichmentService):
            def get_service_name(self):
                return "Incomplete"

        IncompleteService()


def test_abstract_get_service_name_must_be_implemented():
    """Test that get_service_name() must be implemented by subclasses."""
    with pytest.raises(TypeError):

        class IncompleteService(BaseEnrichmentService):
            def enrich(self, submission):
                return {}

        IncompleteService()


def test_concrete_implementation_works():
    """Test that concrete implementation of abstract methods works."""
    service = ConcreteService()

    # Should not raise errors
    assert service.enrich({"submission_id": "test", "title": "Test", "subreddit": "test"})
    assert service.get_service_name() == "ConcreteService"


# ===========================
# validate_input() Tests
# ===========================


def test_validate_input_valid_submission():
    """Test validation with valid submission."""
    service = ConcreteService()
    submission = {"submission_id": "abc123", "title": "Test Title", "subreddit": "test"}

    assert service.validate_input(submission) is True


def test_validate_input_missing_submission_id():
    """Test validation with missing submission_id."""
    service = ConcreteService()
    submission = {"title": "Test", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_missing_title():
    """Test validation with missing title."""
    service = ConcreteService()
    submission = {"submission_id": "abc123", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_missing_subreddit():
    """Test validation with missing subreddit."""
    service = ConcreteService()
    submission = {"submission_id": "abc123", "title": "Test"}

    assert service.validate_input(submission) is False


def test_validate_input_empty_submission_id():
    """Test validation with empty submission_id."""
    service = ConcreteService()
    submission = {"submission_id": "", "title": "Test", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_empty_title():
    """Test validation with empty title."""
    service = ConcreteService()
    submission = {"submission_id": "abc123", "title": "", "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_empty_subreddit():
    """Test validation with empty subreddit."""
    service = ConcreteService()
    submission = {"submission_id": "abc123", "title": "Test", "subreddit": ""}

    assert service.validate_input(submission) is False


def test_validate_input_none_values():
    """Test validation with None values."""
    service = ConcreteService()
    submission = {"submission_id": "abc123", "title": None, "subreddit": "test"}

    assert service.validate_input(submission) is False


def test_validate_input_all_fields_present():
    """Test validation with all required fields present and non-empty."""
    service = ConcreteService()
    submission = {
        "submission_id": "abc123",
        "title": "Valid Title",
        "subreddit": "test",
        "extra_field": "extra",
    }

    assert service.validate_input(submission) is True


# ===========================
# get_statistics() Tests
# ===========================


def test_get_statistics_returns_copy():
    """Test that get_statistics() returns a copy, not the original."""
    service = ConcreteService()
    stats1 = service.get_statistics()
    stats2 = service.get_statistics()

    # Should be equal but not the same object
    assert stats1 == stats2
    assert stats1 is not stats2


def test_get_statistics_includes_all_keys():
    """Test that get_statistics() includes all stat keys."""
    service = ConcreteService()
    stats = service.get_statistics()

    assert "analyzed" in stats
    assert "skipped" in stats
    assert "copied" in stats
    assert "errors" in stats


def test_get_statistics_reflects_updates():
    """Test that statistics reflect updates."""
    service = ConcreteService()

    # Enrich a submission (should increment analyzed)
    service.enrich({"submission_id": "test", "title": "Test", "subreddit": "test"})

    stats = service.get_statistics()
    assert stats["analyzed"] == 1
    assert stats["errors"] == 0


def test_get_statistics_after_error():
    """Test statistics after validation error."""
    service = ConcreteService()

    # Invalid submission (should increment errors)
    service.enrich({"title": "Test"})

    stats = service.get_statistics()
    assert stats["analyzed"] == 0
    assert stats["errors"] == 1


# ===========================
# reset_statistics() Tests
# ===========================


def test_reset_statistics_zeros_all_stats():
    """Test that reset_statistics() zeros all statistics."""
    service = ConcreteService()

    # Generate some stats
    service.stats["analyzed"] = 10
    service.stats["skipped"] = 5
    service.stats["copied"] = 3
    service.stats["errors"] = 2

    service.reset_statistics()

    assert service.stats["analyzed"] == 0
    assert service.stats["skipped"] == 0
    assert service.stats["copied"] == 0
    assert service.stats["errors"] == 0


def test_reset_statistics_allows_reuse():
    """Test that service can be reused after reset."""
    service = ConcreteService()

    # First batch
    service.enrich({"submission_id": "test1", "title": "Test", "subreddit": "test"})
    assert service.stats["analyzed"] == 1

    # Reset
    service.reset_statistics()
    assert service.stats["analyzed"] == 0

    # Second batch
    service.enrich({"submission_id": "test2", "title": "Test", "subreddit": "test"})
    assert service.stats["analyzed"] == 1


# ===========================
# log_statistics() Tests
# ===========================


def test_log_statistics_does_not_raise(caplog):
    """Test that log_statistics() doesn't raise errors."""
    service = ConcreteService()
    service.stats["analyzed"] = 5
    service.stats["skipped"] = 2

    # Should not raise
    service.log_statistics()


def test_log_statistics_logs_correct_message(caplog):
    """Test that log_statistics() logs the correct message."""
    import logging

    caplog.set_level(logging.INFO)

    service = ConcreteService()
    service.stats["analyzed"] = 5
    service.stats["skipped"] = 2
    service.stats["copied"] = 1
    service.stats["errors"] = 0

    service.log_statistics()

    # Check log contains service name and stats
    assert "ConcreteService" in caplog.text
    assert "Analyzed: 5" in caplog.text
    assert "Skipped: 2" in caplog.text
    assert "Copied: 1" in caplog.text
    assert "Errors: 0" in caplog.text


# ===========================
# Integration Tests
# ===========================


def test_full_workflow():
    """Test complete workflow with multiple operations."""
    service = ConcreteService()

    # Process valid submissions
    result1 = service.enrich(
        {"submission_id": "sub1", "title": "Title 1", "subreddit": "test"}
    )
    result2 = service.enrich(
        {"submission_id": "sub2", "title": "Title 2", "subreddit": "test"}
    )

    assert result1["result"] == "success"
    assert result2["result"] == "success"
    assert service.stats["analyzed"] == 2

    # Process invalid submission
    result3 = service.enrich({"title": "Missing ID"})
    assert result3 == {}
    assert service.stats["errors"] == 1

    # Check final statistics
    stats = service.get_statistics()
    assert stats["analyzed"] == 2
    assert stats["errors"] == 1
    assert stats["skipped"] == 0
    assert stats["copied"] == 0


def test_config_can_be_accessed_in_subclass():
    """Test that config is accessible to subclass methods."""

    class ConfigAwareService(BaseEnrichmentService):
        def enrich(self, submission):
            # Use config in enrichment
            batch_size = self.config.get("batch_size", 10)
            return {"batch_size": batch_size}

        def get_service_name(self):
            return "ConfigAwareService"

    service = ConfigAwareService(config={"batch_size": 100})
    result = service.enrich({"submission_id": "test", "title": "Test", "subreddit": "test"})

    assert result["batch_size"] == 100


def test_logger_is_specific_to_service():
    """Test that logger name matches service class."""

    class ServiceA(BaseEnrichmentService):
        def enrich(self, submission):
            return {}

        def get_service_name(self):
            return "ServiceA"

    class ServiceB(BaseEnrichmentService):
        def enrich(self, submission):
            return {}

        def get_service_name(self):
            return "ServiceB"

    service_a = ServiceA()
    service_b = ServiceB()

    assert service_a.logger.name == "ServiceA"
    assert service_b.logger.name == "ServiceB"


# ===========================
# Edge Cases
# ===========================


def test_validate_input_with_extra_fields():
    """Test that validation doesn't fail with extra fields."""
    service = ConcreteService()
    submission = {
        "submission_id": "abc123",
        "title": "Test",
        "subreddit": "test",
        "extra1": "value1",
        "extra2": "value2",
        "extra3": "value3",
    }

    assert service.validate_input(submission) is True


def test_enrich_can_modify_stats_directly():
    """Test that enrich implementation can modify stats."""

    class CustomStatsService(BaseEnrichmentService):
        def enrich(self, submission):
            # Increment skipped for testing
            self.stats["skipped"] += 1
            return {}

        def get_service_name(self):
            return "CustomStats"

    service = CustomStatsService()
    service.enrich({"submission_id": "test", "title": "Test", "subreddit": "test"})

    assert service.stats["skipped"] == 1


def test_multiple_service_instances_independent():
    """Test that multiple service instances have independent stats."""
    service1 = ConcreteService()
    service2 = ConcreteService()

    service1.enrich({"submission_id": "test", "title": "Test", "subreddit": "test"})
    service2.enrich({"title": "Invalid"})

    assert service1.stats["analyzed"] == 1
    assert service1.stats["errors"] == 0
    assert service2.stats["analyzed"] == 0
    assert service2.stats["errors"] == 1
