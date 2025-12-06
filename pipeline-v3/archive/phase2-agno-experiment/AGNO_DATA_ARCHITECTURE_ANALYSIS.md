# Agno Integration: Data Architecture Analysis & Bottleneck Prevention

## Executive Summary

This document analyzes the current Pipeline v3 database architecture and identifies potential bottlenecks, schema conflicts, and regressions that could occur with Agno + Jina integration.

**Status**: Critical Analysis
**Priority**: High - Must resolve before implementation
**Date**: 2025-12-03
**Database Instance**: Port 54322 (PostgreSQL 15.8) - See DATABASE_INSTANCE_RESOLUTION.md

> **⚠️ IMPORTANT**: This analysis is based on **Port 54322** (PostgreSQL 15.8), which contains 11 live app ideas and the correct Pipeline v3 schema. Do NOT confuse with port 54331 (empty Docker container).

---

## 1. Current Database State Analysis

### 1.1 Schema Alignment: Pipeline v3 ✅ Production DB (Port 54322)

#### ✅ **RESOLVED**: Schema Fully Aligned

**Pipeline v3 SQLAlchemy Model** (`models/database.py`):
```python
class Opportunity(Base):
    __tablename__ = "opportunities"

    # 31 columns including:
    - submission_id (String(10), unique index)
    - reddit_* fields (title, url, author, upvotes, comments, created_at)
    - app_* fields (title, concept, problem_statement, target_audience)
    - core_functions (JSON)
    - market metrics (5 fields: demand, pain, monetization, competition, feasibility)
    - scoring fields (final_score, confidence_score, trust_level)
    - AI quality fields (content_quality_score, is_spam, spam_indicators)
    - embedding (JSON - not actual vector type)
    - metadata (analyzed_at, created_at, updated_at)
    - duplicate tracking (is_duplicate, duplicate_of_id)
```

**Production Database Schema** (Port 54322 - actual table):
```sql
Table "public.opportunities"
         Column         |            Type
------------------------+-----------------------------
 id                     | uuid                        ✅
 submission_id          | character varying(10)       ✅ CORRECT TYPE
 reddit_title           | character varying(300)      ✅ PRESENT
 reddit_url             | character varying(500)      ✅ PRESENT
 subreddit              | character varying(100)      ✅ PRESENT
 reddit_author          | character varying(100)      ✅ PRESENT
 reddit_upvotes         | integer                     ✅ PRESENT
 reddit_comments_count  | integer                     ✅ PRESENT
 reddit_created_at      | timestamp                   ✅ PRESENT
 app_title              | character varying(200)      ✅ PRESENT
 app_concept            | text                        ✅ PRESENT
 problem_statement      | text                        ✅ PRESENT
 target_audience        | text                        ✅ PRESENT
 core_functions         | jsonb                       ✅ PRESENT
 market_demand          | double precision            ✅ PRESENT
 pain_intensity         | double precision            ✅ PRESENT
 monetization_potential | double precision            ✅ PRESENT
 competition_level      | double precision            ✅ PRESENT
 technical_feasibility  | double precision            ✅ PRESENT
 final_score            | double precision            ✅ PRESENT
 confidence_score       | double precision            ✅ PRESENT
 trust_level            | character varying(10)       ✅ PRESENT
 content_quality_score  | double precision            ✅ PRESENT
 is_spam                | boolean                     ✅ PRESENT
 spam_indicators        | jsonb                       ✅ PRESENT
 embedding              | jsonb                       ✅ PRESENT
 analyzed_at            | timestamp                   ✅ PRESENT
 created_at             | timestamp                   ✅ PRESENT
 updated_at             | timestamp                   ✅ PRESENT
 is_duplicate           | boolean                     ✅ PRESENT
 duplicate_of_id        | uuid                        ✅ PRESENT

Total: 31 columns - COMPLETE Pipeline v3 schema alignment
```

**Impact**: ✅ **NO BLOCKING ISSUES** - Port 54322 already has complete Pipeline v3 schema

> **Note**: Port 54331 (Docker container) has incomplete schema, but we're using port 54322 which is production-ready.

---

### 1.2 Indexing Analysis

#### Current Indexes on `opportunities`

