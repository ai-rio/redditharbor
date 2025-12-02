"""Cost-saving thresholds for pre-AI filtering.

These thresholds filter approximately 60% of submissions before expensive AI calls,
saving approximately $3,528/year at 10K posts/month based on production data.

Extracted from:
- core/quality_filters/thresholds.py
- scripts/dlt/dlt_trust_pipeline.py lines 92-99
"""

# Engagement thresholds
MIN_ENGAGEMENT_SCORE = 5  # Minimum upvotes (moderate engagement)
MIN_COMMENT_COUNT = 1  # Minimum comments (at least some discussion)

# Quality thresholds
MIN_QUALITY_SCORE = 15.0  # Minimum calculated quality score
MIN_PROBLEM_KEYWORDS = 1  # Minimum problem indicators

# Default threshold for should_analyze_with_ai()
DEFAULT_QUALITY_THRESHOLD = MIN_QUALITY_SCORE

# Problem keywords (from core.fetchers.collection PROBLEM_KEYWORDS)
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
