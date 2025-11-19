# Phase 7: Extract Storage Layer

**Timeline**: Week 7  
**Duration**: 5 days  
**Risk Level**: 🔴 HIGH  
**Dependencies**: Phase 6 completed (enrichment services extracted)

---

## Context

### What Was Completed (Phase 6)
- [x] All 5 AI enrichment services created
- [x] Deduplication integrated into services
- [x] Side-by-side validation passed

### Current State
DLT storage logic scattered across monoliths:
- Opportunity loading (~80 lines in batch_opportunity_scoring.py)
- Profile loading (~60 lines)
- Hybrid submissions (~40 lines in dlt_trust_pipeline.py)
- Different merge strategies

### Why This Phase Is Critical
- Data integrity risk (HIGH)
- DLT schema evolution must work
- No duplicate records allowed
- Foundation for unified orchestrator

---

## Objectives

### Primary Goals
1. **Create** unified `DLTLoader` class
2. **Extract** all storage services
3. **Standardize** merge dispositions
4. **Validate** no duplicate records
5. **Test** schema migration paths

### Success Criteria
- [ ] Unified DLT loading working
- [ ] No duplicate records in database
- [ ] Schema evolution supported
- [ ] All tables populated correctly

---

## Tasks

### Task 1: Create Unified DLT Loader (2 days)

**Create**: `core/storage/dlt_loader.py`

```python
"""Unified DLT loading infrastructure."""
import dlt
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DLTLoader:
    """Unified DLT data loader."""
    
    def __init__(
        self,
        destination: str = "postgres",
        dataset_name: str = "reddit_harbor"
    ):
        self.destination = destination
        self.dataset_name = dataset_name
    
    def load(
        self,
        data: List[Dict[str, Any]],
        table_name: str,
        write_disposition: str = "merge",
        primary_key: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Load data using DLT.
        
        Args:
            data: List of records to load
            table_name: Target table name
            write_disposition: "merge", "replace", or "append"
            primary_key: Primary key field for merge
            
        Returns:
            bool: Success status
        """
        try:
            pipeline = dlt.pipeline(
                pipeline_name=f"{table_name}_loader",
                destination=self.destination,
                dataset_name=self.dataset_name
            )
            
            # Configure write disposition
            load_info = pipeline.run(
                data,
                table_name=table_name,
                write_disposition=write_disposition,
                primary_key=primary_key,
                **kwargs
            )
            
            logger.info(f"Loaded {len(data)} records to {table_name}")
            logger.debug(f"Load info: {load_info}")
            
            return True
            
        except Exception as e:
            logger.error(f"DLT load error for {table_name}: {e}")
            return False
    
    def load_with_schema(
        self,
        data: List[Dict[str, Any]],
        table_name: str,
        schema: Dict[str, Any],
        **kwargs
    ) -> bool:
        """Load with explicit schema definition."""
        # Implementation for schema-controlled loading
        pass
```

---

### Task 2: Create Storage Services (2 days)

**Create storage service files**:

```python
# core/storage/opportunity_store.py
"""Opportunity data storage."""
from .dlt_loader import DLTLoader
from typing import List, Dict, Any

class OpportunityStore:
    """Store opportunity analysis results."""
    
    def __init__(self, loader: DLTLoader):
        self.loader = loader
        self.table_name = 'opportunities_unified'
    
    def store(self, opportunities: List[Dict[str, Any]]) -> bool:
        """Store opportunities with merge disposition."""
        return self.loader.load(
            data=opportunities,
            table_name=self.table_name,
            write_disposition="merge",
            primary_key="submission_id"
        )

# core/storage/profile_store.py
"""AI profile storage."""
# Similar pattern...

# core/storage/hybrid_store.py
"""Hybrid submission storage for trust pipeline."""
# Similar pattern...
```

---

### Task 3: Schema Migration Testing (1 day)

```python
# tests/test_schema_migration.py
"""Test DLT schema evolution."""

def test_add_column_to_existing_table():
    """Test adding new column doesn't break."""
    # Load data with old schema
    # Load data with new schema (additional column)
    # Verify both datasets present
    pass

def test_merge_disposition_no_duplicates():
    """Test merge prevents duplicates."""
    # Load same submission_id twice
    # Verify only one record exists
    pass
```

---

## Validation Checklist

### Implementation Validation
- [ ] DLTLoader created and tested
- [ ] All storage services implemented
- [ ] Merge dispositions configured correctly

### Data Integrity Validation
- [ ] Run full pipeline, check for duplicates: 
  ```sql
  SELECT submission_id, COUNT(*) 
  FROM opportunities_unified 
  GROUP BY submission_id 
  HAVING COUNT(*) > 1;
  ```
- [ ] Verify all expected records present
- [ ] Check schema evolution works

### Integration Validation
- [ ] Storage works with enrichment services
- [ ] Both data sources can store results
- [ ] Performance acceptable (<5s for 100 records)

---

## Rollback Procedure

```bash
rm -rf core/storage/dlt_loader.py
rm -rf core/storage/*_store.py

# Restore database from backup if needed
# (Document backup procedure before this phase)
git checkout HEAD -- scripts/

pytest tests/ -v
```

---

## Next Phase

→ **[Phase 8: Create Unified Orchestrator](phase-08-orchestrator.md)**

**Status**: ⏸️ NOT STARTED
