# Phase 6: Extract AI Enrichment Services

**Timeline**: Week 5-6  
**Duration**: 8 days  
**Risk Level**: 🔴 HIGH  
**Dependencies**: Phase 5 completed (deduplication extracted)

---

## Context

### What Was Completed (Phase 5)
- [x] Extracted all deduplication logic
- [x] $3,528/year savings preserved
- [x] Business concept management unified

### Current State
AI services are called directly from monoliths:
- EnhancedLLMProfiler integration (~200 lines)
- OpportunityAnalyzerAgent integration (~150 lines)
- MonetizationAgnoAnalyzer integration (~180 lines)
- TrustLayerValidator integration (~100 lines)
- MarketDataValidator integration (~120 lines)

### Why This Phase Is Critical
- Highest risk phase (touches all AI components)
- Must integrate deduplication seamlessly
- Foundation for unified orchestrator
- Performance critical (AI calls expensive)

---

## Objectives

### Primary Goals
1. **Create** service wrappers for all 5 AI components
2. **Integrate** deduplication skip logic
3. **Standardize** service interface and error handling
4. **Validate** identical results to monoliths
5. **Maintain** performance (within 10%)

### Success Criteria
- [ ] All 5 services wrapped with deduplication
- [ ] Identical analysis results to monoliths
- [ ] Performance within 10% of baseline
- [ ] 90%+ test coverage
- [ ] Error handling prevents data loss

---

## Tasks

### Task 1: Create Base Service Interface (4 hours)

**Create**: `core/enrichment/base_service.py`

```python
"""Base class for enrichment services."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

class BaseEnrichmentService(ABC):
    """Abstract base for AI enrichment services."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.stats = {'analyzed': 0, 'skipped': 0, 'copied': 0, 'errors': 0}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def enrich(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich submission with AI analysis.
        
        Returns dict with analysis results.
        """
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Return service name for logging."""
        pass
    
    def validate_input(self, submission: Dict[str, Any]) -> bool:
        """Validate submission has required fields."""
        required = ['submission_id', 'title', 'subreddit']
        return all(field in submission for field in required)
    
    def get_statistics(self) -> Dict[str, int]:
        """Return service statistics."""
        return self.stats.copy()
```

---

### Task 2: Create ProfilerService (2 days)

**Create**: `core/enrichment/profiler_service.py`

```python
"""AI Profiler enrichment service with deduplication."""
from typing import Dict, Any, Optional
from core.agents.profiler import EnhancedLLMProfiler
from core.deduplication.profiler_skip_logic import ProfilerSkipLogic
from .base_service.py import BaseEnrichmentService

class ProfilerService(BaseEnrichmentService):
    """Wrapper for EnhancedLLMProfiler with deduplication."""
    
    def __init__(
        self,
        profiler: EnhancedLLMProfiler,
        skip_logic: ProfilerSkipLogic,
        config: Optional[Dict] = None
    ):
        super().__init__(config)
        self.profiler = profiler
        self.skip_logic = skip_logic
        self.enable_dedup = config.get('enable_deduplication', True) if config else True
    
    def enrich(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI profile with deduplication."""
        if not self.validate_input(submission):
            self.stats['errors'] += 1
            return {}
        
        try:
            business_concept_id = submission.get('business_concept_id')
            
            # Check if should skip
            if self.enable_dedup and business_concept_id:
                should_run, reason = self.skip_logic.should_run_profiler_analysis(
                    submission,
                    business_concept_id
                )
                
                if not should_run:
                    self.logger.info(f"Skipping profiler: {reason}")
                    # Try to copy from primary
                    primary_id = self.skip_logic.get_primary_submission_id(business_concept_id)
                    if primary_id:
                        copied = self.skip_logic.copy_profiler_analysis(primary_id, submission['submission_id'])
                        if copied:
                            self.stats['copied'] += 1
                            return copied
                    self.stats['skipped'] += 1
                    return {}
            
            # Run fresh analysis
            profile = self.profiler.generate_profile(
                submission_title=submission['title'],
                submission_content=submission.get('content', ''),
                submission_id=submission['submission_id'],
                subreddit=submission['subreddit']
            )
            
            self.stats['analyzed'] += 1
            self.logger.info(f"Generated profile for {submission['submission_id']}")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Profiler error: {e}")
            self.stats['errors'] += 1
            return {}
    
    def get_service_name(self) -> str:
        return "ProfilerService"
```

---

### Task 3: Create Opportunity, Monetization, Trust, Market Services (4 days)

Create similar services following the ProfilerService pattern:
- `opportunity_service.py` - OpportunityAnalyzerAgent wrapper
- `monetization_service.py` - MonetizationAgnoAnalyzer wrapper (with Agno skip logic)
- `trust_service.py` - TrustLayerValidator wrapper
- `market_validation_service.py` - MarketDataValidator wrapper

Each follows same pattern:
- Extends `BaseEnrichmentService`
- Integrates appropriate skip logic
- Handles errors gracefully
- Returns standardized format

---

### Task 4: Integration Testing (1 day)

```python
# tests/test_enrichment_services.py
import pytest
from core.enrichment.profiler_service import ProfilerService
# ... other imports

def test_profiler_service_fresh_analysis(mock_profiler, mock_skip_logic):
    """Test fresh analysis generation."""
    service = ProfilerService(mock_profiler, mock_skip_logic)
    submission = {'submission_id': 'test1', 'title': 'Test', 'subreddit': 'test'}
    
    result = service.enrich(submission)
    
    assert 'app_name' in result
    assert service.stats['analyzed'] == 1

def test_profiler_service_deduplication(mock_profiler, mock_skip_logic):
    """Test deduplication skip logic."""
    mock_skip_logic.should_run_profiler_analysis.return_value = (False, "Duplicate")
    
    service = ProfilerService(mock_profiler, mock_skip_logic)
    submission = {'submission_id': 'test1', 'title': 'Test', 'subreddit': 'test', 'business_concept_id': 1}
    
    result = service.enrich(submission)
    
    assert service.stats['skipped'] >= 1
```

---

### Task 5: Side-by-Side Validation (1 day)

Run both monolith and new services on same data, compare results:

```python
# scripts/testing/validate_enrichment_services.py
"""Compare enrichment services to monolith results."""

def compare_profiler_results(monolith_result, service_result):
    """Validate profiler service matches monolith."""
    assert monolith_result['app_name'] == service_result['app_name']
    assert set(monolith_result['core_functions']) == set(service_result['core_functions'])
    # ... more validations

# Run comparison on 100 submissions
# Report any discrepancies
```

---

## Validation Checklist

### Service Implementation
- [ ] All 5 services created and tested
- [ ] Deduplication integration working
- [ ] Error handling prevents data loss
- [ ] Statistics tracking accurate

### Results Validation
- [ ] Side-by-side comparison passes (100 submissions)
- [ ] Results identical to monolith (or documented differences)
- [ ] Cost savings maintained

### Performance Validation
- [ ] Processing time within 10% of baseline
- [ ] Memory usage acceptable
- [ ] No performance regressions

---

## Rollback Procedure

```bash
rm -rf core/enrichment/base_service.py
rm -rf core/enrichment/*_service.py
git checkout HEAD -- scripts/core/batch_opportunity_scoring.py
git checkout HEAD -- scripts/dlt/dlt_trust_pipeline.py
pytest tests/ -v
```

---

## Next Phase

→ **[Phase 7: Extract Storage Layer](phase-07-extract-storage.md)**

**Status**: ⏸️ NOT STARTED
