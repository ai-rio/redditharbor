# Pipeline Schema Dependency Matrix

**Purpose**: Complete mapping of all production pipeline dependencies on database schema to support safe schema consolidation.

**Generated**: 2025-11-17
**Critical**: This documentation must be updated before any schema changes
**Risk Level**: CRITICAL - Breaking these dependencies stops production pipelines

---

## Executive Summary

RedditHarbor has **7 active production pipelines** with dependencies on **5 critical tables**:

| Table | Pipelines Using | Breaking Change Risk | JSONB Columns |
|-------|----------------|---------------------|---------------|
| `app_opportunities` | 5 | CRITICAL | `core_functions` |
| `workflow_results` | 3 | HIGH | `function_list`, `dimension_scores` |
| `market_validations` | 2 | HIGH | `validation_result` |
| `llm_usage_tracking` | 1 | MODERATE | `cost_breakdown` |
| `public_staging.app_opportunities` | 1 | CRITICAL | `core_functions` |

**Key Findings**:
- **145+ hard-coded column references** across codebase
- **3 JSONB columns** with complex parsing logic
- **DLT merge disposition** dependencies on `submission_id` and `opportunity_id`
- **Trust validation** system tightly coupled to 12 specific columns

---

## Pipeline 1: DLT Trust Pipeline

**File**: `/home/carlos/projects/redditharbor/scripts/dlt/dlt_trust_pipeline.py`
**Purpose**: End-to-end Reddit collection → AI analysis → Trust validation → DLT storage
**Criticality**: PRODUCTION - Core data ingestion pipeline
**Last Modified**: 2025-11-17

### Table Dependencies

#### `public_staging.app_opportunities` (DLT-managed)

**Access Pattern**: Read/Write (DLT merge disposition)
**Write Disposition**: `merge` (lines 585-594)
**Primary Key**: `submission_id` (line 576)

**Column Usage**:

| Column | Type | Line References | Usage | Breaking Risk |
|--------|------|----------------|-------|---------------|
| `submission_id` | VARCHAR | 525, 576 | DLT primary key for merge deduplication | CRITICAL |
| `trust_score` | DOUBLE PRECISION | 543, 563 | Trust validation score (0-100) | HIGH |
| `trust_badge` | VARCHAR | 544, 565 | Trust indicator (GOLD/SILVER/BRONZE/BASIC) | HIGH |
| `activity_score` | DOUBLE PRECISION | 545 | Community activity metric (0-100) | HIGH |
| `opportunity_score` | DOUBLE PRECISION | 534 | AI scoring result | HIGH |
| `core_functions` | JSONB | 528 | **CRITICAL**: DLT expects JSONB, NOT TEXT[] | CRITICAL |
| `problem_description` | TEXT | 526 | Problem statement from AI analysis | MODERATE |
| `app_concept` | VARCHAR | 527 | AI-generated app concept | MODERATE |
| `value_proposition` | VARCHAR | 529 | Value proposition text | LOW |
| `target_user` | VARCHAR | 530 | Target audience description | LOW |
| `monetization_model` | VARCHAR | 531 | Revenue model | LOW |
| `confidence_score` | DOUBLE PRECISION | 546 | Numeric confidence (0-100) | HIGH |
| `engagement_level` | VARCHAR | 549 | ENUM-like: VERY_HIGH/HIGH/MEDIUM/LOW/MINIMAL | MODERATE |
| `trend_velocity` | DOUBLE PRECISION | 550 | Trend velocity score (0-100) | MODERATE |
| `problem_validity` | VARCHAR | 551 | VALID/POTENTIAL/UNCLEAR/INVALID | MODERATE |
| `discussion_quality` | VARCHAR | 552 | EXCELLENT/GOOD/FAIR/POOR | MODERATE |
| `ai_confidence_level` | VARCHAR | 553 | VERY_HIGH/HIGH/MEDIUM/LOW | MODERATE |
| `trust_validation_timestamp` | DOUBLE PRECISION | 554 | Unix timestamp | LOW |
| `trust_validation_method` | VARCHAR | 555 | Validation method identifier | LOW |
| `trust_level` | VARCHAR | 542 | Trust level from TrustLayerValidator | HIGH |
| `title` | VARCHAR | 535 | Reddit post title | LOW |
| `subreddit` | VARCHAR | 536 | Source subreddit | MODERATE |
| `reddit_score` | BIGINT | 537 | Reddit upvotes | LOW |
| `num_comments` | BIGINT | 538 | Comment count | LOW |
| `status` | VARCHAR | 539 | Record status (discovered/ai_enriched) | LOW |

**Hard-Coded References**:

```python
# Line 543: Direct dictionary access - KeyError if renamed
'trust_score': post.get('trust_score', 0)

# Line 544: Direct dictionary access - KeyError if renamed
'trust_badge': post.get('trust_badge', 'NO-BADGE')

# Line 528: JSONB serialization dependency
'core_functions': core_functions,  # Python list - DLT will handle JSON conversion

# Line 563: Validation before DLT load
print(f"   - trust_score in profile: {profile.get('trust_score')}")
```

**Critical Constraints**:
- **DLT Merge**: `submission_id` MUST be VARCHAR PRIMARY KEY (line 576)
- **JSONB Type**: `core_functions` MUST be JSONB - DLT infers from Python list (lines 510-528)
- **Trust Badge Values**: Expected ENUM-like behavior (GOLD/SILVER/BRONZE/BASIC)
- **Generated Columns**: None in staging table, but workflow_results has them

**Breaking Changes Risk**: 🔴 **CRITICAL**
- Renaming `submission_id` → Breaks DLT merge logic (automatic deduplication fails)
- Changing `core_functions` to TEXT[] → DLT deserialization fails
- Removing trust columns → Trust validation pipeline breaks
- Changing trust badge values → Badge logic fails

**Data Flow**:
```
collect_posts_with_activity_validation()
  → analyze_opportunities_with_ai()
    → apply_trust_validation() (uses TrustLayerValidator)
      → load_trusted_opportunities_to_supabase()
        → DLT pipeline writes to public_staging.app_opportunities
```

---

#### Trust Validation Integration (TrustLayerValidator)

