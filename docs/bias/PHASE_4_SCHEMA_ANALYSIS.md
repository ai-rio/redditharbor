# Phase 4: Schema Analysis for Table Consolidation

**Date:** 2025-11-10
**Purpose:** Analyze schema differences between `workflow_results` and `app_opportunities` for consolidation

---

## Current State: Two Tables

### Table 1: `workflow_results`
**Purpose:** Stores workflow processing results with dimension scores

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| id | uuid | NOT NULL | Primary key |
| opportunity_id | varchar(255) | NOT NULL | Unique constraint |
| app_name | varchar(255) | NOT NULL | |
| function_count | integer | NOT NULL | Count only |
| function_list | text[] | NULL | Array (Phase 2 addition) |
| original_score | double | NOT NULL | |
| final_score | double | NOT NULL | |
| status | varchar(50) | NOT NULL | |
| constraint_applied | boolean | NULL | |
| ai_insight | text | NULL | |
| processed_at | timestamp | NULL | |
| market_demand | numeric(5,2) | NULL | 0-100 |
| pain_intensity | numeric(5,2) | NULL | 0-100 |
| monetization_potential | numeric(5,2) | NULL | 0-100 |
| market_gap | numeric(5,2) | NULL | 0-100 |
| technical_feasibility | numeric(5,2) | NULL | 0-100 |

**Indexes:** 9 indexes including GIN on function_list

### Table 2: `app_opportunities`
**Purpose:** Stores LLM-generated app profiles

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| id | uuid | NOT NULL | Primary key |
| submission_id | text | NOT NULL | Reddit ID |
| problem_description | text | NOT NULL | LLM field |
| app_concept | text | NOT NULL | LLM field |
| core_functions | jsonb | NOT NULL | Array of strings |
| value_proposition | text | NOT NULL | LLM field |
| target_user | text | NOT NULL | LLM field |
| monetization_model | text | NOT NULL | LLM field |
| opportunity_score | numeric(5,2) | NULL | 0-100 |
| title | text | NULL | Reddit post title |
| subreddit | text | NULL | Source subreddit |
| reddit_score | integer | NULL | Upvotes |
| num_comments | integer | NULL | Comment count |
| created_at | timestamptz | NULL | |
| analyzed_at | timestamptz | NULL | |
| status | text | NULL | enum check |
| notes | text | NULL | |
| _dlt_load_id | text | NULL | DLT metadata |
| _dlt_id | text | NULL | DLT metadata |

**Indexes:** 6 indexes

---

## Schema Overlap Analysis

### Shared Concepts (Different Names)
| Concept | workflow_results | app_opportunities |
|---------|------------------|-------------------|
| Functions | function_list (text[]) | core_functions (jsonb) |
| Scoring | final_score (double) | opportunity_score (numeric) |
| Timestamp | processed_at | analyzed_at |
| Status | status (varchar) | status (text with CHECK) |

### Unique to workflow_results
- Dimension scores (market_demand, pain_intensity, etc.)
- function_count (integer)
- original_score / final_score distinction
- constraint_applied flag
- ai_insight

### Unique to app_opportunities
- LLM profile fields (problem_description, app_concept, etc.)
- Reddit metadata (submission_id, subreddit, reddit_score, etc.)
- DLT metadata (_dlt_*)
- Richer status enum

---

## Consolidation Strategy

### Option A: Single Unified Table ⭐ RECOMMENDED

**Approach:** Create `opportunities` table combining both schemas

**Benefits:**
- Single source of truth
- Eliminates synchronization issues
- Simpler queries
- Clearer data model

**Risks:**
- Requires updating all code references
- Migration complexity
- Potential data loss if not careful

### Option B: Keep Separate with Foreign Keys

**Approach:** Maintain both tables but add proper relationships

**Benefits:**
- Lower risk
- Gradual migration path
- Existing code continues working

**Risks:**
- Continues schema fragmentation
- Requires synchronization logic
- More complex queries

---

## Recommended Unified Schema