```sql
idx_opportunities_pkey              -- PRIMARY KEY (id)
idx_opportunities_submission_id     -- submission_id
idx_opportunities_created_at        -- created_at
idx_opportunities_is_spam           -- is_spam
idx_opportunities_quality_score     -- content_quality_score
idx_opportunities_quality_spam      -- (content_quality_score, is_spam)
```

#### Missing Indexes for Agno + Jina Integration

**High-Priority Missing Indexes:**
1. `final_score` - Core filtering (ORDER BY final_score DESC)
2. `trust_level` - Common WHERE clause
3. `subreddit` - Group by subreddit queries
4. `app_title` - Search by app name
5. `analyzed_at` - Time-series analysis

**Agno-Specific Indexes Needed:**
```sql
CREATE INDEX idx_opportunities_final_score ON opportunities(final_score DESC);
CREATE INDEX idx_opportunities_trust_level ON opportunities(trust_level);
CREATE INDEX idx_opportunities_subreddit ON opportunities(subreddit);
CREATE INDEX idx_opportunities_analyzed_at ON opportunities(analyzed_at DESC);

-- Composite indexes for common queries
CREATE INDEX idx_opportunities_score_trust ON opportunities(final_score DESC, trust_level);
CREATE INDEX idx_opportunities_subreddit_created ON opportunities(subreddit, created_at DESC);
```

**Jina Market Validation Indexes Needed:**
```sql
-- For filtering by validation scores
CREATE INDEX idx_opportunities_jina_validation ON opportunities(jina_validation_score DESC);
CREATE INDEX idx_opportunities_jina_quality ON opportunities(jina_data_quality_score DESC);

-- For finding validated opportunities
CREATE INDEX idx_opportunities_validated ON opportunities(jina_validation_score)
    WHERE jina_validation_score IS NOT NULL;
```

---

### 1.3 Data Type Conflicts

#### **CRITICAL CONFLICT**: `submission_id` Type Mismatch

**Pipeline v3 Model**:
```python
submission_id = Column(String(10), nullable=False, index=True, unique=True)
```

**Production DB**:
```sql
submission_id | uuid
```

**Problem**: Reddit submission IDs are strings like "abc123xyz" (6-10 chars), not UUIDs.

**Solution**: Change production column to `VARCHAR(10)` OR use mapping table.

---

### 1.4 `market_validations` Table Analysis

#### Current Schema

```sql
Table "public.market_validations"
      Column      |           Type
------------------+--------------------------
 id               | uuid
 opportunity_id   | uuid                     -- FK to opportunities
 validation_type  | varchar(50)              -- 'agno_market_analysis', 'jina_validation'
 evidence         | jsonb                    -- All validation data stored here
 confidence_level | numeric(3,2)             -- 0.00 to 1.00
 created_at       | timestamptz
 updated_at       | timestamptz

Indexes:
 market_validations_pkey  -- PRIMARY KEY (id)

Foreign Keys:
 market_validations_opportunity_id_fkey  -- REFERENCES opportunities(id) ON DELETE CASCADE
```

#### Issues for Agno + Jina Integration

**1. Missing Indexes** - Performance bottleneck for queries:
```sql
-- Missing critical indexes:
CREATE INDEX idx_market_validations_opportunity_id ON market_validations(opportunity_id);
CREATE INDEX idx_market_validations_type ON market_validations(validation_type);
CREATE INDEX idx_market_validations_created ON market_validations(created_at DESC);
CREATE INDEX idx_market_validations_confidence ON market_validations(confidence_level DESC);

-- Composite index for common queries:
CREATE INDEX idx_market_validations_lookup
    ON market_validations(opportunity_id, validation_type, created_at DESC);
```

**2. JSONB Storage Overhead** - Everything in `evidence` column:
- Jina API costs stored in JSONB
- Competitor pricing arrays in JSONB
- Market size data in JSONB
- Search queries in JSONB

**Performance Impact**:
- Cannot index inside JSONB efficiently
- Cannot filter by Jina-specific fields without `jsonb_extract_path`
- Slower queries for business intelligence reports

**Recommendation**: Add dedicated columns for frequently queried fields:
```sql
ALTER TABLE market_validations
ADD COLUMN validation_score FLOAT,
ADD COLUMN data_quality_score FLOAT,
ADD COLUMN market_size_tam VARCHAR(50),
ADD COLUMN market_size_growth VARCHAR(20),
ADD COLUMN competitor_count INT,
ADD COLUMN jina_api_cost_usd NUMERIC(10,6),
ADD COLUMN search_queries_count INT;
```

