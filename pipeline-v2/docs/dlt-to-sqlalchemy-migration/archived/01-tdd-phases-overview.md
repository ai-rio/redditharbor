# TDD Phases Overview

## Introduction

This document outlines the practical TDD (Test-Driven Development) approach for migrating from DLT to SQLAlchemy. Each phase is designed for a solo developer with clear deliverables and validation steps.

## The TDD Methodology for This Migration

### Red-Green-Refactor Cycle

1. **RED**: Write failing tests that expose current DLT problems
2. **GREEN**: Implement SQLAlchemy solution to make tests pass
3. **REFACTOR**: Clean up and optimize the implementation

### Key Principles

- **Characterize Before Changing**: Document exact current behavior
- **Test Critical Paths**: Focus on data integrity and transaction safety
- **Parallel Validation**: Run both systems during transition
- **Rollback Ready**: Every step must be reversible

## Phase 1: Foundation (1-2 days)

### Objectives
- Document current DLT behavior and failure modes
- Set up SQLAlchemy foundation with ID resolution integration
- Create test infrastructure for migration validation

### Deliverables

#### 1.1 Characterization Tests
**File**: `pipeline-v2/tests/test_dlt_characterization.py`

**Purpose**: Document exactly how DLT behaves today, including:
- Connection validation behavior
- Load success reporting vs actual database state
- Error handling characteristics
- Silent failure confirmation

**Key Tests**:
```python
def test_dlt_silent_failure_investigation(self):
    """Confirm DLT reports success but database receives no data"""

def test_dlt_connection_validation(self):
    """Document DLT's connection validation behavior"""

def test_dlt_error_reporting(self):
    """Characterize DLT's error handling"""
```

#### 1.2 SQLAlchemy Foundation
**File**: `pipeline-v2/storage/sqlalchemy_loader.py`

**Core Components**:
- SQLAlchemy engine with optimized connection settings
- ID resolution system integration (`resolve_submission_id()`)
- Basic transaction control framework
- Connection validation and table existence checks

**Success Criteria**:
- ✅ SQLAlchemy connects to PostgreSQL successfully
- ✅ Target table `app_opportunities` exists and accessible
- ✅ ID resolution system working for Reddit IDs
- ✅ Basic transaction structure in place

### Validation Steps

1. **Run DLT Characterization Tests**:
   ```bash
   pytest pipeline-v2/tests/test_dlt_characterization.py -v
   ```

2. **Document Silent Failure Evidence**:
   - Capture test logs showing DLT reports success but no database changes
   - Record connection port conflicts and resolution attempts
   - Document error handling inconsistencies

3. **Verify SQLAlchemy Foundation**:
   ```bash
   python -c "
   from storage.sqlalchemy_loader import create_sqlalchemy_loader
   loader = create_sqlalchemy_loader()
   print('Connection valid:', loader.validate_connection())
   print('Stats:', loader.get_load_statistics())
   "
   ```

## Phase 2: Implementation (3-5 days)

### Objectives
- Build complete SQLAlchemy loader with explicit transaction control
- Implement DLT compatibility adapter for backwards compatibility
- Create comprehensive test suite for all SQLAlchemy functionality

### Deliverables

#### 2.1 Complete SQLAlchemy Loader
**File**: `pipeline-v2/storage/sqlalchemy_loader.py` (complete)

**Core Features**:
```python
class SQLAlchemyLoader:
    def load_opportunities(self, opportunities, **kwargs):
        with self.get_session() as session:
            with session.begin():  # Explicit transaction control
                # Prepare data with ID resolution
                prepared = self.prepare_opportunity_data(opportunities)

                # Execute with verification
                result = self._merge_opportunities(session, prepared)

                # Verify actual data persistence
                verification_count = self._verify_load_operation(session, prepared)
                assert verification_count == len(prepared)

                # Explicit commit on success
                # Automatic rollback on exception
```

**Key Methods**:
- `prepare_opportunity_data()` - ID resolution and data mapping
- `load_opportunities()` - Main loading with explicit transactions
- `_merge_opportunities()` - Upsert logic with verification
- `_verify_load_operation()` - Confirm data was actually persisted

#### 2.2 DLT Compatibility Adapter
**File**: `pipeline-v2/storage/dlt_compatibility_adapter.py`

**Purpose**: Maintain existing code interfaces while gaining SQLAlchemy reliability

```python
class DLTCompatibilityAdapter:
    def run(self, data, **kwargs):
        # DLT-like interface using SQLAlchemy backend
        result = self.loader.load_opportunities(data, **kwargs)

        # Convert to DLT-like LoadInfo object
        return SimpleNamespace(
            load_id=result.load_id,
            counts={"app_opportunities": result.records_inserted},
            success=result.success
        )
```

#### 2.3 Comprehensive Test Suite
**File**: `pipeline-v2/tests/test_sqlalchemy_loader.py`

**Critical Test Categories**:

1. **Explicit Success/Failure Tests**:
   ```python
   def test_explicit_success_behavior(self):
       """SQLAlchemy provides clear success feedback"""

   def test_explicit_failure_behavior(self):
       """SQLAlchemy provides clear failure feedback"""
   ```

2. **Transaction Control Tests**:
   ```python
   def test_transaction_rollback_behavior(self):
       """Failed transactions properly roll back"""
   ```

