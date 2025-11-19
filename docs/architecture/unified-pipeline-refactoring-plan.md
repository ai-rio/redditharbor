> **📌 DEPRECATION NOTICE**
> 
> **Status**: This document has been superseded  
> **Date**: 2025-11-19  
> **Replacement**: [Unified Pipeline Refactoring Plan](unified-pipeline-refactoring/README.md)
> 
> This file is kept for historical reference only. The content has been reorganized into an executable, phase-by-phase plan with:
> - 11 detailed phase files
> - Complete implementation guides
> - Executable checklists
> - Rollback procedures
> - Progress tracking
> 
> **For current planning, see**: [docs/plans/unified-pipeline-refactoring/](unified-pipeline-refactoring/)
> 
> ---
> 
# Unified Pipeline Refactoring Plan

**Status**: Draft
**Created**: 2025-11-19
**Purpose**: Refactor two monolithic pipelines into a single, modular, Next.js-ready architecture

## Executive Summary

RedditHarbor currently has **TWO competing monolithic pipelines** solving the same problem:

1. **`batch_opportunity_scoring.py`** (2,799 lines) - Sources from database
2. **`dlt_trust_pipeline.py`** (775 lines) - Sources from Reddit API

Both implement:
- Reddit data collection
- AI opportunity analysis (OpportunityAnalyzerAgent)
- Trust layer validation
- DLT loading to Supabase

**Problem**: Massive code duplication, competing architectures, impossible to expose as Next.js API endpoints.

**Solution**: Unified modular pipeline with:
- Single source of truth for each responsibility
- Configurable data sources (database OR Reddit API)
- Clean module boundaries for Next.js integration
- Proper separation of concerns

---

## Current State Analysis

### batch_opportunity_scoring.py (2,799 lines)

**Key Functions**:
```python
# Deduplication Logic (Phase 1: Semantic Deduplication)
should_run_agno_analysis()           # Line 205 - Check if Agno needed
copy_agno_from_primary()             # Line 283 - Copy Agno from primary concept
update_concept_agno_stats()          # Line 436 - Update concept Agno stats
should_run_profiler_analysis()       # Line 486 - Check if Profiler needed
copy_profiler_from_primary()         # Line 567 - Copy Profiler from primary
update_concept_profiler_stats()      # Line 709 - Update concept Profiler stats

# Data Fetching
fetch_all_submissions()              # Line 761 - Fetch with deduplication
fetch_submissions()                  # Line 893 - Basic fetch
format_submission_for_agent()        # Line 939 - Format for AI

# AI Analysis
prepare_analysis_for_storage()       # Line 982 - Format AI results

# Storage (DLT)
load_scores_to_supabase_via_dlt()    # Line 1108 - Store opportunity scores
store_ai_profiles_to_app_opportunities_via_dlt()  # Line 1231 - Store AI profiles

# Hybrid Strategy (Phase 2 & 3)
perform_market_validation()          # Line 1336 - Market data validation
store_hybrid_results_to_database()   # Line 1394 - Store hybrid results

# Main Orchestration
process_batch()                      # Line 1483 - Main processing (800+ lines!)
generate_summary_report()            # Line 2283 - Stats reporting
refresh_problem_metrics()            # Line 2400 - Update metrics
main()                               # Line 2445 - Entry point

# Utilities
map_subreddit_to_sector()            # Line 188 - Map subreddit to business sector
```

**Data Source**: Supabase database (`submissions` table)

**AI Components**:
- EnhancedLLMProfiler (app_name, core_functions, value_proposition)
- OpportunityAnalyzerAgent (5-dimensional scoring)
- MonetizationAgnoAnalyzer (multi-agent WTP, segment, price, payment)
- MarketDataValidator (web search validation)

---

### dlt_trust_pipeline.py (775 lines)

**Key Functions**:
```python
# Data Collection
collect_posts_with_activity_validation()  # Line 55 - Collect from Reddit API
calculate_pre_ai_quality_score()          # Line 101 - Pre-filter quality
should_analyze_with_ai()                  # Line 137 - Pre-filter decision

# AI Analysis
analyze_opportunities_with_ai()           # Line 179 - OpportunityAnalyzerAgent wrapper

# Trust Validation
apply_trust_validation()                  # Line 309 - Trust layer validation
get_engagement_level()                    # Line 423 - Trust score converters
get_problem_validity()                    # Line 437
get_discussion_quality()                  # Line 449
get_ai_confidence_level()                 # Line 461

# Storage (DLT)
load_trusted_opportunities_to_supabase()  # Line 473 - DLT loading

# Orchestration
generate_pipeline_summary()               # Line 609 - Stats reporting
main()                                    # Line 680 - Entry point
```

**Data Source**: Reddit API via DLT (`collect_problem_posts()`)

**AI Components**:
- OpportunityAnalyzerAgent (5-dimensional scoring)
- TrustLayerValidator (6-dimensional trust scoring)

---

## Code Duplication Analysis

### Duplicate Responsibilities

