"""Pre-AI filtering logic for submissions.

This module provides filtering functions to determine which submissions should
undergo expensive AI analysis. Extracted from dlt_trust_pipeline.py line 137
to enable code reuse and consistent filtering across the pipeline.
"""

from typing import Any

from .quality_scorer import calculate_pre_ai_quality_score
from .thresholds import (
    DEFAULT_QUALITY_THRESHOLD,
    MIN_COMMENT_COUNT,
    MIN_ENGAGEMENT_SCORE,
    MIN_PROBLEM_KEYWORDS,
    PROBLEM_KEYWORDS,
)


def should_analyze_with_ai(
    post: dict[str, Any],
    quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
    enable_filtering: bool = True,
) -> tuple[bool, float, str]:
    """
    Determine if a post should undergo AI analysis based on quality criteria.

    This pre-filter prevents expensive AI calls on low-quality content by
    checking engagement levels, problem keyword presence, and overall quality
    score. Extracted from scripts/dlt/dlt_trust_pipeline.py line 137.

    Args:
        post: Reddit post data dictionary
        quality_threshold: Minimum quality score required (default: 15.0)
        enable_filtering: If False, always returns True (for testing)

    Returns:
        tuple: (should_analyze, quality_score, reason)
            - should_analyze: True if post meets criteria
            - quality_score: Calculated quality score
            - reason: Human-readable explanation of decision

    Examples:
        >>> high_quality = {
        ...     'upvotes': 50,
        ...     'num_comments': 20,
        ...     'title': 'I have a problem with my workflow',
        ...     'text': 'It is frustrating',
        ...     'created_utc': time.time()
        ... }
        >>> should_analyze, score, reason = should_analyze_with_ai(high_quality)
        >>> assert should_analyze is True
        >>> assert score > 15.0

        >>> low_quality = {'upvotes': 1, 'num_comments': 0, 'title': 'Test'}
        >>> should_analyze, score, reason = should_analyze_with_ai(low_quality)
        >>> assert should_analyze is False
    """
    # Calculate quality score for reporting
    quality_score = calculate_pre_ai_quality_score(post)

    # If filtering is disabled (testing mode), pass everything
    if not enable_filtering:
        return True, quality_score, "Filtering disabled (test mode)"

    # Check minimum engagement
    upvotes = post.get("upvotes") or post.get("score") or 0
    if upvotes < MIN_ENGAGEMENT_SCORE:
        return (
            False,
            quality_score,
            f"Insufficient engagement ({upvotes} upvotes < {MIN_ENGAGEMENT_SCORE} minimum)",
        )

    # Check minimum comments (community engagement)
    comments = post.get("comments_count") or post.get("num_comments") or 0
    if comments < MIN_COMMENT_COUNT:
        return (
            False,
            quality_score,
            f"Insufficient comments ({comments} comments < {MIN_COMMENT_COUNT} minimum)",
        )

    # Check problem keywords (must show clear problem)
    full_text = f"{post.get('title') or ''} {post.get('text') or post.get('content') or ''}"
    problem_kw_count = len([kw for kw in PROBLEM_KEYWORDS if kw in full_text.lower()])
    if problem_kw_count < MIN_PROBLEM_KEYWORDS:
        return (
            False,
            quality_score,
            f"Insufficient problem keywords ({problem_kw_count} found < {MIN_PROBLEM_KEYWORDS} minimum)",
        )

    # Check overall quality score
    if quality_score < quality_threshold:
        return (
            False,
            quality_score,
            f"Quality score too low ({quality_score:.1f} < {quality_threshold} threshold)",
        )

    return True, quality_score, "Passed all quality filters"


def filter_submissions_batch(
    submissions: list[dict[str, Any]],
    quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
    enable_filtering: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Filter a batch of submissions for AI analysis.

    Applies should_analyze_with_ai() to a list of submissions and separates
    them into passed and filtered lists, adding quality metadata to each.

    Args:
        submissions: List of Reddit post dictionaries
        quality_threshold: Minimum quality score required
        enable_filtering: If False, all submissions pass

    Returns:
        tuple: (passed_submissions, filtered_submissions)
            - passed_submissions: Posts that meet criteria (with quality metadata)
            - filtered_submissions: Posts that failed filters (with quality metadata and filter_reason)

    Examples:
        >>> posts = [
        ...     {'upvotes': 50, 'num_comments': 10, 'title': 'Problem', 'text': 'frustrated'},
        ...     {'upvotes': 1, 'num_comments': 0, 'title': 'Test'}
        ... ]
        >>> passed, filtered = filter_submissions_batch(posts)
        >>> assert len(passed) >= 0
        >>> assert len(filtered) >= 0
        >>> assert len(passed) + len(filtered) == len(posts)
    """
    passed = []
    filtered = []

    for submission in submissions:
        should_analyze, score, reason = should_analyze_with_ai(
            submission, quality_threshold, enable_filtering
        )

        # Add quality metadata to submission
        submission_with_meta = {
            **submission,
            "quality_score": score,
            "filter_reason": reason,
        }

        if should_analyze:
            passed.append(submission_with_meta)
        else:
            filtered.append(submission_with_meta)

    return passed, filtered


def get_filter_stats(filtered_submissions: list[dict[str, Any]]) -> dict[str, int]:
    """
    Get statistics about why submissions were filtered out.

    Analyzes the filter_reason field to provide a breakdown of filtering reasons.

    Args:
        filtered_submissions: List of submissions that failed quality filters

    Returns:
        dict: Counts of each filter reason

    Examples:
        >>> filtered = [
        ...     {'filter_reason': 'Insufficient engagement (2 upvotes < 5 minimum)'},
        ...     {'filter_reason': 'Insufficient engagement (1 upvotes < 5 minimum)'},
        ...     {'filter_reason': 'Quality score too low (10.5 < 15.0 threshold)'}
        ... ]
        >>> stats = get_filter_stats(filtered)
        >>> assert 'Insufficient engagement' in stats
        >>> assert stats['Insufficient engagement'] == 2
    """
    stats: dict[str, int] = {}

    for submission in filtered_submissions:
        reason = submission.get("filter_reason", "Unknown reason")

        # Extract the reason prefix (before the parenthesis)
        if "(" in reason:
            reason_key = reason.split("(")[0].strip()
        else:
            reason_key = reason

        stats[reason_key] = stats.get(reason_key, 0) + 1

    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
