# Phase 8: Create Unified Orchestrator

**Timeline**: Week 8  
**Duration**: 5 days  
**Risk Level**: 🔴 HIGH  
**Dependencies**: Phase 7 completed (storage extracted)

---

## Context

### What Was Completed (Phase 7)
- [x] Unified DLT loading infrastructure
- [x] All storage services extracted
- [x] Schema migration validated

### Current State
Two monolithic orchestrators:
- `batch_opportunity_scoring.py` (2,830 lines)
- `dlt_trust_pipeline.py` (774 lines)
- Different configurations
- Duplicate orchestration logic

### Why This Phase Is Critical
- **FINAL INTEGRATION POINT** - All components come together
- Must work identically to both monoliths
- Side-by-side validation essential
- Foundation for API exposure

---

## Objectives

### Primary Goals
1. **Create** single `OpportunityPipeline` class
2. **Integrate** all extracted services
3. **Support** both data sources
4. **Validate** byte-for-byte comparison with monoliths
5. **Prepare** for monolith decommissioning

### Success Criteria
- [ ] `OpportunityPipeline` replaces both monoliths
- [ ] Identical results to original pipelines
- [ ] Configurable services (enable/disable any service)
- [ ] Performance within 5% of monoliths
- [ ] Side-by-side validation passes (100%)

---

## Tasks

### Task 1: Create OpportunityPipeline Class (3 days)

**Create**: `core/pipeline/orchestrator.py`

```python
"""Unified opportunity discovery pipeline."""
from typing import List, Dict, Any, Optional
from core.fetchers.base_fetcher import BaseFetcher
from core.enrichment import *
from core.storage import *
from core.deduplication import BusinessConceptManager
from .config import PipelineConfig
import logging

logger = logging.getLogger(__name__)

class OpportunityPipeline:
    """Unified pipeline for opportunity discovery."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.stats = {
            'fetched': 0,
            'analyzed': 0,
            'stored': 0,
            'filtered': 0,
            'errors': 0
        }
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute complete pipeline.
        
        Returns:
            dict: Pipeline results and statistics
        """
        try:
            logger.info(f"Starting pipeline with {self.config.data_source} source")
            
            # 1. Fetch submissions
            fetcher = self._create_fetcher()
            submissions = list(fetcher.fetch(
                limit=self.config.limit,
                **kwargs
            ))
            self.stats['fetched'] = len(submissions)
            logger.info(f"Fetched {len(submissions)} submissions")
            
            # 2. Quality filtering
            if self.config.enable_quality_filter:
                submissions = self._apply_quality_filter(submissions)
                logger.info(f"{len(submissions)} passed quality filter")
            
            # 3. AI enrichment
            enriched = []
            for sub in submissions:
                try:
                    result = self._enrich_submission(sub)
                    if result:
                        enriched.append(result)
                        self.stats['analyzed'] += 1
                except Exception as e:
                    logger.error(f"Enrichment error for {sub['submission_id']}: {e}")
                    self.stats['errors'] += 1
            
            logger.info(f"Enriched {len(enriched)} submissions")
            
            # 4. Storage
            if enriched:
                success = self._store_results(enriched)
                if success:
                    self.stats['stored'] = len(enriched)
                    logger.info(f"Stored {len(enriched)} results")
            
            # 5. Generate summary
            summary = self._generate_summary()
            
            return {
                'success': True,
                'stats': self.stats,
                'summary': summary,
                'opportunities': enriched
            }
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
    
    def _create_fetcher(self) -> BaseFetcher:
        """Create appropriate fetcher based on config."""
        if self.config.data_source == 'database':
            from core.fetchers.database_fetcher import DatabaseFetcher
            return DatabaseFetcher(self.config.supabase_client, self.config.source_config)
        elif self.config.data_source == 'reddit':
            from core.fetchers.reddit_api_fetcher import RedditAPIFetcher
            return RedditAPIFetcher(self.config.reddit_client, self.config.source_config)
        else:
            raise ValueError(f"Unknown data source: {self.config.data_source}")
    
    def _enrich_submission(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all enabled enrichment services."""
        result = {**submission}
        
        # Profiler
        if self.config.enable_profiler:
            profile = self.profiler_service.enrich(submission)
            result.update(profile)
        
        # Opportunity scoring
        if self.config.enable_opportunity_scoring:
            scores = self.opportunity_service.enrich(submission)
            result.update(scores)
        
        # Monetization
        if self.config.enable_monetization:
            monetization = self.monetization_service.enrich(submission)
            result.update(monetization)
        
        # Trust validation
        if self.config.enable_trust:
            trust = self.trust_service.enrich(submission)
            result.update(trust)
        
        # Market validation
        if self.config.enable_market_validation:
            market = self.market_validation_service.enrich(submission)
            result.update(market)
        
        return result
    
    def _store_results(self, results: List[Dict[str, Any]]) -> bool:
        """Store results using appropriate storage service."""
        from core.storage.opportunity_store import OpportunityStore
        from core.storage.dlt_loader import DLTLoader
        
        loader = DLTLoader()
        store = OpportunityStore(loader)
        
        return store.store(results)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate pipeline summary."""
        return {
            'total_fetched': self.stats['fetched'],
            'total_analyzed': self.stats['analyzed'],
            'total_stored': self.stats['stored'],
            'success_rate': (self.stats['analyzed'] / self.stats['fetched'] * 100) if self.stats['fetched'] > 0 else 0
        }
```

