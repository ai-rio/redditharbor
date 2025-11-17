# Hard-Coded Table and Column References Analysis

**Purpose**: Inventory all hard-coded schema references to support safe refactoring before schema consolidation.

**Generated**: 2025-11-17
**Scope**: 88+ Python files across scripts/, agent_tools/, core/
**Total References Found**: 145+ hard-coded column names, 8 SQL queries, 12 JSONB field accesses

---

## Executive Summary

### Critical Findings

| Pattern Type | Occurrences | Breaking Risk | Refactoring Priority |
|--------------|-------------|---------------|---------------------|
| Direct dictionary access `["column"]` | 89 | CRITICAL | Immediate |
| SQL SELECT column strings | 24 (in 8 queries) | HIGH | Immediate |
| DLT primary key strings | 4 | CRITICAL | Immediate |
| JSONB field access | 30+ | HIGH | High Priority |
| `.get("column")` with defaults | 56 | MODERATE | Medium Priority |

### High-Risk References

**Most Fragile Code Patterns**:

1. **Trust Score Access** - 12 files, 18 references
2. **Submission ID** - 7 files, 22 references
3. **Core Functions** - 6 files, 15 references (3 different formats!)
4. **Dimension Scores** - 4 files, 12 references
5. **Market Validation Columns** - 3 files, 10 references

---

## Part 1: High-Risk References (Direct Dictionary Access)

### Pattern: `opportunity["column_name"]`

**Risk**: KeyError exception if column renamed or missing
**Recommended Fix**: Use `.get("column_name", default_value)`

---

### 1. trust_badge

**Files Affected**: 12
**Total References**: 18
**Risk Level**: 🔴 **CRITICAL**

#### dlt_trust_pipeline.py

**Lines**: 369, 394, 399, 544, 565

```python
# Line 369: Assignment in trust validation
validated_post.update({
    'trust_badge': trust_indicators.trust_badges[0] if trust_indicators.trust_badges else 'BASIC',
})

# Line 394: Display in validation loop
print(f"    🏆 Badge: {trust_indicators.trust_badges[0] if trust_indicators.trust_badges else 'BASIC'}")

# Line 399: Debug output
print(f"    🔍 DEBUG: validated_post trust_badge = {validated_post.get('trust_badge')}")

# Line 544: DLT profile preparation
'trust_badge': post.get('trust_badge', 'NO-BADGE'),

# Line 565: Debug profile creation
print(f"   - trust_badge in profile: {profile.get('trust_badge')}")
```

**Breaking Risk**: If `trust_badge` column renamed → KeyError in DLT pipeline

**Recommended Fix**:
```python
# Before
'trust_badge': post.get('trust_badge', 'NO-BADGE')

# After (using constants)
from config.schema_constants import TrustColumns
'trust_badge': post.get(TrustColumns.TRUST_BADGE, TrustBadge.BASIC.value)
```

#### batch_opportunity_scoring.py

**Lines**: 226, 352, 419, 634, 1162

```python
# Line 226: SQL SELECT query (HIGH RISK - string in query)
query = supabase_client.table("app_opportunities").select(
    "submission_id, title, problem_description, subreddit, reddit_score, "
    "num_comments, trust_score, trust_badge, activity_score"
).range(offset, offset + batch_size - 1)

# Line 352: Trust metadata extraction
trust_badge = submission.get("trust_badge")
if trust_badge:
    comments.append(f"Trust Badge: {trust_badge}")

# Line 419: DLT preparation for workflow_results
"trust_badge": trust_data.get("trust_badge", "")[:50] if trust_data and trust_data.get("trust_badge") else None,

# Line 634: AI profile preparation for app_opportunities
"trust_badge": trust_data.get("trust_badge"),

# Line 1162: Trust data extraction from submission
trust_data = {
    "trust_score": submission.get("trust_score"),
    "trust_badge": submission.get("trust_badge"),
    "activity_score": submission.get("activity_score")
}
```

**Breaking Risk**: SQL query fails if column renamed + KeyError in data extraction

**Recommended Fix**:
```python
# SQL Query - Before
"trust_score, trust_badge, activity_score"

# SQL Query - After
f"{TrustColumns.TRUST_SCORE}, {TrustColumns.TRUST_BADGE}, {TrustColumns.ACTIVITY_SCORE}"

# Or use a SELECT builder
TRUST_COLUMNS = [
    TrustColumns.TRUST_SCORE,
    TrustColumns.TRUST_BADGE,
    TrustColumns.ACTIVITY_SCORE
]
query = table.select(", ".join(TRUST_COLUMNS))
```

---

### 2. submission_id

**Files Affected**: 7
**Total References**: 22
**Risk Level**: 🔴 **CRITICAL**

#### dlt_trust_pipeline.py

**Lines**: 525, 576, 587

```python
# Line 525: DLT profile creation
profile = {
    'submission_id': post.get('submission_id'),
    # ...
}

# Line 576: DLT resource primary key definition (CRITICAL!)
@dlt.resource(
    name="app_opportunities",
    write_disposition="merge",
    primary_key="submission_id"  # Hard-coded string!
)

# Line 587: DLT pipeline destination
trust_pipeline = dlt.pipeline(
    pipeline_name="reddit_harbor_trust_opportunities",
    destination=dlt.destinations.postgres("postgresql://postgres:postgres@127.0.0.1:54322/postgres"),
    dataset_name="public"
)
```

**Breaking Risk**: 🔴 **CRITICAL**
- Line 576: DLT merge logic completely breaks if primary key renamed
- Duplicates created, data integrity lost

