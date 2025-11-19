# Phase 4: Extract Data Fetching Layer

**Timeline**: Week 3  
**Duration**: 5 days  
**Risk Level**: 🟡 MEDIUM  
**Dependencies**: Phase 3 completed (utilities extracted)

---

## Context

### What Was Completed (Phase 3)
- [x] Extracted all standalone utilities (sector mapping, formatters, quality filters)
- [x] 100% test coverage for extracted utilities
- [x] Both monoliths working with extracted utilities

### Current State
Data fetching logic is embedded in both monoliths:
- `DatabaseFetcher` logic in batch_opportunity_scoring.py (~130 lines)
- `RedditAPIFetcher` logic in dlt_trust_pipeline.py (~35 lines)
- Different interfaces and data formats
- No abstraction for swapping data sources

### Why This Phase Is Critical
- Enables unified pipeline to support both data sources
- Establishes single interface for data acquisition
- Foundation for Phase 8 orchestrator
- Maintains deduplication integration

---

## Objectives

### Primary Goals
1. **Create** `BaseFetcher` abstract interface
2. **Extract** database fetching logic → `DatabaseFetcher`
3. **Extract** Reddit API fetching logic → `RedditAPIFetcher`
4. **Standardize** data format between sources
5. **Integrate** with existing formatters from Phase 3

### Success Criteria
- [ ] Abstract `BaseFetcher` interface defined
- [ ] Both fetchers return identical data structures
- [ ] Both monoliths work with new fetchers (side-by-side)
- [ ] All tests passing with 90%+ coverage
- [ ] Deduplication integration preserved

---

## Tasks

### Task 1: Create BaseFetcher Interface (4 hours)

Already created in Phase 1. Enhance with additional methods:

```python
# core/fetchers/base_fetcher.py (enhance existing)
from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional
from datetime import datetime

class BaseFetcher(ABC):
    """Abstract base class for data fetchers."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.stats = {'fetched': 0, 'filtered': 0, 'errors': 0}
    
    @abstractmethod
    def fetch(self, limit: int, **kwargs) -> Iterator[dict[str, Any]]:
        """Fetch submissions from data source."""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return human-readable source name."""
        pass
    
    def get_statistics(self) -> dict[str, int]:
        """Return fetching statistics."""
        return self.stats.copy()
    
    def validate_submission(self, submission: dict[str, Any]) -> bool:
        """Validate submission has required fields."""
        required_fields = ['submission_id', 'title', 'subreddit']
        return all(field in submission for field in required_fields)
```

---

### Task 2: Extract DatabaseFetcher (1 day)

**Source**: `scripts/core/batch_opportunity_scoring.py:761-893`

**Create**: `core/fetchers/database_fetcher.py`

```python
"""Database fetcher for Supabase submissions."""
from typing import Iterator, Dict, Any, Optional, List
from supabase import Client
from .base_fetcher import BaseFetcher
from .formatters import format_submission_for_agent
import logging

logger = logging.getLogger(__name__)

class DatabaseFetcher(BaseFetcher):
    """Fetch submissions from Supabase database."""
    
    def __init__(self, supabase_client: Client, config: Optional[dict] = None):
        super().__init__(config)
        self.client = supabase_client
        self.table_name = config.get('table_name', 'submission') if config else 'submission'
    
    def fetch(
        self,
        limit: int,
        subreddits: Optional[List[str]] = None,
        min_score: int = 0,
        **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """
        Fetch submissions from database.
        
        Args:
            limit: Maximum number of submissions to fetch
            subreddits: Filter by subreddit list
            min_score: Minimum submission score
            **kwargs: Additional filter parameters
            
        Yields:
            dict: Formatted submission data
        """
        try:
            query = self.client.table(self.table_name).select('*')
            
            # Apply filters
            if subreddits:
                query = query.in_('subreddit', subreddits)
            if min_score > 0:
                query = query.gte('score', min_score)
            
            # Order by created date
            query = query.order('created_utc', desc=True)
            
            # Apply limit
            query = query.limit(limit)
            
            # Execute query
            response = query.execute()
            
            if not response.data:
                logger.warning(f"No submissions found in {self.table_name}")
                return
            
            logger.info(f"Fetched {len(response.data)} submissions from database")
            
            # Format and yield submissions
            for submission in response.data:
                if self.validate_submission(submission):
                    formatted = format_submission_for_agent(submission)
                    self.stats['fetched'] += 1
                    yield formatted
                else:
                    self.stats['filtered'] += 1
                    logger.debug(f"Filtered invalid submission: {submission.get('submission_id')}")
                    
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error fetching from database: {e}")
            raise
    
    def get_source_name(self) -> str:
        return f"Database ({self.table_name})"
    
    def get_submission_by_id(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Fetch specific submission by ID."""
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .eq('submission_id', submission_id)\
                .execute()
            
            if response.data:
                return format_submission_for_agent(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error fetching submission {submission_id}: {e}")
            return None
```

**Update monolith**:
```python
# In batch_opportunity_scoring.py
from core.fetchers.database_fetcher import DatabaseFetcher

# Replace inline fetching logic with:
fetcher = DatabaseFetcher(supabase_client, config={'table_name': 'submission'})
submissions = fetcher.fetch(limit=100, subreddits=['startups', 'SaaS'])
```

---

### Task 3: Extract RedditAPIFetcher (1 day)

**Source**: `scripts/dlt/dlt_trust_pipeline.py:55-90`

**Create**: `core/fetchers/reddit_api_fetcher.py`

