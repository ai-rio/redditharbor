# Clean Break Implementation Workflow

**Created**: 2025-11-24
**Project**: RedditHarbor
**Branch**: `claude/review-pipeline-handover-*`
**Status**: GREEN PHASE IN PROGRESS

---

## 1. Executive Summary

### What
**Clean Break Implementation** for pre-DLT ID normalization in the RedditHarbor data pipeline.

### Why
Fix recurring schema issues caused by ID format mismatches between storage and query paths. Records were being stored in one format (UUID) but queried using another (raw Reddit ID), causing:
- Records not found (4% of data unretrievable)
- Deduplication failures (duplicate records)
- Foreign key relationships breaking (orphaned comments)
- Test suite unreliability (44% of ID-related tests failing)

### How
Partner AI workflow with TDD (Test-Driven Development) approach:
1. Tests written FIRST (RED phase - COMPLETE)
2. Partner AI implements code to make tests pass (GREEN phase - IN PROGRESS)
3. QA Auditor reviews and provides feedback

---

## 2. Decision Record

### Option B Selected: Clean Break with DLT

| Option | Description | Decision |
|--------|-------------|----------|
| **A** | Continue patching existing code | REJECTED - Addresses symptoms, not root cause |
| **B** | Clean Break - normalize BEFORE DLT | **SELECTED** |
| **C** | Abandon DLT entirely | REJECTED - Loses DLT benefits |

### Key Technical Decisions

1. **UUID v5 (Deterministic)**: Same input always produces same UUID
2. **Single Entry Point**: All IDs normalized via `core/utils/id_resolver.py`
3. **Normalize Before DLT**: Data enters pipeline already in correct format
4. **Preserve Original IDs**: Store raw Reddit IDs for debugging/traceability

### TDD Approach

| Phase | Description | Status |
|-------|-------------|--------|
| RED | Tests written first, currently FAILING | COMPLETE |
| GREEN | Implementation makes tests PASS | IN PROGRESS |
| REFACTOR | Clean up while keeping tests green | PENDING |

---

## 3. Workflow Overview

```
+------------------+        +------------------+        +------------------+
|   QA Auditor     |  --->  |   Partner AI     |  --->  |   QA Auditor     |
|   (defines)      |        |   (implements)   |        |   (reviews)      |
+------------------+        +------------------+        +------------------+
        |                           |                          |
        v                           v                          v
   Task Prompts              Implementation             Feedback
   in prompts/               Reports                    APPROVE/REVISE
```

### Communication Flow

1. **QA Auditor** creates task prompt using template
2. **Partner AI** reads prompt, implements code
3. **Partner AI** submits implementation report
4. **QA Auditor** reviews against acceptance criteria
5. **Result**: APPROVED (proceed) or NEEDS_REVISION (iterate)

---

## 4. Folder Structure

```
docs/clean-break-implementation/
|-- prompts/                      # Task instructions for Partner AI
|   |-- README.md                 # Workflow overview and TDD explanation
|   |-- 01-transform-submission-prompt.md
|   |-- 02-transform-comment-prompt.md
|   |-- 03-update-schema-columns-prompt.md
|   |-- 04-verify-tests-prompt.md
|
|-- templates/                    # Standardized communication templates
|   |-- implementation-prompt-template.md
|   |-- implementation-report-template.md
|   |-- qa-feedback-template.md
|
|-- partner-ai-reports/           # Partner AI submissions (after implementation)
|   |-- 01-implementation-report.md
|   |-- (etc.)
|
|-- qa-feedback/                  # QA Auditor feedback on reports
|   |-- 01-qa-feedback.md
|   |-- (etc.)
|
|-- 00-problem-statement.md       # Why we need this fix (root cause analysis)
|-- 02-implementation-guide.md    # Step-by-step implementation instructions
|-- README.md                     # Overview and quick start
```

---

## 5. Implementation Tasks

| Task | File | Function | Description | Status |
|------|------|----------|-------------|--------|
| 01 | `core/dlt/collection.py` | `transform_submission_to_schema()` | Add ID normalization for submissions | PENDING |
| 02 | `core/dlt/collection.py` | `transform_comment_to_schema()` | Add ID normalization for comments | PENDING |
| 03 | `core/dlt/collection.py` | DLT resource definitions | Update column schema hints | PENDING |
| 04 | `tests/test_dlt_id_normalization.py` | All tests | Verify GREEN phase (55/55 pass) | PENDING |

### Task Dependencies

```
Task 01 --> Task 02 --> Task 03 --> Task 04
   |           |           |           |
   v           v           v           v
Submissions  Comments   Schema     Verify
(base)       (depends   (depends   (all pass)
             on 01)     on 01+02)
```

---

## 6. TDD Status

### Test File
`tests/test_dlt_id_normalization.py`

### Current State

| Metric | Count |
|--------|-------|
| **Total Tests** | 55 |
| **Passing** | ~21 (edge cases, data type) |
| **Failing** | ~34 (ID normalization) |

### Test Classes

| Class | Tests | Purpose | Status |
|-------|-------|---------|--------|
| `TestTransformSubmissionIDNormalization` | 10 | Submission UUID generation | RED |
| `TestTransformCommentIDNormalization` | 8 | Comment UUID generation | RED |
| `TestForeignKeyAlignment` | 4 | FK consistency | RED |
| `TestIDResolverIntegration` | 8 | Resolver usage verification | RED |
| `TestEdgeCases` | 10 | None/empty/malformed handling | PARTIAL |
| `TestDataTypeConsistency` | 5 | Type checking | PARTIAL |
| `TestBatchProcessingConsistency` | 2 | Batch behavior | RED |

### RED to GREEN Progression

