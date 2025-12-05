-- Add vector index for embedding_vector column in opportunities table
-- This enables efficient similarity search for embeddings

-- Create ivfflat index for embedding_vector column
-- Uses cosine similarity (vector_cosine_ops) for semantic search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_opportunities_embedding_vector_cosine
ON opportunities USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);

-- Create L2 distance index as backup for different similarity metrics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_opportunities_embedding_vector_l2
ON opportunities USING ivfflat (embedding_vector vector_l2_ops)
WITH (lists = 100);

-- Add comment for documentation
COMMENT ON INDEX idx_opportunities_embedding_vector_cosine IS 'Vector index for embedding similarity search using cosine distance';
COMMENT ON INDEX idx_opportunities_embedding_vector_l2 IS 'Vector index for embedding similarity search using L2 distance';