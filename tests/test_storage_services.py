"""Tests for storage services (OpportunityStore, ProfileStore, HybridStore)."""

import pytest
from unittest.mock import MagicMock, patch
from core.storage import OpportunityStore, ProfileStore, HybridStore, DLTLoader
from core.dlt import PK_SUBMISSION_ID


# Fixtures


@pytest.fixture
def mock_loader():
    """Create a mock DLTLoader for testing."""
    loader = MagicMock(spec=DLTLoader)
    loader.load.return_value = True
    loader.load_batch.return_value = {
        "total_records": 10,
        "batches": 2,
        "successful_batches": 2,
        "failed_batches": 0,
        "success_rate": 1.0,
        "loaded": 10,
        "failed": 0,
    }
    return loader


@pytest.fixture
def sample_opportunities():
    """Sample opportunity data for testing."""
    return [
        {
            "submission_id": "opp1",
            "problem_description": "Teams waste 10 hours weekly",
            "app_concept": "Integrated PM platform",
            "core_functions": ["Time tracking", "Gantt charts"],
            "value_proposition": "Save 10 hours/week",
            "target_user": "Small teams",
            "monetization_model": "Subscription",
            "opportunity_score": 75.0,
        },
        {
            "submission_id": "opp2",
            "problem_description": "Developers struggle with debugging",
            "app_concept": "AI debugging assistant",
            "core_functions": ["Error analysis", "Fix suggestions"],
            "value_proposition": "Fix bugs 3x faster",
            "target_user": "Software developers",
            "monetization_model": "Freemium",
            "opportunity_score": 82.5,
        },
    ]


@pytest.fixture
def sample_profiles():
    """Sample profile data for testing."""
    return [
        {
            "submission_id": "prof1",
            "title": "Looking for feedback on my idea",
            "selftext": "I want to build a project management tool",
            "author": "user123",
            "subreddit": "Entrepreneur",
            "trust_score": 85.5,
            "opportunity_score": 75.0,
        },
        {
            "submission_id": "prof2",
            "title": "Need help with debugging",
            "selftext": "Debugging is taking too much time",
            "author": "user456",
            "subreddit": "programming",
            "trust_score": 78.2,
            "opportunity_score": 82.5,
        },
    ]


@pytest.fixture
def sample_hybrid_submissions():
    """Sample hybrid submission data for testing."""
    return [
        {
            "submission_id": "hybrid1",
            # Opportunity fields
            "problem_description": "Teams waste 10 hours weekly",
            "app_concept": "Integrated PM platform",
            "core_functions": ["Time tracking", "Gantt charts"],
            "value_proposition": "Save 10 hours/week",
            "target_user": "Small teams",
            "monetization_model": "Subscription",
            "opportunity_score": 75.0,
            # Profile fields
            "title": "Looking for feedback on my idea",
            "selftext": "I want to build...",
            "author": "user123",
            "subreddit": "Entrepreneur",
            "trust_score": 85.5,
        },
        {
            "submission_id": "hybrid2",
            # Opportunity fields
            "problem_description": "Developers struggle with debugging",
            "app_concept": "AI debugging assistant",
            "core_functions": ["Error analysis", "Fix suggestions"],
            "value_proposition": "Fix bugs 3x faster",
            "target_user": "Software developers",
            "monetization_model": "Freemium",
            "opportunity_score": 82.5,
            # Profile fields
            "title": "Need help with debugging",
            "selftext": "Debugging is taking too much time",
            "author": "user456",
            "subreddit": "programming",
            "trust_score": 78.2,
        },
    ]


# OpportunityStore Tests


def test_opportunity_store_initialization_default(mock_loader):
    """Test OpportunityStore initialization with defaults."""
    store = OpportunityStore(loader=mock_loader)

    assert store.loader == mock_loader
    assert store.table_name == "app_opportunities"
    assert store.primary_key == PK_SUBMISSION_ID
    assert store.stats.loaded == 0
    assert store.stats.failed == 0


def test_opportunity_store_initialization_custom(mock_loader):
    """Test OpportunityStore initialization with custom table."""
    store = OpportunityStore(loader=mock_loader, table_name="custom_opportunities")

    assert store.table_name == "custom_opportunities"
    assert store.primary_key == PK_SUBMISSION_ID


