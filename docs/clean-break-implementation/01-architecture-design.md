# Pre-DLT ID Normalization Architecture Design

**Document:** ADR-001 - Pre-DLT UUID Normalization Layer
**Status:** Proposed
**Date:** 2025-11-24
**Author:** Architecture Review

---

## 1. Architecture Decision Record (ADR)

### 1.1 Context

RedditHarbor's data pipeline suffers from recurring schema issues caused by ID format mismatches:

- **Root Cause:** Reddit API returns raw IDs (e.g., `abc123`, `hybrid_1`) but different code paths handle these inconsistently
- **Symptom:** NOT FOUND errors when storage uses one format and queries use another
- **Example Failure Mode:**
  ```
  Storage: submission_id = "abc123" (raw)
  Query:   submission_id = "550e8400-e29b-41d4-a716-446655440000" (UUID)
  Result:  NOT FOUND
  ```

### 1.2 Problem Statement

The pipeline lacks a single normalization point for ID formats. Multiple entry points transform IDs differently:

| Entry Point | Current Behavior | Problem |
|-------------|-----------------|---------|
| `transform_submission_to_schema()` | Passes raw ID through | No UUID generation |
| `transform_comment_to_schema()` | Passes raw ID through | Foreign key mismatch |
| `validated_comments` resource | Uses raw `comment.id` | Inconsistent with submissions |
| Query code paths | Sometimes expects UUID | Format mismatch errors |

### 1.3 Decision Drivers

1. **DLT Controls Schema:** Cannot use SQL migrations; must normalize BEFORE data enters DLT
2. **Determinism Required:** Same input must always produce same UUID (idempotent)
3. **Debugging Support:** Original Reddit IDs must be preserved for troubleshooting
4. **Performance:** ID resolution should add minimal overhead (<1ms per record)
5. **Clean Slate:** No existing data to migrate (simplifies implementation)

### 1.4 Considered Alternatives

#### Option A: Database Triggers (Rejected)

```
Pros: Centralized, automatic
Cons: Conflicts with DLT schema control, adds complexity, debugging difficulty
```

#### Option B: Centralized Pre-DLT Hook (Rejected)

```
Pros: Single normalization point
Cons: Requires DLT hook registration, adds abstraction layer, harder to test
```

#### Option C: Transform Function Integration (Selected)

```
Pros: Explicit, testable, no DLT hook complexity, easy to debug
Cons: Requires updating multiple transform functions
```

### 1.5 Decision

**Integrate ID normalization directly into existing transform functions** using the proven `id_resolver` module.

Rationale:
- Transform functions already exist and are well-tested
- Minimal architectural change (evolution, not revolution)
- No DLT hook complexity
- Explicit code path = easy debugging
- Preserves original IDs via `reddit_id` field

### 1.6 Consequences

**Positive:**
- Single source of truth for UUID generation (`id_resolver.py`)
- Deterministic IDs across all code paths
- Original Reddit IDs preserved for debugging
- Works within DLT's schema control model
- Easy to test and validate

**Negative:**
- Must update all transform functions (4-6 locations)
- Requires discipline to use transform functions for all data entry
- Slight code duplication if transform logic expands

---

## 2. Component Design

### 2.1 Architecture Overview

```
+-------------------+     +------------------------+     +------------------+
|  Reddit API       | --> |  Transform Functions   | --> |  DLT Pipeline    |
|  (raw data)       |     |  (ID normalization)    |     |  (schema control)|
+-------------------+     +------------------------+     +------------------+
                                    |
                                    v
                          +------------------+
                          |  ID Resolver     |
                          |  (UUID v5 gen)   |
                          +------------------+
```

### 2.2 Component Responsibilities

#### 2.2.1 ID Resolver (`core/utils/id_resolver.py`)

**Responsibility:** Generate deterministic UUIDs from any input format

