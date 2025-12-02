# ID Resolution Fix - Acceptance Criteria

**Version**: 1.0
**Last Updated**: 2025-11-23
**Status**: Active

---

## Overview

This document defines the acceptance criteria for the ID Resolution Fix workflow. All criteria must be met before the fix is considered complete and ready for production.

---

## Phase-by-Phase Acceptance Criteria

### Phase 1: Audit (01-audit.md)

| Criteria | Status | Evidence Required |
|----------|--------|-------------------|
| All Priority 1 files examined | [ ] | Report Section 3 |
| At least 80% of Priority 2-5 files examined | [ ] | Report Section 3 |
| All grep patterns executed | [ ] | Report Section 2 |
| ID Field Usage Matrix complete | [ ] | Report Section 2 |
| Mismatch Summary Table complete | [ ] | Report Section 5 |
| Risk assessment applied to all findings | [ ] | Report Section 6 |

**Deliverable**: `docs/id-resolution-fix/reports/01-audit-report.md`

---

### Phase 2: Design (02-design.md)

| Criteria | Status | Evidence Required |
|----------|--------|-------------------|
| Architecture diagram present | [ ] | Report Section 2 |
| Interface definition complete with types | [ ] | Report Section 3 |
| Resolution logic flowchart present | [ ] | Report Section 4 |
| Integration points matrix complete | [ ] | Report Section 5 |
| Migration strategy with phases defined | [ ] | Report Section 6 |
| Test specifications defined | [ ] | Report Section 7 |
| No code implementation (design only) | [ ] | Manual review |

**Deliverable**: `docs/id-resolution-fix/reports/02-design-report.md`

---

### Phase 3: Implement (03-implement.md)

| Criteria | Status | Evidence Required |
|----------|--------|-------------------|
| `core/utils/id_resolver.py` exists | [ ] | File presence |
| `core/utils/__init__.py` exports resolver | [ ] | Import test |
| `tests/test_id_resolver.py` exists | [ ] | File presence |
| All 15+ test cases implemented | [ ] | pytest output |
| All unit tests pass | [ ] | `pytest tests/test_id_resolver.py -v` |
| ruff format passes | [ ] | `ruff format --check` |
| ruff lint passes | [ ] | `ruff check` |
| Same input produces same UUID (determinism) | [ ] | UT-011 test |
| No database connection required | [ ] | Tests run offline |

**Deliverables**:
- `core/utils/id_resolver.py`
- `tests/test_id_resolver.py`
- `docs/id-resolution-fix/reports/03-implement-report.md`

---

### Phase 4: Integrate (04-integrate.md)

| Criteria | Status | Evidence Required |
|----------|--------|-------------------|
| `database_verifier.py` imports resolver | [ ] | Code review |
| `database_verifier.py` uses resolver in verify_submission_storage | [ ] | Code review |
| `enhanced_hybrid_store.py` delegates to resolver | [ ] | Code review |
| Integration tests created | [ ] | File presence |
| All integration tests pass | [ ] | pytest output |
| No regression in existing tests | [ ] | Full test suite |
| Test 02 shows improvement | [ ] | Test output |

**Deliverables**:
- Modified `scripts/testing/integration/utils/database_verifier.py`
- Modified `core/storage/enhanced_hybrid_store.py`
- `tests/test_id_resolver_integration.py`
- `docs/id-resolution-fix/reports/04-integrate-report.md`

---

### Phase 5: Enforce (05-enforce.md)

| Criteria | Status | Evidence Required |
|----------|--------|-------------------|
| UP migration file exists | [ ] | File presence |
| DOWN migration file exists | [ ] | File presence |
| PostgreSQL uuid5 matches Python | [ ] | Test parity |
| Trigger fires on INSERT | [ ] | Test evidence |
| Trigger fires on UPDATE | [ ] | Test evidence |
| Valid UUIDs pass through unchanged | [ ] | Test evidence |
| Migration is reversible | [ ] | Rollback test |
| All database tests pass | [ ] | pytest output |

**Deliverables**:
- `supabase/migrations/YYYYMMDDHHMMSS_add_id_normalization_trigger.sql`
- `supabase/migrations/YYYYMMDDHHMMSS_revert_id_normalization_trigger.sql`
- `scripts/database/test_id_normalization_trigger.py`
- `docs/id-resolution-fix/reports/05-enforce-report.md`

---

### Phase 6: Validate (06-validate.md)

| Criteria | Status | Evidence Required |
|----------|--------|-------------------|
| All unit tests pass (100%) | [ ] | pytest output |
| All integration tests pass | [ ] | pytest output |
| Test 01 passes (no regression) | [ ] | Test output |
| Test 02 passes with >90% coverage | [ ] | Test output |
| Database verification matches pipeline | [ ] | Verification logs |
| Full test suite passes | [ ] | pytest output |
| Validation report complete | [ ] | Report presence |

**Deliverable**: `docs/id-resolution-fix/reports/06-validate-report.md`

---

## Critical Success Metrics

### Primary Metric: Test 02 Field Coverage

| Metric | Before Fix | Target | Actual |
|--------|------------|--------|--------|
| Field Coverage | 0% | >90% | ___% |

### Secondary Metrics

| Metric | Before | Target | Actual |
|--------|--------|--------|--------|
| Database Verification | FAIL | PASS | ____ |
| Storage Success Rate | 0% | >90% | ___% |
| ID Format Consistency | Mixed | UUID | ____ |
| Test Suite Pass Rate | ~80% | 100% | ___% |

---

## Non-Functional Requirements

### Performance
- [ ] No measurable performance regression (resolver adds <1ms per call)
- [ ] Database trigger adds <5ms per INSERT/UPDATE

### Backwards Compatibility
- [ ] Existing data not modified
- [ ] Existing tests still pass
- [ ] DLT pipeline continues to work

### Maintainability
- [ ] Single source of truth for ID resolution
- [ ] Documented design decisions
- [ ] Test coverage >90% for resolver

### Security
- [ ] No new security vulnerabilities introduced
- [ ] UUID generation is deterministic and predictable

---

## Sign-Off Checklist

### Technical Review
- [ ] Code reviewed by human developer
- [ ] All tests verified to pass
- [ ] Database state verified

### Documentation Review
- [ ] All reports completed
- [ ] All phases documented
- [ ] Acceptance criteria filled in

### Approval
- [ ] Ready for merge to main branch
- [ ] No outstanding issues

---

## Rollback Checklist

If the fix needs to be reverted:

1. [ ] Run DOWN migration to remove database trigger
2. [ ] Revert `database_verifier.py` changes
3. [ ] Revert `enhanced_hybrid_store.py` changes
4. [ ] Keep `core/utils/id_resolver.py` (no harm in having it)
5. [ ] Run full test suite to verify rollback
6. [ ] Document reason for rollback

---

## Workflow Summary

```
00-context.md (Problem Statement)
       |
       v
01-audit.md ──> 01-audit-report.md
       |
       v
02-design.md ──> 02-design-report.md
       |
       v
03-implement.md ──> 03-implement-report.md
       |                    |
       v                    v
04-integrate.md ──> 04-integrate-report.md
       |                    |
       v                    v
05-enforce.md ──> 05-enforce-report.md
       |                    |
       v                    v
06-validate.md ──> 06-validate-report.md
       |
       v
ACCEPTANCE CRITERIA MET ──> MERGE TO MAIN
```

---

## Contact

For questions about this workflow:
- Primary: Human supervisor (QA/review role)
- Executor: Partner AI agent
- Escalation: Create issue in repository

---

**Document End**
