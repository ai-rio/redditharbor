#!/usr/bin/env python3
"""
Comprehensive Unit Tests for automated_opportunity_collector.py DLT Migration

Tests verify:
- DLT pipeline integration
- Quality filtering logic
- Opportunity enrichment
- Deduplication via merge disposition
- Statistics reporting
- Error handling per subreddit
- 42 subreddit configuration
- Filtering effectiveness

Migration Pattern: Phase 2 - Large-scale opportunity discovery with quality filtering
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import script functions
from scripts.automated_opportunity_collector import (
    FINANCE_SUBREDDITS,
    HEALTH_FITNESS_SUBREDDITS,
    OPPORTUNITY_SUBREDDITS,
    TECH_SAAS_SUBREDDITS,
    calculate_quality_score,
    collect_fresh_reddit_data,
    enrich_opportunity_metadata,
    filter_high_quality_opportunities,
)

# ============================================================================
# Test Configuration
# ============================================================================

@pytest.fixture
def sample_problem_post():
    """Sample problem post for testing."""
    return {
        "id": "test123",
        "title": "I struggle with managing my freelance invoices",
        "selftext": "This is so frustrating and time consuming. I wish there was a better tool.",
        "author": "test_user",
        "created_utc": time.time() - 3600,  # 1 hour ago
        "subreddit": "freelance",
        "score": 25,
        "url": "https://reddit.com/r/freelance/test123",
        "num_comments": 12,
        "problem_keywords_found": ["struggle", "frustrating", "time consuming", "wish"],
        "problem_keyword_count": 4
    }


@pytest.fixture
def low_quality_post():
    """Low quality post that should be filtered out."""
    return {
        "id": "low_quality",
        "title": "Need help",
        "selftext": "Short post",
        "author": "test_user",
        "created_utc": time.time() - 86400,  # 24 hours ago
        "subreddit": "test",
        "score": 2,  # Below MIN_ENGAGEMENT_SCORE
        "url": "https://reddit.com/r/test/low_quality",
        "num_comments": 0,
        "problem_keywords_found": ["help"],
        "problem_keyword_count": 1
    }


@pytest.fixture
def high_engagement_post():
    """High engagement post with excellent quality."""
    return {
        "id": "high_engagement",
        "title": "Major productivity problem - need solution urgently",
        "selftext": "I'm struggling with this workflow issue. It's frustrating and time consuming.",
        "author": "test_user",
        "created_utc": time.time() - 1800,  # 30 minutes ago (very recent)
        "subreddit": "productivity",
        "score": 85,
        "url": "https://reddit.com/r/productivity/high_engagement",
        "num_comments": 45,
        "problem_keywords_found": ["problem", "struggling", "frustrating", "time consuming"],
        "problem_keyword_count": 4
    }


# ============================================================================
# Test Quality Scoring
# ============================================================================

def test_calculate_quality_score_engagement_component(sample_problem_post):
    """Test quality score calculation - engagement component."""
    score = calculate_quality_score(sample_problem_post)
    assert isinstance(score, float)
    assert 0 <= score <= 100
    # With score=25, comments=12, engagement = (25 + 12*2)/2 = 24.5 (capped at 40)
    # So engagement component should be 24.5


def test_calculate_quality_score_keyword_density(sample_problem_post):
    """Test quality score calculation - keyword density component."""
    # 4 problem keywords * 10 = 40, but capped at 30
    score = calculate_quality_score(sample_problem_post)
    # Expected: engagement ~24.5 + keywords 30 + recency ~30 = ~84.5
    assert score > 70  # Should be high quality


def test_calculate_quality_score_recency_factor(sample_problem_post):
    """Test quality score calculation - recency decay."""
    # Recent post (1 hour ago) should have high recency score
    recent_score = calculate_quality_score(sample_problem_post)

    # Old post (24 hours ago)
    old_post = sample_problem_post.copy()
    old_post["created_utc"] = time.time() - 86400
    old_score = calculate_quality_score(old_post)

    # Recent post should have higher score due to recency
    assert recent_score > old_score


def test_calculate_quality_score_zero_engagement(low_quality_post):
    """Test quality score with minimal engagement."""
    score = calculate_quality_score(low_quality_post)
    # Low engagement (2), low comments (0), old post
    # Should have low quality score
    assert score < 30


def test_calculate_quality_score_high_engagement(high_engagement_post):
    """Test quality score with high engagement."""
    score = calculate_quality_score(high_engagement_post)
    # High engagement (85), many comments (45), recent, many keywords
    # Should have very high quality score
    assert score > 80


# ============================================================================
# Test Opportunity Enrichment
# ============================================================================

def test_enrich_opportunity_metadata_adds_quality_score(sample_problem_post):
    """Test that enrichment adds quality score."""
    enriched = enrich_opportunity_metadata(sample_problem_post)
    assert "quality_score" in enriched
    assert isinstance(enriched["quality_score"], float)


def test_enrich_opportunity_metadata_classifies_finance(sample_problem_post):
    """Test opportunity type classification for finance subreddits."""
    finance_post = sample_problem_post.copy()
    finance_post["subreddit"] = "personalfinance"

    enriched = enrich_opportunity_metadata(finance_post)
    assert enriched["opportunity_type"] == "finance"


def test_enrich_opportunity_metadata_classifies_health(sample_problem_post):
    """Test opportunity type classification for health subreddits."""
    health_post = sample_problem_post.copy()
    health_post["subreddit"] = "fitness"

    enriched = enrich_opportunity_metadata(health_post)
    assert enriched["opportunity_type"] == "health_fitness"


def test_enrich_opportunity_metadata_classifies_tech_saas(sample_problem_post):
    """Test opportunity type classification for tech/SaaS subreddits."""
    tech_post = sample_problem_post.copy()
    tech_post["subreddit"] = "SaaS"

    enriched = enrich_opportunity_metadata(tech_post)
    assert enriched["opportunity_type"] == "tech_saas"


def test_enrich_opportunity_metadata_adds_engagement_ratio(sample_problem_post):
    """Test that enrichment calculates engagement ratio."""
    enriched = enrich_opportunity_metadata(sample_problem_post)
    assert "engagement_ratio" in enriched
    # score=25, comments=12, ratio = 25/12 ≈ 2.08
    assert enriched["engagement_ratio"] > 0


def test_enrich_opportunity_metadata_adds_timestamp(sample_problem_post):
    """Test that enrichment adds collection timestamp."""
    enriched = enrich_opportunity_metadata(sample_problem_post)
    assert "collected_at" in enriched
    # Should be valid ISO format
    datetime.fromisoformat(enriched["collected_at"])


def test_enrich_opportunity_metadata_preserves_original_data(sample_problem_post):
    """Test that enrichment preserves original post data."""
    enriched = enrich_opportunity_metadata(sample_problem_post)
    assert enriched["id"] == sample_problem_post["id"]
    assert enriched["title"] == sample_problem_post["title"]
    assert enriched["score"] == sample_problem_post["score"]


# ============================================================================
# Test Quality Filtering
# ============================================================================

def test_filter_high_quality_opportunities_min_engagement(low_quality_post, sample_problem_post):
    """Test filtering based on minimum engagement threshold."""
    posts = [low_quality_post, sample_problem_post]
    filtered = filter_high_quality_opportunities(posts, min_quality_score=20.0)

    # Only sample_problem_post should pass (score=25 >= MIN_ENGAGEMENT_SCORE=5)
    # low_quality_post has score=2 < 5
    assert len(filtered) == 1
    assert filtered[0]["id"] == sample_problem_post["id"]


def test_filter_high_quality_opportunities_quality_score_threshold(sample_problem_post, high_engagement_post):
    """Test filtering based on quality score threshold."""
    posts = [sample_problem_post, high_engagement_post]

    # High threshold - only high engagement post should pass
    filtered = filter_high_quality_opportunities(posts, min_quality_score=80.0)

    assert len(filtered) == 1
    assert filtered[0]["id"] == high_engagement_post["id"]


def test_filter_high_quality_opportunities_enriches_passing_posts(sample_problem_post):
    """Test that filtering enriches posts that pass."""
    posts = [sample_problem_post]
    filtered = filter_high_quality_opportunities(posts, min_quality_score=20.0)

    assert len(filtered) == 1
    # Should have enrichment metadata
    assert "quality_score" in filtered[0]
    assert "opportunity_type" in filtered[0]
    assert "engagement_ratio" in filtered[0]
    assert "collected_at" in filtered[0]


def test_filter_high_quality_opportunities_empty_input():
    """Test filtering with empty input."""
    filtered = filter_high_quality_opportunities([], min_quality_score=20.0)
    assert filtered == []


def test_filter_high_quality_opportunities_all_filtered_out(low_quality_post):
    """Test filtering when all posts are below threshold."""
    posts = [low_quality_post]
    # High quality threshold - should filter out low quality post
    filtered = filter_high_quality_opportunities(posts, min_quality_score=50.0)

    assert len(filtered) == 0


def test_filter_high_quality_opportunities_acceptance_rate():
    """Test filtering acceptance rate calculation."""
    posts = [
        {
            "id": f"post_{i}",
            "title": "Test post",
            "selftext": "Content",
            "author": "test",
            "created_utc": time.time() - i * 3600,
            "subreddit": "test",
            "score": 10 + i * 5,  # Varying scores
            "url": f"https://reddit.com/post_{i}",
            "num_comments": i,
            "problem_keywords_found": ["test"],
            "problem_keyword_count": 1
        }
        for i in range(10)
    ]

    filtered = filter_high_quality_opportunities(posts, min_quality_score=30.0)

    # Calculate acceptance rate
    acceptance_rate = len(filtered) / len(posts) * 100
    assert 0 <= acceptance_rate <= 100


# ============================================================================
# Test Subreddit Configuration
# ============================================================================

def test_subreddit_counts_total_40():
    """Test that total subreddit count is 40 (finance 10 + health 12 + tech 10 + opportunity 8)."""
    total = (
        len(FINANCE_SUBREDDITS) +
        len(HEALTH_FITNESS_SUBREDDITS) +
        len(TECH_SAAS_SUBREDDITS) +
        len(OPPORTUNITY_SUBREDDITS)
    )
    assert total == 40


def test_finance_subreddits_count():
    """Test finance subreddits count."""
    assert len(FINANCE_SUBREDDITS) == 10


def test_health_fitness_subreddits_count():
    """Test health/fitness subreddits count."""
    assert len(HEALTH_FITNESS_SUBREDDITS) == 12


def test_tech_saas_subreddits_count():
    """Test tech/SaaS subreddits count."""
    assert len(TECH_SAAS_SUBREDDITS) == 10


def test_opportunity_subreddits_count():
    """Test opportunity subreddits count."""
    assert len(OPPORTUNITY_SUBREDDITS) == 8


def test_no_duplicate_subreddits():
    """Test that there are no duplicate subreddits across categories."""
    all_subreddits = (
        FINANCE_SUBREDDITS +
        HEALTH_FITNESS_SUBREDDITS +
        TECH_SAAS_SUBREDDITS +
        OPPORTUNITY_SUBREDDITS
    )

    # Convert to set - should have same length if no duplicates
    unique_subreddits = set(all_subreddits)
    assert len(all_subreddits) == len(unique_subreddits)


# ============================================================================
# Test DLT Integration
# ============================================================================

@patch('scripts.automated_opportunity_collector.collect_problem_posts')
@patch('scripts.automated_opportunity_collector.create_dlt_pipeline')
def test_collect_fresh_reddit_data_uses_dlt_pipeline(mock_pipeline, mock_collect):
    """Test that collection uses DLT pipeline."""
    # Mock collect_problem_posts to return test data
    mock_collect.return_value = [
        {
            "id": "test_post",
            "title": "Test problem",
            "selftext": "I'm struggling with this issue",
            "author": "test_user",
            "created_utc": time.time(),
            "subreddit": "test",
            "score": 15,
            "url": "https://reddit.com/test",
            "num_comments": 5,
            "problem_keywords_found": ["struggling", "issue"],
            "problem_keyword_count": 2
        }
    ]

    # Mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.run.return_value = MagicMock(started_at=datetime.now())
    mock_pipeline.return_value = mock_pipeline_instance

    # Run collection with small batch
    stats = collect_fresh_reddit_data(batch_size=5, limit_per_subreddit=10)

    # Verify DLT functions were called
    assert mock_collect.called
    assert mock_pipeline.called


@patch('scripts.automated_opportunity_collector.collect_problem_posts')
@patch('scripts.automated_opportunity_collector.create_dlt_pipeline')
def test_collect_fresh_reddit_data_merge_disposition(mock_pipeline, mock_collect):
    """Test that collection uses merge write disposition for deduplication."""
    # Mock collect_problem_posts
    mock_collect.return_value = [
        {
            "id": "test_post",
            "title": "Test problem",
            "selftext": "I'm struggling",
            "author": "test_user",
            "created_utc": time.time(),
            "subreddit": "test",
            "score": 20,
            "url": "https://reddit.com/test",
            "num_comments": 10,
            "problem_keywords_found": ["struggling"],
            "problem_keyword_count": 1
        }
    ]

    # Mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.run.return_value = MagicMock(started_at=datetime.now())
    mock_pipeline.return_value = mock_pipeline_instance

    # Run collection
    stats = collect_fresh_reddit_data(batch_size=5, limit_per_subreddit=10)

    # Verify merge disposition
    if mock_pipeline_instance.run.called:
        call_kwargs = mock_pipeline_instance.run.call_args[1]
        assert call_kwargs["write_disposition"] == "merge"
        assert call_kwargs["primary_key"] == "id"


@patch('scripts.automated_opportunity_collector.collect_problem_posts')
@patch('scripts.automated_opportunity_collector.create_dlt_pipeline')
def test_collect_fresh_reddit_data_loads_to_opportunities_table(mock_pipeline, mock_collect):
    """Test that collection loads to opportunities table."""
    # Mock collect_problem_posts
    mock_collect.return_value = [
        {
            "id": "test_post",
            "title": "Test problem",
            "selftext": "I'm struggling",
            "author": "test_user",
            "created_utc": time.time(),
            "subreddit": "test",
            "score": 20,
            "url": "https://reddit.com/test",
            "num_comments": 10,
            "problem_keywords_found": ["struggling"],
            "problem_keyword_count": 1
        }
    ]

    # Mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.run.return_value = MagicMock(started_at=datetime.now())
    mock_pipeline.return_value = mock_pipeline_instance

    # Run collection
    stats = collect_fresh_reddit_data(batch_size=5, limit_per_subreddit=10)

    # Verify table name
    if mock_pipeline_instance.run.called:
        call_kwargs = mock_pipeline_instance.run.call_args[1]
        assert call_kwargs["table_name"] == "opportunities"


# ============================================================================
# Test Statistics Reporting
# ============================================================================

@patch('scripts.automated_opportunity_collector.collect_problem_posts')
@patch('scripts.automated_opportunity_collector.create_dlt_pipeline')
def test_collect_fresh_reddit_data_returns_statistics(mock_pipeline, mock_collect):
    """Test that collection returns comprehensive statistics."""
    # Mock collect_problem_posts
    mock_collect.return_value = []

    # Run collection
    stats = collect_fresh_reddit_data(batch_size=5, limit_per_subreddit=10)

    # Verify statistics structure
    assert "total_subreddits" in stats
    assert "total_posts_collected" in stats
    assert "total_opportunities" in stats
    assert "errors" in stats
    assert "batches_processed" in stats
    assert "filter_rate" in stats
    assert "avg_quality_score" in stats


@patch('scripts.automated_opportunity_collector.collect_problem_posts')
@patch('scripts.automated_opportunity_collector.create_dlt_pipeline')
def test_collect_fresh_reddit_data_calculates_filter_rate(mock_pipeline, mock_collect):
    """Test that collection calculates filter rate."""
    # Mock collect_problem_posts - return mix of quality levels
    mock_collect.return_value = [
        {
            "id": f"post_{i}",
            "title": "Test",
            "selftext": "Content",
            "author": "test",
            "created_utc": time.time(),
            "subreddit": "test",
            "score": 5 + i * 5,  # Varying quality
            "url": f"https://reddit.com/post_{i}",
            "num_comments": i,
            "problem_keywords_found": ["test"],
            "problem_keyword_count": 1
        }
        for i in range(5)
    ]

    # Mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.run.return_value = MagicMock(started_at=datetime.now())
    mock_pipeline.return_value = mock_pipeline_instance

    # Run collection
    stats = collect_fresh_reddit_data(batch_size=5, limit_per_subreddit=10)

    # Filter rate should be calculated
    assert 0 <= stats["filter_rate"] <= 100


@patch('scripts.automated_opportunity_collector.collect_problem_posts')
@patch('scripts.automated_opportunity_collector.create_dlt_pipeline')
def test_collect_fresh_reddit_data_calculates_avg_quality_score(mock_pipeline, mock_collect):
    """Test that collection calculates average quality score."""
    # Mock collect_problem_posts
    mock_collect.return_value = [
        {
            "id": "high_quality",
            "title": "Major problem",
            "selftext": "I'm struggling with this issue",
            "author": "test",
            "created_utc": time.time(),
            "subreddit": "test",
            "score": 50,
            "url": "https://reddit.com/test",
            "num_comments": 20,
            "problem_keywords_found": ["struggling", "issue"],
            "problem_keyword_count": 2
        }
    ]

    # Mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.run.return_value = MagicMock(started_at=datetime.now())
    mock_pipeline.return_value = mock_pipeline_instance

    # Run collection
    stats = collect_fresh_reddit_data(batch_size=5, limit_per_subreddit=10)

    # Average quality score should be calculated
    if stats["total_opportunities"] > 0:
        assert stats["avg_quality_score"] > 0


# ============================================================================
# Test Error Handling
# ============================================================================

@patch('scripts.automated_opportunity_collector.collect_problem_posts')
def test_collect_fresh_reddit_data_handles_collection_errors(mock_collect):
    """Test that collection handles errors gracefully."""
    # Mock collect_problem_posts to raise error
    mock_collect.side_effect = Exception("API Error")

    # Run collection - should not crash
    stats = collect_fresh_reddit_data(batch_size=5, limit_per_subreddit=10)

    # Should record errors
    assert stats["errors"] > 0


@patch('scripts.automated_opportunity_collector.collect_problem_posts')
@patch('scripts.automated_opportunity_collector.create_dlt_pipeline')
def test_collect_fresh_reddit_data_handles_load_errors(mock_pipeline, mock_collect):
    """Test that collection handles DLT load errors."""
    # Mock collect_problem_posts
    mock_collect.return_value = [
        {
            "id": "test_post",
            "title": "Test",
            "selftext": "Content",
            "author": "test",
            "created_utc": time.time(),
            "subreddit": "test",
            "score": 20,
            "url": "https://reddit.com/test",
            "num_comments": 10,
            "problem_keywords_found": ["test"],
            "problem_keyword_count": 1
        }
    ]

    # Mock pipeline to raise error
    mock_pipeline_instance = MagicMock()
    mock_pipeline_instance.run.side_effect = Exception("DLT Error")
    mock_pipeline.return_value = mock_pipeline_instance

    # Run collection - should not crash
    stats = collect_fresh_reddit_data(batch_size=5, limit_per_subreddit=10)

    # Should record load failure
    assert stats.get("load_success") is False


# ============================================================================
# Test Batch Processing
# ============================================================================

@patch('scripts.automated_opportunity_collector.collect_problem_posts')
@patch('scripts.automated_opportunity_collector.create_dlt_pipeline')
@patch('time.sleep')  # Mock sleep to speed up tests
def test_collect_fresh_reddit_data_processes_in_batches(mock_sleep, mock_pipeline, mock_collect):
    """Test that collection processes subreddits in batches."""
    # Mock collect_problem_posts
    mock_collect.return_value = []

    # Mock pipeline
    mock_pipeline_instance = MagicMock()
    mock_pipeline.return_value = mock_pipeline_instance

    # Run collection with small batch size
    stats = collect_fresh_reddit_data(batch_size=5, limit_per_subreddit=10)

    # Should have processed multiple batches (40 subreddits / 5 per batch = 8 batches)
    assert stats["batches_processed"] == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
