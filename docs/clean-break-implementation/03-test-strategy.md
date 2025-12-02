# Pre-DLT ID Normalization Test Strategy

This document describes the TDD test strategy for RedditHarbor's pre-DLT ID normalization feature.

## Overview

### Purpose

The test suite in `tests/test_dlt_id_normalization.py` validates that DLT transform functions correctly normalize Reddit IDs to UUIDs before data enters the pipeline. This ensures:

- All submission and comment IDs are converted to deterministic UUIDs
- Foreign key relationships between comments and submissions remain intact
- Original Reddit IDs are preserved for reference
- Edge cases (null, empty, malformed) are handled gracefully

### TDD Approach

This feature follows Test-Driven Development:

| Phase | Status | Description |
|-------|--------|-------------|
| RED | Current | Tests written, expected to fail against existing implementation |
| GREEN | Next | Implement ID normalization in transform functions |
| REFACTOR | Final | Optimize implementation while keeping tests green |

The tests define the expected contract. Implementation follows.

## Test Categories

### 1. Submission Transform Tests

**Class:** `TestTransformSubmissionIDNormalization`

Tests verify that `transform_submission_to_schema()` correctly handles ID normalization.

| Test | Purpose |
|------|---------|
| `test_submission_id_is_uuid_format` | Output `submission_id` is valid UUID (8-4-4-4-12 format) |
| `test_original_reddit_id_preserved` | Original Reddit ID stored in `reddit_id` field |
| `test_submission_transform_deterministic` | Same input always produces same UUID |
| `test_submission_id_not_raw_reddit_id` | `submission_id` is UUID, not raw Reddit ID |
| `test_other_fields_unchanged` | Non-ID fields transform normally |

**Sample Input:**
```python
raw = {
    "id": "abc123",
    "title": "Test Post",
    "selftext": "Content here",
    "created_utc": 1700000000,
    "subreddit": "test",
    "score": 10,
    "url": "https://reddit.com/r/test/comments/abc123",
    "num_comments": 5,
}
```

**Expected Output:**
```python
result = {
    "submission_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # UUID
    "reddit_id": "abc123",  # Preserved original
    "title": "Test Post",
    "text": "Content here",
    "subreddit": "test",
    "upvotes": 10,
    "comments_count": 5,
    # ... other fields
}
```

### 2. Comment Transform Tests

**Class:** `TestTransformCommentIDNormalization`

Tests verify that `transform_comment_to_schema()` correctly normalizes both comment IDs and submission foreign keys.

| Test | Purpose |
|------|---------|
| `test_comment_id_is_uuid_format` | Output `comment_id` is valid UUID |
| `test_comment_submission_id_is_uuid_format` | Foreign key `submission_id` is valid UUID |
| `test_original_comment_ids_preserved` | Original IDs in `reddit_comment_id` and `reddit_submission_id` |
| `test_comment_transform_deterministic` | Same input always produces same UUIDs |

**Sample Input:**
```python
raw = {
    "comment_id": "com123",
    "submission_id": "sub456",
    "body": "Test comment",
    "score": 5,
    "created_utc": 1700000000,
    "parent_id": "t3_sub456",
    "depth": 0,
    "subreddit": "test",
}
```

**Expected Output:**
```python
result = {
    "comment_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",      # UUID
    "submission_id": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",   # UUID (FK)
    "reddit_comment_id": "com123",      # Preserved
    "reddit_submission_id": "sub456",   # Preserved
    "body": "Test comment",
    # ... other fields
}
```

### 3. Foreign Key Alignment Tests

**Class:** `TestForeignKeyAlignment`

Tests verify that comment foreign keys align with submission primary keys.

| Test | Purpose |
|------|---------|
| `test_comment_submission_id_matches_submission` | Comment FK matches parent submission PK |
| `test_multiple_comments_same_submission` | All comments on same submission share FK UUID |

**Critical Alignment:**
```python
# Same Reddit ID used in both transforms
reddit_submission_id = "shared_sub_123"

submission = transform_submission_to_schema({"id": reddit_submission_id, ...})
comment = transform_comment_to_schema({"submission_id": reddit_submission_id, ...})

# Must be true for FK integrity
assert comment["submission_id"] == submission["submission_id"]
```

### 4. ID Resolver Integration Tests

**Class:** `TestIDResolverIntegration`

Tests verify transform functions use the canonical `id_resolver` module.

| Test | Purpose |
|------|---------|
| `test_submission_uses_resolver_namespace` | Transform UUID matches resolver output |
| `test_comment_uses_resolver_namespace` | Comment UUIDs match resolver output |

**Integration Check:**
```python
from core.dlt.collection import transform_submission_to_schema
from core.utils.id_resolver import resolve_submission_id

raw_id = "namespace_test_123"
result = transform_submission_to_schema({"id": raw_id, ...})
resolver_result = resolve_submission_id(raw_id)

# Transform must use the canonical resolver
assert result["submission_id"] == resolver_result.uuid
```

### 5. Edge Case Tests

**Class:** `TestEdgeCases`

Tests verify graceful handling of malformed or missing data.

| Test | Input | Expected Behavior |
|------|-------|-------------------|
| `test_submission_with_none_id` | `"id": None` | Returns None or result with `submission_id=None` |
| `test_submission_with_empty_id` | `"id": ""` | Returns None or result with `submission_id=None` |
| `test_comment_with_none_submission_id` | `"submission_id": None` | `comment_id` still normalized if provided |

## Test Execution

### Running the Tests

