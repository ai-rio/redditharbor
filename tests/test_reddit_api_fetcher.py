"""Tests for RedditAPIFetcher class.

This test suite ensures 100% coverage of the reddit_api_fetcher module,
testing all fetching methods, keyword filtering, and integration with PRAW.
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from core.fetchers.reddit_api_fetcher import RedditAPIFetcher


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def mock_reddit_client():
    """Create mock PRAW Reddit client for testing."""
    return MagicMock()


@pytest.fixture
def mock_submission():
    """Create mock PRAW submission object."""
    submission = Mock()
    submission.id = "abc123"
    submission.title = "I have a problem with my workflow"
    submission.selftext = "It's really frustrating and difficult"
    submission.score = 50
    submission.num_comments = 10
    submission.url = "https://reddit.com/r/SaaS/comments/abc123"
    submission.created_utc = 1704067200
    return submission


@pytest.fixture
def mock_subreddit_with_submissions(mock_reddit_client, mock_submission):
    """Setup mock subreddit with submissions."""
    mock_subreddit = Mock()
    mock_subreddit.new.return_value = [mock_submission]
    mock_subreddit.hot.return_value = [mock_submission]
    mock_subreddit.top.return_value = [mock_submission]
    mock_subreddit.rising.return_value = [mock_submission]

    mock_reddit_client.subreddit.return_value = mock_subreddit
    return mock_subreddit


# ===========================
# Initialization Tests
# ===========================


def test_init_with_provided_client(mock_reddit_client):
    """Test initialization with provided PRAW client."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client)

    assert fetcher.client == mock_reddit_client
    assert fetcher.sort_type == "new"
    assert fetcher.filter_keywords is True
    assert fetcher.min_keywords == 1


def test_init_with_custom_config(mock_reddit_client):
    """Test initialization with custom configuration."""
    config = {"sort_type": "hot", "filter_keywords": False, "min_keywords": 2}
    fetcher = RedditAPIFetcher(client=mock_reddit_client, config=config)

    assert fetcher.sort_type == "hot"
    assert fetcher.filter_keywords is False
    assert fetcher.min_keywords == 2


def test_init_without_client_from_env():
    """Test initialization without client (creates from env vars)."""
    with patch.dict(
        os.environ,
        {
            "REDDIT_PUBLIC": "test_id",
            "REDDIT_SECRET": "test_secret",
            "REDDIT_USER_AGENT": "test_agent",
        },
    ):
        with patch("praw.Reddit") as mock_praw:
            fetcher = RedditAPIFetcher()

            # Should create client from env vars
            mock_praw.assert_called_once_with(
                client_id="test_id",
                client_secret="test_secret",
                user_agent="test_agent",
            )


def test_init_without_client_missing_credentials():
    """Test initialization without client and missing credentials."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Missing Reddit API credentials"):
            RedditAPIFetcher()


def test_init_inherits_from_base_fetcher(mock_reddit_client):
    """Test that RedditAPIFetcher inherits BaseFetcher functionality."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client)

    # Should have methods from BaseFetcher
    assert hasattr(fetcher, "get_statistics")
    assert hasattr(fetcher, "reset_statistics")
    assert hasattr(fetcher, "validate_submission")


# ===========================
# fetch() Method Tests
# ===========================


def test_fetch_single_subreddit(mock_reddit_client, mock_subreddit_with_submissions):
    """Test fetching from a single subreddit."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    results = list(fetcher.fetch(limit=10, subreddit="SaaS"))

    assert len(results) == 1
    assert results[0]["submission_id"] == "abc123"
    assert results[0]["title"] == "I have a problem with my workflow"


def test_fetch_multiple_subreddits(mock_reddit_client, mock_submission):
    """Test fetching from multiple subreddits."""
    # Setup mock for multiple subreddits
    mock_subreddit1 = Mock()
    mock_subreddit1.new.return_value = [mock_submission]
    mock_subreddit2 = Mock()
    mock_subreddit2.new.return_value = [mock_submission]

    def subreddit_side_effect(name):
        if name == "SaaS":
            return mock_subreddit1
        elif name == "startups":
            return mock_subreddit2

    mock_reddit_client.subreddit.side_effect = subreddit_side_effect

    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    results = list(fetcher.fetch(limit=10, subreddits=["SaaS", "startups"]))

    # Should get submissions from both subreddits
    assert len(results) == 2
    assert mock_reddit_client.subreddit.call_count == 2


def test_fetch_missing_subreddit_parameter(mock_reddit_client):
    """Test fetch without subreddit or subreddits parameter."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client)

    with pytest.raises(ValueError, match="Must provide either 'subreddit' or 'subreddits'"):
        list(fetcher.fetch(limit=10))


