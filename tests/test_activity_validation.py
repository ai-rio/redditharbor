#!/usr/bin/env python3
"""
Test module for activity validation functionality using PRAW.

Follows TDD approach: failing tests first, then implementation.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Source virtual environment
os.environ['VIRTUAL_ENV'] = str(project_root / '.venv')
os.environ['PATH'] = f"{project_root}/.venv/bin:{os.environ.get('PATH', '')}"

# Mock environment variables for testing
os.environ['REDDIT_PUBLIC'] = 'test_public_key'
os.environ['REDDIT_SECRET'] = 'test_secret_key'
os.environ['REDDIT_USER_AGENT'] = 'test_user_agent'


class TestActivityValidation:
    """Test suite for activity validation module."""

    def test_calculate_activity_score_basic(self):
        """Test basic activity score calculation."""
        from core.activity_validation import calculate_activity_score

        # Mock subreddit object
        mock_subreddit = Mock()
        mock_subreddit.display_name = "testsubreddit"

        # Test with time_filter
        time_filter = "day"

        # This should fail initially since function doesn't exist
        result = calculate_activity_score(mock_subreddit, time_filter)

        # Should return a numeric score
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100  # Score should be between 0-100

    def test_collect_activity_metrics_basic(self):
        """Test basic activity metrics collection."""
        from core.activity_validation import collect_activity_metrics

        # Mock subreddit object
        mock_subreddit = Mock()
        mock_subreddit.display_name = "testsubreddit"

        time_filter = "day"

        # This should fail initially since function doesn't exist
        result = collect_activity_metrics(mock_subreddit, time_filter)

        # Should return a dictionary with expected metrics
        assert isinstance(result, dict)
        expected_keys = [
            'recent_comments_count', 'post_engagement_score',
            'subscriber_base_score', 'active_users_score',
            'comments_24h', 'posts_24h', 'avg_engagement_rate',
            'quality_signals'
        ]
        for key in expected_keys:
            assert key in result

    def test_calculate_trending_score_basic(self):
        """Test basic trending score calculation."""
        from core.activity_validation import calculate_trending_score

        # Mock metrics
        mock_metrics = {
            'recent_comments_count': 100,
            'post_engagement_score': 75,
            'subscriber_base_score': 50,
            'active_users_score': 60,
            'comments_24h': 50,
            'posts_24h': 25,
            'avg_engagement_rate': 2.5,
            'quality_signals': {'avg_score': 3.2}
        }

        # This should fail initially since function doesn't exist
        result = calculate_trending_score(mock_metrics)

        # Should return a numeric trending score
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100

    def test_get_active_subreddits_basic(self):
        """Test basic active subreddits filtering."""
        from core.activity_validation import get_active_subreddits

        # Mock Reddit client
        mock_reddit_client = Mock()

        # Mock subreddit objects
        mock_subreddit1 = Mock()
        mock_subreddit1.display_name = "active_subreddit"
        mock_subreddit2 = Mock()
        mock_subreddit2.display_name = "inactive_subreddit"

        # Mock Reddit client subreddit method
        mock_reddit_client.subreddit.side_effect = [mock_subreddit1, mock_subreddit2]

        candidate_subreddits = ["active_subreddit", "inactive_subreddit"]
        time_filter = "day"
        min_activity_score = 50

        # This should fail initially since function doesn't exist
        result = get_active_subreddits(
            mock_reddit_client, candidate_subreddits, time_filter, min_activity_score
        )

        # Should return a list of active subreddits
        assert isinstance(result, list)
        # Should contain subreddit objects, not just names
        if result:  # If any subreddits pass the filter
            assert hasattr(result[0], 'display_name')

    @patch('core.activity_validation praw')
    def test_error_handling(self, mock_praw):
        """Test error handling for API failures."""
        from core.activity_validation import calculate_activity_score

        # Mock subreddit that will raise exception
        mock_subreddit = Mock()
        mock_subreddit.comments.side_effect = Exception("API Error")
        mock_subreddit.display_name = "error_subreddit"

        time_filter = "day"

        # Should handle errors gracefully
        result = calculate_activity_score(mock_subreddit, time_filter)

        # Should return 0 or None on error
        assert result == 0 or result is None

    def test_activity_score_weights(self):
        """Test activity score calculation weights."""
        from core.activity_validation import calculate_activity_score

        # Mock subreddit with known metrics
        mock_subreddit = Mock()
        mock_subreddit.display_name = "weight_test_subreddit"

        # Mock comments (40% weight)
        mock_comments = [Mock() for _ in range(100)]  # High comment count
        mock_subreddit.comments.return_value = mock_comments

        # Mock submissions for engagement (30% weight)
        mock_submissions = [Mock(score=100) for _ in range(50)]  # High engagement
        mock_subreddit.top.return_value = mock_submissions

        # Mock subscriber count (20% weight)
        mock_subreddit.subscribers = 10000  # High subscriber count

        time_filter = "day"

        result = calculate_activity_score(mock_subreddit, time_filter)

        # Should be a high score due to high metrics
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