def test_opportunity_store_initialization_no_loader():
    """Test OpportunityStore creates loader if not provided."""
    store = OpportunityStore()

    assert isinstance(store.loader, DLTLoader)
    assert store.table_name == "app_opportunities"


def test_opportunity_store_successful(mock_loader, sample_opportunities):
    """Test successful opportunity storage."""
    store = OpportunityStore(loader=mock_loader)

    success = store.store(sample_opportunities)

    assert success is True
    mock_loader.load.assert_called_once_with(
        data=sample_opportunities,
        table_name="app_opportunities",
        write_disposition="merge",
        primary_key=PK_SUBMISSION_ID,
    )
    assert store.stats.loaded == 2
    assert store.stats.total_attempted == 2


def test_opportunity_store_empty_data(mock_loader):
    """Test OpportunityStore with empty data."""
    store = OpportunityStore(loader=mock_loader)

    success = store.store([])

    assert success is False
    mock_loader.load.assert_not_called()


def test_opportunity_store_filters_invalid(mock_loader):
    """Test OpportunityStore filters opportunities without problem_description."""
    store = OpportunityStore(loader=mock_loader)

    invalid_data = [
        {"submission_id": "opp1"},  # Missing problem_description
        {"submission_id": "opp2", "problem_description": None},  # None problem_description
    ]

    success = store.store(invalid_data)

    assert success is False
    mock_loader.load.assert_not_called()
    assert store.stats.skipped == 2


def test_opportunity_store_filters_partial(mock_loader, sample_opportunities):
    """Test OpportunityStore filters invalid and stores valid."""
    store = OpportunityStore(loader=mock_loader)

    mixed_data = sample_opportunities + [{"submission_id": "invalid"}]

    success = store.store(mixed_data)

    assert success is True
    mock_loader.load.assert_called_once()
    # Should only load the 2 valid opportunities
    call_args = mock_loader.load.call_args
    assert len(call_args.kwargs["data"]) == 2
    assert store.stats.loaded == 2
    assert store.stats.skipped == 1


def test_opportunity_store_load_failure(mock_loader, sample_opportunities):
    """Test OpportunityStore handles load failure."""
    mock_loader.load.return_value = False
    store = OpportunityStore(loader=mock_loader)

    success = store.store(sample_opportunities)

    assert success is False
    assert store.stats.failed == 2
    assert store.stats.loaded == 0
    assert len(store.stats.errors) == 1


def test_opportunity_store_batch_success(mock_loader, sample_opportunities):
    """Test OpportunityStore batch storage."""
    store = OpportunityStore(loader=mock_loader)

    result = store.store_batch(sample_opportunities, batch_size=1)

    assert result["total_records"] == 10
    assert result["batches"] == 2
    assert result["success_rate"] == 1.0
    mock_loader.load_batch.assert_called_once()


def test_opportunity_store_batch_empty(mock_loader):
    """Test OpportunityStore batch with empty data."""
    store = OpportunityStore(loader=mock_loader)

    result = store.store_batch([])

    assert result["total_records"] == 0
    assert result["batches"] == 0
    mock_loader.load_batch.assert_not_called()


def test_opportunity_store_statistics(mock_loader, sample_opportunities):
    """Test OpportunityStore statistics tracking."""
    store = OpportunityStore(loader=mock_loader)

    store.store(sample_opportunities)
    stats = store.get_statistics()

    assert stats["loaded"] == 2
    assert stats["failed"] == 0
    assert stats["total_attempted"] == 2
    assert stats["success_rate"] == 1.0


def test_opportunity_store_reset_statistics(mock_loader, sample_opportunities):
    """Test OpportunityStore statistics reset."""
    store = OpportunityStore(loader=mock_loader)

    store.store(sample_opportunities)
    assert store.stats.loaded == 2

    store.reset_statistics()
    assert store.stats.loaded == 0
    assert store.stats.failed == 0


# ProfileStore Tests


def test_profile_store_initialization_default(mock_loader):
    """Test ProfileStore initialization with defaults."""
    store = ProfileStore(loader=mock_loader)

    assert store.loader == mock_loader
    assert store.table_name == "submissions"
    assert store.primary_key == PK_SUBMISSION_ID


def test_profile_store_initialization_custom(mock_loader):
    """Test ProfileStore initialization with custom table."""
    store = ProfileStore(loader=mock_loader, table_name="custom_profiles")

    assert store.table_name == "custom_profiles"


