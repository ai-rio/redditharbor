# Agno Integration: Environment Setup Guide

**Status**: Configuration Documentation
**Target**: Pipeline v3 Transform Layer
**Prerequisites**: Python 3.10+, UV package manager, Supabase instance

---

## Overview

This guide covers the complete environment setup for integrating Agno's multi-agent system into RedditHarbor Pipeline v3. Follow these steps to configure dependencies, API keys, and environment variables for production deployment.

---

## ⚠️ Critical: UV and Virtual Environment Standards

**RedditHarbor Project Standards:**
1. ✅ **Use UV** as the package manager (NOT pip)
2. ✅ **Always activate `.venv`** before working (`source .venv/bin/activate`)
3. ✅ **Run `uv sync`** after pulling changes to sync dependencies
4. ❌ **Never use `pip install`** directly (use UV instead)

**Why this matters:**
- UV provides faster, deterministic dependency resolution
- Virtual environment isolation prevents dependency conflicts
- Ensures consistent Python environment across all developers
- Required for proper testing and production deployment

**Quick Start:**
```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/
uv sync                      # Install/sync all dependencies
source .venv/bin/activate    # Activate virtual environment
# You're ready to code!
```

---

## 1. Prerequisites Validation

### 1.1 System Requirements

**Python Environment**:
```bash
# Verify Python version (3.10+ required)
python --version
# Expected: Python 3.10.x or higher

# Verify UV package manager
uv --version
# Expected: uv x.x.x or install with: curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Database Requirements**:
```bash
# Verify Supabase CLI
supabase --version
# Expected: 1.x.x or higher

# Start local Supabase instance
supabase start
# Expected: Started supabase local development setup.
```

**Git Repository**:
```bash
# Verify in correct directory
pwd
# Expected: /home/carlos/projects/redditharbor-core-functions-fix

# Verify on correct branch
git branch --show-current
# Expected: feature/ai-quality-validation or create new branch
```

### 1.2 Pipeline v3 Installation Status

```bash
# Verify Pipeline v3 exists
ls pipeline-v3/
# Expected: extract/, transform/, load/, tests/, docs/

# Verify existing analyzers
ls pipeline-v3/transform/
# Expected: analyzer.py, litellm_analyzer.py, analyzer_factory.py
```

---

## 2. Dependency Installation

### 2.1 Agno Framework Dependencies

**Add to `pipeline-v3/requirements.txt`**:
```txt
# Existing dependencies (keep)
praw>=7.7.0
pydantic>=2.0.0
instructor>=0.4.0
litellm>=1.0.0
openai>=1.0.0
anthropic>=0.3.0
pgvector>=0.2.0
sqlalchemy>=2.0.0
agentops>=0.2.0

# NEW: Agno multi-agent framework
agno>=0.3.0
agno-core>=0.3.0

# NEW: Jina API integration (optional, for Market Research Agent)
jina>=3.20.0
requests>=2.31.0

# NEW: Enhanced NLP for PII anonymization
spacy>=3.7.0
en-core-web-lg>=3.7.0  # Download separately
```

### 2.2 Install Dependencies with UV

**⚠️ IMPORTANT: RedditHarbor uses UV as the standard package manager**

UV provides faster, more reliable dependency resolution and automatically manages virtual environments to prevent conflicts.

```bash
# Navigate to project root (not pipeline-v3/)
cd /home/carlos/projects/redditharbor-core-functions-fix/

# Install/sync all dependencies with UV
uv sync

# Expected output:
# Using Python 3.10.x
# Creating virtualenv at .venv
# Resolved X packages in Yms
# Installed agno vX.X.X
# Installed agno-core vX.X.X
# ...

# Activate the virtual environment to prevent dependency conflicts
source .venv/bin/activate

