# Task: 03 - Update DLT Resource Column Definitions

## Assigned Subagent

**Agent**: `python-pro`

## 🚨 CRITICAL: TEST FILE RECREATION REQUIRED

The test file `tests/test_dlt_id_normalization.py` has been **DELETED**. Before ANY implementation work, you MUST ensure the complete test file with all 55 tests exists.

## TEST-FIRST DEVELOPMENT REQUIREMENTS

### CRITICAL: Test File Recreation Required

**BEFORE ANY IMPLEMENTATION WORK, you must verify the test file exists:**

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix

# Check if test file exists
if [ ! -f "tests/test_dlt_id_normalization.py" ]; then
    echo "ERROR: test file does not exist - MUST recreate with all 55 tests"
    exit 1
fi

# Verify it has the expected number of tests
test_count=$(pytest tests/test_dlt_id_normalization.py --collect-only 2>/dev/null | grep "<Function" | wc -l)
if [ "$test_count" -ne 55 ]; then
    echo "ERROR: Expected 55 tests, found $test_count - file incomplete"
    exit 1
fi

echo "✓ Test file exists with all 55 tests"
```

**If the test file is missing or incomplete, you MUST recreate it before proceeding with implementation.**

The complete 55-test specification includes:
- `TestTransformSubmissionIDNormalization` (10 tests)
- `TestTransformCommentIDNormalization` (11 tests)
- `TestForeignKeyAlignment` (4 tests)
- `TestIDResolverIntegration` (9 tests)
- `TestEdgeCases` (10 tests)
- `TestDataTypeConsistency` (5 tests)
- `TestBatchProcessingConsistency` (2 tests)
- **NEW FOR TASK 03**: Additional schema validation tests for DLT resource definitions

## MANDATORY VERIFICATION COMMANDS

### Pre-Implementation (TEST FILE VERIFICATION)
```bash
cd /home/carlos/projects/redditharbor-core-functions-fix

# 1. Verify test file exists with all 55 tests
pytest tests/test_dlt_id_normalization.py --collect-only | grep "test session starts" -A 100 | grep "<Function" | wc -l
# Expected: 55

# 2. Verify current test state (should be RED)
pytest tests/test_dlt_id_normalization.py -v --tb=no 2>&1 | tail -10

# 3. Count specific failing tests
pytest tests/test_dlt_id_normalization.py -v --tb=no 2>&1 | grep -c "FAILED"
```

### Post-Implementation (GREEN STATE VERIFICATION)
```bash
cd /home/carlos/projects/redditharbor-core-functions-fix

# 1. All tests must pass
pytest tests/test_dlt_id_normalization.py -v

# 2. Verify exactly 55 tests run and pass
pytest tests/test_dlt_id_normalization.py -v --tb=no 2>&1 | tail -3

# 3. Check for any warnings or errors
pytest tests/test_dlt_id_normalization.py -v -W error 2>&1 | tail -5
```

### Incremental Testing (TDD Best Practice)
```bash
# After each code change
cd /home/carlos/projects/redditharbor-core-functions-fix

# Quick check - all tests still passing?
pytest tests/test_dlt_id_normalization.py -v --tb=no 2>&1 | tail -5