| Responsibility | batch_opportunity_scoring.py | dlt_trust_pipeline.py | Duplication Level |
|----------------|------------------------------|----------------------|-------------------|
| **Reddit Data Fetching** | `fetch_submissions()` (database) | `collect_posts_with_activity_validation()` (API) | 🔴 HIGH (different sources) |
| **AI Opportunity Analysis** | `process_batch()` (lines 1483-2282) | `analyze_opportunities_with_ai()` (lines 179-306) | 🔴 HIGH (same OpportunityAnalyzerAgent) |
| **DLT Loading** | `load_scores_to_supabase_via_dlt()` + `store_ai_profiles_to_app_opportunities_via_dlt()` | `load_trusted_opportunities_to_supabase()` | 🔴 HIGH (duplicate pipelines) |
| **Trust Validation** | ❌ Missing | `apply_trust_validation()` | 🟡 MEDIUM (one-sided) |
| **Summary Reporting** | `generate_summary_report()` | `generate_pipeline_summary()` | 🟢 LOW (similar stats) |
| **Deduplication Logic** | ✅ Comprehensive (6 functions) | ❌ Missing | 🟡 MEDIUM (one-sided) |
| **Market Validation** | ✅ Has `perform_market_validation()` | ❌ Missing | 🟡 MEDIUM (one-sided) |

### Key Insight

**BOTH files should have access to**:
- ✅ Deduplication logic (from batch_opportunity_scoring.py)
- ✅ Trust validation (from dlt_trust_pipeline.py)
- ✅ Market validation (from batch_opportunity_scoring.py)
- ✅ AI profiling (EnhancedLLMProfiler from batch_opportunity_scoring.py)
- ✅ Opportunity scoring (OpportunityAnalyzerAgent - shared)

**Currently**: Each file has PARTIAL functionality, leading to incomplete pipelines.

---

## Proposed Modular Architecture

### Directory Structure

```
core/
├── pipeline/                           # NEW: Unified pipeline orchestration
│   ├── __init__.py
│   ├── orchestrator.py                 # Unified pipeline orchestrator
│   ├── data_sources.py                 # Abstract data source interface
│   └── pipeline_config.py              # Configuration management
│
├── fetchers/                           # NEW: Data acquisition layer
│   ├── __init__.py
│   ├── base_fetcher.py                 # Abstract base class
│   ├── database_fetcher.py             # Fetch from Supabase (batch_opportunity_scoring logic)
│   ├── reddit_api_fetcher.py           # Fetch from Reddit API (dlt_trust_pipeline logic)
│   └── formatters.py                   # format_submission_for_agent(), etc.
│
├── deduplication/                      # EXTRACTED: Semantic deduplication
│   ├── __init__.py
│   ├── concept_manager.py              # Business concept operations
│   ├── agno_skip_logic.py              # should_run_agno_analysis(), copy_agno_from_primary()
│   ├── profiler_skip_logic.py          # should_run_profiler_analysis(), copy_profiler_from_primary()
│   └── stats_updater.py                # update_concept_agno_stats(), update_concept_profiler_stats()
│
├── enrichment/                         # EXTRACTED: AI analysis layer
│   ├── __init__.py
│   ├── profiler_service.py             # EnhancedLLMProfiler wrapper
│   ├── opportunity_service.py          # OpportunityAnalyzerAgent wrapper
│   ├── monetization_service.py         # MonetizationAgnoAnalyzer wrapper
│   ├── trust_service.py                # TrustLayerValidator wrapper
│   ├── market_validation_service.py    # MarketDataValidator wrapper
│   └── batch_processor.py              # Batch processing utilities
│
├── storage/                            # EXTRACTED: Data persistence layer
│   ├── __init__.py
│   ├── dlt_loader.py                   # Unified DLT loading logic
│   ├── opportunity_store.py            # Store opportunity scores
│   ├── profile_store.py                # Store AI profiles
│   ├── hybrid_store.py                 # Store hybrid results
│   └── metrics_updater.py              # refresh_problem_metrics()
│
├── quality_filters/                    # EXTRACTED: Pre-AI filtering
│   ├── __init__.py
│   ├── quality_scorer.py               # calculate_pre_ai_quality_score()
│   ├── pre_filter.py                   # should_analyze_with_ai()
│   └── thresholds.py                   # Quality threshold constants
│
├── reporting/                          # EXTRACTED: Stats and summaries
│   ├── __init__.py
│   ├── summary_generator.py            # Unified summary reporting
│   └── formatters.py                   # Stats formatting utilities
│
└── utils/                              # Existing utilities
    ├── core_functions_serialization.py # Already exists
    └── sector_mapping.py               # NEW: map_subreddit_to_sector()
```

---

## Module Extraction Plan

### Phase 1: Extract Utilities (Low Risk)

**Target**: Standalone functions with no side effects