def test_profile_store_successful(mock_loader, sample_profiles):
    """Test successful profile storage."""
    store = ProfileStore(loader=mock_loader)

    success = store.store(sample_profiles)

    assert success is True
    mock_loader.load.assert_called_once_with(
        data=sample_profiles,
        table_name="submissions",
        write_disposition="merge",
        primary_key=PK_SUBMISSION_ID,
    )
    assert store.stats.loaded == 2


def test_profile_store_empty_data(mock_loader):
    """Test ProfileStore with empty data."""
    store = ProfileStore(loader=mock_loader)

    success = store.store([])

    assert success is False
    mock_loader.load.assert_not_called()


def test_profile_store_filters_invalid(mock_loader):
    """Test ProfileStore filters profiles without submission_id."""
    store = ProfileStore(loader=mock_loader)

    invalid_data = [
        {"title": "Test"},  # Missing submission_id
        {"submission_id": None, "title": "Test"},  # None submission_id
    ]

    success = store.store(invalid_data)

    assert success is False
    mock_loader.load.assert_not_called()
    assert store.stats.skipped == 2


def test_profile_store_batch_success(mock_loader, sample_profiles):
    """Test ProfileStore batch storage."""
    store = ProfileStore(loader=mock_loader)

    result = store.store_batch(sample_profiles, batch_size=1)

    assert result["total_records"] == 10
    assert result["batches"] == 2
    mock_loader.load_batch.assert_called_once()


def test_profile_store_load_failure(mock_loader, sample_profiles):
    """Test ProfileStore handles load failure."""
    mock_loader.load.return_value = False
    store = ProfileStore(loader=mock_loader)

    success = store.store(sample_profiles)

    assert success is False
    assert store.stats.failed == 2
    assert len(store.stats.errors) == 1


def test_profile_store_statistics(mock_loader, sample_profiles):
    """Test ProfileStore statistics tracking."""
    store = ProfileStore(loader=mock_loader)

    store.store(sample_profiles)
    stats = store.get_statistics()

    assert stats["loaded"] == 2
    assert stats["success_rate"] == 1.0


# HybridStore Tests


def test_hybrid_store_initialization_default(mock_loader):
    """Test HybridStore initialization with defaults."""
    store = HybridStore(loader=mock_loader)

    assert store.loader == mock_loader
    assert store.opportunity_table == "app_opportunities"
    assert store.profile_table == "submissions"
    assert store.primary_key == PK_SUBMISSION_ID


def test_hybrid_store_initialization_custom(mock_loader):
    """Test HybridStore initialization with custom tables."""
    store = HybridStore(
        loader=mock_loader,
        opportunity_table="custom_opps",
        profile_table="custom_profiles",
    )

    assert store.opportunity_table == "custom_opps"
    assert store.profile_table == "custom_profiles"


def test_hybrid_store_successful(mock_loader, sample_hybrid_submissions):
    """Test successful hybrid storage."""
    store = HybridStore(loader=mock_loader)

    success = store.store(sample_hybrid_submissions)

    assert success is True
    # Should call load twice (opportunities and profiles)
    assert mock_loader.load.call_count == 2
    assert store.stats.loaded == 2


def test_hybrid_store_empty_data(mock_loader):
    """Test HybridStore with empty data."""
    store = HybridStore(loader=mock_loader)

    success = store.store([])

    assert success is False
    mock_loader.load.assert_not_called()


def test_hybrid_store_filters_invalid_submission_id(mock_loader):
    """Test HybridStore filters submissions without submission_id."""
    store = HybridStore(loader=mock_loader)

    invalid_data = [
        {"title": "Test"},  # Missing submission_id
        {"submission_id": None, "title": "Test"},  # None submission_id
    ]

    success = store.store(invalid_data)

    # Should skip invalid but still return True if loader calls succeed
    # Since all are invalid, no loader calls should happen
    assert mock_loader.load.call_count == 0
    assert store.stats.skipped == 2