**File**: `/home/carlos/projects/redditharbor/core/trust_layer.py`
**Lines**: 324-419 (validation method called from dlt_trust_pipeline.py)

**Dependencies**:
- Reads: `submission_id`, `title`, `text`, `subreddit`, `upvotes`, `comments_count`, `created_utc`, `permalink`
- Writes: `trust_level`, `trust_score`, `trust_badge`, `activity_score`, `confidence_score`, `engagement_level`, `trend_velocity`, `problem_validity`, `discussion_quality`, `ai_confidence_level`, `trust_validation_timestamp`, `trust_validation_method`

**Trust Badge Generation** (lines 365-369):
```python
validated_post.update({
    'trust_level': trust_indicators.trust_level.value,  # Enum: low/medium/high/very_high
    'trust_score': trust_indicators.overall_trust_score,  # 0-100
    'trust_badge': trust_indicators.trust_badges[0] if trust_indicators.trust_badges else 'BASIC',
    'activity_score': trust_indicators.subreddit_activity_score,  # 0-100
    'confidence_score': trust_indicators.get_confidence_score(),  # 0-100
})
```

**Breaking Risk**: Renaming trust columns breaks trust validation integration.

---

## Pipeline 2: Batch Opportunity Scoring

**File**: `/home/carlos/projects/redditharbor/scripts/core/batch_opportunity_scoring.py`
**Purpose**: Fetch opportunities → AI scoring → Market validation → DLT storage
**Criticality**: PRODUCTION - Primary scoring pipeline
**Last Modified**: 2025-11-17

### Table Dependencies

#### `app_opportunities` (Read Operations)

**Access Pattern**: Read (lines 224-227)
**Query Pattern**: Batch pagination with offset (lines 222-241)

**SQL Query**:
```python
# Line 224
query = supabase_client.table("app_opportunities").select(
    "submission_id, title, problem_description, subreddit, reddit_score, "
    "num_comments, trust_score, trust_badge, activity_score"
).range(offset, offset + batch_size - 1)
```

**Column Usage**:

| Column | Type | Line References | Usage | Breaking Risk |
|--------|------|----------------|-------|---------------|
| `submission_id` | VARCHAR | 224, 407 | Primary identifier, DLT merge key | CRITICAL |
| `title` | VARCHAR | 224, 336 | Post title for analysis | MODERATE |
| `problem_description` | TEXT | 224, 336 | Problem statement | HIGH |
| `subreddit` | VARCHAR | 224, 359 | Source subreddit | MODERATE |
| `reddit_score` | BIGINT | 224, 341 | Reddit upvotes | LOW |
| `num_comments` | BIGINT | 224, 342 | Comment count | LOW |
| `trust_score` | DOUBLE PRECISION | 226, 350, 1160 | Trust validation score | HIGH |
| `trust_badge` | VARCHAR | 226, 352, 1162 | Trust badge value | HIGH |
| `activity_score` | DOUBLE PRECISION | 226, 1162 | Activity score | HIGH |

**Hard-Coded References**:

```python
# Line 226: Direct SELECT query - breaks if columns renamed
"num_comments, trust_score, trust_badge, activity_score"

# Line 350: Conditional trust metadata extraction
trust_score = submission.get("trust_score")
if trust_score:
    comments.append(f"Trust Score: {trust_score}")

# Line 1160-1162: Trust data extraction for DLT
trust_data = {
    "trust_score": submission.get("trust_score"),
    "trust_badge": submission.get("trust_badge"),
    "activity_score": submission.get("activity_score")
}
```

**Breaking Changes Risk**: 🟡 **HIGH**
- Renaming `submission_id` → Breaks DLT merge and queries
- Removing trust columns → Trust data not passed to workflow_results
- Changing column names → SELECT query fails

---

#### `app_opportunities` (Write Operations via DLT)

**Access Pattern**: Write (DLT merge disposition)
**Function**: `store_ai_profiles_to_app_opportunities_via_dlt()` (lines 574-670)
**Write Disposition**: `merge` (line 658)
**Primary Key**: `submission_id` (line 659)

**Updated Columns**:

| Column | Type | Line References | Usage | Breaking Risk |
|--------|------|----------------|-------|---------------|
| `submission_id` | VARCHAR | 606, 622, 659 | Merge key | CRITICAL |
| `problem_description` | TEXT | 623 | AI-generated | HIGH |
| `app_concept` | VARCHAR | 624 | AI-generated | HIGH |
| `core_functions` | TEXT/VARCHAR | 625 | **Format**: Comma-separated string! | CRITICAL |
| `value_proposition` | VARCHAR | 626 | AI-generated | MODERATE |
| `target_user` | VARCHAR | 627 | AI-generated | MODERATE |
| `monetization_model` | VARCHAR | 628 | AI-generated | MODERATE |
| `opportunity_score` | DOUBLE PRECISION | 629 | Final AI score | HIGH |
| `title` | VARCHAR | 630 | Preserved from original | LOW |
| `status` | VARCHAR | 631 | Updated to "ai_enriched" | MODERATE |
| `trust_score` | DOUBLE PRECISION | 633 | **Preserved** from original | HIGH |
| `trust_badge` | VARCHAR | 634 | **Preserved** from original | HIGH |
| `activity_score` | DOUBLE PRECISION | 635 | **Preserved** from original | HIGH |
| `engagement_level` | VARCHAR | 636 | **Preserved** from trust layer | MODERATE |
| `trust_level` | VARCHAR | 637 | **Preserved** from trust layer | MODERATE |
| `trend_velocity` | DOUBLE PRECISION | 638 | **Preserved** from trust layer | MODERATE |
| `problem_validity` | VARCHAR | 639 | **Preserved** from trust layer | MODERATE |
| `discussion_quality` | VARCHAR | 640 | **Preserved** from trust layer | MODERATE |
| `ai_confidence_level` | VARCHAR | 641 | **Preserved** from trust layer | MODERATE |
| `trust_validation_timestamp` | TIMESTAMP | 642 | **Preserved** from trust layer | LOW |
| `trust_validation_method` | VARCHAR | 643 | **Preserved** from trust layer | LOW |
| `subreddit` | VARCHAR | 645 | **Preserved** from original | MODERATE |
| `reddit_score` | BIGINT | 646 | **Preserved** from original | LOW |
| `num_comments` | BIGINT | 647 | **Preserved** from original | LOW |