# If any failures, see details immediately
pytest tests/test_dlt_id_normalization.py -v --tb=short -x
```

## TDD Context

**This implementation follows Test-Driven Development (TDD):**

1. **RED Phase (YOUR FIRST TASK)**: VERIFY TEST FILE EXISTS and confirm tests FAIL
2. **GREEN Phase (YOUR SECOND TASK)**: Implement code to make tests PASS
3. **REFACTOR Phase (LATER)**: Clean up code while keeping tests green

**Your job is to transition from RED to GREEN by implementing the minimum code needed to pass the tests.**

**TDD PHASE COMPLIANCE INSTRUCTIONS:**

### RED Phase (Required First Step)
1. **Verify test file exists** with all 55 tests
2. **Run tests** to confirm they are in RED state (failing)
3. **Document the RED state** - which tests are failing and why
4. **DO NOT** write any implementation code until RED state is confirmed

### GREEN Phase (Implementation)
1. **Write minimal code** to make failing tests pass
2. **Run tests after each change** to verify progress toward GREEN
3. **Stop immediately** when all tests are GREEN
4. **NO EXTRA FEATURES** - only implement what tests require

### Key TDD Principles

- **Tests are the specification** - Read the tests to understand exactly what the code should do
- **Minimum viable implementation** - Only write code needed to pass tests, nothing more
- **Test after each change** - Run tests frequently to verify no regressions
- **RED→GREEN→REFACTOR cycle** - Never skip phases

---

## Context/Background

After Tasks 01 and 02 modified the transform functions to output new fields (`reddit_id`, `reddit_comment_id`, `reddit_submission_id`), the DLT resource definitions need to be updated to include these columns in their schema hints.

DLT resources use column definitions to:
1. Ensure proper data types in the destination database
2. Set nullability constraints
3. Enable unique constraints for deduplication

Without updating these definitions, DLT may infer incorrect types or miss the new columns entirely.

**This is Task 3 of 4** - depends on Tasks 01 and 02 being complete.

## Requirements

### MUST (Required)

- [ ] Add `reddit_id` column to the submission resource schema hints
- [ ] Add `reddit_comment_id` column to any comment resource definitions (if they exist)
- [ ] Add `reddit_submission_id` column to any comment resource definitions (if they exist)
- [ ] Set appropriate data types (`text`) for all new columns
- [ ] Set nullable=True for new columns (original IDs may be missing in edge cases)

### SHOULD (Expected)

- [ ] Maintain consistency with existing column definition patterns
- [ ] Add comments explaining the purpose of new columns
- [ ] Consider adding unique constraint to `reddit_id` for submissions (if not already on submission_id)

### MAY (Optional)

- [ ] Add indexes for lookup performance on reddit_id columns
- [ ] Document the schema changes in inline comments

### SCHEMA VALIDATION TESTS (Task 03 Specific)

Task 03 may need additional schema validation tests beyond the 55 core tests:

- [ ] Verify `reddit_id` column is defined in DLT resource schema hints
- [ ] Verify column data types are correct (`text` for all new columns)
- [ ] Verify nullable constraints are properly set
- [ ] Verify unique constraints (if applied) don't conflict with existing data
- [ ] Test DLT resource definitions can be imported without syntax errors
- [ ] Validate schema consistency across all DLT resources

## Files to Modify

| File | Lines | Description |
|------|-------|-------------|
| `core/dlt/collection.py` | 549-568 | Submission resource `columns={}` definition in `load_to_supabase()` |

## Detailed Instructions

### Step 1: Locate the Resource Definition

In `core/dlt/collection.py`, find the `load_to_supabase()` function (starts around line 526). Inside, there's a DLT resource definition:

```python
@dlt.resource(
    name="submissions",
    write_disposition=write_mode,
    columns={
        "submission_id": {
            "data_type": "text",
            "nullable": True,
            "unique": True,
        },
        # ... other columns
    },
)
def submission_resource():
    yield problem_posts
```

### Step 2: Add the New Column Definition

Add the `reddit_id` column to the columns dictionary:

```python
"reddit_id": {
    "data_type": "text",
    "nullable": True,
},
```

### Step 3: Consider Unique Constraint

Since `reddit_id` represents the original Reddit submission ID:
- It should be unique per submission
- Adding `unique: True` enables deduplication on the original ID
- This is optional but recommended

### Step 4: Check for Comment Resource Definitions

Search for any comment-related DLT resource definitions in the file. If they exist, add:
- `reddit_comment_id` column
- `reddit_submission_id` column

Note: The current `load_to_supabase()` only handles submissions. Comment loading may be handled elsewhere or not yet implemented.

## Code Examples

### Before (Current Implementation - Lines 550-567)

```python
        @dlt.resource(
            name="submissions",
            write_disposition=write_mode,
            columns={
                "submission_id": {
                    "data_type": "text",
                    "nullable": True,
                    "unique": True,
                },
                "title": {"data_type": "text", "nullable": True},
                "text": {"data_type": "text", "nullable": True},
                "content": {"data_type": "text", "nullable": True},
                "subreddit": {"data_type": "text", "nullable": True},
                "score": {"data_type": "bigint", "nullable": True},
                "url": {"data_type": "text", "nullable": True},
                "num_comments": {"data_type": "bigint", "nullable": True},
                "created_at": {"data_type": "timestamp", "nullable": True},
            },
        )
