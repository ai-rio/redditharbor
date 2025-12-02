"""Tests for DatabaseFetcher class.

This test suite ensures 100% coverage of the database_fetcher module,
testing all fetching methods, deduplication logic, and edge cases.
"""

from unittest.mock import MagicMock, Mock

import pytest

from core.fetchers.database_fetcher import DatabaseFetcher


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def mock_supabase_client():
    """Create mock Supabase client for testing."""
    return MagicMock()


@pytest.fixture
def sample_submissions():
    """Sample submission data from database."""
    return [
        {
            "submission_id": "sub1",
            "title": "Problem with my workflow",
            "problem_description": "It's frustrating",
            "subreddit": "SaaS",
            "reddit_score": 50,
            "num_comments": 10,
            "trust_score": 85.0,
            "trust_badge": "GOLD",
            "activity_score": 30.0,
        },
        {
            "submission_id": "sub2",
            "title": "Issue with automation",
            "problem_description": "Need better tools",
            "subreddit": "productivity",
            "reddit_score": 25,
            "num_comments": 5,
            "trust_score": 70.0,
            "trust_badge": "SILVER",
            "activity_score": 20.0,
        },
    ]


@pytest.fixture
def duplicate_submissions():
    """Submissions with duplicate titles (for deduplication testing)."""
    return [
        {
            "submission_id": "sub1",
            "title": "I have a problem with my workflow",
            "problem_description": "First post",
            "subreddit": "SaaS",
            "reddit_score": 50,
            "num_comments": 10,
        },
        {
            "submission_id": "sub2",
            "title": "I have a problem with my workflow",  # Exact duplicate
            "problem_description": "Second post (cross-post)",
            "subreddit": "productivity",
            "reddit_score": 25,
            "num_comments": 5,
        },
        {
            "submission_id": "sub3",
            "title": "Problem with workflow",  # Similar (filler words removed)
            "problem_description": "Third post",
            "subreddit": "startups",
            "reddit_score": 30,
            "num_comments": 3,
        },
    ]


# ===========================
# Initialization Tests
# ===========================


def test_init_with_defaults(mock_supabase_client):
    """Test initialization with default configuration."""
    fetcher = DatabaseFetcher(mock_supabase_client)

    assert fetcher.client == mock_supabase_client
    assert fetcher.batch_size == 1000
    assert fetcher.deduplicate is True
    assert fetcher.table_name == "app_opportunities"
    assert fetcher.stats == {"fetched": 0, "filtered": 0, "errors": 0}


def test_init_with_custom_config(mock_supabase_client):
    """Test initialization with custom configuration."""
    config = {"batch_size": 500, "deduplicate": False, "table_name": "custom_table"}
    fetcher = DatabaseFetcher(mock_supabase_client, config=config)

    assert fetcher.batch_size == 500
    assert fetcher.deduplicate is False
    assert fetcher.table_name == "custom_table"


def test_init_inherits_from_base_fetcher(mock_supabase_client):
    """Test that DatabaseFetcher inherits BaseFetcher functionality."""
    fetcher = DatabaseFetcher(mock_supabase_client)

    # Should have methods from BaseFetcher
    assert hasattr(fetcher, "get_statistics")
    assert hasattr(fetcher, "reset_statistics")
    assert hasattr(fetcher, "validate_submission")


# ===========================
# fetch() Method Tests
# ===========================


def test_fetch_limited(mock_supabase_client, sample_submissions):
    """Test fetching with limit parameter."""
    # Setup mock response
    mock_response = Mock()
    mock_response.data = sample_submissions
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client)
    results = list(fetcher.fetch(limit=2))

    # Check results
    assert len(results) == 2
    assert results[0]["id"] == "sub1"
    assert results[1]["id"] == "sub2"

    # Check statistics
    stats = fetcher.get_statistics()
    assert stats["fetched"] == 2
    assert stats["filtered"] == 0
    assert stats["errors"] == 0


def test_fetch_limited_empty_response(mock_supabase_client):
    """Test fetching with limit when no data is returned."""
    # Setup mock empty response
    mock_response = Mock()
    mock_response.data = []
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client)
    results = list(fetcher.fetch(limit=10))

    assert len(results) == 0
    assert fetcher.stats["fetched"] == 0


def test_fetch_all_with_single_batch(mock_supabase_client, sample_submissions):
    """Test fetching all submissions (single batch)."""
    # Setup mock response - single batch
    mock_response = Mock()
    mock_response.data = sample_submissions
    mock_supabase_client.table.return_value.select.return_value.range.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client, config={"batch_size": 1000})
    results = list(fetcher.fetch())  # No limit = fetch all

    assert len(results) == 2
    assert fetcher.stats["fetched"] == 2


