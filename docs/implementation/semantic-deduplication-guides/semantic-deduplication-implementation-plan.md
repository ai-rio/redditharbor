# RedditHarbor Semantic Deduplication - Consolidated Implementation Plan

**Author**: Claude Code
**Date**: 2025-11-18
**Status**: Ready for Implementation
**Target Schema**: opportunities_unified (primary) + app_opportunities (DLT staging)

---

## Executive Summary

This plan provides a **pragmatic, solo-developer-friendly** approach to implementing semantic deduplication in RedditHarbor, addressing the duplicate AI-enriched profiles issue while respecting the existing dual-table architecture.

### Key Decisions
- ✅ **Phased approach**: String-based first (Week 1), ML-based later (Week 2-3)
- ✅ **Target both tables**: app_opportunities (DLT staging) + opportunities_unified (canonical)
- ✅ **Start simple**: No ML dependencies in Phase 1
- ✅ **Low risk**: Backward compatible, non-breaking changes

### Expected Outcomes
- **Week 1**: 40-50% duplicate reduction (string-based)
- **Week 2-3**: 60-80% duplicate reduction (semantic ML)
- **Cost Savings**: 60-80% reduction in redundant LLM processing
- **Storage Savings**: 40-60% reduction in duplicate records

---

## Current Architecture Analysis

### Actual Schema (from Docker dump 2025-11-18)

```
PUBLIC SCHEMA TABLES (32 total)
├── DLT Pipeline Layer (3 tables)
│   ├── _dlt_loads
│   ├── _dlt_pipeline_state
│   └── _dlt_version
│
├── DLT Staging (2 tables) ⚠️ IMPORTANT
│   ├── app_opportunities (27 columns, DLT managed)
│   └── app_opportunities__core_functions (child table for array flattening)
│
├── Unified Canonical (2 tables) ✅ PRIMARY TARGET
│   ├── opportunities_unified (25 columns, UUID PK)
│   └── opportunity_assessments
│
├── Legacy Workflow (1 table) ⚠️
│   └── workflow_results (still referenced by pipelines)
│
├── Reddit Data (4 tables)
│   ├── subreddits
│   ├── redditors
│   ├── submissions
│   └── comments
│
├── Scoring (2 tables)
│   ├── opportunity_scores
│   └── score_components
│
├── Validation/Analysis (7 tables)
│   ├── market_validations
│   ├── competitive_landscape
│   ├── cross_platform_verification
│   ├── feature_gaps
│   ├── monetization_patterns
│   ├── technical_assessments
│   └── user_willingness_to_pay
│
└── Backups (9 tables)
    └── *_backup_20251118_074449 (clean snapshot)
```

### Data Flow Understanding

```
Reddit API
    ↓
DLT Pipeline (core/dlt_collection.py)
    ↓
app_opportunities (staging table)
    ↓
Transformation/Enrichment (AI profiles)
    ↓
opportunities_unified (canonical storage)
    ↓
opportunity_assessments (scoring/analysis)
```

### Critical Insight: Dual Table Strategy

**app_opportunities** = DLT-managed staging table
- Receives raw Reddit data
- Temporary storage for pipeline processing
- VARCHAR types, no constraints
- Uses DLT merge disposition with _dlt_id

**opportunities_unified** = Canonical opportunity storage
- Clean, normalized schema
- UUID primary keys
- JSONB for structured data
- Proper constraints and indexes
- Foreign key to submissions table

**Deduplication Strategy**: Must handle BOTH tables!

---

## Implementation Plan

### Phase 1: String-Based Deduplication (Week 1)
**Goal**: 40-50% duplicate reduction with zero ML complexity

#### 1.1 Database Schema Changes