# Your prompt should now show: (.venv) user@host:~$
```

**Why activate `.venv`?**
- ✅ Isolates project dependencies from system Python
- ✅ Prevents conflicts between RedditHarbor and other projects
- ✅ Ensures consistent Python environment across team members
- ✅ Required for running tests and scripts

**Verify installation:**
```bash
# (with .venv activated)
python -c "import agno; print(agno.__version__)"
# Expected: 0.3.0 or higher

# Verify virtual environment is active
which python
# Expected: /home/carlos/projects/redditharbor-core-functions-fix/.venv/bin/python
```

**Best Practice Workflow:**
```bash
# 1. Always activate .venv before working
source .venv/bin/activate

# 2. Run your code/tests
pytest tests/
python -m pipeline_v3.main

# 3. Deactivate when done (optional)
deactivate
```

### 2.3 Download spaCy Language Model

```bash
# Ensure .venv is activated
source .venv/bin/activate

# Download English language model for PII detection
python -m spacy download en_core_web_lg

# Verify installation
python -c "import spacy; nlp = spacy.load('en_core_web_lg'); print('spaCy loaded successfully')"
# Expected: spaCy loaded successfully
```

### 2.4 Optional: Jina API Client Setup

**Note:** Jina should already be installed via `uv sync` if listed in `requirements.txt`

```bash
# Ensure .venv is activated
source .venv/bin/activate

# Verify Jina client (should already be installed)
python -c "import jina; print(jina.__version__)"
# Expected: 3.20.0 or higher

# If not installed, add to requirements.txt and re-sync:
# echo "jina>=3.20.0" >> requirements.txt
# uv sync
```

---

## 3. API Key Configuration

### 3.1 Required API Keys

| Service | Purpose | Required | Cost |
|---------|---------|----------|------|
| **OpenRouter** | LLM inference (Agno agents) | Yes | ~$0.004/analysis |
| **AgentOps** | Agent monitoring & tracking | Yes | Free tier available |
| **Reddit API** | Data collection | Yes | Free |
| **Jina API** | Market research validation | Optional | ~$0.002/query |
| **Supabase** | Database storage | Yes | Free tier available |

### 3.2 Obtain API Keys

#### OpenRouter API Key
1. Visit https://openrouter.ai/
2. Sign up for account
3. Navigate to "API Keys" section
4. Create new API key with name "RedditHarbor-Pipeline-v3"
5. Copy API key (starts with `sk-or-v1-...`)

**Recommended Models**:
- `anthropic/claude-haiku-4.5` (Fastest, cost-effective)
- `anthropic/claude-sonnet-3.5` (Balanced quality/cost)
- `openai/gpt-4o-mini` (Alternative option)

**Cost Comparison**:
```
Claude Haiku 4.5:  $0.25/1M input tokens, $1.25/1M output
Claude Sonnet 3.5: $3.00/1M input tokens, $15.00/1M output
GPT-4o Mini:       $0.15/1M input tokens, $0.60/1M output

Average analysis: ~3,000 tokens (input) + 800 tokens (output)
Haiku cost: ~$0.001/analysis
Sonnet cost: ~$0.012/analysis
GPT-4o Mini: ~$0.0009/analysis
```

#### AgentOps API Key
1. Visit https://www.agentops.ai/
2. Sign up for account
3. Navigate to "Settings" → "API Keys"
4. Create new API key
5. Copy API key

#### Jina API Key (Optional)
1. Visit https://jina.ai/reader/
2. Sign up for account
3. Navigate to API settings
4. Generate new API key
5. Copy API key (starts with `jina_...`)

**Jina API Pricing**:
- Search API: $0.0001 per query (5 results)
- Reader API: $0.0002 per URL extraction
- Free tier: 1,000 requests/month

### 3.3 Environment Variable Configuration

**✅ EXISTING CONFIGURATION DETECTED**

Your project already has a comprehensive `.env.local` file at the project root with all required Agno and Jina configuration:

**File location**: `/home/carlos/projects/redditharbor-core-functions-fix/.env.local`

**Already configured variables:**
```bash
# ✅ Agno Integration (Lines 81-84)
AGNO_ANALYZER_ENABLED=true
AGNO_ORCHESTRATION_MODE=sequential  # Change to 'parallel' for better performance
AGNO_CONSENSUS_THRESHOLD=60.0

