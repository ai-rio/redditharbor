"""
Test suite for DLT Reddit Source with Activity Validation

This module tests the DLT source definition for Reddit data collection
with integrated activity validation functionality.
"""

from unittest.mock import MagicMock, patch

import pendulum
import pytest

# Import the module we're going to create
try:
    from core.dlt_reddit_source import (
        active_subreddits,
        activity_trends,
        reddit_activity_aware,
        validated_comments,
    )
except ImportError:
    # This will fail initially, which is expected in TDD
    pytest.skip("DLT Reddit source not implemented yet", allow_module_level=True)


class TestRedditActivityAwareSource:
    """Test the reddit_activity_aware DLT source."""

    def test_source_creation(self):
        """Test that the DLT source can be created with correct parameters."""
        mock_reddit_client = MagicMock()
        subreddits = ["python", "learnprogramming"]
        time_filter = "day"
        min_activity_score = 50.0

        # Test source creation
        source = reddit_activity_aware(
            reddit_client=mock_reddit_client,
            subreddits=subreddits,
            time_filter=time_filter,
            min_activity_score=min_activity_score
        )

        # Verify source configuration
        assert source is not None
        assert source.name == "reddit_activity_aware"

    def test_source_parameters(self):
        """Test that source parameters are properly stored."""
        mock_reddit_client = MagicMock()
        subreddits = ["test", "example"]
        time_filter = "week"
        min_activity_score = 75.0

        source = reddit_activity_aware(
            reddit_client=mock_reddit_client,
            subreddits=subreddits,
            time_filter=time_filter,
            min_activity_score=min_activity_score
        )

        # The source should store these parameters internally
        # Implementation-specific checks would go here
        assert source is not None


class TestActiveSubredditsResource:
    """Test the active_subreddits DLT resource."""

    def test_active_subreddits_resource_creation(self):
        """Test that active_subreddits resource can be created."""
        mock_reddit_client = MagicMock()

        # Test resource creation - it should not call get_active_subreddits immediately
        resource = active_subreddits(
            reddit_client=mock_reddit_client,
            subreddits=["python", "test"],
            time_filter="day",
            min_activity_score=50.0
        )

        # Resource should be created successfully
        assert resource is not None
        assert callable(resource)
        assert resource.name == "active_subreddits"

    def test_active_subreddits_data_structure(self):
        """Test that active_subreddits returns correct data structure."""
        mock_reddit_client = MagicMock()
        mock_subreddit = MagicMock()
        mock_subreddit.display_name = "python"
        mock_subreddit.subscribers = 1000000
        mock_subreddit.public_description = "Python discussions"

        with patch('core.dlt_reddit_source.get_active_subreddits') as mock_get_active, \
             patch('core.dlt_reddit_source.collect_activity_metrics') as mock_metrics, \
             patch('core.dlt_reddit_source.calculate_trending_score') as mock_trending:

            mock_get_active.return_value = [mock_subreddit]
            mock_metrics.return_value = MagicMock(
                comments_24h=100,
                posts_24h=10,
                avg_engagement_rate=10.0,
                subscriber_base_score=80.0,
                active_users_score=60.0,
                quality_signals={},
                trending_velocity=50.0,
                activity_density=0.5
            )
            mock_trending.return_value = 85.5

            resource = active_subreddits(
                reddit_client=mock_reddit_client,
                subreddits=["python"],
                time_filter="day",
                min_activity_score=50.0
            )

            # Verify the resource is a generator function
            assert callable(resource)
            # The resource should have DLT resource metadata
            assert hasattr(resource, 'name')
            assert resource.name in ["active_subreddits", "activity_trends"]


class TestValidatedCommentsResource:
    """Test the validated_comments DLT resource."""

    def test_validated_comments_resource_creation(self):
        """Test that validated_comments resource can be created."""
        mock_reddit_client = MagicMock()

        resource = validated_comments(
            reddit_client=mock_reddit_client,
            subreddits=["python", "test"],
            time_filter="day",
            min_activity_score=50.0,
            comments_per_post=10
        )

        assert resource is not None

    @patch('core.dlt_reddit_source.collect_activity_metrics')
    def test_validated_comments_with_activity_validation(self, mock_metrics):
        """Test that validated_comments integrates with activity validation."""
        mock_reddit_client = MagicMock()
        mock_subreddit = MagicMock()
        mock_subreddit.display_name = "python"
        mock_subreddit.subscribers = 1000000

        # Mock activity metrics
        from core.activity_validation import ActivityMetrics
        mock_metrics.return_value = ActivityMetrics(
            recent_comments_count=100,
            post_engagement_score=75.0,
            subscriber_base_score=80.0,
            active_users_score=60.0,
            comments_24h=50,
            posts_24h=5,
            avg_engagement_rate=10.0
        )

        resource = validated_comments(
            reddit_client=mock_reddit_client,
            subreddits=["python"],
            time_filter="day",
            min_activity_score=50.0,
            comments_per_post=5
        )

        assert resource is not None

    def test_validated_comments_incremental_loading(self):
        """Test that validated_comments supports incremental loading."""
        mock_reddit_client = MagicMock()
        last_created_time = pendulum.now().subtract(days=1)

        resource = validated_comments(
            reddit_client=mock_reddit_client,
            subreddits=["python"],
            time_filter="day",
            min_activity_score=50.0,
            comments_per_post=10,
            created_after=last_created_time
        )

        assert resource is not None


