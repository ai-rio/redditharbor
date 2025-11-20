"""Submission data formatting utilities.

This module provides utilities for formatting Reddit submission data
for AI agent consumption and analysis. Extracted from monolithic pipeline
scripts to enable code reuse across the codebase.
"""

from datetime import datetime
from typing import Any


def format_submission_for_agent(submission: dict[str, Any]) -> dict[str, Any]:
    """
    Format an opportunity from app_opportunities for LLM profiler enrichment.

    Standardizes field names, handles missing data, and adds engagement metadata.
    This function was extracted from batch_opportunity_scoring.py to enable reuse
    across different pipeline components.

    Args:
        submission: Opportunity data from app_opportunities table or raw Reddit data

    Returns:
        dict: Formatted opportunity data for AI profile generation

    Examples:
        >>> raw = {
        ...     'submission_id': 'abc123',
        ...     'title': 'Looking for fitness app',
        ...     'problem_description': 'Need something to track workouts',
        ...     'subreddit': 'fitness',
        ...     'reddit_score': 42,
        ...     'num_comments': 5
        ... }
        >>> formatted = format_submission_for_agent(raw)
        >>> assert 'id' in formatted
        >>> assert 'text' in formatted
        >>> assert 'engagement' in formatted
    """
    # Use existing problem_description, content, or selftext for full text analysis
    title = submission.get("title", "")
    text = (
        submission.get("problem_description", "") or
        submission.get("content", "") or
        submission.get("selftext", "")
    )
    full_text = f"{title}\n\n{text}".strip() if text else title

    # Format engagement data using app_opportunities column names
    engagement = {
        "upvotes": submission.get("reddit_score", 0) or 0,
        "num_comments": submission.get("num_comments", 0) or 0,
    }

    # Include trust metadata for context
    comments = []
    trust_score = submission.get("trust_score")
    trust_badge = submission.get("trust_badge")

    if trust_score:
        comments.append(f"Trust Score: {trust_score}")
    if trust_badge:
        comments.append(f"Trust Badge: {trust_badge}")

    return {
        "submission_id": submission.get("submission_id", submission.get("id", "unknown")),
        "id": submission.get("submission_id", submission.get("id", "unknown")),
        "title": title,
        "text": full_text,
        "subreddit": submission.get("subreddit", ""),
        "engagement": engagement,
        "comments": comments,
        "created_utc": submission.get("created_utc"),
        "author": submission.get("author"),
        "sentiment_score": submission.get("sentiment_score", 0.0),
        "db_id": submission.get("id"),  # Keep reference to database UUID
    }


def format_batch_submissions(
    submissions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Format multiple submissions for batch processing.

    Convenience function to apply format_submission_for_agent to a list
    of submissions efficiently.

    Args:
        submissions: List of raw submission dictionaries

    Returns:
        list: List of formatted submissions

    Examples:
        >>> submissions = [
        ...     {'submission_id': '1', 'title': 'Test 1', 'subreddit': 'test'},
        ...     {'submission_id': '2', 'title': 'Test 2', 'subreddit': 'test'}
        ... ]
        >>> formatted = format_batch_submissions(submissions)
        >>> assert len(formatted) == 2
        >>> assert all('id' in s for s in formatted)
    """
    return [format_submission_for_agent(sub) for sub in submissions]


def extract_problem_statement(submission: dict[str, Any]) -> str:
    """
    Extract the core problem statement from a submission.

    Combines title and content into a concise problem description,
    truncating long content to the first 500 characters.

    Args:
        submission: Submission data dictionary

    Returns:
        str: Concise problem statement

    Examples:
        >>> submission = {
        ...     'title': 'Need fitness app',
        ...     'problem_description': 'Looking for something to track my workouts'
        ... }
        >>> problem = extract_problem_statement(submission)
        >>> assert 'Need fitness app' in problem
        >>> assert 'track my workouts' in problem
    """
    title = submission.get("title", "").strip()
    # Check both problem_description and content/selftext fields
    content = (
        submission.get("problem_description", "")
        or submission.get("content", "")
        or submission.get("selftext", "")
    ).strip()

    # Combine title and first 500 chars of content
    if content:
        content_preview = content[:500] + ("..." if len(content) > 500 else "")
        return f"{title}\n\n{content_preview}"
    return title


def validate_submission_completeness(
    submission: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    Validate submission has all required fields for AI analysis.

    Checks for presence of essential fields needed for opportunity scoring
    and AI enrichment.

    Args:
        submission: Submission data dictionary

    Returns:
        tuple: (is_valid, list of missing fields)
            - is_valid: True if all required fields present
            - missing: List of field names that are missing or empty

    Examples:
        >>> valid_sub = {
        ...     'submission_id': 'abc123',
        ...     'title': 'Need app',
        ...     'subreddit': 'SaaS'
        ... }
        >>> is_valid, missing = validate_submission_completeness(valid_sub)
        >>> assert is_valid is True
        >>> assert len(missing) == 0

        >>> incomplete = {'submission_id': 'abc123'}
        >>> is_valid, missing = validate_submission_completeness(incomplete)
        >>> assert is_valid is False
        >>> assert 'title' in missing
        >>> assert 'subreddit' in missing
    """
    required_fields = ["submission_id", "title", "subreddit"]
    missing = []

    for field in required_fields:
        value = submission.get(field)
        # Check if field is missing, None, or empty string
        if not value or (isinstance(value, str) and not value.strip()):
            missing.append(field)

    return len(missing) == 0, missing
