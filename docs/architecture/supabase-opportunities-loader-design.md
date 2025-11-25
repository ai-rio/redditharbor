# Supabase Opportunities Loader Architecture Design

**Document Type:** Architecture Design
**Status:** Design Phase (RED → GREEN pipeline)
**Created:** 2025-11-24
**Purpose:** Replace DLT-based opportunities loader with direct Supabase implementation

---

## Executive Summary

Replace `core/dlt/app_opportunities.py` (DLT-based) with a direct Supabase implementation that:
- **Fixes the 4-day UUID blocker** (DLT normalizes UUID → text, PostgreSQL rejects)
- **Simplifies codebase** (~100 lines → ~30 lines)
- **Preserves all functionality** (upsert, filtering, standardization)
- **Uses proven patterns** from `core/dlt/collection.py` and `core/clients.py`

---

## Current Architecture (DLT-Based)

### Data Flow

```
AI Profiles (list[dict])
    ↓
DLT Resource (app_opportunities_resource)
    ↓ [Filter: problem_description required]
    ↓ [Transform: dlt_standardize_core_functions]
    ↓
DLT Pipeline (merge mode, primary_key=PK_ID)
    ↓
DLT Normalizer (UUID → text conversion)
    ↓ [TYPE MISMATCH: text vs UUID]
    ↓
PostgreSQL (REJECT - silently fails)
    ✗ UUID blocker
```

### Current Features

**File:** `core/dlt/app_opportunities.py`
**Function:** `load_app_opportunities(ai_profiles: list[dict[str, Any]]) -> bool`

1. **Filtering:** Only profiles with `problem_description` field
2. **Standardization:** `dlt_standardize_core_functions()` for JSONB format
3. **Upsert:** Merge disposition with `primary_key=PK_ID` (deduplication on `id`)
4. **Schema Hints:** Column type hints (including `"data_type": "uuid"`)
5. **Error Handling:** Try-except with traceback
6. **Return Contract:** Boolean success status

### Current Problems

1. **UUID Blocker:** DLT normalizes UUID to text despite hints (`x-normalizer: disable`)
2. **Complexity:** 178 lines for simple database upsert
3. **Dependency:** Requires DLT pipeline infrastructure for DB→DB operation
4. **Debugging:** DLT abstraction hides actual SQL/type issues

---

## Proposed Architecture (Supabase Direct)

### New Data Flow

```
AI Profiles (list[dict])
    ↓
Filter (profiles with problem_description)
    ↓
Transform Loop
    ├─ Standardize core_functions (JSON → JSONB string)
    ├─ Validate UUID fields (id, submission_id)
    └─ Build upsert payload
    ↓
Supabase Client
    ├─ Batch upsert (on_conflict='id')
    ├─ Direct UUID handling (no type inference)
    └─ PostgreSQL native casting
    ↓
PostgreSQL (opportunities table)
    ✓ Success
```

### Design Decisions

#### 1. Batch vs Individual Upserts

**Decision: Batch Upsert**

```python
# Recommended approach
client.table('opportunities').upsert(profiles, on_conflict='id').execute()
```

**Rationale:**
- **Performance:** Single round-trip to database
- **Atomicity:** All-or-nothing transaction
- **Simplicity:** One error handling point
- **Network Efficiency:** Reduced connection overhead

**Alternative (Individual):**
```python
# NOT recommended - only if partial failures needed
for profile in profiles:
    try:
        client.table('opportunities').upsert(profile).execute()
    except Exception as e:
        logger.error(f"Failed to upsert profile {profile['id']}: {e}")
        failures.append(profile)
```

**Trade-off:** Individual allows partial success but adds complexity and network overhead.

#### 2. Upsert Conflict Resolution

**Decision: Supabase `.upsert()` with `on_conflict='id'`**

```python
response = client.table('opportunities').upsert(
    profiles,
    on_conflict='id'  # Explicit primary key conflict handling
).execute()
```

**Rationale:**
- **Automatic Deduplication:** Matches DLT merge behavior
- **Native PostgreSQL:** Uses `ON CONFLICT DO UPDATE` under the hood
- **Idempotent:** Safe to retry without duplicates
- **Explicit:** Clear conflict resolution strategy