```bash
# Run all ID normalization tests
pytest tests/test_dlt_id_normalization.py -v

# Run specific test class
pytest tests/test_dlt_id_normalization.py::TestTransformSubmissionIDNormalization -v

# Run with coverage
pytest tests/test_dlt_id_normalization.py --cov=core.dlt.collection --cov-report=term-missing
```

### Expected Results by Phase

**RED Phase (Current):**
```
FAILED test_submission_id_is_uuid_format - AssertionError
FAILED test_original_reddit_id_preserved - KeyError: 'reddit_id'
FAILED test_comment_submission_id_is_uuid_format - AssertionError
...
```

The current `transform_submission_to_schema()` returns raw Reddit IDs, not UUIDs.

**GREEN Phase (After Implementation):**
```
PASSED test_submission_id_is_uuid_format
PASSED test_original_reddit_id_preserved
PASSED test_comment_submission_id_is_uuid_format
...
==================== 15 passed ====================
```

**REFACTOR Phase:**
All tests remain green while optimizing implementation.

### Coverage Targets

| Module | Target | Critical Paths |
|--------|--------|----------------|
| `core/dlt/collection.py` | 90%+ | `transform_*_to_schema` functions |
| `core/utils/id_resolver.py` | 95%+ | `resolve_submission_id`, `generate_deterministic_uuid` |

## Test Data

### UUID Generation

UUIDs are generated using UUID v5 with the RedditHarbor namespace:

```python
REDDITHARBOR_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")

def generate_deterministic_uuid(input_string: str) -> str:
    return str(uuid.uuid5(REDDITHARBOR_NAMESPACE, input_string.strip()))
```

### Sample Transformations

| Input Reddit ID | Generated UUID |
|-----------------|----------------|
| `abc123` | Deterministic based on namespace |
| `xyz789` | Different UUID (same namespace) |
| `abc123` | Same UUID as first (deterministic) |

### Edge Case Examples

| Scenario | Input | Expected Result |
|----------|-------|-----------------|
| Valid ID | `"abc123"` | UUID: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| None | `None` | `submission_id: None` or result is `None` |
| Empty string | `""` | `submission_id: None` or result is `None` |
| Whitespace | `"   "` | `submission_id: None` or result is `None` |
| Already UUID | `"550e8400-e29b-41d4-a716-446655440000"` | Passthrough (same UUID) |

## Validation Criteria

### Passing Criteria by Category

**Submission Transform:**
- `submission_id` is 36-character string with 4 hyphens
- `reddit_id` contains original Reddit ID
- Deterministic: `f(x) == f(x)` always true
- `submission_id != raw["id"]` (not raw ID passthrough)

**Comment Transform:**
- `comment_id` and `submission_id` are valid UUIDs
- `reddit_comment_id` and `reddit_submission_id` preserve originals
- Deterministic for both ID fields

**Foreign Key Alignment:**
- `comment.submission_id == submission.submission_id` for same Reddit ID
- All comments on same submission have identical `submission_id` UUID

**ID Resolver Integration:**
- Transform output matches direct resolver call
- Uses `REDDITHARBOR_NAMESPACE` for UUID generation

### Performance Requirements

| Operation | Target | Notes |
|-----------|--------|-------|
| Single transform | < 1ms | UUID generation is O(1) |
| Batch of 1000 | < 100ms | No I/O in transform |
| Memory overhead | Minimal | Only adds 2 fields per record |

## Troubleshooting

### Common Test Failures

**`KeyError: 'reddit_id'`**
```
Cause: Transform function does not add `reddit_id` field
Fix: Add `"reddit_id": submission_data.get("id")` to transform output
```

**`AssertionError: 36 != len(result["submission_id"])`**
```
Cause: submission_id is raw Reddit ID (typically 6-7 chars), not UUID
Fix: Call `resolve_submission_id()` and use `.uuid` property
```

**`AssertionError: comment["submission_id"] != submission["submission_id"]`**
```
Cause: FK alignment broken - same Reddit ID generates different UUIDs
Fix: Both transforms must use same resolver function and namespace
```

**`ImportError: cannot import name 'resolve_submission_id'`**
```
Cause: ID resolver module not in import path
Fix: Verify core/utils/id_resolver.py exists and is importable
```

### Debugging Steps

1. **Verify Resolver Availability:**
   ```python
   from core.utils.id_resolver import resolve_submission_id
   result = resolve_submission_id("test123")
   print(f"UUID: {result.uuid}, Source: {result.source}")
   ```

2. **Check Transform Output:**
   ```python
   from core.dlt.collection import transform_submission_to_schema
   raw = {"id": "test123", ...}
   result = transform_submission_to_schema(raw)
   print(f"Keys: {result.keys()}")
   print(f"submission_id: {result.get('submission_id')}")
   print(f"reddit_id: {result.get('reddit_id')}")
   ```

3. **Validate UUID Format:**
   ```python
   import re
   UUID_PATTERN = re.compile(
       r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
       re.IGNORECASE
   )
   is_valid = bool(UUID_PATTERN.match(result["submission_id"]))
   ```

4. **Check Determinism:**
   ```python
   result1 = transform_submission_to_schema({"id": "test", ...})
   result2 = transform_submission_to_schema({"id": "test", ...})
   assert result1["submission_id"] == result2["submission_id"], "Not deterministic"
   ```

### Test Isolation

Tests are isolated and do not require:
- Database connection
- Reddit API credentials
- External services

All tests use in-memory data structures and pure functions.