**Critical Issue - core_functions Format Mismatch**:

```python
# Line 625: Converts list to comma-separated string!
"core_functions": ", ".join(opp.get("function_list", [])) if isinstance(opp.get("function_list"), list) else str(opp.get("function_list", "")),
```

**⚠️ WARNING**: This creates format inconsistency:
- `dlt_trust_pipeline.py` writes `core_functions` as **JSONB** (Python list)
- `batch_opportunity_scoring.py` writes `core_functions` as **VARCHAR** (comma-separated string)
- **Risk**: Query inconsistencies and parsing errors

**Breaking Changes Risk**: 🔴 **CRITICAL**
- Changing `submission_id` type → DLT merge fails
- Removing trust columns → Trust preservation fails
- Changing `core_functions` schema → Format mismatch worsens

**Trust Preservation Pattern**:
```python
# Lines 607-618: Fetch existing trust data before updating
existing = supabase.table("app_opportunities").select(
    "trust_score, trust_badge, activity_score, engagement_level, "
    "trust_level, trend_velocity, problem_validity, discussion_quality, "
    "ai_confidence_level, trust_validation_timestamp, trust_validation_method, "
    "subreddit, reddit_score, num_comments, title"
).eq("submission_id", submission_id).execute()

trust_data = existing.data[0] if existing.data else {}
```

**Design Pattern**: Fetch-then-merge to preserve trust indicators during AI enrichment.

---

#### `workflow_results` (Write Operations via DLT)

**Access Pattern**: Write (DLT merge disposition)
**Function**: `load_scores_to_supabase_via_dlt()` (lines 466-572)
**Write Disposition**: `merge` (line 549)
**Primary Key**: `opportunity_id` (line 550)

**Column Usage**:

| Column | Type | Line References | Usage | Data Source | Breaking Risk |
|--------|------|----------------|-------|-------------|---------------|
| `opportunity_id` | VARCHAR | 384, 405, 550 | Merge key (f"opp_{submission_id}") | Generated | CRITICAL |
| `submission_id` | VARCHAR | 384, 406 | Reddit post ID | From app_opportunities | HIGH |
| `app_name` | VARCHAR | 407 | App concept name | AI analysis | MODERATE |
| `function_count` | INTEGER | 408 | Count of core functions | Derived from function_list | HIGH |
| `function_list` | JSONB | 409 | **List of function names** | AI analysis | CRITICAL |
| `original_score` | DOUBLE PRECISION | 410 | AI score before constraints | AI analysis | MODERATE |
| `final_score` | DOUBLE PRECISION | 411 | AI score after constraints | AI analysis | HIGH |
| `status` | VARCHAR | 412 | Record status | Always "scored" | LOW |
| `constraint_applied` | BOOLEAN | 413 | 1-3 function rule applied | Always True | LOW |
| `ai_insight` | TEXT | 414 | Analysis insights | Generated | LOW |
| `subreddit` | VARCHAR | 415 | Source subreddit | AI analysis | MODERATE |
| `processed_at` | TIMESTAMP | 416 | Processing timestamp | Generated | LOW |
| `trust_score` | DOUBLE PRECISION | 418 | **From app_opportunities** | Trust validation | HIGH |
| `trust_badge` | VARCHAR | 419 | **From app_opportunities** | Trust validation | HIGH |
| `activity_score` | DOUBLE PRECISION | 420 | **From app_opportunities** | Trust validation | HIGH |
| `market_demand` | DOUBLE PRECISION | 422 | Dimension score (0-100) | AI analysis | HIGH |
| `pain_intensity` | DOUBLE PRECISION | 423 | Dimension score (0-100) | AI analysis | HIGH |
| `monetization_potential` | DOUBLE PRECISION | 424 | Dimension score (0-100) | AI analysis | HIGH |
| `market_gap` | DOUBLE PRECISION | 425 | Dimension score (0-100) | AI analysis | HIGH |
| `technical_feasibility` | DOUBLE PRECISION | 426 | Dimension score (0-100) | AI analysis | HIGH |
| `problem_description` | VARCHAR(500) | 428 | Truncated to 500 chars | AI analysis | MODERATE |
| `app_concept` | VARCHAR(500) | 429 | Truncated to 500 chars | AI analysis | MODERATE |
| `value_proposition` | VARCHAR(500) | 430 | Truncated to 500 chars | AI analysis | MODERATE |
| `target_user` | VARCHAR(255) | 431 | Truncated to 255 chars | AI analysis | MODERATE |
| `monetization_model` | VARCHAR(255) | 432 | Truncated to 255 chars | AI analysis | MODERATE |
| `llm_model_used` | VARCHAR | 434 | LLM model name | Cost tracking | MODERATE |
| `llm_provider` | VARCHAR | 435 | LLM provider | Cost tracking | LOW |
| `llm_prompt_tokens` | INTEGER | 436 | Token count | Cost tracking | LOW |
| `llm_completion_tokens` | INTEGER | 437 | Token count | Cost tracking | LOW |
| `llm_total_tokens` | INTEGER | 438 | Token count | Cost tracking | LOW |
| `llm_input_cost_usd` | DOUBLE PRECISION | 439 | Cost in USD | Cost tracking | MODERATE |
| `llm_output_cost_usd` | DOUBLE PRECISION | 440 | Cost in USD | Cost tracking | MODERATE |
| `llm_total_cost_usd` | DOUBLE PRECISION | 441 | Cost in USD | Cost tracking | MODERATE |
| `llm_latency_seconds` | DOUBLE PRECISION | 442 | API latency | Cost tracking | LOW |
| `llm_timestamp` | TIMESTAMP | 443 | LLM call timestamp | Cost tracking | LOW |
| `llm_pricing_info` | JSONB | 444 | **Pricing model data** | Cost tracking | MODERATE |
| `cost_tracking_enabled` | BOOLEAN | 445 | Flag for cost tracking | Cost tracking | LOW |
| `market_validation_score` | DOUBLE PRECISION | 452 | Market validation score | Market validator | HIGH |
| `market_data_quality_score` | DOUBLE PRECISION | 453 | Data quality score | Market validator | HIGH |
| `market_validation_reasoning` | VARCHAR(1000) | 454 | Validation reasoning | Market validator | MODERATE |
| `market_competitors_found` | JSONB | 455 | **Competitor list** | Market validator | HIGH |
| `market_size_tam` | VARCHAR | 456 | Total addressable market | Market validator | MODERATE |
| `market_size_growth` | VARCHAR | 457 | Market growth rate | Market validator | MODERATE |
| `market_similar_launches` | INTEGER | 458 | Similar product count | Market validator | LOW |
| `market_validation_cost_usd` | DOUBLE PRECISION | 459 | Validation cost | Market validator | MODERATE |
| `market_validation_timestamp` | TIMESTAMP | 460 | Validation timestamp | Market validator | LOW |

