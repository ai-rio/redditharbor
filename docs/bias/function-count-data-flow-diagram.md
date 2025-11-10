# Function-Count Bias: Data Flow Diagram & Table Schema

## Full Data Flow (Current State)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ REDDIT SUBMISSION                                                           │
│ (title, text, engagement)                                                   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────┐
        │ OpportunityAnalyzerAgent                 │
        │ ✓ Calculates 5 dimension scores          │
        │ ✓ Returns: final_score, dimension_scores │
        │ ✗ Does NOT generate core_functions       │
        │                                          │
        │ File: agent_tools/opportunity_analyzer... │
        │ Method: analyze_opportunity()            │
        └──────────────┬───────────────────────────┘
                       │
                       │ analysis = {
                       │   final_score: 85.0,
                       │   dimension_scores: {...},
                       │   core_functions: [] ← NOT SET
                       │ }
                       │
                       ▼
        ┌──────────────────────────────────────────────┐
        │ HIGH SCORE CHECK                             │
        │ if final_score >= 40:                        │
        │   → Call LLMProfiler                         │
        │ else:                                        │
        │   → Skip to DLT loading (no AI profile)      │
        │                                              │
        │ File: scripts/batch_opportunity_scoring.py   │
        │ Line: ~539                                   │
        └──────────────┬───────────────────────────────┘
                       │
              ┌────────┴────────┐
              │                 │
              ▼ (≥40)           ▼ (<40)
    ┌─────────────────────┐  [Skip LLM]
    │ LLMProfiler         │     │
    │ ✓ Calls OpenRouter  │     │
    │ ✓ Prompt enforces   │     │
    │   1-2 functions     │     │
    │ ✓ Validates JSON    │     │
    │ ✓ Returns: profile  │     │
    │   {                 │     │
    │   problem_desc: "", │     │
    │   core_functions: [ │     │
    │     "Track",        │     │
    │     "Log"           │     │
    │   ],                │     │
    │   ...               │     │
    │   }                 │     │
    │                     │     │
    │ File: agent_tools/  │     │
    │ llm_profiler.py     │     │
    │ Method:             │     │
    │ generate_app_...()  │     │
    └──────────┬──────────┘     │
               │                │
               │ profile data   │
               │ (with 2 funcs) │
               │                │
               └────────┬───────┘
                        │
                        ▼
        ┌────────────────────────────────────────┐
        │ prepare_analysis_for_storage()         │
        │ (batch_opportunity_scoring.py:308)     │
        │                                        │
        │ Extract:                               │
        │   core_functions = profile.get(...)    │
        │   function_count = len([...])  = 2    │
        │                                        │
        │ Build dict:                            │
        │ {                                      │
        │   opportunity_id: "opp_xyz",           │
        │   function_count: 2,  ← INTEGER        │
        │   function_list: [...],  ← ARRAY       │
        │   final_score: 85.0,                   │
        │   ...                                  │
        │ }                                      │
        └──────────┬─────────────────────────────┘
                   │
                   │ analysis_data (with both count & list)
                   │
                   ▼
        ┌────────────────────────────────────────────────────┐
        │ load_scores_to_supabase_via_dlt()                  │
        │ (batch_opportunity_scoring.py:370)                 │
        │                                                    │
        │ Step 1: Call app_opportunities_with_constraint()   │
        │ (core/dlt/constraint_validator.py:42)              │
        │   ▼ DLT Resource that targets:                     │
        │      @dlt.resource(table_name="workflow_results")  │
        │                                                    │
        │ Logic:                                             │
        │  - _extract_core_functions(): Gets ["Track", ...]│
        │  - Count: 2                                        │
        │  - Set: opportunity["core_functions"] = 2          │
        │  - Set: simplicity_score = 85.0                    │
        │  - Set: is_disqualified = False (2 < 4)            │
        │  - Yield: opportunity (with all fields)            │
        │                                                    │
        │ Step 2: Run DLT pipeline (pipeline.run(...))       │
        │  - Write disposition: "merge"                      │
        │  - Primary key: "opportunity_id"                   │
        │  - Deduplicate if opportunity_id exists            │
        │                                                    │
        └──────────────┬─────────────────────────────────────┘
                       │
                       │ DLT transformation
                       │ (core/dlt/constraint_validator.py schema)
                       │
                       ▼ SPLIT HERE (TWO PATHS)
        ┌──────────────────────────────┐   ┌──────────────────────────────┐
        │ Path A: workflow_results      │   │ Path B: app_opportunities    │
        │                              │   │ (store_ai_profiles_to...)    │
        │ DLT schema expects:          │   │                              │
        │ - core_functions: BIGINT     │   │ DLT resource expects:        │
        │   (INTEGER count)            │   │ - core_functions: JSON       │
        │                              │   │   (array of strings)         │
        │ Stored value:                │   │                              │
        │ - core_functions = 2         │   │ Stored value:                │
        │   (the count, not array)     │   │ - core_functions = [         │
        │ - simplicity_score = 85.0    │   │   "Track",                   │
        │ - is_disqualified = False    │   │   "Log"                      │
        │ - validation_timestamp = ... │   │ ]                            │
        │                              │   │ (the actual array)           │
        │ Use: Constraint validation,  │   │                              │
        │ pipeline audits              │   │ Use: Dashboards, profiles    │
        └──────────────┬───────────────┘   └──────────────┬───────────────┘
                       │                                   │
                       │ problem: types don't match         │ ✓ dashboards read this
                       │ integer count vs. array           │
                       │                                   │
                       └──────────────┬────────────────────┘
                                      │
                                      ▼
                          ┌─────────────────────────────────┐
                          │ DATA INCONSISTENCY              │
                          │ • Both tables have function     │
                          │   data in different formats     │
                          │ • workflow_results = counter    │
                          │ • app_opportunities = array     │
                          │ • Dashboards accidentally work  │
                          │   because they query the right  │
                          │   table (app_opportunities)     │
                          │ • But audit is impossible       │
                          │   (can't join on two different  │
                          │   schema definitions)           │
                          └─────────────────────────────────┘