# ===========================
# Sort Type Tests
# ===========================


def test_fetch_sort_new(mock_reddit_client, mock_submission):
    """Test fetching with 'new' sort type."""
    mock_subreddit = Mock()
    mock_subreddit.new.return_value = [mock_submission]
    mock_reddit_client.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit_client, config={"sort_type": "new"})
    list(fetcher.fetch(limit=10, subreddit="SaaS"))

    mock_subreddit.new.assert_called_once_with(limit=10)


def test_fetch_sort_hot(mock_reddit_client, mock_submission):
    """Test fetching with 'hot' sort type."""
    mock_subreddit = Mock()
    mock_subreddit.hot.return_value = [mock_submission]
    mock_reddit_client.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit_client, config={"sort_type": "hot"})
    list(fetcher.fetch(limit=10, subreddit="SaaS"))

    mock_subreddit.hot.assert_called_once_with(limit=10)


def test_fetch_sort_top(mock_reddit_client, mock_submission):
    """Test fetching with 'top' sort type."""
    mock_subreddit = Mock()
    mock_subreddit.top.return_value = [mock_submission]
    mock_reddit_client.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit_client, config={"sort_type": "top"})
    list(fetcher.fetch(limit=10, subreddit="SaaS"))

    mock_subreddit.top.assert_called_once_with(limit=10)


def test_fetch_sort_rising(mock_reddit_client, mock_submission):
    """Test fetching with 'rising' sort type."""
    mock_subreddit = Mock()
    mock_subreddit.rising.return_value = [mock_submission]
    mock_reddit_client.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit_client, config={"sort_type": "rising"})
    list(fetcher.fetch(limit=10, subreddit="SaaS"))

    mock_subreddit.rising.assert_called_once_with(limit=10)


def test_fetch_unknown_sort_defaults_to_new(mock_reddit_client, mock_submission):
    """Test that unknown sort type defaults to 'new'."""
    mock_subreddit = Mock()
    mock_subreddit.new.return_value = [mock_submission]
    mock_reddit_client.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit_client, config={"sort_type": "unknown"})
    list(fetcher.fetch(limit=10, subreddit="SaaS"))

    # Should fall back to 'new'
    mock_subreddit.new.assert_called_once_with(limit=10)


# ===========================
# Keyword Filtering Tests
# ===========================


def test_filter_keywords_enabled():
    """Test keyword filtering when enabled (default)."""
    mock_reddit = MagicMock()
    mock_subreddit = Mock()

    # Create submissions with and without problem keywords
    sub_with_keywords = Mock()
    sub_with_keywords.id = "sub1"
    sub_with_keywords.title = "I have a problem with this"
    sub_with_keywords.selftext = "It's frustrating"
    sub_with_keywords.score = 10
    sub_with_keywords.num_comments = 5
    sub_with_keywords.url = "https://reddit.com"
    sub_with_keywords.created_utc = 1704067200

    sub_without_keywords = Mock()
    sub_without_keywords.id = "sub2"
    sub_without_keywords.title = "Just sharing my project"
    sub_without_keywords.selftext = "Check it out"
    sub_without_keywords.score = 10
    sub_without_keywords.num_comments = 5
    sub_without_keywords.url = "https://reddit.com"
    sub_without_keywords.created_utc = 1704067200

    mock_subreddit.new.return_value = [sub_with_keywords, sub_without_keywords]
    mock_reddit.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit, config={"filter_keywords": True})
    results = list(fetcher.fetch(limit=10, subreddit="SaaS"))

    # Only submission with problem keywords should be returned
    assert len(results) == 1
    assert results[0]["submission_id"] == "sub1"
    assert fetcher.stats["filtered"] == 1  # One filtered out


def test_filter_keywords_disabled():
    """Test keyword filtering when disabled."""
    mock_reddit = MagicMock()
    mock_subreddit = Mock()

    sub1 = Mock()
    sub1.id = "sub1"
    sub1.title = "No keywords here"
    sub1.selftext = "Just a post"
    sub1.score = 10
    sub1.num_comments = 5
    sub1.url = "https://reddit.com"
    sub1.created_utc = 1704067200

    mock_subreddit.new.return_value = [sub1]
    mock_reddit.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit, config={"filter_keywords": False})
    results = list(fetcher.fetch(limit=10, subreddit="SaaS"))

    # Should return submission even without keywords
    assert len(results) == 1
    assert fetcher.stats["fetched"] == 1
    assert fetcher.stats["filtered"] == 0


