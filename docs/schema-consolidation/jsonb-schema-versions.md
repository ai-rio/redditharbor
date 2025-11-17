# JSONB Schema Versions

**Purpose**: Document all JSONB column structures with versioning to prevent breaking changes during schema consolidation.

**Generated**: 2025-11-17
**Critical**: JSONB changes break parsing logic in Python code
**Scope**: 7 JSONB columns across 3 tables

---

## Executive Summary

RedditHarbor uses **7 JSONB columns** for semi-structured data:

| Table | Column | Version | Breaking Risk | Parsing Locations |
|-------|--------|---------|---------------|-------------------|
| `app_opportunities` | `core_functions` | N/A (inconsistent) | CRITICAL | 3 serialization formats |
| `workflow_results` | `function_list` | 1 | CRITICAL | 1 parser + validator |
| `workflow_results` | `llm_pricing_info` | 1 | MODERATE | 1 parser |
| `app_opportunities` | `market_competitors_found` | 1 | HIGH | 2 parsers |
| `market_validations` | `validation_result` | 1 | CRITICAL | 1 serializer |
| `market_validations` | `market_competitors_found` | 1 | HIGH | 1 serializer |
| `market_validations` | `extraction_stats` | 1 | MODERATE | 1 serializer |

**Critical Findings**:
- **`core_functions` has NO version control** and **3 different serialization formats**
- **`validation_result` stores complex nested objects** requiring careful versioning
- **All parsers use `.get()` with defaults** (good defensive coding)
- **No schema evolution strategy** currently implemented

---

## 1. app_opportunities.core_functions

**Table**: `app_opportunities`
**Column**: `core_functions` (JSONB)
**Current Version**: **NONE** (inconsistent!)
**Critical Issue**: Three different serialization formats across codebase

### Format Inconsistency Problem

| File | Serialization Method | Format | Example |
|------|---------------------|--------|---------|
| `dlt_trust_pipeline.py` | Python list → DLT auto-converts | `["Function 1", "Function 2"]` | JSONB array |
| `dlt_app_opportunities.py` | Python list → `json.dumps()` | `'["Function 1", "Function 2"]'` | JSON string |
| `batch_opportunity_scoring.py` | Python list → `", ".join()` | `"Function 1, Function 2"` | Comma-separated |

**Code References**:

#### Format 1: Python List (DLT auto-converts to JSONB)

**File**: `scripts/dlt/dlt_trust_pipeline.py`
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

**Output**: JSONB array `["Function 1", "Function 2", "Function 3"]`

#### Format 2: JSON String (explicit serialization)

**File**: `core/dlt_app_opportunities.py`
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

**Output**: VARCHAR `"[\"Function 1\", \"Function 2\"]"` (JSON as string)

#### Format 3: Comma-Separated String

**File**: `scripts/core/batch_opportunity_scoring.py`
**Lines**: 625

```python
ai_profile = {
    # ...
    "core_functions": ", ".join(opp.get("function_list", [])) if isinstance(opp.get("function_list"), list) else str(opp.get("function_list", "")),
    # ...
}
```

**Output**: VARCHAR `"Function 1, Function 2, Function 3"`

### Recommended Schema Version 1

**Format**: JSONB array of strings
**Validation**: 1-3 elements required
**Element Type**: Non-empty string

```json
{
    "_version": 1,
    "functions": [
        "Primary function description",
        "Secondary function description",
        "Tertiary function description (optional)"
    ]
}
```

**Constraints**:
- Array length: 1-3 (enforced by constraint_validator.py)
- Element type: String
- Element length: 1-200 characters
- No duplicate functions

### Migration Strategy

**Phase 1: Standardize Current Data**
```sql
-- Find format types
SELECT
    submission_id,
    core_functions,
    CASE
        WHEN core_functions::text LIKE '[%]' THEN 'JSONB array'
        WHEN core_functions::text LIKE '%,%' THEN 'CSV string'
        ELSE 'Unknown'
    END as format_type
FROM app_opportunities
WHERE core_functions IS NOT NULL;

-- Standardize to JSONB array
UPDATE app_opportunities
SET core_functions =
    CASE
        WHEN core_functions::text LIKE '%,%'
        THEN to_jsonb(string_to_array(core_functions::text, ', '))
        ELSE core_functions
    END
WHERE core_functions IS NOT NULL;
```

