# Semantic Deduplication - Quick Start Guide

**For Solo Developers | Week-by-Week Implementation**

---

## Week 1: String-Based Deduplication (No ML Required)

### Day 1-2: Database Setup

```bash
# 1. Apply schema changes
supabase db reset  # Or apply migration manually

# 2. Run this SQL in Supabase SQL Editor:
```

```sql
-- Add deduplication columns
ALTER TABLE opportunities_unified
ADD COLUMN business_concept_id BIGINT,
ADD COLUMN semantic_fingerprint TEXT,
ADD COLUMN is_duplicate BOOLEAN DEFAULT FALSE,
ADD COLUMN duplicate_of_id UUID REFERENCES opportunities_unified(id);

-- Create business_concepts table
CREATE TABLE business_concepts (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  concept_name TEXT NOT NULL,
  concept_fingerprint TEXT UNIQUE NOT NULL,
  embedding VECTOR(384),
  first_seen_at TIMESTAMPTZ DEFAULT NOW(),
  last_updated_at TIMESTAMPTZ DEFAULT NOW(),
  submission_count INTEGER DEFAULT 1,
  primary_opportunity_id UUID REFERENCES opportunities_unified(id),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_business_concepts_fingerprint
ON business_concepts(concept_fingerprint);

CREATE INDEX idx_opportunities_unified_business_concept_id
ON opportunities_unified(business_concept_id);

-- Helper function
CREATE OR REPLACE FUNCTION increment_concept_count(concept_id BIGINT)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  UPDATE business_concepts
  SET submission_count = submission_count + 1
  WHERE id = concept_id;
END;
$$;

-- Stats view
CREATE OR REPLACE VIEW deduplication_stats AS
SELECT
  COUNT(*) as total_opportunities,
  COUNT(CASE WHEN is_duplicate THEN 1 END) as duplicates,
  COUNT(CASE WHEN NOT is_duplicate THEN 1 END) as unique,
  COUNT(DISTINCT business_concept_id) as total_concepts,
  ROUND(
    COUNT(CASE WHEN is_duplicate THEN 1 END)::numeric /
    NULLIF(COUNT(*), 0) * 100, 2
  ) as deduplication_rate_percent
FROM opportunities_unified
WHERE business_concept_id IS NOT NULL;
```

### Day 3: Create Implementation Files

The code is already in `core/deduplication.py` (see main plan).

### Day 4-5: Test & Migrate Existing Data

```bash
# Test the deduplicator
python -c "
from core.deduplication import SimpleDeduplicator
import os
from dotenv import load_dotenv
load_dotenv()

dedup = SimpleDeduplicator(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
test_opp = {
    'id': 'test-123',
    'app_concept': 'Fitness tracking app'
}
result = dedup.process_opportunity(test_opp)
print(f'Test result: {result}')
"

# If test works, run migration
python scripts/deduplication/migrate_existing_opportunities.py
```

### Day 6-7: Monitor & Validate

```sql
-- Check deduplication stats
SELECT * FROM deduplication_stats;

-- Top duplicated concepts
SELECT
  bc.concept_name,
  bc.submission_count,
  bc.first_seen_at
FROM business_concepts bc
WHERE bc.submission_count > 1
ORDER BY bc.submission_count DESC
LIMIT 10;

-- Sample duplicates
SELECT
  ou.id,
  ou.title,
  ou.app_concept,
  ou.is_duplicate,
  bc.concept_name,
  bc.submission_count
FROM opportunities_unified ou
JOIN business_concepts bc ON ou.business_concept_id = bc.id
WHERE ou.is_duplicate = true
LIMIT 20;
```

**✅ Week 1 Success**: 40-50% duplicates found and marked!

---

## Week 2-3: Add Semantic ML (Optional Enhancement)

### Prerequisites

```bash
# Install ML dependencies
echo "sentence-transformers>=2.2.2" >> requirements.txt
echo "torch>=2.0.0" >> requirements.txt
uv sync
```

### Enable pgvector

```sql
-- In Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Add HNSW index
CREATE INDEX idx_business_concepts_embedding_hnsw
ON business_concepts
USING hnsw (embedding vector_ip_ops)
WITH (m = 16, ef_construction = 64);

-- Similarity search function
CREATE OR REPLACE FUNCTION find_similar_concepts(
  query_embedding VECTOR(384),
  match_threshold FLOAT DEFAULT 0.85,
  max_results INT DEFAULT 10
)
RETURNS TABLE (
  concept_id BIGINT,
  concept_name TEXT,
  similarity_score FLOAT,
  primary_opportunity_id UUID,
  submission_count INTEGER
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    bc.id,
    bc.concept_name,
    (1 - (bc.embedding <=> query_embedding)) as similarity_score,
    bc.primary_opportunity_id,
    bc.submission_count
  FROM business_concepts bc
  WHERE bc.embedding IS NOT NULL
    AND (1 - (bc.embedding <=> query_embedding)) >= match_threshold
  ORDER BY bc.embedding <=> query_embedding
  LIMIT max_results;
END;
$$;
```

### Generate Embeddings

```bash
# Run embedding generation script
python scripts/deduplication/generate_embeddings.py
```

