# Schema Consolidation Risk Assessment

**Date**: 2025-11-17
**Status**: 🔴 HIGH RISK - Review Required Before Consolidation
**Recommendation**: **YES, review existing pipelines and agentic integrations FIRST**

---

## Executive Summary

**Can Schema Consolidation Break the App?** **YES - Multiple Critical Integration Points**

- **88 Python files** reference core database tables
- **100+ files** use DLT pipelines and agentic tools
- **7 active production pipelines** depend on exact schema structure
- **3 observability integrations** (AgentOps, Jina MCP, Market Validation)

**Best Practice**: **ABSOLUTELY review pipelines before consolidation**

---

## Active Production Pipelines

### 1. **DLT Trust Pipeline** 🔥 CRITICAL
**File**: `scripts/dlt/dlt_trust_pipeline.py`

**Dependencies**:
- `core.dlt_collection.collect_problem_posts`
- `core.dlt_app_opportunities.load_app_opportunities`
- `core.trust_layer.TrustLayerValidator`
- `agent_tools.opportunity_analyzer_agent.OpportunityAnalyzerAgent`

**Schema Dependencies**:
```python
# Pipeline expects EXACT schema:
- public_staging.app_opportunities (DLT-managed)
- public_staging.app_opportunities__core_functions (DLT child table)
- public.opportunity_scores (manual migration)
- public.workflow_results (manual migration)
```

**Risk**: 🔴 **CRITICAL** - Changes to `app_opportunities` schema will break DLT pipeline
**Mitigation**: Test with `test_mode=True` before production deployment

---

### 2. **Batch Opportunity Scoring** 🔥 CRITICAL
**File**: `scripts/core/batch_opportunity_scoring.py`

**Dependencies**:
- `agent_tools.opportunity_analyzer_agent.OpportunityAnalyzerAgent`
- `agent_tools.market_data_validator.MarketDataValidator`
- `agent_tools.llm_profiler_enhanced.EnhancedLLMProfiler`
- `core.dlt.constraint_validator.app_opportunities_with_constraint`
- Supabase direct queries (bypasses DLT)

**Schema Dependencies**:
```python
# Hard-coded table references:
- public.submissions (Reddit data)
- public.opportunity_scores (scoring results)
- public.app_opportunities (AI profiles)
- public.market_validations (Jina search validation)
- public.competitive_landscape (competitor analysis)
```

**Risk**: 🔴 **HIGH** - Direct SQL queries will fail if column names change
**Mitigation**: Use SQLAlchemy models or keep column names stable

---

### 3. **Trust Layer Validator** 🟡 MODERATE
**File**: `core/trust_layer.py`

**Schema Dependencies**:
```python
# Expects these columns in submissions/opportunities:
- trust_score DOUBLE PRECISION
- trust_badge CHARACTER VARYING
- activity_score DOUBLE PRECISION
- trust_level CHARACTER VARYING
- ai_confidence_level CHARACTER VARYING
```

**Risk**: 🟡 **MODERATE** - Column renames will break trust validation
**Mitigation**: Use data classes/Pydantic models for column mapping

---

### 4. **Market Validation Integration** 🟡 MODERATE
**File**: `agent_tools/market_validation_integration.py`

**Dependencies**:
- Jina MCP Client (external API)
- `market_validations` table persistence
- `ValidationEvidence` data structure

**Schema Dependencies**:
```sql
-- market_validations table
validation_evidence JSONB
search_query TEXT
validation_score DOUBLE PRECISION
```

**Risk**: 🟡 **MODERATE** - JSONB structure changes could break evidence parsing
**Mitigation**: Version the JSONB schema with `_version` field

---

## Agentic Integration Points

### AgentOps Observability (100+ files) 🔥 CRITICAL

**Integration Depth**:
- **LiteLLM instrumentation**: All OpenRouter API calls traced
- **Multi-agent systems**: Agno framework integration
- **Cost tracking**: Every LLM call logged to `llm_usage_tracking` table
- **Trust validation**: Trust layer events tracked

**Schema Dependencies**:
```sql
-- llm_usage_tracking table (cost tracking)
CREATE TABLE llm_usage_tracking (
    id UUID PRIMARY KEY,
    agent_name TEXT,
    model TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_cost NUMERIC(10,4),
    session_id TEXT,  -- AgentOps session ID
    created_at TIMESTAMP
)
```

**Risk**: 🔴 **CRITICAL** - Cost tracking migration breaks observability
**Evidence**: Migration `20251114005544_fix_cost_tracking_functions.sql` already exists
**Mitigation**: Preserve `session_id` column for AgentOps correlation

---

## Schema Consolidation Impact Map

### Tables Referenced in 88+ Files