**Phase 2: Update Code**
1. Refactor all 3 files to use single serialization method
2. Add version field to JSONB: `{"_version": 1, "functions": [...]}`
3. Create utility functions: `serialize_core_functions()`, `parse_core_functions()`

**Breaking Changes Risk**: 🔴 **CRITICAL**
- Current state: Data inconsistency across pipelines
- Any schema change: Must handle 3 existing formats
- Recommended: Immediate standardization before consolidation

---

## 2. workflow_results.function_list

**Table**: `workflow_results`
**Column**: `function_list` (JSONB)
**Current Version**: 1 (implicit)
**Used By**: `batch_opportunity_scoring.py`, `constraint_validator.py`

### Schema Version 1 (Current)

**Format**: Simple JSONB array of strings

```json
[
    "Core function 1",
    "Core function 2",
    "Core function 3"
]
```

**Constraints**:
- Array length: 1-3 (business rule)
- Element type: String
- No nesting allowed

### Code References

#### Write Location

**File**: `scripts/core/batch_opportunity_scoring.py`
**Lines**: 389-399, 409

```python
# Extract core functions from analysis (now always available)
core_functions = analysis.get("core_functions", [])

if isinstance(core_functions, list) and len(core_functions) > 0:
    function_count = len(core_functions)
    function_list = core_functions
else:
    # Fallback for unexpected format
    function_count = core_functions if isinstance(core_functions, int) else 1
    function_list = [f"Core function {i+1}" for i in range(function_count)]

# Prepare data for workflow_results table
analysis_data = {
    # ...
    "function_list": function_list,  # JSONB array
    "function_count": function_count,
    # ...
}
```

#### Read Location (Validation)

**File**: `core/dlt/constraint_validator.py`
**Lines**: 39-54

```python
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

### Validation Rules

**Pre-flight Check** (batch_opportunity_scoring.py lines 487-512):

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
if mismatches:
    print(f"⚠️  WARNING: {len(mismatches)} opportunities have count/list mismatch")
```

### Required Fields
- Array must contain 1-3 strings
- Each string must be non-empty
- `function_count` column must match array length

### Optional Fields
- None (simple array structure)

### Breaking Changes Risk

🔴 **CRITICAL** - Renaming this column breaks:
- Line 502: Pre-flight validation checks
- Line 40 (constraint_validator.py): Function count extraction
- Constraint validation logic for 1-3 function rule

### Migration Strategy

If schema changes needed:
1. Add `_version` field to support future evolution:
   ```json
   {
       "_version": 1,
       "functions": ["Func 1", "Func 2"]
   }
   ```
2. Update constraint_validator.py to check version
3. Backfill existing records with `_version: 1`
4. Deprecate version 1 after 2 sprints

---

## 3. workflow_results.llm_pricing_info

**Table**: `workflow_results`
**Column**: `llm_pricing_info` (JSONB)
**Current Version**: 1
**Used By**: `batch_opportunity_scoring.py`

### Schema Version 1 (Current)

**Format**: Simple pricing model object

```json
{
    "prompt": 0.15,      // USD per 1M tokens
    "completion": 0.60   // USD per 1M tokens
}
```

**Constraints**:
- Both keys required if present
- Values must be positive numbers
- Precision: 2 decimal places sufficient

### Code References

**File**: `scripts/core/batch_opportunity_scoring.py`
**Lines**: 444

```python
# Cost tracking data (from EnhancedLLMProfiler)
"llm_model_used": cost_data.get("model_used"),
"llm_provider": cost_data.get("provider", "openrouter"),
# ... other cost fields ...
"llm_pricing_info": cost_data.get("model_pricing_per_m_tokens", {}),  # JSONB
"cost_tracking_enabled": bool(cost_data),
```