**Alternative (Manual SQL):**
```python
# NOT recommended - bypasses Supabase client benefits
INSERT INTO opportunities (...) VALUES (...)
ON CONFLICT (id) DO UPDATE SET ...
```

#### 3. Core Functions Standardization

**Decision: Transform BEFORE batch upsert**

```python
# Apply standardization in pre-processing loop
standardized_profiles = []
for profile in filtered_profiles:
    profile = dlt_standardize_core_functions(profile)
    standardized_profiles.append(profile)

# Then batch upsert
client.table('opportunities').upsert(standardized_profiles).execute()
```

**Rationale:**
- **Early Validation:** Catch serialization errors before database call
- **Clear Separation:** Transform logic separate from persistence
- **Reusability:** Standardization can be unit tested independently
- **Performance:** No overhead difference for small batches

**Alternative (Inside loop):**
```python
# Could work but mixes concerns
for profile in profiles:
    profile = dlt_standardize_core_functions(profile)
    client.table('opportunities').upsert(profile).execute()
```

#### 4. Error Handling Strategy

**Decision: Fail Fast with Detailed Logging**

```python
try:
    response = client.table('opportunities').upsert(profiles).execute()
    logger.info(f"✓ Loaded {len(profiles)} profiles successfully")
    return True
except Exception as e:
    logger.error(f"✗ Failed to load profiles: {e}")
    logger.error(f"  - Profile count: {len(profiles)}")
    logger.error(f"  - First profile ID: {profiles[0].get('id') if profiles else 'N/A'}")
    import traceback
    traceback.print_exc()
    return False
```

**Rationale:**
- **Fast Feedback:** Developer knows immediately if operation failed
- **Debugging Context:** Log includes profile count and sample ID
- **Atomic Failure:** Matches batch upsert behavior (all-or-nothing)
- **Consistency:** Matches existing `load_app_opportunities()` contract

**Alternative (Continue on Error):**
```python
# NOT recommended - adds complexity without clear benefit
successes, failures = [], []
for profile in profiles:
    try:
        client.table('opportunities').upsert(profile).execute()
        successes.append(profile)
    except Exception as e:
        failures.append((profile, e))

return len(successes) > 0  # Partial success
```

**Trade-off:** Partial success is complex and rarely needed for opportunities loading.

#### 5. Transaction Boundaries

**Decision: Single implicit transaction (Supabase default)**

```python
# Single batch upsert = single transaction
response = client.table('opportunities').upsert(profiles).execute()
```

**Rationale:**
- **Automatic:** Supabase handles transaction for batch operations
- **Atomic:** All profiles succeed or all fail (rollback)
- **Simple:** No explicit transaction management code
- **Sufficient:** Opportunities loading doesn't need complex multi-step transactions

**Alternative (Explicit Transaction):**
```python
# NOT needed - Supabase batch upsert is already transactional
async with connection.transaction():
    await client.table('opportunities').upsert(profiles).execute()
```

**Note:** PostgreSQL guarantees atomicity for single upsert statements.

---

## Implementation Design

### Function Signature

```python
def load_app_opportunities(ai_profiles: list[dict[str, Any]]) -> bool:
    """
    Load AI profiles to opportunities table using direct Supabase client.

    Replaces DLT-based loader with simplified Supabase implementation that:
    - Fixes UUID type handling (no DLT normalization)
    - Preserves merge/upsert behavior (on_conflict='id')
    - Maintains core_functions standardization
    - Simplifies codebase (~30 lines vs ~100 lines)

    Args:
        ai_profiles: List of AI-generated opportunity profiles with fields:
            - id (UUID, required, primary key)
            - problem_description (str, required for filtering)
            - app_concept (str, optional)
            - core_functions (list[str] | str | None, auto-standardized)
            - value_proposition (str, optional)
            - target_user (str, optional)
            - monetization_model (str, optional)
            - opportunity_score (float, optional)
            - submission_id (UUID, optional, foreign key)

    Returns:
        bool: True if successful, False otherwise

    Raises:
        No exceptions - logs errors and returns False

    Example:
        >>> profiles = [{
        ...     "id": uuid.uuid4(),
        ...     "problem_description": "Teams waste time...",
        ...     "core_functions": ["Time tracking", "Reporting"],
        ...     "submission_id": uuid.uuid4()
        ... }]
        >>> success = load_app_opportunities(profiles)
        >>> print(f"Loaded: {success}")
        True
    """
    pass
```