| Table | Files Referencing | Risk Level | Consolidation Impact |
|-------|------------------|-----------|---------------------|
| `app_opportunities` | 88 | 🔴 CRITICAL | DLT pipeline + 6-dimension scoring |
| `opportunity_scores` | 45 | 🔴 HIGH | Weighted scoring methodology |
| `submissions` | 52 | 🔴 HIGH | Reddit data collection |
| `workflow_results` | 23 | 🟡 MODERATE | AI profiling workflow |
| `market_validations` | 18 | 🟡 MODERATE | Jina search validation |
| `trust_validations` | 12 | 🟢 LOW | Trust layer (isolated) |
| `llm_usage_tracking` | 31 | 🔴 CRITICAL | AgentOps cost tracking |

---

## Migration Consolidation Risks

### Current Migration State (20 files, 3,156 lines)

**Phase-by-Phase Risk**:

1. **Phase 1 (Nov 4)**: Foundation tables ✅ LOW RISK
   - `opportunity_scores`, `market_validations`, `competitive_landscape`
   - Well-defined schema, minimal dependencies

2. **Phase 2 (Nov 8-9)**: Consolidation + DLT ⚠️ MODERATE RISK
   - Merged `app_opportunities` with DLT columns
   - Added `workflow_results` table
   - Risk: DLT expects specific column types

3. **Phase 3 (Nov 9-10)**: Trust Layer 🔴 HIGH RISK
   - Added `trust_score`, `trust_badge`, `activity_score`
   - Fragmented across 3 migrations
   - Risk: Column dependencies in trust validation pipeline

4. **Phase 4 (Nov 13-14)**: Cost Tracking 🔴 CRITICAL RISK
   - Added `llm_usage_tracking` table
   - Fixed cost tracking functions (migration 20251114005544)
   - Risk: AgentOps instrumentation depends on exact schema

---

## Recommended Review Strategy

### Step 1: Pipeline Inventory Audit (2 hours)
```bash
# Create comprehensive pipeline dependency map
grep -r "public\." scripts/ agent_tools/ core/ \
  --include="*.py" \
  | grep -E "(opportunity|submission|trust|validation|workflow)" \
  > docs/schema-consolidation/pipeline-dependencies.txt
```

### Step 2: Integration Testing (4 hours)

**Test Checklist**:
- [ ] DLT trust pipeline end-to-end test
- [ ] Batch opportunity scoring with 10 submissions
- [ ] Trust layer validation with test data
- [ ] Market validation Jina MCP integration
- [ ] AgentOps cost tracking verification
- [ ] Marimo dashboard connectivity (6 dashboards)

**Test Script**:
```bash
# Test all critical pipelines
python scripts/testing/test_complete_integration_pipeline.py
python scripts/dlt/dlt_trust_pipeline.py --test-mode --limit 5
python scripts/core/batch_opportunity_scoring.py --test --limit 10
```

### Step 3: Schema Change Impact Analysis (3 hours)

**For Each Table in Consolidation**:
1. List all Python files referencing table
2. Identify hard-coded column names
3. Find dynamic SQL queries (f-strings, concatenation)
4. Check for JSONB structure dependencies
5. Verify foreign key cascades

**Tools**:
```bash
# Find hard-coded table references
rg "app_opportunities|opportunity_scores|workflow_results" \
  --type py \
  --context 3 \
  > docs/schema-consolidation/hardcoded-references.txt
```

### Step 4: Observability Integration Review (2 hours)

**AgentOps Integration Points**:
- [ ] Verify `session_id` column preserved in cost tracking
- [ ] Test trace correlation after schema changes
- [ ] Validate LiteLLM logging integration
- [ ] Check multi-agent system instrumentation

**Jina MCP Integration**:
- [ ] Test market validation with MCP client
- [ ] Verify `validation_evidence` JSONB structure
- [ ] Check search query persistence

---

## Safe Consolidation Strategy

### Option 1: Incremental Migration (RECOMMENDED) 🟢

**Timeline**: 12-16 hours over 2 days

**Approach**:
1. **Day 1 Morning**: Create baseline migration (foundation tables only)
2. **Day 1 Afternoon**: Test all pipelines against baseline
3. **Day 2 Morning**: Migrate trust layer + cost tracking (high-risk tables)
4. **Day 2 Afternoon**: Test observability integrations

**Rollback**: Easy - revert single migration file

**Risk**: 🟢 LOW - Each phase independently tested

---

### Option 2: Full Consolidation (HIGH RISK) 🔴

**Timeline**: 8-10 hours in single sprint

**Approach**:
1. Consolidate all 20 migrations into single baseline
2. Test entire system at once
3. Fix breaking changes reactively

**Rollback**: Hard - requires database restore from dump

**Risk**: 🔴 HIGH - Multiple failure points, hard to debug

**NOT RECOMMENDED** without comprehensive integration tests

---

### Option 3: Hybrid Strategy (BALANCED) 🟡

**Timeline**: 10-14 hours over 2 days

**Approach**:
1. **Phase A**: Consolidate low-risk tables (foundation, analytics)
2. **Phase B**: Test DLT pipelines + agentic integrations
3. **Phase C**: Consolidate high-risk tables (trust, cost tracking)
4. **Phase D**: Full system integration test

