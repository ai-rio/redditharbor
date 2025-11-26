"""
Pytest configuration and shared fixtures for pipeline-v2 tests.

This module provides common test fixtures and configuration for all test suites.
"""

import sys
import time
from pathlib import Path
from typing import Any

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add pipeline-v2 to path
pipeline_v2_path = Path(__file__).parent.parent
sys.path.insert(0, str(pipeline_v2_path))


# ============================================================================
# SHARED FIXTURES
# ============================================================================


@pytest.fixture
def sample_post():
    """Basic sample post for simple tests"""
    return {
        "upvotes": 25,
        "num_comments": 10,
        "title": "Problem with expensive tool",
        "text": "Frustrated with current solution. Looking for better alternative.",
        "created_utc": time.time(),
    }


@pytest.fixture
def high_quality_posts():
    """Generate high-quality posts that should PASS filters"""

    def _generate(count: int = 10) -> list[dict[str, Any]]:
        current_time = time.time()
        return [
            {
                "upvotes": 30 + (i * 5),
                "num_comments": 15 + i,
                "title": f"Struggling with expensive inefficient tool #{i}",
                "text": "Frustrated with current solution. The problem is it's time consuming "
                "and manual. I've tried workarounds but they're complicated.",
                "created_utc": current_time - (i * 1800),
            }
            for i in range(count)
        ]

    return _generate


@pytest.fixture
def low_quality_posts():
    """Generate low-quality posts that should FAIL filters"""

    def _generate(count: int = 10) -> list[dict[str, Any]]:
        current_time = time.time()
        return [
            {
                "upvotes": i % 3,
                "num_comments": 0,
                "title": f"help {i}",
                "text": "random text",
                "created_utc": current_time - (i * 900),
            }
            for i in range(count)
        ]

    return _generate


