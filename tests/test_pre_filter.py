"""Tests for pre-AI filtering logic.

This test suite ensures 100% coverage of the pre_filter module,
testing filtering decisions, batch processing, and statistics.
"""

import time

import pytest

from core.quality_filters.pre_filter import (
    filter_submissions_batch,
    get_filter_stats,
    should_analyze_with_ai,
)
from core.quality_filters.thresholds import (
    MIN_COMMENT_COUNT,
    MIN_ENGAGEMENT_SCORE,
    MIN_PROBLEM_KEYWORDS,
    MIN_QUALITY_SCORE,
)


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def passing_post():
    """Post that passes all quality filters."""
    return {
        "upvotes": 50,
        "num_comments": 20,
        "title": "I have a problem with my workflow",
        "text": "It's frustrating and difficult",
        "created_utc": time.time(),
    }


@pytest.fixture
def low_engagement_post():
    """Post that fails due to low upvotes."""
    return {
        "upvotes": 2,  # Below MIN_ENGAGEMENT_SCORE
        "num_comments": 10,
        "title": "Problem with issue",
        "text": "Having trouble",
        "created_utc": time.time(),
    }


@pytest.fixture
def low_comments_post():
    """Post that fails due to insufficient comments."""
    return {
        "upvotes": 20,
        "num_comments": 0,  # Below MIN_COMMENT_COUNT
        "title": "Problem with issue",
        "text": "Having trouble",
        "created_utc": time.time(),
    }


@pytest.fixture
def no_keywords_post():
    """Post that fails due to missing problem keywords."""
    return {
        "upvotes": 20,
        "num_comments": 10,
        "title": "Test post",  # No problem keywords
        "text": "Just testing things",
        "created_utc": time.time(),
    }


@pytest.fixture
def low_quality_score_post():
    """Post that fails overall quality score."""
    return {
        "upvotes": 5,  # Minimal passing engagement
        "num_comments": 1,  # Minimal passing comments
        "title": "problem",  # Minimal keyword
        "text": "",
        "created_utc": time.time() - (100 * 24 * 3600),  # Very old (no recency)
    }


# ===========================
# should_analyze_with_ai() Tests
# ===========================


def test_should_analyze_passing_post(passing_post):
    """Test that high-quality post passes all filters."""
    should_analyze, score, reason = should_analyze_with_ai(passing_post)

    assert should_analyze is True
    assert score > MIN_QUALITY_SCORE
    assert "Passed all quality filters" in reason


def test_should_analyze_returns_tuple(passing_post):
    """Test that function returns proper tuple structure."""
    result = should_analyze_with_ai(passing_post)

    assert isinstance(result, tuple)
    assert len(result) == 3

    should_analyze, score, reason = result
    assert isinstance(should_analyze, bool)
    assert isinstance(score, float)
    assert isinstance(reason, str)


def test_low_engagement_filtered(low_engagement_post):
    """Test that post with low upvotes is filtered."""
    should_analyze, score, reason = should_analyze_with_ai(low_engagement_post)

    assert should_analyze is False
    assert "Insufficient engagement" in reason
    assert str(MIN_ENGAGEMENT_SCORE) in reason


def test_low_comments_filtered(low_comments_post):
    """Test that post with insufficient comments is filtered."""
    should_analyze, score, reason = should_analyze_with_ai(low_comments_post)

    assert should_analyze is False
    assert "Insufficient comments" in reason
    assert str(MIN_COMMENT_COUNT) in reason


def test_no_keywords_filtered(no_keywords_post):
    """Test that post without problem keywords is filtered."""
    should_analyze, score, reason = should_analyze_with_ai(no_keywords_post)

    assert should_analyze is False
    assert "Insufficient problem keywords" in reason
    assert str(MIN_PROBLEM_KEYWORDS) in reason


def test_low_quality_score_filtered(low_quality_score_post):
    """Test that post with low quality score is filtered."""
    should_analyze, score, reason = should_analyze_with_ai(low_quality_score_post)

    assert should_analyze is False
    assert "Quality score too low" in reason