```sql
CREATE TABLE opportunities (
    -- Primary identification
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id text UNIQUE NOT NULL,  -- Reddit ID
    opportunity_id text UNIQUE NOT NULL,  -- Internal ID

    -- LLM-generated profile (from app_opportunities)
    problem_description text NOT NULL,
    app_concept text NOT NULL,
    core_functions jsonb NOT NULL,  -- Array of 1-3 function names
    function_count integer GENERATED ALWAYS AS (jsonb_array_length(core_functions)) STORED,
    value_proposition text NOT NULL,
    target_user text NOT NULL,
    monetization_model text NOT NULL,
    app_name text,  -- Derived from app_concept or explicit

    -- Scoring (unified)
    opportunity_score numeric(5,2) DEFAULT 0.0,
    original_score double precision,
    final_score double precision,

    -- Dimension scores (from workflow_results)
    market_demand numeric(5,2) CHECK (market_demand BETWEEN 0 AND 100),
    pain_intensity numeric(5,2) CHECK (pain_intensity BETWEEN 0 AND 100),
    monetization_potential numeric(5,2) CHECK (monetization_potential BETWEEN 0 AND 100),
    market_gap numeric(5,2) CHECK (market_gap BETWEEN 0 AND 100),
    technical_feasibility numeric(5,2) CHECK (technical_feasibility BETWEEN 0 AND 100),
    simplicity_score double precision,

    -- Reddit metadata (from app_opportunities)
    title text,
    subreddit text,
    reddit_score integer,
    num_comments integer,

    -- Workflow tracking
    status text DEFAULT 'discovered'
        CHECK (status IN ('discovered', 'validated', 'built', 'rejected', 'processing')),
    constraint_applied boolean DEFAULT false,
    is_disqualified boolean DEFAULT false,

    -- AI insights
    ai_insight text,
    notes text,

    -- Timestamps
    created_at timestamptz DEFAULT now(),
    analyzed_at timestamptz DEFAULT now(),
    processed_at timestamptz DEFAULT now(),

    -- DLT metadata
    _dlt_load_id text,
    _dlt_id text,

    -- Constraint validation metadata
    constraint_version bigint,
    validation_timestamp timestamptz,
    violation_reason text,
    validation_status text
);
```

---

## Migration Plan

### Step 1: Create New Table
- Create `opportunities` with unified schema
- Add all necessary indexes
- Add constraints

### Step 2: Data Migration
```sql
INSERT INTO opportunities (
    submission_id, opportunity_id, problem_description, app_concept,
    core_functions, value_proposition, target_user, monetization_model,
    opportunity_score, title, subreddit, reddit_score, num_comments,
    created_at, analyzed_at, status, notes, _dlt_load_id, _dlt_id
)
SELECT
    submission_id, submission_id as opportunity_id,
    problem_description, app_concept, core_functions, value_proposition,
    target_user, monetization_model, opportunity_score, title, subreddit,
    reddit_score, num_comments, created_at, analyzed_at, status, notes,
    _dlt_load_id, _dlt_id
FROM app_opportunities;

-- Then update with workflow_results data
UPDATE opportunities o
SET
    function_count = wr.function_count,
    original_score = wr.original_score,
    final_score = wr.final_score,
    market_demand = wr.market_demand,
    pain_intensity = wr.pain_intensity,
    monetization_potential = wr.monetization_potential,
    market_gap = wr.market_gap,
    technical_feasibility = wr.technical_feasibility,
    constraint_applied = wr.constraint_applied,
    ai_insight = wr.ai_insight,
    processed_at = wr.processed_at
FROM workflow_results wr
WHERE o.opportunity_id = wr.opportunity_id;
```

### Step 3: Archive Old Tables
```sql
ALTER TABLE app_opportunities RENAME TO app_opportunities_archived;
ALTER TABLE workflow_results RENAME TO workflow_results_archived;
```

### Step 4: Update Code
- Update DLT pipelines
- Update dashboards
- Update scripts

---

## Rollback Plan

```sql
-- If consolidation fails, restore:
ALTER TABLE opportunities RENAME TO opportunities_failed;
ALTER TABLE app_opportunities_archived RENAME TO app_opportunities;
ALTER TABLE workflow_results_archived RENAME TO workflow_results;
```

---

## Next Steps

1. Review and approve unified schema
2. Create migration SQL file
3. Test migration on copy of database
4. Update DLT pipelines
5. Update dashboards
6. Deploy to production

---

**Decision Required:** Proceed with Option A (consolidation) or Option B (keep separate)?
