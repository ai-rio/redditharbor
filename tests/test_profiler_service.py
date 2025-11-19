"""Tests for ProfilerService with deduplication.

This test suite ensures 100% coverage of the profiler_service module,
testing enrichment, deduplication integration, error handling, and statistics.
"""

from unittest.mock import MagicMock, Mock

import pytest

from core.enrichment.profiler_service import ProfilerService


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def mock_profiler():
    """Create mock EnhancedLLMProfiler."""
    profiler = MagicMock()
    profiler.generate_app_profile.return_value = {
        "app_name": "TestApp",
        "core_functions": ["feature1", "feature2"],
        "value_proposition": "Test value prop",
        "problem_description": "Test problem",
        "target_user": "Test users",
        "monetization_model": "Freemium",
        "final_score": 85.0,
        "market_demand": 90,
        "pain_intensity": 80,
    }
    return profiler


@pytest.fixture
def mock_skip_logic():
    """Create mock ProfilerSkipLogic."""
    skip_logic = MagicMock()
    skip_logic.should_run_profiler_analysis.return_value = (True, "No existing profile")
    skip_logic.copy_profiler_analysis.return_value = None
    skip_logic.update_concept_profiler_stats.return_value = True

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
    """Create valid submission data."""
    return {
        "submission_id": "sub123",
        "title": "Need project management tool",
        "text": "Looking for tool to manage team projects",
        "subreddit": "startups",
        "score": 75,
    }


# ===========================
# Initialization Tests
# ===========================


def test_init_with_defaults(mock_profiler, mock_skip_logic):
    """Test initialization with default configuration."""
    service = ProfilerService(mock_profiler, mock_skip_logic)

    assert service.profiler == mock_profiler
    assert service.skip_logic == mock_skip_logic
    assert service.enable_dedup is True
    assert service.stats == {"analyzed": 0, "skipped": 0, "copied": 0, "errors": 0}


def test_init_with_custom_config(mock_profiler, mock_skip_logic):
    """Test initialization with custom configuration."""
    config = {"enable_deduplication": False, "include_agno_evidence": True}
    service = ProfilerService(mock_profiler, mock_skip_logic, config=config)

    assert service.enable_dedup is False
    assert service.config["include_agno_evidence"] is True


def test_init_inherits_from_base_service(mock_profiler, mock_skip_logic):
    """Test that ProfilerService inherits BaseEnrichmentService."""
    service = ProfilerService(mock_profiler, mock_skip_logic)

    # Should have methods from BaseEnrichmentService
    assert hasattr(service, "get_statistics")
    assert hasattr(service, "reset_statistics")
    assert hasattr(service, "validate_input")
    assert hasattr(service, "log_statistics")


# ===========================
# enrich() Method Tests
# ===========================


def test_enrich_fresh_analysis(mock_profiler, mock_skip_logic, valid_submission):
    """Test fresh profile generation (no deduplication)."""
    service = ProfilerService(mock_profiler, mock_skip_logic)

    result = service.enrich(valid_submission)

    # Check profiler was called
    mock_profiler.generate_app_profile.assert_called_once()

    # Check result
    assert result["app_name"] == "TestApp"
    assert "core_functions" in result
    assert result["submission_id"] == "sub123"
    assert result["opportunity_id"] == "opp_sub123"

    # Check statistics
    assert service.stats["analyzed"] == 1
    assert service.stats["skipped"] == 0
    assert service.stats["errors"] == 0


def test_enrich_with_business_concept(mock_profiler, mock_skip_logic, valid_submission):
    """Test enrichment with business concept (deduplication check)."""
    valid_submission["business_concept_id"] = 1

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(valid_submission)

    # Should check skip logic
    mock_skip_logic.should_run_profiler_analysis.assert_called_once_with(
        valid_submission, 1
    )

    # Should update concept stats
    mock_skip_logic.update_concept_profiler_stats.assert_called_once()

    assert result["app_name"] == "TestApp"
    assert service.stats["analyzed"] == 1