```sql
-- Add deduplication columns to opportunities_unified
ALTER TABLE opportunities_unified
ADD COLUMN business_concept_id BIGINT,
ADD COLUMN semantic_fingerprint TEXT,
ADD COLUMN is_duplicate BOOLEAN DEFAULT FALSE,
ADD COLUMN duplicate_of_id UUID REFERENCES opportunities_unified(id);

-- Create canonical business concepts table
CREATE TABLE business_concepts (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  concept_name TEXT NOT NULL,
  concept_fingerprint TEXT UNIQUE NOT NULL,
  embedding VECTOR(384),  -- NULL in Phase 1, populated in Phase 2
  first_seen_at TIMESTAMPTZ DEFAULT NOW(),
  last_updated_at TIMESTAMPTZ DEFAULT NOW(),
  submission_count INTEGER DEFAULT 1,
  primary_opportunity_id UUID REFERENCES opportunities_unified(id),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX idx_business_concepts_fingerprint
ON business_concepts(concept_fingerprint);

CREATE INDEX idx_opportunities_unified_business_concept_id
ON opportunities_unified(business_concept_id);

CREATE INDEX idx_opportunities_unified_is_duplicate
ON opportunities_unified(is_duplicate);

-- Add foreign key after Phase 1 migration complete
ALTER TABLE opportunities_unified
ADD CONSTRAINT fk_business_concept
FOREIGN KEY (business_concept_id) REFERENCES business_concepts(id);
```

#### 1.2 Python Implementation

**File**: `core/deduplication.py`