**Rollback**: Moderate - revert by phase

**Risk**: 🟡 MODERATE - Balanced risk vs. efficiency

**RECOMMENDED** for production systems

---

## Pre-Consolidation Checklist

### Required Before ANY Consolidation

- [ ] **Backup current schema** (pg_dump with data)
- [ ] **Create test environment** (separate Supabase instance)
- [ ] **Run full integration test suite** (baseline performance)
- [ ] **Document all pipeline dependencies** (create dependency graph)
- [ ] **Review AgentOps instrumentation** (verify session tracking)
- [ ] **Test Jina MCP integration** (validate market validation)
- [ ] **Check DLT pipeline state** (verify staging schema)
- [ ] **Verify Marimo dashboards** (test all 6 dashboards)
- [ ] **Create rollback plan** (step-by-step recovery)
- [ ] **Schedule maintenance window** (notify stakeholders)

### Integration Test Coverage Required

**Minimum Passing Tests**:
- ✅ DLT trust pipeline (end-to-end): 8/8 posts processed
- ✅ Batch opportunity scoring: 10/10 submissions scored
- ✅ Trust layer validation: All badges generated correctly
- ✅ Market validation: Jina MCP client functional
- ✅ AgentOps tracking: Cost tracking logged correctly
- ✅ Marimo dashboards: All 6 dashboards render data

**Success Criteria**: 100% pass rate on critical pipelines

---

## Breaking Change Examples (REAL RISKS)

### Example 1: DLT Column Type Mismatch
```python
# Current schema (WORKING)
CREATE TABLE app_opportunities (
    core_functions JSONB  -- DLT infers from JSON string
)

# After consolidation (BROKEN)
CREATE TABLE app_opportunities (
    core_functions TEXT[]  -- PostgreSQL array, DLT fails
)

# Error: DLT cannot deserialize TEXT[] to JSON
```

### Example 2: Trust Layer Column Rename
```python
# Pipeline expects:
opportunity["trust_badge"]  # KeyError if renamed

# Consolidated migration renames:
trust_badge -> credibility_badge  # BREAKS trust_layer.py
```

### Example 3: AgentOps Session ID Missing
```sql
-- Current schema (WORKING)
CREATE TABLE llm_usage_tracking (
    session_id TEXT  -- AgentOps correlation
)

-- After consolidation (BROKEN)
-- session_id column removed, AgentOps trace correlation lost
```

---

## Mitigation Strategies

### Strategy 1: Schema Version Tracking
```sql
-- Add version tracking to all tables
ALTER TABLE app_opportunities
ADD COLUMN _schema_version INTEGER DEFAULT 1;

-- Update version on breaking changes
-- Allows backward compatibility checks in code
```

### Strategy 2: Database Migration Testing Framework
```python
# Create migration test harness
def test_migration_preserves_pipelines():
    # 1. Backup current schema
    # 2. Run consolidated migration
    # 3. Test all pipelines
    # 4. Rollback if failures
    # 5. Report breaking changes
```

### Strategy 3: Gradual Column Deprecation
```sql
-- Don't drop columns immediately
-- Deprecate first, drop in next sprint
ALTER TABLE opportunity_scores
ADD COLUMN total_score_v2 DOUBLE PRECISION;

-- Keep total_score for 1 sprint (backward compatibility)
-- Drop after all code migrated
```

---

## Recommended Action Plan

### Immediate Next Steps (This Sprint)

1. ✅ **Review Documentation** (docs/schema-consolidation/)
2. 🔄 **Pipeline Dependency Audit** (2 hours)
3. 🔄 **Integration Test Baseline** (4 hours)
4. 🔄 **Create Test Environment** (1 hour)

### Next Sprint (Schema Consolidation)

1. 🔄 **Implement Hybrid Strategy** (10-14 hours)
2. 🔄 **Test All Pipelines** (6 hours)
3. 🔄 **Deploy to Production** (2 hours)
4. 🔄 **Monitor for 48 Hours** (continuous)

### Future Improvements

1. 🔄 **Automated Migration Testing** (CI/CD integration)
2. 🔄 **Schema Version Tracking** (database metadata)
3. 🔄 **API Layer Abstraction** (decouple code from schema)
4. 🔄 **Observability Dashboard** (AgentOps + Supabase metrics)

---

## Conclusion

**Is it a good practice to review pipelines?** **ABSOLUTELY YES - MANDATORY**

**Risk Level**: 🔴 **HIGH** without review, 🟡 **MODERATE** with review

**Recommendation**:
- **DO NOT** consolidate migrations without pipeline review
- **DO** create comprehensive integration tests first
- **DO** use hybrid consolidation strategy
- **DO** maintain backward compatibility during transition

**Estimated Time for Safe Consolidation**: 16-20 hours (with review)

---

**Last Updated**: 2025-11-17
**Next Review**: After pipeline dependency audit