**Hard-Coded References**:

```python
# Line 384: opportunity_id generation pattern
opportunity_id = f"opp_{submission_id}"

# Line 408-409: function_count and function_list relationship
"function_count": len(core_functions),
"function_list": core_functions,  # JSONB array

# Line 418-420: Trust data from app_opportunities
"trust_score": float(trust_data.get("trust_score", 0)) if trust_data and trust_data.get("trust_score") else None,
"trust_badge": trust_data.get("trust_badge", "")[:50] if trust_data and trust_data.get("trust_badge") else None,
"activity_score": float(trust_data.get("activity_score", 0)) if trust_data and trust_data.get("activity_score") else None,

# Line 422-426: Dimension scores from AI analysis
"market_demand": float(scores.get("market_demand", 0)) if scores else None,
"pain_intensity": float(scores.get("pain_intensity", 0)) if scores else None,
"monetization_potential": float(scores.get("monetization_potential", 0)) if scores else None,
"market_gap": float(scores.get("market_gap", 0)) if scores else None,
"technical_feasibility": float(scores.get("technical_feasibility", 0)) if scores else None,

# Line 455: JSONB competitors list
"market_competitors_found": market_evidence.get("competitors_found", []),
```

**GENERATED Column Dependency**:

⚠️ **CRITICAL**: The ERD shows `workflow_results.opportunity_assessment_score` is a **GENERATED ALWAYS** column:

```sql
-- From ERD (docs/schema-consolidation/erd.md, lines 283-291)
workflow_results {
    numeric opportunity_assessment_score "GENERATED: Weighted total"
}
```

**Breaking Risk**: If dimension score columns are renamed, the GENERATED column formula breaks.

**Pre-flight Validation** (lines 487-512):
```python
# Check: Every opportunity has function_list
missing_functions = [
    o["opportunity_id"] for o in scored_opportunities
    if not o.get("function_list")
]
if missing_functions:
    raise ValueError(f"Cannot load: {len(missing_functions)} missing function_list")

# Check: function_count matches function_list length
mismatches = [
    o for o in scored_opportunities
    if len(o.get("function_list", [])) != o.get("function_count")
]
```

**Constraint Validation** (lines 520-536):
```python
# DLT constraint validator (1-3 function rule)
validated_opportunities = list(app_opportunities_with_constraint(scored_opportunities))
approved = [o for o in validated_opportunities if not o.get("is_disqualified")]
disqualified = [o for o in validated_opportunities if o.get("is_disqualified")]

print(f"  ✓ Approved: {len(approved)}")
print(f"  ⚠️  Disqualified: {len(disqualified)}")
```

**Breaking Changes Risk**: 🔴 **CRITICAL**
- Renaming `opportunity_id` → DLT merge fails, duplicates created
- Changing `function_list` type from JSONB → Parsing errors in constraint validator
- Renaming dimension score columns → GENERATED column formula breaks
- Removing `trust_score`/`trust_badge`/`activity_score` → Trust tracking lost

---

#### Market Validation Integration

**Function**: `perform_market_validation()` (lines 672-728)
**Conditional Execution**: Only if `final_score >= 60.0` and market validation enabled

**Market Evidence Structure** (lines 1107-1117):
```python
evidence_dict = {
    "validation_score": market_evidence.validation_score,  # 0-100
    "data_quality_score": market_evidence.data_quality_score,  # 0-100
    "reasoning": market_evidence.reasoning,  # Text
    "total_cost": market_evidence.total_cost,  # USD
    "timestamp": market_evidence.timestamp.isoformat(),  # ISO datetime
    "competitors_found": [p.company_name for p in market_evidence.competitor_pricing],  # List[str]
    "tam_value": market_evidence.market_size.tam_value if market_evidence.market_size else None,
    "growth_rate": market_evidence.market_size.growth_rate if market_evidence.market_size else None,
    "similar_launches_count": len(market_evidence.similar_launches),  # Integer
}
```

**Storage** (lines 449-461):
```python
if market_evidence:
    analysis_data.update({
        "market_validation_score": float(market_evidence.get("validation_score", 0)),
        "market_data_quality_score": float(market_evidence.get("data_quality_score", 0)),
        "market_validation_reasoning": market_evidence.get("reasoning", "")[:1000],
        "market_competitors_found": market_evidence.get("competitors_found", []),  # JSONB
        "market_size_tam": market_evidence.get("tam_value"),
        "market_size_growth": market_evidence.get("growth_rate"),
        "market_similar_launches": market_evidence.get("similar_launches_count", 0),
        "market_validation_cost_usd": float(market_evidence.get("total_cost", 0)),
        "market_validation_timestamp": market_evidence.get("timestamp"),
    })
```

**Dependencies on `market_validations` table**: See Pipeline 4 below.

---

## Pipeline 3: Trust Layer Validator

**File**: `/home/carlos/projects/redditharbor/core/trust_layer.py`
**Purpose**: Comprehensive trust validation with 6-dimensional scoring
**Criticality**: PRODUCTION - Used by DLT Trust Pipeline
**Integration**: Called from `dlt_trust_pipeline.py` line 359

### Trust Validation System

**Function**: `validate_opportunity_trust()` (lines 78-136)
**Returns**: `TrustIndicators` dataclass with 18 fields

#### Input Dependencies

**submission_data Dictionary** (line 78):

