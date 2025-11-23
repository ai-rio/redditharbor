# Data Fetchers

Data acquisition layer with pluggable data sources for Reddit content retrieval and processing.

## Overview

This module provides a unified interface for fetching Reddit submissions from multiple data sources. It implements the Strategy pattern with an abstract base class and concrete implementations for database queries and live Reddit API calls. The fetchers handle validation, filtering, deduplication, and standardized data formatting for downstream AI analysis pipelines.

## Modules

| Module | Description |
|--------|-------------|
| `__init__.py` | Package initialization |
| `base_fetcher.py` | Abstract base class (`BaseFetcher`) defining the common interface for all fetchers with statistics tracking and validation |
| `database_fetcher.py` | `DatabaseFetcher` implementation for retrieving submissions from Supabase `app_opportunities` table with batch pagination and content-based deduplication |
| `reddit_api_fetcher.py` | `RedditAPIFetcher` implementation using PRAW for live Reddit API access with problem-keyword filtering and configurable sorting |
| `formatters.py` | Data formatting utilities including `format_submission_for_agent()`, `format_batch_submissions()`, and validation functions |
| `collection.py` | Comprehensive Reddit data collection module with comment collection, sentiment analysis, and monetizable app research support |

## Usage Examples

### Fetching from Database

```python
from supabase import create_client
from core.fetchers.database_fetcher import DatabaseFetcher

client = create_client(url, key)
fetcher = DatabaseFetcher(client, config={
    "batch_size": 500,
    "deduplicate": True,
    "table_name": "app_opportunities"
})

# Fetch limited submissions
for submission in fetcher.fetch(limit=100):
    print(f"Processing: {submission['title']}")

# Check statistics
stats = fetcher.get_statistics()
print(f"Fetched: {stats['fetched']}, Filtered: {stats['filtered']}")
```

### Fetching from Reddit API

```python
import praw
from core.fetchers.reddit_api_fetcher import RedditAPIFetcher

reddit = praw.Reddit(client_id=..., client_secret=..., user_agent=...)
fetcher = RedditAPIFetcher(reddit, config={
    "sort_type": "hot",
    "filter_keywords": True,
    "min_keywords": 1
})

# Fetch from single subreddit
for submission in fetcher.fetch(limit=50, subreddit="SaaS"):
    print(f"Title: {submission['title']}")

# Fetch from multiple subreddits
for submission in fetcher.fetch(limit=25, subreddits=["SaaS", "startups"]):
    process(submission)
```

### Using Formatters

```python
from core.fetchers.formatters import (
    format_submission_for_agent,
    format_batch_submissions,
    validate_submission_completeness
)

# Format single submission for AI analysis
raw = {
    "submission_id": "abc123",
    "title": "Looking for fitness app",
    "content": "Need something to track workouts",
    "subreddit": "fitness",
    "reddit_score": 42,
    "num_comments": 5
}
formatted = format_submission_for_agent(raw)
# Returns: {id, title, text, subreddit, engagement, comments, ...}

# Validate submission completeness
is_valid, missing = validate_submission_completeness(raw)
```

### Using Collection Functions

```python
from core.fetchers.collection import (
    collect_data,
    collect_monetizable_opportunities_data,
    get_collection_status
)

# Basic data collection
success = collect_data(
    reddit_client=reddit,
    supabase_client=supabase,
    db_config={"submission": "submissions", "comment": "comments"},
    subreddits=["fitness", "personalfinance"],
    limit=100,
    sort_types=["hot", "new"],
    mask_pii=True
)

# Monetizable app research collection
success = collect_monetizable_opportunities_data(
    reddit_client=reddit,
    supabase_client=supabase,
    db_config=db_config,
    market_segment="health_fitness",  # or "all"
    limit_per_sort=100,
    time_filter="month",
    sentiment_analysis=True
)
```

## Architecture

```
BaseFetcher (ABC)
    |
    +-- DatabaseFetcher    # Supabase app_opportunities
    |       - Batch pagination
    |       - Content-based deduplication
    |       - Standardized formatting
    |
    +-- RedditAPIFetcher   # PRAW Reddit API
            - Problem keyword filtering
            - Sort type configuration
            - Rate limiting

Formatters
    |
    +-- format_submission_for_agent()  # Single submission
    +-- format_batch_submissions()     # Batch processing
    +-- extract_problem_statement()    # Problem extraction
    +-- validate_submission_completeness()

Collection
    |
    +-- collect_data()                      # Main entry point
    +-- collect_submissions()               # Submission collection
    +-- collect_comments_for_submissions()  # Comment collection
    +-- collect_monetizable_opportunities_data()  # Research-focused
    +-- collect_with_dlt_validation()       # DLT integration
```

## Related Modules

- `core/quality_filters/` - Quality filtering and scoring thresholds
- `core/processing/` - Data processing pipeline components
- `config/settings.py` - Configuration constants and database mappings
