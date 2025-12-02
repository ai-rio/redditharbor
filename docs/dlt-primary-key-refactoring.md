# DLT Primary Key Refactoring Documentation

## Overview

This document describes the comprehensive refactoring of DLT (Data Load Tool) primary key dependencies to support Phase 3 schema consolidation. The refactoring removes hard-coded primary key strings that would break DLT merge logic when database columns are renamed.

## Problem Statement

**Critical Issue**: Hard-coded primary key strings in 4+ DLT resources create dependencies that break schema consolidation.

**Impact**: Renaming primary keys breaks DLT merge logic, creates data duplicates, and prevents safe schema evolution.

**Solution**: Centralized primary key management with type-safe constants.

## Changes Made

### 1. Created Centralized Constants Module

**File**: `core/dlt/constants.py`

**Features**:
- Single source of truth for all primary key constants
- Type-safe validation with runtime checks
- Resource and table mapping dictionaries
- Legacy migration support
- Merge disposition compatibility validation

**Primary Key Constants**:
```python
PK_SUBMISSION_ID: Final[str] = "submission_id"
PK_OPPORTUNITY_ID: Final[str] = "opportunity_id"
PK_COMMENT_ID: Final[str] = "comment_id"
PK_DISPLAY_NAME: Final[str] = "display_name"
PK_ID: Final[str] = "id"
```

### 2. Refactored DLT Resources

#### Core DLT Resources

1. **`core/dlt_app_opportunities.py`**
   - Replaced `primary_key="submission_id"` → `primary_key=PK_SUBMISSION_ID`
   - Updated pipeline.run() call to use constant

2. **`core/dlt_collection.py`**
   - Replaced `primary_key="submission_id"` → `primary_key=PK_SUBMISSION_ID`
   - Updated documentation references

3. **`core/dlt_cost_tracking.py`**
   - Replaced `primary_key="opportunity_id"` → `primary_key=PK_OPPORTUNITY_ID`
   - Updated pipeline configuration

4. **`core/dlt_reddit_source.py`**
   - Replaced `primary_key="display_name"` → `primary_key=PK_DISPLAY_NAME`
   - Replaced `primary_key="id"` → `primary_key=PK_ID`

#### Script DLT Resources

5. **`scripts/dlt/dlt_opportunity_pipeline.py`**
   - Replaced `primary_key="submission_id"` → `primary_key=PK_SUBMISSION_ID`

6. **`scripts/dlt/dlt_trust_pipeline.py`**
   - Replaced `primary_key="submission_id"` → `primary_key=PK_SUBMISSION_ID`

### 3. Package Structure

**File**: `core/dlt/__init__.py`

- Exports all constants and utility functions
- Provides convenient imports for DLT modules
- Maintains backward compatibility

## Usage Patterns

### Basic Import Pattern

```python
from core.dlt import PK_SUBMISSION_ID, PK_OPPORTUNITY_ID, validate_primary_key
```

### DLT Resource Definition

```python
import dlt
from core.dlt import PK_SUBMISSION_ID

@dlt.resource(
    name="my_resource",
    write_disposition="merge",
    primary_key=PK_SUBMISSION_ID
)
def my_resource(data):
    yield data
```

### Pipeline Configuration

```python
from core.dlt import PK_SUBMISSION_ID, submission_resource_config

# Get standard configuration
config = submission_resource_config("merge")
# config = {"write_disposition": "merge", "primary_key": PK_SUBMISSION_ID}

# Use in pipeline
pipeline.run(data, **config)
```

### Validation

```python
from core.dlt import validate_primary_key, PrimaryKeyType

# Validate primary key
validate_primary_key("submission_id")  # Returns True

# Validate with expected type
validate_primary_key("submission_id", PrimaryKeyType.SUBMISSION_ID)  # Returns True

# Invalid validation
validate_primary_key("invalid_key")  # Raises ValueError
```

## Resource and Table Mappings

### DLT Resource Primary Keys

```python
DLT_RESOURCE_PK_MAP = {
    "app_opportunities": PK_SUBMISSION_ID,
    "app_opportunities_trust": PK_SUBMISSION_ID,
    "opportunity_analysis": PK_SUBMISSION_ID,
    "workflow_results_with_costs": PK_OPPORTUNITY_ID,
    "active_subreddits": PK_DISPLAY_NAME,
    "validated_comments": PK_ID,
    "activity_trends": PK_DISPLAY_NAME,
    "submissions": PK_SUBMISSION_ID,
    "comments": PK_COMMENT_ID,
}
```

### Table Primary Keys

