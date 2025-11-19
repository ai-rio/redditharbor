# Phase 5: Extract Deduplication System

**Timeline**: Week 4  
**Duration**: 5 days  
**Risk Level**: 🟡 MEDIUM  
**Dependencies**: Phase 4 completed (fetchers extracted)

---

## Context

### What Was Completed (Phase 4)
- [x] Created `BaseFetcher` interface
- [x] Extracted `DatabaseFetcher` and `RedditAPIFetcher`
- [x] Standardized data format between sources
- [x] Both monoliths using new fetchers

### Current State
Deduplication logic saves $3,528/year but is scattered:
- Agno skip logic in batch_opportunity_scoring.py (lines 205, 283, 436)
- Profiler skip logic in batch_opportunity_scoring.py (lines 486, 567, 709)
- Business concept management inline
- Statistics tracking mixed with business logic

### Why This Phase Is Critical
- Preserves $3,528/year cost savings
- Enables deduplication for both data sources
- Clean separation of concern
- Foundation for AI enrichment services (Phase 6)

---

## Objectives

### Primary Goals
1. **Extract** Agno monetization skip logic
2. **Extract** AI profiler skip logic  
3. **Create** unified `BusinessConceptManager`
4. **Extract** statistics tracking
5. **Preserve** all cost savings

### Success Criteria
- [ ] All deduplication logic extracted and modular
- [ ] $3,528/year savings preserved and validated
- [ ] Skip logic works with both data sources
- [ ] Business concept management unified
- [ ] Statistics tracking accurate

---

## Tasks

### Task 1: Extract Business Concept Manager (1 day)

**Create**: `core/deduplication/concept_manager.py`

```python
"""Business concept management for deduplication."""
from typing import Optional, Dict, Any
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class BusinessConceptManager:
    """Manage business concepts for semantic deduplication."""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.table = 'business_concepts'
    
    def get_or_create_concept(
        self,
        submission_id: str,
        concept_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing concept or create new one.
        
        Returns concept with analysis status flags.
        """
        try:
            # Try to find existing concept
            response = self.client.table(self.table)\
                .select('*')\
                .eq('primary_submission_id', submission_id)\
                .execute()
            
            if response.data:
                return response.data[0]
            
            # Create new concept
            new_concept = {
                'primary_submission_id': submission_id,
                'concept_text': concept_text,
                'has_agno_analysis': False,
                'has_profiler_analysis': False,
                'submission_count': 1
            }
            
            response = self.client.table(self.table).insert(new_concept).execute()
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error in get_or_create_concept: {e}")
            return None
    
    def update_analysis_status(
        self,
        concept_id: int,
        analysis_type: str,
        status: bool = True
    ) -> bool:
        """Update analysis status flag for concept."""
        try:
            field_map = {
                'agno': 'has_agno_analysis',
                'profiler': 'has_profiler_analysis'
            }
            
            field = field_map.get(analysis_type)
            if not field:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            self.client.table(self.table)\
                .update({field: status})\
                .eq('id', concept_id)\
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating analysis status: {e}")
            return False
    
    def get_concept_for_submission(
        self,
        submission_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get business concept associated with submission."""
        try:
            response = self.client.table(self.table)\
                .select('*')\
                .or_(f'primary_submission_id.eq.{submission_id},related_submissions.cs.{{{submission_id}}}')\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error getting concept for submission: {e}")
            return None
```

---

### Task 2: Extract Agno Skip Logic (1.5 days)

**Create**: `core/deduplication/agno_skip_logic.py`

