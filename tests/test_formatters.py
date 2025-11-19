"""Tests for submission formatting utilities.

This test suite ensures 100% coverage of the formatters module,
testing all functions with various edge cases and data formats.
"""

import pytest
from core.fetchers.formatters import (
    extract_problem_statement,
    format_batch_submissions,
    format_submission_for_agent,
    validate_submission_completeness,
)


# ===========================
# Fixtures
# ===========================


@pytest.fixture
def complete_submission():
    """Complete submission with all fields populated."""
    return {
        "submission_id": "test123",
        "title": "I need a fitness tracking app",
        "problem_description": "Looking for an app that helps me track workouts and meals",
        "subreddit": "fitness",
        "reddit_score": 42,
        "num_comments": 15,
        "trust_score": 85.5,
        "trust_badge": "Verified",
        "sentiment_score": 0.75,
        "id": "uuid-12345",
    }


@pytest.fixture
def minimal_submission():
    """Minimal submission with only required fields."""
    return {
        "submission_id": "min123",
        "title": "Simple question",
        "subreddit": "askreddit",
    }


@pytest.fixture
def submission_with_selftext():
    """Submission using selftext instead of problem_description."""
    return {
        "submission_id": "self123",
        "title": "Question about APIs",
        "selftext": "How do I build a REST API?",
        "subreddit": "webdev",
    }


# ===========================
# format_submission_for_agent() Tests
# ===========================


def test_format_submission_complete(complete_submission):
    """Test formatting a complete submission."""
    formatted = format_submission_for_agent(complete_submission)

    assert formatted["id"] == "test123"
    assert formatted["title"] == "I need a fitness tracking app"
    assert "fitness tracking app" in formatted["text"]
    assert "track workouts" in formatted["text"]
    assert formatted["subreddit"] == "fitness"
    assert formatted["engagement"]["upvotes"] == 42
    assert formatted["engagement"]["num_comments"] == 15
    assert formatted["sentiment_score"] == 0.75
    assert formatted["db_id"] == "uuid-12345"
    assert len(formatted["comments"]) == 2
    assert "Trust Score: 85.5" in formatted["comments"]
    assert "Trust Badge: Verified" in formatted["comments"]


def test_format_submission_minimal(minimal_submission):
    """Test formatting a minimal submission."""
    formatted = format_submission_for_agent(minimal_submission)

    assert formatted["id"] == "min123"
    assert formatted["title"] == "Simple question"
    assert formatted["text"] == "Simple question"  # Only title, no problem_description
    assert formatted["subreddit"] == "askreddit"
    assert formatted["engagement"]["upvotes"] == 0
    assert formatted["engagement"]["num_comments"] == 0
    assert formatted["sentiment_score"] == 0.0
    assert formatted["comments"] == []  # No trust data


def test_format_submission_missing_id_uses_fallback(complete_submission):
    """Test that missing submission_id falls back to id field."""
    del complete_submission["submission_id"]
    formatted = format_submission_for_agent(complete_submission)

    assert formatted["id"] == "uuid-12345"


def test_format_submission_missing_all_ids():
    """Test that missing both IDs defaults to 'unknown'."""
    submission = {"title": "Test", "subreddit": "test"}
    formatted = format_submission_for_agent(submission)

    assert formatted["id"] == "unknown"


def test_format_submission_empty_strings():
    """Test handling of empty string values."""
    submission = {
        "submission_id": "empty123",
        "title": "",
        "problem_description": "",
        "subreddit": "",
    }
    formatted = format_submission_for_agent(submission)

    assert formatted["id"] == "empty123"
    assert formatted["title"] == ""
    assert formatted["text"] == ""
    assert formatted["subreddit"] == ""


def test_format_submission_none_values():
    """Test handling of None values in optional fields."""
    submission = {
        "submission_id": "none123",
        "title": "Test",
        "problem_description": None,
        "reddit_score": None,
        "num_comments": None,
        "trust_score": None,
        "trust_badge": None,
    }
    formatted = format_submission_for_agent(submission)

    assert formatted["id"] == "none123"
    assert formatted["text"] == "Test"
    assert formatted["engagement"]["upvotes"] == 0
    assert formatted["engagement"]["num_comments"] == 0
    assert formatted["comments"] == []


def test_format_submission_zero_scores():
    """Test that zero scores (not None) are preserved."""
    submission = {
        "submission_id": "zero123",
        "title": "Downvoted post",
        "reddit_score": 0,
        "num_comments": 0,
    }
    formatted = format_submission_for_agent(submission)

    assert formatted["engagement"]["upvotes"] == 0
    assert formatted["engagement"]["num_comments"] == 0


