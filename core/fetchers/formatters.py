"""Submission data formatting utilities.

This module provides utilities for formatting Reddit submission data
for AI agent consumption and analysis. Extracted from monolithic pipeline
scripts to enable code reuse across the codebase.
"""

from datetime import datetime
from typing import Any


def format_submission_for_agent(submission: dict[str, Any], *,
                               use_legacy_fields: bool = True) -> dict[str, Any]:
    """
    Format a submission for LLM profiler enrichment.

    Standardizes field names, handles missing data, and adds engagement metadata.
    Supports both legacy (app_opportunities) and new (submissions) schemas.

    Args:
        submission: Submission data from database table or raw Reddit data
        use_legacy_fields: Include legacy submission_id field for backward compatibility

    Returns:
        dict: Formatted opportunity data for AI profile generation

    Examples:
        >>> raw = {
        ...     'id': 'uuid-123',
        ...     'reddit_id': 't3_abc123',
        ...     'title': 'Looking for fitness app',
        ...     'content': 'Need something to track workouts',
        ...     'score': 42,
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

    # Format engagement data - support both old and new column names
    # Legacy: reddit_score, New: score
    score_value = submission.get("score") or submission.get("reddit_score", 0) or 0
    engagement = {
        "upvotes": score_value,
        "num_comments": submission.get("num_comments", 0) or 0,
    }

    # Include trust metadata for context (legacy fields)
    comments = []
    trust_score = submission.get("trust_score")
    trust_badge = submission.get("trust_badge")

    if trust_score:
        comments.append(f"Trust Score: {trust_score}")
    if trust_badge:
        comments.append(f"Trust Badge: {trust_badge}")

    # Handle timestamp fields - support both created_at and created_utc
    created_timestamp = submission.get("created_at") or submission.get("created_utc")

    # Build the formatted submission
    formatted = {
        "reddit_id": submission.get("reddit_id"),  # Reddit's native ID (e.g., "t3_abc123")
        "title": title,
        "text": full_text,
        "subreddit": submission.get("subreddit", ""),  # May be empty for new schema
        "engagement": engagement,
        "comments": comments,
        "created_utc": created_timestamp,
        "author": submission.get("author"),
        "sentiment_score": submission.get("sentiment_score", 0.0),
        "db_id": submission.get("id"),  # Database UUID
        "url": submission.get("url"),  # Submission URL
    }

    # Add legacy fields if requested (default for backward compatibility)
    if use_legacy_fields:
        # Prefer submission_id if available, fallback to id, then reddit_id
        legacy_id = (
            submission.get("submission_id") or
            submission.get("id") or
            submission.get("reddit_id") or
            "unknown"
        )
        formatted["submission_id"] = legacy_id
        formatted["id"] = legacy_id
    else:
        # Use configured primary identifier as 'id'
        # Priority: submission_id > id > reddit_id
        if "submission_id" in submission:
            formatted["id"] = submission["submission_id"]
        elif "id" in submission:
            formatted["id"] = submission["id"]
        elif "reddit_id" in submission:
            formatted["id"] = submission["reddit_id"]
        else:
            formatted["id"] = "unknown"

    return formatted


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
    and AI enrichment. Supports both legacy and new schemas.

    Args:
        submission: Submission data dictionary

    Returns:
        tuple: (is_valid, list of missing fields)
            - is_valid: True if all required fields present
            - missing: List of field names that are missing or empty

    Examples:
        >>> valid_sub = {
        ...     'id': 'uuid-123',
        ...     'reddit_id': 't3_abc123',
        ...     'title': 'Need app'
        ... }
        >>> is_valid, missing = validate_submission_completeness(valid_sub)
        >>> assert is_valid is True
        >>> assert len(missing) == 0

        >>> incomplete = {'id': 'uuid-123'}
        >>> is_valid, missing = validate_submission_completeness(incomplete)
        >>> assert is_valid is False
        >>> assert 'title' in missing
    """
    missing = []

    # Check for title (always required)
    value = submission.get("title")
    if not value or (isinstance(value, str) and not value.strip()):
        missing.append("title")

    # Check for ID field - accept any of: submission_id, id, or reddit_id
    has_id = (
        submission.get("submission_id") or
        submission.get("id") or
        submission.get("reddit_id")
    )
    if not has_id:
        missing.append("id_field")  # Generic ID field missing

    # Subreddit is optional for new schema (has subreddit_id instead)
    # Only require for legacy schema
    if "submission_id" in submission:
        # Legacy schema - require subreddit
        value = submission.get("subreddit")
        if not value or (isinstance(value, str) and not value.strip()):
            missing.append("subreddit")

    return len(missing) == 0, missing