---

## 2. Identified Bottlenecks

### 2.1 Write Performance Bottlenecks

#### **Bottleneck 1: Dual-Table Writes**

Every Agno analysis requires **2 separate INSERTs**:

```mermaid
sequenceDiagram
    participant A as AgnoAnalyzer
    participant DB as Database

    A->>DB: BEGIN TRANSACTION
    A->>DB: INSERT INTO opportunities (...)
    Note over DB: Write 25+ columns
    A->>DB: INSERT INTO market_validations (...)
    Note over DB: Write JSONB evidence
    A->>DB: COMMIT TRANSACTION

    Note over A,DB: If EITHER fails, BOTH rollback
```

**Impact**:
- 2x write latency per opportunity
- Transaction lock duration increased
- Higher rollback risk

**Mitigation**:
```python
# Use savepoints for partial failure recovery
with session.begin():
    try:
        opp = session.add(opportunity)
        session.flush()  # Get opportunity.id

        savepoint = session.begin_nested()
        try:
            validation = MarketValidation(opportunity_id=opp.id, ...)
            session.add(validation)
            savepoint.commit()
        except:
            savepoint.rollback()
            # Log warning but continue - validation is optional

    except:
        # Critical failure - rollback everything
        raise
```

---

#### **Bottleneck 2: JSONB Write Overhead**

**Problem**: Large JSONB columns slow down writes

```python
evidence = {
    "competitor_pricing": [
        {
            "company": "...",
            "pricing_tiers": [...],  # Array of dicts
            "features": [...]         # Another array
        }
        # 5-10 competitors = 5-10 nested objects
    ],
    "market_size": {...},
    "similar_launches": [...],  # Another array
    "search_queries_used": [...],
    "urls_fetched": [...],
    "extraction_stats": {...}
}
```

**Size Estimate**: 10-50 KB per evidence object

**Impact on 100 opportunities/batch**:
- 1-5 MB JSONB data per batch
- PostgreSQL TOAST storage overhead
- Slower VACUUM operations

**Mitigation**:
1. **Compress large JSONB** before storage:
```python
import gzip
import json

def compress_evidence(evidence: dict) -> bytes:
    json_str = json.dumps(evidence)
    return gzip.compress(json_str.encode())
```

2. **Store large arrays separately**:
```sql
CREATE TABLE market_validation_competitors (
    id UUID PRIMARY KEY,
    validation_id UUID REFERENCES market_validations(id),
    company_name VARCHAR(200),
    pricing_model VARCHAR(50),
    pricing_tiers JSONB,
    source_url TEXT
);
```

---

#### **Bottleneck 3: Missing Batch Insert Optimization**

**Current Approach** (one-by-one):
```python
for submission in submissions:
    result = analyzer.analyze_submission(submission)
    db.insert(result)  # Individual INSERT
```

**Problem**: N separate transactions for N opportunities

**Optimized Approach** (bulk insert):
```python
results = analyzer.analyze_batch(submissions)
db.bulk_insert(results)  # Single transaction with bulk INSERT
```

**Performance Gain**: ~10x faster for large batches

---

### 2.2 Read Performance Bottlenecks

#### **Bottleneck 4: JSONB Query Performance**

**Slow Query Example**:
```sql
-- Find opportunities with high Jina validation scores
SELECT o.*, mv.evidence->>'validation_score' as jina_score
FROM opportunities o
JOIN market_validations mv ON mv.opportunity_id = o.id
WHERE mv.validation_type = 'jina_validation'
  AND CAST(mv.evidence->>'validation_score' AS FLOAT) > 70.0
ORDER BY CAST(mv.evidence->>'validation_score' AS FLOAT) DESC
LIMIT 100;
```

**Problems**:
1. JSONB extraction (`->>`) is slow
2. `CAST` prevents index usage
3. No index on `validation_score` inside JSONB

**Solution**: Extract to dedicated column:
```sql
ALTER TABLE market_validations
ADD COLUMN validation_score FLOAT
GENERATED ALWAYS AS (CAST(evidence->>'validation_score' AS FLOAT)) STORED;

CREATE INDEX idx_market_validations_score ON market_validations(validation_score DESC);
```

