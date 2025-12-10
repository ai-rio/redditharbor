# Loader Comparison Test Fixes - Task 3.3 Report

## Executive Summary

Successfully debugged and fixed all 20 failing tests in `test_loader_comparison.py`. The test suite now verifies behavioral consistency between PostgresLoader and SQLModelLoader implementations.

**Final Result:** ✅ 20/20 tests passing

## Root Cause Analysis

### 1. Missing Dependencies
**Issue:** `sqlmodel` package not installed in virtual environment
**Fix:** Installed using `uv pip install sqlmodel`

### 2. PostgresLoader Missing `get_opportunity` Method
**Issue:** Tests assumed both loaders had retrieval capability
**Root Cause:** PostgresLoader only had `save_opportunity`, not `get_opportunity`
**Fix:** Implemented `get_opportunity` method in PostgresLoader with proper SQL query and object reconstruction

```python
def get_opportunity(self, submission_id: str):
    """Retrieve opportunity by submission_id from PostgreSQL"""
    # Implemented full SELECT query with proper type conversion
```

### 3. Missing Input Validation
**Issue:** PostgresLoader didn't validate inputs before database operations
**Root Cause:** No validation layer, allowed invalid data to reach database
**Fix:** Added `_validate_opportunity` method to PostgresLoader matching SQLModelLoader's validation

```python
def _validate_opportunity(self, opportunity: Opportunity) -> None:
    """Validate submission_id, trust_level, and data structures"""
```

### 4. SQLAlchemy Session Detachment Errors
**Issue:** `DetachedInstanceError` when accessing Opportunity attributes outside session context
**Root Cause:** SQLModel objects were detached from session before attributes were loaded
**Fix:** Eagerly load all attributes before `session.expunge()` to prevent lazy loading errors

```python
# Access all attributes to load them BEFORE detaching
_ = (opp.id, opp.submission_id, opp.subreddit, opp.title,
     opp.wtp_score, opp.final_score, opp.confidence_score,
     opp.trust_level, opp.analysis, opp.metrics,
     opp.created_at, opp.updated_at)
session.expunge(opp)  # Now safe to detach
```

### 5. Database Cleanup Issues
**Issue:** Tests failing due to duplicate records from previous test runs
**Root Cause:** Fixture only cleaned database AFTER tests, not BEFORE
**Fix:** Modified `clean_test_database` fixture to clean both before and after each test

```python
@pytest.fixture(scope="function", autouse=True)
def clean_test_database():
    # Clean BEFORE test
    # ... cleanup code ...
    yield
    # Clean AFTER test
    # ... cleanup code ...
```

### 6. Incorrect Test Logic - Trust Level Validation
**Issue:** Test expected `save_opportunity` to raise ValueError, but error raised during object creation
**Root Cause:** Opportunity model validates in `__init__`, not during save
**Fix:** Updated test to expect ValueError during Opportunity instantiation

```python
# Changed from:
opportunity = Opportunity(**invalid_data)
with pytest.raises(ValueError):
    loader.save_opportunity(opportunity)

# To:
with pytest.raises(ValueError):
    opportunity = Opportunity(**invalid_data)
```

### 7. Incorrect Test Logic - Duplicate Detection
**Issue:** Tests expected both loaders to succeed with same submission_id
**Root Cause:** Both loaders share the same database - duplicates should be detected across loaders
**Fix:** Updated test expectations to reflect shared database reality

```python
# test_duplicate_across_loaders now expects:
postgres_save = postgres_loader.save_opportunity(opp)  # True
sqlmodel_save = sqlmodel_loader.save_opportunity(opp)  # False (duplicate)
```

### 8. Missing `wtp_score` in Test Data
**Issue:** Database NOT NULL constraint violation for `wtp_score` column
**Root Cause:** Test was creating Opportunity without required `wtp_score` field
**Fix:** Added `wtp_score` parameter to all test opportunity creations

### 9. Connection Error Handling Test Issues
**Issue:** Mock patching strategy didn't work with context managers
**Root Cause:** Tests were patching the wrong layer (method instead of connection/session)
**Fix:** Updated mocking to patch connection pool and session creation

## Code Changes Summary

### Files Modified:

1. **pipeline-v4/load/postgres_loader.py**
   - Added `_validate_opportunity` method
   - Implemented `get_opportunity` method
   - Fixed imports after linting

2. **pipeline-v4/load/sqlmodel_loader.py**
   - Fixed session detachment by eagerly loading attributes
   - Applied eager loading to all retrieval methods
   - Fixed imports and formatting

3. **pipeline-v4/tests/test_loader_comparison.py**
   - Fixed database cleanup fixture
   - Corrected trust level validation test
   - Fixed duplicate detection test expectations
   - Added missing `wtp_score` parameters
   - Fixed connection error mocking
   - Updated test logic to use unique submission_ids
   - Removed unused `clean_test_data` context manager dependencies

## Test Coverage

All 20 tests now verify:

### Basic Functionality (4 tests)
- ✅ Loader initialization
- ✅ Model validation
- ✅ Save/retrieve basic flow

### Consistency (6 tests)
- ✅ Identical persistence behavior
- ✅ Duplicate detection (within loader)
- ✅ Duplicate detection (across loaders)
- ✅ JSON serialization
- ✅ Timestamp handling
- ✅ Final score calculation

### Error Handling (3 tests)
- ✅ Empty submission_id validation
- ✅ Invalid trust level validation
- ✅ Database connection errors

### Performance (3 tests)
- ✅ Single save performance
- ✅ Batch save performance
- ✅ Memory usage comparison

### Transaction Behavior (2 tests)
- ✅ Transaction commits
- ✅ Concurrent safety

### Data Integrity (2 tests)
- ✅ Round-trip consistency
- ✅ Database state consistency

## Prevention Recommendations

1. **Pre-commit Hooks:** Add database schema validation
2. **CI/CD:** Ensure test database is clean before each test run
3. **Documentation:** Document session management patterns for SQLModel
4. **Type Safety:** Add mypy checks for Optional types
5. **Test Data Factories:** Create centralized test data generators with all required fields

## Performance Notes

- Tests complete in ~1.6-2.0 seconds
- Both loaders show comparable performance
- No significant memory differences detected
- Database cleanup adds minimal overhead

## Compliance

✅ Follows project testing standards (80%+ coverage)
✅ Uses pytest as specified
✅ Handles dependency fallbacks
✅ Proper error handling for external calls
✅ Code formatted with ruff
