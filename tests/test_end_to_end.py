#!/usr/bin/env python3
"""
End-to-End Tests for RedditHarbor DLT Activity Validation System

This module provides comprehensive end-to-end testing that validates the complete
RedditHarbor DLT pipeline from Reddit API simulation to data storage simulation.
Tests cover the full workflow including:

- DLT pipeline creation and execution
- Reddit API mocking and simulation
- Activity validation integration
- Data transformation and loading
- Error handling and recovery scenarios
- Performance and memory usage validation

Usage:
    pytest tests/test_end_to_end.py -v
    python -m tests.test_end_to_end
"""

import gc
import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class MockRedditData:
    """Mock Reddit data generator for testing purposes."""

    @staticmethod
    def create_mock_subreddit(name: str, subscribers: int = 10000) -> Mock:
        """Create a mock subreddit object."""
        subreddit = Mock()
        subreddit.display_name = name
        subreddit.subscribers = subscribers
        subreddit.public_description = f"Mock subreddit for {name}"
        subreddit.over18 = False
        subreddit.restricted = False
        subreddit.subreddit_type = "public"

        # Add methods for comments and posts
        subreddit.comments.return_value = Mock()
        subreddit.top.return_value = Mock()
        subreddit.new.return_value = Mock()
        subreddit.hot.return_value = Mock()

        return subreddit

    @staticmethod
    def create_mock_comment(
        comment_id: str,
        body: str,
        score: int = 5,
        author: str = "test_user",
        created_utc: int = 1704067200
    ) -> Mock:
        """Create a mock comment object."""
        comment = Mock()
        comment.id = comment_id
        comment.body = body
        comment.score = score
        comment.author = Mock()
        comment.author.name = author
        comment.author.__str__ = lambda: author
        comment.created_utc = created_utc
        comment.edited = False
        comment.stickied = False
        comment.parent_id = f"t1_parent_{comment_id}"
        comment.permalink = f"/r/test/comments/{comment_id}"
        comment.depth = 0

        return comment

    @staticmethod
    def create_mock_submission(
        submission_id: str,
        title: str,
        score: int = 10,
        num_comments: int = 5,
        author: str = "test_user",
        created_utc: int = 1704067200
    ) -> Mock:
        """Create a mock submission object."""
        submission = Mock()
        submission.id = submission_id
        submission.title = title
        submission.score = score
        submission.num_comments = num_comments
        submission.author = Mock()
        submission.author.name = author
        submission.author.__str__ = lambda: author
        submission.created_utc = created_utc
        submission.url = f"https://reddit.com/r/test/{submission_id}"
        submission.selftext = "This is a test submission content with some real problems and frustrations."
        submission.subreddit = Mock()
        submission.subreddit.display_name = "test"
        submission.permalink = f"/r/test/comments/{submission_id}"

        # Mock comments list
        submission.comments = Mock()
        submission.comments.list.return_value = [
            MockRedditData.create_mock_comment(f"c{i}", f"Test comment {i}")
            for i in range(num_comments)
        ]
        submission.comments.replace_more = Mock()

        return submission