```python
"""Reddit API fetcher using PRAW."""
from typing import Iterator, Dict, Any, Optional, List
import praw
from .base_fetcher import BaseFetcher
from .formatters import format_submission_for_agent
from core.activity_validation import is_subreddit_active
import logging

logger = logging.getLogger(__name__)

class RedditAPIFetcher(BaseFetcher):
    """Fetch submissions from Reddit API."""
    
    def __init__(self, reddit_client: praw.Reddit, config: Optional[dict] = None):
        super().__init__(config)
        self.reddit = reddit_client
        self.validate_activity = config.get('validate_activity', True) if config else True
    
    def fetch(
        self,
        limit: int,
        subreddits: List[str],
        time_filter: str = 'week',
        sort: str = 'hot',
        **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """
        Fetch submissions from Reddit API.
        
        Args:
            limit: Maximum submissions per subreddit
            subreddits: List of subreddit names
            time_filter: Time filter (hour, day, week, month, year, all)
            sort: Sort method (hot, new, top, rising)
            
        Yields:
            dict: Formatted submission data
        """
        for subreddit_name in subreddits:
            try:
                # Validate subreddit activity if enabled
                if self.validate_activity:
                    if not is_subreddit_active(self.reddit, subreddit_name):
                        logger.info(f"Skipping inactive subreddit: {subreddit_name}")
                        continue
                
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Fetch submissions based on sort method
                if sort == 'hot':
                    submissions = subreddit.hot(limit=limit)
                elif sort == 'new':
                    submissions = subreddit.new(limit=limit)
                elif sort == 'top':
                    submissions = subreddit.top(time_filter=time_filter, limit=limit)
                elif sort == 'rising':
                    submissions = subreddit.rising(limit=limit)
                else:
                    raise ValueError(f"Unknown sort method: {sort}")
                
                # Process submissions
                for submission in submissions:
                    try:
                        # Convert PRAW submission to dict
                        submission_dict = {
                            'submission_id': submission.id,
                            'title': submission.title,
                            'content': submission.selftext,
                            'subreddit': subreddit_name,
                            'author': str(submission.author) if submission.author else '[deleted]',
                            'score': submission.score,
                            'num_comments': submission.num_comments,
                            'created_utc': int(submission.created_utc),
                            'url': submission.url,
                            'permalink': submission.permalink,
                            'is_self': submission.is_self
                        }
                        
                        if self.validate_submission(submission_dict):
                            formatted = format_submission_for_agent(submission_dict)
                            self.stats['fetched'] += 1
                            yield formatted
                        else:
                            self.stats['filtered'] += 1
                            
                    except Exception as e:
                        self.stats['errors'] += 1
                        logger.error(f"Error processing submission {submission.id}: {e}")
                        continue
                        
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Error fetching from r/{subreddit_name}: {e}")
                continue
    
    def get_source_name(self) -> str:
        return "Reddit API"
```

**Update monolith**:
```python
# In dlt_trust_pipeline.py
from core.fetchers.reddit_api_fetcher import RedditAPIFetcher

fetcher = RedditAPIFetcher(reddit_client, config={'validate_activity': True})
submissions = fetcher.fetch(limit=50, subreddits=['fitness', 'productivity'])
```

---

### Task 4: Create Tests (1 day)

```python
# tests/test_database_fetcher.py
import pytest
from unittest.mock import MagicMock, Mock
from core.fetchers.database_fetcher import DatabaseFetcher

@pytest.fixture
def mock_supabase():
    client = MagicMock()
    client.table.return_value.select.return_value.in_.return_value\
        .gte.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {
            'submission_id': 'test1',
            'title': 'Test',
            'content': 'Content',
            'subreddit': 'test',
            'score': 10
        }
    ]
    return client

def test_database_fetcher_fetch(mock_supabase):
    fetcher = DatabaseFetcher(mock_supabase)
    submissions = list(fetcher.fetch(limit=10))
    
    assert len(submissions) > 0
    assert fetcher.get_source_name() == "Database (submission)"
    assert fetcher.stats['fetched'] > 0

# tests/test_reddit_api_fetcher.py
# Similar pattern...
```

---

## Validation Checklist

### Implementation Validation
- [ ] `DatabaseFetcher` returns standardized format
- [ ] `RedditAPIFetcher` returns identical format
- [ ] Both implement `BaseFetcher` interface
- [ ] Statistics tracking works correctly

### Integration Validation  
- [ ] batch_opportunity_scoring.py uses `DatabaseFetcher`
- [ ] dlt_trust_pipeline.py uses `RedditAPIFetcher`
- [ ] Both monoliths still functional
- [ ] Data format consistent between sources

### Testing Validation
- [ ] Unit tests for both fetchers: `pytest tests/test_*_fetcher.py -v`
- [ ] Coverage >90%: `pytest tests/test_*_fetcher.py --cov=core.fetchers`
- [ ] Integration tests with real clients (optional)

---

## Rollback Procedure

```bash
# Remove fetcher implementations
rm core/fetchers/database_fetcher.py
rm core/fetchers/reddit_api_fetcher.py

# Restore original monolith logic
git checkout HEAD -- scripts/core/batch_opportunity_scoring.py
git checkout HEAD -- scripts/dlt/dlt_trust_pipeline.py

# Remove tests
rm tests/test_database_fetcher.py
rm tests/test_reddit_api_fetcher.py

# Verify
pytest tests/ -v
```

---

## Next Phase

→ **[Phase 5: Extract Deduplication System](phase-05-extract-deduplication.md)**

**Status**: ⏸️ NOT STARTED  
**Last Updated**: 2025-11-19