```python
"""
RedditHarbor Semantic Deduplication Engine
Phase 1: String-based deduplication (no ML dependencies)
"""

import hashlib
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SimpleDeduplicator:
    """
    Phase 1: String-based deduplication using normalized concept fingerprints.
    No ML dependencies - fast, simple, effective for ~40-50% duplicates.
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize with Supabase client."""
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def normalize_concept(self, concept: str) -> str:
        """
        Normalize business concept for fingerprinting.

        Args:
            concept: Raw business concept text

        Returns:
            Normalized concept string
        """
        if not concept:
            return ""

        # Convert to lowercase
        normalized = concept.lower().strip()

        # Remove common variations
        normalized = normalized.replace("app idea:", "")
        normalized = normalized.replace("app:", "")
        normalized = normalized.replace("mobile app", "app")
        normalized = normalized.replace("web app", "app")

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def generate_fingerprint(self, concept: str) -> str:
        """
        Generate SHA256 fingerprint from normalized concept.

        Args:
            concept: Business concept text

        Returns:
            SHA256 hash as hexadecimal string
        """
        normalized = self.normalize_concept(concept)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def find_existing_concept(self, fingerprint: str) -> Optional[Dict]:
        """
        Check if business concept already exists.

        Args:
            fingerprint: Concept fingerprint to search for

        Returns:
            Existing concept dict or None
        """
        try:
            response = self.supabase.table('business_concepts')\
                .select('id, concept_name, primary_opportunity_id, submission_count')\
                .eq('concept_fingerprint', fingerprint)\
                .execute()

            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error finding concept: {e}")
            return None

    def create_business_concept(
        self,
        concept_name: str,
        fingerprint: str,
        opportunity_id: str
    ) -> Optional[int]:
        """
        Create new business concept.

        Args:
            concept_name: Human-readable concept name
            fingerprint: Unique concept fingerprint
            opportunity_id: UUID of primary opportunity

        Returns:
            Concept ID or None on error
        """
        try:
            response = self.supabase.table('business_concepts').insert({
                'concept_name': concept_name,
                'concept_fingerprint': fingerprint,
                'primary_opportunity_id': opportunity_id,
                'metadata': {
                    'created_by': 'simple_deduplicator',
                    'phase': 1,
                    'method': 'string_fingerprint'
                }
            }).execute()

            return response.data[0]['id']

        except Exception as e:
            logger.error(f"Error creating concept: {e}")
            return None

    def update_concept_stats(self, concept_id: int) -> None:
        """
        Update concept submission count and timestamp.

        Args:
            concept_id: ID of business concept to update
        """
        try:
            # Increment submission count
            self.supabase.rpc('increment_concept_count', {
                'concept_id': concept_id
            }).execute()

            # Update timestamp
            self.supabase.table('business_concepts').update({
                'last_updated_at': datetime.utcnow().isoformat()
            }).eq('id', concept_id).execute()

        except Exception as e:
            logger.warning(f"Error updating concept stats: {e}")

    def mark_as_duplicate(
        self,
        opportunity_id: str,
        concept_id: int,
        primary_opportunity_id: str
    ) -> bool:
        """
        Mark opportunity as duplicate of existing concept.

        Args:
            opportunity_id: UUID of duplicate opportunity
            concept_id: Business concept ID
            primary_opportunity_id: UUID of primary opportunity

        Returns:
            Success boolean
        """
        try:
            self.supabase.table('opportunities_unified').update({
                'business_concept_id': concept_id,
                'is_duplicate': True,
                'duplicate_of_id': primary_opportunity_id,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', opportunity_id).execute()

            return True

        except Exception as e:
            logger.error(f"Error marking duplicate: {e}")
            return False

    def mark_as_unique(self, opportunity_id: str, concept_id: int) -> bool:
        """
        Mark opportunity as unique (first of its concept).

        Args:
            opportunity_id: UUID of unique opportunity
            concept_id: Business concept ID

        Returns:
            Success boolean
        """
        try:
            self.supabase.table('opportunities_unified').update({
                'business_concept_id': concept_id,
                'is_duplicate': False,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', opportunity_id).execute()

            return True

        except Exception as e:
            logger.error(f"Error marking unique: {e}")
            return False

    def process_opportunity(self, opportunity: Dict) -> Dict:
        """
        Process single opportunity for deduplication.

        Args:
            opportunity: Opportunity dict with 'id' and 'app_concept'

        Returns:
            Result dict with 'is_duplicate', 'concept_id', 'success'
        """
        try:
            opportunity_id = opportunity.get('id')
            app_concept = opportunity.get('app_concept', '')

            if not opportunity_id or not app_concept:
                return {
                    'success': False,
                    'error': 'Missing required fields: id or app_concept'
                }

            # Generate fingerprint
            fingerprint = self.generate_fingerprint(app_concept)

            # Check for existing concept
            existing_concept = self.find_existing_concept(fingerprint)

            if existing_concept:
                # Duplicate found
                concept_id = existing_concept['id']
                primary_opp_id = existing_concept['primary_opportunity_id']

                success = self.mark_as_duplicate(
                    opportunity_id,
                    concept_id,
                    primary_opp_id
                )

                if success:
                    self.update_concept_stats(concept_id)

                return {
                    'success': success,
                    'is_duplicate': True,
                    'concept_id': concept_id,
                    'duplicate_of': primary_opp_id,
                    'message': f'Linked to existing concept {concept_id}'
                }
            else:
                # New unique concept
                concept_id = self.create_business_concept(
                    app_concept,
                    fingerprint,
                    opportunity_id
                )

                if concept_id:
                    success = self.mark_as_unique(opportunity_id, concept_id)

                    return {
                        'success': success,
                        'is_duplicate': False,
                        'concept_id': concept_id,
                        'message': f'Created new concept {concept_id}'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to create business concept'
                    }

        except Exception as e:
            logger.error(f"Error processing opportunity {opportunity.get('id')}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class SemanticDeduplicator(SimpleDeduplicator):
    """
    Phase 2: ML-based semantic deduplication using sentence transformers.
    Extends SimpleDeduplicator with embedding-based similarity search.
    """

    def __init__(self, supabase_url: str, supabase_key: str, similarity_threshold: float = 0.85):
        """
        Initialize with sentence transformer model.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service key
            similarity_threshold: Minimum similarity for duplicates (0-1)
        """
        super().__init__(supabase_url, supabase_key)

        # Import here to avoid Phase 1 dependency
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.similarity_threshold = similarity_threshold
        logger.info(f"Initialized SemanticDeduplicator with threshold {similarity_threshold}")

    def generate_embedding(self, text: str) -> list:
        """
        Generate 384-dimensional embedding for text.

        Args:
            text: Input text to embed

        Returns:
            List of floats (embedding vector)
        """
        import numpy as np

        normalized_text = self.normalize_concept(text)
        embedding = self.model.encode(normalized_text, normalize_embeddings=True)
        return embedding.tolist()

    def find_similar_concepts(self, text: str, threshold: Optional[float] = None) -> list:
        """
        Find semantically similar business concepts using pgvector.

        Args:
            text: Business concept text to search
            threshold: Similarity threshold (uses instance default if None)

        Returns:
            List of similar concepts with similarity scores
        """
        if threshold is None:
            threshold = self.similarity_threshold

        embedding = self.generate_embedding(text)

        try:
            response = self.supabase.rpc('find_similar_concepts', {
                'query_embedding': embedding,
                'match_threshold': threshold,
                'max_results': 10
            }).execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error finding similar concepts: {e}")
            return []

    def process_opportunity(self, opportunity: Dict) -> Dict:
        """
        Process opportunity with semantic similarity search.
        Falls back to fingerprint matching if no semantic matches found.

        Args:
            opportunity: Opportunity dict

        Returns:
            Deduplication result
        """
        # Try semantic matching first
        app_concept = opportunity.get('app_concept', '')
        similar_concepts = self.find_similar_concepts(app_concept)

        if similar_concepts:
            # Use most similar concept
            best_match = similar_concepts[0]
            concept_id = best_match['concept_id']
            similarity_score = best_match['similarity_score']

            logger.info(
                f"Semantic match found: concept_id={concept_id}, "
                f"similarity={similarity_score:.3f}"
            )

            # Mark as duplicate with similarity metadata
            opportunity_id = opportunity['id']
            primary_opp_id = best_match.get('primary_opportunity_id')

            self.mark_as_duplicate(opportunity_id, concept_id, primary_opp_id)
            self.update_concept_stats(concept_id)

            return {
                'success': True,
                'is_duplicate': True,
                'concept_id': concept_id,
                'duplicate_of': primary_opp_id,
                'similarity_score': similarity_score,
                'method': 'semantic_embedding',
                'message': f'Semantic match (similarity={similarity_score:.3f})'
            }

        # Fallback to fingerprint matching (from parent class)
        return super().process_opportunity(opportunity)
```