| Field | Type | Line Usage | Breaking Risk |
|-------|------|-----------|---------------|
| `subreddit` | str | 149, 239 | HIGH |
| `upvotes` | int | 171, 201, 241 | HIGH |
| `comments_count` | int | 172, 202, 242, 272 | HIGH |
| `created_utc` | float/str | 200, 208 | HIGH |
| `text` or `content` | str | 251, 335 | HIGH |
| `title` | str | 335 | MODERATE |

**ai_analysis Dictionary** (line 78):

| Field | Type | Line Usage | Breaking Risk |
|-------|------|-----------|---------------|
| `problem_description` | str | 242, 259, 320 | HIGH |
| `app_concept` | str | 247, 315 | HIGH |
| `core_functions` | list | 310 | CRITICAL |
| `final_score` | float | 290 | HIGH |

#### Output Structure (TrustIndicators Dataclass)

**Lines 34-62**:

| Field | Type | Range | Breaking Risk |
|-------|------|-------|---------------|
| `subreddit_activity_score` | float | 0-100 | HIGH |
| `post_engagement_score` | float | 0-100 | HIGH |
| `community_health_score` | float | 0-100 | MODERATE |
| `trend_velocity_score` | float | 0-100 | HIGH |
| `problem_validity_score` | float | 0-100 | HIGH |
| `discussion_quality_score` | float | 0-100 | HIGH |
| `ai_analysis_confidence` | float | 0-100 | HIGH |
| `overall_trust_score` | float | 0-100 | CRITICAL |
| `trust_level` | TrustLevel (Enum) | LOW/MEDIUM/HIGH/VERY_HIGH | HIGH |
| `trust_badges` | list[str] | Badge list | MODERATE |
| `validation_timestamp` | str | ISO datetime | LOW |
| `validation_method` | str | "comprehensive_trust_layer" | LOW |
| `activity_constraints_met` | bool | True/False | MODERATE |
| `quality_constraints_met` | bool | True/False | MODERATE |

#### Trust Score Calculation (lines 69-76)

**Weighted Formula**:
```python
self.trust_weights = {
    "subreddit_activity": 0.25,   # 25%
    "post_engagement": 0.20,      # 20%
    "trend_velocity": 0.15,        # 15%
    "problem_validity": 0.15,      # 15%
    "discussion_quality": 0.15,    # 15%
    "ai_confidence": 0.10          # 10%
}
```

**Formula** (lines 333-340):
```python
overall_score = (
    indicators.subreddit_activity_score * 0.25 +
    indicators.post_engagement_score * 0.20 +
    indicators.trend_velocity_score * 0.15 +
    indicators.problem_validity_score * 0.15 +
    indicators.discussion_quality_score * 0.15 +
    indicators.ai_analysis_confidence * 0.10
)
```

**Breaking Risk**: Changing weight constants breaks scoring methodology.

#### Trust Badge Generation (lines 359-404)

**Badge Logic**:
- Activity: Based on `subreddit_activity_score` (lines 364-370)
- Engagement: Based on `post_engagement_score` (lines 373-376)
- Trend: Based on `trend_velocity_score` (lines 379-382)
- Quality: Based on `quality_constraints_met` (lines 385-386)
- AI Confidence: Based on `ai_analysis_confidence` (lines 389-392)
- Overall Trust: Based on `trust_level` enum (lines 395-402)

**Badge Examples**:
- "🔥 Highly Active Community" (activity_score >= 80)
- "📈 High Engagement" (engagement_score >= 70)
- "🚀 Trending Topic" (trend_velocity >= 80)
- "✅ Quality Verified" (quality_constraints_met)
- "🏆 Premium Quality" (trust_level == VERY_HIGH)

**Breaking Changes Risk**: 🟡 **HIGH**
- Changing input field names → Trust validation fails
- Modifying trust weights → Scoring methodology changes
- Altering TrustLevel enum → Badge generation breaks
- Removing `core_functions` validation → Quality constraint fails

---

## Pipeline 4: Market Validation Integration

**Files**:
- `/home/carlos/projects/redditharbor/agent_tools/market_validation_integration.py`
- `/home/carlos/projects/redditharbor/agent_tools/market_validation_persistence.py`

**Purpose**: Validate opportunities with external market data from Jina Reader API
**Criticality**: PRODUCTION - Phase 3 data validation
**Integration**: Called from `batch_opportunity_scoring.py` lines 1088-1143

### Table Dependencies

#### `app_opportunities` (Update Operations)

**File**: `market_validation_persistence.py`
**Function**: `save_validation_evidence()` (lines 63-200)
**Access Pattern**: Update existing records (line 147)

**Updated Columns**:

| Column | Type | Line References | Data Source | Breaking Risk |
|--------|------|----------------|-------------|---------------|
| `market_validation_score` | DOUBLE PRECISION | 133 | ValidationEvidence.validation_score | HIGH |
| `market_data_quality_score` | DOUBLE PRECISION | 134 | ValidationEvidence.data_quality_score | HIGH |
| `market_validation_reasoning` | TEXT | 135 | ValidationEvidence.reasoning | MODERATE |
| `market_competitors_found` | JSONB | 136 | **List of competitor names** | HIGH |
| `market_size_tam` | VARCHAR | 137 | Total addressable market | MODERATE |
| `market_size_sam` | VARCHAR | 138 | Serviceable addressable market | MODERATE |
| `market_size_growth` | VARCHAR | 139 | Market growth rate | MODERATE |
| `market_similar_launches` | INTEGER | 140 | Count of similar products | LOW |
| `market_validation_cost_usd` | DOUBLE PRECISION | 141 | Jina API cost | MODERATE |
| `market_validation_timestamp` | TIMESTAMP | 142 | Validation timestamp | LOW |

**SQL Query** (line 147):
```python
app_response = self.client.table("app_opportunities").update(
    app_opportunities_data
).eq("id", app_opportunity_id)
```

**Hard-Coded References**:

```python
# Line 108: Competitor serialization
competitors_found = self._serialize_competitors(evidence.competitor_pricing)

# Line 109-111: Market size extraction
market_size_tam = evidence.market_size.tam_value if evidence.market_size else None
market_size_sam = evidence.market_size.sam_value if evidence.market_size else None
market_size_growth = evidence.market_size.growth_rate if evidence.market_size else None

# Line 112: Similar launches count
similar_launches = len(evidence.similar_launches)
```

