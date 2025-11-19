# Pipeline Orchestration

This module contains the unified pipeline orchestration logic for RedditHarbor.

## Overview

The pipeline module provides the core orchestration framework that coordinates data fetching, AI enrichment, deduplication, and storage operations.

## Modules

- `orchestrator.py` - OpportunityPipeline class (main entry point)
- `config.py` - Pipeline configuration management (PipelineConfig, DataSource, ServiceType)
- `factory.py` - Dependency injection and service factory

## Usage

```python
from core.pipeline.config import PipelineConfig, DataSource
from core.pipeline.orchestrator import OpportunityPipeline

# Configure pipeline
config = PipelineConfig(
    data_source=DataSource.DATABASE,
    limit=100,
    enable_profiler=True,
    enable_deduplication=True
)

# Run pipeline (future implementation)
# pipeline = OpportunityPipeline(config)
# results = pipeline.run()
```

## Status

🚧 **Phase 1: Foundation** - Structure created, base classes defined

See: [Unified Pipeline Refactoring Plan](../../docs/plans/unified-pipeline-refactoring/README.md)

## Architecture

Part of the unified modular architecture that replaces:
- `batch_opportunity_scoring.py` (2,830 lines)
- `dlt_trust_pipeline.py` (774 lines)

**Next Phase**: Phase 2 - Agent Tools Restructuring