@pytest.fixture
def mixed_quality_posts():
    """Generate mixed quality posts for realistic testing"""

    def _generate(count: int = 100) -> list[dict[str, Any]]:
        current_time = time.time()
        posts = []

        # 20% high quality
        for i in range(int(count * 0.20)):
            posts.append({
                "upvotes": 30 + (i * 3),
                "num_comments": 12 + i,
                "title": f"Problem with expensive tool #{i}",
                "text": "Frustrated with current solution, manual workaround is tedious",
                "created_utc": current_time - (i * 3600),
            })

        # 30% medium quality
        for i in range(int(count * 0.30)):
            posts.append({
                "upvotes": 6 + (i % 10),
                "num_comments": 1 + (i % 4),
                "title": f"Issue with workflow #{i}",
                "text": "Problem with current approach",
                "created_utc": current_time - (i * 5400),
            })

        # 50% low quality
        remaining = count - len(posts)
        for i in range(remaining):
            posts.append({
                "upvotes": i % 4,
                "num_comments": i % 2,
                "title": f"question {i}",
                "text": "looking for help",
                "created_utc": current_time - (i * 1800),
            })

        return posts

    return _generate


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "baseline: marks tests for old system baseline"
    )
    config.addinivalue_line(
        "markers", "migration: marks tests for migration validation"
    )
    config.addinivalue_line(
        "markers", "cost_savings: marks tests for cost savings validation"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their module"""
    for item in items:
        # Mark baseline tests
        if "test_old_system_baseline" in item.nodeid:
            item.add_marker(pytest.mark.baseline)

        # Mark migration tests
        if "test_quality_filter_migration" in item.nodeid:
            item.add_marker(pytest.mark.migration)

        # Mark cost savings tests
        if "test_cost_savings_validation" in item.nodeid:
            item.add_marker(pytest.mark.cost_savings)

        # Mark slow tests (>1000 posts)
        if "10k" in item.name.lower() or "large" in item.name.lower():
            item.add_marker(pytest.mark.slow)


# ============================================================================
# TEST HELPERS
# ============================================================================


class TestDataGenerator:
    """Helper class for generating test data"""

    @staticmethod
    def create_post(
        upvotes: int = 10,
        comments: int = 5,
        title: str = "Problem with tool",
        text: str = "Frustrated",
        age_hours: float = 0,
    ) -> dict[str, Any]:
        """Create a single test post with specified attributes"""
        return {
            "upvotes": upvotes,
            "num_comments": comments,
            "title": title,
            "text": text,
            "created_utc": time.time() - (age_hours * 3600),
        }

    @staticmethod
    def create_posts_with_scores(
        score_ranges: list[tuple[int, int]], count_per_range: int = 10
    ) -> list[dict[str, Any]]:
        """Create posts with specific upvote score ranges"""
        posts = []
        for min_score, max_score in score_ranges:
            for i in range(count_per_range):
                score = min_score + (i % (max_score - min_score + 1))
                posts.append(
                    TestDataGenerator.create_post(
                        upvotes=score,
                        comments=max(1, score // 5),
                        title=f"Problem {i}",
                        text="Frustrated with expensive tool",
                    )
                )
        return posts


@pytest.fixture
def test_data_generator():
    """Provide TestDataGenerator instance"""
    return TestDataGenerator()


# ============================================================================
# ASSERTION HELPERS
# ============================================================================


def assert_score_in_range(score: float, min_val: float = 0, max_val: float = 100):
    """Assert quality score is in valid range"""
    assert isinstance(score, float), f"Score should be float, got {type(score)}"
    assert min_val <= score <= max_val, (
        f"Score {score} outside range [{min_val}, {max_val}]"
    )


def assert_filter_rate_in_range(
    passed: int, filtered: int, min_rate: float = 0.55, max_rate: float = 0.65
):
    """Assert filter rate is in target range"""
    total = passed + filtered
    filter_rate = filtered / total if total > 0 else 0

    assert min_rate <= filter_rate <= max_rate, (
        f"Filter rate {filter_rate:.1%} outside target range "
        f"{min_rate:.0%}-{max_rate:.0%}\n"
        f"Passed: {passed}, Filtered: {filtered}"
    )


# ============================================================================
# FIXTURES FOR SPECIFIC TEST SCENARIOS
# ============================================================================


@pytest.fixture
def edge_case_posts():
    """Posts at exact threshold boundaries"""
    current_time = time.time()

    from filters.thresholds import (
        MIN_COMMENT_COUNT,
        MIN_ENGAGEMENT_SCORE,
    )

    return [
        # Exactly at minimum
        {
            "upvotes": MIN_ENGAGEMENT_SCORE,
            "num_comments": MIN_COMMENT_COUNT,
            "title": "Problem",
            "text": "",
            "created_utc": current_time,
        },
        # Just below minimum
        {
            "upvotes": MIN_ENGAGEMENT_SCORE - 1,
            "num_comments": MIN_COMMENT_COUNT,
            "title": "Problem",
            "text": "",
            "created_utc": current_time,
        },
        # Just above minimum
        {
            "upvotes": MIN_ENGAGEMENT_SCORE + 1,
            "num_comments": MIN_COMMENT_COUNT + 1,
            "title": "Problem",
            "text": "Frustrated",
            "created_utc": current_time,
        },
    ]


@pytest.fixture
def field_name_variations():
    """Posts with different field name conventions"""
    current_time = time.time()

    return [
        # Standard names
        {
            "upvotes": 10,
            "num_comments": 5,
            "title": "Problem",
            "text": "Frustrated",
            "created_utc": current_time,
        },
        # Alternative: score instead of upvotes
        {
            "score": 10,
            "num_comments": 5,
            "title": "Problem",
            "text": "Frustrated",
            "created_utc": current_time,
        },
        # Alternative: comments_count instead of num_comments
        {
            "upvotes": 10,
            "comments_count": 5,
            "title": "Problem",
            "text": "Frustrated",
            "created_utc": current_time,
        },
        # Alternative: content instead of text
        {
            "upvotes": 10,
            "num_comments": 5,
            "title": "Problem",
            "content": "Frustrated",
            "created_utc": current_time,
        },
    ]


# ============================================================================
# PERFORMANCE TESTING FIXTURES
# ============================================================================


@pytest.fixture
def large_dataset():
    """Generate large dataset for performance testing"""

    def _generate(count: int = 10000) -> list[dict[str, Any]]:
        current_time = time.time()
        return [
            {
                "upvotes": 5 + (i % 50),
                "num_comments": 1 + (i % 20),
                "title": f"Problem {i % 100}",
                "text": "Frustrated with expensive tool" if i % 3 == 0 else "Random",
                "created_utc": current_time - ((i % 1000) * 3600),
            }
            for i in range(count)
        ]

    return _generate


# ============================================================================
# CLEANUP
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test (if needed)"""
    yield
    # Add cleanup code here if needed in the future
