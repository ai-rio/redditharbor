# Phase 4: Database Schema Extensions

**Status**: Implementation Ready
**Phase**: 4 of 5
**Dependencies**: Phase 1-3 (Core Agno, Factory, Jina Integration)
**Estimated Duration**: 4 days

---

## Overview

Phase 4 extends the database schema to persist Agno multi-agent analysis results and Jina market research validation data, enabling comprehensive business intelligence storage and querying.

---

## Database Schema Extensions

### Schema Overview

The integration adds two main areas of extension:

1. **Agno Multi-Agent Columns**: Store individual agent scores and consensus metrics
2. **Jina Market Research Columns**: Store real market validation data and evidence

### Architecture Diagram

```mermaid
erDiagram
    opportunities ||--o{ market_validations : "validates"

    opportunities {
        uuid id PK
        uuid submission_id FK
        varchar app_title
        text app_concept
        jsonb core_functions
        float final_score
        float confidence_score
        varchar trust_level
        vector embedding

        comment "Agno Multi-Agent Scores"
        float agno_wtp_score
        float agno_segment_confidence
        float agno_price_potential
        float agno_behavior_score

        comment "Jina Market Research"
        float jina_validation_score
        float jina_data_quality_score
        int jina_competitor_count
        varchar jina_market_size_tam
        varchar jina_market_size_growth
        jsonb jina_evidence_urls
        numeric jina_api_cost_usd
        float jina_cache_hit_rate

        timestamp created_at
    }

    market_validations {
        uuid id PK
        uuid opportunity_id FK
        varchar validation_type
        varchar validation_source
        float validation_score
        float data_quality_score
        text reasoning

        comment "Competitor Analysis"
        jsonb competitor_pricing
        int competitors_found

        comment "Market Size Data"
        varchar market_size_tam
        varchar market_size_sam
        varchar market_size_growth
        varchar market_source

        comment "Product Launches"
        jsonb similar_launches
        int launches_analyzed

        comment "Evidence Metadata"
        jsonb search_queries_used
        jsonb urls_fetched
        jsonb extraction_stats
        int jina_api_calls_count
        float jina_cache_hit_rate
        numeric total_cost_usd

        timestamp created_at
        timestamp updated_at
    }
```

---

## SQL Migrations

### Migration File Structure

```
pipeline-v3/migrations/
├── 001_add_agno_columns.sql
├── 002_add_jina_columns.sql
└── 003_create_market_validations_indexes.sql
```

### Migration 001: Agno Multi-Agent Columns

**File**: `/pipeline-v3/migrations/001_add_agno_columns.sql`

```sql
-- ================================================================
-- Migration 001: Add Agno Multi-Agent Analysis Columns
-- ================================================================
-- Description: Extends opportunities table with Agno agent scores
-- Dependencies: Existing opportunities table
-- Created: 2025-12-03
-- ================================================================

BEGIN;

-- Add Agno agent-specific score columns
ALTER TABLE opportunities
ADD COLUMN agno_wtp_score FLOAT
    COMMENT 'Willingness to Pay Agent score (0-100)';

ALTER TABLE opportunities
ADD COLUMN agno_segment_confidence FLOAT
    COMMENT 'Market Segment Agent confidence (0-100)';

ALTER TABLE opportunities
ADD COLUMN agno_price_potential FLOAT
    COMMENT 'Price Point Agent revenue potential (0-100)';

ALTER TABLE opportunities
ADD COLUMN agno_behavior_score FLOAT
    COMMENT 'Payment Behavior Agent score (0-100)';

ALTER TABLE opportunities
ADD COLUMN agno_consensus_confidence FLOAT
    COMMENT 'Multi-agent consensus confidence (0-100)';

-- Add indexes for query performance
CREATE INDEX idx_opportunities_agno_wtp
ON opportunities(agno_wtp_score DESC)
WHERE agno_wtp_score IS NOT NULL;

CREATE INDEX idx_opportunities_agno_consensus
ON opportunities(agno_consensus_confidence DESC)
WHERE agno_consensus_confidence IS NOT NULL;

-- Add composite index for multi-agent filtering
CREATE INDEX idx_opportunities_agno_composite
ON opportunities(agno_wtp_score, agno_segment_confidence, agno_price_potential)
WHERE agno_wtp_score IS NOT NULL;

COMMIT;
```

