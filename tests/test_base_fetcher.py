"""Tests for BaseFetcher abstract interface."""
import pytest
from core.fetchers.base_fetcher import BaseFetcher


class ConcreteFetcher(BaseFetcher):
    """Concrete implementation for testing."""

    def fetch(self, limit: int, **kwargs):
        for i in range(limit):
            yield {
                "submission_id": f"test{i}",
                "title": f"Test {i}",
                "content": "Test content",
                "subreddit": "test",
            }

    def get_source_name(self) -> str:
        return "Test Source"


def test_base_fetcher_cannot_instantiate():
    """Test that BaseFetcher cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseFetcher()


def test_concrete_fetcher_works(sample_submission):
    """Test that concrete implementation works."""
    fetcher = ConcreteFetcher()

    submissions = list(fetcher.fetch(limit=5))

    assert len(submissions) == 5
    assert fetcher.get_source_name() == "Test Source"
    assert fetcher.validate_submission(submissions[0]) is True


def test_validate_submission_missing_fields():
    """Test submission validation catches missing fields."""
    fetcher = ConcreteFetcher()

    invalid_submission = {"submission_id": "test"}

    assert fetcher.validate_submission(invalid_submission) is False


def test_validate_submission_all_fields():
    """Test submission validation with all required fields."""
    fetcher = ConcreteFetcher()

    valid_submission = {
        "submission_id": "test123",
        "title": "Test title",
        "content": "Test content",
        "subreddit": "test",
    }

    assert fetcher.validate_submission(valid_submission) is True