```python
TABLE_PRIMARY_KEYS = {
    "submissions": PK_SUBMISSION_ID,
    "comments": PK_COMMENT_ID,
    "redditors": PK_ID,
    "app_opportunities": PK_SUBMISSION_ID,
    "opportunity_analysis": PK_SUBMISSION_ID,
    "workflow_results": PK_OPPORTUNITY_ID,
    "active_subreddits": PK_DISPLAY_NAME,
    "activity_trends": PK_DISPLAY_NAME,
    "validated_comments": PK_ID,
}
```

## Migration Guide

### For Existing Code

1. **Replace Hard-coded Strings**:
   ```python
   # Before
   primary_key="submission_id"

   # After
   from core.dlt import PK_SUBMISSION_ID
   primary_key=PK_SUBMISSION_ID
   ```

2. **Use Resource Configuration Functions**:
   ```python
   # Before
   config = {"write_disposition": "merge", "primary_key": "submission_id"}

   # After
   from core.dlt import submission_resource_config
   config = submission_resource_config("merge")
   ```

3. **Add Validation**:
   ```python
   from core.dlt import validate_primary_key, get_resource_primary_key

   # Validate primary key before use
   validate_primary_key(primary_key)

   # Get resource primary key by name
   pk = get_resource_primary_key("app_opportunities")
   ```

### For Schema Consolidation

1. **Update Primary Key Constants**:
   ```python
   # In core/dlt/constants.py
   PK_SUBMISSION_ID = "new_submission_id"  # Changed from "submission_id"
   ```

2. **All DLT Resources Automatically Updated**:
   - No need to update individual resource files
   - All merge dispositions remain functional
   - No breaking changes to existing code

3. **Database Migration**:
   - Run database migration to rename columns
   - Update application code to use new column names
   - DLT resources automatically use new primary key

## Testing

### Comprehensive Test Suite

**File**: `tests/test_dlt_primary_key_refactoring.py`

**Test Categories**:
1. **Constant Validation**: Ensure all constants are defined and unique
2. **Function Testing**: Test validation, migration, and lookup functions
3. **Integration Testing**: Verify DLT resources use constants correctly
4. **Backward Compatibility**: Ensure legacy code still works
5. **Type Safety**: Validate type hints and runtime checks
6. **Performance**: Ensure efficient imports and validations

### Running Tests

```bash
pytest tests/test_dlt_primary_key_refactoring.py -v
```

### Manual Validation

```python
# Test basic functionality
from core.dlt import PK_SUBMISSION_ID, validate_primary_key

print(f"PK_SUBMISSION_ID: {PK_SUBMISSION_ID}")
print(f"Validation result: {validate_primary_key(PK_SUBMISSION_ID)}")
```

## Benefits

### 1. Eliminates Hard-coded Dependencies
- Single source of truth for primary key names
- Easy to rename primary keys across all DLT resources
- No risk of missed updates during schema changes

### 2. Type Safety and Validation
- Runtime validation of primary key strings
- Type hints for static analysis
- Clear error messages for invalid configurations

### 3. Maintainability
- Centralized management reduces maintenance overhead
- Clear documentation of primary key usage
- Easy to add new resources and tables

### 4. Backward Compatibility
- Legacy migration support for existing code
- Gradual migration path for hard-coded strings
- No breaking changes to existing functionality

### 5. Schema Consolidation Support
- Enables safe primary key renaming
- Maintains DLT merge disposition functionality
- Prevents data duplication during schema evolution

## Future Enhancements

### 1. Dynamic Primary Key Discovery
- Automatic detection of primary keys from database schema
- Runtime validation against actual database structure

### 2. Multi-Column Primary Keys
- Support for composite primary keys
- Enhanced validation for complex schemas

### 3. Migration Tools
- Automated migration scripts for legacy code
- CLI tools for bulk updates

### 4. Performance Optimization
- Caching of validation results
- Lazy loading of resource configurations

## Rollback Plan

If issues arise with the refactoring:

1. **Immediate Rollback**: Restore hard-coded strings in affected files
2. **Gradual Migration**: Revert to constants module while maintaining backward compatibility
3. **Partial Rollback**: Keep constants module but revert specific resource changes

## Conclusion

This refactoring successfully addresses the critical DLT Merge Disposition Dependencies issue identified in Phase 3 schema consolidation. By centralizing primary key management, we enable safe schema evolution while maintaining all existing functionality.

The solution provides:
- ✅ Removal of hard-coded primary key dependencies
- ✅ Type-safe constants with runtime validation
- ✅ Backward compatibility for existing code
- ✅ Comprehensive testing and validation
- ✅ Clear migration path for schema consolidation

This refactoring enables the safe renaming of primary keys during schema consolidation without breaking DLT merge logic or creating data duplicates.