### Migration 002: Jina Market Research Columns

**File**: `/pipeline-v3/migrations/002_add_jina_columns.sql`

```sql
-- ================================================================
-- Migration 002: Add Jina Market Research Columns
-- ================================================================
-- Description: Extends opportunities table with Jina validation data
-- Dependencies: Migration 001 (Agno columns)
-- Created: 2025-12-03
-- ================================================================

BEGIN;

-- Add Jina market validation columns
ALTER TABLE opportunities
ADD COLUMN jina_validation_score FLOAT
    COMMENT 'Jina-based market validation score (0-100)';

ALTER TABLE opportunities
ADD COLUMN jina_data_quality_score FLOAT
    COMMENT 'Data quality score from Jina sources (0-100)';

ALTER TABLE opportunities
ADD COLUMN jina_competitor_count INT DEFAULT 0
    COMMENT 'Number of competitors found via Jina';

ALTER TABLE opportunities
ADD COLUMN jina_market_size_tam VARCHAR(50)
    COMMENT 'Total Addressable Market from Jina research';

ALTER TABLE opportunities
ADD COLUMN jina_market_size_growth VARCHAR(20)
    COMMENT 'Market growth rate (CAGR) from Jina research';

ALTER TABLE opportunities
ADD COLUMN jina_evidence_urls JSONB
    COMMENT 'Array of URLs used for market validation';

ALTER TABLE opportunities
ADD COLUMN jina_api_cost_usd NUMERIC(10,6)
    COMMENT 'Total Jina API cost for this opportunity';

ALTER TABLE opportunities
ADD COLUMN jina_cache_hit_rate FLOAT
    COMMENT 'Cache hit rate for Jina requests (0-1)';

-- Add indexes for Jina-based queries
CREATE INDEX idx_opportunities_jina_validation
ON opportunities(jina_validation_score DESC)
WHERE jina_validation_score IS NOT NULL;

CREATE INDEX idx_opportunities_jina_quality
ON opportunities(jina_data_quality_score DESC)
WHERE jina_data_quality_score IS NOT NULL;

-- Add GIN index for JSONB evidence URLs
CREATE INDEX idx_opportunities_jina_evidence
ON opportunities USING GIN (jina_evidence_urls);

COMMIT;
```

### Migration 003: Market Validations Indexes

**File**: `/pipeline-v3/migrations/003_create_market_validations_indexes.sql`

```sql
-- ================================================================
-- Migration 003: Add Market Validations Performance Indexes
-- ================================================================
-- Description: Optimize queries on market_validations table
-- Dependencies: Existing market_validations table
-- Created: 2025-12-03
-- ================================================================

BEGIN;

-- Note: market_validations table already exists in legacy schema
-- See: docs/integrations/jina/market-validation-persistency-analysis.md

-- Add performance indexes for common queries
CREATE INDEX IF NOT EXISTS idx_market_validations_opportunity
ON market_validations(opportunity_id);

CREATE INDEX IF NOT EXISTS idx_market_validations_score
ON market_validations(validation_score DESC)
WHERE validation_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_market_validations_type_source
ON market_validations(validation_type, validation_source);

-- Add GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_market_validations_competitor_pricing
ON market_validations USING GIN (competitor_pricing);

CREATE INDEX IF NOT EXISTS idx_market_validations_similar_launches
ON market_validations USING GIN (similar_launches);

CREATE INDEX IF NOT EXISTS idx_market_validations_urls_fetched
ON market_validations USING GIN (urls_fetched);

-- Add index for cost analysis queries
CREATE INDEX IF NOT EXISTS idx_market_validations_cost
ON market_validations(total_cost_usd)
WHERE total_cost_usd IS NOT NULL;

COMMIT;
```

---

## SQLAlchemy Model Updates

### File Location

**File**: `/pipeline-v3/models/opportunity.py`

### Updated Opportunity Model