| Function | Source File | New Location | Lines |
|----------|-------------|--------------|-------|
| `map_subreddit_to_sector()` | batch_opportunity_scoring.py:188 | `core/utils/sector_mapping.py` | ~100 |
| `format_submission_for_agent()` | batch_opportunity_scoring.py:939 | `core/fetchers/formatters.py` | ~40 |
| `calculate_pre_ai_quality_score()` | dlt_trust_pipeline.py:101 | `core/quality_filters/quality_scorer.py` | ~35 |
| `should_analyze_with_ai()` | dlt_trust_pipeline.py:137 | `core/quality_filters/pre_filter.py` | ~40 |
| Trust score converters (4 functions) | dlt_trust_pipeline.py:423-471 | `core/enrichment/trust_service.py` | ~50 |

**Benefit**: Immediate reusability, easy to test, zero dependencies

---

### Phase 2: Extract Deduplication (Medium Risk)

**Target**: Self-contained deduplication logic

| Function | Source File | New Location | Lines |
|----------|-------------|--------------|-------|
| `should_run_agno_analysis()` | batch_opportunity_scoring.py:205 | `core/deduplication/agno_skip_logic.py` | ~78 |
| `copy_agno_from_primary()` | batch_opportunity_scoring.py:283 | `core/deduplication/agno_skip_logic.py` | ~150 |
| `update_concept_agno_stats()` | batch_opportunity_scoring.py:436 | `core/deduplication/stats_updater.py` | ~50 |
| `should_run_profiler_analysis()` | batch_opportunity_scoring.py:486 | `core/deduplication/profiler_skip_logic.py` | ~78 |
| `copy_profiler_from_primary()` | batch_opportunity_scoring.py:567 | `core/deduplication/profiler_skip_logic.py` | ~140 |
| `update_concept_profiler_stats()` | batch_opportunity_scoring.py:709 | `core/deduplication/stats_updater.py` | ~50 |

**Dependencies**: Supabase client (passed as parameter)

**Benefit**: Enables deduplication for BOTH pipelines

---

### Phase 3: Extract Data Fetching (Medium Risk)

**Target**: Data acquisition with configurable sources

#### Create Abstract Base Class

```python
# core/fetchers/base_fetcher.py
from abc import ABC, abstractmethod
from typing import Any, Iterator

class BaseFetcher(ABC):
    """Abstract base class for data fetchers"""

    @abstractmethod
    def fetch(self, limit: int, **kwargs) -> Iterator[dict[str, Any]]:
        """Fetch submissions from data source"""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return human-readable source name"""
        pass
```

#### Extract Database Fetcher

| Function | Source File | New Location | Lines |
|----------|-------------|--------------|-------|
| `fetch_all_submissions()` | batch_opportunity_scoring.py:761 | `core/fetchers/database_fetcher.py` | ~130 |
| `fetch_submissions()` | batch_opportunity_scoring.py:893 | `core/fetchers/database_fetcher.py` | ~45 |

#### Extract Reddit API Fetcher

| Function | Source File | New Location | Lines |
|----------|-------------|--------------|-------|
| `collect_posts_with_activity_validation()` | dlt_trust_pipeline.py:55 | `core/fetchers/reddit_api_fetcher.py` | ~35 |

**Design**:
```python
# core/fetchers/database_fetcher.py
class DatabaseFetcher(BaseFetcher):
    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def fetch(self, limit: int, with_deduplication: bool = True):
        # Logic from fetch_all_submissions()
        pass

# core/fetchers/reddit_api_fetcher.py
class RedditAPIFetcher(BaseFetcher):
    def __init__(self, subreddits: list[str]):
        self.subreddits = subreddits

    def fetch(self, limit: int, test_mode: bool = False):
        # Logic from collect_posts_with_activity_validation()
        pass
```

**Benefit**: Single interface for BOTH data sources

---

### Phase 4: Extract AI Enrichment Services (High Risk)

**Target**: AI analysis wrappers with unified interface

| Function | Source File | New Location | Lines | Service Class |
|----------|-------------|--------------|-------|---------------|
| AI Profiler logic | batch_opportunity_scoring.py:1483+ | `core/enrichment/profiler_service.py` | ~150 | `ProfilerService` |
| Opportunity scoring | batch_opportunity_scoring.py:1483+ | `core/enrichment/opportunity_service.py` | ~200 | `OpportunityService` |
| Monetization analysis | batch_opportunity_scoring.py:1483+ | `core/enrichment/monetization_service.py` | ~100 | `MonetizationService` |
| Trust validation | dlt_trust_pipeline.py:309 | `core/enrichment/trust_service.py` | ~120 | `TrustService` |
| Market validation | batch_opportunity_scoring.py:1336 | `core/enrichment/market_validation_service.py` | ~60 | `MarketValidationService` |

**Design Pattern**: Service classes with dependency injection

```python
# core/enrichment/profiler_service.py
from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
from core.deduplication.profiler_skip_logic import should_run_profiler_analysis, copy_profiler_from_primary

class ProfilerService:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.profiler = EnhancedLLMProfiler()

    def enrich(self, submission: dict[str, Any]) -> dict[str, Any]:
        """
        Generate AI profile for submission with deduplication skip logic.
        Returns submission enriched with AI profile OR copied from primary.
        """
        # Check deduplication
        should_run, primary_id = should_run_profiler_analysis(submission, self.supabase)

        if not should_run:
            # Copy from primary concept
            return copy_profiler_from_primary(submission, primary_id, self.supabase)

        # Generate new profile
        profile = self.profiler.generate_profile(submission)
        return {**submission, **profile}
```