**Breaking Changes Risk**: 🟡 **HIGH**
- Renaming market validation columns → UPDATE fails
- Changing `market_competitors_found` from JSONB → Serialization fails
- Removing columns → Data loss for market validation

---

#### `market_validations` (Insert Operations)

**Access Pattern**: Insert new records (line 185)
**Primary Key**: `id` (auto-generated UUID)

**Inserted Columns**:

| Column | Type | Line References | Data Source | Breaking Risk |
|--------|------|----------------|-------------|---------------|
| `opportunity_id` | UUID | 159 | From app_opportunities or fallback | CRITICAL |
| `validation_type` | VARCHAR | 160 | "jina_reader_market_validation" | LOW |
| `validation_source` | VARCHAR | 161 | "jina_api" | LOW |
| `validation_date` | TIMESTAMP | 162 | Current timestamp | LOW |
| `validation_result` | JSONB | 163 | **Full evidence object** | CRITICAL |
| `confidence_score` | NUMERIC(5,4) | 164 | data_quality_score / 100 | MODERATE |
| `notes` | TEXT | 165 | Reasoning text | LOW |
| `status` | VARCHAR | 166 | "completed" | LOW |
| `evidence_url` | TEXT | 167 | Extracted URLs | LOW |
| `market_validation_score` | DOUBLE PRECISION | 169 | Validation score | HIGH |
| `market_data_quality_score` | DOUBLE PRECISION | 170 | Data quality score | HIGH |
| `market_validation_reasoning` | TEXT | 171 | Reasoning | MODERATE |
| `market_competitors_found` | JSONB | 172 | **Competitor list** | HIGH |
| `market_size_tam` | VARCHAR | 173 | TAM value | MODERATE |
| `market_size_sam` | VARCHAR | 174 | SAM value | MODERATE |
| `market_size_growth` | VARCHAR | 175 | Growth rate | MODERATE |
| `market_similar_launches` | INTEGER | 176 | Similar product count | LOW |
| `market_validation_cost_usd` | DOUBLE PRECISION | 177 | API cost | MODERATE |
| `search_queries_used` | TEXT[] | 178 | Search queries | LOW |
| `urls_fetched` | TEXT[] | 179 | Fetched URLs | LOW |
| `extraction_stats` | JSONB | 180 | **Extraction statistics** | MODERATE |
| `jina_api_calls_count` | INTEGER | 181 | API call count | LOW |
| `jina_cache_hit_rate` | DOUBLE PRECISION | 182 | Cache efficiency | LOW |

**SQL Query** (line 185):
```python
validation_response = self.client.table("market_validations").insert(
    market_validation_data
)
```

**JSONB Column: `validation_result`** (line 163):

Structure (from `_serialize_validation_result()` method):
```python
{
    "validation_score": 85.5,
    "data_quality_score": 72.3,
    "reasoning": "Strong market validation...",
    "competitor_pricing": [
        {
            "company_name": "CompetitorA",
            "pricing_model": "Subscription",
            "monthly_price": "$29/mo",
            "features": ["Feature 1", "Feature 2"]
        }
    ],
    "market_size": {
        "tam_value": "$2.5B",
        "sam_value": "$500M",
        "som_value": "$50M",
        "growth_rate": "15% CAGR"
    },
    "similar_launches": [
        {
            "product_name": "Similar Product",
            "launch_platform": "Product Hunt",
            "launch_date": "2023-06-15",
            "success_metrics": "500+ upvotes"
        }
    ],
    "data_sources": ["jina_reader", "external_api"],
    "timestamp": "2025-11-17T12:34:56Z"
}
```

**Breaking Changes Risk**: 🔴 **CRITICAL**
- Renaming `opportunity_id` → Foreign key relationship breaks
- Changing `validation_result` JSONB structure → Parsing fails
- Removing `market_competitors_found` or `extraction_stats` → Data loss
- Changing column types → INSERT fails

---

#### Retrieval Operations

**Function**: `get_market_validation()` (lines 202-262)
**Access Pattern**: Read (JOIN pattern)

**SQL Queries**:

```python
# Line 214: app_opportunities query
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

# Line 238: market_validations query
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

**Breaking Changes Risk**: 🟡 **HIGH**
- Renaming columns in SELECT queries → Query fails
- Removing columns → Incomplete data returned
- Changing foreign key relationship → JOIN pattern breaks

---

## Pipeline 5: DLT App Opportunities

**File**: `/home/carlos/projects/redditharbor/core/dlt_app_opportunities.py`
**Purpose**: DLT resource for app_opportunities with deduplication
**Criticality**: PRODUCTION - Used by batch_opportunity_scoring.py
**Integration**: Called from batch_opportunity_scoring.py lines 656-666

### Table Dependencies

#### `app_opportunities` (DLT Resource)

**Access Pattern**: Write (DLT merge disposition)
**Write Disposition**: `merge` (line 39)
**Primary Key**: `submission_id` (line 40)

**DLT Resource Definition** (lines 37-62):

```python
@dlt.resource(
    name="app_opportunities",
    write_disposition="merge",  # Deduplication via primary key
    primary_key="submission_id",  # Specify primary key for merge operations
)
def app_opportunities_resource(ai_profiles: list[dict[str, Any]]):
    """
    DLT resource for app_opportunities with automatic deduplication.
    """
    import json

    for profile in ai_profiles:
        # Only yield if it has AI-generated content
        if profile.get("problem_description"):
            # Convert core_functions from Python list to JSON string for jsonb
            if "core_functions" in profile and isinstance(profile["core_functions"], list):
                profile["core_functions"] = json.dumps(profile["core_functions"])
            yield profile
```

**Critical core_functions Handling** (lines 60-61):

```python
# Convert core_functions from Python list to JSON string for JSONB
if "core_functions" in profile and isinstance(profile["core_functions"], list):
    profile["core_functions"] = json.dumps(profile["core_functions"])
