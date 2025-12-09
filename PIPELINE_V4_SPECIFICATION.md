# Pipeline V4 Technical Specification

**Project:** RedditHarbor Pipeline V4
**Date:** 2025-12-09
**Purpose:** Clean architecture rebuild based on v3 lessons learned
**Target:** 99% code reduction (119k → 1k lines)
**Complexity Reduction:** 433% bloat → Single-responsibility components

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Component Specifications](#component-specifications)
4. [Database Schema](#database-schema)
5. [Configuration Management](#configuration-management)
6. [Testing Strategy](#testing-strategy)
7. [Migration from V3](#migration-from-v3)
8. [Implementation Checklist](#implementation-checklist)

---

## Executive Summary

### Problem Statement
Pipeline v3 has 119,001 lines of over-engineered code with:
- 3 analyzer backends (all broken)
- 4 embedding providers (unused complexity)
- 3 cost tracking systems (redundant)
- Database port configuration scattered across 10+ files
- 2-day Agno integration with marginal business value

### Solution: V4 Clean Architecture
**One component per responsibility. No alternatives. No factories. No abstraction layers.**

```
Reddit API → LLM Analysis → PostgreSQL
     ↓            ↓              ↓
  Extract     Transform        Load
```

### Success Metrics
- ✅ Extract 100 Reddit submissions
- ✅ Analyze with LLM (OpenRouter/OpenAI/Anthropic)
- ✅ Store in PostgreSQL with deduplication
- ✅ Complete in < 5 minutes
- ✅ < 1,500 lines of code total
- ✅ Zero configuration errors

---

## Architecture Overview

### Directory Structure

```
pipeline-v4/
├── README.md                    # Quick start guide
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Pydantic settings (≤150 lines)
│
├── models/
│   ├── __init__.py
│   ├── reddit.py                # RedditSubmission model (STEAL from v3)
│   └── analysis.py              # AnalysisResult model (STEAL from v3)
│
├── extract/
│   ├── __init__.py
│   └── reddit_client.py         # PRAW wrapper (STEAL from v3)
│
├── transform/
│   ├── __init__.py
│   └── analyzer.py              # Single LLM analyzer (≤200 lines)
│
├── load/
│   ├── __init__.py
│   └── postgres_loader.py       # Direct psycopg2 (≤150 lines)
│
├── core/
│   ├── __init__.py
│   ├── pipeline.py              # Orchestrator (≤300 lines)
│   └── staging.py               # Deduplication (≤150 lines)
│
├── tests/
│   ├── test_reddit_client.py
│   ├── test_analyzer.py
│   ├── test_loader.py
│   └── test_pipeline.py
│
└── main.py                      # CLI entry point (≤100 lines)
```

**Total Target: ~1,200 lines (99% reduction from v3)**

---

## Component Specifications

### 1. Configuration (`config/settings.py`)

**Purpose:** Centralized environment variable management with Pydantic validation

**Source:** Simplified version of `pipeline-v3/config/settings.py`

**Implementation:**

```python
"""
Pipeline V4 Configuration
Centralized settings with environment variable support
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation"""

    # ===== Reddit API =====
    reddit_client_id: str = Field(alias="REDDIT_PUBLIC")
    reddit_client_secret: str = Field(alias="REDDIT_SECRET")
    reddit_user_agent: str = Field(
        default="RedditHarbor Pipeline v4/1.0"
    )

    # ===== Database =====
    database_url: str = Field(
        default="postgresql://postgres:postgres@127.0.0.1:54331/postgres",
        alias="DATABASE_URL"
    )

    # ===== LLM Configuration =====
    llm_api_key: str = Field(alias="OPENROUTER_API_KEY")
    llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="LLM_BASE_URL"
    )
    llm_model: str = Field(
        default="openai/gpt-4o-mini",
        alias="LLM_MODEL"
    )
    llm_max_tokens: int = Field(default=2000)
    llm_temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    # ===== Pipeline Configuration =====
    default_subreddits: list[str] = Field(
        default=["productivity", "tools"]
    )
    default_limit: int = Field(default=10, ge=1, le=1000)
    batch_size: int = Field(default=5, ge=1, le=50)

    # ===== Deduplication =====
    enable_deduplication: bool = Field(default=True)
    checkpoint_interval: int = Field(default=25)

    # ===== Logging =====
    log_level: str = Field(default="INFO")

    model_config = {
        "env_file": ".env.local",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Global singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**Key Decisions:**
- ✅ Keep Pydantic for type safety
- ✅ Single database URL (no port chaos)
- ✅ Generic LLM config (works with any provider)
- ❌ Delete Agno settings
- ❌ Delete embedding provider settings
- ❌ Delete Jina settings

**Lines:** ~150

---

### 2. Data Models (`models/`)

**Purpose:** Type-safe data structures for Reddit data and analysis results

**Source:** Copied directly from `pipeline-v3/models/`

#### `models/reddit.py`

**Action:** COPY AS-IS from v3

```python
"""Reddit data models"""

from datetime import datetime
from pydantic import BaseModel, Field


class RedditSubmission(BaseModel):
    """Reddit submission data"""
    id: str
    subreddit: str
    title: str
    selftext: str
    author: str
    score: int
    num_comments: int
    url: str
    created_utc: datetime
    permalink: str

    # Computed fields
    upvote_ratio: float | None = None
    is_self: bool = True

    class Config:
        frozen = True  # Immutable
```

**Lines:** ~30

#### `models/analysis.py`

**Action:** COPY from v3, REMOVE Agno-specific fields

```python
"""Analysis result models"""

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """LLM analysis result for opportunity scoring"""

    # Identifiers
    submission_id: str
    subreddit: str
    title: str

    # Core scores (0-100)
    wtp_score: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=100)

    # Analysis content
    core_functions: list[str] = Field(default_factory=list)
    pricing_strategy: dict = Field(default_factory=dict)
    target_segment: str = ""
    pain_points: list[str] = Field(default_factory=list)

    # Metadata
    trust_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    analysis_timestamp: str = ""

    class Config:
        frozen = True
```

**Key Changes:**
- ❌ Remove `agno_wtp_score`
- ❌ Remove `agno_agents_count`
- ❌ Remove `agno_analysis_cost_usd`
- ❌ Remove `agno_orchestration_time`
- ✅ Keep core scoring fields

**Lines:** ~40

---

### 3. Reddit Client (`extract/reddit_client.py`)

**Purpose:** Fetch Reddit submissions using PRAW

**Source:** COPY AS-IS from `pipeline-v3/extract/reddit_client.py`

**Action:** Copy entire file unchanged

**Key Features:**
- ✅ Lazy initialization of PRAW client
- ✅ Error handling for API failures
- ✅ Supports hot/top/new sorting
- ✅ Returns typed `RedditSubmission` objects

**Lines:** ~150 (copied from v3)

**File Path:** `pipeline-v3/extract/reddit_client.py` → `pipeline-v4/extract/reddit_client.py`

---

### 4. Analyzer (`transform/analyzer.py`)

**Purpose:** Single LLM analyzer using LiteLLM with native JSON mode

**Implementation:**

```python
"""
LLM-based opportunity analyzer using LiteLLM
Supports OpenAI, Anthropic, OpenRouter, and other providers
"""

import logging
import json
from typing import Any
import litellm
from models.reddit import RedditSubmission
from models.analysis import AnalysisResult
from config.settings import get_settings

logger = logging.getLogger(__name__)


class OpportunityAnalyzer:
    """
    Single LLM analyzer with structured output
    Uses LiteLLM for provider flexibility
    """

    def __init__(self, settings=None):
        """Initialize analyzer with settings"""
        self.settings = settings or get_settings()

        # Configure LiteLLM
        litellm.api_key = self.settings.llm_api_key
        litellm.api_base = self.settings.llm_base_url

        # System prompt for opportunity analysis
        self.system_prompt = """You are an expert product opportunity analyst.
Analyze Reddit submissions to identify SaaS product opportunities.

For each submission, provide:
1. WTP Score (0-100): Willingness-to-pay based on pain severity
2. Final Score (0-100): Overall opportunity score
3. Confidence Score (0-100): Analysis confidence level
4. Core Functions: 3-5 key features the product should have
5. Pricing Strategy: Initial pricing recommendation
6. Target Segment: Primary user persona
7. Pain Points: Key problems mentioned
8. Trust Level: LOW/MEDIUM/HIGH based on post quality

Return valid JSON matching the AnalysisResult schema."""

    def analyze(self, submission: RedditSubmission) -> AnalysisResult:
        """
        Analyze a Reddit submission for product opportunities

        Args:
            submission: Reddit submission to analyze

        Returns:
            Structured analysis result

        Raises:
            RuntimeError: If LLM call fails
        """
        try:
            # Build analysis prompt
            prompt = self._build_prompt(submission)

            # Call LLM with structured output
            response = litellm.completion(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens,
                response_format={"type": "json_object"}  # Force JSON
            )

            # Parse response
            content = response.choices[0].message.content
            result_data = json.loads(content)

            # Add metadata
            result_data["submission_id"] = submission.id
            result_data["subreddit"] = submission.subreddit
            result_data["title"] = submission.title

            # Validate with Pydantic
            return AnalysisResult(**result_data)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from LLM: {e}")
            raise RuntimeError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Analysis failed for {submission.id}: {e}")
            raise RuntimeError(f"Analysis failed: {e}")

    def _build_prompt(self, submission: RedditSubmission) -> str:
        """Build analysis prompt from submission"""
        return f"""Analyze this Reddit post for SaaS product opportunities:

SUBREDDIT: r/{submission.subreddit}
TITLE: {submission.title}
CONTENT: {submission.selftext[:1000]}
ENGAGEMENT: {submission.score} upvotes, {submission.num_comments} comments

Provide a JSON analysis matching this structure:
{{
    "wtp_score": <0-100>,
    "final_score": <0-100>,
    "confidence_score": <0-100>,
    "core_functions": ["feature1", "feature2", ...],
    "pricing_strategy": {{"tier": "...", "price": "..."}},
    "target_segment": "description",
    "pain_points": ["pain1", "pain2", ...],
    "trust_level": "LOW|MEDIUM|HIGH"
}}"""
```

**Key Decisions:**
- ✅ Use LiteLLM (works with any provider)
- ✅ Native JSON mode (no parsing errors)
- ✅ Built-in cost tracking via LiteLLM
- ✅ Single analyzer (no test/production split)
- ❌ No Agno multi-agent
- ❌ No embedding generation
- ❌ No factory pattern

**Lines:** ~120

**Dependencies:**
```txt
litellm>=1.0.0
```

---

### 5. Database Loader (`load/postgres_loader.py`)

**Purpose:** Direct PostgreSQL insertion with connection pooling

**Implementation:**

```python
"""
Direct PostgreSQL loader using psycopg2
No ORM, no abstraction layers
"""

import logging
from typing import Any
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import Json
from models.analysis import AnalysisResult
from config.settings import get_settings

logger = logging.getLogger(__name__)


class PostgresLoader:
    """
    Direct PostgreSQL loader with connection pooling
    """

    def __init__(self, settings=None):
        """Initialize with connection pool"""
        self.settings = settings or get_settings()

        # Create connection pool
        self.pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=self.settings.database_url
        )

        logger.info("✓ PostgreSQL connection pool initialized")

    def save_analysis(self, analysis: AnalysisResult) -> bool:
        """
        Save analysis result to opportunities table

        Args:
            analysis: Analysis result to save

        Returns:
            True if saved, False if duplicate skipped

        Raises:
            RuntimeError: If database operation fails
        """
        conn = None
        try:
            conn = self.pool.getconn()

            with conn.cursor() as cur:
                # Insert or skip on conflict
                cur.execute(
                    """
                    INSERT INTO opportunities (
                        submission_id,
                        subreddit,
                        title,
                        wtp_score,
                        final_score,
                        confidence_score,
                        core_functions,
                        pricing_strategy,
                        target_segment,
                        pain_points,
                        trust_level
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (submission_id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        analysis.submission_id,
                        analysis.subreddit,
                        analysis.title,
                        analysis.wtp_score,
                        analysis.final_score,
                        analysis.confidence_score,
                        Json(analysis.core_functions),
                        Json(analysis.pricing_strategy),
                        analysis.target_segment,
                        Json(analysis.pain_points),
                        analysis.trust_level
                    )
                )

                result = cur.fetchone()
                conn.commit()

                if result:
                    logger.info(f"✓ Saved analysis for {analysis.submission_id}")
                    return True
                else:
                    logger.info(f"⊘ Skipped duplicate {analysis.submission_id}")
                    return False

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to save analysis: {e}")
            raise RuntimeError(f"Database save failed: {e}")
        finally:
            if conn:
                self.pool.putconn(conn)

    def close(self):
        """Close all connections"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connections closed")
```

**Key Decisions:**
- ✅ Direct psycopg2 (no ORM)
- ✅ Connection pooling for performance
- ✅ ON CONFLICT for automatic deduplication
- ✅ JSONB columns for flexible data
- ❌ No OnlyMaps abstraction

**Lines:** ~100

**Dependencies:**
```txt
psycopg2-binary>=2.9.0
```

---

### 6. Staging Layer (`core/staging.py`)

**Purpose:** Deduplication and checkpoint recovery

**Source:** Simplified from `pipeline-v3/staging/`

**Implementation:**

```python
"""
Staging layer for deduplication and checkpointing
Uses local JSON file for state persistence
"""

import json
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)


class StagingLayer:
    """
    Lightweight staging layer for pipeline state
    Tracks processed submissions to avoid duplicates
    """

    def __init__(self, staging_file: str = "pipeline_staging/processed.json"):
        """Initialize staging layer with file path"""
        self.staging_file = Path(staging_file)
        self.processed_ids: Set[str] = set()

        # Load existing state
        self._load_state()

    def is_duplicate(self, submission_id: str) -> bool:
        """Check if submission was already processed"""
        return submission_id in self.processed_ids

    def checkpoint(self, submission_id: str) -> None:
        """Mark submission as processed"""
        self.processed_ids.add(submission_id)
        self._save_state()

    def clear(self) -> None:
        """Clear all staging data"""
        self.processed_ids.clear()
        self._save_state()
        logger.info("Staging state cleared")

    def _load_state(self) -> None:
        """Load state from file"""
        if self.staging_file.exists():
            try:
                with open(self.staging_file, 'r') as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get("processed_ids", []))
                logger.info(f"Loaded {len(self.processed_ids)} processed IDs")
            except Exception as e:
                logger.warning(f"Failed to load staging state: {e}")
                self.processed_ids = set()
        else:
            # Create directory if needed
            self.staging_file.parent.mkdir(parents=True, exist_ok=True)

    def _save_state(self) -> None:
        """Save state to file"""
        try:
            with open(self.staging_file, 'w') as f:
                json.dump({
                    "processed_ids": list(self.processed_ids)
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save staging state: {e}")
```

**Key Decisions:**
- ✅ Simple JSON file for state
- ✅ In-memory set for fast lookups
- ✅ Auto-creates staging directory
- ❌ No complex staging features from v3

**Lines:** ~70

---

### 7. Pipeline Orchestrator (`core/pipeline.py`)

**Purpose:** Coordinate Extract → Transform → Load

**Implementation:**

```python
"""
Pipeline orchestrator
Coordinates Reddit extraction, LLM analysis, and database storage
"""

import logging
import time
from dataclasses import dataclass
from typing import List

from extract.reddit_client import RedditClient
from transform.analyzer import OpportunityAnalyzer
from load.postgres_loader import PostgresLoader
from core.staging import StagingLayer
from models.reddit import RedditSubmission
from models.analysis import AnalysisResult
from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PipelineResults:
    """Pipeline execution results"""
    total_time: float
    submissions_fetched: int
    analyses_completed: int
    analyses_saved: int
    analyses_skipped: int
    errors: int


class Pipeline:
    """
    Simple 3-stage pipeline orchestrator
    Extract → Transform → Load
    """

    def __init__(
        self,
        reddit_client: RedditClient | None = None,
        analyzer: OpportunityAnalyzer | None = None,
        loader: PostgresLoader | None = None,
        staging: StagingLayer | None = None,
        settings = None
    ):
        """Initialize with dependency injection"""
        self.settings = settings or get_settings()

        # Initialize components (or use provided)
        self.reddit = reddit_client or RedditClient()
        self.analyzer = analyzer or OpportunityAnalyzer(self.settings)
        self.loader = loader or PostgresLoader(self.settings)
        self.staging = staging or StagingLayer()

        logger.info("✓ Pipeline initialized")

    def run(
        self,
        subreddits: List[str] | None = None,
        limit: int | None = None
    ) -> PipelineResults:
        """
        Run the complete pipeline

        Args:
            subreddits: List of subreddit names (uses default if None)
            limit: Number of submissions per subreddit (uses default if None)

        Returns:
            Pipeline execution results
        """
        start_time = time.time()

        # Use defaults if not provided
        subreddits = subreddits or self.settings.default_subreddits
        limit = limit or self.settings.default_limit

        logger.info(f"Starting pipeline: {subreddits}, limit={limit}")

        # Counters
        fetched = 0
        analyzed = 0
        saved = 0
        skipped = 0
        errors = 0

        try:
            # STAGE 1: Extract from Reddit
            logger.info("Stage 1: Extracting from Reddit...")
            submissions = self.reddit.fetch_submissions(
                subreddits=subreddits,
                limit=limit,
                sort_by="hot"
            )
            fetched = len(submissions)
            logger.info(f"✓ Extracted {fetched} submissions")

            # STAGE 2: Transform with LLM
            logger.info("Stage 2: Analyzing with LLM...")
            analyses: List[AnalysisResult] = []

            for submission in submissions:
                # Check deduplication
                if self.staging.is_duplicate(submission.id):
                    logger.info(f"⊘ Skipping duplicate: {submission.id}")
                    skipped += 1
                    continue

                try:
                    # Analyze
                    analysis = self.analyzer.analyze(submission)
                    analyses.append(analysis)
                    analyzed += 1

                    # Checkpoint
                    self.staging.checkpoint(submission.id)

                    logger.info(
                        f"✓ Analyzed {submission.id}: "
                        f"WTP={analysis.wtp_score:.1f}, "
                        f"Score={analysis.final_score:.1f}"
                    )

                except Exception as e:
                    logger.error(f"Analysis failed for {submission.id}: {e}")
                    errors += 1

            # STAGE 3: Load to PostgreSQL
            logger.info("Stage 3: Loading to database...")
            for analysis in analyses:
                try:
                    if self.loader.save_analysis(analysis):
                        saved += 1
                except Exception as e:
                    logger.error(f"Save failed for {analysis.submission_id}: {e}")
                    errors += 1

            logger.info(f"✓ Saved {saved} analyses to database")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

        finally:
            total_time = time.time() - start_time

            # Results
            results = PipelineResults(
                total_time=total_time,
                submissions_fetched=fetched,
                analyses_completed=analyzed,
                analyses_saved=saved,
                analyses_skipped=skipped,
                errors=errors
            )

            # Summary
            logger.info("=" * 50)
            logger.info("PIPELINE COMPLETE")
            logger.info(f"Total Time: {total_time:.2f}s")
            logger.info(f"Fetched: {fetched}")
            logger.info(f"Analyzed: {analyzed}")
            logger.info(f"Saved: {saved}")
            logger.info(f"Skipped: {skipped}")
            logger.info(f"Errors: {errors}")
            logger.info("=" * 50)

            return results
```

**Key Decisions:**
- ✅ Simple sequential execution
- ✅ Dependency injection for testing
- ✅ Comprehensive logging
- ✅ Error tracking per stage
- ❌ No complex orchestration from v3

**Lines:** ~180

---

### 8. CLI Entry Point (`main.py`)

**Purpose:** Command-line interface for running pipeline

**Implementation:**

```python
"""
Pipeline V4 CLI
Usage: python main.py [--subreddits r1,r2] [--limit N] [--clear-staging]
"""

import argparse
import logging
import sys
from config.settings import get_settings
from core.pipeline import Pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="RedditHarbor Pipeline V4"
    )

    parser.add_argument(
        '--subreddits',
        type=str,
        help='Comma-separated list of subreddits (e.g., "productivity,tools")'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Number of submissions per subreddit'
    )
    parser.add_argument(
        '--clear-staging',
        action='store_true',
        help='Clear staging state before running'
    )

    args = parser.parse_args()

    try:
        # Initialize pipeline
        settings = get_settings()
        pipeline = Pipeline(settings=settings)

        # Clear staging if requested
        if args.clear_staging:
            pipeline.staging.clear()
            logger.info("Staging state cleared")

        # Parse subreddits
        subreddits = None
        if args.subreddits:
            subreddits = [s.strip() for s in args.subreddits.split(',')]

        # Run pipeline
        results = pipeline.run(
            subreddits=subreddits,
            limit=args.limit
        )

        # Exit code based on success
        if results.errors > 0:
            logger.warning(f"Pipeline completed with {results.errors} errors")
            sys.exit(1)
        else:
            logger.info("Pipeline completed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        pipeline.loader.close()


if __name__ == "__main__":
    main()
```

**Lines:** ~70

---

## Database Schema

### Migration from V3

**File:** `migrations/v4_schema.sql`

```sql
-- Pipeline V4 Database Schema
-- Simplified opportunities table without Agno fields

CREATE TABLE IF NOT EXISTS opportunities (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Reddit identifiers
    submission_id TEXT UNIQUE NOT NULL,
    subreddit TEXT NOT NULL,
    title TEXT NOT NULL,

    -- Core scores (0-100)
    wtp_score DECIMAL(5,2) NOT NULL,
    final_score DECIMAL(5,2) NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL,

    -- Analysis data (JSONB for flexibility)
    core_functions JSONB DEFAULT '[]'::jsonb,
    pricing_strategy JSONB DEFAULT '{}'::jsonb,
    pain_points JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    target_segment TEXT,
    trust_level TEXT DEFAULT 'MEDIUM',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for common queries
    CONSTRAINT valid_scores CHECK (
        wtp_score >= 0 AND wtp_score <= 100 AND
        final_score >= 0 AND final_score <= 100 AND
        confidence_score >= 0 AND confidence_score <= 100
    ),
    CONSTRAINT valid_trust_level CHECK (
        trust_level IN ('LOW', 'MEDIUM', 'HIGH')
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_opportunities_subreddit
    ON opportunities(subreddit);
CREATE INDEX IF NOT EXISTS idx_opportunities_final_score
    ON opportunities(final_score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_created_at
    ON opportunities(created_at DESC);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_opportunities_updated_at
    BEFORE UPDATE ON opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Key Changes from V3:**
- ❌ Removed `agno_wtp_score`
- ❌ Removed `agno_agents_count`
- ❌ Removed `agno_analysis_cost_usd`
- ❌ Removed `agno_orchestration_time`
- ✅ Kept core scoring fields
- ✅ JSONB for flexible nested data
- ✅ Constraints for data validation

---

## Configuration Management

### Environment Variables

**File:** `.env.example`

```bash
# Reddit API Credentials
REDDIT_PUBLIC=your_client_id_here
REDDIT_SECRET=your_client_secret_here

# Database
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54331/postgres

# LLM Configuration (OpenRouter)
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini

# Pipeline Settings
DEFAULT_SUBREDDITS=productivity,tools
DEFAULT_LIMIT=10
BATCH_SIZE=5

# Logging
LOG_LEVEL=INFO
```

### Required Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDDIT_PUBLIC` | ✅ Yes | - | Reddit client ID |
| `REDDIT_SECRET` | ✅ Yes | - | Reddit client secret |
| `OPENROUTER_API_KEY` | ✅ Yes | - | LLM API key |
| `DATABASE_URL` | ⚠️ Optional | `postgresql://...` | PostgreSQL connection string |
| `LLM_MODEL` | ⚠️ Optional | `openai/gpt-4o-mini` | LLM model to use |

---

## Testing Strategy

### Test Structure

```
tests/
├── test_reddit_client.py      # Reddit API integration tests
├── test_analyzer.py            # LLM analyzer tests (with mocking)
├── test_loader.py              # Database loader tests
├── test_staging.py             # Staging layer tests
└── test_pipeline.py            # End-to-end pipeline tests
```

### Test Requirements

**1. Unit Tests (Mocked)**
```python
# tests/test_analyzer.py
def test_analyzer_with_mock_llm():
    """Test analyzer with mocked LLM response"""
    # Mock LiteLLM to avoid API calls
    # Verify prompt construction
    # Verify response parsing
```

**2. Integration Tests (Real APIs)**
```python
# tests/test_pipeline.py
def test_pipeline_end_to_end():
    """Test complete pipeline with 5 submissions"""
    # Use real Reddit API
    # Use real LLM API
    # Use test database
    # Verify results
```

### Pytest Configuration

**File:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
markers =
    unit: Unit tests with mocked dependencies
    integration: Integration tests requiring external APIs
    slow: Slow tests that take >5 seconds
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest -m unit

# Integration tests (requires API keys)
pytest -m integration

# With coverage
pytest --cov=. --cov-report=html
```

---

## Migration from V3

### File Copy Operations

**1. Copy Models (Unchanged)**
```bash
cp pipeline-v3/models/reddit.py pipeline-v4/models/
cp pipeline-v3/models/analysis.py pipeline-v4/models/
```

**2. Copy Reddit Client (Unchanged)**
```bash
cp pipeline-v3/extract/reddit_client.py pipeline-v4/extract/
```

**3. Adapt Settings (Simplified)**
- Source: `pipeline-v3/config/settings.py` (440 lines)
- Target: `pipeline-v4/config/settings.py` (150 lines)
- Action: Remove Agno/Jina/embedding settings

### Database Migration

**Option 1: Fresh Start (Recommended)**
```sql
-- Drop old table
DROP TABLE IF EXISTS opportunities CASCADE;

-- Create v4 schema
\i migrations/v4_schema.sql
```

**Option 2: Preserve Data**
```sql
-- Add v4 columns
ALTER TABLE opportunities
    ALTER COLUMN agno_wtp_score DROP NOT NULL,
    ALTER COLUMN agno_agents_count DROP NOT NULL;

-- Migrate existing data (set defaults)
UPDATE opportunities
SET
    wtp_score = COALESCE(agno_wtp_score, final_score),
    confidence_score = COALESCE(confidence_score, 50.0)
WHERE wtp_score IS NULL;
```

### Deletion Checklist

**Delete These from V3:**
- ❌ `transform/agno_analyzer.py` (1,387 lines)
- ❌ `transform/agno_agents.py`
- ❌ `transform/embedding_providers*.py`
- ❌ `transform/jina_client.py`
- ❌ `transform/market_research_*.py`
- ❌ `load/onlymaps_database.py`
- ❌ All Agno test files

---

## Implementation Checklist

### Phase 1: Setup (30 minutes)

- [ ] Create `pipeline-v4/` directory
- [ ] Copy `requirements.txt` and update dependencies
- [ ] Copy `.env.example`
- [ ] Create directory structure
- [ ] Initialize `__init__.py` files
- [ ] Create `README.md`

### Phase 2: Core Components (2 hours)

- [ ] **Config** (30 min)
  - [ ] Copy and simplify `config/settings.py`
  - [ ] Remove Agno/Jina settings
  - [ ] Test settings load from `.env.local`

- [ ] **Models** (15 min)
  - [ ] Copy `models/reddit.py`
  - [ ] Copy and adapt `models/analysis.py` (remove Agno fields)

- [ ] **Extract** (15 min)
  - [ ] Copy `extract/reddit_client.py`
  - [ ] Test Reddit API connection

- [ ] **Transform** (45 min)
  - [ ] Implement `transform/analyzer.py`
  - [ ] Test LLM call with sample submission
  - [ ] Verify JSON response parsing

- [ ] **Load** (30 min)
  - [ ] Implement `load/postgres_loader.py`
  - [ ] Test database connection
  - [ ] Test INSERT with sample data

### Phase 3: Orchestration (1 hour)

- [ ] **Staging** (20 min)
  - [ ] Implement `core/staging.py`
  - [ ] Test deduplication logic

- [ ] **Pipeline** (40 min)
  - [ ] Implement `core/pipeline.py`
  - [ ] Test with 5 submissions end-to-end

### Phase 4: CLI & Testing (1 hour)

- [ ] **CLI** (20 min)
  - [ ] Implement `main.py`
  - [ ] Test command-line arguments

- [ ] **Tests** (40 min)
  - [ ] Write unit tests for analyzer
  - [ ] Write integration test for pipeline
  - [ ] Run full test suite

### Phase 5: Database Setup (30 minutes)

- [ ] Create `migrations/v4_schema.sql`
- [ ] Run migration on test database
- [ ] Verify schema with sample INSERT
- [ ] Test constraints and indexes

### Phase 6: Documentation (30 minutes)

- [ ] Write `README.md` with quick start
- [ ] Document CLI usage
- [ ] Add architecture diagram
- [ ] Create troubleshooting guide

---

## Success Criteria

### Functional Requirements
- ✅ Fetch 100 Reddit submissions in < 30 seconds
- ✅ Analyze each submission with LLM in < 5 seconds
- ✅ Store results in PostgreSQL with deduplication
- ✅ Handle API failures gracefully (retry/skip)
- ✅ Cost tracking via LiteLLM

### Performance Requirements
- ✅ Process 100 submissions in < 10 minutes
- ✅ Database queries < 100ms
- ✅ Memory usage < 500MB

### Code Quality Requirements
- ✅ Total codebase < 1,500 lines
- ✅ Test coverage > 70%
- ✅ No lint errors (ruff)
- ✅ Type hints on all functions
- ✅ Comprehensive logging

### Operational Requirements
- ✅ Single `.env.local` for all config
- ✅ Zero hardcoded credentials
- ✅ Graceful shutdown (no orphaned connections)
- ✅ Clear error messages

---

## Dependencies

### Python Packages

**File:** `requirements.txt`

```txt
# Core dependencies
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# Reddit API
praw>=7.7.0

# LLM
litellm>=1.0.0

# Database
psycopg2-binary>=2.9.0

# Utilities
python-dateutil>=2.8.0

# Development
pytest>=7.4.0
pytest-cov>=4.1.0
ruff>=0.1.0
```

### System Requirements
- Python 3.11+
- PostgreSQL 14+
- 2GB RAM minimum
- Internet connection (Reddit API, LLM API)

---

## Deployment

### Local Development

```bash
# 1. Clone and setup
git clone <repo>
cd pipeline-v4

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env.local
# Edit .env.local with your credentials

# 5. Setup database
psql -U postgres -f migrations/v4_schema.sql

# 6. Run pipeline
python main.py --subreddits productivity,tools --limit 10
```

### Production Deployment

**Recommended Stack:**
- Docker container with Python 3.11
- Managed PostgreSQL (AWS RDS, Supabase, etc.)
- Environment variables via secrets manager
- Scheduled runs via cron/Airflow

**Docker Example:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```
Error: connection to server at '127.0.0.1', port 54331 failed
```
**Solution:** Check `DATABASE_URL` in `.env.local`, verify PostgreSQL is running

**2. Reddit API Authentication Failed**
```
Error: Failed to initialize Reddit client
```
**Solution:** Verify `REDDIT_PUBLIC` and `REDDIT_SECRET` in `.env.local`

**3. LLM JSON Parsing Error**
```
Error: LLM returned invalid JSON
```
**Solution:** Check `LLM_MODEL` supports JSON mode, verify API key is valid

**4. Deduplication Not Working**
```
Warning: All submissions marked as duplicates
```
**Solution:** Run with `--clear-staging` to reset state

---

## Appendix: V3 vs V4 Comparison

| Aspect | V3 | V4 | Change |
|--------|----|----|--------|
| **Lines of Code** | 119,001 | ~1,200 | -99% |
| **Analyzers** | 3 (test/prod/agno) | 1 (LiteLLM) | -67% |
| **Embedding Providers** | 4 | 0 | -100% |
| **Cost Tracking** | 3 systems | 1 (LiteLLM) | -67% |
| **Database Loaders** | 2 (OnlyMaps + direct) | 1 (psycopg2) | -50% |
| **Config Files** | 440 lines | 150 lines | -66% |
| **Complexity Score** | 433% overhead | 0% overhead | Clean |
| **Setup Time** | Unknown | 4 hours | Fast |
| **Maintenance** | High (13 components) | Low (6 components) | -54% |

---

## Next Steps

1. **Scaffold v4** using this specification
2. **Test with 10 submissions** to validate
3. **Run full pipeline** with 100 submissions
4. **Compare results** with v3 (if any v3 data exists)
5. **Deploy to production**
6. **Archive v3** after successful migration

---

**Document Version:** 1.0
**Last Updated:** 2025-12-09
**Author:** Claude Sonnet 4.5 (Data Engineering Agent)
**Status:** Ready for Implementation