class TestEndToEndDLTSystem:
    """End-to-end tests for the complete DLT system."""

    @pytest.fixture
    def mock_reddit_client(self):
        """Create a mock Reddit client for testing."""
        reddit = Mock()

        # Create mock subreddits
        subreddits = {
            "python": MockRedditData.create_mock_subreddit("python", 500000),
            "learnprogramming": MockRedditData.create_mock_subreddit("learnprogramming", 100000),
            "technology": MockRedditData.create_mock_subreddit("technology", 1000000),
            "inactive": MockRedditData.create_mock_subreddit("inactive", 100),
        }

        def subreddit_side_effect(name):
            return subreddits.get(name, MockRedditData.create_mock_subreddit(name, 0))

        reddit.subreddit.side_effect = subreddit_side_effect

        return reddit

    @pytest.fixture
    def mock_dlt_pipeline(self):
        """Create a mock DLT pipeline for testing."""
        pipeline = Mock()
        pipeline.run.return_value = Mock()
        pipeline.run.return_value.started_at = datetime.now(timezone.utc)
        pipeline.run.return_value.counts = {"python": 10, "learnprogramming": 5}

        return pipeline

    def test_dlt_imports_and_setup(self):
        """Test that all DLT dependencies can be imported."""
        try:
            import dlt
            import pendulum
            import praw
            from core.activity_validation import (
                calculate_activity_score,
                collect_activity_metrics,
                get_active_subreddits,
            )
            from core.dlt_reddit_source import (
                reddit_activity_aware,
                create_reddit_pipeline,
                run_reddit_collection,
            )

            # Verify DLT version
            assert hasattr(dlt, 'pipeline'), "DLT pipeline function not available"
            assert hasattr(dlt, 'source'), "DLT source decorator not available"
            assert hasattr(dlt, 'resource'), "DLT resource decorator not available"

            # Verify pendulum
            assert hasattr(pendulum, 'now'), "Pendulum now function not available"

            logger.info("✅ All DLT imports successful")

        except ImportError as e:
            pytest.fail(f"Failed to import DLT dependencies: {e}")

    def test_activity_validation_integration(self, mock_reddit_client):
        """Test activity validation integration with DLT."""
        try:
            from core.activity_validation import (
                calculate_activity_score,
                collect_activity_metrics,
                get_active_subreddits,
            )

            # Test individual subreddit validation
            subreddit = mock_reddit_client.subreddit("python")

            # Mock the API calls
            subreddit.comments.return_value = [
                MockRedditData.create_mock_comment(f"c{i}", f"Comment {i}")
                for i in range(20)
            ]
            subreddit.top.return_value = [
                MockRedditData.create_mock_submission(f"s{i}", f"Submission {i}", 50, 10)
                for i in range(10)
            ]

            # Test activity score calculation
            score = calculate_activity_score(subreddit, time_filter="day")
            assert isinstance(score, float), "Activity score should be a float"
            assert 0 <= score <= 100, "Activity score should be between 0-100"

            # Test metrics collection
            metrics = collect_activity_metrics(subreddit, time_filter="day")
            assert hasattr(metrics, 'recent_comments_count'), "Metrics should include recent comments"
            assert hasattr(metrics, 'post_engagement_score'), "Metrics should include engagement score"
            assert hasattr(metrics, 'subscriber_base_score'), "Metrics should include subscriber score"

            # Test active subreddit filtering
            test_subreddits = ["python", "learnprogramming", "inactive"]
            active_subs = get_active_subreddits(
                mock_reddit_client, test_subreddits, time_filter="day", min_activity_score=30.0
            )

            assert len(active_subs) >= 1, "Should find at least one active subreddit"
            logger.info(f"✅ Found {len(active_subs)} active subreddits")

        except Exception as e:
            pytest.fail(f"Activity validation integration test failed: {e}")

    def test_dlt_source_creation(self, mock_reddit_client):
        """Test DLT source creation and configuration."""
        try:
            from core.dlt_reddit_source import reddit_activity_aware

            test_subreddits = ["python", "learnprogramming"]

            # Mock Reddit API responses
            for subreddit_name in test_subreddits:
                subreddit = mock_reddit_client.subreddit(subreddit_name)
                subreddit.comments.return_value = [
                    MockRedditData.create_mock_comment(f"c{i}", f"Comment {i}")
                    for i in range(15)
                ]
                subreddit.top.return_value = [
                    MockRedditData.create_mock_submission(f"s{i}", f"Submission {i}", 30, 8)
                    for i in range(5)
                ]

            # Create DLT source
            source = reddit_activity_aware(
                reddit_client=mock_reddit_client,
                subreddits=test_subreddits,
                time_filter="day",
                min_activity_score=30.0
            )

            # Verify source structure
            assert hasattr(source, '__iter__'), "Source should be iterable"
            resources = list(source)
            assert len(resources) == 3, "Should have 3 resources (active_subreddits, validated_comments, activity_trends)"

            # Verify resource names and configurations
            resource_names = [getattr(resource, '__name__', 'unknown') for resource in resources]
            expected_resources = ['active_subreddits', 'validated_comments', 'activity_trends']

            for expected in expected_resources:
                assert expected in str(resources), f"Missing resource: {expected}"

            logger.info("✅ DLT source creation successful")

        except Exception as e:
            pytest.fail(f"DLT source creation test failed: {e}")

    @patch('core.dlt_reddit_source.dlt.pipeline')
    def test_dlt_pipeline_creation(self, mock_dlt_pipeline_func, mock_reddit_client):
        """Test DLT pipeline creation and configuration."""
        try:
            from core.dlt_reddit_source import create_reddit_pipeline

            # Mock the pipeline creation
            mock_pipeline = Mock()
            mock_dlt_pipeline_func.return_value = mock_pipeline

            # Create pipeline
            pipeline = create_reddit_pipeline(
                pipeline_name="test_pipeline",
                destination="postgres",
                dataset_name="test_data"
            )

            # Verify pipeline creation was called correctly
            mock_dlt_pipeline_func.assert_called_once_with(
                pipeline_name="test_pipeline",
                destination="postgres",
                dataset_name="test_data"
            )

            assert pipeline is mock_pipeline, "Should return the created pipeline"

            logger.info("✅ DLT pipeline creation successful")

        except Exception as e:
            pytest.fail(f"DLT pipeline creation test failed: {e}")

    def test_data_transformation_and_schema(self):
        """Test data transformation to match Supabase schema."""
        try:
            from core.dlt_collection import transform_submission_to_schema, transform_comment_to_schema

            # Test submission transformation
            raw_submission = {
                "id": "test123",
                "title": "Test Submission with Problem Keywords",
                "selftext": "I'm struggling with this frustrating and time consuming task",
                "author": "test_user",
                "created_utc": 1704067200,
                "subreddit": "test",
                "score": 25,
                "url": "https://reddit.com/r/test/test123",
                "num_comments": 10,
            }

            transformed_submission = transform_submission_to_schema(raw_submission)

            # Verify required fields
            assert "submission_id" in transformed_submission, "Should have submission_id"
            assert "title" in transformed_submission, "Should have title"
            assert "text" in transformed_submission, "Should have text"
            assert "content" in transformed_submission, "Should have content"
            assert "subreddit" in transformed_submission, "Should have subreddit"
            assert "upvotes" in transformed_submission, "Should have upvotes"
            assert "comments_count" in transformed_submission, "Should have comments_count"
            assert "created_at" in transformed_submission, "Should have created_at"

            # Test comment transformation
            raw_comment = {
                "comment_id": "comment123",
                "submission_id": "test123",
                "link_id": "t3_test123",
                "author": "test_user",
                "body": "This is a test comment",
                "score": 5,
                "created_utc": 1704067200,
                "parent_id": "t3_test123",
                "depth": 0,
                "subreddit": "test",
            }

            transformed_comment = transform_comment_to_schema(raw_comment)

            # Verify required fields
            assert "comment_id" in transformed_comment, "Should have comment_id"
            assert "submission_id" in transformed_comment, "Should have submission_id"
            assert "link_id" in transformed_comment, "Should have link_id"
            assert "body" in transformed_comment, "Should have body"
            assert "content" in transformed_comment, "Should have content"
            assert "score" in transformed_comment, "Should have score"
            assert "created_at" in transformed_comment, "Should have created_at"
            assert "parent_id" in transformed_comment, "Should have parent_id"
            assert "depth" in transformed_comment, "Should have depth"

            logger.info("✅ Data transformation validation successful")

        except Exception as e:
            pytest.fail(f"Data transformation test failed: {e}")

    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios."""
        try:
            from core.activity_validation import calculate_activity_score

            # Test with None subreddit
            score = calculate_activity_score(None, time_filter="day")
            assert score == 0.0, "Should return 0 for None subreddit"

            # Test with invalid subreddit object
            invalid_subreddit = Mock()
            del invalid_subreddit.display_name  # Remove required attribute

            score = calculate_activity_score(invalid_subreddit, time_filter="day")
            assert score == 0.0, "Should return 0 for invalid subreddit"

            # Test with valid subreddit but API errors
            valid_subreddit = MockRedditData.create_mock_subreddit("test")
            valid_subreddit.comments.side_effect = Exception("API Error")

            # Should handle API errors gracefully
            score = calculate_activity_score(valid_subreddit, time_filter="day")
            assert isinstance(score, float), "Should return a float even on errors"

            logger.info("✅ Error handling validation successful")

        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")

    def test_performance_and_memory_usage(self, mock_reddit_client):
        """Test performance and memory usage of the DLT system."""
        try:
            import psutil
            import os

            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            logger.info(f"Initial memory usage: {initial_memory:.2f} MB")

            from core.dlt_reddit_source import reddit_activity_aware
            from core.activity_validation import calculate_activity_score

            # Test with multiple subreddits
            test_subreddits = ["python", "learnprogramming", "technology"] * 10  # 30 subreddits

            # Mock API responses
            for subreddit_name in set(test_subreddits):
                subreddit = mock_reddit_client.subreddit(subreddit_name)
                subreddit.comments.return_value = [
                    MockRedditData.create_mock_comment(f"c{i}", f"Comment {i}")
                    for i in range(50)
                ]
                subreddit.top.return_value = [
                    MockRedditData.create_mock_submission(f"s{i}", f"Submission {i}", 100, 20)
                    for i in range(25)
                ]

            # Test performance metrics
            start_time = time.time()

            # Create DLT source (this should be fast)
            source = reddit_activity_aware(
                reddit_client=mock_reddit_client,
                subreddits=test_subreddits,
                time_filter="day",
                min_activity_score=30.0
            )

            creation_time = time.time() - start_time
            logger.info(f"DLT source creation time: {creation_time:.3f} seconds")

            # Test individual calculations
            calc_start = time.time()

            for subreddit_name in test_subreddits[:10]:  # Test first 10
                subreddit = mock_reddit_client.subreddit(subreddit_name)
                score = calculate_activity_score(subreddit, time_filter="day")
                assert isinstance(score, float), f"Invalid score for {subreddit_name}"

            calc_time = time.time() - calc_start
            logger.info(f"Activity score calculation time: {calc_time:.3f} seconds")

            # Check memory usage after processing
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory

            logger.info(f"Peak memory usage: {peak_memory:.2f} MB")
            logger.info(f"Memory increase: {memory_increase:.2f} MB")

            # Performance assertions
            assert creation_time < 5.0, f"Source creation too slow: {creation_time:.3f}s"
            assert calc_time < 10.0, f"Score calculation too slow: {calc_time:.3f}s"
            assert memory_increase < 100, f"Memory usage too high: {memory_increase:.2f}MB"

            # Force garbage collection
            gc.collect()

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            logger.info(f"Memory after GC: {final_memory:.2f} MB")

            logger.info("✅ Performance and memory usage validation successful")

        except ImportError:
            logger.warning("psutil not available, skipping memory usage tests")
        except Exception as e:
            pytest.fail(f"Performance test failed: {e}")

    def test_configuration_and_settings(self):
        """Test configuration and settings loading."""
        try:
            from config.settings import (
                DLT_MIN_ACTIVITY_SCORE,
                DLT_TIME_FILTER,
                DLT_PIPELINE_NAME,
                DLT_DATASET_NAME,
                DLT_QUALITY_MIN_COMMENT_LENGTH,
                DLT_QUALITY_MIN_SCORE,
                DLT_QUALITY_COMMENTS_PER_POST,
                DLT_ENABLED,
                DLT_USE_ACTIVITY_VALIDATION,
                DLT_MAX_SUBREDDITS_PER_RUN,
            )

            # Verify configuration values
            assert isinstance(DLT_MIN_ACTIVITY_SCORE, float), "DLT_MIN_ACTIVITY_SCORE should be float"
            assert 0 <= DLT_MIN_ACTIVITY_SCORE <= 100, "DLT_MIN_ACTIVITY_SCORE should be between 0-100"
            assert isinstance(DLT_TIME_FILTER, str), "DLT_TIME_FILTER should be string"
            assert isinstance(DLT_PIPELINE_NAME, str), "DLT_PIPELINE_NAME should be string"
            assert isinstance(DLT_DATASET_NAME, str), "DLT_DATASET_NAME should be string"
            assert isinstance(DLT_QUALITY_MIN_COMMENT_LENGTH, int), "DLT_QUALITY_MIN_COMMENT_LENGTH should be int"
            assert isinstance(DLT_QUALITY_MIN_SCORE, int), "DLT_QUALITY_MIN_SCORE should be int"
            assert isinstance(DLT_QUALITY_COMMENTS_PER_POST, int), "DLT_QUALITY_COMMENTS_PER_POST should be int"
            assert isinstance(DLT_ENABLED, bool), "DLT_ENABLED should be boolean"
            assert isinstance(DLT_USE_ACTIVITY_VALIDATION, bool), "DLT_USE_ACTIVITY_VALIDATION should be boolean"
            assert isinstance(DLT_MAX_SUBREDDITS_PER_RUN, int), "DLT_MAX_SUBREDDITS_PER_RUN should be int"

            logger.info("✅ Configuration validation successful")

        except Exception as e:
            pytest.fail(f"Configuration test failed: {e}")

    def test_dry_run_simulation(self, mock_reddit_client):
        """Test dry run simulation without actual API calls."""
        try:
            from core.dlt_collection import collect_problem_posts
            from core.dlt_reddit_source import reddit_activity_aware

            test_subreddits = ["python", "learnprogramming"]

            # Test problem post collection in test mode
            problem_posts = collect_problem_posts(
                subreddits=test_subreddits,
                limit=5,
                sort_type="new",
                test_mode=True  # Use test data
            )

            assert isinstance(problem_posts, list), "Should return a list"
            assert len(problem_posts) > 0, "Should return mock data in test mode"

            # Verify problem post structure
            for post in problem_posts:
                assert "submission_id" in post, "Should have submission_id"
                assert "title" in post, "Should have title"
                assert "subreddit" in post, "Should have subreddit"
                assert "created_at" in post, "Should have created_at"

            # Test DLT source with mock data
            source = reddit_activity_aware(
                reddit_client=mock_reddit_client,
                subreddits=test_subreddits,
                time_filter="day",
                min_activity_score=30.0
            )

            # Verify source was created without errors
            resources = list(source)
            assert len(resources) == 3, "Should create 3 resources"

            logger.info("✅ Dry run simulation successful")

        except Exception as e:
            pytest.fail(f"Dry run simulation test failed: {e}")


class TestEndToEndIntegration:
    """Integration tests for complete workflow scenarios."""

    def test_complete_workflow_simulation(self):
        """Test complete workflow from start to finish."""
        try:
            # This test simulates the complete workflow that would run in production

            # 1. Configuration loading
            from config.settings import DEFAULT_SUBREDDITS, DLT_MIN_ACTIVITY_SCORE

            test_subreddits = DEFAULT_SUBREDDITS[:3]  # Use first 3 subreddits

            # 2. Mock Reddit client setup
            mock_reddit = Mock()

            # Create mock subreddits with varying activity levels
            mock_subreddits = {}
            for name in test_subreddits:
                mock_subreddits[name] = MockRedditData.create_mock_subreddit(
                    name,
                    subscribers=100000 + hash(name) % 900000  # Varying subscriber counts
                )

            mock_reddit.subreddit.side_effect = lambda name: mock_subreddits.get(name, None)

            # 3. Activity validation
            from core.activity_validation import get_active_subreddits, calculate_activity_score

            # Mock API responses for activity validation
            for subreddit in mock_subreddits.values():
                subreddit.comments.return_value = [
                    MockRedditData.create_mock_comment(f"c{i}", f"Comment content {i}")
                    for i in range(30)
                ]
                subreddit.top.return_value = [
                    MockRedditData.create_mock_submission(f"s{i}", f"Submission title {i}", 100, 25)
                    for i in range(20)
                ]

            active_subs = get_active_subreddits(
                mock_reddit, test_subreddits, time_filter="day", min_activity_score=30.0
            )

            assert len(active_subs) >= 2, "Should find at least 2 active subreddits"

            # 4. DLT source creation
            from core.dlt_reddit_source import reddit_activity_aware

            source = reddit_activity_aware(
                reddit_client=mock_reddit,
                subreddits=test_subreddits,
                time_filter="day",
                min_activity_score=DLT_MIN_ACTIVITY_SCORE
            )

            resources = list(source)
            assert len(resources) == 3, "Should have 3 DLT resources"

            # 5. Resource validation
            for resource in resources:
                assert hasattr(resource, '__iter__'), "Resource should be iterable"
                assert hasattr(resource, '__name__'), "Resource should have name"

            # 6. Data transformation validation
            from core.dlt_collection import collect_problem_posts, transform_submission_to_schema

            # Test problem post collection with test data
            problem_posts = collect_problem_posts(
                subreddits=test_subreddits[:2],
                limit=3,
                sort_type="new",
                test_mode=True
            )

            assert len(problem_posts) == 6, "Should collect 6 posts (3 per subreddit)"

            # Transform each post
            for post in problem_posts:
                transformed = transform_submission_to_schema(post)
                assert "submission_id" in transformed, "Transformed post should have submission_id"
                assert "created_at" in transformed, "Transformed post should have created_at"

            logger.info("✅ Complete workflow simulation successful")

        except Exception as e:
            error_msg = f"Complete workflow test failed: {e}\n{traceback.format_exc()}"
            pytest.fail(error_msg)


if __name__ == "__main__":
    # Run tests manually if executed directly
    pytest.main([__file__, "-v", "--tb=short"])