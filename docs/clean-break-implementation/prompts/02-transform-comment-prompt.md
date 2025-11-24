# Task: 02 - Modify transform_comment_to_schema() for ID Normalization

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
pytest tests/test_dlt_id_normalization.py::TestTransformCommentIDNormalization -v --tb=no | grep -E "(PASSED|FAILED|ERROR)"
pytest tests/test_dlt_id_normalization.py::TestForeignKeyAlignment -v --tb=no | grep -E "(PASSED|FAILED|ERROR)"
```

Expected: Multiple FAILED tests (this confirms RED phase)

### Key TDD Principles

- **Tests are the specification** - Read the tests to understand exactly what the code should do
- **Minimum viable implementation** - Only write code needed to pass tests, nothing more
- **Test after each change** - Run tests frequently to track your progress toward GREEN

---

## Context/Background

After Task 01 normalized submission IDs, we must now normalize comment IDs to maintain foreign key alignment. Comments have two IDs that need normalization:

1. **comment_id**: The comment's own identifier (primary key)
2. **submission_id**: Reference to the parent submission (foreign key)

Both must be converted to deterministic UUIDs using the same canonical resolver. This ensures:
- Comment `submission_id` matches parent submission's `submission_id`
- Referential integrity is maintained in the database
- Consistent ID format across all tables

**This is Task 2 of 4** - depends on Task 01 being complete.

## Requirements

### MUST (Required)

- [ ] Import `resolve_submission_id` from `core.utils.id_resolver` (if not already imported from Task 01)
- [ ] Normalize `comment_id` to UUID using `resolve_submission_id()`
- [ ] Normalize `submission_id` to UUID using `resolve_submission_id()`
- [ ] Preserve original comment ID in new `reddit_comment_id` field
- [ ] Preserve original submission ID in new `reddit_submission_id` field
- [ ] Handle None/empty values for both IDs gracefully
- [ ] Ensure comment's `submission_id` UUID matches what `transform_submission_to_schema()` produces for the same Reddit submission ID

### SHOULD (Expected)

- [ ] Maintain all existing field transformations (body, score, depth, etc.)
- [ ] Ensure UUIDs are lowercase for consistency
- [ ] Add inline comments explaining the dual ID normalization

### MAY (Optional)

- [ ] Log debug information about ID resolution
- [ ] Add type hints if not already present

## Files to Modify

| File | Lines | Description |
|------|-------|-------------|
| `core/dlt/collection.py` | 290-334 | `transform_comment_to_schema()` function |

## Detailed Instructions

### Step 1: Verify Import Exists

Ensure this import is present (should be added in Task 01):

```python
from core.utils.id_resolver import resolve_submission_id
```

### Step 2: Modify the Transform Function

The current function at lines 290-334 needs to:

1. Capture raw `comment_id` from input
2. Capture raw `submission_id` from input
3. Resolve both to UUIDs using `resolve_submission_id()`
4. Add `reddit_comment_id` and `reddit_submission_id` preservation fields

### Step 3: Handle Edge Cases

Must handle for both comment_id and submission_id:
- Value is None
- Value is empty string `""`
- Value is whitespace only

### Step 4: Ensure FK Alignment

Critical: The `submission_id` UUID in a comment MUST match the `submission_id` UUID produced by `transform_submission_to_schema()` for the same Reddit submission ID. This is automatic if both use `resolve_submission_id()`.

## Code Examples

### Before (Current Implementation - Lines 311-331)

```python
    transformed = {
        "comment_id": comment_data.get("comment_id"),
        "submission_id": comment_data.get(
            "submission_id"
        ),  # Reddit submission ID (string)
        "link_id": comment_data.get(
            "link_id"
        ),  # Same as submission_id, for FK backfill
        "body": body_text,
        "content": body_text,  # Also store as content for public schema
        "score": comment_data.get("score"),
        "created_at": datetime.fromtimestamp(
            comment_data.get("created_utc", 0)
        ).isoformat(),
        "parent_id": comment_data.get("parent_id"),
        "depth": comment_data.get("depth"),
        "comment_depth": comment_data.get("depth", 0),  # Also store as comment_depth
        "subreddit": comment_data.get("subreddit"),  # Denormalized subreddit name
    }
```

### After (Expected Implementation)

```python
    # Get raw Reddit IDs
    raw_comment_id = comment_data.get("comment_id")
    raw_submission_id = comment_data.get("submission_id")

    # Normalize comment_id to deterministic UUID
    resolved_comment_id = None
    if raw_comment_id and str(raw_comment_id).strip():
        resolution_result = resolve_submission_id(raw_comment_id)
        if resolution_result and resolution_result.uuid:
            resolved_comment_id = resolution_result.uuid

    # Normalize submission_id to deterministic UUID (FK alignment)
    resolved_submission_id = None
    if raw_submission_id and str(raw_submission_id).strip():
        resolution_result = resolve_submission_id(raw_submission_id)
        if resolution_result and resolution_result.uuid:
            resolved_submission_id = resolution_result.uuid

    transformed = {
        "comment_id": resolved_comment_id,          # Canonical UUID
        "reddit_comment_id": raw_comment_id,        # Preserve original
        "submission_id": resolved_submission_id,    # Canonical UUID (FK)
        "reddit_submission_id": raw_submission_id,  # Preserve original
        "link_id": comment_data.get("link_id"),     # Keep for backward compatibility
        "body": body_text,
        "content": body_text,  # Also store as content for public schema
        "score": comment_data.get("score"),
        "created_at": datetime.fromtimestamp(
            comment_data.get("created_utc", 0)
        ).isoformat(),
        "parent_id": comment_data.get("parent_id"),
        "depth": comment_data.get("depth"),
        "comment_depth": comment_data.get("depth", 0),  # Also store as comment_depth
        "subreddit": comment_data.get("subreddit"),  # Denormalized subreddit name
    }
