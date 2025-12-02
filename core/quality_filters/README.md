# Quality Filters

Pre-AI filtering module to reduce unnecessary AI processing costs by evaluating Reddit submissions before expensive AI analysis.

## Overview

This module provides quality scoring and filtering functions that evaluate Reddit submissions based on engagement metrics, problem keyword density, and recency. Posts that do not meet configurable quality thresholds are filtered out before being sent to AI analysis, reducing API costs and improving signal-to-noise ratio.

## Modules

| Module | Description |
|--------|-------------|
| `thresholds.py` | Quality threshold constants and problem keyword definitions |
| `quality_scorer.py` | Quality scoring functions with detailed breakdown capabilities |
| `pre_filter.py` | Pre-filtering logic for individual posts and batch processing |

## Usage Examples

### Basic Quality Scoring

```python
import time
from core.quality_filters.quality_scorer import calculate_pre_ai_quality_score, get_quality_breakdown

post = {
    'upvotes': 50,
    'num_comments': 20,
    'title': 'I have a problem with my workflow',
    'text': 'It is frustrating and difficult to manage',
    'created_utc': time.time()
}

# Get overall quality score (0-100)
score = calculate_pre_ai_quality_score(post)
print(f"Quality score: {score}")

# Get detailed breakdown
breakdown = get_quality_breakdown(post)
print(f"Engagement: {breakdown['engagement_score']}/40")
print(f"Keywords: {breakdown['keyword_score']}/30")
print(f"Recency: {breakdown['recency_score']}/30")
```

### Single Post Filtering

```python
from core.quality_filters.pre_filter import should_analyze_with_ai

post = {
    'upvotes': 50,
    'num_comments': 10,
    'title': 'Struggling with data pipeline issues',
    'text': 'This is frustrating and time consuming'
}

should_analyze, score, reason = should_analyze_with_ai(post)

if should_analyze:
    print(f"Post passed (score: {score}): {reason}")
else:
    print(f"Post filtered (score: {score}): {reason}")
```

### Batch Filtering

```python
from core.quality_filters.pre_filter import filter_submissions_batch, get_filter_stats

posts = [
    {'upvotes': 50, 'num_comments': 10, 'title': 'Problem with workflow', 'text': 'frustrated'},
    {'upvotes': 1, 'num_comments': 0, 'title': 'Test post'},
    {'upvotes': 30, 'num_comments': 5, 'title': 'Another issue', 'text': 'difficult to use'}
]

passed, filtered = filter_submissions_batch(posts)

print(f"Passed: {len(passed)}, Filtered: {len(filtered)}")

# Get filtering statistics
stats = get_filter_stats(filtered)
for reason, count in stats.items():
    print(f"  {reason}: {count}")
```

### Custom Thresholds

```python
from core.quality_filters.pre_filter import should_analyze_with_ai

# Use custom quality threshold
should_analyze, score, reason = should_analyze_with_ai(
    post,
    quality_threshold=25.0,  # Higher threshold for stricter filtering
    enable_filtering=True
)

# Disable filtering for testing
should_analyze, score, reason = should_analyze_with_ai(
    post,
    enable_filtering=False  # All posts pass, useful for testing
)
```

## Quality Score Components

The quality score (0-100) is calculated from three dimensions:

- **Engagement (0-40 points)**: Based on upvotes and comment count, reflecting community validation
- **Problem Keywords (0-30 points)**: Presence of problem indicators like "frustrated", "difficult", "issue"
- **Recency (0-30 points)**: Newer posts score higher, with decay over 24 hours

## Default Thresholds

| Threshold | Value | Description |
|-----------|-------|-------------|
| `MIN_ENGAGEMENT_SCORE` | 5 | Minimum upvotes required |
| `MIN_COMMENT_COUNT` | 1 | Minimum comments required |
| `MIN_PROBLEM_KEYWORDS` | 1 | Minimum problem keywords required |
| `MIN_QUALITY_SCORE` | 15.0 | Minimum overall quality score |

## Related Modules

- `core/collection.py` - Reddit data collection pipeline
- `scripts/dlt/dlt_trust_pipeline.py` - DLT pipeline that uses these filters
