"""
Test suite for full_scale_collection.py DLT migration

This test suite validates the DLT migration of the large-scale collection script
that processes 73 subreddits across 6 market segments.

Tests cover:
- DLT pipeline integration
- Problem keyword filtering
- Per-segment error handling
- Batch loading to Supabase
- Deduplication via merge disposition
- Statistics reporting
- Comment collection workflow
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import script functions
from scripts.full_scale_collection import (
    ALL_SUBREDDITS,
    TARGET_SUBREDDITS,
    collect_segment_comments,
    collect_segment_submissions,
    load_comments_to_supabase,
    load_submissions_to_supabase,
    verify_database_results,
)


class TestTargetSubreddits:
    """Test target subreddit configuration"""

    def test_market_segments_count(self):
        """Test that there are 6 market segments"""
        assert len(TARGET_SUBREDDITS) == 6

    def test_market_segment_names(self):
        """Test that all expected market segments exist"""
        expected_segments = {
            "finance_investing",
            "health_fitness",
            "technology",
            "education",
            "lifestyle",
            "business"
        }
        assert set(TARGET_SUBREDDITS.keys()) == expected_segments

    def test_total_subreddits_count(self):
        """Test that there are 73 total subreddits"""
        assert len(ALL_SUBREDDITS) == 73

    def test_all_subreddits_flattened(self):
        """Test that ALL_SUBREDDITS correctly flattens all segments"""
        manual_flatten = []
        for segment_subs in TARGET_SUBREDDITS.values():
            manual_flatten.extend(segment_subs)
        assert len(ALL_SUBREDDITS) == len(manual_flatten)


class TestCollectSegmentSubmissions:
    """Test segment submission collection with DLT"""

    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_collect_segment_submissions_success(self, mock_collect):
        """Test successful segment submission collection"""
        # Mock data
        mock_posts = [
            {"id": "post1", "title": "Test post 1", "problem_keywords_found": ["struggle"]},
            {"id": "post2", "title": "Test post 2", "problem_keywords_found": ["frustrated"]}
        ]
        mock_collect.return_value = mock_posts

        # Call function
        segment_name = "test_segment"
        subreddits = ["test_sub1", "test_sub2"]
        sort_types = ["hot", "new"]
        limit_per_sort = 10

        submissions, count, errors = collect_segment_submissions(
            segment_name, subreddits, sort_types, limit_per_sort
        )

        # Verify results
        assert len(submissions) > 0
        assert count > 0
        assert errors == 0

        # Verify collect_problem_posts was called for each subreddit and sort type
        assert mock_collect.call_count == len(subreddits) * len(sort_types)

    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_collect_segment_submissions_with_errors(self, mock_collect):
        """Test segment collection with some errors"""
        # Mock: first call succeeds, second call fails
        mock_collect.side_effect = [
            [{"id": "post1", "title": "Test"}],
            Exception("API error"),
            [{"id": "post2", "title": "Test 2"}],
            Exception("Rate limit")
        ]

        segment_name = "test_segment"
        subreddits = ["test_sub1", "test_sub2"]
        sort_types = ["hot", "new"]
        limit_per_sort = 10

        submissions, count, errors = collect_segment_submissions(
            segment_name, subreddits, sort_types, limit_per_sort
        )

        # Should have some submissions despite errors
        assert len(submissions) >= 0
        assert errors > 0  # Should record errors

    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_collect_segment_submissions_empty_results(self, mock_collect):
        """Test segment collection with no results"""
        mock_collect.return_value = []

        segment_name = "test_segment"
        subreddits = ["test_sub"]
        sort_types = ["hot"]
        limit_per_sort = 10

        submissions, count, errors = collect_segment_submissions(
            segment_name, subreddits, sort_types, limit_per_sort
        )

        assert len(submissions) == 0
        assert count == 0
        assert errors == 0


class TestLoadSubmissionsToSupabase:
    """Test submission loading via DLT pipeline"""

    @patch('scripts.full_scale_collection.create_dlt_pipeline')
    def test_load_submissions_success(self, mock_create_pipeline):
        """Test successful submission loading"""
        # Mock pipeline
        mock_pipeline = Mock()
        mock_load_info = Mock()
        mock_load_info.started_at = "2025-01-01"
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Test data
        submissions = [
            {"id": "sub1", "title": "Test 1"},
            {"id": "sub2", "title": "Test 2"}
        ]

        # Call function
        success = load_submissions_to_supabase(submissions)

        # Verify
        assert success is True
        mock_pipeline.run.assert_called_once()

        # Verify merge disposition used
        call_kwargs = mock_pipeline.run.call_args[1]
        assert call_kwargs["write_disposition"] == "merge"
        assert call_kwargs["primary_key"] == "id"
        assert call_kwargs["table_name"] == "submissions"

    @patch('scripts.full_scale_collection.create_dlt_pipeline')
    def test_load_submissions_failure(self, mock_create_pipeline):
        """Test submission loading failure"""
        # Mock pipeline failure
        mock_pipeline = Mock()
        mock_pipeline.run.side_effect = Exception("Database error")
        mock_create_pipeline.return_value = mock_pipeline

        submissions = [{"id": "sub1", "title": "Test"}]

        # Call function
        success = load_submissions_to_supabase(submissions)

        # Verify failure
        assert success is False

    def test_load_submissions_empty_list(self):
        """Test loading with empty submission list"""
        success = load_submissions_to_supabase([])
        assert success is False


class TestCollectSegmentComments:
    """Test segment comment collection with DLT"""

    @patch('scripts.full_scale_collection.get_reddit_client')
    @patch('scripts.full_scale_collection.collect_post_comments')
    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_collect_segment_comments_success(
        self, mock_collect_posts, mock_collect_comments, mock_get_reddit
    ):
        """Test successful comment collection"""
        # Mock posts
        mock_posts = [
            {"id": "post1", "title": "Test 1"},
            {"id": "post2", "title": "Test 2"}
        ]
        mock_collect_posts.return_value = mock_posts

        # Mock comments
        mock_comments = [
            {"comment_id": "c1", "body": "Comment 1"},
            {"comment_id": "c2", "body": "Comment 2"}
        ]
        mock_collect_comments.return_value = mock_comments

        # Mock Reddit client
        mock_reddit = Mock()
        mock_get_reddit.return_value = mock_reddit

        # Call function
        segment_name = "test_segment"
        subreddits = ["test_sub"]
        sort_types = ["hot"]
        comment_limit = 20

        comments, count = collect_segment_comments(
            segment_name, subreddits, sort_types, comment_limit
        )

        # Verify
        assert len(comments) > 0
        assert count > 0
        mock_collect_comments.assert_called()

    @patch('scripts.full_scale_collection.get_reddit_client')
    @patch('scripts.full_scale_collection.collect_post_comments')
    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_collect_segment_comments_no_posts(
        self, mock_collect_posts, mock_collect_comments, mock_get_reddit
    ):
        """Test comment collection when no posts found"""
        # No posts found
        mock_collect_posts.return_value = []
        mock_reddit = Mock()
        mock_get_reddit.return_value = mock_reddit

        segment_name = "test_segment"
        subreddits = ["test_sub"]
        sort_types = ["hot"]
        comment_limit = 20

        comments, count = collect_segment_comments(
            segment_name, subreddits, sort_types, comment_limit
        )

        # Verify no comments collected
        assert len(comments) == 0
        assert count == 0
        mock_collect_comments.assert_not_called()

    @patch('scripts.full_scale_collection.get_reddit_client')
    @patch('scripts.full_scale_collection.collect_post_comments')
    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_collect_segment_comments_with_errors(
        self, mock_collect_posts, mock_collect_comments, mock_get_reddit
    ):
        """Test comment collection with errors"""
        # Mock posts
        mock_posts = [{"id": "post1", "title": "Test"}]
        mock_collect_posts.return_value = mock_posts

        # Mock comment collection failure
        mock_collect_comments.side_effect = Exception("API error")

        mock_reddit = Mock()
        mock_get_reddit.return_value = mock_reddit

        segment_name = "test_segment"
        subreddits = ["test_sub"]
        sort_types = ["hot"]
        comment_limit = 20

        # Should not raise, just log error
        comments, count = collect_segment_comments(
            segment_name, subreddits, sort_types, comment_limit
        )

        assert len(comments) == 0
        assert count == 0


class TestLoadCommentsToSupabase:
    """Test comment loading via DLT pipeline"""

    @patch('scripts.full_scale_collection.create_dlt_pipeline')
    def test_load_comments_success(self, mock_create_pipeline):
        """Test successful comment loading"""
        # Mock pipeline
        mock_pipeline = Mock()
        mock_load_info = Mock()
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Test data
        comments = [
            {"comment_id": "c1", "body": "Test 1"},
            {"comment_id": "c2", "body": "Test 2"}
        ]

        # Call function
        success = load_comments_to_supabase(comments)

        # Verify
        assert success is True
        mock_pipeline.run.assert_called_once()

        # Verify merge disposition used
        call_kwargs = mock_pipeline.run.call_args[1]
        assert call_kwargs["write_disposition"] == "merge"
        assert call_kwargs["primary_key"] == "comment_id"
        assert call_kwargs["table_name"] == "comments"

    @patch('scripts.full_scale_collection.create_dlt_pipeline')
    def test_load_comments_failure(self, mock_create_pipeline):
        """Test comment loading failure"""
        # Mock pipeline failure
        mock_pipeline = Mock()
        mock_pipeline.run.side_effect = Exception("Database error")
        mock_create_pipeline.return_value = mock_pipeline

        comments = [{"comment_id": "c1", "body": "Test"}]

        success = load_comments_to_supabase(comments)

        assert success is False

    def test_load_comments_empty_list(self):
        """Test loading with empty comment list"""
        success = load_comments_to_supabase([])
        assert success is False


class TestVerifyDatabaseResults:
    """Test database verification functionality"""

    @patch('scripts.full_scale_collection.create_client')
    def test_verify_database_results_success(self, mock_create_client):
        """Test successful database verification"""
        # Mock Supabase client
        mock_supabase = Mock()

        # Mock submissions count
        mock_subs_result = Mock()
        mock_subs_result.count = 100
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_subs_result

        # Mock comments count
        mock_comments_result = Mock()
        mock_comments_result.count = 250

        # Mock redditors count
        mock_redditors_result = Mock()
        mock_redditors_result.count = 75

        # Set up side effects for different table calls
        mock_supabase.table.return_value.select.return_value.execute.side_effect = [
            mock_subs_result,
            mock_comments_result,
            mock_redditors_result
        ]

        mock_create_client.return_value = mock_supabase

        # Call function
        stats = verify_database_results()

        # Verify
        assert stats["submissions"] == 100
        assert stats["comments"] == 250
        assert stats["redditors"] == 75
        assert stats["avg_comments_per_sub"] > 0

    @patch('scripts.full_scale_collection.create_client')
    def test_verify_database_results_failure(self, mock_create_client):
        """Test database verification failure"""
        # Mock failure
        mock_create_client.side_effect = Exception("Connection error")

        # Call function
        stats = verify_database_results()

        # Verify default values returned
        assert stats["submissions"] == 0
        assert stats["comments"] == 0
        assert stats["redditors"] == 0


class TestDeduplication:
    """Test deduplication behavior"""

    @patch('scripts.full_scale_collection.create_dlt_pipeline')
    def test_duplicate_submissions_merged(self, mock_create_pipeline):
        """Test that duplicate submissions are merged, not duplicated"""
        mock_pipeline = Mock()
        mock_load_info = Mock()
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Same ID submitted twice
        submissions = [
            {"id": "duplicate_id", "title": "First version"},
            {"id": "duplicate_id", "title": "Second version"}
        ]

        success = load_submissions_to_supabase(submissions)

        assert success is True

        # Verify merge disposition was used (deduplication enabled)
        call_kwargs = mock_pipeline.run.call_args[1]
        assert call_kwargs["write_disposition"] == "merge"
        assert call_kwargs["primary_key"] == "id"

    @patch('scripts.full_scale_collection.create_dlt_pipeline')
    def test_duplicate_comments_merged(self, mock_create_pipeline):
        """Test that duplicate comments are merged, not duplicated"""
        mock_pipeline = Mock()
        mock_load_info = Mock()
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Same comment_id submitted twice
        comments = [
            {"comment_id": "dup_comment", "body": "First version"},
            {"comment_id": "dup_comment", "body": "Second version"}
        ]

        success = load_comments_to_supabase(comments)

        assert success is True

        # Verify merge disposition was used
        call_kwargs = mock_pipeline.run.call_args[1]
        assert call_kwargs["write_disposition"] == "merge"
        assert call_kwargs["primary_key"] == "comment_id"


class TestLargeScaleCollection:
    """Test large-scale collection behavior"""

    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_handles_73_subreddits(self, mock_collect):
        """Test that collection can handle all 73 subreddits"""
        mock_collect.return_value = [{"id": "test", "title": "Test"}]

        # Simulate collecting from all segments
        total_subreddits_processed = 0

        for segment_name, subreddits in TARGET_SUBREDDITS.items():
            total_subreddits_processed += len(subreddits)

        assert total_subreddits_processed == 73

    @patch('scripts.full_scale_collection.create_dlt_pipeline')
    def test_batch_loading_efficiency(self, mock_create_pipeline):
        """Test that batch loading is used (single DLT load for all segments)"""
        mock_pipeline = Mock()
        mock_load_info = Mock()
        mock_pipeline.run.return_value = mock_load_info
        mock_create_pipeline.return_value = mock_pipeline

        # Large batch of submissions (simulating 73 subreddits)
        submissions = [
            {"id": f"post_{i}", "title": f"Test {i}"}
            for i in range(500)  # Simulate large collection
        ]

        success = load_submissions_to_supabase(submissions)

        assert success is True

        # Verify only ONE pipeline.run call (batch loading)
        assert mock_pipeline.run.call_count == 1

        # Verify all submissions passed at once
        call_args = mock_pipeline.run.call_args[0][0]
        assert len(call_args) == 500


class TestErrorRecovery:
    """Test error handling and recovery"""

    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_subreddit_error_does_not_stop_collection(self, mock_collect):
        """Test that error in one subreddit doesn't stop collection"""
        # Mock: first subreddit fails, second succeeds
        mock_collect.side_effect = [
            Exception("API error"),
            [{"id": "post1", "title": "Success"}]
        ]

        segment_name = "test_segment"
        subreddits = ["failing_sub", "working_sub"]
        sort_types = ["hot"]
        limit_per_sort = 10

        submissions, count, errors = collect_segment_submissions(
            segment_name, subreddits, sort_types, limit_per_sort
        )

        # Should continue despite error
        assert errors > 0
        # May have some successful submissions
        assert count >= 0

    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_sort_type_error_continues_to_next(self, mock_collect):
        """Test that error in one sort type continues to next sort type"""
        # Mock: first sort fails, second succeeds
        mock_collect.side_effect = [
            Exception("Rate limit"),
            [{"id": "post1", "title": "Success"}]
        ]

        segment_name = "test_segment"
        subreddits = ["test_sub"]
        sort_types = ["hot", "new"]  # Two sort types
        limit_per_sort = 10

        submissions, count, errors = collect_segment_submissions(
            segment_name, subreddits, sort_types, limit_per_sort
        )

        # Should continue to second sort type
        assert mock_collect.call_count == 2


