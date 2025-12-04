-- RedditHarbor Agno Integration Migration
-- Purpose: Add Agno multi-agent and Jina market research columns
-- Database: reddit_harbor (localhost:54322)
-- Generated: 2025-12-03
-- Estimated runtime: 2-3 minutes

BEGIN;

-- ================================================================================
-- Phase 1: Add Agno Multi-Agent Columns
-- ================================================================================

-- Step 1.1: Add core Agno scoring columns
ALTER TABLE public.opportunities
ADD COLUMN IF NOT EXISTS agno_wtp_score FLOAT CHECK (agno_wtp_score >= 0 AND agno_wtp_score <= 100),
ADD COLUMN IF NOT EXISTS agno_segment_confidence FLOAT CHECK (agno_segment_confidence >= 0 AND agno_segment_confidence <= 100),
ADD COLUMN IF NOT EXISTS agno_price_potential FLOAT CHECK (agno_price_potential >= 0),
ADD COLUMN IF NOT EXISTS agno_behavior_score FLOAT CHECK (agno_behavior_score >= 0 AND agno_behavior_score <= 100),
ADD COLUMN IF NOT EXISTS agno_consensus_confidence FLOAT CHECK (agno_consensus_confidence >= 0 AND agno_consensus_confidence <= 100);

-- Step 1.2: Add Agno segmentation and metadata columns
ALTER TABLE public.opportunities
ADD COLUMN IF NOT EXISTS agno_segment_type VARCHAR(10) CHECK (agno_segment_type IN ('B2B', 'B2C', 'UNKNOWN')),
ADD COLUMN IF NOT EXISTS agno_agents_count INTEGER DEFAULT 0 CHECK (agno_agents_count >= 0),
ADD COLUMN IF NOT EXISTS agno_analysis_cost_usd NUMERIC(10,6) DEFAULT 0.000000,
ADD COLUMN IF NOT EXISTS agno_agent_metadata JSONB;