def test_enrich_skip_due_to_deduplication(mock_profiler, mock_skip_logic, valid_submission):
    """Test skipping analysis due to deduplication."""
    valid_submission["business_concept_id"] = 1

    # Mock skip logic to return False (should skip)
    mock_skip_logic.should_run_profiler_analysis.return_value = (
        False,
        "Concept already has profile",
    )

    # Mock successful copy
    mock_skip_logic.copy_profiler_analysis.return_value = {
        "app_name": "CopiedApp",
        "core_functions": ["copied1", "copied2"],
        "copied_from_primary": True,
    }

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(valid_submission)

    # Should NOT call profiler
    mock_profiler.generate_app_profile.assert_not_called()

    # Should copy from primary
    mock_skip_logic.copy_profiler_analysis.assert_called_once()

    # Check result is copied profile
    assert result["app_name"] == "CopiedApp"
    assert result["copied_from_primary"] is True

    # Check statistics
    assert service.stats["copied"] == 1
    assert service.stats["analyzed"] == 0


def test_enrich_skip_but_copy_fails(mock_profiler, mock_skip_logic, valid_submission):
    """Test skipping but copy fails, returns empty dict."""
    valid_submission["business_concept_id"] = 1

    # Mock skip logic to return False (should skip)
    mock_skip_logic.should_run_profiler_analysis.return_value = (
        False,
        "Concept already has profile",
    )

    # Mock failed copy (returns None)
    mock_skip_logic.copy_profiler_analysis.return_value = None

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(valid_submission)

    # Should NOT call profiler
    mock_profiler.generate_app_profile.assert_not_called()

    # Should return empty dict
    assert result == {}

    # Check statistics
    assert service.stats["skipped"] == 1
    assert service.stats["copied"] == 0
    assert service.stats["analyzed"] == 0


def test_enrich_with_deduplication_disabled(mock_profiler, mock_skip_logic, valid_submission):
    """Test enrichment with deduplication disabled."""
    valid_submission["business_concept_id"] = 1

    config = {"enable_deduplication": False}
    service = ProfilerService(mock_profiler, mock_skip_logic, config=config)

    result = service.enrich(valid_submission)

    # Should NOT check skip logic
    mock_skip_logic.should_run_profiler_analysis.assert_not_called()

    # Should call profiler directly
    mock_profiler.generate_app_profile.assert_called_once()

    assert result["app_name"] == "TestApp"
    assert service.stats["analyzed"] == 1


def test_enrich_with_agno_analysis(mock_profiler, mock_skip_logic, valid_submission):
    """Test enrichment with Agno analysis evidence."""
    valid_submission["agno_analysis"] = {
        "willingness_to_pay_score": 85.0,
        "customer_segment": "B2B SaaS",
    }

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(valid_submission)

    # Check profiler was called with agno_analysis
    call_args = mock_profiler.generate_app_profile.call_args
    assert call_args[1]["agno_analysis"] is not None
    assert result["app_name"] == "TestApp"


# ===========================
# Validation Tests
# ===========================


def test_enrich_invalid_submission_missing_id(mock_profiler, mock_skip_logic):
    """Test enrichment with missing submission_id."""
    invalid_submission = {"title": "Test", "text": "Content", "subreddit": "test"}

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(invalid_submission)

    # Should return empty dict
    assert result == {}
    # Should increment errors
    assert service.stats["errors"] == 1
    # Should not call profiler
    mock_profiler.generate_app_profile.assert_not_called()


def test_enrich_invalid_submission_missing_text(mock_profiler, mock_skip_logic):
    """Test enrichment with missing text/content."""
    invalid_submission = {
        "submission_id": "sub123",
        "title": "Test",
        "subreddit": "test",
    }

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(invalid_submission)

    # Should return empty dict
    assert result == {}
    # Should increment errors
    assert service.stats["errors"] == 1


def test_validate_input_accepts_content_field(mock_profiler, mock_skip_logic):
    """Test that validate_input accepts 'content' field instead of 'text'."""
    submission = {
        "submission_id": "sub123",
        "title": "Test",
        "content": "This is content",  # Using 'content' instead of 'text'
        "subreddit": "test",
    }

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(submission)

    # Should not be an error
    assert result != {}
    assert service.stats["errors"] == 0