Now query becomes:
```sql
SELECT o.*, mv.validation_score as jina_score
FROM opportunities o
JOIN market_validations mv ON mv.opportunity_id = o.id
WHERE mv.validation_type = 'jina_validation'
  AND mv.validation_score > 70.0
ORDER BY mv.validation_score DESC
LIMIT 100;
```

**Performance Gain**: ~50x faster (indexed column scan vs JSONB extraction)

---

#### **Bottleneck 5: Multi-Agent Score Aggregation**

**Problem**: Querying Agno individual agent scores requires complex JSONB queries

```sql
-- Get opportunities with high WTP scores from Agno
SELECT o.*,
    mv.evidence->'agno_analysis'->'wtp_agent'->>'score' as wtp_score
FROM opportunities o
JOIN market_validations mv ON mv.opportunity_id = o.id
WHERE mv.validation_type = 'agno_market_analysis'
  AND CAST(mv.evidence->'agno_analysis'->'wtp_agent'->>'score' AS FLOAT) > 80
```

**Solution**: Add Agno-specific columns to `opportunities` table:
```sql
ALTER TABLE opportunities
ADD COLUMN agno_wtp_score FLOAT,
ADD COLUMN agno_segment_confidence FLOAT,
ADD COLUMN agno_price_potential FLOAT,
ADD COLUMN agno_behavior_score FLOAT,
ADD COLUMN agno_consensus_confidence FLOAT;

-- Indexes for filtering
CREATE INDEX idx_opportunities_agno_wtp ON opportunities(agno_wtp_score DESC);
CREATE INDEX idx_opportunities_agno_consensus ON opportunities(agno_consensus_confidence DESC);
```

---

### 2.3 Concurrency Bottlenecks

#### **Bottleneck 6: Table-Level Locking**

**Problem**: High-concurrency writes may cause lock contention

**Scenario**:
```
Process 1: INSERT INTO opportunities (...)  -- Acquires row lock
Process 2: INSERT INTO opportunities (...)  -- Acquires different row lock
Process 3: INSERT INTO opportunities (...)  -- Acquires different row lock

No conflict! ✅
```

But with foreign keys:
```
Process 1: INSERT INTO market_validations (opportunity_id = X)
Process 2: INSERT INTO market_validations (opportunity_id = X)  -- BLOCKS!
```

**Solution**: Use advisory locks for high-concurrency scenarios:
```python
from sqlalchemy import select, func

def insert_with_advisory_lock(session, opportunity_id, validation_data):
    # Use opportunity_id hash as lock key
    lock_key = hash(str(opportunity_id)) % 2147483647

    # Acquire advisory lock
    session.execute(select([func.pg_advisory_lock(lock_key)]))

    try:
        # Perform insert
        validation = MarketValidation(
            opportunity_id=opportunity_id,
            **validation_data
        )
        session.add(validation)
        session.commit()
    finally:
        # Release advisory lock
        session.execute(select([func.pg_advisory_unlock(lock_key)]))
```

---

## 3. Schema Enhancements for Agno Integration

### 3.1 Required Migrations (Port 54322)

> **✅ Migration 1 NOT NEEDED**: Port 54322 already has complete Pipeline v3 schema (31 columns)

#### Migration 1: Add Agno Multi-Agent Columns (REQUIRED)

```sql
ALTER TABLE opportunities
ADD COLUMN agno_wtp_score FLOAT,
ADD COLUMN agno_segment_type VARCHAR(10),  -- 'B2B' or 'B2C'
ADD COLUMN agno_segment_confidence FLOAT,
ADD COLUMN agno_price_potential FLOAT,
ADD COLUMN agno_behavior_score FLOAT,
ADD COLUMN agno_consensus_confidence FLOAT,
ADD COLUMN agno_analysis_cost_usd NUMERIC(10,6);
```

#### Migration 2: Add Jina Market Research Columns (REQUIRED)