#### 1.3 Migration Script for Existing Data

**File**: `scripts/deduplication/migrate_existing_opportunities.py`

```python
"""
Migrate existing opportunities_unified records to deduplication system.
Phase 1: String-based fingerprinting
"""

import os
import sys
from datetime import datetime
from typing import Dict

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.deduplication import SimpleDeduplicator
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def migrate_existing_data():
    """Migrate all opportunities_unified records to deduplication system."""

    print("🚀 Starting Phase 1 deduplication migration...")
    print(f"⏰ Started at: {datetime.now().isoformat()}\n")

    # Initialize
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        return

    supabase = create_client(supabase_url, supabase_key)
    deduplicator = SimpleDeduplicator(supabase_url, supabase_key)

    # Fetch opportunities without business_concept_id
    print("📊 Fetching opportunities to process...")
    response = supabase.table('opportunities_unified')\
        .select('id, app_concept, title, created_at')\
        .is_('business_concept_id', 'null')\
        .order('created_at', desc=False)\
        .execute()

    opportunities = response.data
    total = len(opportunities)

    if total == 0:
        print("✅ No opportunities to process - all already deduplicated!")
        return

    print(f"📝 Found {total} opportunities to process\n")

    # Process statistics
    stats = {
        'total': total,
        'processed': 0,
        'unique_concepts': 0,
        'duplicates': 0,
        'errors': 0,
        'start_time': datetime.now()
    }

    # Process each opportunity
    for i, opp in enumerate(opportunities, 1):
        try:
            result = deduplicator.process_opportunity(opp)

            stats['processed'] += 1

            if result.get('success'):
                if result.get('is_duplicate'):
                    stats['duplicates'] += 1
                else:
                    stats['unique_concepts'] += 1
            else:
                stats['errors'] += 1
                print(f"⚠️  Error processing {opp['id']}: {result.get('error')}")

            # Progress update every 100 records
            if i % 100 == 0:
                elapsed = (datetime.now() - stats['start_time']).total_seconds()
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (total - i) / rate if rate > 0 else 0

                print(f"📈 Progress: {i}/{total} ({i/total*100:.1f}%)")
                print(f"   Unique: {stats['unique_concepts']}, Duplicates: {stats['duplicates']}, Errors: {stats['errors']}")
                print(f"   Rate: {rate:.1f} records/sec, ETA: {remaining:.0f}s\n")

        except Exception as e:
            stats['errors'] += 1
            print(f"❌ Exception processing {opp.get('id')}: {e}")

    # Final statistics
    stats['end_time'] = datetime.now()
    stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
    stats['deduplication_rate'] = stats['duplicates'] / total * 100 if total > 0 else 0

    print("\n" + "="*60)
    print("🎉 MIGRATION COMPLETE!")
    print("="*60)
    print(f"Total Processed:    {stats['processed']:,}")
    print(f"Unique Concepts:    {stats['unique_concepts']:,}")
    print(f"Duplicates Found:   {stats['duplicates']:,} ({stats['deduplication_rate']:.1f}%)")
    print(f"Errors:             {stats['errors']:,}")
    print(f"Duration:           {stats['duration']:.1f}s")
    print(f"Processing Rate:    {stats['processed']/stats['duration']:.1f} records/sec")
    print("="*60)

    # Save results
    results_file = f"migration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import json
    with open(results_file, 'w') as f:
        json.dump({
            k: str(v) if isinstance(v, datetime) else v
            for k, v in stats.items()
        }, f, indent=2)

    print(f"\n💾 Results saved to: {results_file}")

if __name__ == '__main__':
    migrate_existing_data()
```