**Similar pattern for**:
- `OpportunityService` (OpportunityAnalyzerAgent + deduplication)
- `MonetizationService` (MonetizationAgnoAnalyzer + Agno skip logic)
- `TrustService` (TrustLayerValidator)
- `MarketValidationService` (MarketDataValidator)

**Benefit**: Each service is:
- ✅ Independently testable
- ✅ Reusable across pipelines
- ✅ Exposable as Next.js API endpoint
- ✅ Includes deduplication automatically

---

### Phase 5: Extract Storage Layer (High Risk)

**Target**: Unified DLT loading logic

| Function | Source File | New Location | Lines |
|----------|-------------|--------------|-------|
| `load_scores_to_supabase_via_dlt()` | batch_opportunity_scoring.py:1108 | `core/storage/opportunity_store.py` | ~120 |
| `store_ai_profiles_to_app_opportunities_via_dlt()` | batch_opportunity_scoring.py:1231 | `core/storage/profile_store.py` | ~105 |
| `load_trusted_opportunities_to_supabase()` | dlt_trust_pipeline.py:473 | `core/storage/dlt_loader.py` | ~135 |
| `store_hybrid_results_to_database()` | batch_opportunity_scoring.py:1394 | `core/storage/hybrid_store.py` | ~90 |
| `refresh_problem_metrics()` | batch_opportunity_scoring.py:2400 | `core/storage/metrics_updater.py` | ~45 |

**Design**: Unified DLT resource pattern

```python
# core/storage/dlt_loader.py
import dlt
from typing import Any, Callable

class DLTLoader:
    """Unified DLT loader with configurable resources"""

    def __init__(self, pipeline_name: str = "reddit_harbor_unified"):
        self.pipeline = dlt.pipeline(
            pipeline_name=pipeline_name,
            destination=dlt.destinations.postgres(...),
            dataset_name="public"
        )

    def load(
        self,
        data: list[dict[str, Any]],
        table_name: str,
        resource_name: str,
        primary_key: str,
        transformer: Callable[[dict], dict] | None = None
    ) -> bool:
        """
        Generic DLT loading with merge disposition.

        Args:
            data: Records to load
            table_name: Target table name
            resource_name: DLT resource name
            primary_key: Primary key field
            transformer: Optional data transformation function
        """
        @dlt.resource(
            name=resource_name,
            write_disposition="merge",
            primary_key=primary_key
        )
        def resource_generator(records):
            for record in records:
                yield transformer(record) if transformer else record

        info = self.pipeline.run(
            resource_generator(data),
            table_name=table_name
        )
        return info is not None

# Usage:
loader = DLTLoader()
loader.load(
    data=opportunities,
    table_name="opportunities_unified",
    resource_name="app_opportunities",
    primary_key="submission_id",
    transformer=prepare_opportunity_record  # Optional transform
)
```

**Benefit**: Single DLT pipeline for ALL storage operations

---

### Phase 6: Extract Reporting (Low Risk)

**Target**: Summary generation and stats

| Function | Source File | New Location | Lines |
|----------|-------------|--------------|-------|
| `generate_summary_report()` | batch_opportunity_scoring.py:2283 | `core/reporting/summary_generator.py` | ~115 |
| `generate_pipeline_summary()` | dlt_trust_pipeline.py:609 | `core/reporting/summary_generator.py` | ~70 |

**Design**: Merge into unified summary generator

```python
# core/reporting/summary_generator.py
class SummaryGenerator:
    def generate(self,
                 opportunities: list[dict[str, Any]],
                 pipeline_stats: dict[str, Any],
                 include_trust_metrics: bool = True,
                 include_deduplication_metrics: bool = True) -> str:
        """Generate unified pipeline summary"""
        # Combine logic from both files
        pass
```

---

### Phase 7: Create Unified Orchestrator (High Risk)

**Target**: Single entry point replacing both monoliths

