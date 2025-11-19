# Function-Count Bias Investigation: Complete Documentation Index

**Investigation Date:** 2025-11-10
**Status:** Complete diagnosis, no code changes executed
**Finding:** Root cause is architectural fragmentation + schema mismatch, not profiler bias

---

## 📋 Document Roadmap

### 1. **One-Pager (Start Here)**
**File:** [`function-count-diagnosis-summary.md`](./function-count-diagnosis-summary.md)

**Purpose:** Executive summary, 5-minute read
- What's the problem?
- Why is it happening?
- Is the LLM profiler really to blame?
- What's the fix?

**Best For:** Quick understanding, management briefing, decision-making

---

### 2. **Detailed Technical Diagnosis**
**File:** [`diagnosis-function-count-bias.md`](./diagnosis-function-count-bias.md)

**Purpose:** Full forensic analysis, 30-minute deep dive
- Line-by-line code path tracing
- Each component investigated separately
- Data flow analysis
- Function count distribution analysis
- 7 detailed failure points identified
- 3 solution options with pros/cons

**Sections:**
- Executive Summary
- Pipeline Architecture & Data Flow
- Investigation by Component (6 detailed sections)
- Function Count Distribution Analysis
- Failure Points & Guardrail Gaps
- 3 Proposed Solutions (Options A, B, C)
- SQL Migration Plan with phases
- Acceptance Criteria (testable)
- Summary Table

**Best For:** Code review, architectural discussion, implementation planning

---

### 3. **Migration & Repair Plan**
**File:** [`function-count-migration-plan.md`](./function-count-migration-plan.md)

**Purpose:** Step-by-step implementation guide, 2–3 day project
- Phased approach (4 phases over 2–3 days)
- SQL migrations with data preservation
- Test cases (unit + integration)
- Rollback procedures
- Effort estimates

**Phases:**
1. **Immediate Guardrails** (2 hours)
   - Add validation function
   - Add assertions
   - No schema changes

2. **Schema Migration** (3 hours)
   - Add `function_list` to `workflow_results`
   - Backfill data safely
   - Optional: Add CHECK constraint

3. **Dashboard Update** (3 hours)
   - Update 3 marimo notebooks
   - Ensure correct table/column reads

4. **Consolidation** (Optional, next release)
   - Merge two tables into unified schema
   - Single source of truth

**Best For:** Implementation checklist, testing, deployment planning

---

### 4. **Data Flow Diagram & Schema Analysis**
**File:** [`function-count-data-flow-diagram.md`](./function-count-data-flow-diagram.md)

**Purpose:** Visual understanding of architecture, 10-minute read
- Full ASCII flow diagram of current pipeline
- Split point where data diverges into two tables
- Schema conflict matrix
- Historical context
- Code locations referenced in flow

**Diagrams:**
- Full pipeline flow with decision points
- Two-table divergence and data types
- Schema mismatch matrix
- Correct vs. current flow comparison

**Best For:** Understanding the "why", onboarding engineers, architecture review

---

## 🎯 How to Use These Documents

### Scenario 1: "I Need to Understand This Quickly"
1. Read: **One-Pager** (5 min)
2. Review: **Data Flow Diagram** (10 min)
3. Total: 15 minutes

### Scenario 2: "I Need to Fix This"
1. Read: **Migration Plan** (20 min)
2. Execute: Phase 1 (immediate guardrails)
3. Run: Test cases
4. Then decide: Phase 2+ later

### Scenario 3: "I Need to Review This Thoroughly"
1. Read: **One-Pager** (5 min)
2. Read: **Data Flow Diagram** (10 min)
3. Read: **Detailed Diagnosis** (30 min)
4. Review: **Migration Plan** (20 min)
5. Ask: Questions, request code review

### Scenario 4: "I Need to Explain This to My Team"
1. Present: **One-Pager** summary
2. Show: **Data Flow Diagram** visually
3. Demo: Test cases from **Migration Plan**
4. Decide: Which phase to implement

---

## 🔑 Key Findings

### Your Premise vs. Reality

**Your Assumption:**
> "The profiler agent is deciding function counts, creating a 2-function bias"

**Actual Finding:**
✓ Partially correct: LLM profiler DOES prefer 2 functions (intentional)
✗ Incomplete: The bias cascades because **schema is fragmented**

