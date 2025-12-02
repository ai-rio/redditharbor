"""Pre-AI quality scoring for submissions.

This module provides quality scoring functions to evaluate Reddit submissions
before sending them for expensive AI analysis. Extracted from dlt_trust_pipeline.py
to enable code reuse across the pipeline.
"""

import time
from datetime import datetime
from typing import Any

from .thresholds import PROBLEM_KEYWORDS


def calculate_pre_ai_quality_score(post: dict[str, Any]) -> float:
    """
    Calculate quality score for opportunity posts BEFORE AI analysis.

    This scoring function evaluates submissions based on three key dimensions:
    engagement (community validation), problem keyword density (relevance),
    and recency (timeliness). Extracted from scripts/dlt/dlt_trust_pipeline.py
    line 101 to enable reuse across pipeline components.

    Quality factors:
    - Engagement (0-40 points): upvotes + comments
    - Problem keyword density (0-30 points): presence of problem indicators
    - Recency (0-30 points): newer posts score higher

    Args:
        post: Reddit post data dictionary with fields:
            - upvotes or score: post score
            - comments_count or num_comments: comment count
            - title: post title
            - text or content: post body
            - created_utc: creation timestamp (Unix or ISO string)

    Returns:
        float: Quality score (0-100), rounded to 2 decimal places

    Examples:
        >>> post = {
        ...     'upvotes': 50,
        ...     'num_comments': 20,
        ...     'title': 'I have a problem with my workflow',
        ...     'text': 'It is frustrating and difficult',
        ...     'created_utc': time.time()
        ... }
        >>> score = calculate_pre_ai_quality_score(post)
        >>> assert 0 <= score <= 100
        >>> assert isinstance(score, float)
    """
    # Engagement score (0-40 points)
    score = post.get("upvotes") or post.get("score") or 0
    num_comments = post.get("comments_count") or post.get("num_comments") or 0
    engagement = min(40, (score + num_comments * 2) / 2)

    # Problem keyword density (0-30 points)
    full_text = f"{post.get('title') or ''} {post.get('text') or post.get('content') or ''}"
    problem_kw_count = len([kw for kw in PROBLEM_KEYWORDS if kw in full_text.lower()])
    keyword_score = min(30, problem_kw_count * 10)

    # Recency score (0-30 points)
    created_utc = post.get("created_utc", time.time())
    if isinstance(created_utc, str):
        # Handle ISO datetime strings
        created_utc = datetime.fromisoformat(created_utc.replace("Z", "+00:00")).timestamp()
    age_hours = (time.time() - created_utc) / 3600
    recency_score = max(0, 30 - (age_hours / 24))  # Decay over 24 hours

    total = engagement + keyword_score + recency_score
    return round(total, 2)


def get_quality_breakdown(post: dict[str, Any]) -> dict[str, float]:
    """
    Get detailed breakdown of quality score components.

    Provides insight into how each dimension (engagement, keywords, recency)
    contributes to the overall quality score. Useful for debugging and
    understanding why posts pass or fail quality filters.

    Args:
        post: Reddit post data dictionary

    Returns:
        dict: Breakdown with keys:
            - engagement_score: Points from upvotes and comments (0-40)
            - keyword_score: Points from problem keywords (0-30)
            - recency_score: Points from post age (0-30)
            - total_score: Overall quality score (0-100)
            - problem_keyword_count: Number of problem keywords found

    Examples:
        >>> post = {
        ...     'upvotes': 10,
        ...     'num_comments': 5,
        ...     'title': 'Problem with my issue',
        ...     'created_utc': time.time()
        ... }
        >>> breakdown = get_quality_breakdown(post)
        >>> assert 'engagement_score' in breakdown
        >>> assert 'keyword_score' in breakdown
        >>> assert 'recency_score' in breakdown
        >>> assert 'total_score' in breakdown
    """
    # Engagement score (0-40 points)
    score = post.get("upvotes") or post.get("score") or 0
    num_comments = post.get("comments_count") or post.get("num_comments") or 0
    engagement = min(40, (score + num_comments * 2) / 2)

    # Problem keyword density (0-30 points)
    full_text = f"{post.get('title') or ''} {post.get('text') or post.get('content') or ''}"
    problem_kw_count = len([kw for kw in PROBLEM_KEYWORDS if kw in full_text.lower()])
    keyword_score = min(30, problem_kw_count * 10)

    # Recency score (0-30 points)
    created_utc = post.get("created_utc", time.time())
    if isinstance(created_utc, str):
        # Handle ISO datetime strings
        created_utc = datetime.fromisoformat(created_utc.replace("Z", "+00:00")).timestamp()
    age_hours = (time.time() - created_utc) / 3600
    recency_score = max(0, 30 - (age_hours / 24))  # Decay over 24 hours

    total = engagement + keyword_score + recency_score

    return {
        "engagement_score": float(round(engagement, 2)),
        "keyword_score": float(round(keyword_score, 2)),
        "recency_score": float(round(recency_score, 2)),
        "total_score": float(round(total, 2)),
        "problem_keyword_count": problem_kw_count,
    }