# ✅ AgentOps Monitoring (Lines 71-75)
AGENTOPS_API_KEY=c79b4416-4f0d-41fd-a7db-d40a57e1a1d6
AGENTOPS_AUTO_INSTRUMENT_OPENAI=false

# ✅ OpenRouter LLM (Lines 23, 43)
OPENROUTER_API_KEY=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
MONETIZATION_LLM_MODEL=meta-llama/llama-3.1-8b-instruct:floor

# ✅ Jina API (Lines 92-103)
JINA_API_KEY=jina_cdf8fca7214d4fde905401839b8d93f7GUgKuLpDzrrnTF-MKvGxorA8JOtt
MARKET_VALIDATION_ENABLED=true
MARKET_VALIDATION_MIN_COMPETITORS=2
MARKET_VALIDATION_MAX_SEARCHES=5

# ✅ Reddit API (Lines 8-11)
REDDIT_PUBLIC=jEAmLlbzr0TvxbR1W0ziBQ
REDDIT_SECRET=g2r7vhtAB_kEmCeGcXXEM_KIzDh8iQ

# ✅ Supabase (Lines 16-18)
SUPABASE_URL=http://127.0.0.1:54330
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

**🎯 NO ACTION REQUIRED** - Your `.env.local` is already configured for Agno integration!

**Optional optimizations** (edit `.env.local` if desired):
```bash
# For better performance (line 83):
AGNO_ORCHESTRATION_MODE=parallel  # Change from 'sequential' to 'parallel'

# For production-grade model (line 43):
MONETIZATION_LLM_MODEL=anthropic/claude-haiku-4.5  # Upgrade from Llama for better quality

# ============================================================
# COST & PERFORMANCE LIMITS
# ============================================================

# Cost Controls
DAILY_COST_LIMIT_USD=50.00
COST_PER_ANALYSIS_LIMIT_USD=0.01
ALERT_COST_THRESHOLD_USD=40.00

# Performance Controls
MAX_ANALYSIS_LATENCY_SECONDS=10
BATCH_SIZE=25
MAX_CONCURRENT_ANALYSES=4

# Quality Controls
MIN_CONFIDENCE_SCORE=50.0
MIN_FINAL_SCORE=30.0
```

**Secure the environment file**:
```bash
# Set restrictive permissions
chmod 600 pipeline-v3/.env.local

# Verify not tracked by Git
cat .gitignore | grep ".env.local"
# Expected: .env.local (should be ignored)

# Add to .gitignore if missing
echo ".env.local" >> .gitignore
```

---

## 4. Configuration Validation

### 4.1 Verify Environment Variables

