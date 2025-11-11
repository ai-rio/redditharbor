#!/usr/bin/env python3
"""
Test suite for DLT comment collection functionality.

Tests the collect_post_comments function including:
- Single submission ID handling
- Multiple submission IDs handling
- Error handling for invalid IDs
- Reddit API rate limiting
- Comment data structure validation
- Error logging functionality
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import the module with fallback for missing dependencies
try:
    import praw

    from core.dlt_collection import collect_post_comments, get_reddit_client
    HAS_DEPENDENCIES = True
except ImportError as e:
    HAS_DEPENDENCIES = False
    print(f"Warning: Could not import required dependencies: {e}")


class TestCollectPostComments:
    """Test cases for collect_post_comments function"""

    @pytest.mark.skipif(not HAS_DEPENDENCIES, reason="praw not available")
    def test_single_submission_id(self):
        """Test collecting comments from a single submission ID"""
        # Mock Reddit client
        mock_reddit = MagicMock(spec=praw.Reddit)
        mock_submission = MagicMock()
        mock_submission.title = "Test Post"
        mock_reddit.submission.return_value = mock_submission

        # Create mock comments
        mock_comment1 = MagicMock()
        mock_comment1.id = "comment1"
        mock_comment1.author = "test_user"
        mock_comment1.body = "This is a test comment"
        mock_comment1.score = 10
        mock_comment1.created_utc = 1704067200
        mock_comment1.parent_id = "t3_abc123"
        mock_comment1.depth = 0

        mock_submission.comments.list.return_value = [mock_comment1]
        mock_submission.comments.replace_more = MagicMock()

        # Test
        result = collect_post_comments("abc123", reddit_client=mock_reddit)

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["comment_id"] == "comment1"
        assert result[0]["submission_id"] == "abc123"
        assert result[0]["author"] == "test_user"
        assert result[0]["depth"] == 0

    @pytest.mark.skipif(not HAS_DEPENDENCIES, reason="praw not available")
    def test_multiple_submission_ids(self):
        """Test collecting comments from multiple submission IDs"""
        # Mock Reddit client
        mock_reddit = MagicMock(spec=praw.Reddit)

        # Create mock comments for first submission
        mock_comment1 = MagicMock()
        mock_comment1.id = "comment1"
        mock_comment1.author = "user1"
        mock_comment1.body = "Comment 1"
        mock_comment1.score = 5
        mock_comment1.created_utc = 1704067200
        mock_comment1.parent_id = "t3_sub1"
        mock_comment1.depth = 0

        # Create mock comments for second submission
        mock_comment2 = MagicMock()
        mock_comment2.id = "comment2"
        mock_comment2.author = "user2"
        mock_comment2.body = "Comment 2"
        mock_comment2.score = 8
        mock_comment2.created_utc = 1704067201
        mock_comment2.parent_id = "t3_sub2"
        mock_comment2.depth = 1

        # Setup mock submissions
        mock_submission1 = MagicMock()
        mock_submission1.title = "Post 1"
        mock_submission1.comments.list.return_value = [mock_comment1]
        mock_submission1.comments.replace_more = MagicMock()

        mock_submission2 = MagicMock()
        mock_submission2.title = "Post 2"
        mock_submission2.comments.list.return_value = [mock_comment2]
        mock_submission2.comments.replace_more = MagicMock()

        # Configure mock to return appropriate submission
        def submission_side_effect(id):
            if id == "sub1":
                return mock_submission1
            elif id == "sub2":
                return mock_submission2

        mock_reddit.submission.side_effect = submission_side_effect

        # Test
        result = collect_post_comments(["sub1", "sub2"], reddit_client=mock_reddit)

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["submission_id"] == "sub1"
        assert result[1]["submission_id"] == "sub2"

    @pytest.mark.skipif(not HAS_DEPENDENCIES, reason="praw not available")
    def test_deleted_comments_filtered(self):
        """Test that deleted/removed comments are filtered out"""
        mock_reddit = MagicMock(spec=praw.Reddit)
        mock_submission = MagicMock()
        mock_submission.title = "Test Post"

        # Create regular comment
        mock_comment1 = MagicMock()
        mock_comment1.id = "comment1"
        mock_comment1.author = "test_user"
        mock_comment1.body = "Regular comment"
        mock_comment1.score = 10
        mock_comment1.created_utc = 1704067200
        mock_comment1.parent_id = "t3_abc123"
        mock_comment1.depth = 0

        # Create deleted comment (author is None)
        mock_deleted = MagicMock()
        mock_deleted.author = None
        mock_deleted.id = "deleted1"
        mock_deleted.body = "[deleted]"
        mock_deleted.score = -1
        mock_deleted.created_utc = 1704067201
        mock_deleted.parent_id = "t3_abc123"
        mock_deleted.depth = 0

        mock_submission.comments.list.return_value = [mock_comment1, mock_deleted]
        mock_submission.comments.replace_more = MagicMock()
        mock_reddit.submission.return_value = mock_submission

        # Test
        result = collect_post_comments("abc123", reddit_client=mock_reddit)

        # Assertions - deleted comment should be filtered
        assert len(result) == 1
        assert result[0]["comment_id"] == "comment1"
        assert result[0]["author"] == "test_user"

    @pytest.mark.skipif(not HAS_DEPENDENCIES, reason="praw not available")
    def test_invalid_submission_id(self):
        """Test handling of invalid submission IDs"""
        mock_reddit = MagicMock(spec=praw.Reddit)
        mock_reddit.submission.side_effect = Exception(
            "Invalid submission ID"
        )

        # Test
        result = collect_post_comments("invalid_id", reddit_client=mock_reddit)

        # Should return empty list for invalid ID
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.skipif(not HAS_DEPENDENCIES, reason="praw not available")
    def test_empty_submission(self):
        """Test handling of submissions with no comments"""
        mock_reddit = MagicMock(spec=praw.Reddit)
        mock_submission = MagicMock()
        mock_submission.title = "Empty Post"
        mock_submission.comments.list.return_value = []
        mock_submission.comments.replace_more = MagicMock()
        mock_reddit.submission.return_value = mock_submission

        # Test
        result = collect_post_comments("abc123", reddit_client=mock_reddit)

        # Should return empty list, not False
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.skipif(not HAS_DEPENDENCIES, reason="praw not available")
    def test_comment_data_structure(self):
        """Test that returned comment data has correct structure"""
        mock_reddit = MagicMock(spec=praw.Reddit)
        mock_submission = MagicMock()
        mock_submission.title = "Test Post"

        mock_comment = MagicMock()
        mock_comment.id = "cmt_123"
        mock_comment.author = "john_doe"
        mock_comment.body = "Great discussion here!"
        mock_comment.score = 42
        mock_comment.created_utc = 1704067200.5
        mock_comment.parent_id = "t1_parent123"
        mock_comment.depth = 2

        mock_submission.comments.list.return_value = [mock_comment]
        mock_submission.comments.replace_more = MagicMock()
        mock_reddit.submission.return_value = mock_submission

        # Test
        result = collect_post_comments("abc123", reddit_client=mock_reddit)

        # Verify data structure
        assert len(result) == 1
        comment = result[0]

        # Check all required fields exist
        required_fields = [
            "comment_id",
            "submission_id",
            "author",
            "body",
            "score",
            "created_utc",
            "parent_id",
            "depth",
        ]
        for field in required_fields:
            assert field in comment, f"Missing field: {field}"

        # Check field types
        assert isinstance(comment["comment_id"], str)
        assert isinstance(comment["submission_id"], str)
        assert isinstance(comment["author"], str)
        assert isinstance(comment["body"], str)
        assert isinstance(comment["score"], int)
        assert isinstance(comment["created_utc"], int)
        assert isinstance(comment["parent_id"], str)
        assert isinstance(comment["depth"], int)

        # Check field values
        assert comment["comment_id"] == "cmt_123"
        assert comment["submission_id"] == "abc123"
        assert comment["author"] == "john_doe"
        assert comment["depth"] == 2

    @pytest.mark.skipif(not HAS_DEPENDENCIES, reason="praw not available")
    def test_rate_limiting_handling(self):
        """Test that rate limiting errors are handled gracefully"""
        mock_reddit = MagicMock(spec=praw.Reddit)
        mock_reddit.submission.side_effect = Exception(
            Mock(status_code=429)
        )

        # Test - should not raise exception
        result = collect_post_comments("abc123", reddit_client=mock_reddit)

        # Should return empty list on API error
        assert isinstance(result, list)

    def test_no_submission_ids(self):
        """Test handling when no submission IDs provided"""
        result = collect_post_comments([])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_string_vs_list_input(self):
        """Test that both string and list inputs are normalized"""
        mock_reddit = MagicMock(spec=praw.Reddit)
        mock_submission = MagicMock()
        mock_submission.title = "Test"
        mock_submission.comments.list.return_value = []
        mock_submission.comments.replace_more = MagicMock()
        mock_reddit.submission.return_value = mock_submission

        # Both should work
        result1 = collect_post_comments("abc123", reddit_client=mock_reddit)
        assert isinstance(result1, list)

        result2 = collect_post_comments(["abc123"], reddit_client=mock_reddit)
        assert isinstance(result2, list)


class TestCommentThreading:
    """Test comment threading metadata"""

    @pytest.mark.skipif(not HAS_DEPENDENCIES, reason="praw not available")
    def test_depth_tracking(self):
        """Test that comment depth is correctly tracked"""
        mock_reddit = MagicMock(spec=praw.Reddit)
        mock_submission = MagicMock()
        mock_submission.title = "Thread Test"

        # Create comments at different depths
        comments_data = [
            (0, "t3_sub123", "Top-level comment"),
            (1, "t1_comment1", "Reply to top-level"),
            (2, "t1_comment2", "Nested reply"),
            (3, "t1_comment3", "Deep nested reply"),
        ]

        mock_comments = []
        for depth, parent_id, body in comments_data:
            mock_comment = MagicMock()
            mock_comment.id = f"cmt{depth}"
            mock_comment.author = MagicMock(name=f"user{depth}")
            mock_comment.body = body
            mock_comment.score = 10 - depth
            mock_comment.created_utc = 1704067200 + depth
            mock_comment.parent_id = parent_id
            mock_comment.depth = depth
            mock_comments.append(mock_comment)

        mock_submission.comments.list.return_value = mock_comments
        mock_submission.comments.replace_more = MagicMock()
        mock_reddit.submission.return_value = mock_submission

        # Test
        result = collect_post_comments("sub123", reddit_client=mock_reddit)

        # Verify depth tracking
        assert len(result) == 4
        for i, comment in enumerate(result):
            assert comment["depth"] == i
            assert comment["parent_id"] == comments_data[i][1]


class TestErrorLogging:
    """Test error logging functionality"""

    @pytest.mark.skipif(not HAS_DEPENDENCIES, reason="praw not available")
    def test_error_log_creation(self):
        """Test that error logs are created for failures"""
        mock_reddit = MagicMock(spec=praw.Reddit)
        mock_reddit.submission.side_effect = Exception("Bad ID")

        # Test
        result = collect_post_comments("bad_id", reddit_client=mock_reddit)

        # Check that error log was created
        error_logs = list((project_root / "error_log").glob("collect_comments_*.log"))
        assert len(error_logs) > 0

        # Verify log contains error message
        latest_log = sorted(error_logs)[-1]
        with open(latest_log) as f:
            log_content = f.read()
            assert "Invalid submission ID" in log_content or "bad_id" in log_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