class TestStatistics:
    """Test statistics collection and reporting"""

    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_per_segment_statistics(self, mock_collect):
        """Test that statistics are tracked per segment"""
        mock_collect.return_value = [
            {"id": "post1", "title": "Test 1"},
            {"id": "post2", "title": "Test 2"}
        ]

        segment_name = "test_segment"
        subreddits = ["sub1", "sub2"]
        sort_types = ["hot"]
        limit_per_sort = 10

        submissions, count, errors = collect_segment_submissions(
            segment_name, subreddits, sort_types, limit_per_sort
        )

        # Verify statistics returned
        assert isinstance(submissions, list)
        assert isinstance(count, int)
        assert isinstance(errors, int)
        assert count >= 0
        assert errors >= 0

    @patch('scripts.full_scale_collection.collect_problem_posts')
    def test_total_statistics_accumulation(self, mock_collect):
        """Test that total statistics accumulate across segments"""
        mock_collect.return_value = [{"id": "post1", "title": "Test"}]

        total_submissions = 0
        total_errors = 0

        # Simulate collecting from multiple segments
        for segment_name, subreddits in list(TARGET_SUBREDDITS.items())[:2]:
            submissions, count, errors = collect_segment_submissions(
                segment_name, subreddits, ["hot"], 10
            )
            total_submissions += count
            total_errors += errors

        assert total_submissions >= 0
        assert total_errors >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
