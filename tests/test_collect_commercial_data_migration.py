#!/usr/bin/env python3
"""
Unit Tests for collect_commercial_data.py DLT Migration

Tests the migration from direct PRAW collection to DLT pipeline with commercial
signal detection and filtering.

Test Coverage:
- Commercial keyword detection
- Commercial post filtering
- DLT integration
- Deduplication
- Statistics reporting
- Error handling
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.collect_commercial_data import (
    BUSINESS_KEYWORDS,
    MONETIZATION_KEYWORDS,
    TOP_COMMERCIAL_SUBREDDITS,
    collect_commercial_data,
    contains_commercial_keywords,
    filter_commercial_posts,
)


class TestCommercialKeywordDetection:
    """Test commercial keyword detection logic."""

    def test_contains_commercial_keywords_with_business_terms(self):
        """Test detection of business keywords."""
        text = "Our startup is looking for a tool to help with client management"
        assert contains_commercial_keywords(text, min_keywords=1) is True

    def test_contains_commercial_keywords_with_monetization_terms(self):
        """Test detection of monetization keywords."""
        text = "I would pay $50/month for a subscription service that solves this"
        assert contains_commercial_keywords(text, min_keywords=1) is True

    def test_contains_commercial_keywords_with_multiple_terms(self):
        """Test detection of multiple commercial keywords."""
        text = "Our company needs better revenue tracking for our B2B customers"
        found = contains_commercial_keywords(text, min_keywords=3)
        assert found is True

    def test_contains_commercial_keywords_without_commercial_terms(self):
        """Test no detection when commercial keywords absent."""
        text = "I like to play video games on weekends"
        assert contains_commercial_keywords(text, min_keywords=1) is False

    def test_contains_commercial_keywords_empty_text(self):
        """Test handling of empty text."""
        assert contains_commercial_keywords("", min_keywords=1) is False
        assert contains_commercial_keywords(None, min_keywords=1) is False

    def test_contains_commercial_keywords_case_insensitive(self):
        """Test case-insensitive keyword matching."""
        text = "BUSINESS REVENUE CUSTOMER"
        assert contains_commercial_keywords(text, min_keywords=1) is True


class TestCommercialPostFiltering:
    """Test commercial post filtering logic."""

    def test_filter_commercial_posts_keeps_commercial_posts(self):
        """Test that commercial posts are kept after filtering."""
        problem_posts = [
            {
                "id": "test1",
                "title": "My startup needs better customer management",
                "selftext": "We're a SaaS company struggling with client tracking",
                "subreddit": "startups",
                "problem_keywords_found": ["struggle", "needs"],
                "problem_keyword_count": 2
            },
            {
                "id": "test2",
                "title": "Looking for productivity tips",
                "selftext": "I waste too much time on email",
                "subreddit": "productivity",
                "problem_keywords_found": ["waste time"],
                "problem_keyword_count": 1
            }
        ]

        commercial_posts = filter_commercial_posts(problem_posts, min_commercial_keywords=1)

        # Only first post should pass (has commercial keywords)
        assert len(commercial_posts) == 1
        assert commercial_posts[0]["id"] == "test1"
        assert "commercial_keywords_found" in commercial_posts[0]
        assert "commercial_keyword_count" in commercial_posts[0]

    def test_filter_commercial_posts_adds_metadata(self):
        """Test that commercial metadata is added to filtered posts."""
        problem_posts = [
            {
                "id": "test1",
                "title": "Need pricing strategy for my startup",
                "selftext": "Looking for revenue optimization advice",
                "subreddit": "entrepreneur",
                "problem_keywords_found": ["need"],
                "problem_keyword_count": 1
            }
        ]

        commercial_posts = filter_commercial_posts(problem_posts, min_commercial_keywords=1)

        assert len(commercial_posts) == 1
        post = commercial_posts[0]
        assert "commercial_keywords_found" in post
        assert "commercial_keyword_count" in post
        assert "business_keywords" in post
        assert "monetization_keywords" in post
        assert post["commercial_keyword_count"] > 0

    def test_filter_commercial_posts_empty_list(self):
        """Test handling of empty post list."""
        commercial_posts = filter_commercial_posts([], min_commercial_keywords=1)
        assert commercial_posts == []

    def test_filter_commercial_posts_filters_all_non_commercial(self):
        """Test that non-commercial posts are completely filtered out."""
        problem_posts = [
            {
                "id": "test1",
                "title": "I love hiking",
                "selftext": "Nature is beautiful",
                "subreddit": "hiking",
                "problem_keywords_found": [],
                "problem_keyword_count": 0
            },
            {
                "id": "test2",
                "title": "Video game recommendations",
                "selftext": "What should I play?",
                "subreddit": "gaming",
                "problem_keywords_found": [],
                "problem_keyword_count": 0
            }
        ]

        commercial_posts = filter_commercial_posts(problem_posts, min_commercial_keywords=1)
        assert len(commercial_posts) == 0


class TestDLTIntegration:
    """Test DLT pipeline integration."""

    @patch('scripts.collect_commercial_data.collect_problem_posts')
    @patch('scripts.collect_commercial_data.load_to_supabase')
    def test_collect_commercial_data_test_mode(self, mock_load, mock_collect):
        """Test collection in test mode (no API calls)."""
        # Mock collect_problem_posts to return test data
        mock_collect.return_value = [
            {
                "id": "test1",
                "title": "Need help with startup pricing",
                "selftext": "Our SaaS business needs revenue optimization",
                "subreddit": "startups",
                "problem_keywords_found": ["need", "help"],
                "problem_keyword_count": 2,
                "score": 25
            }
        ]
        mock_load.return_value = True

        stats = collect_commercial_data(
            subreddits=["startups"],
            limit=10,
            test_mode=True
        )

        # Verify DLT functions were called
        mock_collect.assert_called_once()
        mock_load.assert_called_once()

        # Verify stats
        assert stats["success"] is True
        assert stats["total_collected"] == 1
        assert stats["commercial_posts"] == 1

    @patch('scripts.collect_commercial_data.collect_problem_posts')
    @patch('scripts.collect_commercial_data.load_to_supabase')
    def test_collect_commercial_data_no_posts_collected(self, mock_load, mock_collect):
        """Test handling when no posts are collected."""
        mock_collect.return_value = []

        stats = collect_commercial_data(
            subreddits=["startups"],
            limit=10,
            test_mode=True
        )

        # Should not attempt to load if no posts collected
        mock_load.assert_not_called()

        assert stats["success"] is False
        assert stats["total_collected"] == 0
        assert stats["commercial_posts"] == 0

    @patch('scripts.collect_commercial_data.collect_problem_posts')
    @patch('scripts.collect_commercial_data.load_to_supabase')
    def test_collect_commercial_data_filters_correctly(self, mock_load, mock_collect):
        """Test that commercial filtering is applied correctly."""
        # Mix of commercial and non-commercial posts
        mock_collect.return_value = [
            {
                "id": "commercial1",
                "title": "Startup needs customer management",
                "selftext": "Our business is growing",
                "subreddit": "startups",
                "problem_keywords_found": ["needs"],
                "problem_keyword_count": 1,
                "score": 30
            },
            {
                "id": "non_commercial1",
                "title": "I need better sleep",
                "selftext": "Having trouble sleeping",
                "subreddit": "sleep",
                "problem_keywords_found": ["trouble"],
                "problem_keyword_count": 1,
                "score": 20
            }
        ]
        mock_load.return_value = True

        stats = collect_commercial_data(
            subreddits=["startups", "sleep"],
            limit=10,
            test_mode=True
        )

        # Verify filtering worked
        assert stats["total_collected"] == 2
        assert stats["commercial_posts"] == 1
        assert stats["filter_rate"] == 50.0

        # Verify only commercial posts were loaded
        call_args = mock_load.call_args
        loaded_posts = call_args[0][0]
        assert len(loaded_posts) == 1
        assert loaded_posts[0]["id"] == "commercial1"

    @patch('scripts.collect_commercial_data.collect_problem_posts')
    @patch('scripts.collect_commercial_data.load_to_supabase')
    def test_collect_commercial_data_uses_merge_disposition(self, mock_load, mock_collect):
        """Test that merge write disposition is used for deduplication."""
        mock_collect.return_value = [
            {
                "id": "test1",
                "title": "Business revenue tracking",
                "selftext": "Need pricing strategy",
                "subreddit": "entrepreneur",
                "problem_keywords_found": ["need"],
                "problem_keyword_count": 1,
                "score": 40
            }
        ]
        mock_load.return_value = True

        collect_commercial_data(
            subreddits=["entrepreneur"],
            limit=10,
            test_mode=True
        )

        # Verify merge disposition is used
        call_args = mock_load.call_args
        assert call_args[1]["write_mode"] == "merge"

    @patch('scripts.collect_commercial_data.collect_problem_posts')
    @patch('scripts.collect_commercial_data.load_to_supabase')
    def test_collect_commercial_data_statistics_complete(self, mock_load, mock_collect):
        """Test that all statistics are calculated correctly."""
        mock_collect.return_value = [
            {
                "id": "test1",
                "title": "Startup customer management problem",
                "selftext": "Our company needs better revenue tracking",
                "subreddit": "startups",
                "problem_keywords_found": ["problem", "needs"],
                "problem_keyword_count": 2,
                "score": 50
            }
        ]
        mock_load.return_value = True

        stats = collect_commercial_data(
            subreddits=["startups"],
            limit=10,
            test_mode=True
        )

        # Verify all expected stats are present
        required_keys = [
            "success", "total_collected", "commercial_posts", "filter_rate",
            "collection_time", "load_time", "total_time",
            "avg_commercial_keywords", "avg_problem_keywords", "subreddits_processed"
        ]
        for key in required_keys:
            assert key in stats, f"Missing stat: {key}"

        assert stats["avg_commercial_keywords"] > 0
        assert stats["avg_problem_keywords"] > 0


class TestCommercialKeywordConstants:
    """Test that commercial keyword constants are properly defined."""

    def test_business_keywords_defined(self):
        """Test that business keywords list is non-empty."""
        assert len(BUSINESS_KEYWORDS) > 0
        assert "business" in BUSINESS_KEYWORDS
        assert "startup" in BUSINESS_KEYWORDS
        assert "customer" in BUSINESS_KEYWORDS

    def test_monetization_keywords_defined(self):
        """Test that monetization keywords list is non-empty."""
        assert len(MONETIZATION_KEYWORDS) > 0
        assert "pay" in MONETIZATION_KEYWORDS
        assert "subscription" in MONETIZATION_KEYWORDS
        assert "revenue" in MONETIZATION_KEYWORDS

    def test_top_commercial_subreddits_defined(self):
        """Test that target subreddits are properly defined."""
        assert len(TOP_COMMERCIAL_SUBREDDITS) == 5
        assert "smallbusiness" in TOP_COMMERCIAL_SUBREDDITS
        assert "startups" in TOP_COMMERCIAL_SUBREDDITS
        assert "SaaS" in TOP_COMMERCIAL_SUBREDDITS
        assert "entrepreneur" in TOP_COMMERCIAL_SUBREDDITS
        assert "indiehackers" in TOP_COMMERCIAL_SUBREDDITS


class TestEdgeCases:
    """Test edge cases and error handling."""

    @patch('scripts.collect_commercial_data.collect_problem_posts')
    @patch('scripts.collect_commercial_data.load_to_supabase')
    def test_collect_commercial_data_load_failure(self, mock_load, mock_collect):
        """Test handling when Supabase load fails."""
        mock_collect.return_value = [
            {
                "id": "test1",
                "title": "Business problem",
                "selftext": "Need startup advice",
                "subreddit": "startups",
                "problem_keywords_found": ["problem", "need"],
                "problem_keyword_count": 2,
                "score": 30
            }
        ]
        mock_load.return_value = False  # Simulate load failure

        stats = collect_commercial_data(
            subreddits=["startups"],
            limit=10,
            test_mode=True
        )

        # Should still return stats but with success=False
        assert stats["success"] is False
        assert stats["commercial_posts"] == 1  # Posts were filtered
        assert stats["total_collected"] == 1

    def test_filter_commercial_posts_with_high_threshold(self):
        """Test filtering with high keyword threshold."""
        problem_posts = [
            {
                "id": "test1",
                "title": "Business problem",  # Only 1 commercial keyword
                "selftext": "I have an issue",
                "subreddit": "startups",
                "problem_keywords_found": ["problem"],
                "problem_keyword_count": 1,
                "score": 20
            }
        ]

        # Require 3 commercial keywords (should filter out)
        commercial_posts = filter_commercial_posts(problem_posts, min_commercial_keywords=3)
        assert len(commercial_posts) == 0

    @patch('scripts.collect_commercial_data.collect_problem_posts')
    @patch('scripts.collect_commercial_data.load_to_supabase')
    def test_collect_commercial_data_all_filtered_out(self, mock_load, mock_collect):
        """Test when all posts are filtered out (no commercial keywords)."""
        mock_collect.return_value = [
            {
                "id": "test1",
                "title": "I need sleep",
                "selftext": "Having trouble sleeping",
                "subreddit": "sleep",
                "problem_keywords_found": ["trouble"],
                "problem_keyword_count": 1,
                "score": 10
            }
        ]

        stats = collect_commercial_data(
            subreddits=["sleep"],
            limit=10,
            test_mode=True
        )

        # Should not load if all posts filtered out
        mock_load.assert_not_called()

        assert stats["success"] is False
        assert stats["total_collected"] == 1
        assert stats["commercial_posts"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