**Data Source**: `agent_tools/llm_profiler_enhanced.py` (cost tracking module)

### Required Fields
- `prompt` (number) - Prompt token cost per 1M tokens
- `completion` (number) - Completion token cost per 1M tokens

### Optional Fields
- None currently, but could add:
  - `currency` (string) - Default "USD"
  - `model` (string) - Model identifier
  - `provider` (string) - Provider name

### Breaking Changes Risk

🟡 **MODERATE** - This column is used for cost analysis:
- Renaming keys breaks cost calculation formulas
- Removing column loses pricing history for budget tracking
- Not mission-critical (pipelines still run)

### Migration Strategy

If schema changes needed:
1. Add version and expand structure:
   ```json
   {
       "_version": 1,
       "pricing": {
           "prompt": 0.15,
           "completion": 0.60,
           "currency": "USD"
       },
       "effective_date": "2025-11-17"
   }
   ```
2. Keep backward compatibility for old records

---

## 4. app_opportunities.market_competitors_found

**Table**: `app_opportunities`
**Column**: `market_competitors_found` (JSONB)
**Current Version**: 1
**Used By**: `market_validation_persistence.py`, `batch_opportunity_scoring.py`

### Schema Version 1 (Current)

**Format**: Array of competitor names (simplified)

```json
[
    "Competitor Company A",
    "Competitor Company B",
    "Competitor Company C"
]
```

**Source**: Extracted from `ValidationEvidence.competitor_pricing` list

### Code References

#### Write Location

**File**: `agent_tools/market_validation_persistence.py`
**Lines**: 108, 136, 172

```python
# Extract data from evidence
competitors_found = self._serialize_competitors(evidence.competitor_pricing)

# Step 1: Update app_opportunities table
app_opportunities_data = {
    # ...
    "market_competitors_found": competitors_found,  # JSONB array
    # ...
}

# Step 2: Insert detailed record in market_validations table
market_validation_data = {
    # ...
    "market_competitors_found": competitors_found,  # JSONB array (duplicated)
    # ...
}
```

#### Serialization Method

**File**: `agent_tools/market_validation_persistence.py`
**Method**: `_serialize_competitors()` (not shown in snippet, but referenced)

**Expected Input**: List of `CompetitorPricing` objects
**Output**: List of company name strings

### Required Fields
- Array of strings (competitor names)
- Can be empty array `[]`

### Optional Fields
- Future expansion could add:
  - Pricing details
  - Feature comparison
  - Market share estimates

### Breaking Changes Risk

🟡 **HIGH** - Used in two locations:
- Quick access queries on `app_opportunities`
- Detailed storage in `market_validations`
- Renaming breaks both persistence and retrieval

### Migration Strategy

For richer competitor data:
```json
{
    "_version": 2,
    "competitors": [
        {
            "name": "Competitor A",
            "pricing_model": "Subscription",
            "monthly_price": 29.99,
            "features": ["Feature 1", "Feature 2"]
        }
    ]
}
```

---

## 5. market_validations.validation_result

**Table**: `market_validations`
**Column**: `validation_result` (JSONB)
**Current Version**: 1
**Used By**: `market_validation_persistence.py`

### Schema Version 1 (Current)

**Format**: Complex nested validation evidence

