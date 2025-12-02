"""Tests for quality scoring utilities.

This test suite ensures 100% coverage of the quality_scorer module,
testing scoring logic with various post types and edge cases.
"""

import time
from datetime import datetime, timedelta

import pytest

from core.quality_filters.quality_scorer import (
    calculate_pre_ai_quality_score,
    get_quality_breakdown,
)


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def high_quality_post():
    """High-quality post with good engagement and problem keywords."""
    return {
        "upvotes": 50,
        "num_comments": 25,
        "title": "I have a problem with my workflow",
        "text": "It's frustrating and difficult to manage",
        "created_utc": time.time(),  # Just created
    }


@pytest.fixture
def medium_quality_post():
    """Medium-quality post with moderate engagement."""
    return {
        "upvotes": 10,
        "num_comments": 5,
        "title": "Question about an issue",
        "text": "Having trouble with this",
        "created_utc": time.time() - (12 * 3600),  # 12 hours old
    }


@pytest.fixture
def low_quality_post():
    """Low-quality post with minimal engagement."""
    return {
        "upvotes": 2,
        "num_comments": 0,
        "title": "Test post",
        "text": "Just testing",
        "created_utc": time.time() - (1000 * 24 * 3600),  # Very old (>30 days)
    }


@pytest.fixture
def minimal_post():
    """Minimal post with only required fields."""
    return {
        "title": "Minimal",
    }


# ===========================
# calculate_pre_ai_quality_score() Tests
# ===========================


def test_calculate_score_high_quality(high_quality_post):
    """Test scoring of high-quality post."""
    score = calculate_pre_ai_quality_score(high_quality_post)

    # High engagement (50 upvotes + 25 comments)
    # Should hit max 40 points for engagement
    # Multiple problem keywords should give good keyword score
    # Recent post should give good recency score
    assert score >= 60.0, f"Expected high score, got {score}"
    assert isinstance(score, float)
    assert score <= 100.0


def test_calculate_score_medium_quality(medium_quality_post):
    """Test scoring of medium-quality post."""
    score = calculate_pre_ai_quality_score(medium_quality_post)

    # Moderate engagement
    # Some problem keywords
    # 12 hours old (partial recency)
    assert 20.0 <= score <= 60.0, f"Expected medium score, got {score}"
    assert isinstance(score, float)


def test_calculate_score_low_quality(low_quality_post):
    """Test scoring of low-quality post."""
    score = calculate_pre_ai_quality_score(low_quality_post)

    # Low engagement
    # No problem keywords
    # Old post (no recency score)
    assert score < 20.0, f"Expected low score, got {score}"
    assert isinstance(score, float)


def test_calculate_score_minimal_post(minimal_post):
    """Test scoring of minimal post with defaults."""
    score = calculate_pre_ai_quality_score(minimal_post)

    # All defaults except created_utc which defaults to now
    # Should get some recency score but nothing else
    assert 0.0 <= score <= 40.0
    assert isinstance(score, float)


def test_engagement_calculation():
    """Test engagement score calculation."""
    post = {
        "upvotes": 20,
        "num_comments": 10,
        "title": "Test",
        "created_utc": time.time() - (1000 * 24 * 3600),  # Very old (>30 days) (no recency)
    }
    score = calculate_pre_ai_quality_score(post)

    # Expected: (20 + 10*2) / 2 = 20 points
    # No keyword points, no recency points
    assert score == 20.0


def test_engagement_max_cap():
    """Test that engagement score is capped at 40 points."""
    post = {
        "upvotes": 1000,
        "num_comments": 1000,
        "title": "Test",
        "created_utc": time.time() - (1000 * 24 * 3600),  # Very old (>30 days)
    }
    score = calculate_pre_ai_quality_score(post)

    # Should be capped at 40 points for engagement
    assert score == 40.0


def test_keyword_scoring_single():
    """Test keyword scoring with single problem keyword."""
    post = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "I have a problem",  # Contains 'problem'
        "text": "",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }
    score = calculate_pre_ai_quality_score(post)

    # 1 keyword * 10 points = 10 points
    assert score == 10.0


def test_keyword_scoring_multiple():
    """Test keyword scoring with multiple problem keywords."""
    post = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "Problem with frustrating issue",  # 3 keywords
        "text": "It's difficult and annoying",  # 2 more keywords
        "created_utc": time.time() - (1000 * 24 * 3600),
    }
    score = calculate_pre_ai_quality_score(post)

    # Should detect multiple problem keywords
    assert score >= 20.0  # At least 2 keywords found