def test_hybrid_store_splits_data_correctly(mock_loader, sample_hybrid_submissions):
    """Test HybridStore splits data into opportunity and profile components."""
    store = HybridStore(loader=mock_loader)

    store.store(sample_hybrid_submissions)

    # Check first call (opportunities)
    first_call = mock_loader.load.call_args_list[0]
    assert first_call.kwargs["table_name"] == "app_opportunities"
    assert len(first_call.kwargs["data"]) == 2
    assert "problem_description" in first_call.kwargs["data"][0]

    # Check second call (profiles)
    second_call = mock_loader.load.call_args_list[1]
    assert second_call.kwargs["table_name"] == "submissions"
    assert len(second_call.kwargs["data"]) == 2
    assert "title" in second_call.kwargs["data"][0]


def test_hybrid_store_partial_failure(mock_loader, sample_hybrid_submissions):
    """Test HybridStore when one storage operation fails."""
    # First call succeeds, second call fails
    mock_loader.load.side_effect = [True, False]
    store = HybridStore(loader=mock_loader)

    success = store.store(sample_hybrid_submissions)

    assert success is False  # Overall failure
    assert mock_loader.load.call_count == 2
    assert store.stats.failed == 2
    assert len(store.stats.errors) == 1


def test_hybrid_store_complete_failure(mock_loader, sample_hybrid_submissions):
    """Test HybridStore when both storage operations fail."""
    mock_loader.load.return_value = False
    store = HybridStore(loader=mock_loader)

    success = store.store(sample_hybrid_submissions)

    assert success is False
    assert mock_loader.load.call_count == 2
    assert store.stats.failed == 2
    assert len(store.stats.errors) == 2


def test_hybrid_store_batch_success(mock_loader, sample_hybrid_submissions):
    """Test HybridStore batch storage."""
    store = HybridStore(loader=mock_loader)

    result = store.store_batch(sample_hybrid_submissions, batch_size=1)

    assert result["total_records"] == 2
    assert result["batches"] == 2
    assert result["successful_batches"] == 2
    assert result["success_rate"] == 1.0


def test_hybrid_store_batch_empty(mock_loader):
    """Test HybridStore batch with empty data."""
    store = HybridStore(loader=mock_loader)

    result = store.store_batch([])

    assert result["total_records"] == 0
    assert result["batches"] == 0


def test_hybrid_store_batch_partial_failure(mock_loader, sample_hybrid_submissions):
    """Test HybridStore batch with some batch failures."""
    # First batch succeeds, second batch fails
    mock_loader.load.side_effect = [True, True, True, False]
    store = HybridStore(loader=mock_loader)

    result = store.store_batch(sample_hybrid_submissions, batch_size=1)

    assert result["successful_batches"] == 1
    assert result["failed_batches"] == 1
    assert result["success_rate"] == 0.5


def test_hybrid_store_statistics(mock_loader, sample_hybrid_submissions):
    """Test HybridStore statistics tracking."""
    store = HybridStore(loader=mock_loader)

    store.store(sample_hybrid_submissions)
    stats = store.get_statistics()

    assert stats["loaded"] == 2
    assert stats["success_rate"] == 1.0


def test_hybrid_store_only_profiles_no_opportunities(mock_loader):
    """Test HybridStore with submissions that have no opportunity data."""
    store = HybridStore(loader=mock_loader)

    # Submissions without problem_description (no opportunity data)
    profile_only_data = [
        {
            "submission_id": "prof_only1",
            "title": "Just a discussion",
            "author": "user789",
            "subreddit": "general",
        }
    ]

    success = store.store(profile_only_data)

    # Should still succeed, just storing profiles
    assert success is True
    # Should only call load once (for profiles)
    assert mock_loader.load.call_count == 1
    assert mock_loader.load.call_args.kwargs["table_name"] == "submissions"


# Integration Tests


def test_all_stores_with_same_loader(sample_opportunities, sample_profiles, sample_hybrid_submissions):
    """Test all three stores can share the same DLTLoader."""
    loader = MagicMock(spec=DLTLoader)
    loader.load.return_value = True

    opp_store = OpportunityStore(loader=loader)
    profile_store = ProfileStore(loader=loader)
    hybrid_store = HybridStore(loader=loader)

    opp_store.store(sample_opportunities)
    profile_store.store(sample_profiles)
    hybrid_store.store(sample_hybrid_submissions)

    # All stores should use the same loader instance
    assert opp_store.loader == profile_store.loader == hybrid_store.loader
    # Loader should be called multiple times
    assert loader.load.call_count == 4  # 1 + 1 + 2 (hybrid calls twice)
