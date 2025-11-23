# Storage Layer

Data persistence layer for RedditHarbor opportunities, profiles, and DLT loading operations.

## Overview

This package provides unified storage services for all data persistence operations in RedditHarbor. It centralizes DLT (Data Load Tool) loading logic, handles automatic deduplication via merge disposition, and manages storage to both main tables and specialized enrichment tables.

Key capabilities:
- Unified interface for PostgreSQL/Supabase data loading
- Automatic merge disposition to prevent duplicates
- Statistics tracking (loaded, failed, skipped records)
- JSONB column type hints for proper PostgreSQL storage
- Batch loading for large datasets
- Trust data preservation during updates

## Modules

| Module | Description |
|--------|-------------|
| `dlt_loader.py` | Core DLT loading infrastructure with pipeline caching, batch loading, and statistics tracking |
| `opportunity_store.py` | Storage service for AI-generated app opportunity profiles to `app_opportunities` table |
| `profile_store.py` | Storage service for enriched Reddit submission profiles to `submissions` table |
| `hybrid_store.py` | Combined storage for submissions processed through both opportunity and trust pipelines |
| `enhanced_hybrid_store.py` | Extended hybrid store that persists to specialized enrichment tables (opportunity_scores, monetization_patterns, market_validations, competitive_landscape) |

## Usage Examples

### Basic DLT Loading

```python
from core.storage import DLTLoader

loader = DLTLoader()

# Load with merge disposition (prevents duplicates)
success = loader.load(
    data=[{"submission_id": "abc123", "title": "My Post"}],
    table_name="submissions",
    write_disposition="merge",
    primary_key="submission_id"
)

# Batch loading for large datasets
results = loader.load_batch(
    data=large_dataset,
    table_name="submissions",
    primary_key="submission_id",
    batch_size=100
)
print(f"Success rate: {results['success_rate'] * 100:.1f}%")

# Get statistics
stats = loader.get_statistics()
print(f"Loaded: {stats['loaded']}, Failed: {stats['failed']}")
```

### Opportunity Storage

```python
from core.storage import OpportunityStore

store = OpportunityStore()

opportunities = [{
    "submission_id": "abc123",
    "problem_description": "Teams waste time on manual tracking",
    "app_concept": "Integrated PM platform",
    "core_functions": ["Time tracking", "Gantt charts"],
    "value_proposition": "Save 10 hours/week",
    "target_user": "Small teams",
    "monetization_model": "Subscription",
    "opportunity_score": 75.0
}]

store.store(opportunities)
```

### Profile Storage

```python
from core.storage import ProfileStore

store = ProfileStore()

profiles = [{
    "submission_id": "xyz789",
    "title": "Looking for feedback on my idea",
    "selftext": "I want to build...",
    "author": "user123",
    "subreddit": "Entrepreneur",
    "trust_score": 85.5,
    "opportunity_score": 72.0
}]

store.store(profiles)
```

### Hybrid Storage (Combined Pipelines)

```python
from core.storage import HybridStore

store = HybridStore()

# Store submissions with both opportunity and profile data
submissions = [{
    "submission_id": "abc123",
    "problem_description": "Teams waste time...",
    "app_concept": "PM platform",
    "opportunity_score": 75.0,
    "title": "Need feedback on my idea",
    "trust_score": 85.5,
    "author": "user123",
    "subreddit": "startups"
}]

store.store(submissions)  # Writes to both app_opportunities and submissions tables
```

### Enhanced Hybrid Storage (Enrichment Tables)

```python
from core.storage.enhanced_hybrid_store import EnhancedHybridStore
from supabase import create_client

client = create_client(url, key)
store = EnhancedHybridStore(supabase_client=client)

# Stores to main tables AND enrichment tables:
# - opportunity_scores
# - monetization_patterns
# - market_validations
# - competitive_landscape
store.store(enriched_submissions)

# Get comprehensive statistics
stats = store.get_enhanced_statistics()
```

## Architecture

```
DLTLoader (base)
    |
    +-- OpportunityStore (app_opportunities table)
    |
    +-- ProfileStore (submissions table)
    |
    +-- HybridStore (both tables)
            |
            +-- EnhancedHybridStore (+ enrichment tables)
```

All stores use `DLTLoader` internally for consistent data loading with:
- Automatic primary key handling via `PK_SUBMISSION_ID`
- JSONB column type hints for fields like `ai_profile`, `dimension_scores`, `trust_badges`
- Merge disposition to prevent duplicate records
- Comprehensive error handling and logging

## Related Modules

- `core/dlt/` - DLT constants and primary key definitions
- `core/pipeline/` - Pipeline orchestration that uses these stores
- `config/settings.py` - Database configuration