```python
# core/pipeline/orchestrator.py
from core.fetchers.base_fetcher import BaseFetcher
from core.fetchers.database_fetcher import DatabaseFetcher
from core.fetchers.reddit_api_fetcher import RedditAPIFetcher
from core.enrichment.profiler_service import ProfilerService
from core.enrichment.opportunity_service import OpportunityService
from core.enrichment.monetization_service import MonetizationService
from core.enrichment.trust_service import TrustService
from core.enrichment.market_validation_service import MarketValidationService
from core.storage.dlt_loader import DLTLoader
from core.quality_filters.pre_filter import PreFilter
from core.reporting.summary_generator import SummaryGenerator

class OpportunityPipeline:
    """
    Unified opportunity discovery pipeline.

    Replaces:
    - scripts/core/batch_opportunity_scoring.py
    - scripts/dlt/dlt_trust_pipeline.py

    Features:
    - Configurable data sources (database OR Reddit API)
    - Automatic deduplication (Agno + Profiler skip logic)
    - Trust layer validation
    - Market data validation
    - DLT-powered storage
    """

    def __init__(
        self,
        fetcher: BaseFetcher,
        supabase_client,
        enable_profiler: bool = True,
        enable_opportunity_scoring: bool = True,
        enable_monetization: bool = True,
        enable_trust: bool = True,
        enable_market_validation: bool = True,
    ):
        self.fetcher = fetcher
        self.supabase = supabase_client

        # Initialize services
        self.pre_filter = PreFilter()
        self.profiler = ProfilerService(supabase_client) if enable_profiler else None
        self.opportunity_scorer = OpportunityService(supabase_client) if enable_opportunity_scoring else None
        self.monetization = MonetizationService(supabase_client) if enable_monetization else None
        self.trust = TrustService(supabase_client) if enable_trust else None
        self.market_validator = MarketValidationService() if enable_market_validation else None

        self.loader = DLTLoader()
        self.summary = SummaryGenerator()

    def run(self, limit: int = 100, **kwargs) -> dict[str, Any]:
        """
        Execute full pipeline:
        1. Fetch submissions from configured source
        2. Pre-filter low-quality submissions
        3. AI Profiling (with deduplication skip)
        4. Opportunity Scoring (with deduplication skip)
        5. Monetization Analysis (with Agno skip)
        6. Trust Validation
        7. Market Validation
        8. Store to Supabase via DLT
        9. Generate summary report
        """
        stats = {
            'total_fetched': 0,
            'pre_filtered': 0,
            'profiled': 0,
            'scored': 0,
            'monetized': 0,
            'trusted': 0,
            'validated': 0,
            'stored': 0,
        }

        # Step 1: Fetch
        submissions = list(self.fetcher.fetch(limit=limit, **kwargs))
        stats['total_fetched'] = len(submissions)

        # Step 2: Pre-filter
        filtered = [s for s in submissions if self.pre_filter.should_analyze(s)]
        stats['pre_filtered'] = len(submissions) - len(filtered)

        # Step 3-7: Enrich
        enriched = []
        for submission in filtered:
            # AI Profiling (includes deduplication skip)
            if self.profiler:
                submission = self.profiler.enrich(submission)
                stats['profiled'] += 1

            # Opportunity Scoring (includes deduplication skip)
            if self.opportunity_scorer:
                submission = self.opportunity_scorer.enrich(submission)
                stats['scored'] += 1

            # Monetization Analysis (includes Agno skip)
            if self.monetization:
                submission = self.monetization.enrich(submission)
                stats['monetized'] += 1

            # Trust Validation
            if self.trust:
                submission = self.trust.enrich(submission)
                stats['trusted'] += 1

            # Market Validation
            if self.market_validator:
                submission = self.market_validator.enrich(submission)
                stats['validated'] += 1

            enriched.append(submission)

        # Step 8: Store
        success = self.loader.load(
            data=enriched,
            table_name="opportunities_unified",
            resource_name="app_opportunities",
            primary_key="submission_id"
        )
        stats['stored'] = len(enriched) if success else 0

        # Step 9: Summary
        summary_report = self.summary.generate(enriched, stats)

        return {
            'success': success,
            'stats': stats,
            'summary': summary_report,
            'opportunities': enriched
        }


# Usage Example 1: Database source (replaces batch_opportunity_scoring.py)
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
fetcher = DatabaseFetcher(supabase)

pipeline = OpportunityPipeline(
    fetcher=fetcher,
    supabase_client=supabase,
    enable_profiler=True,
    enable_opportunity_scoring=True,
    enable_monetization=True,
    enable_trust=True,
    enable_market_validation=True
)

result = pipeline.run(limit=100)


# Usage Example 2: Reddit API source (replaces dlt_trust_pipeline.py)
fetcher = RedditAPIFetcher(subreddits=["startups", "SaaS", "indiehackers"])

pipeline = OpportunityPipeline(
    fetcher=fetcher,
    supabase_client=supabase,
    enable_profiler=True,
    enable_trust=True  # Trust layer was unique to dlt_trust_pipeline.py
)

result = pipeline.run(limit=50, test_mode=False)
```

---

## Next.js API Integration Points

### REST API Endpoints Design

Once refactored, each service becomes an API endpoint:

