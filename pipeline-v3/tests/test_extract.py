"""
Tests for Reddit extraction module
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC

from extract.reddit_client import RedditClient
from models import RedditSubmission


class TestRedditClient:
    """Test cases for RedditClient"""

    def test_init_with_settings(self):
        """Test RedditClient initialization"""
        client = RedditClient()
        assert client.settings is not None
        assert client._reddit is None  # Should be lazy loaded

    @patch('extract.reddit_client.praw.Reddit')
    def test_connection_success(self, mock_praw):
        """Test successful Reddit API connection"""
        # Mock successful authentication
        mock_reddit = Mock()
        mock_reddit.user.me.return_value = Mock()
        mock_praw.return_value = mock_reddit

        client = RedditClient()
        result = client.test_connection()

        assert result is True
        mock_praw.assert_called_once()
        mock_reddit.user.me.assert_called_once()

    @patch('extract.reddit_client.praw.Reddit')
    def test_connection_failure(self, mock_praw):
        """Test failed Reddit API connection"""
        # Mock failed authentication
        mock_praw.side_effect = Exception("Authentication failed")

        client = RedditClient()
        result = client.test_connection()

        assert result is False

    @patch('extract.reddit_client.paw.Reddit')
    def test_fetch_submissions_success(self, mock_praw):
        """Test successful submission fetching"""
        # Mock Reddit API response
        mock_subreddit = Mock()
        mock_submission = Mock()
        mock_submission.id = "test123"
        mock_submission.title = "Test Submission"
        mock_submission.selftext = "Test content"
        mock_submission.author = Mock()
        mock_submission.author.__str__ = lambda: "testuser"
        mock_submission.ups = 100
        mock_submission.score = 100
        mock_submission.num_comments = 25
        mock_submission.subreddit = Mock()
        mock_submission.subreddit.display_name.lower.return_value = "test"
        mock_submission.created_utc = 1640995200  # 2022-01-01
        mock_submission.permalink = "/r/test/test123"
        mock_submission.url = "https://example.com"
        mock_submission.is_self = True
        mock_submission.over_18 = False

        mock_subreddit.hot.return_value = [mock_submission]
        mock_reddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_reddit.user.me.return_value = Mock()
        mock_praw.return_value = mock_reddit

        client = RedditClient()
        submissions = client.fetch_submissions(["test"], limit=1)

        assert len(submissions) == 1
        assert isinstance(submissions[0], RedditSubmission)
        assert submissions[0].id == "test123"
        assert submissions[0].title == "Test Submission"

    def test_convert_to_model_validation(self):
        """Test submission to model conversion validation"""
        client = RedditClient()

        # Mock submission with invalid data
        mock_submission = Mock()
        mock_submission.id = "test"
        mock_submission.title = ""  # Invalid: too short
        mock_submission.text = "Test content"
        mock_submission.author = Mock()
        mock_submission.author.__str__ = lambda: "testuser"
        mock_submission.ups = 100
        mock_submission.score = 100
        mock_submission.num_comments = 25
        mock_submission.subreddit = Mock()
        mock_submission.subreddit.display_name.lower.return_value = "test"
        mock_submission.created_utc = 1640995200
        mock_submission.permalink = "/r/test/test123"

        with pytest.raises(ValueError, match="Invalid submission data"):
            client._convert_to_model(mock_submission)

    def test_fetch_submissions_invalid_params(self):
        """Test parameter validation"""
        client = RedditClient()

        with pytest.raises(ValueError, match="At least one subreddit"):
            client.fetch_submissions([], limit=10)

        with pytest.raises(ValueError, match="Limit must be positive"):
            client.fetch_submissions(["test"], limit=0)

        with pytest.raises(ValueError, match="sort_by must be one of"):
            client.fetch_submissions(["test"], limit=10, sort_by="invalid")

    @patch('extract.reddit_client.paw.Reddit')
    def test_get_subreddit_info(self, mock_praw):
        """Test subreddit information retrieval"""
        mock_subreddit = Mock()
        mock_subreddit.display_name = "testsub"
        mock_subreddit.title = "Test Subreddit"
        mock_subreddit.public_description = "A test subreddit"
        mock_subreddit.subscribers = 1000
        mock_subreddit.active_user_count = 100
        mock_subreddit.created_utc = 1640995200
        mock_subreddit.over_18 = False
        mock_subreddit.restricted = False

        mock_reddit = Mock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_reddit.user.me.return_value = Mock()
        mock_praw.return_value = mock_reddit

        client = RedditClient()
        info = client.get_subreddit_info("testsub")

        assert info["name"] == "testsub"
        assert info["title"] == "Test Subreddit"
        assert info["subscribers"] == 1000
        assert info["active_users"] == 100