```python
from sqlalchemy import Column, Integer, String, Float, Text, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, VECTOR
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models.base import Base


class Opportunity(Base):
    """
    SQLAlchemy model for opportunities table with Agno + Jina extensions
    """
    __tablename__ = 'opportunities'

    # Primary Keys and Foreign Keys
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey('reddit_submissions.id'))

    # Core Opportunity Data
    app_title = Column(String(255), nullable=False)
    app_concept = Column(Text, nullable=False)
    problem_statement = Column(Text)
    target_audience = Column(String(255))
    core_functions = Column(JSONB)  # Max 3 functions

    # Scores and Metrics
    final_score = Column(Float)
    confidence_score = Column(Float)
    trust_level = Column(String(20))  # high/medium/low

    # Market Metrics
    market_demand = Column(Float)
    pain_intensity = Column(Float)
    monetization_potential = Column(Float)

    # Embeddings
    embedding = Column(VECTOR(1536))  # OpenAI ada-002 dimensions

    # ================================================================
    # AGNO MULTI-AGENT EXTENSIONS
    # ================================================================

    agno_wtp_score = Column(
        Float,
        comment='Willingness to Pay Agent score (0-100)'
    )
    agno_segment_confidence = Column(
        Float,
        comment='Market Segment Agent confidence (0-100)'
    )
    agno_price_potential = Column(
        Float,
        comment='Price Point Agent revenue potential (0-100)'
    )
    agno_behavior_score = Column(
        Float,
        comment='Payment Behavior Agent score (0-100)'
    )
    agno_consensus_confidence = Column(
        Float,
        comment='Multi-agent consensus confidence (0-100)'
    )

    # ================================================================
    # JINA MARKET RESEARCH EXTENSIONS
    # ================================================================

    jina_validation_score = Column(
        Float,
        comment='Jina-based market validation score (0-100)'
    )
    jina_data_quality_score = Column(
        Float,
        comment='Data quality score from Jina sources (0-100)'
    )
    jina_competitor_count = Column(
        Integer,
        default=0,
        comment='Number of competitors found via Jina'
    )
    jina_market_size_tam = Column(
        String(50),
        comment='Total Addressable Market from Jina research'
    )
    jina_market_size_growth = Column(
        String(20),
        comment='Market growth rate (CAGR) from Jina research'
    )
    jina_evidence_urls = Column(
        JSONB,
        comment='Array of URLs used for market validation'
    )
    jina_api_cost_usd = Column(
        Float,
        comment='Total Jina API cost for this opportunity'
    )
    jina_cache_hit_rate = Column(
        Float,
        comment='Cache hit rate for Jina requests (0-1)'
    )

    # Metadata
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submission = relationship("RedditSubmission", back_populates="opportunities")
    market_validations = relationship(
        "MarketValidation",
        back_populates="opportunity",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Opportunity(id={self.id}, title='{self.app_title}', score={self.final_score})>"

    @property
    def has_agno_analysis(self) -> bool:
        """Check if opportunity has Agno multi-agent analysis"""
        return self.agno_wtp_score is not None

    @property
    def has_jina_validation(self) -> bool:
        """Check if opportunity has Jina market validation"""
        return self.jina_validation_score is not None

    @property
    def agno_agent_scores(self) -> dict:
        """Get all Agno agent scores as dictionary"""
        return {
            'wtp': self.agno_wtp_score,
            'segment': self.agno_segment_confidence,
            'price': self.agno_price_potential,
            'behavior': self.agno_behavior_score,
            'consensus': self.agno_consensus_confidence
        }

    @property
    def jina_validation_data(self) -> dict:
        """Get all Jina validation data as dictionary"""
        return {
            'validation_score': self.jina_validation_score,
            'data_quality_score': self.jina_data_quality_score,
            'competitor_count': self.jina_competitor_count,
            'market_size_tam': self.jina_market_size_tam,
            'market_size_growth': self.jina_market_size_growth,
            'evidence_urls': self.jina_evidence_urls,
            'api_cost_usd': self.jina_api_cost_usd,
            'cache_hit_rate': self.jina_cache_hit_rate
        }
```

### MarketValidation Model

**File**: `/pipeline-v3/models/market_validation.py`