**Interface Contract:**
```python
def resolve_submission_id(
    input_value: str | dict[str, Any] | None,
    *,
    require_db_existence: bool = False,
    fallback_to_generated: bool = True,
    supabase_client: Any = None,
) -> ResolutionResult | None:
    """
    Resolve various ID formats to canonical RedditHarbor UUID.

    Returns:
        ResolutionResult with:
        - uuid: Canonical UUID string (or None on failure)
        - source: "passthrough" | "generated" | "database"
        - original_input: String representation of input
        - error: Error message if resolution failed
        - metadata: Additional context (extraction_method, etc.)
    """
```

**Determinism Guarantee:**
```python
# Same input = same output, always
assert resolve_submission_id("abc123").uuid == resolve_submission_id("abc123").uuid
```

**Supported Input Formats:**
| Input Type | Example | Resolution |
|------------|---------|------------|
| Raw Reddit ID | `"abc123"` | UUID v5 from namespace |
| Reddit URL | `"https://reddit.com/r/test/comments/abc123"` | Extract ID, then UUID v5 |
| Existing UUID | `"550e8400-e29b-41d4-a716-446655440000"` | Passthrough (normalized case) |
| Dict with ID | `{"submission_id": "abc123"}` | Extract, then UUID v5 |
| None/Empty | `None`, `""` | Returns `None` |

#### 2.2.2 Transform Functions (`core/dlt/collection.py`)

**Responsibility:** Transform Reddit API data to DLT-compatible schema with normalized IDs

**Modified Functions:**

1. **`transform_submission_to_schema()`** (Line ~113)
2. **`transform_comment_to_schema()`** (Line ~290)

**New Interface Contract:**
```python
def transform_submission_to_schema(submission_data: dict[str, Any]) -> dict[str, Any]:
    """
    Transform Reddit API submission data to match Supabase schema.

    ID Normalization:
    - submission_id: UUID v5 from raw Reddit ID
    - reddit_id: Original raw Reddit ID (preserved for debugging)

    Args:
        submission_data: Raw submission dict from Reddit API

    Returns:
        Transformed submission dict with:
        - submission_id: Normalized UUID
        - reddit_id: Original Reddit ID
        - title, text, content, subreddit, upvotes, etc.
    """
```

#### 2.2.3 DLT Resources (`core/dlt/reddit_source.py`)

**Responsibility:** Collect Reddit data and yield to DLT pipeline

**Normalization Point:** Resources yield raw data; transform functions normalize.

**No Changes Required:** Resources already call transform functions or should be updated to do so.

### 2.3 Error Handling Strategy

```
+------------------+     +------------------+     +------------------+
|  Input Received  | --> |  Validate Input  | --> |  Resolve ID      |
+------------------+     +------------------+     +------------------+
                                |                         |
                                v                         v
                         +-------------+          +----------------+
                         |  Log Error  |          |  Return Result |
                         |  Return None|          |  or Error      |
                         +-------------+          +----------------+
```

**Error Handling Rules:**

1. **Null/Empty Input:** Return `None` immediately (not an error)
2. **Invalid Type:** Return `ResolutionResult` with `error` field set
3. **Exception During Resolution:** Catch, log, return `ResolutionResult` with error
4. **Transform Function Handling:**
   ```python
   result = resolve_submission_id(raw_id)
   if result is None or result.uuid is None:
       # Skip record or use fallback
       logger.warning(f"Failed to resolve ID: {raw_id}")
       return None  # Or skip this record
   ```

### 2.4 Logging/Observability Requirements

**Log Events:**

| Event | Level | Fields |
|-------|-------|--------|
| ID resolved (generated) | DEBUG | `original_input`, `uuid`, `source` |
| ID resolved (passthrough) | DEBUG | `original_input`, `uuid` |
| ID resolution failed | WARNING | `original_input`, `error` |
| Transform completed | DEBUG | `submission_id`, `reddit_id` |
| Transform skipped (null ID) | WARNING | `raw_data_keys` |

**Structured Logging Format:**
```python
logger.debug(
    "ID resolved",
    extra={
        "original_input": result.original_input,
        "uuid": result.uuid,
        "source": result.source,
        "metadata": result.metadata,
    }
)
```