**Create validation script `pipeline-v3/scripts/validate-agno-config.py`**:
```python
#!/usr/bin/env python3
"""
Validate Agno integration configuration

Usage:
    python scripts/validate-agno-config.py
"""

import os
import sys
from pathlib import Path

# Add pipeline-v3 to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def validate_environment():
    """Validate all required environment variables"""

    required_vars = {
        "OPENROUTER_API_KEY": "OpenRouter API key for LLM inference",
        "MONETIZATION_LLM_MODEL": "Model name (e.g., anthropic/claude-haiku-4.5)",
        "AGENTOPS_API_KEY": "AgentOps API key for monitoring",
        "REDDIT_CLIENT_ID": "Reddit API client ID",
        "REDDIT_CLIENT_SECRET": "Reddit API client secret",
        "SUPABASE_URL": "Supabase instance URL",
        "SUPABASE_KEY": "Supabase anonymous key"
    }

    optional_vars = {
        "JINA_API_KEY": "Jina API key for market research (optional)",
        "AGNO_ORCHESTRATION_MODE": "Agent orchestration mode (default: parallel)",
        "AGNO_CONSENSUS_THRESHOLD": "Consensus confidence threshold (default: 60.0)"
    }

    print("=" * 60)
    print("AGNO CONFIGURATION VALIDATION")
    print("=" * 60)

    # Check required variables
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                display = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display = value
            print(f"✓ {var}: {display}")
        else:
            print(f"✗ {var}: MISSING - {description}")
            missing_required.append(var)

    print()

    # Check optional variables
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {value}")
        else:
            print(f"○ {var}: Not set (optional) - {description}")

    print()

    # Validation result
    if missing_required:
        print("❌ VALIDATION FAILED")
        print(f"   Missing required variables: {', '.join(missing_required)}")
        print("\n   Please set these in pipeline-v3/.env.local")
        return False
    else:
        print("✅ VALIDATION PASSED")
        print("   All required environment variables are set")
        return True

def test_api_connectivity():
    """Test API connectivity for all services"""

    print("\n" + "=" * 60)
    print("API CONNECTIVITY TESTS")
    print("=" * 60)

    # Test OpenRouter
    try:
        import openai
        client = openai.OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        )
        response = client.chat.completions.create(
            model=os.getenv("MONETIZATION_LLM_MODEL", "anthropic/claude-haiku-4.5"),
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=10
        )
        print("✓ OpenRouter API: Connected")
    except Exception as e:
        print(f"✗ OpenRouter API: Failed - {e}")

    # Test AgentOps
    try:
        import agentops
        agentops.init(api_key=os.getenv("AGENTOPS_API_KEY"))
        print("✓ AgentOps API: Connected")
    except Exception as e:
        print(f"✗ AgentOps API: Failed - {e}")

    # Test Supabase
    try:
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        # Simple query test
        result = supabase.table("opportunities").select("id").limit(1).execute()
        print("✓ Supabase Database: Connected")
    except Exception as e:
        print(f"✗ Supabase Database: Failed - {e}")

    # Test Jina (optional)
    if os.getenv("JINA_API_KEY"):
        try:
            import requests
            response = requests.get(
                "https://r.jina.ai/https://example.com",
                headers={"Authorization": f"Bearer {os.getenv('JINA_API_KEY')}"},
                timeout=5
            )
            print("✓ Jina API: Connected")
        except Exception as e:
            print(f"✗ Jina API: Failed - {e}")

def test_agno_import():
    """Test Agno framework import"""

    print("\n" + "=" * 60)
    print("DEPENDENCY VALIDATION")
    print("=" * 60)

    # Test Agno import
    try:
        import agno
        print(f"✓ Agno Framework: v{agno.__version__}")
    except ImportError as e:
        print(f"✗ Agno Framework: Not installed - {e}")
        return False

    # Test spaCy
    try:
        import spacy
        nlp = spacy.load("en_core_web_lg")
        print(f"✓ spaCy NLP: v{spacy.__version__} (en_core_web_lg loaded)")
    except Exception as e:
        print(f"✗ spaCy NLP: Failed - {e}")

    # Test LiteLLM
    try:
        import litellm
        print(f"✓ LiteLLM: v{litellm.__version__}")
    except ImportError as e:
        print(f"✗ LiteLLM: Not installed - {e}")

    # Test AgentOps
    try:
        import agentops
        print(f"✓ AgentOps: v{agentops.__version__}")
    except ImportError as e:
        print(f"✗ AgentOps: Not installed - {e}")

    return True

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv("pipeline-v3/.env.local")

    # Run validations
    env_valid = validate_environment()
    deps_valid = test_agno_import()

    if env_valid and deps_valid:
        test_api_connectivity()
        print("\n" + "=" * 60)
        print("✅ AGNO SETUP COMPLETE")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ SETUP INCOMPLETE - Please fix errors above")
        print("=" * 60)
        sys.exit(1)
```

