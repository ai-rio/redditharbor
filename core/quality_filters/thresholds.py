"""Quality filtering thresholds and constants.

This module defines threshold values for pre-AI quality scoring and filtering.
Extracted from dlt_trust_pipeline.py to enable code reuse and configuration management.
"""

# Minimum engagement thresholds for AI analysis
MIN_ENGAGEMENT_SCORE = 5  # Minimum upvotes (moderate engagement)
MIN_COMMENT_COUNT = 1  # Minimum comments (at least some discussion)

# Content quality thresholds
MIN_PROBLEM_KEYWORDS = 1  # Minimum problem keywords (at least one clear problem indicator)
MIN_QUALITY_SCORE = 15.0  # Minimum quality score before AI analysis (lowered for testing)

# Default threshold for should_analyze_with_ai()
DEFAULT_QUALITY_THRESHOLD = MIN_QUALITY_SCORE

# Problem detection keywords (imported from core.collection for consistency)
# These are the standard problem indicators used across the platform
PROBLEM_KEYWORDS = [
    "pain",
    "problem",
    "frustrated",
    "wish",
    "if only",
    "hate",
    "annoying",
    "difficult",
    "struggle",
    "confusing",
    "complicated",
    "time consuming",
    "manual",
    "tedious",
    "cumbersome",
    "inefficient",
    "slow",
    "expensive",
    "costly",
    "broken",
    "doesn't work",
    "fails",
    "error",
    "bug",
    "issue",
    "limitation",
    "lacks",
    "missing",
    "no way to",
    "hard to",
    "impossible",
    "can't",
    "unable to",
    "irksome",
    "aggravating",
]