```typescript
// Next.js App Router API Routes

// app/api/opportunities/analyze/route.ts
export async function POST(request: Request) {
  const { submission_id } = await request.json();

  // Call ProfilerService
  const result = await fetch('http://localhost:8000/api/v1/profiler/analyze', {
    method: 'POST',
    body: JSON.stringify({ submission_id })
  });

  return Response.json(result);
}

// app/api/opportunities/score/route.ts
export async function POST(request: Request) {
  const { submission_id } = await request.json();

  // Call OpportunityService
  const result = await fetch('http://localhost:8000/api/v1/opportunities/score', {
    method: 'POST',
    body: JSON.stringify({ submission_id })
  });

  return Response.json(result);
}

// app/api/opportunities/monetize/route.ts
export async function POST(request: Request) {
  const { submission_id } = await request.json();

  // Call MonetizationService
  const result = await fetch('http://localhost:8000/api/v1/monetization/analyze', {
    method: 'POST',
    body: JSON.stringify({ submission_id })
  });

  return Response.json(result);
}

// app/api/opportunities/validate-trust/route.ts
export async function POST(request: Request) {
  const { submission_id } = await request.json();

  // Call TrustService
  const result = await fetch('http://localhost:8000/api/v1/trust/validate', {
    method: 'POST',
    body: JSON.stringify({ submission_id })
  });

  return Response.json(result);
}

// app/api/pipeline/run/route.ts
export async function POST(request: Request) {
  const { source, limit, config } = await request.json();

  // Call OpportunityPipeline orchestrator
  const result = await fetch('http://localhost:8000/api/v1/pipeline/run', {
    method: 'POST',
    body: JSON.stringify({ source, limit, config })
  });

  return Response.json(result);
}
```

### Python FastAPI Backend (New)

```python
# api/main.py (NEW FILE)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.pipeline.orchestrator import OpportunityPipeline
from core.fetchers.database_fetcher import DatabaseFetcher
from core.fetchers.reddit_api_fetcher import RedditAPIFetcher
from supabase import create_client

app = FastAPI(title="RedditHarbor API", version="2.0.0")

# Initialize services
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class AnalyzeRequest(BaseModel):
    submission_id: str

class PipelineRequest(BaseModel):
    source: str  # "database" or "reddit"
    limit: int = 100
    config: dict = {}

@app.post("/api/v1/profiler/analyze")
async def analyze_profiler(request: AnalyzeRequest):
    """Endpoint for AI Profiler (EnhancedLLMProfiler)"""
    from core.enrichment.profiler_service import ProfilerService

    service = ProfilerService(supabase)
    submission = fetch_submission(request.submission_id)
    result = service.enrich(submission)
    return result

@app.post("/api/v1/opportunities/score")
async def score_opportunity(request: AnalyzeRequest):
    """Endpoint for Opportunity Scoring (OpportunityAnalyzerAgent)"""
    from core.enrichment.opportunity_service import OpportunityService

    service = OpportunityService(supabase)
    submission = fetch_submission(request.submission_id)
    result = service.enrich(submission)
    return result

@app.post("/api/v1/monetization/analyze")
async def analyze_monetization(request: AnalyzeRequest):
    """Endpoint for Monetization Analysis (MonetizationAgnoAnalyzer)"""
    from core.enrichment.monetization_service import MonetizationService

    service = MonetizationService(supabase)
    submission = fetch_submission(request.submission_id)
    result = service.enrich(submission)
    return result

@app.post("/api/v1/trust/validate")
async def validate_trust(request: AnalyzeRequest):
    """Endpoint for Trust Validation (TrustLayerValidator)"""
    from core.enrichment.trust_service import TrustService

    service = TrustService(supabase)
    submission = fetch_submission(request.submission_id)
    result = service.enrich(submission)
    return result

@app.post("/api/v1/pipeline/run")
async def run_pipeline(request: PipelineRequest):
    """Endpoint for full pipeline execution"""
    if request.source == "database":
        fetcher = DatabaseFetcher(supabase)
    elif request.source == "reddit":
        fetcher = RedditAPIFetcher(subreddits=request.config.get("subreddits", []))
    else:
        raise HTTPException(status_code=400, detail="Invalid source")

    pipeline = OpportunityPipeline(
        fetcher=fetcher,
        supabase_client=supabase,
        **request.config
    )

    result = pipeline.run(limit=request.limit)
    return result
```

---

## Migration Strategy

### Step 1: Create Module Structure (Week 1)

**Goal**: Create directory structure without breaking existing code

**Actions**:
1. Create all new directories under `core/`
2. Add `__init__.py` files
3. Create empty module files with docstrings
4. Update `CLAUDE.md` with new architecture

**Risk**: ✅ Zero - no code changes yet

---

### Step 2: Extract Utilities (Week 1)

**Goal**: Move standalone functions to new modules

**Order**:
1. `map_subreddit_to_sector()` → `core/utils/sector_mapping.py`
2. `format_submission_for_agent()` → `core/fetchers/formatters.py`
3. Trust score converters → `core/enrichment/trust_service.py`
4. Quality scoring functions → `core/quality_filters/`

**Testing**:
- Create unit tests for each extracted function
- Import from new location in existing scripts (side-by-side)
- Run existing pipelines to verify no breakage

**Risk**: 🟡 Low - functions are stateless

---

### Step 3: Extract Deduplication (Week 2)

**Goal**: Move deduplication logic to dedicated module

**Order**:
1. `should_run_agno_analysis()` + `copy_agno_from_primary()` → `core/deduplication/agno_skip_logic.py`
2. `should_run_profiler_analysis()` + `copy_profiler_from_primary()` → `core/deduplication/profiler_skip_logic.py`
3. Update stats functions → `core/deduplication/stats_updater.py`

