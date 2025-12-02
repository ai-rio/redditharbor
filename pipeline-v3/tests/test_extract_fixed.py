"""
Fixed tests for Reddit extraction module using enhanced mock infrastructure
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime, UTC

# Setup comprehensive mocks before importing actual modules
from tests.mock_enhanced_praw import (
    setup_extract_test_environment,
    cleanup_extract_test_environment,
    MockSubmission,
    MockSubreddit,
    MockReddit,
    MockAuthor
)

# Global variable to store mocks for cleanup
mocks = None

# Import the modules we're testing (these will use mocks when set up)
from extract.reddit_client import RedditClient
from models import RedditSubmission


@pytest.fixture(scope="module")
def extract_mocks():
    """Setup and cleanup mock environment for extract tests"""
    global mocks
    mocks = setup_extract_test_environment()
    yield mocks
    # Clean up after tests to restore real modules
    cleanup_extract_test_environment(mocks.get('original_modules'))


class TestRedditClientFixed:
    """Test cases for RedditClient using enhanced mock infrastructure"""

    def test_init_with_settings(self):
        """Test RedditClient initialization with mock settings"""
        client = RedditClient()
        assert client.settings is not None
        assert client.settings.reddit_client_id == "test_client_id"
        assert client._reddit is None  # Should be lazy loaded

    def test_connection_success(self):
        """Test successful Reddit API connection"""
        # Create a properly configured MockReddit instance
        mock_reddit = MockReddit()
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        # Patch praw.Reddit to return our mock
        with patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            client = RedditClient()
            result = client.test_connection()

            assert result is True
            mock_reddit.user.me.assert_called()

    def test_connection_failure(self):
        """Test failed Reddit API connection"""
        # Mock praw.Reddit to raise exception on initialization
        with patch('extract.reddit_client.praw.Reddit', side_effect=Exception("Authentication failed")):
            client = RedditClient()
            result = client.test_connection()

            assert result is False

    def test_fetch_submissions_success(self):
        """Test successful submission fetching"""
        # Create mock submission
        mock_submission = MockSubmission(
            id="test123",
            title="Test Submission",
            selftext="Test content",
            author_name="testuser",
            ups=100,
            score=100,
            num_comments=25,
            created_utc=1640995200,
            permalink="/r/test/test123",
            url="https://example.com"
        )

        # Create mock subreddit with the submission
        mock_subreddit = MockSubreddit(
            display_name="test",
            hot_submissions=[mock_submission]
        )

        # Create mock Reddit instance
        mock_reddit = MockReddit()
        mock_reddit._subreddits = {"test": mock_subreddit}
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        # Patch praw.Reddit to return our mock
        with patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            client = RedditClient()
            submissions = client.fetch_submissions(["test"], limit=1)

            assert len(submissions) == 1
            assert submissions[0].__class__.__name__ == "RedditSubmission"
            assert submissions[0].id == "test123"
            assert submissions[0].title == "Test Submission"
            assert submissions[0].author == "testuser"

    def test_convert_to_model_validation(self):
        """Test submission to model conversion validation"""
        client = RedditClient()

        # Mock submission with invalid data that will cause validation error
        mock_submission = Mock()
        mock_submission.id = "test"
        mock_submission.title = ""  # Invalid: too short
        mock_submission.selftext = "Test content"
        mock_submission.author = MockAuthor("testuser")
        mock_submission.ups = 100
        mock_submission.score = 100
        mock_submission.num_comments = 25
        mock_submission.subreddit = Mock()
        mock_submission.subreddit.display_name = "test"
        mock_submission.created_utc = 1640995200
        mock_submission.permalink = "/r/test/test123"
        mock_submission.url = "https://example.com"
        mock_submission.is_self = True
        mock_submission.over_18 = False

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

    def test_get_subreddit_info(self):
        """Test subreddit information retrieval"""
        # Create mock subreddit
        mock_subreddit = MockSubreddit(
            display_name="testsub",
            title="Test Subreddit",
            public_description="A test subreddit",
            subscribers=1000,
            active_user_count=100,
            created_utc=1640995200,
            over_18=False,
            restricted=False
        )

        # Create mock Reddit instance
        mock_reddit = MockReddit()
        mock_reddit._subreddits = {"testsub": mock_subreddit}
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        # Patch praw.Reddit to return our mock
        with patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            client = RedditClient()
            info = client.get_subreddit_info("testsub")

            assert info["name"] == "testsub"
            assert info["title"] == "Test Subreddit"
            assert info["subscribers"] == 1000
            assert info["active_users"] == 100
            assert info["description"] == "A test subreddit"

    def test_fetch_submissions_with_top_sort(self):
        """Test fetching submissions with top sort"""
        # Create mock submission
        mock_submission = MockSubmission(id="top123", title="Top Post")

        # Create mock subreddit with top submission
        mock_subreddit = MockSubreddit(
            display_name="test",
            top_submissions=[mock_submission]
        )

        # Create mock Reddit instance
        mock_reddit = MockReddit()
        mock_reddit._subreddits = {"test": mock_subreddit}
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        # Patch praw.Reddit to return our mock
        with patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            client = RedditClient()
            submissions = client.fetch_submissions(["test"], limit=1, sort_by="top")

            assert len(submissions) == 1
            assert submissions[0].id == "top123"

    def test_fetch_submissions_with_new_sort(self):
        """Test fetching submissions with new sort"""
        # Create mock submission
        mock_submission = MockSubmission(id="new123", title="New Post")

        # Create mock subreddit with new submission
        mock_subreddit = MockSubreddit(
            display_name="test",
            new_submissions=[mock_submission]
        )

        # Create mock Reddit instance
        mock_reddit = MockReddit()
        mock_reddit._subreddits = {"test": mock_subreddit}
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        # Patch praw.Reddit to return our mock
        with patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            client = RedditClient()
            submissions = client.fetch_submissions(["test"], limit=1, sort_by="new")

            assert len(submissions) == 1
            assert submissions[0].id == "new123"

    def test_fetch_submissions_error_handling(self):
        """Test error handling in fetch_submissions"""
        # Create mock Reddit that raises exception when accessing subreddit
        mock_reddit = MockReddit()
        # Override the subreddit method to raise exception
        mock_reddit.subreddit = Mock(side_effect=Exception("Subreddit not found"))
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        # Patch praw.Reddit to return our mock
        with patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            client = RedditClient()

            with pytest.raises(RuntimeError, match="Failed to fetch any submissions"):
                client.fetch_submissions(["nonexistent"], limit=1)

    def test_convert_to_model_with_deleted_author(self):
        """Test conversion with deleted author"""
        client = RedditClient()

        # Mock submission with deleted author
        mock_submission = MockSubmission(
            id="test123",
            title="Test Submission with Deleted Author",
            selftext="Test content",
            author=None,  # Deleted author
            ups=100,
            score=100,
            num_comments=25,
            created_utc=1640995200,
            permalink="/r/test/test123",
            url="https://example.com"
        )

        # Manually set author to None for deleted author test
        mock_submission.author = None

        reddit_submission = client._convert_to_model(mock_submission)

        assert reddit_submission.author == "[deleted]"
        assert reddit_submission.id == "test123"
        assert reddit_submission.title == "Test Submission with Deleted Author"

    def test_lazy_initialization(self):
        """Test that Reddit client is lazily initialized"""
        client = RedditClient()
        assert client._reddit is None

        # This should trigger lazy initialization
        mock_reddit = MockReddit()
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        with patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            # Access the reddit property
            reddit = client.reddit

            assert reddit is not None
            assert client._reddit is not None

    def test_subreddit_info_missing_attributes(self):
        """Test subreddit info with missing optional attributes"""
        # Create minimal mock subreddit with only display_name
        mock_subreddit = Mock(spec=[])  # Create mock with no attributes
        mock_subreddit.display_name = "minimal"
        mock_subreddit.created_utc = None  # Explicitly set to None to test fallback
        # Remove other attributes to test getattr fallbacks
        del mock_subreddit.title
        del mock_subreddit.public_description
        del mock_subreddit.subscribers
        del mock_subreddit.active_user_count
        del mock_subreddit.over18
        del mock_subreddit.restricted

        # Create mock Reddit instance
        mock_reddit = MockReddit()
        # Override subreddit method to return our minimal mock
        mock_reddit.subreddit = Mock(return_value=mock_subreddit)
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        # Patch praw.Reddit to return our mock
        with patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            client = RedditClient()
            info = client.get_subreddit_info("minimal")

            assert info["name"] == "minimal"
            assert info["title"] == "No title"  # Should use default
            assert info["description"] == "No description"  # Should use default
            assert info["subscribers"] == 0  # Should use default
            assert info["created_utc"] is None  # Should be None when created_utc is None

    def test_fetch_submissions_multiple_subreddits(self):
        """Test fetching submissions from multiple subreddits"""
        # Create mock submissions
        mock_submission1 = MockSubmission(id="sub1_123", title="Post from sub1")
        mock_submission2 = MockSubmission(id="sub2_456", title="Post from sub2")

        # Create mock subreddits
        mock_subreddit1 = MockSubreddit(display_name="sub1", hot_submissions=[mock_submission1])
        mock_subreddit2 = MockSubreddit(display_name="sub2", hot_submissions=[mock_submission2])

        # Create mock Reddit instance with both subreddits
        mock_reddit = MockReddit()
        mock_reddit._subreddits = {
            "sub1": mock_subreddit1,
            "sub2": mock_subreddit2
        }
        mock_reddit.user.me.return_value = MockAuthor('testuser')

        # Patch praw.Reddit to return our mock
        with patch('extract.reddit_client.praw.Reddit', return_value=mock_reddit):
            client = RedditClient()
            submissions = client.fetch_submissions(["sub1", "sub2"], limit=2)

            assert len(submissions) == 2
            submission_ids = [s.id for s in submissions]
            assert "sub1_123" in submission_ids
            assert "sub2_456" in submission_ids

    def test_convert_to_model_complete_data(self):
        """Test conversion with complete submission data"""
        client = RedditClient()

        # Create complete mock submission
        mock_submission = MockSubmission(
            id="complete123",
            title="Complete Test Submission",
            selftext="Complete test content",
            author_name="completeuser",
            ups=500,
            score=500,
            downs=0,
            num_comments=100,
            created_utc=1640995200,
            permalink="/r/test/complete123",
            url="https://complete.example.com",
            is_self=True,
            over_18=False,
            subreddit_name="completesub"
        )

        reddit_submission = client._convert_to_model(mock_submission)

        assert reddit_submission.id == "complete123"
        assert reddit_submission.title == "Complete Test Submission"
        assert reddit_submission.text == "Complete test content"
        assert reddit_submission.author == "completeuser"
        assert reddit_submission.upvotes == 500
        assert reddit_submission.score == 500
        assert reddit_submission.comments_count == 100
        assert reddit_submission.subreddit == "completesub"
        assert reddit_submission.permalink == "https://reddit.com/r/test/complete123"
        assert reddit_submission.url == "https://complete.example.com"
        assert reddit_submission.is_self is True
        assert reddit_submission.over_18 is False