def test_fetch_all_with_multiple_batches(mock_supabase_client):
    """Test fetching all submissions across multiple batches."""
    # Create data for 3 batches
    batch1 = [
        {"submission_id": f"sub{i}", "title": f"Title {i}", "subreddit": "test"}
        for i in range(5)
    ]
    batch2 = [
        {"submission_id": f"sub{i}", "title": f"Title {i}", "subreddit": "test"}
        for i in range(5, 8)
    ]
    batch3 = []  # Empty batch signals end

    # Setup mock to return different batches
    mock_response1 = Mock()
    mock_response1.data = batch1
    mock_response2 = Mock()
    mock_response2.data = batch2
    mock_response3 = Mock()
    mock_response3.data = batch3

    mock_supabase_client.table.return_value.select.return_value.range.return_value.execute.side_effect = [
        mock_response1,
        mock_response2,
        mock_response3,
    ]

    fetcher = DatabaseFetcher(mock_supabase_client, config={"batch_size": 5})
    results = list(fetcher.fetch())

    assert len(results) == 8  # 5 + 3 from two batches
    assert fetcher.stats["fetched"] == 8


# ===========================
# Deduplication Tests
# ===========================


def test_deduplication_enabled(mock_supabase_client, duplicate_submissions):
    """Test content-based deduplication when enabled."""
    mock_response = Mock()
    mock_response.data = duplicate_submissions
    mock_supabase_client.table.return_value.select.return_value.range.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client, config={"deduplicate": True})
    results = list(fetcher.fetch())

    # Should keep only unique title signatures
    # "I have a problem with my workflow" and "Problem with workflow"
    # both have same signature after filler word removal
    assert len(results) == 1  # Only first unique submission
    assert results[0]["id"] == "sub1"
    assert fetcher.stats["filtered"] == 2  # 2 duplicates filtered


def test_deduplication_disabled(mock_supabase_client, duplicate_submissions):
    """Test fetching with deduplication disabled."""
    mock_response = Mock()
    mock_response.data = duplicate_submissions
    mock_supabase_client.table.return_value.select.return_value.range.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client, config={"deduplicate": False})
    results = list(fetcher.fetch())

    # All submissions should be included
    assert len(results) == 3
    assert fetcher.stats["fetched"] == 3
    assert fetcher.stats["filtered"] == 0


def test_is_duplicate_exact_match():
    """Test duplicate detection with exact title match."""
    from core.fetchers.database_fetcher import DatabaseFetcher

    seen_titles = set()
    submission1 = {"title": "I have a problem"}
    submission2 = {"title": "I have a problem"}  # Exact duplicate

    fetcher = DatabaseFetcher(MagicMock())

    # First submission is not a duplicate
    assert not fetcher._is_duplicate(submission1, seen_titles)

    # Second submission IS a duplicate
    assert fetcher._is_duplicate(submission2, seen_titles)


def test_is_duplicate_filler_words_removed():
    """Test that filler words are removed when checking for duplicates."""
    from core.fetchers.database_fetcher import DatabaseFetcher

    seen_titles = set()
    submission1 = {"title": "I have a problem with my workflow"}
    submission2 = {"title": "problem workflow"}  # Same after removing filler words

    fetcher = DatabaseFetcher(MagicMock())

    assert not fetcher._is_duplicate(submission1, seen_titles)
    assert fetcher._is_duplicate(submission2, seen_titles)


# ===========================
# Validation Tests
# ===========================


def test_validate_submission_valid():
    """Test validation with valid submission."""
    fetcher = DatabaseFetcher(MagicMock())
    submission = {"submission_id": "abc123", "title": "Test", "subreddit": "test"}

    assert fetcher.validate_submission(submission) is True


def test_validate_submission_missing_fields():
    """Test validation with missing required fields."""
    fetcher = DatabaseFetcher(MagicMock())

    # Missing title
    assert fetcher.validate_submission({"submission_id": "abc123", "subreddit": "test"}) is False

    # Missing subreddit
    assert fetcher.validate_submission({"submission_id": "abc123", "title": "Test"}) is False

    # Missing submission_id
    assert fetcher.validate_submission({"title": "Test", "subreddit": "test"}) is False


def test_validate_submission_empty_values():
    """Test validation with empty field values."""
    fetcher = DatabaseFetcher(MagicMock())
    submission = {"submission_id": "", "title": "Test", "subreddit": "test"}

    # Empty submission_id should fail validation
    assert fetcher.validate_submission(submission) is False


def test_fetch_filters_invalid_submissions(mock_supabase_client):
    """Test that invalid submissions are filtered out."""
    invalid_submissions = [
        {"submission_id": "sub1", "title": "Valid", "subreddit": "test"},
        {"submission_id": "", "title": "Invalid ID", "subreddit": "test"},
        {"submission_id": "sub3", "subreddit": "test"},  # Missing title
    ]

    mock_response = Mock()
    mock_response.data = invalid_submissions
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client)
    results = list(fetcher.fetch(limit=10))

    # Only 1 valid submission should be returned
    assert len(results) == 1
    assert results[0]["id"] == "sub1"
    assert fetcher.stats["fetched"] == 1
    assert fetcher.stats["filtered"] == 2