**Run validation**:
```bash
# Make script executable
chmod +x pipeline-v3/scripts/validate-agno-config.py

# Run validation
python pipeline-v3/scripts/validate-agno-config.py

# Expected output:
# ============================================================
# AGNO CONFIGURATION VALIDATION
# ============================================================
# ✓ OPENROUTER_API_KEY: sk-or-v1...
# ✓ MONETIZATION_LLM_MODEL: anthropic/claude-haiku-4.5
# ...
# ✅ VALIDATION PASSED
```

---

## 5. Database Schema Setup

### 5.1 Apply Agno Schema Migrations

**Create migration file `pipeline-v3/migrations/add-agno-columns.sql`**:
```sql
-- ============================================================
-- Agno Multi-Agent Integration Schema Extensions
-- ============================================================
-- Description: Add columns for Agno multi-agent analysis results
-- Version: 1.0
-- Date: 2025-12-03

BEGIN;

-- Phase 1: Add Agno multi-agent score columns
ALTER TABLE opportunities
  ADD COLUMN IF NOT EXISTS agno_wtp_score FLOAT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS agno_segment_confidence FLOAT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS agno_price_potential FLOAT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS agno_behavior_score FLOAT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS agno_consensus_confidence FLOAT DEFAULT NULL;

-- Add indexes for Agno scores
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_wtp
  ON opportunities(agno_wtp_score);
CREATE INDEX IF NOT EXISTS idx_opportunities_agno_consensus
  ON opportunities(agno_consensus_confidence);

-- Phase 2: Add Jina market research columns (optional, for Phase 6)
ALTER TABLE opportunities
  ADD COLUMN IF NOT EXISTS jina_validation_score FLOAT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS jina_data_quality_score FLOAT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS jina_competitor_count INT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS jina_market_size_tam VARCHAR(50) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS jina_market_size_growth VARCHAR(20) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS jina_evidence_urls JSONB DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS jina_api_cost_usd NUMERIC(10,6) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS jina_cache_hit_rate FLOAT DEFAULT NULL;

-- Add indexes for Jina metrics
CREATE INDEX IF NOT EXISTS idx_opportunities_jina_validation
  ON opportunities(jina_validation_score);

-- Add comments for documentation
COMMENT ON COLUMN opportunities.agno_wtp_score IS
  'Willingness to Pay score from WTP Agent (0-100)';
COMMENT ON COLUMN opportunities.agno_segment_confidence IS
  'Market Segment classification confidence from Segment Agent (0-100)';
COMMENT ON COLUMN opportunities.agno_price_potential IS
  'Revenue potential score from Price Agent (0-100)';
COMMENT ON COLUMN opportunities.agno_behavior_score IS
  'Payment behavior analysis score from Behavior Agent (0-100)';
COMMENT ON COLUMN opportunities.agno_consensus_confidence IS
  'Multi-agent consensus confidence score (0-100)';

COMMIT;
```

**Apply migration**:
```bash
# Using Supabase CLI
supabase db push --file pipeline-v3/migrations/add-agno-columns.sql

# Or using psql directly
psql $DATABASE_URL -f pipeline-v3/migrations/add-agno-columns.sql

# Verify columns added
psql $DATABASE_URL -c "\d opportunities" | grep agno
# Expected:
# agno_wtp_score           | double precision |
# agno_segment_confidence  | double precision |
# agno_price_potential     | double precision |
# agno_behavior_score      | double precision |
# agno_consensus_confidence| double precision |
```

---

## 6. Testing Configuration

### 6.1 Run Configuration Tests

```bash
# Test basic Agno import
python -c "from pipeline_v3.transform.agno_analyzer import AgnoOpportunityAnalyzer; print('✓ Agno analyzer imported')"

# Test factory integration
python -c "from pipeline_v3.transform.analyzer_factory import get_analyzer; a = get_analyzer('agno'); print('✓ Agno analyzer created')"

# Run unit tests
cd pipeline-v3/
pytest tests/transform/test_agno_analyzer.py -v

# Expected:
# tests/transform/test_agno_analyzer.py::test_agno_initialization PASSED
# tests/transform/test_agno_analyzer.py::test_analyze_submission PASSED
# ...
```