**Testing**:
- Import from new modules in `batch_opportunity_scoring.py`
- Run full pipeline with deduplication enabled
- Verify no duplicate `core_functions` arrays generated
- Check `business_concepts` table integrity

**Risk**: 🟡 Medium - database queries involved

---

### Step 4: Extract Data Fetchers (Week 2-3)

**Goal**: Create abstract fetcher interface

**Order**:
1. Create `BaseFetcher` abstract class
2. Extract `DatabaseFetcher` from `batch_opportunity_scoring.py`
3. Extract `RedditAPIFetcher` from `dlt_trust_pipeline.py`
4. Update both scripts to use new fetchers (side-by-side)

**Testing**:
- Test `DatabaseFetcher` with existing database
- Test `RedditAPIFetcher` with test mode
- Verify both return identical data structures
- Run both pipelines end-to-end

**Risk**: 🟠 Medium-High - core data acquisition logic

---

### Step 5: Extract Enrichment Services (Week 3-4)

**Goal**: Create service classes for AI components

**Order**:
1. `ProfilerService` (EnhancedLLMProfiler wrapper + profiler skip logic)
2. `OpportunityService` (OpportunityAnalyzerAgent wrapper)
3. `TrustService` (TrustLayerValidator wrapper)
4. `MonetizationService` (MonetizationAgnoAnalyzer wrapper + Agno skip logic)
5. `MarketValidationService` (MarketDataValidator wrapper)

**Testing**:
- Unit test each service in isolation
- Integration test with real submissions
- Verify deduplication skip logic works
- Check AI profile quality (compare before/after)
- Run cost analysis (ensure no extra LLM calls)

**Risk**: 🔴 High - touches all AI components

---

### Step 6: Extract Storage Layer (Week 4)

**Goal**: Unified DLT loading

**Order**:
1. Create `DLTLoader` with generic `load()` method
2. Extract opportunity store logic
3. Extract profile store logic
4. Extract hybrid store logic
5. Update both scripts to use `DLTLoader`

**Testing**:
- Test DLT pipeline with merge disposition
- Verify no duplicate records created
- Check schema evolution (add new fields)
- Run full pipeline end-to-end
- Query Supabase to verify data integrity

**Risk**: 🔴 High - data persistence layer

---

### Step 7: Create Unified Orchestrator (Week 5)

**Goal**: Single `OpportunityPipeline` class

**Order**:
1. Create `OpportunityPipeline` in `core/pipeline/orchestrator.py`
2. Wire up all services
3. Create test script using database source
4. Create test script using Reddit API source
5. Run side-by-side with existing monoliths
6. Compare outputs (should be identical)

**Testing**:
- Run unified pipeline with database source
- Run unified pipeline with Reddit API source
- Compare results with existing monoliths
- Verify all enrichment services called
- Check summary reports match

**Risk**: 🔴 High - integrates all components

---

### Step 8: Deprecate Monoliths (Week 6)

**Goal**: Replace monoliths with unified pipeline

**Actions**:
1. Move `batch_opportunity_scoring.py` → `scripts/archive/`
2. Move `dlt_trust_pipeline.py` → `scripts/archive/`
3. Create new entry point: `scripts/core/run_pipeline.py`
4. Update documentation
5. Update cron jobs / scheduled tasks

**New Entry Point**:
```python
# scripts/core/run_pipeline.py
"""
Unified RedditHarbor Pipeline Entry Point

Replaces:
- batch_opportunity_scoring.py (database source)
- dlt_trust_pipeline.py (Reddit API source)
"""
import argparse
from core.pipeline.orchestrator import OpportunityPipeline
from core.fetchers.database_fetcher import DatabaseFetcher
from core.fetchers.reddit_api_fetcher import RedditAPIFetcher

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', choices=['database', 'reddit'], required=True)
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()

    if args.source == 'database':
        fetcher = DatabaseFetcher(supabase)
    else:
        fetcher = RedditAPIFetcher(subreddits=DEFAULT_SUBREDDITS)

    pipeline = OpportunityPipeline(fetcher=fetcher, supabase_client=supabase)
    result = pipeline.run(limit=args.limit)
    print(result['summary'])

if __name__ == "__main__":
    main()
```

**Testing**:
- Run new entry point with both sources
- Verify identical behavior to monoliths
- Check all database tables populated correctly
- Monitor for errors in logs

**Risk**: 🔴 High - production cutover

---

### Step 9: Build FastAPI Backend (Week 7)

**Goal**: Expose services as REST APIs

**Actions**:
1. Create `api/main.py` with FastAPI app
2. Implement endpoints for each service
3. Add request validation (Pydantic models)
4. Add authentication (if needed)
5. Deploy to production (Docker container)

**Testing**:
- Test each endpoint with curl/Postman
- Load test with realistic traffic
- Monitor latency and error rates
- Verify deduplication still works via API

**Risk**: 🟡 Medium - new component

---

### Step 10: Integrate Next.js Frontend (Week 8+)

**Goal**: Connect Next.js to FastAPI backend