---

## 3. Data Flow Diagram

### 3.1 Submission Data Flow

```
+----------------------+
|    Reddit API        |
|  (PRAW submission)   |
+----------+-----------+
           |
           | Raw submission data:
           | {
           |   "id": "abc123",
           |   "title": "...",
           |   "selftext": "...",
           |   ...
           | }
           v
+----------+-----------+
| collect_problem_posts|
| or validated_comments|
+----------+-----------+
           |
           | Raw dict passed to:
           v
+----------+------------------+
| transform_submission_to_    |
| schema()                    |
|                             |
| 1. Extract raw_id from data |
| 2. Call resolve_submission_ |
|    id(raw_id)               |  <-- NORMALIZATION POINT
| 3. Set submission_id = uuid |
| 4. Set reddit_id = raw_id   |
+----------+------------------+
           |
           | Transformed data:
           | {
           |   "submission_id": "550e8400-...",  <- UUID
           |   "reddit_id": "abc123",            <- Original
           |   "title": "...",
           |   ...
           | }
           v
+----------+-----------+
|    DLT Resource      |
|   (yields data)      |
+----------+-----------+
           |
           v
+----------+-----------+
|    DLT Pipeline      |
| (schema evolution)   |
+----------+-----------+
           |
           v
+----------+-----------+
|   PostgreSQL/        |
|   Supabase           |
+----------------------+
```

### 3.2 Comment Data Flow

```
+----------------------+
|    Reddit API        |
|  (PRAW comment)      |
+----------+-----------+
           |
           | Raw comment data:
           | {
           |   "comment_id": "xyz789",
           |   "submission_id": "abc123",  <- Raw Reddit ID
           |   "body": "...",
           |   ...
           | }
           v
+----------+------------------+
| transform_comment_to_       |
| schema()                    |
|                             |
| 1. Resolve comment_id       |
| 2. Resolve submission_id    |  <-- BOTH IDs NORMALIZED
| 3. Set normalized values    |
| 4. Preserve originals       |
+----------+------------------+
           |
           | Transformed data:
           | {
           |   "comment_id": "uuid-for-xyz789",
           |   "submission_id": "uuid-for-abc123",  <- Matches submissions table
           |   "reddit_comment_id": "xyz789",
           |   "reddit_submission_id": "abc123",
           |   "body": "...",
           |   ...
           | }
           v
+----------+-----------+
|    DLT Pipeline      |
+----------------------+
```

### 3.3 ID Resolution Flow

```
                    +----------------+
                    |  Input Value   |
                    +-------+--------+
                            |
              +-------------+-------------+
              |                           |
       Is None/Empty?              Is String/Dict?
              |                           |
              v                           v
        +-----+-----+              +------+------+
        | Return    |              | Process     |
        | None      |              | Input       |
        +-----------+              +------+------+
                                          |
                    +---------------------+---------------------+
                    |                     |                     |
             Is Valid UUID?        Is Reddit URL?         Is Dict?
                    |                     |                     |
                    v                     v                     v
             +------+------+       +------+------+       +------+------+
             | Passthrough |       | Extract ID  |       | Extract ID  |
             | (normalize  |       | from URL    |       | from dict   |
             | case)       |       +------+------+       +------+------+
             +------+------+              |                     |
                    |                     +----------+----------+
                    |                                |
                    |                     +----------v----------+
                    |                     | Generate UUID v5    |
                    |                     | from raw ID         |
                    |                     +----------+----------+
                    |                                |
                    +----------------+---------------+
                                     |
                                     v
                            +--------+--------+
                            | Return Result   |
                            | {uuid, source,  |
                            |  original_input}|
                            +-----------------+
```

---

## 4. Implementation Checklist

### 4.1 Phase 1: Transform Function Updates (Critical Path)

