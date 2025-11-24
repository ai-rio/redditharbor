# Task: 01 - Modify transform_submission_to_schema() for ID Normalization

## Assigned Subagent

**Agent**: `python-pro`

## TDD Context

**This implementation follows Test-Driven Development (TDD):**

1. **RED Phase (COMPLETE)**: Tests have been written FIRST and currently FAIL
2. **GREEN Phase (YOUR TASK)**: Implement code to make tests PASS
3. **REFACTOR Phase (LATER)**: Clean up code while keeping tests green

**Your job is to transition from RED to GREEN by implementing the minimum code needed to pass the tests.**

### Pre-Implementation Verification

Before making ANY code changes, run the tests to confirm RED state:

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix
pytest tests/test_dlt_id_normalization.py::TestTransformSubmissionIDNormalization -v --tb=no | grep -E "(PASSED|FAILED|ERROR)"
```

Expected: Multiple FAILED tests (this confirms RED phase)

### Key TDD Principles

- **Tests are the specification** - Read the tests to understand exactly what the code should do
- **Minimum viable implementation** - Only write code needed to pass tests, nothing more
- **Test after each change** - Run tests frequently to track your progress toward GREEN

---

## Context/Background

RedditHarbor currently stores Reddit submission IDs as raw strings (e.g., `abc123`) in the database. This causes issues with:

1. **Primary Key Inconsistency**: Different ID formats across the codebase
2. **Foreign Key Alignment**: Comments reference submissions using mismatched ID formats
3. **Deduplication Failures**: Same submission can appear with different ID representations

The solution is to normalize all Reddit IDs to deterministic UUIDs **before** they enter the DLT pipeline. The `transform_submission_to_schema()` function is the critical point where this normalization must occur.

A canonical ID resolver already exists at `core/utils/id_resolver.py` that provides `resolve_submission_id()` - you MUST use this function to ensure consistency across the codebase.

**This is Task 1 of 4** - subsequent tasks depend on this implementation.

## Requirements

### MUST (Required)

- [ ] Import `resolve_submission_id` from `core.utils.id_resolver`
- [ ] Use `resolve_submission_id()` to convert raw Reddit ID to UUID
- [ ] Store the generated UUID in `submission_id` field
- [ ] Preserve the original Reddit ID in a new `reddit_id` field
- [ ] Handle None/empty ID values gracefully (return None or omit field)
- [ ] Ensure UUID generation is deterministic (same input = same UUID)

### SHOULD (Expected)

- [ ] Maintain all existing field transformations (title, text, subreddit, etc.)
- [ ] Ensure UUIDs are lowercase for consistency
- [ ] Add appropriate inline comments explaining the ID normalization

### MAY (Optional)

- [ ] Add type hints to the function if not already present
- [ ] Log debug information about ID resolution

## Files to Modify

| File | Lines | Description |
|------|-------|-------------|
| `core/dlt/collection.py` | 113-152 | `transform_submission_to_schema()` function |

## Detailed Instructions

### Step 1: Add Import

At the top of `core/dlt/collection.py`, add the import for the ID resolver. Place it with other core imports (around line 58):

```python
from core.utils.id_resolver import resolve_submission_id
```

### Step 2: Modify the Transform Function

The current function at lines 113-152 needs to:

1. Capture the raw Reddit ID from `submission_data.get("id")`
2. Call `resolve_submission_id()` to get the canonical UUID
3. Use the resolved UUID for `submission_id`
4. Add `reddit_id` field with the original value

### Step 3: Handle Edge Cases

The function must handle:
- `id` is None
- `id` is empty string `""`
- `id` is whitespace only `"   "`

For these cases, either:
- Return the record with `submission_id` as None (will be filtered by `if v is not None`)
- Or skip adding `submission_id` entirely

## Code Examples

### Before (Current Implementation - Lines 136-148)

```python
    transformed = {
        "submission_id": submission_data.get("id"),
        "title": submission_data.get("title"),
        "text": selftext,
        "content": selftext,  # Also store as content for public schema
        "subreddit": submission_data.get("subreddit"),
        "upvotes": score_value,  # Store score as upvotes (integer column)
        "comments_count": comments_count,  # Store as comments_count (integer column)
        "url": submission_data.get("url"),
        "created_at": datetime.fromtimestamp(
            submission_data.get("created_utc", 0)
        ).isoformat(),
    }