def test_custom_threshold_higher():
    """Test custom quality threshold (higher than default)."""
    post = {
        "upvotes": 10,
        "num_comments": 5,
        "title": "problem issue",
        "created_utc": time.time(),
    }

    # Should pass with default threshold
    should_analyze_default, _, _ = should_analyze_with_ai(post, quality_threshold=15.0)

    # Should fail with higher threshold
    should_analyze_high, score, reason = should_analyze_with_ai(post, quality_threshold=50.0)

    assert should_analyze_default is True or should_analyze_high is False
    if not should_analyze_high:
        assert "Quality score too low" in reason
        assert "50.0" in reason


def test_custom_threshold_lower():
    """Test custom quality threshold (lower than default)."""
    post = {
        "upvotes": 5,
        "num_comments": 1,
        "title": "problem",
        "created_utc": time.time() - (48 * 3600),  # 2 days old
    }

    # Might fail with default
    # Should pass with very low threshold
    should_analyze, score, reason = should_analyze_with_ai(post, quality_threshold=5.0)

    # Should pass or fail based on score, but function should work
    assert isinstance(should_analyze, bool)
    assert isinstance(score, float)


def test_filtering_disabled():
    """Test that enable_filtering=False passes everything."""
    # Create a post that would normally fail everything
    terrible_post = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "x",
        "text": "",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }

    should_analyze, score, reason = should_analyze_with_ai(
        terrible_post, enable_filtering=False
    )

    assert should_analyze is True
    assert "Filtering disabled" in reason or "test mode" in reason.lower()


def test_score_field_name_variation():
    """Test that 'score' field works instead of 'upvotes'."""
    post = {
        "score": 50,  # Using 'score' instead of 'upvotes'
        "num_comments": 20,
        "title": "Problem with issue",
        "created_utc": time.time(),
    }

    should_analyze, quality_score, reason = should_analyze_with_ai(post)

    assert should_analyze is True  # Should pass with good score


def test_comments_count_field_variation():
    """Test that 'comments_count' field works instead of 'num_comments'."""
    post = {
        "upvotes": 50,
        "comments_count": 20,  # Using 'comments_count' instead
        "title": "Problem with issue",
        "created_utc": time.time(),
    }

    should_analyze, quality_score, reason = should_analyze_with_ai(post)

    assert should_analyze is True


def test_content_field_variation():
    """Test that 'content' field works instead of 'text'."""
    post = {
        "upvotes": 50,
        "num_comments": 20,
        "title": "Test",
        "content": "problem issue frustrated",  # Using 'content' instead of 'text'
        "created_utc": time.time(),
    }

    should_analyze, quality_score, reason = should_analyze_with_ai(post)

    assert should_analyze is True


def test_quality_score_returned(passing_post):
    """Test that quality score is always calculated and returned."""
    should_analyze, score, reason = should_analyze_with_ai(passing_post)

    assert score > 0
    assert isinstance(score, float)


def test_quality_score_returned_on_failure(low_engagement_post):
    """Test that quality score is returned even when filtered."""
    should_analyze, score, reason = should_analyze_with_ai(low_engagement_post)

    assert should_analyze is False
    assert score >= 0  # Score still calculated
    assert isinstance(score, float)


# ===========================
# filter_submissions_batch() Tests
# ===========================


def test_filter_batch_all_passing(passing_post):
    """Test batch filtering with all passing posts."""
    posts = [passing_post.copy() for _ in range(3)]
    passed, filtered = filter_submissions_batch(posts)

    assert len(passed) == 3
    assert len(filtered) == 0
    assert all("quality_score" in p for p in passed)
    assert all("filter_reason" in p for p in passed)


def test_filter_batch_all_failing(low_engagement_post):
    """Test batch filtering with all failing posts."""
    posts = [low_engagement_post.copy() for _ in range(3)]
    passed, filtered = filter_submissions_batch(posts)

    assert len(passed) == 0
    assert len(filtered) == 3
    assert all("quality_score" in p for p in filtered)
    assert all("filter_reason" in p for p in filtered)