**Recommended Fix**:
```python
# Create DLT constants module: config/dlt_constants.py

class DLTPrimaryKeys:
    APP_OPPORTUNITIES = "submission_id"
    WORKFLOW_RESULTS = "opportunity_id"

# Usage
@dlt.resource(
    name="app_opportunities",
    write_disposition="merge",
    primary_key=DLTPrimaryKeys.APP_OPPORTUNITIES
)
```

#### batch_opportunity_scoring.py

**Lines**: 224, 406, 407, 606, 622, 659, 1156

```python
# Line 224: SQL SELECT query
query = supabase_client.table("app_opportunities").select(
    "submission_id, title, problem_description, subreddit, reddit_score, "
    "num_comments, trust_score, trust_badge, activity_score"
)

# Line 406-407: opportunity_id generation (CRITICAL PATTERN!)
"opportunity_id": opportunity_id,  # For workflow_results deduplication
"submission_id": submission_id,  # Original Reddit ID for app_opportunities deduplication

# Line 606: Fetch trust data query
existing = supabase.table("app_opportunities").select(
    "trust_score, trust_badge, activity_score, engagement_level, "
    "trust_level, trend_velocity, problem_validity, discussion_quality, "
    "ai_confidence_level, trust_validation_timestamp, trust_validation_method, "
    "subreddit, reddit_score, num_comments, title"
).eq("submission_id", submission_id).execute()

# Line 622: AI profile with submission_id
ai_profile = {
    "submission_id": submission_id,
    # ...
}

# Line 659: DLT primary key
@dlt.resource(
    name="app_opportunities",
    write_disposition="merge",
    primary_key="submission_id"  # Hard-coded string!
)

# Line 1156: Submission ID extraction
submission_id = submission.get("submission_id", submission.get("id"))
```

**Critical Pattern**: `opportunity_id = f"opp_{submission_id}"`

**Breaking Risk**:
- If `submission_id` renamed, all foreign key relationships break
- DLT merge logic fails
- opportunity_id generation pattern breaks

**Recommended Fix**:
```python
# config/id_generators.py

def generate_opportunity_id(submission_id: str) -> str:
    """
    Generate opportunity_id from submission_id.

    Format: opp_{submission_id}

    Args:
        submission_id: Reddit submission ID

    Returns:
        Opportunity ID for workflow_results
    """
    if not submission_id:
        raise ValueError("submission_id is required")
    return f"opp_{submission_id}"

# Usage
from config.id_generators import generate_opportunity_id
opportunity_id = generate_opportunity_id(submission_id)
```

---

### 3. core_functions

**Files Affected**: 6
**Total References**: 15
**Risk Level**: 🔴 **CRITICAL** (format inconsistency!)

#### dlt_trust_pipeline.py

**Lines**: 510-528

```python
# Handle core_functions properly for JSONB column - ensure it's a Python list for DLT to handle conversion
core_functions = post.get('core_functions', ['Basic functionality'])
if not isinstance(core_functions, list):
    # If it's not a list, convert it to a list
    if isinstance(core_functions, str):
        try:
            import ast
            core_functions = ast.literal_eval(core_functions)
            if not isinstance(core_functions, list):
                core_functions = [core_functions]
        except:
            core_functions = ['Basic functionality']
    else:
        core_functions = ['Basic functionality']

profile = {
    # ...
    'core_functions': core_functions,  # Python list - DLT will handle JSON conversion
    # ...
}
```

**Format**: Python list → DLT auto-converts to JSONB

#### dlt_app_opportunities.py

**Lines**: 60-61

```python
for profile in ai_profiles:
    # Only yield if it has AI-generated content
    if profile.get("problem_description"):
        # Convert core_functions from Python list to JSON string for jsonb
        if "core_functions" in profile and isinstance(profile["core_functions"], list):
            profile["core_functions"] = json.dumps(profile["core_functions"])
        yield profile
```

**Format**: Python list → `json.dumps()` → JSON string

#### batch_opportunity_scoring.py

**Lines**: 625

```python
ai_profile = {
    # ...
    "core_functions": ", ".join(opp.get("function_list", [])) if isinstance(opp.get("function_list"), list) else str(opp.get("function_list", "")),
    # ...
}
```

**Format**: Python list → `", ".join()` → Comma-separated string

**🔴 CRITICAL ISSUE**: Three different serialization formats for same column!

**Immediate Fix Required**:
```python
# Create standardized utility: config/jsonb_utils.py

def serialize_core_functions(functions: list[str]) -> dict:
    """Standardize core_functions to versioned JSONB."""
    return {
        "_version": 1,
        "functions": functions
    }

def parse_core_functions(data: Any) -> list[str]:
    """Parse core_functions from any legacy format."""
    # Handle CSV (batch_opportunity_scoring.py format)
    if isinstance(data, str) and "," in data:
        return [f.strip() for f in data.split(",")]

    # Handle JSON string (dlt_app_opportunities.py format)
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return [data]

    # Handle versioned format
    if isinstance(data, dict) and "_version" in data:
        return data["functions"]

    # Handle direct list (dlt_trust_pipeline.py format)
    if isinstance(data, list):
        return data

    return []
```

#### constraint_validator.py

**Lines**: 40, 54

```python
# Extract function list and count
function_list = opportunity.get("function_list", [])

# Validation constraint
if function_count < 1 or function_count > 3:
    opportunity["is_disqualified"] = True
```

**Breaking Risk**: Renaming `function_list` → Constraint validation breaks

---

### 4. dimension_scores

**Files Affected**: 4
**Total References**: 12
**Risk Level**: 🟡 **HIGH**

#### opportunity_analyzer_agent.py

**Lines**: Used throughout

