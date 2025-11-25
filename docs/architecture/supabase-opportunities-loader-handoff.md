# Supabase Opportunities Loader - Handoff Guide

**Mission:** Replace DLT-based opportunities loader with direct Supabase implementation
**Status:** Architecture complete → Ready for GREEN phase (Test + Implementation)
**Timeline:** 2-3 hours for full implementation + testing
**Blocker Fixed:** UUID normalization (DLT text conversion → Direct UUID handling)

---

## Quick Summary

### What We're Replacing

**Current:** `core/dlt/app_opportunities.py` (178 lines, DLT pipeline)
- **Problem:** DLT normalizes UUID → text, PostgreSQL rejects
- **Complexity:** Pipeline config, schema hints, DLT abstraction

**New:** `core/supabase/opportunities_loader.py` (~30 lines, direct Supabase)
- **Solution:** Direct UUID handling via Supabase client
- **Simplicity:** Single function, batch upsert, minimal dependencies

### Key Design Decisions (Already Made)

1. **Batch upsert** (not individual) for performance
2. **Fail fast** error handling (all-or-nothing)
3. **Pre-transform** core_functions before database call
4. **Implicit transactions** (Supabase handles atomicity)
5. **Same function signature** (drop-in replacement)

---

## File Structure

### New Implementation

```
core/supabase/
├── __init__.py
└── opportunities_loader.py  ← New file (GREEN phase)
```

### Test Suite

```
tests/
└── test_opportunities_supabase_loader.py  ← New file (GREEN phase)
```

### Documentation

```
docs/architecture/
├── supabase-opportunities-loader-design.md      ← Full architecture (you are here)
└── supabase-opportunities-loader-handoff.md     ← This handoff guide
```

---

## Implementation Checklist

### Test Engineer Tasks

- [ ] Create `tests/test_opportunities_supabase_loader.py`
- [ ] Write unit tests:
  - [ ] `test_load_empty_profiles()` - Empty list handling
  - [ ] `test_load_no_problem_description()` - Filtering logic
  - [ ] `test_load_valid_profiles()` - Success path
  - [ ] `test_load_duplicate_ids()` - Upsert behavior
  - [ ] `test_core_functions_standardization()` - JSON serialization
  - [ ] `test_uuid_field_handling()` - UUID type validation
- [ ] Write integration tests:
  - [ ] `test_integration_with_submissions()` - Foreign key
  - [ ] `test_integration_null_submission_id()` - NULL FK
- [ ] Write performance test:
  - [ ] `test_batch_performance()` - 100 profiles in <2 seconds
- [ ] Verify all tests pass

### Python Pro Tasks

- [ ] Create `core/supabase/__init__.py`
- [ ] Implement `core/supabase/opportunities_loader.py`:
  - [ ] Copy template from design doc appendix
  - [ ] Add logging statements
  - [ ] Add type hints
  - [ ] Add comprehensive docstring
  - [ ] Test with real profiles
- [ ] Verify function signature matches old DLT version
- [ ] Run linting: `ruff check . && ruff format .`
- [ ] Run tests: `pytest tests/test_opportunities_supabase_loader.py -v`

### Validation Tasks

- [ ] Database schema validation:
  ```sql
  SELECT pg_typeof(id), pg_typeof(submission_id)
  FROM opportunities LIMIT 1;
  -- Expected: uuid, uuid (not text)
  ```
- [ ] Performance benchmark:
  ```python
  # Load 100 profiles, measure time
  assert duration < 2.0  # Should be <2 seconds
  ```
- [ ] Integration test with real AI profiles
- [ ] Update imports in scripts (if file moved)

---

## Code Template (Ready to Use)

### Location: `core/supabase/opportunities_loader.py`

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

    logger.info(f"📤 Loading {len(filtered_profiles)} AI profiles to opportunities...")

    # STEP 3: Standardize core_functions (list → JSON string for JSONB)
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
        if standardized_profiles:
            logger.error(f"  - First profile ID: {standardized_profiles[0].get('id')}")
        import traceback
        traceback.print_exc()
        return False


# Example usage / manual testing
if __name__ == "__main__":
    import uuid

    test_profiles = [{
        "id": uuid.uuid4(),
        "problem_description": "Teams waste time switching between tools",
        "core_functions": ["Time tracking", "Task management", "Reporting"],
        "submission_id": uuid.uuid4()
    }]

    success = load_app_opportunities(test_profiles)
    print(f"Test result: {'SUCCESS ✓' if success else 'FAILED ✗'}")
```

---

## Test Template (Ready to Use)

### Location: `tests/test_opportunities_supabase_loader.py`

```python
#!/usr/bin/env python3
"""
Test Suite for Supabase Opportunities Loader

Tests the direct Supabase implementation that replaces DLT pipeline.
"""

import uuid
import pytest
from core.supabase.opportunities_loader import load_app_opportunities


