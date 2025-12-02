# Pipeline Orchestration

The unified pipeline orchestration system for RedditHarbor opportunity discovery.

## Overview

This module provides the core orchestration framework that coordinates:
- Data fetching from multiple sources (Database, Reddit API)
- AI enrichment services (profiling, opportunity scoring, trust validation)
- Cost-saving deduplication
- Persistent storage

## Modules

| Module | Description |
|--------|-------------|
| `orchestrator.py` | `OpportunityPipeline` - Main pipeline orchestrator |
| `factory.py` | `ServiceFactory` - Dependency injection and service lifecycle |
| `config.py` | `PipelineConfig`, `DataSource`, `ServiceType` - Configuration |
| `templates.py` | Research project templates and configurations |

## Usage

```python
from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource

# Configure pipeline
config = PipelineConfig(
    data_source=DataSource.DATABASE,
    limit=100,
    enable_profiler=True,
    enable_opportunity_scoring=True,
    enable_trust=True,
    enable_deduplication=True
)

# Run pipeline
pipeline = OpportunityPipeline(config)
result = pipeline.run()

print(f"Processed {result['stats']['analyzed']} submissions")
print(f"Stored {result['stats']['stored']} opportunities")
```

## Configuration Options

```python
@dataclass
class PipelineConfig:
    # Data Source
    data_source: DataSource          # DATABASE or REDDIT_API
    limit: int = 100                 # Max submissions to process

    # Service Toggles
    enable_profiler: bool = False    # AI profiling service
    enable_opportunity_scoring: bool = False
    enable_trust: bool = False       # Trust validation
    enable_market_validation: bool = False
    enable_deduplication: bool = True

    # Quality Filtering
    enable_quality_filter: bool = True
    min_score: int = 1
    min_comments: int = 0

    # Storage
    dry_run: bool = False            # Skip storage if True
    return_data: bool = False        # Return processed data
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OpportunityPipeline                       │
├─────────────────────────────────────────────────────────────┤
│  Config ──► Fetcher ──► Quality Filter ──► Enrichment ──► Storage
│                              │                   │
│                              ▼                   ▼
│                        (optional)          ServiceFactory
│                                            ├── ProfilerService
│                                            ├── OpportunityService
│                                            ├── TrustService
│                                            └── MonetizationService
└─────────────────────────────────────────────────────────────┘
```

## Research Templates

Pre-configured templates for common research workflows:

```python
from core.pipeline.templates import PROJECT_CONFIGS, run_project

# Available templates
PROJECT_CONFIGS.keys()
# - tech_research
# - ai_ml_monitoring
# - startup_analysis
# - health_fitness_opportunities
# - finance_opportunities
# - education_career_opportunities
# - travel_opportunities
# - real_estate_opportunities
# - productivity_saas_opportunities
# ...

# Run a template
run_project("health_fitness_opportunities", pipeline)
```

## Integration

This module replaced the legacy monolithic scripts:
- `batch_opportunity_scoring.py` (2,830 lines) → `orchestrator.py`
- `dlt_trust_pipeline.py` (774 lines) → Integrated into pipeline

## Related Modules

- `core/enrichment/` - AI enrichment services used by the pipeline
- `core/fetchers/` - Data fetchers for different sources
- `core/storage/` - Storage backends for persisting results
- `core/deduplication/` - Cost-saving deduplication logic