def test_keyword_scoring_max_cap():
    """Test that keyword score is capped at 30 points."""
    # Create text with many problem keywords
    problem_text = "problem issue error bug fails broken difficult frustrating annoying"
    post = {
        "upvotes": 0,
        "num_comments": 0,
        "title": problem_text,
        "text": problem_text * 10,  # Lots of keywords
        "created_utc": time.time() - (1000 * 24 * 3600),
    }
    score = calculate_pre_ai_quality_score(post)

    # Should be capped at 30 points for keywords
    assert score == 30.0


def test_keyword_case_insensitive():
    """Test that keyword matching is case-insensitive."""
    post1 = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "PROBLEM with ISSUE",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }
    post2 = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "problem with issue",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }

    score1 = calculate_pre_ai_quality_score(post1)
    score2 = calculate_pre_ai_quality_score(post2)

    assert score1 == score2


def test_recency_score_new_post():
    """Test recency scoring for very new post."""
    post = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "Test",
        "created_utc": time.time(),  # Just now
    }
    score = calculate_pre_ai_quality_score(post)

    # Should get close to full 30 points for recency
    assert score >= 29.0
    assert score <= 30.0


def test_recency_score_old_post():
    """Test recency scoring for very old post."""
    post = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "Test",
        "created_utc": time.time() - (100 * 24 * 3600),  # 100 days old
    }
    score = calculate_pre_ai_quality_score(post)

    # Should get 0 points for recency (decayed completely)
    assert score == 0.0


def test_recency_score_decay():
    """Test that recency score decays over time (1 point per 24 hours)."""
    # Post from 12 hours ago should lose 0.5 points
    post = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "Test",
        "created_utc": time.time() - (12 * 3600),  # 12 hours old
    }
    score = calculate_pre_ai_quality_score(post)

    # Expected: 30 - (12/24) = 30 - 0.5 = 29.5 points
    assert 28.5 <= score <= 30.0  # Allow small margin for execution time


def test_field_name_variations_score():
    """Test that different field names are handled (score vs upvotes)."""
    post1 = {
        "score": 20,
        "num_comments": 10,
        "title": "Test",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }
    post2 = {
        "upvotes": 20,
        "num_comments": 10,
        "title": "Test",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }

    score1 = calculate_pre_ai_quality_score(post1)
    score2 = calculate_pre_ai_quality_score(post2)

    assert score1 == score2


def test_field_name_variations_comments():
    """Test that different comment field names are handled."""
    post1 = {
        "upvotes": 20,
        "comments_count": 10,
        "title": "Test",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }
    post2 = {
        "upvotes": 20,
        "num_comments": 10,
        "title": "Test",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }

    score1 = calculate_pre_ai_quality_score(post1)
    score2 = calculate_pre_ai_quality_score(post2)

    assert score1 == score2


def test_field_name_variations_content():
    """Test that different content field names are handled."""
    post1 = {
        "upvotes": 0,
        "title": "Test",
        "text": "problem issue",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }
    post2 = {
        "upvotes": 0,
        "title": "Test",
        "content": "problem issue",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }

    score1 = calculate_pre_ai_quality_score(post1)
    score2 = calculate_pre_ai_quality_score(post2)

    assert score1 == score2


def test_iso_datetime_string():
    """Test handling of ISO datetime string for created_utc."""
    # Create ISO string for 12 hours ago
    dt = datetime.utcnow() - timedelta(hours=12)
    iso_string = dt.isoformat() + "Z"

    post = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "Test",
        "created_utc": iso_string,
    }
    score = calculate_pre_ai_quality_score(post)

    # Should process ISO string correctly
    # Expected recency around 29.5 points (12 hours = 0.5 point decay)
    assert 28.0 <= score <= 30.0


def test_none_values_default_to_zero():
    """Test that None values in optional fields default appropriately."""
    post = {
        "upvotes": None,
        "num_comments": None,
        "title": "Test",
        "text": None,
        "created_utc": time.time(),
    }
    score = calculate_pre_ai_quality_score(post)

    # Only recency score should contribute
    assert 25.0 <= score <= 30.0