```

**⚠️ Format Inconsistency Alert**:

| File | core_functions Format | Line Reference |
|------|----------------------|----------------|
| `dlt_app_opportunities.py` | JSON string from Python list | 61 |
| `dlt_trust_pipeline.py` | Python list (DLT auto-converts) | 528 |
| `batch_opportunity_scoring.py` | Comma-separated string | 625 |

**Risk**: Three different serialization approaches for same column!

**Breaking Changes Risk**: 🔴 **CRITICAL**
- Changing `submission_id` type → DLT merge fails
- Removing `problem_description` → All records filtered (line 58)
- Changing `core_functions` expected type → Serialization fails
- Modifying primary key → Duplicates created

**Load Function** (lines 65-135):

```python
def load_app_opportunities(ai_profiles: list[dict[str, Any]]) -> bool:
    """
    Load AI profiles to app_opportunities table with DLT deduplication.
    """
    if not ai_profiles:
        print("⚠️  No AI profiles to load")
        return False

    # Filter to only profiles with AI content
    ai_only = [p for p in ai_profiles if p.get("problem_description")]

    if not ai_only:
        print("⚠️  No AI-generated profiles found (all missing problem_description)")
        return False

    pipeline = create_app_opportunities_pipeline()

    try:
        # Run DLT pipeline with merge disposition
        load_info = pipeline.run(
            app_opportunities_resource(ai_only),
            primary_key="submission_id"
        )

        return True

    except Exception as e:
        print(f"✗ AI profile load failed: {e}")
        return False
```

**Design Pattern**: Filter → Convert → DLT Load with merge deduplication

---

## Pipeline 6: AgentOps Cost Tracking

**Pattern**: Implicit via `llm_usage_tracking` columns in `workflow_results`
**Files**: Cost tracking integrated into `batch_opportunity_scoring.py`
**Criticality**: MODERATE - Cost monitoring, not blocking

### Table Dependencies

#### `workflow_results` (LLM Cost Columns)

**Cost Tracking Columns** (batch_opportunity_scoring.py lines 434-446):

| Column | Type | Data Source | Breaking Risk |
|--------|------|-------------|---------------|
| `llm_model_used` | VARCHAR | `cost_data.get("model_used")` | MODERATE |
| `llm_provider` | VARCHAR | `cost_data.get("provider", "openrouter")` | LOW |
| `llm_prompt_tokens` | INTEGER | `cost_data.get("prompt_tokens", 0)` | LOW |
| `llm_completion_tokens` | INTEGER | `cost_data.get("completion_tokens", 0)` | LOW |
| `llm_total_tokens` | INTEGER | `cost_data.get("total_tokens", 0)` | LOW |
| `llm_input_cost_usd` | DOUBLE PRECISION | `cost_data.get("input_cost_usd", 0.0)` | MODERATE |
| `llm_output_cost_usd` | DOUBLE PRECISION | `cost_data.get("output_cost_usd", 0.0)` | MODERATE |
| `llm_total_cost_usd` | DOUBLE PRECISION | `cost_data.get("total_cost_usd", 0.0)` | MODERATE |
| `llm_latency_seconds` | DOUBLE PRECISION | `cost_data.get("latency_seconds", 0.0)` | LOW |
| `llm_timestamp` | TIMESTAMP | `cost_data.get("timestamp")` | LOW |
| `llm_pricing_info` | JSONB | `cost_data.get("model_pricing_per_m_tokens", {})` | MODERATE |
| `cost_tracking_enabled` | BOOLEAN | `bool(cost_data)` | LOW |

**Cost Tracking Flow**:

```python
# Line 401: Extract cost data from AI analysis
cost_data = analysis.get("cost_tracking", {})