```json
{
    "_version": 1,
    "validation_score": 85.5,
    "data_quality_score": 72.3,
    "reasoning": "Strong market validation based on 5 competitors found and clear market size data.",
    "competitor_pricing": [
        {
            "company_name": "CompetitorA",
            "pricing_model": "Subscription",
            "monthly_price": "$29/mo",
            "annual_price": "$290/yr",
            "features": [
                "Feature 1",
                "Feature 2",
                "Feature 3"
            ],
            "target_market": "B2B",
            "source_url": "https://example.com/pricing"
        },
        {
            "company_name": "CompetitorB",
            "pricing_model": "Freemium",
            "free_tier": "Up to 100 users",
            "paid_tier": "$49/mo",
            "features": ["Feature A", "Feature B"],
            "target_market": "B2C"
        }
    ],
    "market_size": {
        "tam_value": "$2.5B",
        "sam_value": "$500M",
        "som_value": "$50M",
        "growth_rate": "15% CAGR",
        "year": 2025,
        "currency": "USD",
        "source": "Industry report"
    },
    "similar_launches": [
        {
            "product_name": "Similar Product 1",
            "launch_platform": "Product Hunt",
            "launch_date": "2023-06-15",
            "success_metrics": "500+ upvotes, 2000+ users",
            "outcome": "Acquired by BigCorp for $5M",
            "url": "https://producthunt.com/..."
        },
        {
            "product_name": "Similar Product 2",
            "launch_platform": "HackerNews",
            "launch_date": "2024-01-20",
            "success_metrics": "Front page, 300+ comments",
            "outcome": "Active with 10K+ users"
        }
    ],
    "data_sources": [
        "jina_reader",
        "external_api",
        "manual_research"
    ],
    "timestamp": "2025-11-17T12:34:56.789Z",
    "confidence_indicators": {
        "competitor_data_quality": 0.85,
        "market_size_confidence": 0.72,
        "launch_data_reliability": 0.68
    }
}
```

### Code References

**File**: `agent_tools/market_validation_persistence.py`
**Lines**: 163

```python
# Step 2: Insert detailed record in market_validations table
market_validation_data = {
    # ...
    "validation_result": json.dumps(self._serialize_validation_result(evidence), indent=2),
    # ...
}
```

**Serialization Method**: `_serialize_validation_result(evidence)`
- Input: `ValidationEvidence` object from MarketDataValidator
- Output: Dictionary with full evidence structure
- Method: Not fully shown in snippets, but creates nested structure above

### Required Fields
- `validation_score` (number 0-100) - Overall validation score
- `data_quality_score` (number 0-100) - Data reliability score
- `reasoning` (string) - Human-readable explanation

### Optional Fields
- `competitor_pricing` (array) - May be empty if no competitors found
- `market_size` (object) - May be null if data unavailable
- `similar_launches` (array) - May be empty
- `data_sources` (array) - Source attribution
- `timestamp` (string ISO 8601) - Validation time
- `confidence_indicators` (object) - Quality metrics

### Nested Structure Rules

**competitor_pricing[*]**:
- `company_name` (string) - Required
- `pricing_model` (string) - Required
- `monthly_price`, `annual_price` (string) - Optional
- `features` (array of strings) - Optional
- `target_market` (string) - Optional

**market_size**:
- `tam_value`, `sam_value`, `som_value` (string with currency) - Optional
- `growth_rate` (string) - Optional
- `year` (integer) - Optional
- `currency` (string) - Default "USD"

**similar_launches[*]**:
- `product_name` (string) - Required
- `launch_platform` (string) - Required
- `launch_date` (string ISO date) - Required
- `success_metrics` (string) - Optional
- `outcome` (string) - Optional

### Breaking Changes Risk

🔴 **CRITICAL** - This is the master evidence record:
- Contains full market validation data for audit trail
- Renaming top-level keys breaks evidence retrieval
- Changing nested structure breaks analysis dashboards
- Must maintain backward compatibility for historical data

### Backward Compatibility Strategy

**Reading Version 1**:
```python
def parse_validation_result(validation_json):
    """Parse validation result with version handling."""
    version = validation_json.get("_version", 1)

    if version == 1:
        return {
            "validation_score": validation_json.get("validation_score", 0),
            "competitors": validation_json.get("competitor_pricing", []),
            "market_size": validation_json.get("market_size"),
            # ... etc
        }
    elif version == 2:
        # Handle future version 2 structure
        pass
```

**Writing with Version**:
```python
evidence_dict = {
    "_version": 1,
    "validation_score": evidence.validation_score,
    "data_quality_score": evidence.data_quality_score,
    # ... rest of structure
}
```