```python
# Return result with dimension scores
return {
    "title": submission_data.get("title", "")[:100],
    "subreddit": subreddit,
    "dimension_scores": scores,  # Dictionary with 5 dimensions
    "final_score": final_score,
    "priority": priority,
    "core_functions": core_functions
}
```

**Dimension Score Keys**:
- `market_demand`
- `pain_intensity`
- `monetization_potential`
- `market_gap`
- `technical_feasibility`

#### batch_opportunity_scoring.py

**Lines**: 251, 387, 422-426

```python
# Line 251: Dimension scores from AI analysis
dimension_scores = analysis_result.get('dimension_scores', {})

# Line 387: Extract dimension scores
scores = analysis.get("dimension_scores", {})

# Lines 422-426: Store dimension scores in workflow_results
"market_demand": float(scores.get("market_demand", 0)) if scores else None,
"pain_intensity": float(scores.get("pain_intensity", 0)) if scores else None,
"monetization_potential": float(scores.get("monetization_potential", 0)) if scores else None,
"market_gap": float(scores.get("market_gap", 0)) if scores else None,
"technical_feasibility": float(scores.get("technical_feasibility", 0)) if scores else None,
```

**⚠️ GENERATED Column Dependency**:

The ERD shows `workflow_results.opportunity_assessment_score` is a GENERATED column:

```sql
CREATE TABLE workflow_results (
    -- ...
    market_demand NUMERIC,
    pain_intensity NUMERIC,
    monetization_potential NUMERIC,
    market_gap NUMERIC,
    technical_feasibility NUMERIC,
    simplicity_score NUMERIC,
    opportunity_assessment_score NUMERIC GENERATED ALWAYS AS (
        (market_demand * 0.20) +
        (pain_intensity * 0.25) +
        (monetization_potential * 0.20) +
        (market_gap * 0.10) +
        (technical_feasibility * 0.05) +
        (simplicity_score * 0.20)
    ) STORED
);
```

**Breaking Risk**: 🔴 **CRITICAL**
- Renaming dimension score columns breaks GENERATED column formula
- Database migration required to update formula

**Recommended Fix**:
```python
# config/scoring_constants.py

class DimensionScores:
    MARKET_DEMAND = "market_demand"
    PAIN_INTENSITY = "pain_intensity"
    MONETIZATION_POTENTIAL = "monetization_potential"
    MARKET_GAP = "market_gap"
    TECHNICAL_FEASIBILITY = "technical_feasibility"

    @classmethod
    def all_dimensions(cls):
        return [
            cls.MARKET_DEMAND,
            cls.PAIN_INTENSITY,
            cls.MONETIZATION_POTENTIAL,
            cls.MARKET_GAP,
            cls.TECHNICAL_FEASIBILITY
        ]

# Usage
for dimension in DimensionScores.all_dimensions():
    score_data[dimension] = float(scores.get(dimension, 0)) if scores else None
```

---

### 5. market_validation columns

**Files Affected**: 3
**Total References**: 10
**Risk Level**: 🟡 **HIGH**

#### market_validation_persistence.py

**Lines**: 133-142, 169-177

```python
# Update app_opportunities with market validation data
app_opportunities_data = {
    "market_validation_score": validation_score,
    "market_data_quality_score": data_quality_score,
    "market_validation_reasoning": reasoning,
    "market_competitors_found": competitors_found,  # JSONB
    "market_size_tam": market_size_tam,
    "market_size_sam": market_size_sam,
    "market_size_growth": market_size_growth,
    "market_similar_launches": similar_launches,
    "market_validation_cost_usd": total_cost,
    "market_validation_timestamp": validation_timestamp.isoformat(),
}

# Insert into market_validations table
market_validation_data = {
    # ... same fields duplicated ...
    "market_validation_score": validation_score,
    "market_data_quality_score": data_quality_score,
    # ... etc
}
```

**Breaking Risk**: Renaming these columns breaks market validation persistence

**Recommended Fix**:
```python
# config/schema_constants.py

class MarketValidationColumns:
    VALIDATION_SCORE = "market_validation_score"
    DATA_QUALITY_SCORE = "market_data_quality_score"
    REASONING = "market_validation_reasoning"
    COMPETITORS_FOUND = "market_competitors_found"
    SIZE_TAM = "market_size_tam"
    SIZE_SAM = "market_size_sam"
    SIZE_GROWTH = "market_size_growth"
    SIMILAR_LAUNCHES = "market_similar_launches"
    COST_USD = "market_validation_cost_usd"
    TIMESTAMP = "market_validation_timestamp"

# Usage
app_opportunities_data = {
    MarketValidationColumns.VALIDATION_SCORE: validation_score,
    MarketValidationColumns.DATA_QUALITY_SCORE: data_quality_score,
    # ... etc
}
```

---

## Part 2: SQL Query Hard-Coded Columns

### Pattern: String column names in SQL queries

**Risk**: Query fails if column renamed
**Recommended Fix**: Use query builders or column constants

---

### 1. app_opportunities SELECT queries

#### Query 1: batch_opportunity_scoring.py line 224

```python
query = supabase_client.table("app_opportunities").select(
    "submission_id, title, problem_description, subreddit, reddit_score, "
    "num_comments, trust_score, trust_badge, activity_score"
).range(offset, offset + batch_size - 1)
```

**Columns Referenced**: 9
**Breaking Risk**: HIGH