### 6.2 Test End-to-End Analysis

```bash
# Run single analysis test
python -m pipeline_v3 \
  --analyzer-type agno \
  --limit 1 \
  --subreddits SaaS \
  --test-mode

# Expected output:
# [INFO] Initialized AgnoOpportunityAnalyzer
# [INFO] Analyzing submission: "..."
# [INFO] WTP Agent score: 75.2
# [INFO] Segment Agent confidence: 82.5
# [INFO] Price Agent potential: 68.9
# [INFO] Behavior Agent score: 71.3
# [INFO] Consensus confidence: 74.5
# [INFO] Analysis complete - Final score: 72.1
```

---

## 7. Production Deployment Checklist

### 7.1 Pre-Production Validation

- [ ] All dependencies installed via UV
- [ ] Environment variables configured in `.env.local`
- [ ] API keys validated and tested
- [ ] Database migrations applied successfully
- [ ] Configuration validation script passes
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] End-to-end test successful

### 7.2 Security Checklist

- [ ] `.env.local` has restrictive permissions (600)
- [ ] Environment file not tracked in Git
- [ ] API keys rotated from defaults
- [ ] Cost limits configured
- [ ] Alert thresholds set
- [ ] Monitoring enabled

### 7.3 Performance Checklist

- [ ] Orchestration mode configured (parallel recommended)
- [ ] Batch size optimized (default: 25)
- [ ] Concurrent analysis limit set (default: 4)
- [ ] Timeout limits configured
- [ ] AgentOps monitoring active

---

## 8. Troubleshooting

### 8.1 Common Issues

**Issue**: `ImportError: No module named 'agno'`
```bash
# Solution: Reinstall dependencies
cd pipeline-v3/
uv sync --force
python -c "import agno; print(agno.__version__)"
```

**Issue**: `OpenRouter API authentication failed`
```bash
# Solution: Verify API key format
echo $OPENROUTER_API_KEY
# Should start with: sk-or-v1-

# Test API key
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

**Issue**: `spaCy model 'en_core_web_lg' not found`
```bash
# Solution: Download language model
python -m spacy download en_core_web_lg
python -m spacy validate
```

**Issue**: `Database migration failed`
```bash
# Solution: Check database connection
psql $DATABASE_URL -c "SELECT version();"

# Manually verify table exists
psql $DATABASE_URL -c "\dt opportunities"

# Retry migration
supabase db reset
supabase db push
```

### 8.2 Getting Help

**Documentation**:
- Architecture: `/pipeline-v3/docs/AGNO_INTEGRATION_ARCHITECTURE.md`
- Cost Optimization: `/pipeline-v3/docs/agno-integration/configuration/cost-optimization.md`
- Production Testing: `/pipeline-v3/docs/agno-integration/implementation/phase-5-production-testing.md`

**Support Channels**:
- GitHub Issues: https://github.com/yourusername/redditharbor/issues
- Agno Framework: https://github.com/agno-agi/agno
- LiteLLM Docs: https://docs.litellm.ai/

---

## 9. Next Steps

After completing environment setup:

1. **Review Architecture**: Read `AGNO_INTEGRATION_ARCHITECTURE.md`
2. **Understand Cost Model**: Review `cost-optimization.md`
3. **Run Tests**: Execute Phase 1-4 test suites
4. **Production Testing**: Follow `phase-5-production-testing.md`
5. **Deploy**: Use gradual rollout strategy (5% → 25% → 50% → 100%)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-03
**Status**: Configuration Guide
**Related Documents**:
- `/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/docs/AGNO_INTEGRATION_ARCHITECTURE.md`
- `/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/docs/agno-integration/configuration/cost-optimization.md`
- `/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/docs/agno-integration/implementation/phase-5-production-testing.md`