# Lines 434-446: Prepare for storage
"llm_model_used": cost_data.get("model_used"),
"llm_provider": cost_data.get("provider", "openrouter"),
"llm_prompt_tokens": cost_data.get("prompt_tokens", 0),
# ... etc
"llm_pricing_info": cost_data.get("model_pricing_per_m_tokens", {}),  # JSONB
"cost_tracking_enabled": bool(cost_data),
```

**JSONB Column: `llm_pricing_info`** (line 444):

Expected structure:
```json
{
    "prompt": 0.15,      // $ per 1M tokens
    "completion": 0.60   // $ per 1M tokens
}
```

**Breaking Changes Risk**: 🟡 **MODERATE**
- Renaming cost columns → Cost tracking reports break
- Changing `llm_pricing_info` JSONB structure → Pricing analysis fails
- Removing columns → Cost monitoring lost (non-blocking)

---

## Pipeline 7: Marimo Dashboards

**Files**: `marimo_notebooks/*.py`
**Purpose**: Interactive data visualization dashboards
**Criticality**: LOW - Reporting only, not production critical
**Note**: Specific file analysis pending (requires file access)

### Expected Dependencies

Based on ERD and other pipelines, Marimo dashboards likely query:

| Table | Expected Columns | Usage |
|-------|-----------------|-------|
| `workflow_results` | `opportunity_assessment_score`, `market_demand`, `pain_intensity`, `monetization_potential` | Score visualization |
| `app_opportunities` | `trust_score`, `trust_badge`, `activity_score` | Trust analysis |
| `market_validations` | `market_validation_score`, `market_competitors_found` | Market validation dashboard |

**Breaking Changes Risk**: 🟢 **LOW**
- Dashboard queries can be updated independently
- No write operations
- Non-blocking for production pipelines

---

## Critical Constraint: 1-3 Core Functions Rule

**Implemented In**: `core/dlt/constraint_validator.py`
**Used By**: batch_opportunity_scoring.py lines 522-560
**Business Rule**: Opportunities with 4+ core functions are disqualified

### Constraint Logic

**Function**: `app_opportunities_with_constraint()` (lines 22-80)

```python
@dlt.resource(
    name="workflow_results",
    write_disposition="merge",
    primary_key="opportunity_id"
)
def app_opportunities_with_constraint(opportunities):
    """
    DLT resource with native 1-3 core function constraint validation.
    """
    for opportunity in opportunities:
        # Extract function list and count
        function_list = opportunity.get("function_list", [])
        function_count = len(function_list) if isinstance(function_list, list) else 0

        # Validate constraint: 1-3 functions
        if function_count < 1 or function_count > 3:
            opportunity["is_disqualified"] = True
            opportunity["violation_reason"] = f"Invalid function count: {function_count} (must be 1-3)"
            opportunity["simplicity_score"] = 0
        else:
            opportunity["is_disqualified"] = False
            opportunity["violation_reason"] = None
            # Calculate simplicity score: 1 func = 100, 2 = 85, 3 = 70
            simplicity_score_map = {1: 100, 2: 85, 3: 70}
            opportunity["simplicity_score"] = simplicity_score_map.get(function_count, 0)

        yield opportunity
```

**Hard-Coded References**:

```python
# Line 40: function_list extraction
function_list = opportunity.get("function_list", [])

# Line 46: is_disqualified flag (added to record)
opportunity["is_disqualified"] = True

# Line 47: violation_reason message
opportunity["violation_reason"] = f"Invalid function count: {function_count} (must be 1-3)"

# Line 48: simplicity_score reset
opportunity["simplicity_score"] = 0

# Line 54: simplicity_score calculation
simplicity_score_map = {1: 100, 2: 85, 3: 70}
opportunity["simplicity_score"] = simplicity_score_map.get(function_count, 0)
```

**Breaking Changes Risk**: 🔴 **CRITICAL**
- Renaming `function_list` → Constraint validation breaks
- Changing simplicity score calculation → Scoring methodology changes
- Removing `is_disqualified` or `violation_reason` → Validation tracking lost

---

## Hard-Coded Column References Summary

### Critical Hard-Coded Patterns

**Pattern 1: Direct Dictionary Access**

```python
# High risk - KeyError if column renamed
opportunity["trust_badge"]
post.get("submission_id")
analysis["dimension_scores"]["market_demand"]
```

**Occurrences**: 145+ across all pipelines

**Pattern 2: SQL SELECT Queries**

```python
# High risk - Query fails if columns renamed
query = supabase_client.table("app_opportunities").select(
    "submission_id, title, problem_description, subreddit, reddit_score, "
    "num_comments, trust_score, trust_badge, activity_score"
)
```

**Occurrences**: 8 SELECT queries

**Pattern 3: DLT Primary Keys**

```python
# Critical risk - Merge logic breaks
@dlt.resource(
    name="app_opportunities",
    write_disposition="merge",
    primary_key="submission_id"  # Hard-coded string
)
```

**Occurrences**: 4 DLT resources

**Pattern 4: JSONB Field Access**

```python
# High risk - Parsing fails if structure changes
competitors = evidence.get("competitors_found", [])
market_data = evidence["market_size"]["tam_value"]
```

**Occurrences**: 30+ JSONB field accesses

### Recommended Refactoring

**Create Constants File**: `config/schema_constants.py`

```python
class TableNames:
    APP_OPPORTUNITIES = "app_opportunities"
    WORKFLOW_RESULTS = "workflow_results"
    MARKET_VALIDATIONS = "market_validations"

class AppOpportunitiesColumns:
    SUBMISSION_ID = "submission_id"
    TRUST_SCORE = "trust_score"
    TRUST_BADGE = "trust_badge"
    CORE_FUNCTIONS = "core_functions"
    # ... etc

class WorkflowResultsColumns:
    OPPORTUNITY_ID = "opportunity_id"
    FUNCTION_LIST = "function_list"
    DIMENSION_SCORES = "dimension_scores"
    # ... etc
```

**Refactored Code**:

```python
# Before
opportunity["trust_badge"]

# After
from config.schema_constants import AppOpportunitiesColumns
opportunity.get(AppOpportunitiesColumns.TRUST_BADGE, "BASIC")
```

---

## JSONB Schema Dependencies

All JSONB columns are documented in `jsonb-schema-versions.md` (see companion file).

**Critical JSONB Columns**:

1. `app_opportunities.core_functions` - JSONB array of function names
2. `workflow_results.function_list` - JSONB array of function names
3. `workflow_results.dimension_scores` - JSONB object with scoring dimensions (DEPRECATED)
4. `market_validations.validation_result` - JSONB object with full evidence
5. `market_validations.market_competitors_found` - JSONB array of competitor names
6. `workflow_results.llm_pricing_info` - JSONB object with pricing model
7. `market_validations.extraction_stats` - JSONB object with extraction statistics

---

## Breaking Change Impact Matrix

| Change Type | Affected Pipelines | Risk Level | Mitigation |
|-------------|-------------------|-----------|------------|
| Rename `submission_id` | 1, 2, 5 | CRITICAL | Update all queries, DLT primary keys |
| Rename `opportunity_id` | 2, 4 | CRITICAL | Update all queries, DLT primary keys |
| Rename trust columns | 1, 2, 3 | HIGH | Update TrustLayerValidator, all consumers |
| Change `core_functions` type | 1, 2, 5 | CRITICAL | Standardize serialization across all files |
| Rename dimension score columns | 2 | CRITICAL | Update GENERATED column formula |
| Change JSONB structure | 2, 4 | HIGH | Version JSONB schemas, update parsers |
| Remove market validation columns | 4 | HIGH | Update market_validation_persistence.py |
| Rename `function_list` | 2, 6 | CRITICAL | Update constraint_validator.py |

---

## Safe Schema Consolidation Checklist

Before consolidating 20 migrations → single baseline:

- [ ] **Verify all 145+ hard-coded column references** documented
- [ ] **Test all 7 pipelines** with schema dump
- [ ] **Validate JSONB parsing** for all 7 JSONB columns
- [ ] **Check DLT merge logic** for `submission_id` and `opportunity_id`
- [ ] **Confirm trust validation** system still works
- [ ] **Test constraint validator** (1-3 function rule)
- [ ] **Validate GENERATED column** formula for `opportunity_assessment_score`
- [ ] **Check market validation** persistence
- [ ] **Review core_functions** serialization consistency
- [ ] **Test batch loading** with DLT merge disposition

---

## Next Steps

1. Create `jsonb-schema-versions.md` with detailed JSONB structures
2. Create `hardcoded-references-analysis.md` with code refactoring suggestions
3. Update this document when new pipelines are added
4. Create migration testing suite before schema consolidation

---

**Document Version**: 1.0
**Last Updated**: 2025-11-17
**Maintained By**: RedditHarbor Data Engineering Team
**Review Frequency**: Before any schema changes