---

### Task 2: Service Container / Dependency Injection (1 day)

**Create**: `core/pipeline/factory.py`

```python
"""Service factory for dependency injection."""
from core.enrichment import *
from core.deduplication import *

class ServiceContainer:
    """Container for pipeline services."""
    
    def __init__(self, config):
        self.config = config
        self._services = {}
    
    def get_profiler_service(self):
        """Get or create profiler service."""
        if 'profiler' not in self._services:
            # Initialize profiler with dependencies
            profiler = EnhancedLLMProfiler(...)
            skip_logic = ProfilerSkipLogic(...)
            self._services['profiler'] = ProfilerService(profiler, skip_logic)
        return self._services['profiler']
    
    # Similar for other services...
```

---

### Task 3: Side-by-Side Validation (1 day)

**Create**: `scripts/testing/validate_unified_pipeline.py`

```python
"""Compare unified pipeline to monolithic pipelines."""

def run_comparison():
    """Run both pipelines on same data, compare results."""
    
    # Run batch_opportunity_scoring.py on 100 submissions
    monolith_results = run_batch_pipeline(limit=100)
    
    # Run unified OpportunityPipeline on same submissions
    unified_results = run_unified_pipeline(limit=100)
    
    # Compare results field-by-field
    differences = compare_results(monolith_results, unified_results)
    
    if differences:
        print(f"Found {len(differences)} differences:")
        for diff in differences:
            print(f"  - {diff}")
        return False
    else:
        print("✅ All results identical!")
        return True

if __name__ == '__main__':
    success = run_comparison()
    exit(0 if success else 1)
```

---

## Validation Checklist

### Implementation Validation
- [ ] `OpportunityPipeline` created and tested
- [ ] ServiceContainer working
- [ ] Configuration system functional

### Functional Validation
- [ ] Side-by-side comparison passes (100%)
- [ ] Both data sources work
- [ ] All service combinations work
- [ ] Error handling prevents data loss

### Performance Validation
- [ ] Processing time within 5% of monoliths
- [ ] Memory usage acceptable
- [ ] No performance regressions

---

## Rollback Procedure

```bash
rm -rf core/pipeline/orchestrator.py
rm -rf core/pipeline/factory.py
git checkout HEAD -- scripts/
pytest tests/ -v
```

---

## Next Phase

→ **[Phase 9: Build FastAPI Backend](phase-09-fastapi-backend.md)**

**Status**: ⏸️ NOT STARTED