**Root Cause (Architectural):**
1. `workflow_results.core_functions` = INTEGER (validator's count)
2. `app_opportunities.core_functions` = JSON array (profiler's list)
3. No validation that count matches array length
4. Dashboards accidentally use correct table; core issue hidden

---

## 📊 Data Distribution Insight

**Current State:**
- 95%+ of app_opportunities have exactly 2 functions
- **Root:** LLM prompt lines 99–102 explicitly prefer 2 (simplicity rule)
- **Not a bug:** This is working as designed
- **But:** Schema fragmentation makes it hard to audit or verify

---

## ✅ Acceptance Criteria

After implementing fixes, verify:
```python
✓ All opportunities have non-NULL function_list
✓ function_count matches len(function_list)
✓ All counts are 1-3 (constraint enforced)
✓ No records with 0 or >3 functions in production
✓ Distribution check: <80% concentration on single count
✓ Dashboards render correctly without errors
✓ Validation warnings logged for all detected mismatches
```

---

## 📝 Code References (From Diagnosis)

### Critical Files
| File | Issue | Line(s) |
|------|-------|---------|
| `agent_tools/llm_profiler.py` | Prompt bias (intentional) | 99–102 |
| `core/dlt/constraint_validator.py` | Integer count storage | 15, 65 |
| `core/dlt/schemas/app_opportunities_schema.py` | JSON type definition | 43 |
| `core/dlt_app_opportunities.py` | Separate resource | 44 |
| `scripts/batch_opportunity_scoring.py` | Data preparation | 308–368 |
| `supabase/migrations/20251108000001...sql` | workflow_results schema | LINE 8 |

### Key Methods
| Method | Purpose | File | Line |
|--------|---------|------|------|
| `LLMProfiler.generate_app_profile()` | Generate profiles (1-3 functions) | llm_profiler.py | 33 |
| `OpportunityAnalyzerAgent.analyze_opportunity()` | Score (no functions) | opportunity_analyzer_agent.py | 89 |
| `prepare_analysis_for_storage()` | Extract and prepare data | batch_opportunity_scoring.py | 308 |
| `app_opportunities_with_constraint()` | Validate constraints | constraint_validator.py | 42 |
| `_extract_core_functions()` | Extract function list | constraint_validator.py | 83 |
| `_validate_function_consistency()` | **NEW (proposed)** | constraint_validator.py | — |

---

## 🔧 Implementation Checklist

### Phase 1 (Immediate, 2 hours)
- [ ] Add `_validate_function_consistency()` to constraint_validator.py
- [ ] Add pre-flight assertions to batch_opportunity_scoring.py
- [ ] Write unit tests (test_constraint_validator.py)
- [ ] Deploy to staging
- [ ] Test with sample data

### Phase 2 (Schema, 3 hours)
- [ ] Write SQL migration: add function_list to workflow_results
- [ ] Backfill data from app_opportunities
- [ ] Test in staging
- [ ] Run acceptance test
- [ ] Deploy to production (low-traffic window)

### Phase 3 (Dashboards, 3 hours)
- [ ] Update opportunity_dashboard_reactive.py
- [ ] Update opportunity_dashboard_fixed.py
- [ ] Update ultra_rare_dashboard.py
- [ ] Test in staging
- [ ] Verify rendering

### Phase 4 (Optional, next release)
- [ ] Plan consolidation
- [ ] Create app_opportunities_v2
- [ ] Migrate data with triggers/sync
- [ ] Update all queries
- [ ] Archive old tables

---

## 🚨 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Schema migration breaks workflow_results reads | Low | Medium | Test migration in staging first |
| Data not backfilled correctly | Low | High | Run audit query, verify counts match |
| Dashboards break due to column rename | Low | Medium | Update all queries before deploying |
| Rollback needed | Very Low | Low | All changes are additive, safe to revert |

---

## 🎓 Learning Outcomes

After reading these docs, you'll understand:

1. ✅ Why 95%+ of opportunities have exactly 2 functions (LLM prompt bias, intentional)
2. ✅ How data flows from submission → scoring → profiling → two tables
3. ✅ Why the schema fragmentation matters (architectural debt)
4. ✅ How to add validation without breaking existing code (Phase 1)
5. ✅ How to consolidate schema safely (Phase 2–4)
6. ✅ How to test and verify the fix (acceptance criteria)

---

## 📞 Questions & Decisions

### Decision Points
1. **Phase 1:** Start immediately? (Low risk, high value)
   - [ ] Yes, deploy guardrails
   - [ ] No, wait for full plan

2. **Phase 2:** Schema migration needed?
   - [ ] Yes, unify tables
   - [ ] No, keep separate (accept debt)

3. **Phase 4:** Consolidate or keep two tables?
   - [ ] Consolidate in v2 (cleaner architecture)
   - [ ] Keep both (accept fragmentation)

### Follow-Up Questions
- **LLM Prompt:** Should we adjust preference away from 2 functions?
  - Current: "2 = GOOD, 3 = ACCEPTABLE"
  - Option: Make all 1-2-3 equal weight?

- **Validation Strictness:** Should we auto-correct or fail?
  - Current (proposed): Auto-correct + warn
  - Alternative: Fail loudly (safer but slower)

- **Timeline:** When can this be prioritized?
  - Phase 1: ~2 hours (can do immediately)
  - Phase 2: ~3 hours (schedule maintenance window)
  - Phase 3: ~3 hours (rolling deployment)

---

## 📚 Additional Resources

- **DLT Documentation:** https://dlthub.com/docs
- **Supabase Schema Management:** https://supabase.com/docs/guides/database/migrations
- **Constraint Validator Source:** `core/dlt/constraint_validator.py`
- **Testing Setup:** `tests/test_constraint_validator.py` (template provided)

---

## 🏁 Next Step

**Recommended:** Read the one-pager, then share with team for decisions on phases 1–4.

**Questions?** Refer to the detailed diagnosis or data flow diagram for specifics.

---

**Generated:** 2025-11-10
**Status:** Diagnosis complete, no changes executed
**Approval Status:** Awaiting review & decision on implementation phases