### Pseudocode Implementation

```python
# STEP 1: Early validation
if not ai_profiles:
    logger.warning("⚠️  No AI profiles to load")
    return False

# STEP 2: Filter profiles (only those with problem_description)
filtered_profiles = [
    profile for profile in ai_profiles
    if profile.get("problem_description")
]

if not filtered_profiles:
    logger.warning("⚠️  No profiles with problem_description found")
    return False

logger.info(f"📤 Loading {len(filtered_profiles)} AI profiles...")

# STEP 3: Standardize core_functions (list → JSON string for JSONB)
standardized_profiles = []
for profile in filtered_profiles:
    try:
        # Apply core_functions serialization
        profile = dlt_standardize_core_functions(profile)
        standardized_profiles.append(profile)
    except Exception as e:
        logger.error(f"Failed to standardize profile {profile.get('id')}: {e}")
        return False

# STEP 4: Initialize Supabase client
try:
    from core.clients import get_supabase_client
    client = get_supabase_client()
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    return False

# STEP 5: Batch upsert to opportunities table
try:
    response = client.table('opportunities').upsert(
        standardized_profiles,
        on_conflict='id'  # Deduplicate on primary key
    ).execute()

    logger.info(f"✓ Successfully loaded {len(standardized_profiles)} profiles")
    logger.info(f"  - Write mode: upsert (on_conflict='id')")
    return True

except Exception as e:
    logger.error(f"✗ Failed to load profiles: {e}")
    logger.error(f"  - Profile count: {len(standardized_profiles)}")
    logger.error(f"  - First profile ID: {standardized_profiles[0].get('id')}")
    import traceback
    traceback.print_exc()
    return False
```

### Key Implementation Notes

1. **UUID Handling:**
   - Python `uuid.UUID` objects pass through Supabase client correctly
   - No explicit casting needed (Supabase handles UUID ↔ PostgreSQL mapping)
   - String UUIDs also work (`"550e8400-e29b-41d4-a716-446655440000"`)

2. **JSONB Fields:**
   - `core_functions`: Must be JSON string (e.g., `'["func1", "func2"]'`)
   - `dlt_standardize_core_functions()` handles serialization
   - PostgreSQL JSONB column accepts JSON strings automatically

3. **Foreign Keys:**
   - `submission_id` references `submissions(id)`
   - NULL allowed (opportunities can exist without submission)
   - Supabase enforces FK constraints automatically

4. **Timestamps:**
   - `created_at` and `updated_at` auto-populated by database
   - No need to include in upsert payload
   - PostgreSQL triggers handle timestamp updates

---

## Trade-offs Analysis

### What We Gain

| Benefit | Impact | Evidence |
|---------|--------|----------|
| **UUID Fix** | Critical | Direct UUID handling bypasses DLT normalization |
| **Simplicity** | High | ~100 lines → ~30 lines (70% reduction) |
| **Debuggability** | High | Direct SQL visibility vs DLT abstraction |
| **Performance** | Medium | Removes DLT overhead (~100-200ms) |
| **Maintainability** | High | Fewer dependencies, clearer code flow |
| **Testability** | High | Direct Supabase mocking vs DLT pipeline mocking |

### What We Might Lose

| Risk | Mitigation | Severity |
|------|------------|----------|
| **DLT Features** | Not needed (no schema evolution, state tracking) | Low |
| **Batch Retry** | Add explicit retry logic if needed | Low |
| **Schema Validation** | Rely on PostgreSQL constraints | Low |
| **Type Inference** | Explicitly handle types in code | Low |

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| UUID still fails | Low | High | Python UUID objects work natively with Supabase |
| Upsert conflicts | Low | Medium | Test with duplicate IDs in test suite |
| FK violations | Low | Medium | Validate submission_id exists before upsert |
| JSONB format | Low | Medium | Test core_functions serialization in unit tests |
| Performance regression | Very Low | Low | Batch upsert is equivalent to DLT merge |