```python
from sqlalchemy import Column, Integer, String, Float, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models.base import Base


class MarketValidation(Base):
    """
    SQLAlchemy model for market_validations table

    Stores detailed market research evidence from Jina API
    """
    __tablename__ = 'market_validations'

    # Primary Keys and Foreign Keys
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(
        UUID(as_uuid=True),
        ForeignKey('opportunities.id'),
        nullable=False
    )

    # Validation Metadata
    validation_type = Column(String(50))  # 'competitor', 'market_size', 'product_launch'
    validation_source = Column(String(100))  # 'jina', 'manual', etc.
    validation_score = Column(Float)
    data_quality_score = Column(Float)
    reasoning = Column(Text)

    # Competitor Analysis
    competitor_pricing = Column(JSONB)  # Array of CompetitorPricing objects
    competitors_found = Column(Integer, default=0)

    # Market Size Data
    market_size_tam = Column(String(50))
    market_size_sam = Column(String(50))
    market_size_growth = Column(String(20))
    market_source = Column(String(255))

    # Product Launches
    similar_launches = Column(JSONB)  # Array of ProductLaunchData objects
    launches_analyzed = Column(Integer, default=0)

    # Evidence Metadata
    search_queries_used = Column(JSONB)  # Array of search queries
    urls_fetched = Column(JSONB)  # Array of fetched URLs
    extraction_stats = Column(JSONB)  # Stats about data extraction
    jina_api_calls_count = Column(Integer, default=0)
    jina_cache_hit_rate = Column(Float)
    total_cost_usd = Column(Float)

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    opportunity = relationship("Opportunity", back_populates="market_validations")

    def __repr__(self):
        return f"<MarketValidation(id={self.id}, type='{self.validation_type}', score={self.validation_score})>"

    @property
    def has_competitor_data(self) -> bool:
        """Check if validation includes competitor pricing data"""
        return self.competitor_pricing is not None and len(self.competitor_pricing) > 0

    @property
    def has_market_size_data(self) -> bool:
        """Check if validation includes market size data"""
        return self.market_size_tam is not None

    @property
    def average_competitor_pricing(self) -> float:
        """Calculate average pricing from competitor data"""
        if not self.has_competitor_data:
            return None

        # Extract prices from competitor_pricing JSONB
        prices = [
            comp.get('price', 0)
            for comp in self.competitor_pricing
            if comp.get('price')
        ]

        return sum(prices) / len(prices) if prices else None
```

---

## Phase 4 Tasks

### Task List

1. **Add Agno Columns Migration** (1 day)
   - Create `001_add_agno_columns.sql`
   - Test migration on development database
   - Verify indexes created correctly
   - Document rollback procedure

2. **Add Jina Columns Migration** (1 day)
   - Create `002_add_jina_columns.sql`
   - Test JSONB columns and GIN indexes
   - Verify data types and constraints
   - Test with sample data

3. **Update SQLAlchemy Models** (1 day)
   - Extend `Opportunity` model with Agno fields
   - Extend `Opportunity` model with Jina fields
   - Update `MarketValidation` model
   - Add helper properties and methods
   - Test model relationships

4. **Data Persistence Testing** (1 day)
   - Test Agno data storage and retrieval
   - Test Jina data storage and retrieval
   - Test JSONB query performance
   - Test indexes improve query speed
   - Verify data integrity constraints

### Deliverables

- Database schema migration scripts
- Updated SQLAlchemy models
- Comprehensive data persistence tests
- Performance benchmarks
- Migration documentation

---

## Data Persistence Testing

### File Location

**File**: `/tests/integration/test_data_persistence.py`

### Test Suite

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.opportunity import Opportunity
from models.market_validation import MarketValidation
from transform.agno_analyzer import AgnoOpportunityAnalyzer
from models.submission import RedditSubmission


@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine('postgresql://localhost/redditharbor_test')
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_agno_data_storage(db_session):
    """Test Agno multi-agent scores are stored correctly"""
    analyzer = AgnoOpportunityAnalyzer()
    submission = RedditSubmission(
        id="test123",
        title="Looking for automation tool",
        selftext="Need to automate tasks",
        subreddit="productivity"
    )

    # Analyze with Agno
    result = analyzer.analyze_submission(submission)

    # Create Opportunity record
    opportunity = Opportunity(
        submission_id=submission.id,
        app_title=result.app_idea.title,
        app_concept=result.app_idea.app_concept,
        final_score=result.final_score,

        # Agno fields
        agno_wtp_score=75.5,
        agno_segment_confidence=82.3,
        agno_price_potential=68.9,
        agno_behavior_score=71.2,
        agno_consensus_confidence=74.5
    )

    db_session.add(opportunity)
    db_session.commit()

    # Retrieve and verify
    stored = db_session.query(Opportunity).filter_by(id=opportunity.id).first()
    assert stored.agno_wtp_score == 75.5
    assert stored.agno_segment_confidence == 82.3
    assert stored.has_agno_analysis is True