- [ ] **4.1.1** Update `transform_submission_to_schema()` in `core/dlt/collection.py`
  - Location: Line ~113-151
  - Changes:
    - Import `resolve_submission_id` from `core.utils.id_resolver`
    - Resolve raw `id` to UUID before assignment
    - Add `reddit_id` field with original value
    - Handle resolution failures gracefully

- [ ] **4.1.2** Update `transform_comment_to_schema()` in `core/dlt/collection.py`
  - Location: Line ~290-334
  - Changes:
    - Import `resolve_submission_id` (can be reused for comment IDs)
    - Resolve `comment_id` to UUID
    - Resolve `submission_id` to UUID (foreign key alignment)
    - Add `reddit_comment_id` and `reddit_submission_id` fields

### 4.2 Phase 2: Schema Updates

- [ ] **4.2.1** Update DLT resource columns in `core/dlt/collection.py`
  - Add `reddit_id` column to submission resource schema hints
  - Ensure `submission_id` type is `text` (UUIDs stored as text in PostgreSQL)

- [ ] **4.2.2** Update DLT resource columns in `core/dlt/reddit_source.py`
  - Location: `validated_comments` resource (Line ~341-366)
  - Add `reddit_submission_id` column
  - Ensure `submission_id` column stores UUID

### 4.3 Phase 3: Constants Update

- [ ] **4.3.1** Review `core/dlt/constants.py` for any ID-related constants
  - Verify `PK_SUBMISSION_ID` and `PK_COMMENT_ID` work with UUID values
  - No changes expected (constants are string names, not values)

### 4.4 Phase 4: Downstream Query Updates

- [ ] **4.4.1** Audit query code paths for ID format expectations
  - Files to check:
    - `core/fetchers/database_fetcher.py`
    - `core/storage/opportunity_store.py`
    - `core/storage/profile_store.py`
  - Update any raw ID queries to use UUID resolution

- [ ] **4.4.2** Update any lookup functions that accept user input
  - Wrap user-provided IDs with `resolve_submission_id()` before queries

### 4.5 Phase 5: Logging Enhancement

- [ ] **4.5.1** Add structured logging to transform functions
  - Log successful resolutions at DEBUG level
  - Log failures at WARNING level

### 4.6 Phase 6: Documentation

- [ ] **4.6.1** Update inline docstrings in modified functions
- [ ] **4.6.2** Add example usage to `id_resolver.py` module docstring

---

## 5. Testing Strategy

### 5.1 Unit Tests

**File:** `tests/test_id_normalization.py`

```python
"""
Unit tests for pre-DLT ID normalization.
"""

import pytest
from core.utils.id_resolver import resolve_submission_id, ResolutionResult


class TestIDResolution:
    """Tests for ID resolution logic."""

    def test_raw_reddit_id_produces_uuid(self):
        """Raw Reddit ID should produce a valid UUID."""
        result = resolve_submission_id("abc123")
        assert result is not None
        assert result.uuid is not None
        assert result.source == "generated"
        # UUID format validation
        assert len(result.uuid) == 36
        assert result.uuid.count("-") == 4

    def test_deterministic_resolution(self):
        """Same input should always produce same UUID."""
        result1 = resolve_submission_id("test123")
        result2 = resolve_submission_id("test123")
        assert result1.uuid == result2.uuid

    def test_uuid_passthrough(self):
        """Existing UUID should pass through unchanged."""
        uuid_input = "550e8400-e29b-41d4-a716-446655440000"
        result = resolve_submission_id(uuid_input)
        assert result.uuid == uuid_input.lower()
        assert result.source == "passthrough"

    def test_url_extraction(self):
        """Reddit URLs should have ID extracted and resolved."""
        url = "https://reddit.com/r/test/comments/abc123/title"
        result = resolve_submission_id(url)
        assert result is not None
        assert result.metadata.get("extracted_reddit_id") == "abc123"

    def test_dict_extraction(self):
        """Dicts with submission_id should be extracted."""
        data = {"submission_id": "abc123", "other": "data"}
        result = resolve_submission_id(data)
        assert result is not None
        assert result.uuid is not None

    def test_null_input_returns_none(self):
        """Null input should return None."""
        assert resolve_submission_id(None) is None
        assert resolve_submission_id("") is None

    def test_preserves_original_input(self):
        """Original input should be preserved in result."""
        result = resolve_submission_id("abc123")
        assert result.original_input == "abc123"
```