**Overall Risk Level:** **LOW** - Direct Supabase approach is simpler and more reliable.

---

## Migration Impact

### Breaking Changes

**None** - Function signature and return contract remain identical:

```python
# Before (DLT)
load_app_opportunities(profiles: list[dict[str, Any]]) -> bool

# After (Supabase)
load_app_opportunities(profiles: list[dict[str, Any]]) -> bool
```

### Files Requiring Updates

#### 1. Core Implementation
- **File:** `core/dlt/app_opportunities.py` (or new `core/supabase/opportunities_loader.py`)
- **Change:** Replace DLT pipeline with Supabase client
- **Lines Changed:** ~100 lines rewritten
- **Risk:** Low (comprehensive tests in GREEN phase)

#### 2. Import Statements
- **Files:** Any script importing from `core/dlt/app_opportunities.py`
- **Change:** Update import path if file renamed
- **Example:**
  ```python
  # Before
  from core.dlt.app_opportunities import load_app_opportunities

  # After (if moved)
  from core.supabase.opportunities_loader import load_app_opportunities
  ```
- **Risk:** Low (search and replace)

#### 3. Tests
- **New File:** `tests/test_opportunities_supabase_loader.py`
- **Change:** Test engineer creates comprehensive test suite
- **Coverage:**
  - UUID field validation
  - Upsert conflict resolution
  - core_functions standardization
  - Error handling paths
  - Integration with actual database

#### 4. Scripts
- **Files:** Scripts calling `load_app_opportunities()`
  - `scripts/batch_opportunity_scoring.py`
  - `scripts/automated_opportunity_collector.py`
  - `scripts/generate_opportunity_insights.py`
- **Change:** None (function signature unchanged)
- **Risk:** Low (no code changes needed)

### Database Schema Impact

**None** - Table structure remains unchanged:

```sql
-- opportunities table (no changes)
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    problem_statement TEXT,
    target_audience TEXT,
    submission_id UUID REFERENCES submissions(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Deployment Strategy

1. **GREEN Phase:** Implement + test new Supabase loader
2. **Integration Testing:** Run side-by-side comparison (DLT vs Supabase)
3. **Cut-over:** Replace DLT implementation
4. **Validation:** Monitor production for 24h
5. **Cleanup:** Remove DLT dependencies (if unused elsewhere)

---

## Implementation Specification

### File Structure

**Option A: Replace in-place**
```
core/dlt/app_opportunities.py (replace implementation)
```

**Option B: New location (recommended)**
```
core/supabase/
├── __init__.py
└── opportunities_loader.py
```

**Recommendation:** Option B (cleaner separation, easier rollback)

### Dependencies

```python
# Required imports
from typing import Any
from core.clients import get_supabase_client
from core.utils.core_functions_serialization import dlt_standardize_core_functions
import logging
```

### Error Messages

```python
# Standardized error/info messages
INFO_NO_PROFILES = "⚠️  No AI profiles to load"
INFO_NO_PROBLEM_DESC = "⚠️  No profiles with problem_description found"
INFO_LOADING = "📤 Loading {count} AI profiles to opportunities..."
SUCCESS_LOADED = "✓ Successfully loaded {count} profiles (upsert mode)"
ERROR_CLIENT_INIT = "✗ Failed to initialize Supabase client: {error}"
ERROR_STANDARDIZATION = "✗ Failed to standardize profile {id}: {error}"
ERROR_UPSERT = "✗ Failed to load profiles: {error}"
```

### Logging Strategy

```python
# Use module-level logger
logger = logging.getLogger(__name__)

# Log levels
logger.info()    # Success messages, progress updates
logger.warning() # Empty profiles, missing fields
logger.error()   # Database failures, client errors
logger.debug()   # Profile details, intermediate values
```

---

## Testing Requirements

### Unit Tests (Test Engineer: GREEN Phase)

**File:** `tests/test_opportunities_supabase_loader.py`

```python
def test_load_empty_profiles():
    """Test with empty profile list"""
    assert load_app_opportunities([]) == False