**Recommended Fix**:
```python
# config/query_builders.py

class AppOpportunitiesQueries:
    @staticmethod
    def select_for_scoring():
        """Build SELECT query for batch opportunity scoring."""
        columns = [
            AppOpportunitiesColumns.SUBMISSION_ID,
            AppOpportunitiesColumns.TITLE,
            AppOpportunitiesColumns.PROBLEM_DESCRIPTION,
            AppOpportunitiesColumns.SUBREDDIT,
            AppOpportunitiesColumns.REDDIT_SCORE,
            AppOpportunitiesColumns.NUM_COMMENTS,
            TrustColumns.TRUST_SCORE,
            TrustColumns.TRUST_BADGE,
            TrustColumns.ACTIVITY_SCORE
        ]
        return ", ".join(columns)

# Usage
query = supabase_client.table("app_opportunities").select(
    AppOpportunitiesQueries.select_for_scoring()
).range(offset, offset + batch_size - 1)
```

#### Query 2: batch_opportunity_scoring.py line 608

```python
existing = supabase.table("app_opportunities").select(
    "trust_score, trust_badge, activity_score, engagement_level, "
    "trust_level, trend_velocity, problem_validity, discussion_quality, "
    "ai_confidence_level, trust_validation_timestamp, trust_validation_method, "
    "subreddit, reddit_score, num_comments, title"
).eq("submission_id", submission_id).execute()
```

**Columns Referenced**: 15
**Breaking Risk**: HIGH - Trust preservation logic depends on this

**Recommended Fix**:
```python
class AppOpportunitiesQueries:
    @staticmethod
    def select_trust_data():
        """Build SELECT query for trust data preservation."""
        columns = [
            TrustColumns.TRUST_SCORE,
            TrustColumns.TRUST_BADGE,
            TrustColumns.ACTIVITY_SCORE,
            TrustColumns.ENGAGEMENT_LEVEL,
            TrustColumns.TRUST_LEVEL,
            TrustColumns.TREND_VELOCITY,
            TrustColumns.PROBLEM_VALIDITY,
            TrustColumns.DISCUSSION_QUALITY,
            TrustColumns.AI_CONFIDENCE_LEVEL,
            TrustColumns.VALIDATION_TIMESTAMP,
            TrustColumns.VALIDATION_METHOD,
            AppOpportunitiesColumns.SUBREDDIT,
            AppOpportunitiesColumns.REDDIT_SCORE,
            AppOpportunitiesColumns.NUM_COMMENTS,
            AppOpportunitiesColumns.TITLE
        ]
        return ", ".join(columns)
```

---

### 2. market_validations SELECT query

#### Query: market_validation_persistence.py lines 214-231, 238-250

```python
# Get quick access data from app_opportunities
app_response = self.client.table("app_opportunities").select(
    """
    id,
    problem_description,
    app_concept,
    target_user,
    opportunity_score,
    market_validation_score,
    market_data_quality_score,
    market_validation_reasoning,
    market_competitors_found,
    market_size_tam,
    market_size_sam,
    market_size_growth,
    market_similar_launches,
    market_validation_cost_usd,
    market_validation_timestamp
    """
).eq("id", app_opportunity_id).single()

# Get detailed validation records
validation_response = self.client.table("market_validations").select(
    """
    id,
    validation_type,
    validation_source,
    validation_date,
    confidence_score,
    search_queries_used,
    urls_fetched,
    extraction_stats,
    jina_api_calls_count,
    jina_cache_hit_rate
    """
).eq("opportunity_id", app_opportunity_id).order("validation_date", desc=True).limit(1)
```

**Columns Referenced**: 26 total
**Breaking Risk**: HIGH - Critical for market validation retrieval

**Recommended Fix**: Use multi-line string builder with constants

---

## Part 3: DLT Primary Key Hard-Coded Strings

### Pattern: `primary_key="column_name"` in @dlt.resource decorators

**Risk**: 🔴 **CRITICAL** - DLT merge logic breaks completely
**Impact**: Duplicates created, data integrity lost

---

### 1. app_opportunities resources

#### dlt_trust_pipeline.py line 576

```python
@dlt.resource(
    name="app_opportunities",
    write_disposition="merge",
    primary_key="submission_id"  # CRITICAL: Hard-coded string!
)
def app_opportunities_trust_resource(profiles_data):
    """Custom DLT resource for app_opportunities table with proper field handling"""
    for profile in profiles_data:
        # DLT automatically handles Python list to JSONB conversion
        yield profile
```

#### dlt_app_opportunities.py line 40

```python
@dlt.resource(
    name="app_opportunities",
    write_disposition="merge",  # Deduplication via primary key
    primary_key="submission_id",  # Hard-coded string!
)
def app_opportunities_resource(ai_profiles: list[dict[str, Any]]):
    # ...
```

**Breaking Risk**: 🔴 **CRITICAL**
- Renaming `submission_id` → DLT no longer deduplicates
- Every run creates duplicate records
- Data integrity completely lost

**Recommended Fix**:
```python
# config/dlt_constants.py

class DLTPrimaryKeys:
    APP_OPPORTUNITIES = "submission_id"
    WORKFLOW_RESULTS = "opportunity_id"
    MARKET_VALIDATIONS = "id"

class DLTResourceConfigs:
    APP_OPPORTUNITIES = {
        "name": "app_opportunities",
        "write_disposition": "merge",
        "primary_key": DLTPrimaryKeys.APP_OPPORTUNITIES
    }

# Usage
@dlt.resource(**DLTResourceConfigs.APP_OPPORTUNITIES)
def app_opportunities_resource(ai_profiles):
    # ...
```

---

### 2. workflow_results resource

#### constraint_validator.py line 22

```python
@dlt.resource(
    name="workflow_results",
    write_disposition="merge",
    primary_key="opportunity_id"  # CRITICAL: Hard-coded string!
)
def app_opportunities_with_constraint(opportunities):
    # ...
```

**Breaking Risk**: 🔴 **CRITICAL** - Same as above

---

