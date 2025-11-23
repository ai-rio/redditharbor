# Core Module Architecture

The `core/` package contains the essential business logic for RedditHarbor's data collection, enrichment, and analysis pipeline.

## Directory Structure

```
core/
├── agents/              # AI agents for specialized tasks
├── deduplication/       # Cost-saving deduplication logic
├── dlt/                 # DLT (Data Load Tool) pipeline components
├── enrichment/          # Data enrichment services
├── fetchers/            # Data fetching from various sources
├── pipeline/            # Unified pipeline orchestration
├── quality_filters/     # Data quality filtering
├── reporting/           # Report generation
├── storage/             # Data persistence layer
├── trust/               # Trust validation system
├── utils/               # Shared utilities
└── *.py                 # Backward-compatibility shims (see Migration section)
```

## Module Descriptions

### `pipeline/` - Unified Pipeline Orchestration
The modern, unified pipeline architecture that replaces legacy monolithic scripts.

```python
from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource

config = PipelineConfig(
    data_source=DataSource.DATABASE,
    limit=100,
    enable_profiler=True,
    enable_opportunity_scoring=True
)
pipeline = OpportunityPipeline(config)
result = pipeline.run()
```

**Key Components:**
- `orchestrator.py` - Main pipeline orchestrator
- `factory.py` - Service factory with dependency injection
- `config.py` - Pipeline configuration dataclasses
- `templates.py` - Research project templates

### `enrichment/` - Data Enrichment Services
AI-powered services that add value to raw Reddit data.

```python
from core.enrichment.activity_validation import calculate_activity_score
from core.enrichment.lead_extractor import LeadExtractor
```

**Key Components:**
- `activity_validation.py` - Subreddit activity scoring
- `lead_extractor.py` - Sales lead extraction from posts
- `profiler_service.py` - AI profiling service
- `opportunity_service.py` - Opportunity scoring service
- `trust_service.py` - Trust validation service
- `monetization_service.py` - Monetization analysis

### `fetchers/` - Data Fetching
Components for retrieving data from various sources.

```python
from core.fetchers.collection import PROBLEM_KEYWORDS, TARGET_SUBREDDITS
from core.fetchers.database_fetcher import DatabaseFetcher
from core.fetchers.reddit_api_fetcher import RedditAPIFetcher
```

**Key Components:**
- `collection.py` - Reddit data collection with keyword configs
- `database_fetcher.py` - Fetch from Supabase database
- `reddit_api_fetcher.py` - Fetch from Reddit API
- `base_fetcher.py` - Abstract base class

### `dlt/` - DLT Pipeline Components
Data Load Tool integration for ETL operations.

```python
from core.dlt.reddit_source import reddit_activity_aware
from core.dlt.collection import collect_problem_posts
from core.dlt import PK_SUBMISSION_ID, PK_OPPORTUNITY_ID
```

**Key Components:**
- `reddit_source.py` - Reddit DLT source with activity validation
- `collection.py` - DLT-powered data collection
- `cost_tracking.py` - LLM cost tracking integration
- `app_opportunities.py` - App opportunity resource
- `constants.py` - Primary key constants and utilities

### `storage/` - Data Persistence
Storage services for persisting enriched data.

```python
from core.storage import OpportunityStore, HybridStore, ProfileStore
```

### `trust/` - Trust Validation
System for validating trust signals in opportunities.

```python
from core.trust import TrustValidationService, TrustLevel
```

### `deduplication/` - Cost Optimization
Prevents redundant AI analyses on semantically similar content.

```python
from core.deduplication import AgnoSkipLogic, ProfilerSkipLogic
```

**Key Components:**
- `agno_skip_logic.py` - Monetization analysis deduplication
- `profiler_skip_logic.py` - AI profiler deduplication
- `simple_deduplicator.py` - String-based fingerprint deduplication
- `concept_manager.py` - Business concept management

### `utils/` - Shared Utilities
Common utilities used across modules.

```python
from core.utils import get_logger, setup_logging
from core.utils.http_client_config import initialize_http_clients
```

**Key Components:**
- `http_client_config.py` - HTTP client configuration for LLM libraries
- `cost_tracking_error_handler.py` - Cost tracking error handling
- `logging.py` - Logging utilities
- `core_functions_serialization.py` - Serialization helpers

## Backward Compatibility

The `.py` files at `core/` root level are **backward-compatibility shims**. They re-export from the new canonical locations:

| Old Import | New Canonical Import |
|------------|---------------------|
| `from core.activity_validation import ...` | `from core.enrichment.activity_validation import ...` |
| `from core.lead_extractor import ...` | `from core.enrichment.lead_extractor import ...` |
| `from core.collection import ...` | `from core.fetchers.collection import ...` |
| `from core.templates import ...` | `from core.pipeline.templates import ...` |
| `from core.dlt_reddit_source import ...` | `from core.dlt.reddit_source import ...` |
| `from core.dlt_collection import ...` | `from core.dlt.collection import ...` |
| `from core.dlt_cost_tracking import ...` | `from core.dlt.cost_tracking import ...` |
| `from core.dlt_app_opportunities import ...` | `from core.dlt.app_opportunities import ...` |
| `from core.http_client_config import ...` | `from core.utils.http_client_config import ...` |
| `from core.cost_tracking_error_handler import ...` | `from core.utils.cost_tracking_error_handler import ...` |
| `from core.trust_layer import ...` | `from core.trust import ...` |

**Note:** New code should use the canonical imports. The shims will be removed in a future version.

## Architecture Principles

1. **Single Responsibility**: Each subdirectory handles one concern
2. **Dependency Direction**: `pipeline` → `enrichment` → `fetchers` → `storage`
3. **No Circular Imports**: Lower-level modules don't import from higher-level ones
4. **Backward Compatibility**: Shims ensure existing code continues to work

## Adding New Components

1. Identify the appropriate subdirectory based on responsibility
2. Create the module in that subdirectory
3. Export public APIs in the subdirectory's `__init__.py`
4. Add tests in `tests/`
5. Update this README if adding a new category
