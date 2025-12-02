"""
Standalone OLD filter implementation for testing (extracted from dlt_trust_pipeline.py).

This module contains EXACT copies of the OLD filtering functions without
dependencies on the rest of the codebase. Used for baseline testing.

Source: scripts/dlt/dlt_trust_pipeline.py lines 92-176
"""

import time
from datetime import datetime
from typing import Any


# Pre-AI filtering constants - PRODUCTION READY: Balanced for cost efficiency + quality
# Production thresholds - balanced to filter spam while allowing quality posts through
# Trust validation and AI scoring provide additional quality gates
MIN_ENGAGEMENT_SCORE = 5   # Minimum upvotes (moderate engagement)
MIN_PROBLEM_KEYWORDS = 1   # Minimum problem keywords (at least one clear problem indicator)
MIN_COMMENT_COUNT = 1      # Minimum comments (at least some discussion)
MIN_QUALITY_SCORE = 15.0   # Minimum quality score before AI analysis (lowered for testing) (lower bar for quality)


# Problem keywords (from core.fetchers.collection PROBLEM_KEYWORDS)
PROBLEM_KEYWORDS = [
    "pain", "problem", "frustrated", "wish", "if only", "hate", "annoying", "difficult",
    "struggle", "confusing", "complicated", "time consuming", "manual", "tedious",
    "cumbersome", "inefficient", "slow", "expensive", "costly", "broken", "doesn't work",
    "fails", "error", "bug", "issue", "limitation", "lacks", "missing", "no way to",
    "hard to", "impossible", "can't", "unable to", "annoying", "irksome", "aggravating"
]


def calculate_pre_ai_quality_score(post: dict[str, Any]) -> float:
    """
    Calculate quality score for opportunity posts BEFORE AI analysis.

    EXACT COPY from scripts/dlt/dlt_trust_pipeline.py lines 101-134

    Quality factors:
    - Engagement (upvotes + comments)
    - Problem keyword density
    - Recency (newer = better)

    Returns:
        Float quality score (0-100)
    """
    # Engagement score (0-40 points)
    score = post.get("upvotes") or post.get("score") or 0
    num_comments = post.get("comments_count") or post.get("num_comments") or 0
    # Handle negative values
    score = max(0, score)
    num_comments = max(0, num_comments)
    engagement = min(40, (score + num_comments * 2) / 2)

    # Problem keyword density (0-30 points)
    full_text = f"{post.get('title', '')} {post.get('text', '') or post.get('content', '')}"
    problem_kw_count = len([kw for kw in PROBLEM_KEYWORDS if kw in full_text.lower()])
    keyword_score = min(30, problem_kw_count * 10)

    # Recency score (0-30 points)
    created_utc = post.get("created_utc", time.time())
    if isinstance(created_utc, str):
        # Handle ISO datetime strings
        created_utc = datetime.fromisoformat(created_utc.replace('Z', '+00:00')).timestamp()
    age_hours = (time.time() - created_utc) / 3600
    recency_score = max(0, 30 - (age_hours / 24))  # Decay over 24 hours

    total = engagement + keyword_score + recency_score
    return round(total, 2)


def should_analyze_with_ai(post: dict[str, Any]) -> bool:
    """
    Pre-filter posts to determine if they should be sent to AI analysis.

    EXACT COPY from scripts/dlt/dlt_trust_pipeline.py lines 137-176

    This prevents expensive AI calls on low-quality content and ensures
    we only analyze posts that have documented rare score potential.

    Args:
        post: Reddit post data

    Returns:
        True if post meets minimum quality criteria for AI analysis

    NOTE: Filtering is TEMPORARILY DISABLED in the original (line 152: return True)
    This copy includes the INTENDED filtering logic when re-enabled.
    """
    # TEMPORARILY DISABLED FOR TRUST VALIDATION TESTING
    # Trust layer will handle quality filtering
    return True

    # The following code is COMMENTED OUT in the original but shows intended behavior:

    # # Check minimum engagement
    # upvotes = post.get("upvotes", 0) or post.get("score", 0)
    # if upvotes < MIN_ENGAGEMENT_SCORE:
    #     return False

    # # Check minimum comments (community engagement)
    # comments = post.get("comments_count", 0) or post.get("num_comments", 0)
    # if comments < MIN_COMMENT_COUNT:
    #     return False

    # # Check problem keywords (must show clear problem)
    # full_text = f"{post.get('title', '')} {post.get('text', '') or post.get('content', '')}"
    # problem_kw_count = len([kw for kw in PROBLEM_KEYWORDS if kw in full_text.lower()])
    # if problem_kw_count < MIN_PROBLEM_KEYWORDS:
    #     return False

    # # Check quality score
    # quality_score = calculate_pre_ai_quality_score(post)
    # if quality_score < MIN_QUALITY_SCORE:
    #     return False

    # return True


def should_analyze_with_ai_if_enabled(post: dict[str, Any]) -> bool:
    """
    Version of should_analyze_with_ai with filtering ENABLED.

    This represents what the OLD system WOULD do if filtering was re-enabled.
    """
    # Check minimum engagement
    upvotes = post.get("upvotes", 0) or post.get("score", 0)
    if upvotes < MIN_ENGAGEMENT_SCORE:
        return False

    # Check minimum comments (community engagement)
    comments = post.get("comments_count", 0) or post.get("num_comments", 0)
    if comments < MIN_COMMENT_COUNT:
        return False

    # Check problem keywords (must show clear problem)
    full_text = f"{post.get('title', '')} {post.get('text', '') or post.get('content', '')}"
    problem_kw_count = len([kw for kw in PROBLEM_KEYWORDS if kw in full_text.lower()])
    if problem_kw_count < MIN_PROBLEM_KEYWORDS:
        return False

    # Check quality score
    quality_score = calculate_pre_ai_quality_score(post)
    if quality_score < MIN_QUALITY_SCORE:
        return False

    return True