def test_format_submission_trust_score_without_badge(complete_submission):
    """Test trust score display when badge is missing."""
    del complete_submission["trust_badge"]
    formatted = format_submission_for_agent(complete_submission)

    assert len(formatted["comments"]) == 1
    assert "Trust Score: 85.5" in formatted["comments"]


def test_format_submission_trust_badge_without_score(complete_submission):
    """Test trust badge display when score is missing."""
    del complete_submission["trust_score"]
    formatted = format_submission_for_agent(complete_submission)

    assert len(formatted["comments"]) == 1
    assert "Trust Badge: Verified" in formatted["comments"]


def test_format_submission_combines_title_and_description():
    """Test that title and problem_description are properly combined."""
    submission = {
        "submission_id": "combo123",
        "title": "Need help",
        "problem_description": "With my project",
    }
    formatted = format_submission_for_agent(submission)

    assert formatted["text"] == "Need help\n\nWith my project"


def test_format_submission_title_only_when_no_description():
    """Test that text contains only title when problem_description is missing."""
    submission = {
        "submission_id": "title123",
        "title": "Just a title",
    }
    formatted = format_submission_for_agent(submission)

    assert formatted["text"] == "Just a title"


# ===========================
# format_batch_submissions() Tests
# ===========================


def test_format_batch_submissions_multiple(complete_submission, minimal_submission):
    """Test batch formatting multiple submissions."""
    submissions = [complete_submission, minimal_submission]
    formatted = format_batch_submissions(submissions)

    assert len(formatted) == 2
    assert formatted[0]["id"] == "test123"
    assert formatted[1]["id"] == "min123"
    assert all("text" in sub for sub in formatted)
    assert all("engagement" in sub for sub in formatted)


def test_format_batch_submissions_empty_list():
    """Test batch formatting with empty list."""
    formatted = format_batch_submissions([])

    assert formatted == []
    assert isinstance(formatted, list)


def test_format_batch_submissions_single_item(complete_submission):
    """Test batch formatting with single submission."""
    formatted = format_batch_submissions([complete_submission])

    assert len(formatted) == 1
    assert formatted[0]["id"] == "test123"


def test_format_batch_submissions_preserves_order():
    """Test that batch formatting preserves input order."""
    submissions = [
        {"submission_id": "1", "title": "First", "subreddit": "test"},
        {"submission_id": "2", "title": "Second", "subreddit": "test"},
        {"submission_id": "3", "title": "Third", "subreddit": "test"},
    ]
    formatted = format_batch_submissions(submissions)

    assert [s["id"] for s in formatted] == ["1", "2", "3"]


# ===========================
# extract_problem_statement() Tests
# ===========================


def test_extract_problem_statement_with_description(complete_submission):
    """Test problem extraction with problem_description."""
    problem = extract_problem_statement(complete_submission)

    assert "I need a fitness tracking app" in problem
    assert "Looking for an app" in problem


def test_extract_problem_statement_title_only():
    """Test problem extraction with only title."""
    submission = {"title": "Need a todo app"}
    problem = extract_problem_statement(submission)

    assert problem == "Need a todo app"


def test_extract_problem_statement_with_selftext(submission_with_selftext):
    """Test problem extraction using selftext field."""
    problem = extract_problem_statement(submission_with_selftext)

    assert "Question about APIs" in problem
    assert "How do I build a REST API?" in problem


def test_extract_problem_statement_with_content_field():
    """Test problem extraction using content field."""
    submission = {
        "title": "Help needed",
        "content": "I need assistance with my code",
    }
    problem = extract_problem_statement(submission)

    assert "Help needed" in problem
    assert "I need assistance" in problem


def test_extract_problem_statement_truncates_long_content():
    """Test that long content is truncated to 500 chars."""
    long_content = "x" * 1000
    submission = {
        "title": "Long post",
        "problem_description": long_content,
    }
    problem = extract_problem_statement(submission)

    # Should have title + \n\n + 500 chars + ...
    assert "Long post" in problem
    assert problem.endswith("...")
    assert len(problem) <= len("Long post") + 2 + 500 + 3  # title + \n\n + content + ...


def test_extract_problem_statement_short_content_no_ellipsis():
    """Test that short content doesn't get ellipsis."""
    submission = {
        "title": "Short post",
        "problem_description": "Brief description",
    }
    problem = extract_problem_statement(submission)

    assert not problem.endswith("...")
    assert problem == "Short post\n\nBrief description"


def test_extract_problem_statement_empty_title():
    """Test problem extraction with empty title."""
    submission = {
        "title": "",
        "problem_description": "Some content",
    }
    problem = extract_problem_statement(submission)

    assert problem == "\n\nSome content"


def test_extract_problem_statement_empty_all():
    """Test problem extraction with all empty fields."""
    submission = {}
    problem = extract_problem_statement(submission)

    assert problem == ""