### Test Semantic Search

```python
from core.deduplication import SemanticDeduplicator
import os
from dotenv import load_dotenv
load_dotenv()

dedup = SemanticDeduplicator(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Test semantic similarity
similar = dedup.find_similar_concepts("Fitness workout tracker", threshold=0.80)
print(f"Found {len(similar)} similar concepts")
for concept in similar:
    print(f"  - {concept['concept_name']} (similarity: {concept['similarity_score']:.3f})")
```

**✅ Week 2-3 Success**: 60-80% duplicates caught with ML!

---

## Week 3-4: Pipeline Integration

### Update Your DLT Pipeline

```python
# In core/dlt_app_opportunities.py or similar

from core.deduplication import SemanticDeduplicator  # or SimpleDeduplicator
import os

# Initialize once at module level
deduplicator = SemanticDeduplicator(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY'),
    similarity_threshold=0.85
)

@dlt.resource(write_disposition="merge", merge_key="submission_id")
def app_opportunities():
    """Your existing resource with deduplication."""

    # Your existing data extraction
    for opportunity in fetch_reddit_opportunities():

        # Add deduplication BEFORE yield
        dedup_result = deduplicator.process_opportunity(opportunity)
        opportunity['_dedup_result'] = dedup_result

        yield opportunity
```

### Test Pipeline

```bash
# Run pipeline in test mode
python scripts/core/collect_reddit_data.py --test --limit 10

# Check results
supabase db execute "
SELECT
  title,
  app_concept,
  is_duplicate,
  business_concept_id
FROM opportunities_unified
ORDER BY created_at DESC
LIMIT 10;
"
```

---

## Troubleshooting

### Issue: Migration script fails

```bash
# Check database connection
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('Connection successful')
"
```

### Issue: Fingerprints not matching similar concepts

```python
# Test normalization
from core.deduplication import SimpleDeduplicator
dedup = SimpleDeduplicator('url', 'key')

concept1 = "FitnessFAQ app"
concept2 = "FitnessFAQ App"

print(f"Normalized 1: {dedup.normalize_concept(concept1)}")
print(f"Normalized 2: {dedup.normalize_concept(concept2)}")
print(f"FP1: {dedup.generate_fingerprint(concept1)}")
print(f"FP2: {dedup.generate_fingerprint(concept2)}")
```

### Issue: pgvector not working

```sql
-- Check if extension enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- If not enabled
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;
```

---

## Monitoring Dashboard Queries

### Daily Stats

```sql
-- Today's deduplication performance
SELECT
  COUNT(*) as new_opportunities_today,
  COUNT(CASE WHEN is_duplicate THEN 1 END) as duplicates_caught,
  ROUND(
    COUNT(CASE WHEN is_duplicate THEN 1 END)::numeric /
    NULLIF(COUNT(*), 0) * 100, 2
  ) as dedup_rate_today
FROM opportunities_unified
WHERE created_at >= CURRENT_DATE;
```

### Cost Savings

```sql
-- Estimated cost savings
SELECT
  ds.duplicates,
  ds.duplicates * 0.01 as llm_cost_savings_usd,
  ds.duplicates * 10 / 1024.0 as storage_savings_mb
FROM deduplication_stats ds;
```

### Top Concepts

```sql
-- Most frequently seen concepts
SELECT
  concept_name,
  submission_count,
  DATE(first_seen_at) as first_seen_date,
  DATE(last_updated_at) as last_seen_date,
  EXTRACT(DAY FROM (last_updated_at - first_seen_at)) as days_active
FROM business_concepts
WHERE submission_count > 2
ORDER BY submission_count DESC
LIMIT 20;
```

---

## Rollback Instructions

If you need to rollback:

```sql
-- Disable deduplication (keeps data for analysis)
UPDATE opportunities_unified
SET
  business_concept_id = NULL,
  is_duplicate = FALSE,
  duplicate_of_id = NULL;

-- Drop foreign key (if added)
ALTER TABLE opportunities_unified
DROP CONSTRAINT IF EXISTS fk_business_concept;

-- DON'T DROP business_concepts table yet - useful for debugging
```

---

## Success Checklist

### Phase 1 Complete ✅
- [ ] business_concepts table created
- [ ] Deduplication columns added to opportunities_unified
- [ ] Migration script completed successfully
- [ ] 40-50% deduplication rate achieved
- [ ] deduplication_stats view working
- [ ] No errors in logs

### Phase 2 Complete ✅
- [ ] pgvector extension enabled
- [ ] Embeddings generated for all concepts
- [ ] Similarity search function working
- [ ] 60-80% deduplication rate achieved
- [ ] Semantic search returns results <500ms

### Phase 3 Complete ✅
- [ ] DLT pipeline integrated
- [ ] Real-time deduplication working
- [ ] Monitoring queries showing savings
- [ ] No duplicate AI enrichments created

---

## Need Help?

1. Check logs in `error_log/` directory
2. Review the main implementation plan
3. Test individual components in Python REPL
4. Verify database schema matches plan

**Remember**: Start simple (Phase 1), validate, then enhance (Phase 2-3)!
