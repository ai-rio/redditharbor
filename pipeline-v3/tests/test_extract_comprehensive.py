"""
Fixed comprehensive tests for Reddit extraction module using proper patching
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, UTC

# Import mock classes for testing
from tests.mock_enhanced_praw import (
    MockSubmission,
    MockSubreddit,
    MockReddit,
    MockAuthor
)

# Import models (these will use real models)
from models import RedditSubmission


@pytest.fixture
def mock_settings():
    """Create mock settings for testing"""
    settings = Mock()
    settings.reddit_client_id = "test_client_id"
    settings.reddit_client_secret = "test_client_secret"
    settings.reddit_user_agent = "test_agent"
    return settings


@pytest.fixture
def mock_reddit_instance():
    """Create mock Reddit instance"""
    reddit = MockReddit()
    reddit.user.me.return_value = MockAuthor('testuser')
    return reddit


class TestRedditClientComprehensive:
    """Comprehensive test cases for RedditClient using proper mock patching"""

    def test_init_with_settings(self, mock_settings):
        """Test RedditClient initialization with mock settings"""
        with patch('extract.reddit_client.get_settings', return_value=mock_settings):
            from extract.reddit_client import RedditClient
            client = RedditClient()
            assert client.settings is not None
            assert client.settings.reddit_client_id == "test_client_id"
            assert client._reddit is None  # Should be lazy loaded

    def test_connection_success(self, mock_settings, mock_reddit_instance):
        """Test successful Reddit API connection"""
        with patch('extract.reddit_client.get_settings', return_value=mock_settings), \
             patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit_instance):
            from extract.reddit_client import RedditClient
            client = RedditClient()
            result = client.test_connection()

            assert result is True
            assert mock_reddit_instance.user.me.call_count >= 1

    def test_connection_failure(self, mock_settings):
        """Test failed Reddit API connection"""
        with patch('extract.reddit_client.get_settings', return_value=mock_settings), \
             patch('extract.reddit_client.praw.Reddit', side_effect=Exception("Authentication failed")):
            from extract.reddit_client import RedditClient
            client = RedditClient()
            result = client.test_connection()

            assert result is False

    def test_fetch_submissions_with_various_limits(self, mock_settings):
        """Test fetching submissions with different limit parameters"""
        # Create mock submissions
        submissions = [
            MockSubmission(id=f"test{i}", title=f"Test Post {i}")
            for i in range(5)
        ]

        # Create mock subreddit
        mock_subreddit = MockSubreddit(
            display_name="test",
            hot_submissions=submissions
        )

        # Create mock Reddit instance
        mock_reddit = MockReddit()
        mock_reddit._subreddits = {"test": mock_subreddit}
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        with patch('extract.reddit_client.get_settings', return_value=mock_settings), \
             patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            from extract.reddit_client import RedditClient
            client = RedditClient()

            # Test different limits
            for limit in [1, 3, 5]:
                submissions_result = client.fetch_submissions(["test"], limit=limit)
                assert len(submissions_result) == limit

    def test_fetch_submissions_all_sort_methods(self, mock_settings):
        """Test fetching submissions with all available sort methods"""
        # Create mock submissions for different sorts
        hot_submission = MockSubmission(id="hot123", title="Hot Post")
        top_submission = MockSubmission(id="top123", title="Top Post")
        new_submission = MockSubmission(id="new123", title="New Post")

        # Create mock subreddits with different submissions
        mock_subreddit = MockSubreddit(
            display_name="test",
            hot_submissions=[hot_submission],
            top_submissions=[top_submission],
            new_submissions=[new_submission]
        )

        # Create mock Reddit instance
        mock_reddit = MockReddit()
        mock_reddit._subreddits = {"test": mock_subreddit}
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        with patch('extract.reddit_client.get_settings', return_value=mock_settings), \
             patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            from extract.reddit_client import RedditClient
            client = RedditClient()

            # Test each sort method
            hot_results = client.fetch_submissions(["test"], limit=1, sort_by="hot")
            top_results = client.fetch_submissions(["test"], limit=1, sort_by="top")
            new_results = client.fetch_submissions(["test"], limit=1, sort_by="new")

            assert len(hot_results) == 1 and hot_results[0].id == "hot123"
            assert len(top_results) == 1 and top_results[0].id == "top123"
            assert len(new_results) == 1 and new_results[0].id == "new123"

    def test_fetch_submissions_time_filters(self, mock_settings):
        """Test fetching submissions with different time filters"""
        # Create mock submissions for time filtering
        mock_submission = MockSubmission(id="time123", title="Time Filtered Post")

        # Create mock subreddit
        mock_subreddit = MockSubreddit(
            display_name="test",
            top_submissions=[mock_submission]
        )

        # Create mock Reddit instance
        mock_reddit = MockReddit()
        mock_reddit._subreddits = {"test": mock_subreddit}
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        with patch('extract.reddit_client.get_settings', return_value=mock_settings), \
             patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            from extract.reddit_client import RedditClient
            client = RedditClient()

            # Test different time filters
            time_filters = ['hour', 'day', 'week', 'month', 'year', 'all']
            for time_filter in time_filters:
                results = client.fetch_submissions(
                    ["test"],
                    limit=1,
                    sort_by="top",
                    time_filter=time_filter
                )
                assert len(results) == 1
                assert results[0].id == "time123"

    def test_convert_to_model_edge_cases(self, mock_settings):
        """Test model conversion with various edge cases"""
        with patch('extract.reddit_client.get_settings', return_value=mock_settings):
            from extract.reddit_client import RedditClient
            client = RedditClient()

            # Test with minimum valid data
            minimal_submission = MockSubmission(
                id="min123",
                title="Min",
                selftext="",
                author_name="user",
                ups=0,
                score=0,
                num_comments=0,
                created_utc=1640995200,
                permalink="/r/test/min123",
                url="https://reddit.com/r/test/min123"
            )

            reddit_submission = client._convert_to_model(minimal_submission)
            assert reddit_submission.id == "min123"
            assert reddit_submission.title == "Min"
            assert reddit_submission.author == "user"

    def test_get_subreddit_info_various_subreddits(self, mock_settings):
        """Test subreddit info for different types of subreddits"""
        # Test cases for different subreddit configurations
        subreddit_configs = [
            {
                "display_name": "public",
                "title": "Public Subreddit",
                "public_description": "A public subreddit",
                "subscribers": 10000,
                "active_user_count": 1000,
                "over_18": False,
                "restricted": False
            },
            {
                "display_name": "nsfw",
                "title": "NSFW Subreddit",
                "public_description": "An NSFW subreddit",
                "subscribers": 5000,
                "active_user_count": 500,
                "over_18": True,
                "restricted": False
            },
            {
                "display_name": "restricted",
                "title": "Restricted Subreddit",
                "public_description": "A restricted subreddit",
                "subscribers": 2000,
                "active_user_count": 200,
                "over_18": False,
                "restricted": True
            }
        ]

        for config in subreddit_configs:
            mock_subreddit = MockSubreddit(**config)
            mock_reddit = MockReddit()
            mock_reddit._subreddits = {config["display_name"]: mock_subreddit}
            mock_reddit.user.me.return_value = MockAuthor('testuser')

            with patch('extract.reddit_client.get_settings', return_value=mock_settings), \
                 patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
                from extract.reddit_client import RedditClient
                client = RedditClient()
                info = client.get_subreddit_info(config["display_name"])

                assert info["name"] == config["display_name"]
                assert info["title"] == config["title"]
                assert info["subscribers"] == config["subscribers"]
                assert info["active_users"] == config["active_user_count"]

    def test_fetch_submissions_large_dataset(self, mock_settings):
        """Test fetching a large number of submissions"""
        # Create many mock submissions
        submissions = [
            MockSubmission(id=f"large{i}", title=f"Large Dataset Post {i}")
            for i in range(50)
        ]

        # Create mock subreddit
        mock_subreddit = MockSubreddit(
            display_name="large",
            hot_submissions=submissions
        )

        # Create mock Reddit instance
        mock_reddit = MockReddit()
        mock_reddit._subreddits = {"large": mock_subreddit}
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        with patch('extract.reddit_client.get_settings', return_value=mock_settings), \
             patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            from extract.reddit_client import RedditClient
            client = RedditClient()
            results = client.fetch_submissions(["large"], limit=25)

            assert len(results) == 25
            for i, submission in enumerate(results):
                assert submission.id.startswith("large")

    def test_lazy_initialization_multiple_access(self, mock_settings, mock_reddit_instance):
        """Test that lazy initialization works correctly with multiple accesses"""
        with patch('extract.reddit_client.get_settings', return_value=mock_settings), \
             patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit_instance):
            from extract.reddit_client import RedditClient
            client = RedditClient()

            # Multiple accesses should use the same instance
            reddit1 = client.reddit
            reddit2 = client.reddit
            reddit3 = client.reddit

            assert reddit1 is reddit2 is reddit3
            assert client._reddit is not None

    def test_error_handling_network_issues(self, mock_settings):
        """Test handling of network-related errors"""
        # Mock Reddit with network error
        mock_reddit = MockReddit()
        mock_reddit.subreddit = Mock(side_effect=ConnectionError("Network timeout"))
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        with patch('extract.reddit_client.get_settings', return_value=mock_settings), \
             patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            from extract.reddit_client import RedditClient
            client = RedditClient()

            with pytest.raises(RuntimeError, match="Failed to fetch any submissions"):
                client.fetch_submissions(["test"], limit=10)

    def test_convert_to_model_unicode_handling(self, mock_settings):
        """Test model conversion with Unicode characters"""
        with patch('extract.reddit_client.get_settings', return_value=mock_settings):
            from extract.reddit_client import RedditClient
            client = RedditClient()

            # Create submission with Unicode characters
            unicode_submission = MockSubmission(
                id="unicode123",
                title="Test with émojis 🎉 and ünicode",
                selftext="Content with special chars: café, résumé, naïve",
                author_name="üser_🚀",
                ups=100,
                score=100,
                num_comments=25,
                created_utc=1640995200,
                permalink="/r/test/unicode123",
                url="https://example.com/ünicode"
            )

            reddit_submission = client._convert_to_model(unicode_submission)
            assert reddit_submission.id == "unicode123"
            assert "🎉" in reddit_submission.title
            assert "café" in reddit_submission.text
            assert "🚀" in reddit_submission.author