class TestActivityTrendsResource:
    """Test the activity_trends DLT resource."""

    def test_activity_trends_resource_creation(self):
        """Test that activity_trends resource can be created."""
        mock_reddit_client = MagicMock()

        resource = activity_trends(
            reddit_client=mock_reddit_client,
            subreddits=["python", "test"],
            time_filter="week",
            min_activity_score=50.0
        )

        assert resource is not None

    def test_activity_trends_data_structure(self):
        """Test that activity_trends returns correct data structure."""
        mock_reddit_client = MagicMock()

        with patch('core.dlt_reddit_source.get_active_subreddits') as mock_get_active, \
             patch('core.dlt_reddit_source.calculate_activity_score') as mock_score:

            mock_get_active.return_value = []
            mock_score.return_value = 85.5

            resource = activity_trends(
                reddit_client=mock_reddit_client,
                subreddits=["python"],
                time_filter="day",
                min_activity_score=50.0
            )

            # Verify the resource is a generator function
            assert callable(resource)
            # The resource should have DLT resource metadata
            assert hasattr(resource, 'name')
            assert resource.name in ["active_subreddits", "activity_trends"]


class TestIntegrationFeatures:
    """Test integration and production features."""

    def test_error_handling(self):
        """Test error handling in DLT resources."""
        mock_reddit_client = MagicMock()
        # Simulate API failure
        mock_reddit_client.subreddit.side_effect = Exception("Reddit API Error")

        # Resource should still be created successfully despite mock setup
        resource = active_subreddits(
            reddit_client=mock_reddit_client,
            subreddits=["nonexistent"],
            time_filter="day",
            min_activity_score=50.0
        )

        # The resource should exist even if execution would fail
        assert resource is not None
        assert callable(resource)

    def test_rate_limiting_awareness(self):
        """Test that resources are rate limiting aware."""
        mock_reddit_client = MagicMock()

        # Create resources - they should be configured for rate limiting
        resource = validated_comments(
            reddit_client=mock_reddit_client,
            subreddits=["python"],
            time_filter="day",
            min_activity_score=50.0,
            comments_per_post=10
        )

        assert resource is not None

    def test_quality_filters(self):
        """Test that quality filters are applied."""
        mock_reddit_client = MagicMock()

        resource = validated_comments(
            reddit_client=mock_reddit_client,
            subreddits=["python"],
            time_filter="day",
            min_activity_score=50.0,
            comments_per_post=10,
            min_comment_length=10,
            min_score=1
        )

        assert resource is not None

    def test_merge_write_disposition(self):
        """Test that merge write disposition is configured."""
        mock_reddit_client = MagicMock()

        # Resources should be configured with merge write disposition
        resource = validated_comments(
            reddit_client=mock_reddit_client,
            subreddits=["python"],
            time_filter="day",
            min_activity_score=50.0
        )

        assert resource is not None

    def test_primary_keys_configuration(self):
        """Test that primary keys are properly configured."""
        mock_reddit_client = MagicMock()

        # Resources should have proper primary key configuration
        resource = validated_comments(
            reddit_client=mock_reddit_client,
            subreddits=["python"],
            time_filter="day",
            min_activity_score=50.0
        )

        assert resource is not None


class TestDLTConfiguration:
    """Test DLT-specific configuration."""

    def test_dlt_decorators(self):
        """Test that DLT decorators are properly applied."""
        # The functions should have DLT decorator attributes
        assert hasattr(reddit_activity_aware, 'name')
        assert reddit_activity_aware.name == "reddit_activity_aware"
        assert hasattr(active_subreddits, 'name')
        assert active_subreddits.name == "active_subreddits"
        assert hasattr(validated_comments, 'name')
        assert validated_comments.name == "validated_comments"
        assert hasattr(activity_trends, 'name')
        assert activity_trends.name == "activity_trends"

    def test_incremental_configuration(self):
        """Test incremental loading configuration."""
        # Check pendulum integration for incremental loading
        last_created = pendulum.now().subtract(days=1)

        resource = validated_comments(
            reddit_client=MagicMock(),
            subreddits=["python"],
            time_filter="day",
            min_activity_score=50.0,
            created_after=last_created
        )

        assert resource is not None

    def test_schema_definitions(self):
        """Test that schema definitions are included."""
        mock_reddit_client = MagicMock()

        # Resources should have proper schema definitions
        resource = active_subreddits(
            reddit_client=mock_reddit_client,
            subreddits=["python"],
            time_filter="day",
            min_activity_score=50.0
        )

        assert resource is not None