# ===========================
# Statistics Tests
# ===========================


def test_get_statistics(mock_supabase_client, sample_submissions):
    """Test statistics tracking."""
    mock_response = Mock()
    mock_response.data = sample_submissions
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client)
    list(fetcher.fetch(limit=2))

    stats = fetcher.get_statistics()
    assert stats["fetched"] == 2
    assert stats["filtered"] == 0
    assert stats["errors"] == 0


def test_reset_statistics(mock_supabase_client, sample_submissions):
    """Test resetting statistics."""
    mock_response = Mock()
    mock_response.data = sample_submissions
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client)
    list(fetcher.fetch(limit=2))

    assert fetcher.stats["fetched"] == 2

    fetcher.reset_statistics()
    assert fetcher.stats["fetched"] == 0
    assert fetcher.stats["filtered"] == 0
    assert fetcher.stats["errors"] == 0


# ===========================
# Source Name Tests
# ===========================


def test_get_source_name_default(mock_supabase_client):
    """Test source name with default table."""
    fetcher = DatabaseFetcher(mock_supabase_client)
    assert fetcher.get_source_name() == "Database (app_opportunities)"


def test_get_source_name_custom_table(mock_supabase_client):
    """Test source name with custom table."""
    fetcher = DatabaseFetcher(mock_supabase_client, config={"table_name": "custom_table"})
    assert fetcher.get_source_name() == "Database (custom_table)"


# ===========================
# Error Handling Tests
# ===========================


def test_fetch_limited_error_handling(mock_supabase_client):
    """Test error handling during limited fetch."""
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
        "Database connection failed"
    )

    fetcher = DatabaseFetcher(mock_supabase_client)

    with pytest.raises(Exception, match="Database fetch failed"):
        list(fetcher.fetch(limit=10))

    # Error is incremented in both _fetch_limited and fetch() wrapper
    assert fetcher.stats["errors"] >= 1


def test_fetch_all_error_handling(mock_supabase_client):
    """Test error handling during batch fetch."""
    mock_supabase_client.table.return_value.select.return_value.range.return_value.execute.side_effect = Exception(
        "Network error"
    )

    fetcher = DatabaseFetcher(mock_supabase_client)

    with pytest.raises(Exception, match="Database fetch failed"):
        list(fetcher.fetch())

    # Error is incremented in both _fetch_all and fetch() wrapper
    assert fetcher.stats["errors"] >= 1


def test_fetch_error_increments_error_count(mock_supabase_client):
    """Test that errors increment error count."""
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
        "Test error"
    )

    fetcher = DatabaseFetcher(mock_supabase_client)

    try:
        list(fetcher.fetch(limit=10))
    except Exception:
        pass

    # Error count should be incremented even if exception is raised
    assert fetcher.stats["errors"] >= 1


# ===========================
# Integration Tests
# ===========================


def test_fetch_uses_formatter(mock_supabase_client, sample_submissions):
    """Test that fetch() uses format_submission_for_agent()."""
    mock_response = Mock()
    mock_response.data = sample_submissions
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client)
    results = list(fetcher.fetch(limit=2))

    # Check that formatter was applied (formatted submissions have 'id' field)
    assert all("id" in result for result in results)
    assert all("text" in result for result in results)
    assert all("engagement" in result for result in results)


def test_fetch_preserves_trust_metadata(mock_supabase_client, sample_submissions):
    """Test that trust metadata is preserved in formatted output."""
    mock_response = Mock()
    mock_response.data = sample_submissions
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client)
    results = list(fetcher.fetch(limit=1))

    # Check trust metadata in comments field
    assert "Trust Score: 85.0" in results[0]["comments"]
    assert "Trust Badge: GOLD" in results[0]["comments"]


# ===========================
# Edge Cases
# ===========================


def test_fetch_with_none_values(mock_supabase_client):
    """Test fetching with None values in optional fields."""
    submissions_with_nones = [
        {
            "submission_id": "sub1",
            "title": "Test",
            "subreddit": "test",
            "problem_description": None,
            "reddit_score": None,
            "num_comments": None,
        }
    ]

    mock_response = Mock()
    mock_response.data = submissions_with_nones
    mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        mock_response
    )

    fetcher = DatabaseFetcher(mock_supabase_client)
    results = list(fetcher.fetch(limit=1))

    assert len(results) == 1
    assert results[0]["engagement"]["upvotes"] == 0  # None converted to 0


def test_filler_words_constant():
    """Test that FILLER_WORDS constant is properly defined."""
    from core.fetchers.database_fetcher import DatabaseFetcher

    assert "the" in DatabaseFetcher.FILLER_WORDS
    assert "a" in DatabaseFetcher.FILLER_WORDS
    assert "is" in DatabaseFetcher.FILLER_WORDS
    assert len(DatabaseFetcher.FILLER_WORDS) > 20  # Should have many filler words