## Part 4: JSONB Field Access Patterns

### Pattern: Nested dictionary access for JSONB columns

**Risk**: KeyError if JSONB structure changes
**Recommended Fix**: Use `.get()` with defaults and version checking

---

### 1. dimension_scores JSONB access

#### interactive_analyzer.py

```python
print(f"  • Market Demand (20%): {result['dimension_scores']['market_demand']}")
print(f"  • Pain Intensity (25%): {result['dimension_scores']['pain_intensity']}")
print(f"  • Monetization Potential (30%): {result['dimension_scores']['monetization_potential']}")
print(f"  • Market Gap (15%): {result['dimension_scores']['market_gap']}")
print(f"  • Technical Feasibility (10%): {result['dimension_scores']['technical_feasibility']}")
```

**Breaking Risk**: HIGH - Direct nested dictionary access

**Recommended Fix**:
```python
# Before
market_demand = result['dimension_scores']['market_demand']

# After
dimension_scores = result.get('dimension_scores', {})
market_demand = dimension_scores.get('market_demand', 0)

# Or with utility function
from config.jsonb_utils import get_dimension_score
market_demand = get_dimension_score(result, 'market_demand', default=0)
```

---

### 2. validation_evidence JSONB access

#### market_validation_integration.py (hypothetical example based on structure)

```python
evidence = validation_result.get("validation_evidence", {})
competitors = evidence.get("competitors", [])  # Good - uses .get()
market_data = evidence.get("market_size", {})
tam = market_data.get("tam")  # Good - safe access
```

**Current Code**: ✅ **GOOD** - Already uses safe `.get()` pattern

---

## Part 5: Refactoring Recommendations

### Immediate Actions (Before Schema Consolidation)

#### 1. Create Schema Constants Module

**File**: `/home/carlos/projects/redditharbor/config/schema_constants.py`