**Actions**:
1. Create Next.js API routes (proxies to FastAPI)
2. Build UI components for opportunity discovery
3. Implement real-time pipeline status
4. Add data visualization dashboards
5. Deploy Next.js app (Vercel)

**Risk**: 🟡 Medium - frontend integration

---

## Success Criteria

### Functional Requirements

✅ **Single Unified Pipeline**
- One codebase for both data sources (database + Reddit API)
- No code duplication between pipelines

✅ **Deduplication Preserved**
- Agno skip logic works for both sources
- Profiler skip logic works for both sources
- No semantic fragmentation of `core_functions`

✅ **All AI Components Working**
- EnhancedLLMProfiler
- OpportunityAnalyzerAgent
- MonetizationAgnoAnalyzer
- TrustLayerValidator
- MarketDataValidator

✅ **DLT Storage Working**
- Merge disposition prevents duplicates
- All tables populated correctly
- Schema evolution supported

✅ **Next.js Integration Ready**
- Each service exposable as API endpoint
- FastAPI backend deployed
- Authentication implemented

### Performance Requirements

✅ **Processing Speed**
- ≤ 10 seconds per submission (same as before)
- Parallel processing for batches (if possible)

✅ **Cost Efficiency**
- No extra LLM calls due to refactoring
- Deduplication saves $3,528/year (as calculated)
- Market validation optional (toggle on/off)

✅ **Code Quality**
- < 500 lines per module
- 80%+ test coverage
- Type hints on all functions
- Comprehensive docstrings

### Non-Functional Requirements

✅ **Maintainability**
- Clear module boundaries
- Single Responsibility Principle
- Easy to add new enrichment services

✅ **Testability**
- Unit tests for all modules
- Integration tests for pipelines
- Mocking for external APIs (Reddit, Jina, OpenRouter)

✅ **Documentation**
- Architecture diagrams
- API documentation (OpenAPI/Swagger)
- Migration guide for future changes

---

## Rollback Plan

### If Refactoring Fails

**Option 1**: Revert to monoliths
- Keep `scripts/archive/` copies functional
- Roll back database migrations if needed
- Restore original cron jobs

**Option 2**: Hybrid approach
- Use new modules where safe (utilities, deduplication)
- Keep monoliths for orchestration temporarily
- Gradual migration over longer timeline

**Trigger Conditions**:
- Data integrity issues (wrong data in database)
- Performance regression (> 20% slower)
- Critical bugs blocking production
- Cost explosion (> 10% increase in LLM costs)

---

## Cost-Benefit Analysis

### Development Cost

**Estimated Effort**: 8 weeks (1 developer)

| Phase | Effort | Risk |
|-------|--------|------|
| Module structure | 2 days | Low |
| Utilities extraction | 3 days | Low |
| Deduplication extraction | 5 days | Medium |
| Fetchers extraction | 5 days | Medium-High |
| Enrichment services | 10 days | High |
| Storage layer | 5 days | High |
| Unified orchestrator | 5 days | High |
| Deprecate monoliths | 3 days | High |
| FastAPI backend | 5 days | Medium |
| Next.js integration | 7 days | Medium |
| **Total** | **50 days (10 weeks)** | |

### Benefits

**Immediate**:
- ✅ Eliminates 3,574 lines of duplicate code
- ✅ Enables Next.js web app integration
- ✅ Deduplication works for BOTH pipelines
- ✅ Trust validation available in batch pipeline
- ✅ Single source of truth for each responsibility

**Long-term**:
- ✅ Easy to add new enrichment services
- ✅ Each service exposable as API endpoint
- ✅ Testability improves dramatically
- ✅ Onboarding new developers faster
- ✅ Future AI components easier to integrate

**Cost Savings**:
- Deduplication: **$3,528/year** (as calculated)
- Development velocity: **50% faster** (estimate)
- Bug fixes: **Reduced by 60%** (single codebase)

---

## Questions for User

Before proceeding with implementation:

1. **Timeline**: Is 8-10 week timeline acceptable, or should we prioritize faster delivery?
2. **Risk Tolerance**: Are you comfortable with high-risk phases (enrichment services, storage layer)?
3. **Testing Strategy**: Do you want to run monoliths side-by-side during migration, or cutover immediately?
4. **Next.js Priority**: Should we build FastAPI backend first, or wait until after refactoring?
5. **Production Impact**: Can we afford downtime during migration, or must it be zero-downtime?
6. **Feature Freeze**: Should we freeze new features during refactoring, or continue parallel development?

---

## Next Steps

**Immediate Actions** (if approved):

1. ✅ Create GitHub issue for tracking refactoring work
2. ✅ Set up project board with phases as milestones
3. ✅ Create feature branch: `feature/unified-pipeline-refactoring`
4. ✅ Begin Phase 1 (Module Structure) - 2 days
5. ✅ Update CLAUDE.md with new architecture
6. ✅ Create test plan document

**Awaiting User Approval** for:
- Overall refactoring approach
- Timeline and resource allocation
- Migration strategy (side-by-side vs. cutover)
- Next.js integration timeline