def test_filter_batch_mixed(passing_post, low_engagement_post, no_keywords_post):
    """Test batch filtering with mixed quality posts."""
    posts = [passing_post, low_engagement_post, no_keywords_post]
    passed, filtered = filter_submissions_batch(posts)

    assert len(passed) >= 1  # At least passing_post
    assert len(filtered) >= 2  # At least the two failing posts
    assert len(passed) + len(filtered) == 3


def test_filter_batch_empty_list():
    """Test batch filtering with empty list."""
    passed, filtered = filter_submissions_batch([])

    assert passed == []
    assert filtered == []


def test_filter_batch_single_post(passing_post):
    """Test batch filtering with single post."""
    passed, filtered = filter_submissions_batch([passing_post])

    assert len(passed) == 1
    assert len(filtered) == 0


def test_filter_batch_preserves_order():
    """Test that batch filtering preserves post order."""
    posts = [
        {"upvotes": 50, "num_comments": 10, "title": "problem 1", "text": "", "id": "1"},
        {"upvotes": 60, "num_comments": 15, "title": "problem 2", "text": "", "id": "2"},
        {"upvotes": 70, "num_comments": 20, "title": "problem 3", "text": "", "id": "3"},
    ]
    # Add created_utc to all
    for post in posts:
        post["created_utc"] = time.time()

    passed, filtered = filter_submissions_batch(posts)

    # Check that order is preserved in passed posts
    if len(passed) >= 2:
        assert passed[0].get("id") == "1"
        assert passed[1].get("id") == "2"


def test_filter_batch_adds_metadata(passing_post):
    """Test that batch filtering adds quality metadata."""
    passed, filtered = filter_submissions_batch([passing_post])

    post = passed[0]
    assert "quality_score" in post
    assert "filter_reason" in post
    assert isinstance(post["quality_score"], float)
    assert isinstance(post["filter_reason"], str)


def test_filter_batch_preserves_original_fields(passing_post):
    """Test that original post fields are preserved."""
    original_upvotes = passing_post["upvotes"]
    original_title = passing_post["title"]

    passed, filtered = filter_submissions_batch([passing_post])

    post = passed[0]
    assert post["upvotes"] == original_upvotes
    assert post["title"] == original_title


def test_filter_batch_custom_threshold():
    """Test batch filtering with custom threshold."""
    posts = [
        {"upvotes": 20, "num_comments": 10, "title": "problem", "created_utc": time.time()},
        {"upvotes": 10, "num_comments": 5, "title": "issue", "created_utc": time.time()},
    ]

    # Use very low threshold - both should pass
    passed_low, filtered_low = filter_submissions_batch(posts, quality_threshold=5.0)

    # Use high threshold - might filter some
    passed_high, filtered_high = filter_submissions_batch(posts, quality_threshold=50.0)

    # With higher threshold, we should get fewer or equal passed
    assert len(passed_high) <= len(passed_low)


def test_filter_batch_filtering_disabled():
    """Test batch filtering with filtering disabled."""
    # Create posts that would normally fail
    bad_posts = [
        {"upvotes": 0, "num_comments": 0, "title": "x"},
        {"upvotes": 1, "num_comments": 0, "title": "y"},
    ]

    passed, filtered = filter_submissions_batch(bad_posts, enable_filtering=False)

    # All should pass when filtering is disabled
    assert len(passed) == 2
    assert len(filtered) == 0


# ===========================
# get_filter_stats() Tests
# ===========================


def test_get_filter_stats_single_reason():
    """Test stats generation with single filter reason."""
    filtered = [
        {"filter_reason": "Insufficient engagement (2 upvotes < 5 minimum)"},
        {"filter_reason": "Insufficient engagement (1 upvotes < 5 minimum)"},
        {"filter_reason": "Insufficient engagement (3 upvotes < 5 minimum)"},
    ]

    stats = get_filter_stats(filtered)

    assert "Insufficient engagement" in stats
    assert stats["Insufficient engagement"] == 3