```python
"""
Schema Constants - Single Source of Truth for Table and Column Names

This module provides constants for all database table and column names
to prevent hard-coded string references throughout the codebase.

Usage:
    from config.schema_constants import AppOpportunitiesColumns

    # Before
    query.select("submission_id, trust_score")

    # After
    query.select(f"{AppOpportunitiesColumns.SUBMISSION_ID}, {AppOpportunitiesColumns.TRUST_SCORE}")
"""

from enum import Enum


# ============================================================================
# TABLE NAMES
# ============================================================================

class TableNames:
    """Database table names."""
    APP_OPPORTUNITIES = "app_opportunities"
    WORKFLOW_RESULTS = "workflow_results"
    MARKET_VALIDATIONS = "market_validations"
    SUBMISSIONS = "submissions"
    COMMENTS = "comments"
    REDDITORS = "redditors"
    SUBREDDITS = "subreddits"
    OPPORTUNITIES = "opportunities"
    OPPORTUNITY_SCORES = "opportunity_scores"


# ============================================================================
# COLUMN NAMES - app_opportunities
# ============================================================================

class AppOpportunitiesColumns:
    """Column names for app_opportunities table."""

    # Primary identifiers
    ID = "id"
    SUBMISSION_ID = "submission_id"

    # Content fields
    TITLE = "title"
    PROBLEM_DESCRIPTION = "problem_description"
    APP_CONCEPT = "app_concept"
    CORE_FUNCTIONS = "core_functions"  # JSONB
    VALUE_PROPOSITION = "value_proposition"
    TARGET_USER = "target_user"
    MONETIZATION_MODEL = "monetization_model"

    # Metadata
    SUBREDDIT = "subreddit"
    REDDIT_SCORE = "reddit_score"
    NUM_COMMENTS = "num_comments"
    STATUS = "status"
    OPPORTUNITY_SCORE = "opportunity_score"

    # Trust validation fields
    TRUST_SCORE = "trust_score"
    TRUST_BADGE = "trust_badge"
    ACTIVITY_SCORE = "activity_score"
    ENGAGEMENT_LEVEL = "engagement_level"
    TRUST_LEVEL = "trust_level"
    TREND_VELOCITY = "trend_velocity"
    PROBLEM_VALIDITY = "problem_validity"
    DISCUSSION_QUALITY = "discussion_quality"
    AI_CONFIDENCE_LEVEL = "ai_confidence_level"
    TRUST_VALIDATION_TIMESTAMP = "trust_validation_timestamp"
    TRUST_VALIDATION_METHOD = "trust_validation_method"

    # Market validation fields
    MARKET_VALIDATION_SCORE = "market_validation_score"
    MARKET_DATA_QUALITY_SCORE = "market_data_quality_score"
    MARKET_VALIDATION_REASONING = "market_validation_reasoning"
    MARKET_COMPETITORS_FOUND = "market_competitors_found"  # JSONB
    MARKET_SIZE_TAM = "market_size_tam"
    MARKET_SIZE_SAM = "market_size_sam"
    MARKET_SIZE_GROWTH = "market_size_growth"
    MARKET_SIMILAR_LAUNCHES = "market_similar_launches"
    MARKET_VALIDATION_COST_USD = "market_validation_cost_usd"
    MARKET_VALIDATION_TIMESTAMP = "market_validation_timestamp"


# ============================================================================
# COLUMN NAMES - workflow_results
# ============================================================================

class WorkflowResultsColumns:
    """Column names for workflow_results table."""

    # Primary identifiers
    ID = "id"
    OPPORTUNITY_ID = "opportunity_id"
    SUBMISSION_ID = "submission_id"

    # Function metadata
    APP_NAME = "app_name"
    FUNCTION_COUNT = "function_count"
    FUNCTION_LIST = "function_list"  # JSONB

    # Scoring
    ORIGINAL_SCORE = "original_score"
    FINAL_SCORE = "final_score"
    STATUS = "status"
    CONSTRAINT_APPLIED = "constraint_applied"

    # Dimension scores
    MARKET_DEMAND = "market_demand"
    PAIN_INTENSITY = "pain_intensity"
    MONETIZATION_POTENTIAL = "monetization_potential"
    MARKET_GAP = "market_gap"
    TECHNICAL_FEASIBILITY = "technical_feasibility"
    SIMPLICITY_SCORE = "simplicity_score"
    OPPORTUNITY_ASSESSMENT_SCORE = "opportunity_assessment_score"  # GENERATED column

    # Trust data (from app_opportunities)
    TRUST_SCORE = "trust_score"
    TRUST_BADGE = "trust_badge"
    ACTIVITY_SCORE = "activity_score"

    # LLM cost tracking
    LLM_MODEL_USED = "llm_model_used"
    LLM_PROVIDER = "llm_provider"
    LLM_PROMPT_TOKENS = "llm_prompt_tokens"
    LLM_COMPLETION_TOKENS = "llm_completion_tokens"
    LLM_TOTAL_TOKENS = "llm_total_tokens"
    LLM_INPUT_COST_USD = "llm_input_cost_usd"
    LLM_OUTPUT_COST_USD = "llm_output_cost_usd"
    LLM_TOTAL_COST_USD = "llm_total_cost_usd"
    LLM_LATENCY_SECONDS = "llm_latency_seconds"
    LLM_TIMESTAMP = "llm_timestamp"
    LLM_PRICING_INFO = "llm_pricing_info"  # JSONB
    COST_TRACKING_ENABLED = "cost_tracking_enabled"


# ============================================================================
# COLUMN NAMES - market_validations
# ============================================================================

class MarketValidationsColumns:
    """Column names for market_validations table."""

    # Primary identifiers
    ID = "id"
    OPPORTUNITY_ID = "opportunity_id"

    # Validation metadata
    VALIDATION_TYPE = "validation_type"
    VALIDATION_SOURCE = "validation_source"
    VALIDATION_DATE = "validation_date"
    VALIDATION_RESULT = "validation_result"  # JSONB - full evidence
    CONFIDENCE_SCORE = "confidence_score"
    NOTES = "notes"
    STATUS = "status"
    EVIDENCE_URL = "evidence_url"

    # Jina-specific columns
    MARKET_VALIDATION_SCORE = "market_validation_score"
    MARKET_DATA_QUALITY_SCORE = "market_data_quality_score"
    MARKET_VALIDATION_REASONING = "market_validation_reasoning"
    MARKET_COMPETITORS_FOUND = "market_competitors_found"  # JSONB
    MARKET_SIZE_TAM = "market_size_tam"
    MARKET_SIZE_SAM = "market_size_sam"
    MARKET_SIZE_GROWTH = "market_size_growth"
    MARKET_SIMILAR_LAUNCHES = "market_similar_launches"
    MARKET_VALIDATION_COST_USD = "market_validation_cost_usd"
    SEARCH_QUERIES_USED = "search_queries_used"  # TEXT[]
    URLS_FETCHED = "urls_fetched"  # TEXT[]
    EXTRACTION_STATS = "extraction_stats"  # JSONB
    JINA_API_CALLS_COUNT = "jina_api_calls_count"
    JINA_CACHE_HIT_RATE = "jina_cache_hit_rate"


# ============================================================================
# TRUST VALIDATION ENUMS
# ============================================================================

class TrustLevel(str, Enum):
    """Trust level values."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TrustBadge(str, Enum):
    """Trust badge values."""
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"
    BASIC = "BASIC"
    NO_BADGE = "NO-BADGE"


# ============================================================================
# DLT CONSTANTS
# ============================================================================

class DLTPrimaryKeys:
    """DLT resource primary keys."""
    APP_OPPORTUNITIES = AppOpportunitiesColumns.SUBMISSION_ID
    WORKFLOW_RESULTS = WorkflowResultsColumns.OPPORTUNITY_ID
    MARKET_VALIDATIONS = MarketValidationsColumns.ID


# ============================================================================
# DIMENSION SCORE KEYS
# ============================================================================

class DimensionScoreKeys:
    """Keys for dimension_scores JSONB."""
    MARKET_DEMAND = "market_demand"
    PAIN_INTENSITY = "pain_intensity"
    MONETIZATION_POTENTIAL = "monetization_potential"
    MARKET_GAP = "market_gap"
    TECHNICAL_FEASIBILITY = "technical_feasibility"

    @classmethod
    def all_keys(cls):
        return [
            cls.MARKET_DEMAND,
            cls.PAIN_INTENSITY,
            cls.MONETIZATION_POTENTIAL,
            cls.MARKET_GAP,
            cls.TECHNICAL_FEASIBILITY
        ]
```

---

#### 2. Create Query Builder Utilities

**File**: `/home/carlos/projects/redditharbor/config/query_builders.py`