def test_jina_data_storage(db_session):
    """Test Jina market validation data is stored correctly"""
    opportunity = Opportunity(
        app_title="Test App",
        app_concept="Test concept",
        final_score=80.0,

        # Jina fields
        jina_validation_score=85.2,
        jina_data_quality_score=90.5,
        jina_competitor_count=5,
        jina_market_size_tam="$1.5B",
        jina_market_size_growth="12% CAGR",
        jina_evidence_urls=["https://competitor1.com", "https://competitor2.com"],
        jina_api_cost_usd=0.007,
        jina_cache_hit_rate=0.65
    )

    db_session.add(opportunity)
    db_session.commit()

    # Retrieve and verify
    stored = db_session.query(Opportunity).filter_by(id=opportunity.id).first()
    assert stored.jina_validation_score == 85.2
    assert stored.jina_competitor_count == 5
    assert len(stored.jina_evidence_urls) == 2
    assert stored.has_jina_validation is True


def test_market_validation_relationship(db_session):
    """Test Opportunity -> MarketValidation relationship"""
    opportunity = Opportunity(
        app_title="Test App",
        app_concept="Test concept"
    )
    db_session.add(opportunity)
    db_session.flush()

    # Add market validation
    validation = MarketValidation(
        opportunity_id=opportunity.id,
        validation_type='competitor',
        validation_source='jina',
        validation_score=82.5,
        competitor_pricing=[
            {
                "company": "Competitor A",
                "pricing_model": "subscription",
                "price": 29.99,
                "tiers": ["basic", "pro", "enterprise"]
            }
        ],
        competitors_found=3,
        urls_fetched=["https://competitor-a.com/pricing"]
    )

    db_session.add(validation)
    db_session.commit()

    # Verify relationship
    stored_opp = db_session.query(Opportunity).filter_by(id=opportunity.id).first()
    assert len(stored_opp.market_validations) == 1
    assert stored_opp.market_validations[0].validation_type == 'competitor'


def test_jsonb_query_performance(db_session):
    """Test JSONB columns are indexed and queryable"""
    # Create opportunities with JSONB evidence
    for i in range(100):
        opp = Opportunity(
            app_title=f"App {i}",
            app_concept=f"Concept {i}",
            jina_evidence_urls=[
                f"https://competitor{i}.com",
                f"https://market-report{i}.com"
            ]
        )
        db_session.add(opp)

    db_session.commit()

    # Query using JSONB containment (uses GIN index)
    import time
    start = time.time()

    results = db_session.query(Opportunity).filter(
        Opportunity.jina_evidence_urls.contains(["https://competitor50.com"])
    ).all()

    elapsed = time.time() - start

    assert len(results) == 1
    assert elapsed < 0.1  # Should be fast with GIN index


def test_agno_composite_index_performance(db_session):
    """Test composite index on Agno scores improves query performance"""
    # Create opportunities with Agno scores
    for i in range(1000):
        opp = Opportunity(
            app_title=f"App {i}",
            app_concept=f"Concept {i}",
            agno_wtp_score=float(i % 100),
            agno_segment_confidence=float(i % 90),
            agno_price_potential=float(i % 80)
        )
        db_session.add(opp)

    db_session.commit()

    # Query using composite index
    import time
    start = time.time()

    results = db_session.query(Opportunity).filter(
        Opportunity.agno_wtp_score > 80,
        Opportunity.agno_segment_confidence > 75,
        Opportunity.agno_price_potential > 70
    ).all()

    elapsed = time.time() - start

    assert elapsed < 0.05  # Should be very fast with composite index
