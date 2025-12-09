# Test Suite: end_analysis_session() Method

This directory contains comprehensive failing unit tests for the `end_analysis_session()` method in `transform/agno_analyzer.py`.

## Overview

These tests follow Test-Driven Development (TDD) principles and are designed to fail initially since the `end_analysis_session()` method doesn't exist yet. Each test file represents a specific scenario from the test specification.

## Test Files

### TC-001: Basic Method Existence
- **File**: `test_end_analysis_session_tc001.py`
- **Purpose**: Verify that the `end_analysis_session` method exists on the `AgnoOpportunityAnalyzer` class
- **Expected Failure**: `AttributeError: 'AgnoOpportunityAnalyzer' object has no attribute 'end_analysis_session'`

### TC-002: Session End with Success Status
- **File**: `test_end_analysis_session_tc002.py`
- **Purpose**: Test ending a session with "success" status
- **Expected Failure**: `AttributeError: 'AgnoOpportunityAnalyzer' object has no attribute 'end_analysis_session_async'`

### TC-003: Session End with Error Status
- **File**: `test_end_analysis_session_tc003.py`
- **Purpose**: Test ending a session with "error" status and error message
- **Expected Failure**: `AttributeError: 'AgnoOpportunityAnalyzer' object has no attribute 'end_analysis_session_async'`

### TC-004: Session End with Custom Tags
- **File**: `test_end_analysis_session_tc004.py`
- **Purpose**: Test ending a session with custom tags
- **Expected Failure**: `AttributeError: 'AgnoOpportunityAnalyzer' object has no attribute 'end_analysis_session_async'`

### TC-005: Session End without Active Session
- **File**: `test_end_analysis_session_tc005.py`
- **Purpose**: Test ending a session when no active session exists
- **Expected Failure**: `AttributeError: 'AgnoOpportunityAnalyzer' object has no attribute 'end_analysis_session_async'`

### TC-006: Session End with Missing Status
- **File**: `test_end_analysis_session_tc006.py`
- **Purpose**: Test ending a session without providing status parameter
- **Expected Failure**: `AttributeError: 'AgnoOpportunityAnalyzer' object has no attribute 'end_analysis_session_async'`

### TC-007: Session End Return Value
- **File**: `test_end_analysis_session_tc007.py`
- **Purpose**: Test that the method returns proper session summary
- **Expected Failure**: `AttributeError: 'AgnoOpportunityAnalyzer' object has no attribute 'end_analysis_session_async'`

### TC-008: Session End Error Handling
- **File**: `test_end_analysis_session_tc008.py`
- **Purpose**: Test error handling when tracker fails
- **Expected Failure**: `AttributeError: 'AgnoOpportunityAnalyzer' object has no attribute 'end_analysis_session_async'`

## Running Tests

### Run Individual Tests
```bash
# Run TC-001 (synchronous method test)
python tests/transform/test_end_analysis_session_tc001.py

# Run TC-002 through TC-008 (async method tests)
python -c "
import asyncio
from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').absolute()))

# Add individual test imports here
"
```

### Run All Tests
```bash
# Test that all tests fail as expected
for i in {001..008}; do
    echo -e "\n=== Running TC-$i ==="
    python tests/transform/test_end_analysis_session_tc$i.py || echo "Failed as expected"
done
```

### Using pytest
```bash
# Run all tests with pytest (when implemented)
pytest tests/transform/test_end_analysis_session_tc*.py -v
```

## Test Coverage

The test suite covers the following requirements:

1. **Method Existence**: Both sync and async versions of the method
2. **Status Handling**: Success, error, and default status scenarios
3. **Parameters**: Required (status) and optional (error_message, tags) parameters
4. **Error Conditions**: No active session, missing status, tracker failures
5. **Return Values**: Session summary with proper structure
6. **Edge Cases**: Custom tags, error message passing, missing parameters

## TDD Implementation Plan

1. **RED**: All tests currently fail as expected
2. **GREEN**: Implement minimal code to make one test pass at a time
3. **REFACTOR**: Improve implementation while maintaining all tests passing

### Implementation Order
1. Start with TC-001 (basic method existence)
2. Implement TC-002 and TC-003 (basic success/error scenarios)
3. Add TC-004 through TC-006 (parameter handling)
4. Implement TC-007 (return values)
5. Add TC-008 (error handling)

## Expected Method Signature

```python
# Synchronous version
def end_analysis_session(self, status: str, error_message: str = None, tags: List[str] = None) -> Dict[str, Any]:
    pass

# Asynchronous version
async def end_analysis_session_async(self, status: str = None, error_message: str = None, tags: List[str] = None) -> Dict[str, Any]:
    pass
```

## Mock Fixtures

Each test uses mock AgentOps trackers to simulate:
- Session end calls
- Error scenarios
- Return value expectations
- Custom parameter passing

## Success Criteria

All tests should:
- Initially fail with AttributeError (method doesn't exist)
- Pass after implementation with proper behavior
- Maintain backward compatibility
- Handle edge cases gracefully
- Provide proper return values