def test_validate_input_requires_either_text_or_content(mock_profiler, mock_skip_logic):
    """Test that validation requires either text or content field."""
    submission_no_content = {
        "submission_id": "sub123",
        "title": "Test",
        "subreddit": "test",
        # No text or content field
    }

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(submission_no_content)

    assert result == {}
    assert service.stats["errors"] == 1


# ===========================
# Error Handling Tests
# ===========================


def test_enrich_profiler_raises_exception(mock_profiler, mock_skip_logic, valid_submission):
    """Test error handling when profiler raises exception."""
    mock_profiler.generate_app_profile.side_effect = Exception("Profiler error")

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(valid_submission)

    # Should return empty dict
    assert result == {}
    # Should increment errors
    assert service.stats["errors"] == 1


def test_enrich_skip_logic_raises_exception(mock_profiler, mock_skip_logic, valid_submission):
    """Test error handling when skip logic raises exception."""
    valid_submission["business_concept_id"] = 1
    mock_skip_logic.should_run_profiler_analysis.side_effect = Exception("Skip logic error")

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(valid_submission)

    # Should return empty dict
    assert result == {}
    # Should increment errors
    assert service.stats["errors"] == 1


def test_enrich_copy_raises_exception(mock_profiler, mock_skip_logic, valid_submission):
    """Test error handling when copy operation raises exception."""
    valid_submission["business_concept_id"] = 1
    mock_skip_logic.should_run_profiler_analysis.return_value = (
        False,
        "Should skip",
    )
    mock_skip_logic.copy_profiler_analysis.side_effect = Exception("Copy error")

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service.enrich(valid_submission)

    # Should return empty dict
    assert result == {}
    # Should not crash
    assert service.stats["errors"] == 1


# ===========================
# _generate_profile() Tests
# ===========================


def test_generate_profile_uses_correct_fields(mock_profiler, mock_skip_logic):
    """Test that _generate_profile extracts correct fields."""
    submission = {
        "submission_id": "sub123",
        "title": "Test Title",
        "text": "Test Content",
        "subreddit": "test",
        "score": 80,
        "agno_analysis": {"wtp": 85},
    }

    service = ProfilerService(mock_profiler, mock_skip_logic)
    service._generate_profile(submission)

    # Check profiler was called with correct arguments
    call_args = mock_profiler.generate_app_profile.call_args
    assert call_args[1]["text"] == "Test Content"
    assert call_args[1]["title"] == "Test Title"
    assert call_args[1]["subreddit"] == "test"
    assert call_args[1]["score"] == 80
    assert call_args[1]["agno_analysis"] == {"wtp": 85}


def test_generate_profile_defaults_score(mock_profiler, mock_skip_logic):
    """Test that _generate_profile defaults score to 50 if missing."""
    submission = {
        "submission_id": "sub123",
        "title": "Test",
        "text": "Content",
        "subreddit": "test",
        # No score field
    }

    service = ProfilerService(mock_profiler, mock_skip_logic)
    service._generate_profile(submission)

    # Check profiler was called with default score 50
    call_args = mock_profiler.generate_app_profile.call_args
    assert call_args[1]["score"] == 50


def test_generate_profile_adds_metadata(mock_profiler, mock_skip_logic, valid_submission):
    """Test that _generate_profile adds submission metadata."""
    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service._generate_profile(valid_submission)

    # Check metadata added
    assert result["submission_id"] == "sub123"
    assert result["opportunity_id"] == "opp_sub123"


def test_generate_profile_handles_profiler_error(mock_profiler, mock_skip_logic, valid_submission):
    """Test that _generate_profile handles profiler errors."""
    mock_profiler.generate_app_profile.side_effect = Exception("Profiler error")

    service = ProfilerService(mock_profiler, mock_skip_logic)
    result = service._generate_profile(valid_submission)

    # Should return empty dict
    assert result == {}


# ===========================
# _get_primary_submission_id() Tests
# ===========================