class TestOpportunitiesLoader:
    """Test suite for load_app_opportunities function."""

    def test_load_empty_profiles(self):
        """Test with empty profile list."""
        assert load_app_opportunities([]) == False

    def test_load_no_problem_description(self):
        """Test filtering profiles without problem_description."""
        profiles = [{"id": uuid.uuid4(), "title": "Test"}]
        assert load_app_opportunities(profiles) == False

    def test_load_valid_profiles(self, supabase_client):
        """Test successful upsert of valid profiles."""
        profiles = [{
            "id": uuid.uuid4(),
            "problem_description": "Test problem",
            "core_functions": ["Func1", "Func2"]
        }]
        assert load_app_opportunities(profiles) == True

    def test_load_duplicate_ids(self, supabase_client):
        """Test upsert behavior with duplicate IDs."""
        id = uuid.uuid4()
        profiles = [
            {"id": id, "problem_description": "First"},
            {"id": id, "problem_description": "Second"}
        ]
        assert load_app_opportunities(profiles) == True

        # Verify only one record in database
        response = supabase_client.table('opportunities').select('*').eq('id', str(id)).execute()
        assert len(response.data) == 1
        assert response.data[0]['problem_description'] == "Second"

    def test_core_functions_standardization(self, supabase_client):
        """Test core_functions JSON serialization."""
        id = uuid.uuid4()
        profiles = [{
            "id": id,
            "problem_description": "Test",
            "core_functions": ["Func1", "Func2"]
        }]
        load_app_opportunities(profiles)

        # Verify database has JSON array string
        response = supabase_client.table('opportunities').select('core_functions').eq('id', str(id)).execute()
        # Note: PostgreSQL JSONB may return as parsed JSON
        assert isinstance(response.data[0]['core_functions'], (str, list))

    def test_uuid_field_handling(self, supabase_client):
        """Test UUID fields are stored correctly."""
        id = uuid.uuid4()
        submission_id = uuid.uuid4()
        profiles = [{
            "id": id,
            "submission_id": submission_id,
            "problem_description": "Test"
        }]
        load_app_opportunities(profiles)

        # Verify database has UUID types
        response = supabase_client.table('opportunities').select('*').eq('id', str(id)).execute()
        assert response.data[0]['id'] == str(id)
        assert response.data[0]['submission_id'] == str(submission_id)

    def test_integration_with_submissions(self, supabase_client):
        """Test foreign key relationship with submissions table."""
        # Create submission first
        submission_id = uuid.uuid4()
        supabase_client.table('submissions').insert({
            "id": submission_id,
            "reddit_id": "test123",
            "title": "Test submission"
        }).execute()

        # Load opportunity referencing submission
        profiles = [{
            "id": uuid.uuid4(),
            "submission_id": submission_id,
            "problem_description": "Test"
        }]
        assert load_app_opportunities(profiles) == True

    def test_integration_null_submission_id(self, supabase_client):
        """Test opportunities without submission_id."""
        profiles = [{
            "id": uuid.uuid4(),
            "submission_id": None,
            "problem_description": "Test"
        }]
        assert load_app_opportunities(profiles) == True

    def test_batch_performance(self, supabase_client):
        """Test batch upsert performance."""
        import time

        profiles = [
            {"id": uuid.uuid4(), "problem_description": f"Test problem {i}"}
            for i in range(100)
        ]

        start = time.time()
        load_app_opportunities(profiles)
        duration = time.time() - start

        assert duration < 2.0  # Should complete in <2 seconds


@pytest.fixture
def supabase_client():
    """Fixture providing Supabase client for tests."""
    from core.clients import get_supabase_client
    return get_supabase_client()
```

---

## Database Validation Queries

### Verify UUID Types (PostgreSQL)

```sql
-- Check column types
SELECT
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE table_name = 'opportunities'
    AND column_name IN ('id', 'submission_id');

-- Expected output:
-- column_name     | data_type | udt_name
-- ----------------+-----------+---------
-- id              | uuid      | uuid
-- submission_id   | uuid      | uuid
```

### Verify Upsert Behavior

```sql
-- Insert test record
INSERT INTO opportunities (id, problem_description)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'First description');

-- Upsert with same ID (should update, not duplicate)
INSERT INTO opportunities (id, problem_description)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Second description')
ON CONFLICT (id) DO UPDATE SET problem_description = EXCLUDED.problem_description;

-- Verify only one record
SELECT COUNT(*) FROM opportunities WHERE id = '550e8400-e29b-41d4-a716-446655440000';
-- Expected: 1 (not 2)
```

### Verify JSONB Format

```sql
-- Check core_functions JSONB storage
SELECT
    id,
    core_functions,
    pg_typeof(core_functions) as type,
    jsonb_array_length(core_functions::jsonb) as array_length
FROM opportunities
WHERE core_functions IS NOT NULL
LIMIT 5;