def test_load_no_problem_description():
    """Test filtering profiles without problem_description"""
    profiles = [{"id": uuid.uuid4(), "title": "Test"}]
    assert load_app_opportunities(profiles) == False

def test_load_valid_profiles():
    """Test successful upsert of valid profiles"""
    profiles = [{
        "id": uuid.uuid4(),
        "problem_description": "Test problem",
        "core_functions": ["Func1", "Func2"]
    }]
    assert load_app_opportunities(profiles) == True

def test_load_duplicate_ids():
    """Test upsert behavior with duplicate IDs"""
    id = uuid.uuid4()
    profiles = [
        {"id": id, "problem_description": "First"},
        {"id": id, "problem_description": "Second"}
    ]
    assert load_app_opportunities(profiles) == True
    # Verify database has only one record

def test_core_functions_standardization():
    """Test core_functions JSON serialization"""
    profiles = [{
        "id": uuid.uuid4(),
        "problem_description": "Test",
        "core_functions": ["Func1", "Func2"]
    }]
    load_app_opportunities(profiles)
    # Verify database has JSON array string

def test_uuid_field_handling():
    """Test UUID fields are stored correctly"""
    id = uuid.uuid4()
    submission_id = uuid.uuid4()
    profiles = [{
        "id": id,
        "submission_id": submission_id,
        "problem_description": "Test"
    }]
    load_app_opportunities(profiles)
    # Verify database has UUID types (not text)
```

### Integration Tests

```python
def test_integration_with_submissions():
    """Test foreign key relationship with submissions table"""
    # Create submission first
    submission_id = create_test_submission()

    # Load opportunity referencing submission
    profiles = [{
        "id": uuid.uuid4(),
        "submission_id": submission_id,
        "problem_description": "Test"
    }]
    assert load_app_opportunities(profiles) == True

def test_integration_null_submission_id():
    """Test opportunities without submission_id"""
    profiles = [{
        "id": uuid.uuid4(),
        "submission_id": None,
        "problem_description": "Test"
    }]
    assert load_app_opportunities(profiles) == True
```

### Performance Tests

```python
def test_batch_performance():
    """Test batch upsert performance"""
    profiles = [
        {"id": uuid.uuid4(), "problem_description": f"Test {i}"}
        for i in range(100)
    ]

    start = time.time()
    load_app_opportunities(profiles)
    duration = time.time() - start

    assert duration < 2.0  # Should complete in <2 seconds
```

---

## Success Criteria

### Functional Requirements

- ✅ **UUID Fix:** Profiles with UUID fields load successfully (no type errors)
- ✅ **Upsert Behavior:** Duplicate IDs update existing records (no duplicates)
- ✅ **Filtering:** Only profiles with `problem_description` are loaded
- ✅ **Standardization:** `core_functions` serialized to JSONB-compatible JSON
- ✅ **Return Contract:** Returns `True` on success, `False` on failure
- ✅ **Error Handling:** Logs errors with context, includes traceback

### Non-Functional Requirements

- ✅ **Simplicity:** Implementation <50 lines (vs 100+ in DLT version)
- ✅ **Performance:** Batch upsert completes in <2 seconds for 100 profiles
- ✅ **Maintainability:** No DLT-specific abstractions or config
- ✅ **Testability:** All paths covered in unit tests (>90% coverage)
- ✅ **Documentation:** Clear docstrings and inline comments

### Validation Checklist

```bash
# GREEN Phase validation
pytest tests/test_opportunities_supabase_loader.py -v

# Integration validation
python scripts/test_opportunities_loader.py

# Database validation (SQL)
SELECT
    id::text,
    submission_id::text,
    core_functions::text,
    pg_typeof(id) as id_type,
    pg_typeof(submission_id) as submission_id_type
FROM opportunities
WHERE id = '<test_uuid>';

# Expected output:
# id_type: uuid
# submission_id_type: uuid
# core_functions: ["func1", "func2"]
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ SUPABASE OPPORTUNITIES LOADER ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

INPUT LAYER
┌─────────────────────────────────────┐
│ AI Profiles (list[dict[str, Any]]) │
│                                     │
│ Required: id, problem_description   │
│ Optional: core_functions, etc.      │
└─────────────────┬───────────────────┘
                  │
                  ▼
