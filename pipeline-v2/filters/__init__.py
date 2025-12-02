"""Pre-AI quality filtering for cost-effective submission analysis.

This module provides filtering logic to reduce expensive AI calls by ~60%
through quality-based pre-filtering.

Extracted from:
- core/quality_filters/
- scripts/dlt/dlt_trust_pipeline.py

Main Functions:
- should_analyze_with_ai(): Determine if submission meets quality criteria
- calculate_pre_ai_quality_score(): Score submission quality (0-100)
- filter_submissions_batch(): Batch filtering with statistics
- get_filter_stats(): Analyze filtering reasons

Usage:
    >>> from pipeline-v2.filters import should_analyze_with_ai
    >>> should_analyze, score, reason = should_analyze_with_ai(post)
    >>> if should_analyze:
    ...     # Send to AI analysis
    ...     pass
"""

from .quality import (
    calculate_pre_ai_quality_score,
    filter_submissions_batch,
    get_filter_stats,
    get_quality_breakdown,
    should_analyze_with_ai,
)
from .thresholds import (
    DEFAULT_QUALITY_THRESHOLD,
    MIN_COMMENT_COUNT,
    MIN_ENGAGEMENT_SCORE,
    MIN_PROBLEM_KEYWORDS,
    MIN_QUALITY_SCORE,
    PROBLEM_KEYWORDS,
)

__all__ = [
    # Threshold constants
    "DEFAULT_QUALITY_THRESHOLD",
    "MIN_COMMENT_COUNT",
    "MIN_ENGAGEMENT_SCORE",
    "MIN_PROBLEM_KEYWORDS",
    "MIN_QUALITY_SCORE",
    "PROBLEM_KEYWORDS",
    # Quality filtering functions
    "calculate_pre_ai_quality_score",
    "filter_submissions_batch",
    "get_filter_stats",
    "get_quality_breakdown",
    "should_analyze_with_ai",
]