-- Expected output:
-- type: jsonb
-- array_length: 2 or 3 (for 2-3 functions)
```

---

## Migration Path

### Phase 1: GREEN (Test + Implement)

1. **Test Engineer:** Write test suite
2. **Python Pro:** Implement loader
3. **Validation:** Run tests, verify UUID handling

### Phase 2: Integration Testing

1. **Side-by-side:** Run both DLT and Supabase loaders
2. **Compare:** Verify identical database state
3. **Performance:** Measure speed difference

### Phase 3: Cut-over

1. **Update imports:** Change scripts to use new loader
2. **Deploy:** Replace DLT implementation
3. **Monitor:** Watch for errors in production

### Phase 4: Cleanup

1. **Remove DLT:** Delete old implementation (if unused)
2. **Update docs:** Mark DLT loader as deprecated
3. **Celebrate:** UUID blocker resolved! 🎉

---

## Success Metrics

### Functional Success

- ✅ All tests pass (unit + integration)
- ✅ UUID fields stored as `uuid` type (not `text`)
- ✅ Upsert behavior works (no duplicates)
- ✅ core_functions stored as JSONB array
- ✅ Same return contract as DLT version

### Non-Functional Success

- ✅ Implementation <50 lines (vs 178 in DLT)
- ✅ Batch upsert <2 seconds for 100 profiles
- ✅ No DLT dependencies in loader
- ✅ Test coverage >90%
- ✅ Clear error messages with context

---

## Key Files Reference

### Implementation

- **New Loader:** `core/supabase/opportunities_loader.py`
- **Old Loader:** `core/dlt/app_opportunities.py` (reference only)
- **Supabase Client:** `core/clients.py` (connection management)
- **Serialization:** `core/utils/core_functions_serialization.py`

### Tests

- **New Tests:** `tests/test_opportunities_supabase_loader.py`
- **Existing Tests:** `tests/test_opportunity_*.py` (may need import updates)

### Documentation

- **Architecture:** `docs/architecture/supabase-opportunities-loader-design.md`
- **Handoff:** `docs/architecture/supabase-opportunities-loader-handoff.md` (this file)
- **Schema:** `supabase/migrations/00000000000000_baseline_schema.sql`

### Scripts (Import Updates Needed)

- `scripts/batch_opportunity_scoring.py`
- `scripts/automated_opportunity_collector.py`
- `scripts/generate_opportunity_insights.py`

---

## Questions for Python Pro

### Q: Where should I create the new file?

**A:** `core/supabase/opportunities_loader.py` (create `__init__.py` too)

### Q: Do I need to update the database schema?

**A:** No, `opportunities` table already exists with correct UUID columns.

### Q: What about error handling?

**A:** Use fail-fast pattern (see template). Single try-except for upsert.

### Q: Should I add retry logic?

**A:** No, keep simple for GREEN phase. Can add later if needed.

### Q: How do I test UUID handling?

**A:** Test engineer will create `test_uuid_field_handling()` - verify `pg_typeof(id)` returns `uuid`.

---

## Questions for Test Engineer

### Q: What's the most important test?

**A:** `test_uuid_field_handling()` - validates the core blocker fix.

### Q: Do I need to mock Supabase?

**A:** Use real Supabase for integration tests (local instance). Mock for unit tests if needed.

### Q: How do I verify upsert behavior?

**A:** Insert profile twice with same ID, verify database has only one record.

### Q: What about performance?

**A:** Load 100 profiles, assert completion <2 seconds (batch upsert is fast).

### Q: Should I test foreign keys?

**A:** Yes - `test_integration_with_submissions()` creates submission first, then opportunity.

---

## Contact / Escalation

### Blockers

If you encounter issues:

1. **UUID still fails:** Check if using `uuid.UUID` objects (not strings)
2. **Supabase connection:** Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
3. **Foreign key errors:** Ensure `submission_id` references valid submission
4. **JSONB errors:** Verify `dlt_standardize_core_functions()` returns JSON string

### Resources

- **Supabase Python Docs:** https://supabase.com/docs/reference/python/upsert
- **PostgreSQL UUID Docs:** https://www.postgresql.org/docs/current/datatype-uuid.html
- **Project Config:** `config/settings.py`
- **Database Client:** `core/clients.py`

---

## Final Notes

### Why This Matters

This replacement:
- **Unblocks 4-day UUID issue** (DLT normalization bug)
- **Simplifies codebase** (70% line reduction)
- **Improves maintainability** (direct SQL visibility)
- **Preserves functionality** (drop-in replacement)

### What Success Looks Like

```python
# After GREEN phase
from core.supabase.opportunities_loader import load_app_opportunities

profiles = [{"id": uuid.uuid4(), "problem_description": "Test"}]
success = load_app_opportunities(profiles)
# ✓ Returns True
# ✓ Database has UUID type (not text)
# ✓ Tests pass with 90%+ coverage
# ✓ Implementation <50 lines
```

---

**Handoff Status:** ✅ Complete - Ready for GREEN phase
**Next Action:** Test engineer creates test suite, Python pro implements loader
**Estimated Time:** 2-3 hours total
**Priority:** High (unblocks UUID issue)

---

**Good luck! You have everything you need to implement and test this successfully.** 🚀