```sql
ALTER TABLE opportunities
ADD COLUMN jina_validation_score FLOAT,
ADD COLUMN jina_data_quality_score FLOAT,
ADD COLUMN jina_competitor_count INT,
ADD COLUMN jina_market_size_tam VARCHAR(50),
ADD COLUMN jina_market_size_sam VARCHAR(50),
ADD COLUMN jina_market_size_growth VARCHAR(20),
ADD COLUMN jina_evidence_urls JSONB,
ADD COLUMN jina_api_cost_usd NUMERIC(10,6),
ADD COLUMN jina_cache_hit_rate FLOAT;
```

#### Migration 3: Enhance market_validations Table (OPTIONAL)

```sql
ALTER TABLE market_validations
-- Extract frequently queried fields from JSONB
ADD COLUMN validation_score FLOAT,
ADD COLUMN data_quality_score FLOAT,
ADD COLUMN validation_source VARCHAR(100),  -- 'agno_agents', 'jina_api', etc.
ADD COLUMN reasoning TEXT,

-- Jina-specific fields
ADD COLUMN market_size_tam VARCHAR(50),
ADD COLUMN market_size_sam VARCHAR(50),
ADD COLUMN market_size_growth VARCHAR(20),
ADD COLUMN market_source VARCHAR(200),
ADD COLUMN competitor_count INT,
ADD COLUMN launches_analyzed INT,

-- Cost tracking
ADD COLUMN jina_api_calls_count INT,
ADD COLUMN jina_cache_hit_rate FLOAT,
ADD COLUMN total_cost_usd NUMERIC(10,6),

-- Metadata
ADD COLUMN search_queries_used JSONB,
ADD COLUMN urls_fetched JSONB,
ADD COLUMN extraction_stats JSONB;
```

---

### 3.2 Index Creation for Performance

```sql
-- Opportunities table indexes
CREATE INDEX idx_opportunities_final_score ON opportunities(final_score DESC);
CREATE INDEX idx_opportunities_trust_level ON opportunities(trust_level);
CREATE INDEX idx_opportunities_subreddit ON opportunities(subreddit);
CREATE INDEX idx_opportunities_analyzed_at ON opportunities(analyzed_at DESC);
CREATE INDEX idx_opportunities_reddit_created ON opportunities(reddit_created_at DESC);

-- Agno-specific indexes
CREATE INDEX idx_opportunities_agno_wtp ON opportunities(agno_wtp_score DESC)
    WHERE agno_wtp_score IS NOT NULL;
CREATE INDEX idx_opportunities_agno_segment ON opportunities(agno_segment_type)
    WHERE agno_segment_type IS NOT NULL;

-- Jina-specific indexes
CREATE INDEX idx_opportunities_jina_validation ON opportunities(jina_validation_score DESC)
    WHERE jina_validation_score IS NOT NULL;
CREATE INDEX idx_opportunities_jina_quality ON opportunities(jina_data_quality_score DESC)
    WHERE jina_data_quality_score IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX idx_opportunities_score_trust
    ON opportunities(final_score DESC, trust_level);
CREATE INDEX idx_opportunities_subreddit_score
    ON opportunities(subreddit, final_score DESC);
CREATE INDEX idx_opportunities_validated
    ON opportunities(final_score DESC, jina_validation_score DESC)
    WHERE jina_validation_score IS NOT NULL;

-- market_validations indexes
CREATE INDEX idx_market_validations_opportunity_id
    ON market_validations(opportunity_id);
CREATE INDEX idx_market_validations_type
    ON market_validations(validation_type);
CREATE INDEX idx_market_validations_created
    ON market_validations(created_at DESC);
CREATE INDEX idx_market_validations_score
    ON market_validations(validation_score DESC)
    WHERE validation_score IS NOT NULL;

-- Composite index for lookups
CREATE INDEX idx_market_validations_lookup
    ON market_validations(opportunity_id, validation_type, created_at DESC);

-- GIN index for JSONB search
CREATE INDEX idx_market_validations_evidence
    ON market_validations USING gin(evidence);
```

---

## 4. Transaction Safety Analysis

### 4.1 Current Transaction Patterns

**Pipeline v3 Load Pattern** (`load/database_loader.py`):
```python
def store_analysis(self, result: AnalysisResult):
    with self.session.begin():
        opportunity = result.to_db_model()
        self.session.add(opportunity)
        # Implicit commit on context exit
```

**Issue**: No explicit error handling for constraint violations

---

### 4.2 Agno + Jina Transaction Pattern

