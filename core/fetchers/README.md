# Data Fetchers

Data acquisition layer with pluggable data sources.

## Modules

- `base_fetcher.py` - Abstract base class (BaseFetcher)
- `database_fetcher.py` - Supabase implementation (🚧 Phase 4)
- `reddit_api_fetcher.py` - Reddit API implementation (🚧 Phase 4)
- `formatters.py` - Data formatting utilities (🚧 Phase 4)

## Usage

```python
from core.fetchers.base_fetcher import BaseFetcher

# Implementations will fetch from database or Reddit API
# Standardized interface for all data sources
```

## Status

🚧 **Phase 1: Foundation** - Base class defined

**Next**: Phase 4 - Extract Data Fetching

See: [Refactoring Plan](../../docs/plans/unified-pipeline-refactoring/README.md)