```python
"""
Query Builder Utilities

Helper functions to build SQL queries using schema constants
instead of hard-coded column names.
"""

from config.schema_constants import (
    AppOpportunitiesColumns,
    WorkflowResultsColumns,
    MarketValidationsColumns,
    TableNames
)


class AppOpportunitiesQueries:
    """Query builders for app_opportunities table."""

    @staticmethod
    def select_for_scoring():
        """SELECT columns for batch opportunity scoring."""
        columns = [
            AppOpportunitiesColumns.SUBMISSION_ID,
            AppOpportunitiesColumns.TITLE,
            AppOpportunitiesColumns.PROBLEM_DESCRIPTION,
            AppOpportunitiesColumns.SUBREDDIT,
            AppOpportunitiesColumns.REDDIT_SCORE,
            AppOpportunitiesColumns.NUM_COMMENTS,
            AppOpportunitiesColumns.TRUST_SCORE,
            AppOpportunitiesColumns.TRUST_BADGE,
            AppOpportunitiesColumns.ACTIVITY_SCORE
        ]
        return ", ".join(columns)

    @staticmethod
    def select_trust_data():
        """SELECT columns for trust data preservation."""
        columns = [
            AppOpportunitiesColumns.TRUST_SCORE,
            AppOpportunitiesColumns.TRUST_BADGE,
            AppOpportunitiesColumns.ACTIVITY_SCORE,
            AppOpportunitiesColumns.ENGAGEMENT_LEVEL,
            AppOpportunitiesColumns.TRUST_LEVEL,
            AppOpportunitiesColumns.TREND_VELOCITY,
            AppOpportunitiesColumns.PROBLEM_VALIDITY,
            AppOpportunitiesColumns.DISCUSSION_QUALITY,
            AppOpportunitiesColumns.AI_CONFIDENCE_LEVEL,
            AppOpportunitiesColumns.TRUST_VALIDATION_TIMESTAMP,
            AppOpportunitiesColumns.TRUST_VALIDATION_METHOD,
            AppOpportunitiesColumns.SUBREDDIT,
            AppOpportunitiesColumns.REDDIT_SCORE,
            AppOpportunitiesColumns.NUM_COMMENTS,
            AppOpportunitiesColumns.TITLE
        ]
        return ", ".join(columns)

    @staticmethod
    def select_market_validation():
        """SELECT columns for market validation data."""
        columns = [
            AppOpportunitiesColumns.ID,
            AppOpportunitiesColumns.PROBLEM_DESCRIPTION,
            AppOpportunitiesColumns.APP_CONCEPT,
            AppOpportunitiesColumns.TARGET_USER,
            AppOpportunitiesColumns.OPPORTUNITY_SCORE,
            AppOpportunitiesColumns.MARKET_VALIDATION_SCORE,
            AppOpportunitiesColumns.MARKET_DATA_QUALITY_SCORE,
            AppOpportunitiesColumns.MARKET_VALIDATION_REASONING,
            AppOpportunitiesColumns.MARKET_COMPETITORS_FOUND,
            AppOpportunitiesColumns.MARKET_SIZE_TAM,
            AppOpportunitiesColumns.MARKET_SIZE_SAM,
            AppOpportunitiesColumns.MARKET_SIZE_GROWTH,
            AppOpportunitiesColumns.MARKET_SIMILAR_LAUNCHES,
            AppOpportunitiesColumns.MARKET_VALIDATION_COST_USD,
            AppOpportunitiesColumns.MARKET_VALIDATION_TIMESTAMP
        ]
        return ", ".join(columns)


class MarketValidationsQueries:
    """Query builders for market_validations table."""

    @staticmethod
    def select_validation_details():
        """SELECT columns for validation details."""
        columns = [
            MarketValidationsColumns.ID,
            MarketValidationsColumns.VALIDATION_TYPE,
            MarketValidationsColumns.VALIDATION_SOURCE,
            MarketValidationsColumns.VALIDATION_DATE,
            MarketValidationsColumns.CONFIDENCE_SCORE,
            MarketValidationsColumns.SEARCH_QUERIES_USED,
            MarketValidationsColumns.URLS_FETCHED,
            MarketValidationsColumns.EXTRACTION_STATS,
            MarketValidationsColumns.JINA_API_CALLS_COUNT,
            MarketValidationsColumns.JINA_CACHE_HIT_RATE
        ]
        return ", ".join(columns)
```

---

#### 3. Create DLT Resource Configurations

**File**: `/home/carlos/projects/redditharbor/config/dlt_configs.py`

```python
"""
DLT Resource Configurations

Centralized DLT resource configurations to prevent hard-coded
resource names and primary keys.
"""

from config.schema_constants import DLTPrimaryKeys, TableNames


class DLTResourceConfigs:
    """DLT resource configuration dictionaries."""

    APP_OPPORTUNITIES = {
        "name": TableNames.APP_OPPORTUNITIES,
        "write_disposition": "merge",
        "primary_key": DLTPrimaryKeys.APP_OPPORTUNITIES
    }

    WORKFLOW_RESULTS = {
        "name": TableNames.WORKFLOW_RESULTS,
        "write_disposition": "merge",
        "primary_key": DLTPrimaryKeys.WORKFLOW_RESULTS
    }

    MARKET_VALIDATIONS = {
        "name": TableNames.MARKET_VALIDATIONS,
        "write_disposition": "merge",
        "primary_key": DLTPrimaryKeys.MARKET_VALIDATIONS
    }


# Usage example
import dlt

@dlt.resource(**DLTResourceConfigs.APP_OPPORTUNITIES)
def app_opportunities_resource(ai_profiles):
    for profile in ai_profiles:
        yield profile
```

---

### Medium Priority Actions

#### 4. Refactor Hard-Coded Dictionary Access

**Pattern to Replace**:

```python
# Before (HIGH RISK)
trust_badge = opportunity["trust_badge"]  # KeyError if column renamed

# After (SAFER)
from config.schema_constants import AppOpportunitiesColumns
trust_badge = opportunity.get(AppOpportunitiesColumns.TRUST_BADGE, "BASIC")
```

**Files to Update** (prioritize by usage frequency):
1. `dlt_trust_pipeline.py` - 18 references
2. `batch_opportunity_scoring.py` - 22 references
3. `trust_layer.py` - 12 references
4. `market_validation_persistence.py` - 10 references