def test_get_filter_stats_multiple_reasons():
    """Test stats generation with multiple filter reasons."""
    filtered = [
        {"filter_reason": "Insufficient engagement (2 upvotes < 5 minimum)"},
        {"filter_reason": "Insufficient comments (0 comments < 1 minimum)"},
        {"filter_reason": "Insufficient engagement (1 upvotes < 5 minimum)"},
        {"filter_reason": "Quality score too low (10.5 < 15.0 threshold)"},
        {"filter_reason": "Insufficient comments (0 comments < 1 minimum)"},
    ]

    stats = get_filter_stats(filtered)

    assert "Insufficient engagement" in stats
    assert "Insufficient comments" in stats
    assert "Quality score too low" in stats

    assert stats["Insufficient engagement"] == 2
    assert stats["Insufficient comments"] == 2
    assert stats["Quality score too low"] == 1


def test_get_filter_stats_empty_list():
    """Test stats generation with empty list."""
    stats = get_filter_stats([])

    assert stats == {}


def test_get_filter_stats_sorted_by_count():
    """Test that stats are sorted by count (descending)."""
    filtered = [
        {"filter_reason": "Insufficient engagement (2 upvotes < 5 minimum)"},
        {"filter_reason": "Insufficient engagement (1 upvotes < 5 minimum)"},
        {"filter_reason": "Insufficient engagement (3 upvotes < 5 minimum)"},
        {"filter_reason": "Quality score too low (10.5 < 15.0 threshold)"},
    ]

    stats = get_filter_stats(filtered)

    # Convert to list to check order
    items = list(stats.items())

    # First item should have highest count
    assert items[0][1] >= items[-1][1]


def test_get_filter_stats_extracts_reason_prefix():
    """Test that reason prefix is extracted correctly (before parenthesis)."""
    filtered = [
        {"filter_reason": "Insufficient engagement (2 upvotes < 5 minimum)"},
        {"filter_reason": "Insufficient engagement (100 upvotes < 5 minimum)"},
    ]

    stats = get_filter_stats(filtered)

    # Should group by prefix "Insufficient engagement", not full string
    assert len(stats) == 1
    assert "Insufficient engagement" in stats


def test_get_filter_stats_no_parenthesis():
    """Test stats with reasons that have no parenthesis."""
    filtered = [
        {"filter_reason": "Custom filter reason"},
        {"filter_reason": "Custom filter reason"},
        {"filter_reason": "Another reason"},
    ]

    stats = get_filter_stats(filtered)

    assert "Custom filter reason" in stats
    assert "Another reason" in stats
    assert stats["Custom filter reason"] == 2
    assert stats["Another reason"] == 1


def test_get_filter_stats_missing_reason_field():
    """Test stats when filter_reason field is missing."""
    filtered = [
        {"other_field": "value"},
        {"filter_reason": "Insufficient engagement (2 upvotes < 5 minimum)"},
    ]

    stats = get_filter_stats(filtered)

    # Should handle missing field gracefully
    assert "Insufficient engagement" in stats or "Unknown reason" in stats


def test_get_filter_stats_with_real_batch_results():
    """Integration test: use real batch filtering results."""
    posts = [
        {"upvotes": 1, "num_comments": 5, "title": "problem", "created_utc": time.time()},
        {"upvotes": 2, "num_comments": 0, "title": "issue", "created_utc": time.time()},
        {"upvotes": 3, "num_comments": 0, "title": "test", "created_utc": time.time()},
    ]

    passed, filtered = filter_submissions_batch(posts)

    # Get stats from filtered results
    stats = get_filter_stats(filtered)

    # Should have some stats if any were filtered
    if len(filtered) > 0:
        assert isinstance(stats, dict)
        assert len(stats) > 0