def test_contains_problem_keywords_true():
    """Test _contains_problem_keywords() with matching text."""
    fetcher = RedditAPIFetcher(client=MagicMock())

    assert fetcher._contains_problem_keywords("I have a problem with this") is True
    assert fetcher._contains_problem_keywords("This is frustrated") is True
    assert fetcher._contains_problem_keywords("Need help with an issue") is True


def test_contains_problem_keywords_false():
    """Test _contains_problem_keywords() with non-matching text."""
    fetcher = RedditAPIFetcher(client=MagicMock())

    assert fetcher._contains_problem_keywords("Just sharing my project") is False
    assert fetcher._contains_problem_keywords("Check out this tool") is False


def test_contains_problem_keywords_empty_text():
    """Test _contains_problem_keywords() with empty text."""
    fetcher = RedditAPIFetcher(client=MagicMock())

    assert fetcher._contains_problem_keywords("") is False
    assert fetcher._contains_problem_keywords(None) is False


def test_min_keywords_threshold():
    """Test minimum keywords threshold."""
    fetcher = RedditAPIFetcher(client=MagicMock(), config={"min_keywords": 2})

    # One keyword - should fail
    assert fetcher._contains_problem_keywords("I have a problem") is False

    # Two keywords - should pass
    assert fetcher._contains_problem_keywords("I have a problem and an issue") is True


# ===========================
# Validation Tests
# ===========================


def test_validate_submission_valid():
    """Test validation with valid submission."""
    fetcher = RedditAPIFetcher(client=MagicMock())
    submission = {"submission_id": "abc123", "title": "Test", "subreddit": "test"}

    assert fetcher.validate_submission(submission) is True


def test_validate_submission_missing_fields():
    """Test validation with missing required fields."""
    fetcher = RedditAPIFetcher(client=MagicMock())

    # Missing title
    assert fetcher.validate_submission({"submission_id": "abc123", "subreddit": "test"}) is False

    # Missing subreddit
    assert fetcher.validate_submission({"submission_id": "abc123", "title": "Test"}) is False

    # Missing submission_id
    assert fetcher.validate_submission({"title": "Test", "subreddit": "test"}) is False


def test_validate_submission_empty_values():
    """Test validation with empty field values."""
    fetcher = RedditAPIFetcher(client=MagicMock())
    submission = {"submission_id": "", "title": "Test", "subreddit": "test"}

    # Empty submission_id should fail validation
    assert fetcher.validate_submission(submission) is False


def test_fetch_filters_invalid_submissions(mock_reddit_client):
    """Test that invalid submissions are filtered out."""
    # Create submission with empty ID
    invalid_sub = Mock()
    invalid_sub.id = ""  # Invalid empty ID
    invalid_sub.title = "Test"
    invalid_sub.selftext = "problem"  # Has keyword
    invalid_sub.score = 10
    invalid_sub.num_comments = 5
    invalid_sub.url = "https://reddit.com"
    invalid_sub.created_utc = 1704067200

    mock_subreddit = Mock()
    mock_subreddit.new.return_value = [invalid_sub]
    mock_reddit_client.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    results = list(fetcher.fetch(limit=10, subreddit="SaaS"))

    # Invalid submission should be filtered out
    assert len(results) == 0
    assert fetcher.stats["filtered"] == 1


# ===========================
# Formatting Tests
# ===========================


def test_format_submission(mock_reddit_client, mock_submission):
    """Test _format_submission() produces standardized format."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    formatted = fetcher._format_submission(mock_submission, "SaaS")

    # Check all required fields
    assert formatted["submission_id"] == "abc123"
    assert formatted["title"] == "I have a problem with my workflow"
    assert formatted["text"] == "It's really frustrating and difficult"
    assert formatted["subreddit"] == "SaaS"
    assert formatted["upvotes"] == 50
    assert formatted["num_comments"] == 10
    assert formatted["url"] == "https://reddit.com/r/SaaS/comments/abc123"

    # Check aliases for compatibility
    assert formatted["content"] == formatted["text"]
    assert formatted["reddit_score"] == formatted["upvotes"]
    assert formatted["comments_count"] == formatted["num_comments"]

    # Check timestamps
    assert "created_at" in formatted
    assert "created_utc" in formatted


def test_format_submission_datetime_conversion(mock_reddit_client, mock_submission):
    """Test that created_utc is converted to ISO datetime."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    formatted = fetcher._format_submission(mock_submission, "SaaS")

    # Should have ISO format datetime
    assert isinstance(formatted["created_at"], str)
    assert "T" in formatted["created_at"]  # ISO format has 'T' separator