#### 1.4 SQL Helper Functions

```sql
-- Helper function to increment concept submission count
CREATE OR REPLACE FUNCTION increment_concept_count(concept_id BIGINT)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE business_concepts
  SET submission_count = submission_count + 1
  WHERE id = concept_id;
END;
$$;

-- View for deduplication statistics
CREATE OR REPLACE VIEW deduplication_stats AS
SELECT
  COUNT(*) as total_opportunities,
  COUNT(CASE WHEN is_duplicate THEN 1 END) as duplicates,
  COUNT(CASE WHEN NOT is_duplicate THEN 1 END) as unique,
  COUNT(DISTINCT business_concept_id) as total_concepts,
  ROUND(
    COUNT(CASE WHEN is_duplicate THEN 1 END)::numeric /
    NULLIF(COUNT(*), 0) * 100,
    2
  ) as deduplication_rate_percent
FROM opportunities_unified
WHERE business_concept_id IS NOT NULL;
```

---

### Phase 2: Semantic Deduplication (Week 2-3)
**Goal**: Enhance to 60-80% duplicate reduction using ML

#### 2.1 Enable pgvector Extension

```sql
-- Enable pgvector in Supabase
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- Add HNSW index for fast similarity search
CREATE INDEX idx_business_concepts_embedding_hnsw
ON business_concepts
USING hnsw (embedding vector_ip_ops)
WITH (m = 16, ef_construction = 64);
```

#### 2.2 Install ML Dependencies

```bash
# Add to requirements.txt
sentence-transformers>=2.2.2
torch>=2.0.0  # CPU version for solo dev
numpy>=1.24.0

# Install
uv sync
```

#### 2.3 Generate Embeddings for Existing Concepts

**File**: `scripts/deduplication/generate_embeddings.py`

```python
"""
Generate embeddings for existing business concepts.
Run AFTER Phase 1 migration complete.
"""

import os
import sys
from datetime import datetime
from sentence_transformers import SentenceTransformer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def generate_embeddings():
    """Generate embeddings for all business concepts without embeddings."""

    print("🧠 Generating embeddings for business concepts...")

    # Initialize
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Fetch concepts without embeddings
    response = supabase.table('business_concepts')\
        .select('id, concept_name')\
        .is_('embedding', 'null')\
        .execute()

    concepts = response.data
    total = len(concepts)

    print(f"📝 Found {total} concepts to process\n")

    processed = 0
    for i, concept in enumerate(concepts, 1):
        try:
            # Generate embedding
            embedding = model.encode(
                concept['concept_name'],
                normalize_embeddings=True
            ).tolist()

            # Update database
            supabase.table('business_concepts').update({
                'embedding': embedding
            }).eq('id', concept['id']).execute()

            processed += 1

            if i % 100 == 0:
                print(f"📈 Progress: {i}/{total} ({i/total*100:.1f}%)")

        except Exception as e:
            print(f"❌ Error processing concept {concept['id']}: {e}")

    print(f"\n✅ Completed: {processed}/{total} embeddings generated")

if __name__ == '__main__':
    generate_embeddings()
```

#### 2.4 Similarity Search SQL Function

```sql
-- Function for semantic similarity search
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
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    bc.id as concept_id,
    bc.concept_name,
    (1 - (bc.embedding <=> query_embedding)) as similarity_score,
    bc.primary_opportunity_id,
    bc.submission_count
  FROM business_concepts bc
  WHERE
    bc.embedding IS NOT NULL
    AND (1 - (bc.embedding <=> query_embedding)) >= match_threshold
  ORDER BY bc.embedding <=> query_embedding
  LIMIT max_results;
END;
$$;
```

---

### Phase 3: DLT Pipeline Integration (Week 3-4)

#### 3.1 Update DLT Pipeline

Add deduplication middleware to existing pipeline:

```python
# In your existing DLT pipeline file
from core.deduplication import SemanticDeduplicator
import os

# Initialize deduplicator (use Simple in Phase 1, Semantic in Phase 2)
deduplicator = SemanticDeduplicator(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY'),
    similarity_threshold=0.85
)

@dlt.resource(write_disposition="merge", merge_key="id")
def app_opportunities_with_dedup():
    """Existing resource enhanced with deduplication."""

    # Your existing Reddit data extraction
    reddit_data = fetch_reddit_opportunities()  # Your existing function

    for opportunity in reddit_data:
        # Process through deduplication BEFORE yielding
        dedup_result = deduplicator.process_opportunity(opportunity)

        # Add deduplication metadata
        opportunity['_deduplication'] = dedup_result

        yield opportunity
```

---

## Testing Strategy

### Phase 1 Testing

```python
# tests/test_deduplication.py
import pytest
from core.deduplication import SimpleDeduplicator

def test_fingerprint_generation():
    """Test fingerprint consistency."""
    dedup = SimpleDeduplicator('test_url', 'test_key')

    concept1 = "FitnessFAQ app for tracking workouts"
    concept2 = "FitnessFAQ App for Tracking Workouts"  # Different case

    fp1 = dedup.generate_fingerprint(concept1)
    fp2 = dedup.generate_fingerprint(concept2)

    assert fp1 == fp2, "Fingerprints should match despite case differences"

def test_concept_normalization():
    """Test concept normalization."""
    dedup = SimpleDeduplicator('test_url', 'test_key')

    normalized = dedup.normalize_concept("  Mobile App: FitnessFAQ  ")
    assert normalized == "app: fitnessfaq"
```

### Phase 2 Testing

```python
def test_semantic_similarity():
    """Test semantic deduplication finds similar concepts."""
    from core.deduplication import SemanticDeduplicator

    dedup = SemanticDeduplicator('test_url', 'test_key')

    concept1 = "Fitness tracking app"
    concept2 = "Workout monitoring application"

    emb1 = dedup.generate_embedding(concept1)
    emb2 = dedup.generate_embedding(concept2)

    # Calculate cosine similarity
    import numpy as np
    similarity = np.dot(emb1, emb2)

    assert similarity > 0.7, "Similar concepts should have high similarity"
```

---

## Monitoring & Metrics

### Key Metrics Dashboard

```sql
-- Deduplication effectiveness query
SELECT
  ds.total_opportunities,
  ds.duplicates,
  ds.unique,
  ds.total_concepts,
  ds.deduplication_rate_percent,

  -- Cost savings estimate (assuming $0.01 per LLM enrichment)
  ds.duplicates * 0.01 as estimated_cost_savings_usd,

  -- Storage savings estimate (assuming 10KB per duplicate)
  ROUND(ds.duplicates * 10 / 1024.0, 2) as estimated_storage_savings_mb

FROM deduplication_stats ds;

-- Top duplicated concepts
SELECT
  bc.concept_name,
  bc.submission_count,
  bc.first_seen_at,
  bc.last_updated_at
FROM business_concepts bc
WHERE bc.submission_count > 1
ORDER BY bc.submission_count DESC
LIMIT 20;
```

---

## Rollback Plan

If issues arise:

```sql
-- Disable deduplication
UPDATE opportunities_unified
SET
  business_concept_id = NULL,
  is_duplicate = FALSE,
  duplicate_of_id = NULL;

-- Drop constraints
ALTER TABLE opportunities_unified
DROP CONSTRAINT IF EXISTS fk_business_concept;

-- Keep business_concepts table for investigation
-- Don't drop it immediately
```

---

## Success Criteria

### Phase 1 (Week 1)
- ✅ 40-50% deduplication rate achieved
- ✅ Zero errors in migration script
- ✅ Sub-100ms fingerprint lookup performance
- ✅ All existing opportunities processed

### Phase 2 (Week 2-3)
- ✅ 60-80% deduplication rate achieved
- ✅ Embeddings generated for all concepts
- ✅ Semantic search returns results in <500ms
- ✅ pgvector index operational

### Phase 3 (Week 3-4)
- ✅ DLT pipeline integrated with deduplication
- ✅ Real-time deduplication working in production
- ✅ Monitoring dashboard showing cost savings
- ✅ No duplicate AI enrichments being created

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Run Phase 1 migration** on staging/local environment
3. **Validate results** before production deployment
4. **Monitor metrics** for first week
5. **Proceed to Phase 2** only if Phase 1 successful

---

**Questions or concerns? Review this plan thoroughly before implementation.**