---

## 6. market_validations.market_competitors_found

**Table**: `market_validations`
**Column**: `market_competitors_found` (JSONB)
**Current Version**: 1
**Used By**: `market_validation_persistence.py`

### Schema Version 1 (Current)

**Format**: Array of competitor names (same as app_opportunities version)

```json
[
    "Competitor Company A",
    "Competitor Company B",
    "Competitor Company C"
]
```

**Note**: This is a **denormalized copy** of the same data in `app_opportunities.market_competitors_found` for quick access without joining tables.

### Code References

**File**: `agent_tools/market_validation_persistence.py`
**Lines**: 172

```python
market_validation_data = {
    # ...
    "market_competitors_found": competitors_found,  # JSONB array (duplicated from app_opportunities)
    # ...
}
```

### Design Pattern

**Dual-Tier Storage**:
1. `app_opportunities.market_competitors_found` - Quick access for common queries
2. `market_validations.validation_result.competitor_pricing` - Full detailed data
3. `market_validations.market_competitors_found` - Denormalized copy for filtering

**Why Denormalize?**:
- Fast filtering: `WHERE market_competitors_found @> '["CompetitorA"]'::jsonb`
- Avoids JOIN + JSONB extraction on large validation_result column

### Breaking Changes Risk

🟡 **HIGH** - Denormalized data requires:
- Keeping both copies in sync
- Update logic in both locations
- Risk of data inconsistency if not handled properly

### Recommendations
1. Use database trigger to auto-sync both columns
2. Or remove denormalization and query validation_result directly
3. Document denormalization strategy clearly

---

## 7. market_validations.extraction_stats

**Table**: `market_validations`
**Column**: `extraction_stats` (JSONB)
**Current Version**: 1
**Used By**: `market_validation_persistence.py`

### Schema Version 1 (Current)

**Format**: Jina Reader API extraction statistics

```json
{
    "_version": 1,
    "total_urls_fetched": 8,
    "successful_extractions": 7,
    "failed_extractions": 1,
    "total_content_bytes": 245600,
    "average_extraction_time_ms": 1250,
    "jina_api_calls": 8,
    "cache_hits": 2,
    "cache_misses": 6,
    "error_types": {
        "timeout": 1,
        "rate_limit": 0,
        "parse_error": 0
    },
    "extraction_timestamp": "2025-11-17T12:34:56.789Z"
}
```

### Code References

**File**: `agent_tools/market_validation_persistence.py`
**Lines**: 116, 180

```python
# Extract data from evidence
extraction_stats = self._prepare_extraction_stats(evidence)

# Store in market_validations
market_validation_data = {
    # ...
    "extraction_stats": extraction_stats,  # JSONB
    # ...
}
```

**Preparation Method**: `_prepare_extraction_stats(evidence)`
- Aggregates statistics from Jina Reader API calls
- Calculates success rates, cache efficiency
- Tracks errors by type

### Required Fields
- `total_urls_fetched` (integer) - URLs attempted
- `successful_extractions` (integer) - Successful parses
- `failed_extractions` (integer) - Failed parses

### Optional Fields
- `total_content_bytes` (integer) - Data volume
- `average_extraction_time_ms` (integer) - Performance metric
- `jina_api_calls` (integer) - API usage tracking
- `cache_hits`, `cache_misses` (integer) - Cache efficiency
- `error_types` (object) - Error categorization

### Breaking Changes Risk

🟢 **MODERATE** - Statistics for monitoring:
- Used for cost and performance analysis
- Not critical for pipeline operation
- Can be regenerated if needed

### Future Enhancements

**Version 2** could add:
```json
{
    "_version": 2,
    "extraction_summary": {
        "total_urls": 8,
        "success_rate": 0.875,
        "average_time_ms": 1250
    },
    "by_source": {
        "product_hunt": {"urls": 3, "success": 3},
        "github": {"urls": 5, "success": 4}
    },
    "cost_breakdown": {
        "jina_api_cost": 0.024,
        "bandwidth_cost": 0.001
    }
}
```