### 5.2 Integration Tests

**File:** `tests/test_transform_integration.py`

```python
"""
Integration tests for transform functions with ID normalization.
"""

import pytest
from core.dlt.collection import (
    transform_submission_to_schema,
    transform_comment_to_schema,
)


class TestTransformSubmission:
    """Tests for submission transform with ID normalization."""

    def test_submission_gets_uuid(self):
        """Submission should have UUID in submission_id."""
        raw = {
            "id": "abc123",
            "title": "Test Post",
            "selftext": "Content",
            "created_utc": 1700000000,
            "subreddit": "test",
            "score": 10,
            "url": "https://reddit.com/...",
            "num_comments": 5,
        }
        result = transform_submission_to_schema(raw)

        # UUID format check
        assert "-" in result["submission_id"]
        assert len(result["submission_id"]) == 36

        # Original preserved
        assert result["reddit_id"] == "abc123"

    def test_submission_determinism(self):
        """Same raw submission should produce same UUID."""
        raw = {"id": "test999", "title": "Test", "selftext": "",
               "created_utc": 0, "subreddit": "test", "score": 0,
               "url": "", "num_comments": 0}
        result1 = transform_submission_to_schema(raw)
        result2 = transform_submission_to_schema(raw)
        assert result1["submission_id"] == result2["submission_id"]


class TestTransformComment:
    """Tests for comment transform with ID normalization."""

    def test_comment_ids_normalized(self):
        """Both comment_id and submission_id should be UUIDs."""
        raw = {
            "comment_id": "xyz789",
            "submission_id": "abc123",
            "body": "Test comment",
            "score": 5,
            "created_utc": 1700000000,
            "parent_id": "t3_abc123",
            "depth": 0,
            "subreddit": "test",
        }
        result = transform_comment_to_schema(raw)

        # Both IDs normalized
        assert "-" in result["comment_id"]
        assert "-" in result["submission_id"]

        # Originals preserved
        assert result["reddit_comment_id"] == "xyz789"
        assert result["reddit_submission_id"] == "abc123"

    def test_foreign_key_alignment(self):
        """Comment submission_id should match submission UUID."""
        from core.utils.id_resolver import resolve_submission_id

        raw_submission = {"id": "abc123", "title": "Test", "selftext": "",
                         "created_utc": 0, "subreddit": "test", "score": 0,
                         "url": "", "num_comments": 0}
        raw_comment = {"comment_id": "xyz789", "submission_id": "abc123",
                      "body": "", "score": 0, "created_utc": 0,
                      "parent_id": "", "depth": 0, "subreddit": "test"}

        submission = transform_submission_to_schema(raw_submission)
        comment = transform_comment_to_schema(raw_comment)

        # Foreign key alignment
        assert comment["submission_id"] == submission["submission_id"]
```

### 5.3 End-to-End Tests

**File:** `tests/test_dlt_normalization_e2e.py`