After Task 01:
- `TestTransformSubmissionIDNormalization`: GREEN
- `TestIDResolverIntegration` (submission tests): GREEN

After Task 02:
- `TestTransformCommentIDNormalization`: GREEN
- `TestForeignKeyAlignment`: GREEN
- `TestIDResolverIntegration` (all): GREEN

After Task 03+04:
- All 55 tests: GREEN

---

## 7. Key Files Reference

| File | Purpose |
|------|---------|
| `core/utils/id_resolver.py` | Canonical ID resolver (UUID v5 generation) |
| `core/dlt/collection.py` | Transform functions to modify (lines 113-152, 290-334) |
| `tests/test_dlt_id_normalization.py` | TDD test suite (55 tests) |
| `core/dlt/constants.py` | Primary key constants (`PK_SUBMISSION_ID`, `PK_COMMENT_ID`) |
| `config/dlt.toml` | DLT configuration |

### ID Resolver API

```python
from core.utils.id_resolver import resolve_submission_id, REDDITHARBOR_NAMESPACE

# Usage
result = resolve_submission_id("abc123")
print(result.uuid)           # "550e8400-e29b-41d4-a716-446655440000"
print(result.source)         # "generated"
print(result.original_input) # "abc123"

# Same input = same UUID (deterministic)
result2 = resolve_submission_id("abc123")
assert result.uuid == result2.uuid  # Always true
```

### Transform Function Location

```python
# core/dlt/collection.py

# Lines 113-152: Submission transform
def transform_submission_to_schema(submission_data: dict[str, Any]) -> dict[str, Any]:
    # MODIFY: Add ID normalization here
    pass

# Lines 290-334: Comment transform
def transform_comment_to_schema(comment_data: dict[str, Any]) -> dict[str, Any]:
    # MODIFY: Add ID normalization here
    pass
```

---

## 8. Quick Commands

### Run All ID Normalization Tests

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix
pytest tests/test_dlt_id_normalization.py -v
```

### Check RED/GREEN Status (Summary)

```bash
pytest tests/test_dlt_id_normalization.py -v --tb=no 2>&1 | grep -E "passed|failed"
```

### Run Specific Test Class

```bash
# Submission tests
pytest tests/test_dlt_id_normalization.py::TestTransformSubmissionIDNormalization -v

# Comment tests
pytest tests/test_dlt_id_normalization.py::TestTransformCommentIDNormalization -v

# Foreign key tests
pytest tests/test_dlt_id_normalization.py::TestForeignKeyAlignment -v
```

### Pre-Implementation Verification (Confirm RED)

```bash
pytest tests/test_dlt_id_normalization.py -v --tb=no | grep -E "(PASSED|FAILED|ERROR)"
```

Expected: Multiple FAILED tests (confirms RED phase ready).

### Post-Implementation Verification (Confirm GREEN)

```bash
pytest tests/test_dlt_id_normalization.py -v
```

Expected: `55 passed` (confirms GREEN phase complete).

---

## 9. Next Actions

### Immediate (Task 01)

1. Open task prompt: `docs/clean-break-implementation/prompts/01-transform-submission-prompt.md`
2. Execute with Partner AI
3. Partner AI submits report to `partner-ai-reports/01-implementation-report.md`
4. QA audit the implementation

### Subsequent Tasks

| Order | Task | Prompt File |
|-------|------|-------------|
| 1 | Submission transform | `01-transform-submission-prompt.md` |
| 2 | Comment transform | `02-transform-comment-prompt.md` |
| 3 | Schema columns | `03-update-schema-columns-prompt.md` |
| 4 | Verify all tests | `04-verify-tests-prompt.md` |

---

## 10. Troubleshooting Guide

### Tests Fail After Implementation

**Symptom**: Tests passing before now fail with ID mismatch

**Cause**: Test fixtures using old ID format

**Solution**:
```python
# Update test expectations
from core.utils.id_resolver import resolve_submission_id
expected_id = resolve_submission_id("abc123").uuid  # Use UUID, not raw ID
```

### UUID Mismatch Between Python and PostgreSQL

**Symptom**: Different UUIDs generated

**Cause**: Namespace UUIDs not identical

**Solution**: Verify namespace matches:
```python
import uuid
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")
print(NAMESPACE)  # Must match PostgreSQL value
```

### Foreign Key Violations

**Symptom**: Updates fail with FK constraint errors

**Cause**: Comment submission_id does not match parent submission's submission_id

**Solution**: Ensure both use same resolver call for same Reddit ID

---

## 11. Related Documentation

| Document | Location |
|----------|----------|
| Problem Statement | `docs/clean-break-implementation/00-problem-statement.md` |
| Implementation Guide | `docs/clean-break-implementation/02-implementation-guide.md` |
| Partner AI Workflow | `docs/clean-break-implementation/prompts/README.md` |
| ID Resolution Fix Reports | `docs/id-resolution-fix/reports/` |
| Option B Plan | `docs/id-resolution-fix/OPTION_B_CLEAN_BREAK_PLAN.md` |

---

## 12. Success Criteria

### Task-Level Acceptance

Each task is complete when:
1. All specified tests pass
2. Implementation report submitted
3. QA audit approves

### Project-Level Acceptance

The Clean Break Implementation is complete when:
1. All 55 tests in `test_dlt_id_normalization.py` pass (GREEN phase)
2. `submission_id` fields contain UUID format (36 chars, 8-4-4-4-12)
3. Original Reddit IDs preserved in `reddit_id` / `reddit_comment_id` / `reddit_submission_id`
4. Foreign key alignment maintained (comment.submission_id matches parent submission.submission_id)
5. Deterministic UUIDs (same input always produces same UUID)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-24 | 1.0 | Initial workflow document created |