3. **Data Integrity Tests**:
   ```python
   def test_merge_disposition_behavior(self):
       """Upsert logic works correctly"""

   def test_id_resolution_integration(self):
       """Reddit IDs properly resolved to UUIDs"""
   ```

### Validation Steps

1. **Run SQLAlchemy Tests**:
   ```bash
   pytest pipeline-v2/tests/test_sqlalchemy_loader.py -v
   ```

2. **Verify Transaction Behavior**:
   - Test success cases with database verification
   - Test failure cases with explicit rollback confirmation
   - Validate merge vs append vs replace dispositions

3. **Test DLT Compatibility**:
   ```bash
   python -c "
   from storage.dlt_compatibility_adapter import create_dlt_compatible_loader
   loader = create_dlt_compatible_loader()
   # Should work exactly like DLT loader but with SQLAlchemy backend
   "
   ```

## Phase 3: Validation (2-3 days)

### Objectives
- Run parallel tests comparing DLT and SQLAlchemy side-by-side
- Validate data consistency and performance characteristics
- Confirm migration eliminates silent failures

### Deliverables

#### 3.1 Parallel Testing Framework
**File**: `pipeline-v2/tests/test_migration_parallel.py`

**Purpose**: Direct comparison between DLT and SQLAlchemy implementations

**Key Tests**:
```python
def test_parallel_data_consistency(self):
    """Both implementations handle same data consistently"""

def test_error_handling_comparison(self):
    """Compare error handling between implementations"""

def test_performance_comparison(self):
    """Validate reasonable performance characteristics"""
```

#### 3.2 Migration Validation Report
**File**: `pipeline-v2/docs/migration-validation-report.md`

**Contents**:
- Silent failure confirmation evidence
- Data consistency validation results
- Performance comparison metrics
- Error handling improvement documentation

### Validation Steps

1. **Run Parallel Tests**:
   ```bash
   pytest pipeline-v2/tests/test_migration_parallel.py -v -s
   ```

2. **Document Silent Fixation**:
   - Capture evidence of DLT silent failures
   - Document SQLAlchemy explicit success/failure behavior
   - Record performance comparisons

3. **Data Integrity Validation**:
   - Verify same input data produces equivalent results
   - Confirm no data loss during migration
   - Validate ID resolution consistency

## Phase 4: Migration (1-2 days)

### Objectives
- Safe cutover from DLT to SQLAlchemy
- Monitoring and rollback preparation
- Documentation updates

### Deliverables

#### 4.1 Migration Script
**File**: `pipeline-v2/scripts/migrate_to_sqlalchemy.py`

**Features**:
- Backup current data state
- Update configuration to use SQLAlchemy loader
- Validate migration success
- Rollback capability if issues arise

#### 4.2 Updated Configuration
**Files**: Update relevant config files to use SQLAlchemy loader by default

#### 4.3 Migration Documentation
**File**: Update existing docs to reflect SQLAlchemy implementation

### Validation Steps

1. **Pre-Migration Backup**:
   ```bash
   # Full database backup
   pg_dump -h 127.0.0.1 -p 54322 -U postgres postgres > backup_before_migration.sql
   ```

2. **Run Migration Script**:
   ```bash
   python pipeline-v2/scripts/migrate_to_sqlalchemy.py --dry-run
   python pipeline-v2/scripts/migrate_to_sqlalchemy.py --execute
   ```

3. **Post-Migration Validation**:
   - Verify all existing functionality works
   - Test data loading with sample data
   - Confirm no regression in performance

## Success Criteria Per Phase

### Phase 1 Success
- ✅ DLT silent failures documented with evidence
- ✅ SQLAlchemy foundation connects and validates successfully
- ✅ ID resolution system integrated
- ✅ Test infrastructure in place

### Phase 2 Success
- ✅ SQLAlchemy loader implements all required features
- ✅ DLT compatibility adapter maintains existing interfaces
- ✅ Comprehensive test suite passes
- ✅ Transaction control working explicitly

### Phase 3 Success
- ✅ Parallel tests confirm data consistency
- ✅ Performance comparable or better than DLT
- ✅ Error handling significantly improved
- ✅ No silent failures detected

### Phase 4 Success
- ✅ Migration completed without data loss
- ✅ All existing functionality preserved
- ✅ Performance acceptable in production
- ✅ Monitoring shows reliable operation

## Risk Mitigation Strategies

### High-Risk Areas
1. **Data Loss During Migration** - Mitigated by full backup and dry-run validation
2. **Transaction Rollback Regression** - Mitigated by comprehensive transaction testing
3. **Performance Degradation** - Mitigated by parallel performance testing
4. **Connection Pool Issues** - Mitigated by direct connection management

### Safety Mechanisms
- Every phase is independently testable
- Rollback capability at each stage
- Parallel testing during transition
- Comprehensive logging and monitoring

## Decision Points

### Go/No-Go Gates

1. **End of Phase 1**: Continue only if DLT silent failures confirmed
2. **End of Phase 2**: Continue only if SQLAlchemy tests pass completely
3. **End of Phase 3**: Continue only if parallel validation succeeds
4. **End of Phase 4**: Migration complete and validated

### Rollback Triggers
- Any data integrity issues detected
- Performance degradation beyond acceptable limits
- Unexpected error conditions in production
- Test failures that cannot be resolved

This TDD approach ensures a safe, validated migration while addressing the critical silent failure issue in the current DLT implementation.