```

---

## Table Schema Conflict

### workflow_results (Source: DLT Constraint Validator)
```sql
CREATE TABLE workflow_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id VARCHAR(255) UNIQUE NOT NULL,
  app_name VARCHAR(255) NOT NULL,
  function_count INTEGER NOT NULL,           -- ← COUNT (integer 2)
  function_list TEXT[] DEFAULT '{}',         -- ← ARRAY (for reference)
  core_functions BIGINT,                     -- ← DUPLICATE: DLT adds this as INTEGER
  simplicity_score DOUBLE PRECISION,
  is_disqualified BOOLEAN,
  final_score FLOAT NOT NULL,
  status VARCHAR(50) NOT NULL,
  processed_at TIMESTAMP DEFAULT NOW(),
  ...
);
```

**Problem:**
- `function_count` = 2 (integer, from constraint validator)
- `core_functions` = 2 (integer, DLT's normalized field name)
- `function_list` = ARRAY, but not used (data is in the counts)
- Schema designed for **counting**, not **profiling**

---

### app_opportunities (Source: DLT app_opportunities_resource)
```sql
CREATE TABLE app_opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id VARCHAR(255) UNIQUE NOT NULL,
  submission_id VARCHAR(255),
  app_name VARCHAR(255) NOT NULL,
  core_functions JSON,                       -- ← ARRAY (["Track", "Log"])
  problem_description TEXT,
  app_concept TEXT,
  value_proposition TEXT,
  target_user TEXT,
  monetization_model TEXT,
  opportunity_score DECIMAL,
  final_score FLOAT NOT NULL,
  status VARCHAR(50) NOT NULL,
  ...
);
```

**Expected:**
- `core_functions` = JSON array of function names
- Full AI-generated profile
- Schema designed for **profiling and business analysis**

---

### Schema Mismatch Matrix

| Field | workflow_results | app_opportunities | Conflict? |
|-------|------------------|-------------------|-----------|
| opportunity_id | VARCHAR UNIQUE | VARCHAR UNIQUE | ❌ Different PK strategy |
| core_functions | BIGINT (count) | JSON (array) | ✗ **TYPE MISMATCH** |
| function_list | TEXT[] | — | ❌ Not in app_opportunities |
| function_count | INTEGER | — | ❌ Not in app_opportunities |
| problem_description | — | TEXT | ❌ Profiling data missing |
| app_concept | — | TEXT | ❌ Profiling data missing |
| simplicity_score | DOUBLE | — | ❌ Not in app_opportunities |

**Result:** Two tables, two sources of truth, incompatible schemas for the same entity.

---

## Data Flow: Correct vs. Current

### Correct Flow (Proposed Fix)
```
Submission
  ↓
OpportunityAnalyzer (score only)
  ↓ (high score)
LLMProfiler (profile: 2 functions)
  ↓
prepare_analysis_for_storage() → {
    function_list: ["Track", "Log"]  ← ARRAY
    function_count: 2                 ← INTEGER (derived)
}
  ↓
Constraint Validator
  ✓ Validates: count == len(list)
  ✓ Auto-corrects mismatches
  ✓ Ensures 1-3 range
  ↓
Unified Table: app_opportunities
  core_functions: ["Track", "Log"]  ← ARRAY (source of truth)
  function_count: 2                  ← INTEGER (derived field)
  simplicity_score: 85.0             ← DERIVED from count

Dashboard reads:
  function_list = core_functions (JSON array)
  function_count = derived from array length
```

---

## Why The Problem Exists

### Historical Context
1. **Original design:** Two independent tables (`workflow_results` for validation metrics, `app_opportunities` for profiling)
2. **Constraint validator:** Designed to validate counts in `workflow_results`, stores integer
3. **LLM profiler:** Designed to generate profiles in `app_opportunities`, stores arrays
4. **No consolidation:** Both tables coexist, each with different schema
5. **Accidental correctness:** Dashboards query `app_opportunities` (the right table), so bugs are hidden

### Why It Matters
- **Scaling risk:** If you switch dashboards to `workflow_results`, they break immediately
- **Audit trail:** Hard to trace which table is "correct"
- **Constraint enforcement:** Validator can only check integers, not actual function names
- **Maintenance burden:** Two paths to same data = engineering debt

---

## Summary for Code Review

**Table Responsible for Core Functions:**
- `workflow_results`: Stores INTEGER count (validation layer)
- `app_opportunities`: Stores JSON array (profiling layer)
- **Problem:** Both claim ownership; schema conflict

**Field Responsible for Function Count:**
- `workflow_results.core_functions`: INTEGER (from constraint validator)
- `workflow_results.function_count`: INTEGER (original, redundant)
- `app_opportunities.core_functions`: JSON (from LLM profiler)
- **Problem:** Three fields, two types, one concept

**Data Flow at Risk:**
- Constraint validator → workflow_results ✓ Works, but wrong type
- LLM profiler → app_opportunities ✓ Works, correct type
- Cross-table queries ✗ Fail due to type mismatch

**Fix Priority:**
1. Add validation (Phase 1): Catch mismatches early
2. Add function_list to workflow_results (Phase 2): Unify schema
3. Update dashboards (Phase 3): Query correct table/column
4. Consolidate tables (Phase 4): Single source of truth