def test_get_primary_submission_id_success(mock_profiler, mock_skip_logic):
    """Test getting primary submission ID successfully."""
    service = ProfilerService(mock_profiler, mock_skip_logic)
    primary_id = service._get_primary_submission_id(1)

    # Check concept manager was called
    mock_skip_logic.concept_manager.get_concept_by_id.assert_called_once_with(1)

    assert primary_id == "primary_sub123"


def test_get_primary_submission_id_not_found(mock_profiler, mock_skip_logic):
    """Test getting primary submission ID when concept not found."""
    mock_skip_logic.concept_manager.get_concept_by_id.return_value = None

    service = ProfilerService(mock_profiler, mock_skip_logic)
    primary_id = service._get_primary_submission_id(999)

    assert primary_id is None


def test_get_primary_submission_id_error(mock_profiler, mock_skip_logic):
    """Test getting primary submission ID when error occurs."""
    mock_skip_logic.concept_manager.get_concept_by_id.side_effect = Exception("DB error")

    service = ProfilerService(mock_profiler, mock_skip_logic)
    primary_id = service._get_primary_submission_id(1)

    # Should return None on error
    assert primary_id is None


# ===========================
# get_service_name() Tests
# ===========================


def test_get_service_name(mock_profiler, mock_skip_logic):
    """Test get_service_name returns correct name."""
    service = ProfilerService(mock_profiler, mock_skip_logic)
    assert service.get_service_name() == "ProfilerService"


# ===========================
# Statistics Tests
# ===========================


def test_statistics_tracking(mock_profiler, mock_skip_logic):
    """Test statistics tracking across multiple enrichments."""
    service = ProfilerService(mock_profiler, mock_skip_logic)

    # Fresh analysis
    service.enrich({
        "submission_id": "sub1",
        "title": "Test 1",
        "text": "Content 1",
        "subreddit": "test",
    })

    assert service.stats["analyzed"] == 1

    # Invalid submission
    service.enrich({"title": "Invalid"})
    assert service.stats["errors"] == 1

    # Check final stats
    stats = service.get_statistics()
    assert stats["analyzed"] == 1
    assert stats["errors"] == 1
    assert stats["skipped"] == 0
    assert stats["copied"] == 0


# ===========================
# Integration Tests
# ===========================


def test_full_workflow_with_deduplication(mock_profiler, mock_skip_logic):
    """Test complete workflow with deduplication."""
    service = ProfilerService(mock_profiler, mock_skip_logic)

    # First submission (fresh)
    sub1 = {
        "submission_id": "sub1",
        "title": "Test 1",
        "text": "Content 1",
        "subreddit": "test",
        "business_concept_id": 1,
    }
    result1 = service.enrich(sub1)
    assert result1["app_name"] == "TestApp"
    assert service.stats["analyzed"] == 1

    # Second submission (duplicate - should skip)
    mock_skip_logic.should_run_profiler_analysis.return_value = (False, "Duplicate")
    mock_skip_logic.copy_profiler_analysis.return_value = {
        "app_name": "CopiedApp",
        "copied_from_primary": True,
    }

    sub2 = {
        "submission_id": "sub2",
        "title": "Test 2",
        "text": "Content 2",
        "subreddit": "test",
        "business_concept_id": 1,
    }
    result2 = service.enrich(sub2)
    assert result2["app_name"] == "CopiedApp"
    assert service.stats["copied"] == 1

    # Check final statistics
    stats = service.get_statistics()
    assert stats["analyzed"] == 1
    assert stats["copied"] == 1
    assert stats["skipped"] == 0
    assert stats["errors"] == 0


def test_reset_and_reuse(mock_profiler, mock_skip_logic, valid_submission):
    """Test resetting statistics and reusing service."""
    service = ProfilerService(mock_profiler, mock_skip_logic)

    # First batch
    service.enrich(valid_submission)
    assert service.stats["analyzed"] == 1

    # Reset
    service.reset_statistics()
    assert service.stats["analyzed"] == 0

    # Second batch
    service.enrich(valid_submission)
    assert service.stats["analyzed"] == 1