def test_extract_problem_statement_whitespace_handling():
    """Test that whitespace is properly stripped."""
    submission = {
        "title": "  Title with spaces  ",
        "problem_description": "  Content with spaces  ",
    }
    problem = extract_problem_statement(submission)

    assert problem == "Title with spaces\n\nContent with spaces"


def test_extract_problem_statement_field_priority():
    """Test that problem_description takes priority over content/selftext."""
    submission = {
        "title": "Test",
        "problem_description": "First choice",
        "content": "Second choice",
        "selftext": "Third choice",
    }
    problem = extract_problem_statement(submission)

    assert "First choice" in problem
    assert "Second choice" not in problem
    assert "Third choice" not in problem


def test_extract_problem_statement_content_fallback():
    """Test that content field is used when problem_description is empty."""
    submission = {
        "title": "Test",
        "problem_description": "",
        "content": "Fallback content",
        "selftext": "Not used",
    }
    problem = extract_problem_statement(submission)

    assert "Fallback content" in problem


def test_extract_problem_statement_selftext_final_fallback():
    """Test that selftext is used as final fallback."""
    submission = {
        "title": "Test",
        "problem_description": "",
        "content": "",
        "selftext": "Final fallback",
    }
    problem = extract_problem_statement(submission)

    assert "Final fallback" in problem


# ===========================
# validate_submission_completeness() Tests
# ===========================


def test_validate_complete_submission(complete_submission):
    """Test validation of complete submission."""
    is_valid, missing = validate_submission_completeness(complete_submission)

    assert is_valid is True
    assert missing == []


def test_validate_minimal_valid_submission(minimal_submission):
    """Test validation of minimal valid submission."""
    is_valid, missing = validate_submission_completeness(minimal_submission)

    assert is_valid is True
    assert missing == []


def test_validate_missing_submission_id():
    """Test validation catches missing submission_id."""
    submission = {
        "title": "Test",
        "subreddit": "test",
    }
    is_valid, missing = validate_submission_completeness(submission)

    assert is_valid is False
    assert "submission_id" in missing
    assert len(missing) == 1


def test_validate_missing_title():
    """Test validation catches missing title."""
    submission = {
        "submission_id": "test123",
        "subreddit": "test",
    }
    is_valid, missing = validate_submission_completeness(submission)

    assert is_valid is False
    assert "title" in missing
    assert len(missing) == 1


def test_validate_missing_subreddit():
    """Test validation catches missing subreddit."""
    submission = {
        "submission_id": "test123",
        "title": "Test",
    }
    is_valid, missing = validate_submission_completeness(submission)

    assert is_valid is False
    assert "subreddit" in missing
    assert len(missing) == 1


def test_validate_missing_multiple_fields():
    """Test validation catches multiple missing fields."""
    submission = {"submission_id": "test123"}
    is_valid, missing = validate_submission_completeness(submission)

    assert is_valid is False
    assert "title" in missing
    assert "subreddit" in missing
    assert len(missing) == 2


def test_validate_empty_submission():
    """Test validation of completely empty submission."""
    submission = {}
    is_valid, missing = validate_submission_completeness(submission)

    assert is_valid is False
    assert set(missing) == {"submission_id", "title", "subreddit"}


def test_validate_empty_string_fields():
    """Test that empty string values are caught as invalid."""
    submission = {
        "submission_id": "",
        "title": "",
        "subreddit": "",
    }
    is_valid, missing = validate_submission_completeness(submission)

    assert is_valid is False
    assert len(missing) == 3


def test_validate_whitespace_only_fields():
    """Test that whitespace-only values are caught as invalid."""
    submission = {
        "submission_id": "   ",
        "title": "\t\n",
        "subreddit": "  ",
    }
    is_valid, missing = validate_submission_completeness(submission)

    assert is_valid is False
    assert len(missing) == 3


def test_validate_none_fields():
    """Test that None values are caught as invalid."""
    submission = {
        "submission_id": None,
        "title": None,
        "subreddit": None,
    }
    is_valid, missing = validate_submission_completeness(submission)

    assert is_valid is False
    assert len(missing) == 3


def test_validate_partial_none_fields():
    """Test validation with some None and some valid fields."""
    submission = {
        "submission_id": "test123",
        "title": None,
        "subreddit": "test",
    }
    is_valid, missing = validate_submission_completeness(submission)

    assert is_valid is False
    assert missing == ["title"]


def test_validate_extra_fields_dont_affect_validation(complete_submission):
    """Test that extra fields beyond required don't affect validation."""
    is_valid, missing = validate_submission_completeness(complete_submission)

    # Should be valid despite having many extra fields
    assert is_valid is True
    assert missing == []