# ===========================
# Statistics Tests
# ===========================


def test_get_statistics(mock_reddit_client, mock_subreddit_with_submissions):
    """Test statistics tracking."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    list(fetcher.fetch(limit=10, subreddit="SaaS"))

    stats = fetcher.get_statistics()
    assert stats["fetched"] == 1
    assert stats["filtered"] == 0
    assert stats["errors"] == 0


def test_reset_statistics(mock_reddit_client, mock_subreddit_with_submissions):
    """Test resetting statistics."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    list(fetcher.fetch(limit=10, subreddit="SaaS"))

    assert fetcher.stats["fetched"] == 1

    fetcher.reset_statistics()
    assert fetcher.stats["fetched"] == 0
    assert fetcher.stats["filtered"] == 0
    assert fetcher.stats["errors"] == 0


# ===========================
# Source Name Tests
# ===========================


def test_get_source_name_default(mock_reddit_client):
    """Test source name with default sort type."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    assert fetcher.get_source_name() == "Reddit API (new)"


def test_get_source_name_custom_sort(mock_reddit_client):
    """Test source name with custom sort type."""
    fetcher = RedditAPIFetcher(client=mock_reddit_client, config={"sort_type": "hot"})
    assert fetcher.get_source_name() == "Reddit API (hot)"


# ===========================
# Error Handling Tests
# ===========================


def test_fetch_error_handling(mock_reddit_client):
    """Test error handling during fetch."""
    mock_reddit_client.subreddit.side_effect = Exception("Network error")

    fetcher = RedditAPIFetcher(client=mock_reddit_client)

    with pytest.raises(Exception, match="Reddit API fetch failed"):
        list(fetcher.fetch(limit=10, subreddit="SaaS"))

    # Error is incremented in both _fetch_from_subreddit and fetch() wrapper
    assert fetcher.stats["errors"] >= 1


def test_fetch_subreddit_error(mock_reddit_client):
    """Test error handling for individual subreddit fetch."""
    mock_reddit_client.subreddit.side_effect = Exception("Subreddit not found")

    fetcher = RedditAPIFetcher(client=mock_reddit_client)

    with pytest.raises(Exception, match="Error fetching from r/SaaS"):
        list(fetcher.fetch(limit=10, subreddit="SaaS"))

    assert fetcher.stats["errors"] >= 1


# ===========================
# Integration Tests
# ===========================


def test_fetch_complete_workflow(mock_reddit_client):
    """Test complete fetch workflow with filtering and formatting."""
    # Setup submissions
    sub1 = Mock()
    sub1.id = "sub1"
    sub1.title = "I have a problem"
    sub1.selftext = "It's frustrating"
    sub1.score = 50
    sub1.num_comments = 10
    sub1.url = "https://reddit.com"
    sub1.created_utc = 1704067200

    sub2 = Mock()
    sub2.id = "sub2"
    sub2.title = "No keywords"
    sub2.selftext = "Just sharing"
    sub2.score = 25
    sub2.num_comments = 5
    sub2.url = "https://reddit.com"
    sub2.created_utc = 1704067200

    mock_subreddit = Mock()
    mock_subreddit.new.return_value = [sub1, sub2]
    mock_reddit_client.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    results = list(fetcher.fetch(limit=10, subreddit="SaaS"))

    # Should get only one result (filtered by keywords)
    assert len(results) == 1
    assert results[0]["submission_id"] == "sub1"
    assert results[0]["upvotes"] == 50

    # Check statistics
    assert fetcher.stats["fetched"] == 1
    assert fetcher.stats["filtered"] == 1
    assert fetcher.stats["errors"] == 0


def test_fetch_multiple_subreddits_with_stats(mock_reddit_client):
    """Test fetching from multiple subreddits tracks stats correctly."""
    sub1 = Mock()
    sub1.id = "sub1"
    sub1.title = "problem"
    sub1.selftext = "issue"
    sub1.score = 10
    sub1.num_comments = 5
    sub1.url = "https://reddit.com"
    sub1.created_utc = 1704067200

    mock_subreddit = Mock()
    mock_subreddit.new.return_value = [sub1]
    mock_reddit_client.subreddit.return_value = mock_subreddit

    fetcher = RedditAPIFetcher(client=mock_reddit_client)
    results = list(fetcher.fetch(limit=10, subreddits=["SaaS", "startups"]))

    # Should get 2 results (one from each subreddit)
    assert len(results) == 2
    assert fetcher.stats["fetched"] == 2