VALIDATION LAYER
┌─────────────────────────────────────┐
│ Early Validation                    │
│ ├─ Empty list check                 │
│ └─ Return False if empty            │
└─────────────────┬───────────────────┘
                  │
                  ▼
FILTER LAYER
┌─────────────────────────────────────┐
│ Filter by problem_description       │
│                                     │
│ filtered = [p for p in profiles    │
│             if p.get("problem_...")]│
└─────────────────┬───────────────────┘
                  │
                  ▼
TRANSFORM LAYER
┌─────────────────────────────────────┐
│ Standardize Core Functions          │
│                                     │
│ FOR each profile:                   │
│   profile = dlt_standardize_...()   │
│   # list → JSON string              │
│   # ["f1","f2"] → '["f1","f2"]'    │
└─────────────────┬───────────────────┘
                  │
                  ▼
CLIENT LAYER
┌─────────────────────────────────────┐
│ Supabase Client                     │
│                                     │
│ from core.clients import            │
│   get_supabase_client               │
│ client = get_supabase_client()      │
└─────────────────┬───────────────────┘
                  │
                  ▼
PERSISTENCE LAYER
┌─────────────────────────────────────┐
│ Batch Upsert                        │
│                                     │
│ client.table('opportunities')       │
│   .upsert(profiles, on_conflict=...)│
│   .execute()                        │
│                                     │
│ Transaction: Implicit (atomic)      │
│ Conflict: UPDATE on id match        │
└─────────────────┬───────────────────┘
                  │
                  ▼
DATABASE LAYER
┌─────────────────────────────────────┐
│ PostgreSQL (opportunities table)    │
│                                     │
│ COLUMNS:                            │
│ ├─ id (UUID, PK)                   │
│ ├─ submission_id (UUID, FK)        │
│ ├─ core_functions (JSONB)          │
│ ├─ problem_description (TEXT)      │
│ └─ created_at, updated_at (TSTZ)   │
│                                     │
│ CONSTRAINTS:                        │
│ ├─ PRIMARY KEY (id)                │
│ └─ FOREIGN KEY (submission_id)     │
└─────────────────┬───────────────────┘
                  │
                  ▼
RESULT LAYER
┌─────────────────────────────────────┐
│ Return Status                       │
│                                     │
│ SUCCESS: True + log info            │
│ FAILURE: False + log error          │
└─────────────────────────────────────┘