**Recommended Approach**:
```python
async def store_agno_analysis(
    self,
    result: AnalysisResult,
    validation_evidence: ValidationEvidence
) -> Tuple[bool, str]:
    """Store Agno analysis with market validation evidence"""

    try:
        async with self.session.begin():
            # Step 1: Insert opportunity
            opportunity = result.to_db_model()

            # Add Agno scores
            opportunity.agno_wtp_score = agno_synthesis.wtp_score
            opportunity.agno_segment_type = agno_synthesis.segment_type
            # ... other Agno fields

            # Add Jina validation scores
            opportunity.jina_validation_score = validation_evidence.validation_score
            opportunity.jina_competitor_count = len(validation_evidence.competitor_pricing)
            # ... other Jina fields

            self.session.add(opportunity)
            await self.session.flush()  # Get opportunity.id

            # Step 2: Create savepoint for optional validation insert
            savepoint = await self.session.begin_nested()

            try:
                # Insert market validation evidence
                market_validation = MarketValidation(
                    opportunity_id=opportunity.id,
                    validation_type='agno_jina_combined',
                    validation_source='agno_team+jina_api',
                    validation_score=validation_evidence.validation_score,
                    evidence=validation_evidence.to_dict(),
                    # ... other fields
                )
                self.session.add(market_validation)
                await savepoint.commit()

            except Exception as validation_error:
                # Market validation failed - rollback savepoint but continue
                await savepoint.rollback()
                logger.warning(
                    f"Market validation insert failed for opportunity {opportunity.id}: "
                    f"{validation_error}. Opportunity data saved successfully."
                )

            # Main transaction commits both or only opportunity
            return True, f"Stored opportunity {opportunity.id}"

    except sqlalchemy.exc.IntegrityError as e:
        # Constraint violation (duplicate submission_id, etc.)
        return False, f"Integrity error: {e}"

    except Exception as e:
        # Unexpected error
        logger.error(f"Failed to store analysis: {e}", exc_info=True)
        return False, f"Storage error: {e}"
```

---

### 4.3 Deadlock Prevention

**Scenario**: Multiple processes writing to same opportunity

```mermaid
sequenceDiagram
    participant P1 as Process 1
    participant P2 as Process 2
    participant DB as Database

    P1->>DB: INSERT opportunity (id=X)
    P2->>DB: INSERT opportunity (id=X)

    Note over DB: IntegrityError!<br/>submission_id unique constraint

    DB-->>P2: ERROR: duplicate key
```

**Prevention Strategy**:
1. **Idempotent writes** - Check before insert:
```python
existing = session.query(Opportunity).filter_by(
    submission_id=submission_id
).first()

if existing:
    logger.info(f"Opportunity {submission_id} already exists, skipping")
    return existing.id
```

2. **Upsert pattern** - Use PostgreSQL ON CONFLICT:
```python
from sqlalchemy.dialects.postgresql import insert

stmt = insert(Opportunity).values(
    submission_id=submission_id,
    # ... other fields
).on_conflict_do_update(
    index_elements=['submission_id'],
    set_={
        'final_score': stmt.excluded.final_score,
        'updated_at': datetime.utcnow()
    }
)
```

---

## 5. Recommendations & Migration Strategy

### 5.1 Immediate Actions (Pre-Implementation)

**Priority 1: Verify Port Configuration** 🔴 CRITICAL
- [x] ✅ Confirmed port 54322 is correct instance (11 app ideas, complete schema)
- [ ] Update `config/settings.py` default port from 54331 → 54322
- [ ] Create `.env` file with `DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres`
- [ ] Test connection to port 54322

**Priority 2: Add Agno/Jina Columns** 🟡 HIGH
- [ ] Run Migration 1: Add Agno multi-agent columns to port 54322
- [ ] Run Migration 2: Add Jina market research columns to port 54322
- [ ] (Optional) Run Migration 3: Enhance market_validations table

**Priority 3: Performance Indexes** 🟡 HIGH
- [ ] Add `final_score`, `trust_level`, `subreddit` indexes
- [ ] Add composite indexes for common query patterns
- [ ] Add partial indexes for nullable Agno/Jina columns

**Priority 3: Transaction Safety** 🟡 HIGH
- [ ] Implement savepoint pattern for market validations
- [ ] Add idempotent write checks
- [ ] Test rollback scenarios