```python
"""Monetization analysis deduplication logic."""
from typing import Dict, Any, Optional, Tuple
from supabase import Client
from .concept_manager import BusinessConceptManager
import logging

logger = logging.getLogger(__name__)

class AgnoSkipLogic:
    """Handle monetization analysis deduplication."""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.concept_manager = BusinessConceptManager(supabase_client)
        self.stats = {'skipped': 0, 'fresh': 0, 'copied': 0, 'errors': 0}
    
    def should_run_agno_analysis(
        self,
        submission: Dict[str, Any],
        business_concept_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if Agno analysis should run.
        
        Returns:
            (should_run, reason)
        """
        if not business_concept_id:
            return True, "No business concept (first submission)"
        
        try:
            # Check if concept already has Agno analysis
            concept = self.concept_manager.get_concept_for_submission(
                submission['submission_id']
            )
            
            if concept and concept.get('has_agno_analysis'):
                self.stats['skipped'] += 1
                return False, f"Concept {concept['id']} already has Agno analysis"
            
            self.stats['fresh'] += 1
            return True, "No existing Agno analysis found"
            
        except Exception as e:
            logger.error(f"Error checking Agno skip: {e}")
            self.stats['errors'] += 1
            return True, f"Error during check, running analysis as fallback"
    
    def copy_agno_analysis(
        self,
        source_submission_id: str,
        target_submission_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Copy Agno analysis from source to target submission.
        
        Returns copied analysis or None if failed.
        """
        try:
            # Fetch source analysis
            response = self.client.table('agno_analysis')\
                .select('*')\
                .eq('submission_id', source_submission_id)\
                .execute()
            
            if not response.data:
                logger.warning(f"No Agno analysis found for {source_submission_id}")
                return None
            
            source_analysis = response.data[0]
            
            # Copy to target
            copied_analysis = {
                **source_analysis,
                'submission_id': target_submission_id,
                'copied_from_primary': True,
                'primary_submission_id': source_submission_id
            }
            
            # Remove id field
            copied_analysis.pop('id', None)
            copied_analysis.pop('created_at', None)
            
            response = self.client.table('agno_analysis')\
                .insert(copied_analysis)\
                .execute()
            
            if response.data:
                self.stats['copied'] += 1
                logger.info(f"Copied Agno analysis from {source_submission_id} to {target_submission_id}")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error copying Agno analysis: {e}")
            self.stats['errors'] += 1
            return None
    
    def get_statistics(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        return self.stats.copy()
```

---

### Task 3: Extract Profiler Skip Logic (1.5 days)

**Create**: `core/deduplication/profiler_skip_logic.py`

```python
"""AI profiler deduplication logic."""
# Similar structure to AgnoSkipLogic
# Handles core_functions, app_name, value_proposition copying
# (Full implementation follows same pattern)
```

---

### Task 4: Extract Statistics Updater (1 day)

**Create**: `core/deduplication/stats_updater.py`

```python
"""Deduplication cost savings statistics."""
from typing import Dict
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class DeduplicationStatsUpdater:
    """Track and update deduplication cost savings."""
    
    # Cost per analysis (based on token usage)
    AGNO_ANALYSIS_COST = 0.15  # $0.15 per analysis
    PROFILER_ANALYSIS_COST = 0.05  # $0.05 per analysis
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    def update_savings(
        self,
        analysis_type: str,
        skipped_count: int,
        copied_count: int
    ) -> float:
        """
        Calculate and record cost savings.
        
        Returns total savings amount.
        """
        cost_map = {
            'agno': self.AGNO_ANALYSIS_COST,
            'profiler': self.PROFILER_ANALYSIS_COST
        }
        
        cost_per_analysis = cost_map.get(analysis_type, 0)
        total_saved = (skipped_count + copied_count) * cost_per_analysis
        
        logger.info(f"{analysis_type} deduplication saved ${total_saved:.2f} "
                   f"({skipped_count} skipped, {copied_count} copied)")
        
        return total_saved
    
    def get_monthly_savings(self) -> Dict[str, float]:
        """Calculate projected monthly savings."""
        # Query deduplication stats from database
        # Return breakdown by analysis type
        pass
```

---

## Validation Checklist

### Extraction Validation
- [ ] All deduplication logic extracted
- [ ] No duplicate code in monoliths
- [ ] Business concept management unified

### Cost Savings Validation
- [ ] Run batch pipeline with deduplication enabled
- [ ] Verify skip logic triggers correctly
- [ ] Validate $3,528/year savings maintained
- [ ] Check statistics tracking accuracy

### Integration Validation
- [ ] Deduplication works with DatabaseFetcher
- [ ] Can integrate with RedditAPIFetcher
- [ ] Concept lookup performant (<100ms)

---

## Rollback Procedure

```bash
rm -rf core/deduplication/concept_manager.py
rm -rf core/deduplication/agno_skip_logic.py
rm -rf core/deduplication/profiler_skip_logic.py
rm -rf core/deduplication/stats_updater.py

git checkout HEAD -- scripts/core/batch_opportunity_scoring.py
pytest tests/ -v
```

---

## Next Phase

→ **[Phase 6: Extract AI Enrichment Services](phase-06-extract-enrichment.md)**

**Status**: ⏸️ NOT STARTED