```

---

## Success Criteria

### Phase 4 Completion Checklist

- [ ] All migration scripts created and tested
- [ ] Migrations run successfully on development database
- [ ] SQLAlchemy models updated with new columns
- [ ] Model relationships tested and working
- [ ] All data persistence tests passing
- [ ] Query performance benchmarks established
- [ ] Indexes verified to improve performance
- [ ] Rollback procedures documented
- [ ] Database documentation updated

### Quality Metrics

- **Migration Success**: 100% success rate on dev/test databases
- **Test Coverage**: >85% for data persistence code
- **Query Performance**: <50ms for indexed queries on 10K records
- **Data Integrity**: All constraints and relationships validated

---

## Performance Benchmarks

### Expected Query Performance

| Query Type | Without Index | With Index | Improvement |
|-----------|--------------|-----------|-------------|
| Agno WTP Score Filter | 250ms | 15ms | 16x faster |
| Jina Validation Score | 300ms | 12ms | 25x faster |
| JSONB Evidence URLs | 500ms | 20ms | 25x faster |
| Composite Agno Filter | 800ms | 25ms | 32x faster |

### Storage Impact

- **Agno Columns**: ~40 bytes per row
- **Jina Columns**: ~200 bytes per row (includes JSONB)
- **Total Increase**: ~240 bytes per opportunity
- **For 100K opportunities**: ~24 MB additional storage

---

## Rollback Procedures

### Rollback Migration 002 (Jina Columns)

```sql
BEGIN;

-- Drop Jina indexes
DROP INDEX IF EXISTS idx_opportunities_jina_validation;
DROP INDEX IF EXISTS idx_opportunities_jina_quality;
DROP INDEX IF EXISTS idx_opportunities_jina_evidence;

-- Drop Jina columns
ALTER TABLE opportunities DROP COLUMN IF EXISTS jina_validation_score;
ALTER TABLE opportunities DROP COLUMN IF EXISTS jina_data_quality_score;
ALTER TABLE opportunities DROP COLUMN IF EXISTS jina_competitor_count;
ALTER TABLE opportunities DROP COLUMN IF EXISTS jina_market_size_tam;
ALTER TABLE opportunities DROP COLUMN IF EXISTS jina_market_size_growth;
ALTER TABLE opportunities DROP COLUMN IF EXISTS jina_evidence_urls;
ALTER TABLE opportunities DROP COLUMN IF EXISTS jina_api_cost_usd;
ALTER TABLE opportunities DROP COLUMN IF EXISTS jina_cache_hit_rate;

COMMIT;
```

### Rollback Migration 001 (Agno Columns)

```sql
BEGIN;

-- Drop Agno indexes
DROP INDEX IF EXISTS idx_opportunities_agno_wtp;
DROP INDEX IF EXISTS idx_opportunities_agno_consensus;
DROP INDEX IF EXISTS idx_opportunities_agno_composite;

-- Drop Agno columns
ALTER TABLE opportunities DROP COLUMN IF EXISTS agno_wtp_score;
ALTER TABLE opportunities DROP COLUMN IF EXISTS agno_segment_confidence;
ALTER TABLE opportunities DROP COLUMN IF EXISTS agno_price_potential;
ALTER TABLE opportunities DROP COLUMN IF EXISTS agno_behavior_score;
ALTER TABLE opportunities DROP COLUMN IF EXISTS agno_consensus_confidence;

COMMIT;
```

---

## Next Steps

After Phase 4 completion:

1. **Phase 5**: Production testing and optimization
2. **A/B Testing**: Compare single LLM vs Agno analysis
3. **Performance Tuning**: Optimize query patterns
4. **Documentation**: Update API docs with new fields

---

## References

### Related Documentation

- [AGNO_INTEGRATION_ARCHITECTURE.md](/pipeline-v3/docs/AGNO_INTEGRATION_ARCHITECTURE.md) - Complete architecture
- [Phase 2: Factory Pattern Integration](/pipeline-v3/docs/agno-integration/implementation/phase-2-factory-pattern.md)
- [Jina Market Validation Persistency Analysis](/docs/integrations/jina/market-validation-persistency-analysis.md)

### Code Files

- `/pipeline-v3/migrations/` - Database migration scripts
- `/pipeline-v3/models/opportunity.py` - SQLAlchemy models
- `/tests/integration/test_data_persistence.py` - Persistence tests

---

**Document Version**: 1.0
**Created**: 2025-12-03
**Last Updated**: 2025-12-03
**Status**: Implementation Ready