---

## Schema Evolution Strategy

### Versioning Best Practices

1. **Always Include `_version` Field**:
   ```json
   {
       "_version": 1,
       "data": { ... }
   }
   ```

2. **Version Parser Function**:
   ```python
   def parse_jsonb_column(json_data, column_name):
       """Parse JSONB with version handling."""
       version = json_data.get("_version", 1)

       if version == 1:
           return parse_v1(json_data, column_name)
       elif version == 2:
           return parse_v2(json_data, column_name)
       else:
           raise ValueError(f"Unknown version {version} for {column_name}")
   ```

3. **Backward Compatibility Window**:
   - Support N-1 versions (current + previous)
   - Deprecation notice for 2 sprints
   - Migration script before dropping old version

4. **Version Migration SQL**:
   ```sql
   -- Backfill _version for existing records
   UPDATE market_validations
   SET validation_result = jsonb_set(
       validation_result,
       '{_version}',
       '1'::jsonb
   )
   WHERE validation_result->>'_version' IS NULL;
   ```

### Breaking Change Checklist

Before modifying any JSONB schema:

- [ ] **Check all parsing locations** (see "Used By" in each section)
- [ ] **Update version number** in JSONB structure
- [ ] **Write migration script** to backfill existing data
- [ ] **Update parsing functions** to handle both versions
- [ ] **Add tests** for old and new version parsing
- [ ] **Document deprecation timeline** for old version
- [ ] **Update this document** with new schema version

---

## Immediate Action Items

### 1. CRITICAL: Standardize core_functions Format

**Problem**: Three different formats across codebase
**Impact**: Data inconsistency, query failures
**Solution**:

```python
# Create utility module: config/jsonb_utils.py

def serialize_core_functions(functions: list[str]) -> dict:
    """
    Standardize core_functions serialization.

    Args:
        functions: List of 1-3 function strings

    Returns:
        Versioned JSONB structure
    """
    if not isinstance(functions, list) or len(functions) < 1 or len(functions) > 3:
        raise ValueError("functions must be list of 1-3 strings")

    return {
        "_version": 1,
        "functions": [str(f).strip() for f in functions if f]
    }

def parse_core_functions(jsonb_data: dict | str) -> list[str]:
    """
    Parse core_functions from any format.

    Args:
        jsonb_data: JSONB dict, JSON string, or CSV string

    Returns:
        List of function strings
    """
    # Handle CSV format (legacy)
    if isinstance(jsonb_data, str) and "," in jsonb_data:
        return [f.strip() for f in jsonb_data.split(",") if f.strip()]

    # Handle JSON string format (legacy)
    if isinstance(jsonb_data, str):
        try:
            jsonb_data = json.loads(jsonb_data)
        except:
            return [jsonb_data]  # Single function as string

    # Handle versioned format (current)
    if isinstance(jsonb_data, dict):
        version = jsonb_data.get("_version", 0)
        if version == 1:
            return jsonb_data.get("functions", [])
        elif version == 0:
            # Legacy format without version
            if "functions" in jsonb_data:
                return jsonb_data["functions"]
            else:
                # Assume it's a direct list
                return list(jsonb_data.values())

    # Handle direct list (legacy)
    if isinstance(jsonb_data, list):
        return jsonb_data

    raise ValueError(f"Cannot parse core_functions: {jsonb_data}")
```

**Migration Steps**:
1. Add `jsonb_utils.py` module
2. Update all 3 files to use utility functions
3. Run data migration to standardize existing data
4. Add tests for backward compatibility

### 2. Add Version Fields to All JSONB Columns

**Files to Update**:
- `market_validation_persistence.py` - Add `_version: 1` to all JSONB writes
- `batch_opportunity_scoring.py` - Add `_version: 1` to function_list, llm_pricing_info
- `dlt_trust_pipeline.py` - Add `_version: 1` to core_functions (after standardization)

### 3. Create JSONB Parsing Test Suite