```

### After (Expected Implementation)

```python
    # Get raw Reddit ID and resolve to canonical UUID
    raw_reddit_id = submission_data.get("id")

    # Normalize ID to deterministic UUID using canonical resolver
    resolved_id = None
    if raw_reddit_id and str(raw_reddit_id).strip():
        resolution_result = resolve_submission_id(raw_reddit_id)
        if resolution_result and resolution_result.uuid:
            resolved_id = resolution_result.uuid

    transformed = {
        "submission_id": resolved_id,  # Canonical UUID
        "reddit_id": raw_reddit_id,    # Preserve original Reddit ID
        "title": submission_data.get("title"),
        "text": selftext,
        "content": selftext,  # Also store as content for public schema
        "subreddit": submission_data.get("subreddit"),
        "upvotes": score_value,  # Store score as upvotes (integer column)
        "comments_count": comments_count,  # Store as comments_count (integer column)
        "url": submission_data.get("url"),
        "created_at": datetime.fromtimestamp(
            submission_data.get("created_utc", 0)
        ).isoformat(),
    }
```

## Acceptance Criteria

All of the following MUST be true for this task to be accepted:

1. [ ] `transform_submission_to_schema()` produces UUID in `submission_id` field (36 chars, 8-4-4-4-12 format)
2. [ ] Original Reddit ID is preserved in `reddit_id` field
3. [ ] Same input produces identical UUID on every call (deterministic)
4. [ ] UUID matches output of `resolve_submission_id()` for the same input
5. [ ] None/empty/whitespace IDs are handled gracefully (no exceptions)
6. [ ] Other fields (title, text, subreddit, etc.) remain unchanged
7. [ ] At least the following tests pass:
   - `test_submission_id_is_uuid_format`
   - `test_original_reddit_id_preserved`
   - `test_submission_transform_deterministic`
   - `test_submission_id_not_raw_reddit_id`
   - `test_submission_uses_resolver_namespace`

## Verification Commands

Run these commands to verify your implementation:

```bash
# Run the specific test class for submission transforms
cd /home/carlos/projects/redditharbor-core-functions-fix
pytest tests/test_dlt_id_normalization.py::TestTransformSubmissionIDNormalization -v

# Run the ID resolver integration tests
pytest tests/test_dlt_id_normalization.py::TestIDResolverIntegration::test_submission_uses_resolver_namespace -v
pytest tests/test_dlt_id_normalization.py::TestIDResolverIntegration::test_resolver_consistency_across_id_formats -v

# Run edge case tests
pytest tests/test_dlt_id_normalization.py::TestEdgeCases::test_submission_with_none_id -v
pytest tests/test_dlt_id_normalization.py::TestEdgeCases::test_submission_with_empty_id -v
pytest tests/test_dlt_id_normalization.py::TestEdgeCases::test_submission_with_whitespace_id -v
```

### Incremental Testing (TDD Best Practice)

After EACH code change, run tests to track progress from RED to GREEN:

```bash
# Quick check - just pass/fail counts
pytest tests/test_dlt_id_normalization.py::TestTransformSubmissionIDNormalization -v --tb=no 2>&1 | tail -5

# If failures, see details for the first failing test
pytest tests/test_dlt_id_normalization.py::TestTransformSubmissionIDNormalization -v --tb=short -x
```

**Goal**: Move from RED (failing) to GREEN (passing) incrementally. Each passing test is progress.

## Report Template

Use the following template for your implementation report:

**Template**: `templates/implementation-report-template.md`

**Report Location**: Place completed report at:
```
docs/clean-break-implementation/partner-ai-reports/01-implementation-report.md
```

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| ID Resolver | Complete | `core/utils/id_resolver.py` is implemented |
| Test File | Complete | `tests/test_dlt_id_normalization.py` contains 55 tests |

## Reference Materials

- **ID Resolver**: `/home/carlos/projects/redditharbor-core-functions-fix/core/utils/id_resolver.py`
- **Collection Module**: `/home/carlos/projects/redditharbor-core-functions-fix/core/dlt/collection.py`
- **Test File**: `/home/carlos/projects/redditharbor-core-functions-fix/tests/test_dlt_id_normalization.py`

## Test Status Before Implementation

The test file contains 55 tests total. Before this task:
- **Passing**: ~21 tests (edge cases and data type tests)
- **Failing**: ~34 tests (ID normalization tests)

After completing Task 01, expect:
- `TestTransformSubmissionIDNormalization` tests should pass
- Some `TestIDResolverIntegration` tests should pass
- Comment-related tests will still fail (Task 02)

## Important Notes

1. **Do NOT modify the function signature** - keep `transform_submission_to_schema(submission_data: dict[str, Any]) -> dict[str, Any]`

2. **Preserve existing behavior** for all non-ID fields - this is a targeted change

3. **Use the canonical resolver** - do not implement custom UUID generation

4. **The resolver returns a `ResolutionResult` object** with a `.uuid` attribute - check the resolver source code if needed