ERROR HANDLING POINTS (🔴)
├─ Empty profiles → Return False, log warning
├─ No problem_description → Return False, log warning
├─ Standardization error → Return False, log error + traceback
├─ Client init error → Return False, log error
└─ Upsert error → Return False, log error + traceback
```

---

## Comparison: DLT vs Supabase

| Aspect | DLT Implementation | Supabase Implementation |
|--------|-------------------|------------------------|
| **Lines of Code** | ~178 lines | ~30 lines |
| **Dependencies** | DLT, pipeline config | Supabase client only |
| **UUID Handling** | Text conversion (broken) | Native UUID support |
| **Error Visibility** | Hidden in DLT abstraction | Direct SQL errors |
| **Configuration** | Pipeline config, hints | Client + table name |
| **Testing Complexity** | Mock DLT pipeline | Mock Supabase client |
| **Performance** | DLT overhead + normalization | Direct database call |
| **Schema Evolution** | Automatic (unused) | Manual (acceptable) |
| **State Tracking** | Built-in (unused) | Not needed |
| **Deduplication** | merge + primary_key | upsert + on_conflict |

---

## Next Steps (GREEN Phase)

### Test Engineer Tasks

1. **Create test file:** `tests/test_opportunities_supabase_loader.py`
2. **Write unit tests:** Cover all decision points
3. **Create integration tests:** Test with real database
4. **Create performance tests:** Validate batch upsert speed
5. **Document test scenarios:** Edge cases and error paths

### Python Pro Tasks

1. **Implement loader:** `core/supabase/opportunities_loader.py`
2. **Add logging:** Structured log messages
3. **Error handling:** Try-except with context
4. **Docstrings:** Comprehensive function documentation
5. **Type hints:** Full type annotations

### Validation Tasks

1. **Run tests:** `pytest tests/test_opportunities_supabase_loader.py -v`
2. **Database inspection:** Verify UUID types in PostgreSQL
3. **Performance benchmark:** Compare DLT vs Supabase speed
4. **Integration test:** Run with real AI profiles
5. **Documentation:** Update README with new approach

---

## References

### Source Files

- **Current Implementation:** `/home/carlos/projects/redditharbor-core-functions-fix/core/dlt/app_opportunities.py`
- **Supabase Client:** `/home/carlos/projects/redditharbor-core-functions-fix/core/clients.py`
- **Serialization Utility:** `/home/carlos/projects/redditharbor-core-functions-fix/core/utils/core_functions_serialization.py`
- **Database Schema:** `/home/carlos/projects/redditharbor-core-functions-fix/supabase/migrations/00000000000000_baseline_schema.sql`

### Related Patterns

- **DLT Collection Pattern:** `core/dlt/collection.py` (Reddit API → DB)
- **Supabase Usage:** `core/clients.py` (Connection management)
- **Error Handling:** `core/dlt/collection.py` (Try-except pattern)

### External Documentation

- **Supabase Python Docs:** https://supabase.com/docs/reference/python/upsert
- **PostgreSQL Upsert:** https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT
- **UUID Type:** https://www.postgresql.org/docs/current/datatype-uuid.html

---

## Appendix: Implementation Template

```python
#!/usr/bin/env python3
"""
Supabase-based Opportunities Loader

Direct Supabase implementation replacing DLT pipeline for opportunities loading.
Fixes UUID handling and simplifies codebase by removing DLT abstraction layer.
"""

import logging
from typing import Any

from core.clients import get_supabase_client
from core.utils.core_functions_serialization import dlt_standardize_core_functions

logger = logging.getLogger(__name__)


def load_app_opportunities(ai_profiles: list[dict[str, Any]]) -> bool:
    """
    Load AI profiles to opportunities table using direct Supabase client.

    [Full docstring as specified in Function Signature section]
    """

    # STEP 1: Early validation
    if not ai_profiles:
        logger.warning("⚠️  No AI profiles to load")
        return False

    # STEP 2: Filter profiles
    filtered_profiles = [
        profile for profile in ai_profiles
        if profile.get("problem_description")
    ]

    if not filtered_profiles:
        logger.warning("⚠️  No profiles with problem_description found")
        return False

    logger.info(f"📤 Loading {len(filtered_profiles)} AI profiles to opportunities...")

    # STEP 3: Standardize core_functions
    standardized_profiles = []
    for profile in filtered_profiles:
        try:
            profile = dlt_standardize_core_functions(profile)
            standardized_profiles.append(profile)
        except Exception as e:
            logger.error(f"✗ Failed to standardize profile {profile.get('id')}: {e}")
            return False

    # STEP 4: Initialize Supabase client
    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(f"✗ Failed to initialize Supabase client: {e}")
        return False

    # STEP 5: Batch upsert
    try:
        response = client.table('opportunities').upsert(
            standardized_profiles,
            on_conflict='id'
        ).execute()

        logger.info(f"✓ Successfully loaded {len(standardized_profiles)} profiles")
        logger.info(f"  - Write mode: upsert (on_conflict='id')")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to load profiles: {e}")
        logger.error(f"  - Profile count: {len(standardized_profiles)}")
        if standardized_profiles:
            logger.error(f"  - First profile ID: {standardized_profiles[0].get('id')}")
        import traceback
        traceback.print_exc()
        return False


# Example usage
if __name__ == "__main__":
    import uuid

    test_profiles = [{
        "id": uuid.uuid4(),
        "problem_description": "Test problem",
        "core_functions": ["Function 1", "Function 2"],
        "submission_id": uuid.uuid4()
    }]

    success = load_app_opportunities(test_profiles)
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")
```

---

**End of Architecture Design Document**

**Status:** Ready for GREEN phase implementation
**Next Action:** Test engineer creates test suite, Python pro implements loader
**Estimated Implementation Time:** 2-3 hours (tests + implementation)