```python
# tests/test_jsonb_schemas.py

import pytest
from config.jsonb_utils import parse_core_functions, serialize_core_functions

def test_core_functions_csv_format():
    """Test parsing legacy CSV format."""
    result = parse_core_functions("Function 1, Function 2")
    assert result == ["Function 1", "Function 2"]

def test_core_functions_json_string_format():
    """Test parsing legacy JSON string format."""
    result = parse_core_functions('["Function 1", "Function 2"]')
    assert result == ["Function 1", "Function 2"]

def test_core_functions_versioned_format():
    """Test parsing versioned format."""
    data = {"_version": 1, "functions": ["Function 1", "Function 2"]}
    result = parse_core_functions(data)
    assert result == ["Function 1", "Function 2"]

def test_core_functions_serialization():
    """Test standardized serialization."""
    result = serialize_core_functions(["Function 1", "Function 2"])
    assert result == {"_version": 1, "functions": ["Function 1", "Function 2"]}

def test_core_functions_constraint_validation():
    """Test 1-3 function constraint."""
    with pytest.raises(ValueError):
        serialize_core_functions([])  # Too few
    with pytest.raises(ValueError):
        serialize_core_functions(["A", "B", "C", "D"])  # Too many
```

---

## Schema Consolidation Impact

### Pre-Consolidation Validation

Before consolidating 20 migrations → single baseline:

1. **Audit All JSONB Data**:
   ```sql
   -- Check core_functions format distribution
   SELECT
       CASE
           WHEN core_functions::text LIKE '[%' THEN 'JSONB array'
           WHEN core_functions::text LIKE '%,%' THEN 'CSV string'
           WHEN core_functions::text LIKE '"%"' THEN 'JSON string'
           ELSE 'Other'
       END as format_type,
       COUNT(*) as count
   FROM app_opportunities
   WHERE core_functions IS NOT NULL
   GROUP BY format_type;
   ```

2. **Validate All Parsers**:
   - Run test suite against real data samples
   - Check for parsing errors in logs
   - Verify version field presence

3. **Create Backup**:
   ```sql
   -- Backup all JSONB columns before migration
   CREATE TABLE jsonb_backup_20251117 AS
   SELECT
       id,
       'app_opportunities' as table_name,
       'core_functions' as column_name,
       core_functions as jsonb_value
   FROM app_opportunities
   WHERE core_functions IS NOT NULL
   UNION ALL
   SELECT
       id,
       'workflow_results' as table_name,
       'function_list' as column_name,
       function_list as jsonb_value
   FROM workflow_results
   WHERE function_list IS NOT NULL;
   -- Add other JSONB columns...
   ```

### Post-Consolidation Validation

After baseline migration:

1. **Verify Data Integrity**:
   ```sql
   -- Check no data loss
   SELECT
       table_name,
       column_name,
       COUNT(*) as records_with_data
   FROM jsonb_backup_20251117
   GROUP BY table_name, column_name;

   -- Compare with current state
   SELECT
       'app_opportunities' as table_name,
       'core_functions' as column_name,
       COUNT(*) as current_count
   FROM app_opportunities
   WHERE core_functions IS NOT NULL;
   ```

2. **Test All Pipelines**:
   - Run DLT trust pipeline end-to-end
   - Execute batch opportunity scoring
   - Verify market validation persistence
   - Check constraint validation

3. **Monitor Error Logs**:
   - Watch for JSONB parsing errors
   - Check for serialization failures
   - Verify DLT merge operations

---

## Related Documentation

- [Pipeline Schema Dependencies](./pipeline-schema-dependencies.md) - Table and column usage
- [Hard-Coded References Analysis](./hardcoded-references-analysis.md) - Code refactoring guide
- [ERD](./erd.md) - Complete schema visualization
- [Migration Analysis](./migration-analysis.md) - Historical schema evolution

---

**Document Version**: 1.0
**Last Updated**: 2025-11-17
**Maintained By**: RedditHarbor Data Engineering Team
**Review Frequency**: Before any JSONB schema changes
