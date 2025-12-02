-- Migration: Add Deduplication Schema
-- Description: Add tables, columns, indexes, and functions for semantic deduplication
-- Version: 001
-- Date: 2025-11-18
-- Task: Semantic Deduplication Implementation - Task 1

-- Add deduplication columns to opportunities_unified table
ALTER TABLE opportunities_unified
ADD COLUMN IF NOT EXISTS business_concept_id BIGINT,
ADD COLUMN IF NOT EXISTS semantic_fingerprint TEXT,
ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS duplicate_of_id UUID REFERENCES opportunities_unified(id);

-- Create canonical business concepts table
CREATE TABLE IF NOT EXISTS business_concepts (
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
CREATE INDEX IF NOT EXISTS idx_business_concepts_fingerprint
ON business_concepts(concept_fingerprint);

CREATE INDEX IF NOT EXISTS idx_opportunities_unified_business_concept_id
ON opportunities_unified(business_concept_id);

CREATE INDEX IF NOT EXISTS idx_opportunities_unified_is_duplicate
ON opportunities_unified(is_duplicate);

-- Index for embedding search (will be used in Phase 2)
CREATE INDEX IF NOT EXISTS idx_business_concepts_embedding_hnsw
ON business_concepts
USING hnsw (embedding vector_ip_ops)
WITH (m = 16, ef_construction = 64);

-- Add foreign key constraint (deferred to avoid circular dependency issues)
ALTER TABLE opportunities_unified
ADD CONSTRAINT IF NOT EXISTS fk_business_concept
FOREIGN KEY (business_concept_id) REFERENCES business_concepts(id);

-- Helper function to increment concept submission count
CREATE OR REPLACE FUNCTION increment_concept_count(concept_id BIGINT)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE business_concepts
  SET submission_count = submission_count + 1,
      last_updated_at = NOW()
  WHERE id = concept_id;
END;
$$;

-- Function to update concept timestamp
CREATE OR REPLACE FUNCTION update_concept_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.last_updated_at = NOW();
  RETURN NEW;
END;
$$;

-- Trigger to automatically update timestamps
CREATE TRIGGER update_business_concepts_timestamp
  BEFORE UPDATE ON business_concepts
  FOR EACH ROW
  EXECUTE FUNCTION update_concept_timestamp();

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
  ) as deduplication_rate_percent,
  COUNT(CASE WHEN is_duplicate AND duplicate_of_id IS NOT NULL THEN 1 END) as linked_duplicates,
  COUNT(CASE WHEN is_duplicate AND duplicate_of_id IS NULL THEN 1 END) as unlinked_duplicates
FROM opportunities_unified
WHERE business_concept_id IS NOT NULL;

-- View for business concept statistics
CREATE OR REPLACE VIEW business_concept_stats AS
SELECT
  bc.id,
  bc.concept_name,
  bc.submission_count,
  bc.first_seen_at,
  bc.last_updated_at,
  COUNT(ou.id) as opportunity_count,
  COUNT(CASE WHEN ou.is_duplicate THEN 1 END) as duplicate_count,
  COUNT(CASE WHEN NOT ou.is_duplicate THEN 1 END) as unique_count,
  ROUND(
    COUNT(CASE WHEN ou.is_duplicate THEN 1 END)::numeric /
    NULLIF(COUNT(ou.id), 0) * 100,
    2
  ) as duplicate_percentage
FROM business_concepts bc
LEFT JOIN opportunities_unified ou ON bc.id = ou.business_concept_id
GROUP BY bc.id, bc.concept_name, bc.submission_count, bc.first_seen_at, bc.last_updated_at
ORDER BY bc.submission_count DESC;

-- Function to find similar concepts (for Phase 2 - semantic search)
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

-- Function to mark opportunity as duplicate (with safety checks)
CREATE OR REPLACE FUNCTION mark_opportunity_duplicate(
  p_opportunity_id UUID,
  p_concept_id BIGINT,
  p_primary_opportunity_id UUID DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
  v_success BOOLEAN := FALSE;
BEGIN
  -- Validate inputs
  IF p_opportunity_id IS NULL OR p_concept_id IS NULL THEN
    RETURN FALSE;
  END IF;

  -- Update opportunity
  UPDATE opportunities_unified
  SET
    business_concept_id = p_concept_id,
    is_duplicate = TRUE,
    duplicate_of_id = COALESCE(p_primary_opportunity_id, (
      SELECT primary_opportunity_id
      FROM business_concepts
      WHERE id = p_concept_id
    )),
    updated_at = NOW()
  WHERE id = p_opportunity_id;

  -- Check if update was successful
  v_success := FOUND;

  IF v_success THEN
    -- Increment concept count
    PERFORM increment_concept_count(p_concept_id);
  END IF;

  RETURN v_success;
END;
$$;

-- Function to mark opportunity as unique
CREATE OR REPLACE FUNCTION mark_opportunity_unique(
  p_opportunity_id UUID,
  p_concept_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
  v_success BOOLEAN := FALSE;
BEGIN
  -- Validate inputs
  IF p_opportunity_id IS NULL OR p_concept_id IS NULL THEN
    RETURN FALSE;
  END IF;

  -- Update opportunity
  UPDATE opportunities_unified
  SET
    business_concept_id = p_concept_id,
    is_duplicate = FALSE,
    duplicate_of_id = NULL,
    updated_at = NOW()
  WHERE id = p_opportunity_id;

  v_success := FOUND;

  RETURN v_success;
END;
$$;

-- Add comments for documentation
COMMENT ON TABLE business_concepts IS 'Canonical storage for unique business concepts with deduplication metadata';
COMMENT ON COLUMN business_concepts.concept_fingerprint IS 'SHA256 fingerprint for exact duplicate detection';
COMMENT ON COLUMN business_concepts.embedding IS 'Vector embedding for semantic similarity search (Phase 2)';
COMMENT ON COLUMN business_concepts.submission_count IS 'Number of opportunities linked to this concept';
COMMENT ON COLUMN business_concepts.primary_opportunity_id IS 'Reference to the primary/unique opportunity for this concept';
COMMENT ON COLUMN opportunities_unified.business_concept_id IS 'Foreign key to business_concepts for deduplication';
COMMENT ON COLUMN opportunities_unified.semantic_fingerprint IS 'Deprecated - use business_concepts.concept_fingerprint instead';
COMMENT ON COLUMN opportunities_unified.is_duplicate IS 'Flag indicating if this opportunity is a duplicate';
COMMENT ON COLUMN opportunities_unified.duplicate_of_id IS 'Reference to the primary opportunity if this is a duplicate';

COMMIT;