```python
"""
End-to-end tests for DLT pipeline with ID normalization.
"""

import pytest


class TestDLTPipelineE2E:
    """End-to-end tests for full pipeline flow."""

    @pytest.fixture
    def mock_reddit_data(self):
        """Mock Reddit API response data."""
        return {
            "submissions": [
                {"id": "sub001", "title": "Test 1", "selftext": "Content 1",
                 "created_utc": 1700000000, "subreddit": "test",
                 "score": 100, "url": "https://...", "num_comments": 10},
                {"id": "sub002", "title": "Test 2", "selftext": "Content 2",
                 "created_utc": 1700000001, "subreddit": "test",
                 "score": 50, "url": "https://...", "num_comments": 5},
            ],
            "comments": [
                {"comment_id": "com001", "submission_id": "sub001",
                 "body": "Comment 1", "score": 10, "created_utc": 1700000002,
                 "parent_id": "t3_sub001", "depth": 0, "subreddit": "test"},
            ],
        }

    def test_full_transform_pipeline(self, mock_reddit_data):
        """Test complete data transformation with ID normalization."""
        from core.dlt.collection import (
            transform_submission_to_schema,
            transform_comment_to_schema,
        )

        # Transform all data
        submissions = [transform_submission_to_schema(s)
                      for s in mock_reddit_data["submissions"]]
        comments = [transform_comment_to_schema(c)
                   for c in mock_reddit_data["comments"]]

        # Verify all IDs are UUIDs
        for s in submissions:
            assert "-" in s["submission_id"]
            assert s.get("reddit_id") is not None

        for c in comments:
            assert "-" in c["comment_id"]
            assert "-" in c["submission_id"]

        # Verify FK alignment
        submission_uuids = {s["submission_id"] for s in submissions}
        for c in comments:
            assert c["submission_id"] in submission_uuids

    def test_idempotent_transforms(self, mock_reddit_data):
        """Transforms should be idempotent."""
        from core.dlt.collection import transform_submission_to_schema

        raw = mock_reddit_data["submissions"][0]

        # Multiple transforms should produce identical results
        result1 = transform_submission_to_schema(raw)
        result2 = transform_submission_to_schema(raw)
        result3 = transform_submission_to_schema(raw)

        assert result1 == result2 == result3
```

### 5.4 Test Execution

```bash
# Run all ID normalization tests
pytest tests/test_id_normalization.py tests/test_transform_integration.py -v

# Run with coverage
pytest tests/test_id_normalization.py --cov=core.utils.id_resolver --cov=core.dlt.collection --cov-report=term-missing

# Run E2E tests
pytest tests/test_dlt_normalization_e2e.py -v
```

### 5.5 Validation Criteria

| Criterion | Target | Verification |
|-----------|--------|--------------|
| Unit test coverage | >90% | `pytest --cov` |
| All IDs are UUIDs | 100% | E2E test assertion |
| Determinism | 100% | Repeated transform tests |
| Original IDs preserved | 100% | Field existence checks |
| FK alignment | 100% | Cross-reference tests |
| Performance | <1ms/record | Benchmark test |

---

## 6. Risk Assessment

### 6.1 Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Missing transform call | Medium | High | Code review, grep audit |
| Performance degradation | Low | Medium | Benchmark tests |
| UUID collision | Very Low | High | UUID v5 namespace isolation |
| Breaking existing queries | Low | High | Phase 4 audit |

### 6.2 Rollback Plan

If issues arise post-implementation:

1. **Immediate:** Revert transform function changes
2. **Data:** No migration needed (clean slate)
3. **Queries:** Restore any modified query code

---

## 7. Appendix

### 7.1 UUID v5 Namespace

```python
# From core/utils/id_resolver.py
REDDITHARBOR_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")
```

This namespace ensures:
- RedditHarbor UUIDs don't collide with UUIDs from other systems
- Same raw ID in different namespaces produces different UUIDs
- Deterministic across all pipeline runs

### 7.2 Example UUID Generation

```python
>>> from core.utils.id_resolver import resolve_submission_id
>>> result = resolve_submission_id("abc123")
>>> result.uuid
'7a8b9c0d-1e2f-5a3b-8c4d-5e6f7a8b9c0d'  # Deterministic
>>> result.source
'generated'
>>> result.original_input
'abc123'
```

### 7.3 Related Files

| File | Purpose |
|------|---------|
| `core/utils/id_resolver.py` | ID resolution logic |
| `core/dlt/collection.py` | Transform functions |
| `core/dlt/reddit_source.py` | DLT resources |
| `core/dlt/constants.py` | Primary key constants |
| `config/dlt.toml` | DLT configuration |
