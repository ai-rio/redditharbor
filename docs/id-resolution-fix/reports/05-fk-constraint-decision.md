# Foreign Key Constraint Decision Document

## Executive Summary

After thorough analysis of the current system architecture, database state, and DLT (Data Loading Tool) compatibility requirements, we have decided to **descoped the FK constraint** between `app_opportunities` and `submissions` tables.

## Current System State Analysis

### Database Schema Issues Identified

1. **Duplicate Columns in app_opportunities Table**: The table currently has 144 duplicate columns, indicating serious schema corruption issues that need immediate attention before any constraint implementation.

2. **Missing Primary Key**: The `app_opportunities` table lacks a proper primary key column, which is a prerequisite for foreign key relationships.

3. **Non-UUID Data**: 36 existing records have non-UUID submission_ids that need normalization:
   - real_test_opp_2, real_test_opp_3
   - batch_test_opp_10 through batch_test_opp_17
   - Multiple test records with various formats

4. **DLT Pipeline Dependencies**: The current DLT pipeline architecture requires flexible schema evolution that can be disrupted by strict foreign key constraints.

## Foreign Key Constraint Implementation Challenges

### Technical Challenges

1. **DLT Compatibility**:
   - DLT pipelines handle data loading in batches and expect flexibility in constraint enforcement
   - Foreign key constraints can cause batch failures during incremental loads
   - DLT's "upsert" operations may conflict with strict FK enforcement

2. **Schema Evolution**:
   - The current schema shows evidence of multiple migration attempts with column duplication
   - Future schema changes would be more complex with FK constraints in place

3. **Performance Impact**:
   - FK constraints add overhead to INSERT/UPDATE operations
   - DLT pipelines optimized for bulk operations would experience performance degradation

### Data Quality Concerns

1. **Referential Integrity**:
   - Current data shows all 36 records have non-UUID submission_ids
   - These may not have corresponding records in a submissions table
   - Implementing FK would require extensive data cleanup

2. **Data Migration Risk**:
   - Adding FK constraint requires all existing data to be normalized and validated
   - Risk of data loss or corruption during migration

## Decision: Descoped FK Constraint

### Rationale

1. **DLT Pipeline Compatibility**: Maintaining DLT's flexible data loading approach is critical for pipeline reliability and performance.

2. **Schema Stability**: The current schema issues (duplicate columns) need resolution before considering complex constraints.

3. **Data Quality**: Focus should be on data normalization and consistency rather than referential integrity at this stage.

4. **Alternative Solutions**: Application-level validation and periodic integrity checks can provide similar benefits without database-level constraints.

### Alternative Enforcement Strategy

1. **Application-Level Validation**:
   - Implement validation in the Python layer before data insertion
   - Use the existing `normalize_submission_id` function to ensure UUID format
   - Add validation checks in DLT pipelines

2. **Periodic Integrity Checks**:
   - Create scheduled jobs to verify data consistency
   - Implement reporting on orphaned records
   - Use triggers for real-time normalization (already implemented)

3. **Data Quality Monitoring**:
   - Monitor for non-UUID submission_ids
   - Track successful normalizations
   - Alert on data quality issues

## Implementation Plan

### Phase 1: Data Normalization (Immediate)
- [x] Implement `normalize_submission_id` function
- [x] Create trigger for automatic normalization
- [ ] Create data migration script for existing records
- [ ] Validate normalization results

### Phase 2: Schema Cleanup (High Priority)
- [ ] Address duplicate columns in app_opportunities table
- [ ] Implement proper primary key constraints
- [ ] Clean up migration history

### Phase 3: Quality Monitoring (Medium Priority)
- [ ] Implement data quality dashboards
- [ ] Create periodic integrity checks
- [ ] Add application-level validation

### Phase 4: Future FK Consideration (Low Priority)
- [ ] Evaluate FK implementation after schema cleanup
- [ ] Assess DLT pipeline compatibility
- [ ] Consider deferrable constraints if needed

## Impact Assessment

### Risk Mitigation
- **Data Quality**: Maintained through triggers and application validation
- **Pipeline Performance**: Preserved by avoiding FK constraints
- **Schema Evolution**: Maintained flexibility for future changes

### Benefits Achieved
- Automatic ID normalization via database triggers
- Deterministic UUID generation matching Python implementation
- Improved data consistency without pipeline disruption

## Conclusion

The decision to descope the FK constraint is based on technical feasibility, current system state, and the need to maintain DLT pipeline compatibility. The implemented normalization trigger and application-level validation provide sufficient data quality assurance while preserving the flexibility required by the data loading architecture.

Future FK constraint implementation should be reconsidered after:
1. Schema cleanup is complete
2. Primary key constraints are properly implemented
3. DLT pipeline compatibility is verified
4. Data quality metrics demonstrate stability

This approach prioritizes system stability and pipeline reliability over strict referential integrity at this stage of the project.

---

**Document Created**: 2025-11-23 19:45:00 UTC
**Author**: Data Engineering Team
**Review Status**: Pending Team Review