def test_score_is_rounded():
    """Test that score is rounded to 2 decimal places."""
    post = {
        "upvotes": 7,
        "num_comments": 3,
        "title": "Test",
        "created_utc": time.time(),
    }
    score = calculate_pre_ai_quality_score(post)

    # Check that score has at most 2 decimal places
    assert len(str(score).split(".")[-1]) <= 2


# ===========================
# get_quality_breakdown() Tests
# ===========================


def test_get_breakdown_complete(high_quality_post):
    """Test quality breakdown with all components."""
    breakdown = get_quality_breakdown(high_quality_post)

    assert "engagement_score" in breakdown
    assert "keyword_score" in breakdown
    assert "recency_score" in breakdown
    assert "total_score" in breakdown
    assert "problem_keyword_count" in breakdown

    assert isinstance(breakdown["engagement_score"], float)
    assert isinstance(breakdown["keyword_score"], float)
    assert isinstance(breakdown["recency_score"], float)
    assert isinstance(breakdown["total_score"], float)
    assert isinstance(breakdown["problem_keyword_count"], int)


def test_breakdown_matches_total_score(medium_quality_post):
    """Test that breakdown total matches calculate_pre_ai_quality_score."""
    breakdown = get_quality_breakdown(medium_quality_post)
    direct_score = calculate_pre_ai_quality_score(medium_quality_post)

    assert breakdown["total_score"] == direct_score


def test_breakdown_components_sum(high_quality_post):
    """Test that breakdown components sum to total."""
    breakdown = get_quality_breakdown(high_quality_post)

    components_sum = (
        breakdown["engagement_score"]
        + breakdown["keyword_score"]
        + breakdown["recency_score"]
    )

    assert abs(components_sum - breakdown["total_score"]) < 0.01  # Allow rounding error


def test_breakdown_engagement_calculation():
    """Test engagement score calculation in breakdown."""
    post = {
        "upvotes": 10,
        "num_comments": 5,
        "title": "Test",
        "created_utc": time.time() - (1000 * 24 * 3600),
    }
    breakdown = get_quality_breakdown(post)

    # Expected: (10 + 5*2) / 2 = 10
    assert breakdown["engagement_score"] == 10.0
    assert breakdown["keyword_score"] == 0.0  # No keywords
    assert breakdown["recency_score"] == 0.0  # Very old


def test_breakdown_keyword_count():
    """Test problem keyword count in breakdown."""
    post = {
        "upvotes": 0,
        "title": "Problem with issue and error",  # 3 keywords
        "created_utc": time.time() - (1000 * 24 * 3600),
    }
    breakdown = get_quality_breakdown(post)

    assert breakdown["problem_keyword_count"] >= 3
    assert breakdown["keyword_score"] >= 20.0  # At least 2 * 10


def test_breakdown_all_zeros():
    """Test breakdown for post with all zero scores."""
    post = {
        "upvotes": 0,
        "num_comments": 0,
        "title": "Test",  # No keywords
        "created_utc": time.time() - (1000 * 24 * 3600),  # Old
    }
    breakdown = get_quality_breakdown(post)

    assert breakdown["engagement_score"] == 0.0
    assert breakdown["keyword_score"] == 0.0
    assert breakdown["recency_score"] == 0.0
    assert breakdown["total_score"] == 0.0
    assert breakdown["problem_keyword_count"] == 0


def test_breakdown_values_rounded():
    """Test that all breakdown values are rounded to 2 decimals."""
    post = {
        "upvotes": 7,
        "num_comments": 3,
        "title": "problem",
        "created_utc": time.time() - (13 * 3600),  # 13 hours
    }
    breakdown = get_quality_breakdown(post)

    for key in ["engagement_score", "keyword_score", "recency_score", "total_score"]:
        value_str = str(breakdown[key])
        if "." in value_str:
            decimals = len(value_str.split(".")[-1])
            assert decimals <= 2, f"{key} has too many decimals: {value_str}"


def test_breakdown_iso_datetime_string():
    """Test that breakdown handles ISO datetime strings."""
    dt = datetime.utcnow() - timedelta(hours=6)
    iso_string = dt.isoformat() + "Z"

    post = {
        "upvotes": 10,
        "num_comments": 5,
        "title": "problem",
        "created_utc": iso_string,
    }
    breakdown = get_quality_breakdown(post)

    # Should process ISO string and return valid breakdown
    assert isinstance(breakdown["recency_score"], float)
    assert breakdown["recency_score"] > 25.0  # 6 hours old = ~29.75 points