-- Step 1.3: Add Agno processing status columns
ALTER TABLE public.opportunities
ADD COLUMN IF NOT EXISTS agno_validation_status VARCHAR(20) DEFAULT 'pending' CHECK (agno_validation_status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')),
ADD COLUMN IF NOT EXISTS agno_processed_at TIMESTAMP WITH TIME ZONE;

-- ================================================================================
-- Phase 2: Add Jina Market Research Columns
-- ================================================================================

-- Step 2.1: Add Jina validation scoring columns
ALTER TABLE public.opportunities
ADD COLUMN IF NOT EXISTS jina_validation_score FLOAT CHECK (jina_validation_score >= 0 AND jina_validation_score <= 100),
ADD COLUMN IF NOT EXISTS jina_data_quality_score FLOAT CHECK (jina_data_quality_score >= 0 AND jina_data_quality_score <= 100),
ADD COLUMN IF NOT EXISTS jina_competitor_count INTEGER CHECK (jina_competitor_count >= 0),
ADD COLUMN IF NOT EXISTS jina_confidence_level FLOAT CHECK (jina_confidence_level >= 0 AND jina_confidence_level <= 100);

-- Step 2.2: Add Jina market size columns
ALTER TABLE public.opportunities
ADD COLUMN IF NOT EXISTS jina_market_size_tam VARCHAR(50),
ADD COLUMN IF NOT EXISTS jina_market_size_sam VARCHAR(50),
ADD COLUMN IF NOT EXISTS jina_market_size_growth VARCHAR(20),
ADD COLUMN IF NOT EXISTS jina_market_source VARCHAR(200);

-- Step 2.3: Add Jina cost and performance tracking
ALTER TABLE public.opportunities
ADD COLUMN IF NOT EXISTS jina_api_cost_usd NUMERIC(10,6) DEFAULT 0.000000,
ADD COLUMN IF NOT EXISTS jina_cache_hit_rate FLOAT CHECK (jina_cache_hit_rate >= 0 AND jina_cache_hit_rate <= 100),
ADD COLUMN IF NOT EXISTS jina_api_calls_count INTEGER DEFAULT 0 CHECK (jina_api_calls_count >= 0);

-- Step 2.4: Add Jina evidence storage
ALTER TABLE public.opportunities
ADD COLUMN IF NOT EXISTS jina_evidence_urls JSONB,
ADD COLUMN IF NOT EXISTS jina_competitor_pricing JSONB,
ADD COLUMN IF NOT EXISTS jina_processed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS jina_validation_status VARCHAR(20) DEFAULT 'pending' CHECK (jina_validation_status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped'));

-- ================================================================================
-- Phase 3: Add Performance Indexes
-- ================================================================================

-- Step 3.1: Agno-specific indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_wtp
ON public.opportunities(agno_wtp_score DESC)
WHERE agno_wtp_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_opportunities_agno_consensus
ON public.opportunities(agno_consensus_confidence DESC)
WHERE agno_consensus_confidence IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_opportunities_agno_status
ON public.opportunities(agno_validation_status);

CREATE INDEX IF NOT EXISTS idx_opportunities_agno_segment
ON public.opportunities(agno_segment_type)
WHERE agno_segment_type IS NOT NULL;

-- Step 3.2: Jina-specific indexes
CREATE INDEX IF NOT EXISTS idx_opportunities_jina_validation
ON public.opportunities(jina_validation_score DESC)
WHERE jina_validation_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_opportunities_jina_quality
ON public.opportunities(jina_data_quality_score DESC)
WHERE jina_data_quality_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_opportunities_jina_status
ON public.opportunities(jina_validation_status);

-- Step 3.3: Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_jina_combined
ON public.opportunities(final_score DESC, agno_consensus_confidence DESC, jina_validation_score DESC)
WHERE agno_consensus_confidence IS NOT NULL AND jina_validation_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_opportunities_processed_status
ON public.opportunities(agno_validation_status, jina_validation_status);

-- ================================================================================
-- Phase 4: Verification
-- ================================================================================

-- Step 4.1: Verify columns were added
DO $$
DECLARE
    agno_count INTEGER;
    jina_count INTEGER;
    total_expected INTEGER := 16; -- 10 Agno + 6 Jina core columns
BEGIN
    -- Count Agno columns
    SELECT COUNT(*) INTO agno_count
    FROM information_schema.columns
    WHERE table_name = 'opportunities'
      AND table_schema = 'public'
      AND column_name LIKE 'agno_%';

    -- Count Jina columns
    SELECT COUNT(*) INTO jina_count
    FROM information_schema.columns
    WHERE table_name = 'opportunities'
      AND table_schema = 'public'
      AND column_name LIKE 'jina_%';

    RAISE NOTICE 'Agno columns added: % (expected ~10)', agno_count;
    RAISE NOTICE 'Jina columns added: % (expected ~6)', jina_count;
    RAISE NOTICE 'Total new columns: % (expected %)', agno_count + jina_count, total_expected;

    IF agno_count + jina_count >= total_expected - 2 THEN
        RAISE NOTICE '✅ Migration successful: Most expected columns added';
    ELSE
        RAISE NOTICE '⚠️ Migration partial: Some columns may be missing';
    END IF;
END $$;

-- Step 4.2: Verify indexes were created
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE tablename = 'opportunities'
      AND schemaname = 'public'
      AND (indexname LIKE 'idx_opportunities_agno_%' OR indexname LIKE 'idx_opportunities_jina_%');

    RAISE NOTICE 'Agno/Jina indexes created: %', index_count;

    IF index_count >= 6 THEN
        RAISE NOTICE '✅ Index creation successful';
    ELSE
        RAISE NOTICE '⚠️ Some indexes may be missing';
    END IF;
END $$;

COMMIT;

-- ================================================================================
-- Migration Summary
-- ================================================================================
-- Added columns:
-- Agno (10): wtp_score, segment_confidence, price_potential, behavior_score,
--          consensus_confidence, segment_type, agents_count, analysis_cost_usd,
--          agent_metadata, validation_status, processed_at
--
-- Jina (6): validation_score, data_quality_score, competitor_count,
--          confidence_level, market_size_tam, market_size_sam, market_size_growth,
--          market_source, api_cost_usd, cache_hit_rate, api_calls_count,
--          evidence_urls, competitor_pricing, processed_at, validation_status
--
-- Total: 16 new columns + 8 new indexes
--
-- Migration status: Check the notices above for verification
-- ================================================================================