```

## Acceptance Criteria

All of the following MUST be true for this task to be accepted:

1. [ ] `transform_comment_to_schema()` produces UUID in `comment_id` field (36 chars, 8-4-4-4-12 format)
2. [ ] `transform_comment_to_schema()` produces UUID in `submission_id` field (36 chars, 8-4-4-4-12 format)
3. [ ] Original comment ID preserved in `reddit_comment_id` field
4. [ ] Original submission ID preserved in `reddit_submission_id` field
5. [ ] Comment's `submission_id` UUID matches what `transform_submission_to_schema()` produces for same Reddit ID
6. [ ] Multiple comments referencing same submission have identical `submission_id` UUIDs
7. [ ] None/empty IDs handled gracefully (no exceptions)
8. [ ] At least the following tests pass:
   - `test_comment_id_is_uuid_format`
   - `test_comment_submission_id_is_uuid_format`
   - `test_original_comment_ids_preserved`
   - `test_comment_transform_deterministic`
   - `test_comment_submission_id_matches_submission`
   - `test_multiple_comments_same_submission`

## Verification Commands

Run these commands to verify your implementation:

```bash
# Run the specific test class for comment transforms
cd /home/carlos/projects/redditharbor-core-functions-fix
pytest tests/test_dlt_id_normalization.py::TestTransformCommentIDNormalization -v

# Run the FK alignment tests
pytest tests/test_dlt_id_normalization.py::TestForeignKeyAlignment -v

# Run ID resolver integration tests for comments
pytest tests/test_dlt_id_normalization.py::TestIDResolverIntegration::test_comment_submission_id_uses_resolver -v
pytest tests/test_dlt_id_normalization.py::TestIDResolverIntegration::test_comment_id_uses_resolver_namespace -v

# Run edge case tests for comments
pytest tests/test_dlt_id_normalization.py::TestEdgeCases::test_comment_with_none_submission_id -v
pytest tests/test_dlt_id_normalization.py::TestEdgeCases::test_comment_with_none_comment_id -v
pytest tests/test_dlt_id_normalization.py::TestEdgeCases::test_comment_with_both_ids_none -v

# Run batch processing tests
pytest tests/test_dlt_id_normalization.py::TestBatchProcessingConsistency -v
```

### Incremental Testing (TDD Best Practice)

After EACH code change, run tests to track progress from RED to GREEN:

```bash
# Quick check - just pass/fail counts
pytest tests/test_dlt_id_normalization.py::TestTransformCommentIDNormalization -v --tb=no 2>&1 | tail -5

# Check FK alignment progress
pytest tests/test_dlt_id_normalization.py::TestForeignKeyAlignment -v --tb=no 2>&1 | tail -5

# If failures, see details for the first failing test
pytest tests/test_dlt_id_normalization.py::TestTransformCommentIDNormalization -v --tb=short -x
```

**Goal**: Move from RED (failing) to GREEN (passing) incrementally. Each passing test is progress.

## Report Template

Use the following template for your implementation report:

**Template**: `templates/implementation-report-template.md`

**Report Location**: Place completed report at:
```
docs/clean-break-implementation/partner-ai-reports/02-implementation-report.md
```

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Task 01 | Required Complete | Submission transform must be done first |
| ID Resolver | Complete | `core/utils/id_resolver.py` is implemented |
| Test File | Complete | Tests already written in TDD style |

## Reference Materials

- **ID Resolver**: `/home/carlos/projects/redditharbor-core-functions-fix/core/utils/id_resolver.py`
- **Collection Module**: `/home/carlos/projects/redditharbor-core-functions-fix/core/dlt/collection.py`
- **Test File**: `/home/carlos/projects/redditharbor-core-functions-fix/tests/test_dlt_id_normalization.py`

## Test Status After Task 01

After Task 01 completion:
- `TestTransformSubmissionIDNormalization` tests should be passing
- `TestTransformCommentIDNormalization` tests should be failing
- `TestForeignKeyAlignment` tests should be failing

After Task 02 completion:
- All comment-related tests should pass
- FK alignment tests should pass
- Only schema column tests may still fail (Task 03)

## Critical FK Alignment Verification

The most important test is FK alignment. Run this to verify:

```bash
pytest tests/test_dlt_id_normalization.py::TestForeignKeyAlignment::test_comment_submission_id_matches_submission -v
```

This test:
1. Creates a submission with Reddit ID `shared_sub_123`
2. Creates a comment referencing the same Reddit ID
3. Transforms both
4. Verifies `comment["submission_id"] == submission["submission_id"]`

If this test fails, the implementation is incorrect.

## Important Notes

1. **Use the same resolver for both IDs** - `resolve_submission_id()` works for any Reddit ID, not just submission IDs

2. **Do NOT modify the function signature** - keep `transform_comment_to_schema(comment_data: dict[str, Any]) -> dict[str, Any]`

3. **Keep `link_id` unchanged** - this is used for backward compatibility and should remain as the raw value

4. **The resolver is deterministic** - same input string always produces same UUID, which is how FK alignment works automatically