```

### After (Expected Implementation)

```python
        @dlt.resource(
            name="submissions",
            write_disposition=write_mode,
            columns={
                "submission_id": {
                    "data_type": "text",
                    "nullable": True,
                    "unique": True,
                },
                "reddit_id": {  # Original Reddit submission ID (preserved)
                    "data_type": "text",
                    "nullable": True,
                },
                "title": {"data_type": "text", "nullable": True},
                "text": {"data_type": "text", "nullable": True},
                "content": {"data_type": "text", "nullable": True},
                "subreddit": {"data_type": "text", "nullable": True},
                "score": {"data_type": "bigint", "nullable": True},
                "url": {"data_type": "text", "nullable": True},
                "num_comments": {"data_type": "bigint", "nullable": True},
                "created_at": {"data_type": "timestamp", "nullable": True},
            },
        )
```

## Acceptance Criteria

All of the following MUST be true for this task to be accepted:

1. [ ] `reddit_id` column is defined in the submissions resource schema
2. [ ] Column has data_type of `text`
3. [ ] Column is nullable (True)
4. [ ] Existing column definitions remain unchanged
5. [ ] No syntax errors in the resource definition
6. [ ] All previously passing tests still pass

## Verification Commands

Run these commands to verify your implementation:

```bash
# Verify no syntax errors
cd /home/carlos/projects/redditharbor-core-functions-fix
python -c "from core.dlt.collection import load_to_supabase; print('Import OK')"

# Run all tests to ensure nothing broke
pytest tests/test_dlt_id_normalization.py -v

# Verify the column is properly defined (basic check)
python -c "
from core.dlt.collection import load_to_supabase
import inspect
source = inspect.getsource(load_to_supabase)
assert 'reddit_id' in source, 'reddit_id column not found'
print('Column definition found')
"
```

### Incremental Testing (TDD Best Practice)

After EACH code change, run tests to ensure no regressions:

```bash
# Quick check - verify all tests still pass
pytest tests/test_dlt_id_normalization.py -v --tb=no 2>&1 | tail -5

# If any failures, see details
pytest tests/test_dlt_id_normalization.py -v --tb=short -x  # Stop at first failure
```

**Goal**: Keep tests GREEN after schema changes. No regressions allowed.

## Report Template

Use the following template for your implementation report:

**Template**: `templates/implementation-report-template.md`

**Report Location**: Place completed report at:
```
docs/clean-break-implementation/partner-ai-reports/03-implementation-report.md
```

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Task 01 | Required Complete | Submission transform adds `reddit_id` field |
| Task 02 | Required Complete | Comment transform adds preservation fields |
| Test File | **DELETED - MUST RECREATE** | `tests/test_dlt_id_normalization.py` was deleted - ensure it exists with all 55 tests |

## Reference Materials

- **Collection Module**: `/home/carlos/projects/redditharbor-core-functions-fix/core/dlt/collection.py`
- **DLT Documentation**: https://dlthub.com/docs/general-usage/resource
- **Test File**: `/home/carlos/projects/redditharbor-core-functions-fix/tests/test_dlt_id_normalization.py`

## Additional Considerations

### Database Impact

Adding new columns to the DLT schema hints will:
1. Create new columns in the destination table on first run
2. Not affect existing data (new columns will be NULL for existing rows)
3. Enable proper type inference for new fields

### Comment Resource

If a comment DLT resource exists elsewhere in the codebase, you should also update it. Search for:
- `@dlt.resource` decorators with `name="comments"`
- Any function that yields comment data to DLT

Locations to check:
- `core/dlt/collection.py`
- `core/dlt/reddit_source.py`
- Other files in `core/dlt/`

### Backward Compatibility

This change is backward compatible because:
- New columns are nullable
- Existing columns are unchanged
- DLT handles schema evolution automatically

## Important Notes

1. **This is a low-risk change** - adding nullable columns is safe

2. **DLT handles schema evolution** - new columns will be added on next pipeline run

3. **Focus on submissions first** - comment resources may not exist in this file

4. **Check for other resource definitions** - there may be additional places to update

5. **Run full test suite** - ensure no regressions from the change