---

### 5.2 Phased Migration Strategy

> **Note**: Timeline significantly reduced since port 54322 already has Pipeline v3 schema

#### **Phase 1: Configuration & Setup (Day 1 - 20 minutes)**
1. ✅ Verified port 54322 has correct schema and 11 app ideas
2. Update `config/settings.py` default port to 54322
3. Create `.env` file with correct DATABASE_URL
4. Test database connection
5. Verify all 11 app ideas accessible

#### **Phase 2: Agno Integration (Day 1-2)**
1. Add Agno multi-agent columns (Migration 1) - 10 minutes
2. Add Agno-specific indexes - 5 minutes
3. Update database loader with Agno fields - 30 minutes
4. Test Agno write performance on port 54322 (target: <100ms per opportunity)
5. Verify Agno data persistence with 11 existing app ideas

#### **Phase 3: Jina Integration (Day 2-3)**
1. Add Jina market research columns (Migration 2) - 10 minutes
2. Add Jina-specific indexes - 5 minutes
3. Enhance market_validations table (Migration 3 - Optional) - 15 minutes
4. Implement Jina data persistence - 30 minutes
5. Test combined Agno+Jina write performance (target: <200ms per opportunity)

#### **Phase 4: Validation & Optimization (Day 3-4)**
1. Run Agno+Jina on all 11 existing app ideas
2. Benchmark query performance with EXPLAIN ANALYZE
3. Tune index usage based on actual query patterns
4. Implement savepoint pattern for optional market validations
5. Add connection pooling if needed

**Total Timeline**: 3-4 days (vs. 3 weeks if we had to migrate data)

---

### 5.3 Performance Targets

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| **Single opportunity write** | N/A | <100ms | Indexed columns, savepoints |
| **Batch write (100 opps)** | N/A | <5s | Bulk insert, reduced locks |
| **Query by score** | N/A | <50ms | Indexed final_score |
| **Query by validation** | N/A | <100ms | Indexed jina_validation_score |
| **JSONB extraction** | N/A | <200ms | Extracted columns + indexes |
| **Market validation lookup** | N/A | <50ms | Composite index (opp_id, type) |

---

### 5.4 Monitoring & Alerts

**Key Metrics to Track**:
1. Write latency (p50, p95, p99)
2. Index hit rate (`pg_stat_user_indexes`)
3. Table bloat percentage
4. Lock wait times
5. JSONB storage size
6. Transaction rollback rate

**Alert Thresholds**:
- Write latency p95 > 500ms
- Index hit rate < 95%
- Table bloat > 20%
- Lock wait time > 1s
- Rollback rate > 5%

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| **Schema mismatch on deploy** | High | Critical | Pre-deployment schema validation |
| **Slow JSONB queries** | Medium | High | Extract to columns, add indexes |
| **Write contention** | Low | Medium | Advisory locks, connection pooling |
| **Index bloat** | Medium | Medium | Regular VACUUM, index monitoring |
| **Transaction deadlocks** | Low | High | Idempotent writes, retry logic |
| **Data corruption** | Very Low | Critical | Comprehensive testing, backups |

---

## 7. Rollback Plan

If Agno + Jina integration causes performance degradation:

1. **Immediate**: Disable Agno analyzer in factory (fallback to LiteLLM)
2. **Short-term**: Remove Agno/Jina columns from queries
3. **Long-term**: Drop Agno/Jina columns if unused

**Rollback SQL**:
```sql
-- Drop Agno columns
ALTER TABLE opportunities
DROP COLUMN IF EXISTS agno_wtp_score,
DROP COLUMN IF EXISTS agno_segment_type,
-- ... other Agno columns

-- Drop Jina columns
ALTER TABLE opportunities
DROP COLUMN IF EXISTS jina_validation_score,
-- ... other Jina columns
```

---

## Appendix: Database Statistics

### Current Table Sizes
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('opportunities', 'market_validations')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Index Usage Statistics
```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('opportunities', 'market_validations')
ORDER BY idx_scan DESC;
```

---

**Document Version**: 1.0
**Created**: 2025-12-03
**Author**: RedditHarbor Engineering Team
**Status**: Critical Analysis - Ready for Review