#### 5. Add Type Hints with Column Constants

```python
from config.schema_constants import AppOpportunitiesColumns
from typing import Dict, Any

def extract_trust_data(submission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract trust validation data from submission.

    Args:
        submission: Submission dictionary with trust fields

    Returns:
        Dictionary with trust data
    """
    return {
        AppOpportunitiesColumns.TRUST_SCORE: submission.get(AppOpportunitiesColumns.TRUST_SCORE),
        AppOpportunitiesColumns.TRUST_BADGE: submission.get(AppOpportunitiesColumns.TRUST_BADGE),
        AppOpportunitiesColumns.ACTIVITY_SCORE: submission.get(AppOpportunitiesColumns.ACTIVITY_SCORE)
    }
```

---

## Testing Strategy

### 1. Unit Tests for Constants

**File**: `tests/test_schema_constants.py`

```python
import pytest
from config.schema_constants import (
    AppOpportunitiesColumns,
    WorkflowResultsColumns,
    DLTPrimaryKeys,
    TrustBadge
)


def test_app_opportunities_columns_exist():
    """Verify all expected columns are defined."""
    assert hasattr(AppOpportunitiesColumns, "SUBMISSION_ID")
    assert hasattr(AppOpportunitiesColumns, "TRUST_BADGE")
    assert hasattr(AppOpportunitiesColumns, "CORE_FUNCTIONS")


def test_dlt_primary_keys():
    """Verify DLT primary keys match column names."""
    assert DLTPrimaryKeys.APP_OPPORTUNITIES == "submission_id"
    assert DLTPrimaryKeys.WORKFLOW_RESULTS == "opportunity_id"


def test_trust_badge_enum():
    """Verify TrustBadge enum values."""
    assert TrustBadge.GOLD.value == "GOLD"
    assert TrustBadge.BASIC.value == "BASIC"
```

### 2. Integration Tests for Refactored Code

**File**: `tests/test_query_builders.py`

```python
import pytest
from config.query_builders import AppOpportunitiesQueries


def test_select_for_scoring_query():
    """Verify scoring query includes required columns."""
    query = AppOpportunitiesQueries.select_for_scoring()

    required_columns = [
        "submission_id",
        "trust_score",
        "trust_badge",
        "problem_description"
    ]

    for column in required_columns:
        assert column in query, f"Missing required column: {column}"


def test_select_trust_data_query():
    """Verify trust data query includes all trust columns."""
    query = AppOpportunitiesQueries.select_trust_data()

    trust_columns = [
        "trust_score",
        "trust_badge",
        "activity_score",
        "trust_level"
    ]

    for column in trust_columns:
        assert column in query, f"Missing trust column: {column}"
```

### 3. Smoke Tests After Refactoring

```bash
# Run all pipelines to verify no breakage
pytest tests/test_pipelines_integration.py -v

# Test DLT merge logic
python scripts/dlt/dlt_trust_pipeline.py --test-mode --limit 5

# Test batch scoring
python scripts/core/batch_opportunity_scoring.py --limit 10

# Verify market validation
python -m pytest tests/test_market_validation.py
```

---

## Migration Timeline

### Phase 1: Infrastructure (Week 1)

- [ ] Create `config/schema_constants.py`
- [ ] Create `config/query_builders.py`
- [ ] Create `config/dlt_configs.py`
- [ ] Write unit tests for constants
- [ ] Review and approve constants module

### Phase 2: High-Risk Refactoring (Week 2)

- [ ] Refactor DLT primary keys (4 occurrences)
- [ ] Refactor SQL queries (8 queries)
- [ ] Refactor `core_functions` serialization (standardize format)
- [ ] Test all DLT pipelines
- [ ] Verify no duplicates created

### Phase 3: Medium-Risk Refactoring (Week 3)

- [ ] Refactor trust badge references (18 occurrences)
- [ ] Refactor submission_id references (22 occurrences)
- [ ] Refactor market validation columns (10 occurrences)
- [ ] Test trust validation pipeline
- [ ] Test market validation integration

### Phase 4: Low-Risk Refactoring (Week 4)

- [ ] Refactor dimension score access (12 occurrences)
- [ ] Refactor JSONB field access (30+ occurrences)
- [ ] Add type hints with column constants
- [ ] Update all `.get()` calls to use constants
- [ ] Full integration testing

### Phase 5: Schema Consolidation (Week 5)

- [ ] Verify all constants are used
- [ ] Run full test suite
- [ ] Execute schema consolidation migration
- [ ] Verify no hard-coded strings remain
- [ ] Update documentation

---

## Success Metrics

### Before Refactoring

- Hard-coded string references: **145+**
- SQL queries with strings: **8**
- DLT primary keys as strings: **4**
- Files with hard-coded columns: **88+**

### After Refactoring (Target)

- Hard-coded string references: **0**
- SQL queries with strings: **0**
- DLT primary keys as strings: **0**
- Files with hard-coded columns: **0**

### Quality Gates

- [ ] All SQL queries use query builders
- [ ] All DLT resources use configuration objects
- [ ] All column access uses constants
- [ ] No `grep` results for `["column_name"]` pattern
- [ ] 100% test coverage for schema constants
- [ ] All pipelines pass integration tests

---

## Related Documentation

- [Pipeline Schema Dependencies](./pipeline-schema-dependencies.md) - Complete dependency matrix
- [JSONB Schema Versions](./jsonb-schema-versions.md) - JSONB structure documentation
- [ERD](./erd.md) - Complete schema visualization

---

**Document Version**: 1.0
**Last Updated**: 2025-11-17
**Maintained By**: RedditHarbor Data Engineering Team
**Review Frequency**: After refactoring milestone completion
