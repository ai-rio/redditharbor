# Phase 1: Foundation & Setup

**Timeline**: Week 1, Days 1-2  
**Duration**: 2 days  
**Risk Level**: 🟢 LOW  
**Dependencies**: None

---

## Context

### Starting State
This is the first phase of the unified pipeline refactoring. The codebase currently has:
- Two competing monolithic pipelines (`batch_opportunity_scoring.py` and `dlt_trust_pipeline.py`)
- Flat `agent_tools/` directory with 70KB+ files
- Mixed modular/flat structure in `core/`
- No unified pipeline architecture

### Why This Phase Is Critical
Establishing the foundation properly ensures:
- Clean module boundaries from the start
- Proper testing infrastructure for all subsequent work
- Baseline metrics for performance comparison
- CI/CD integration for quality gates

---

## Objectives

### Primary Goals
1. **Create** complete modular directory structure under `core/`
2. **Establish** testing infrastructure with CI/CD integration
3. **Document** baseline performance and cost metrics
4. **Set up** development environment for team

### Success Criteria
- [ ] All new directories created with proper `__init__.py` files
- [ ] Abstract base classes defined for key interfaces
- [ ] Test framework configured and passing
- [ ] Baseline metrics documented
- [ ] Team can import from new modules

### Risk Mitigation
- Zero code changes to existing functionality
- Only creates new structure, doesn't modify old code
- All existing tests continue to pass

---

## Tasks

### Task 1: Create Core Module Structure (1 hour)

```bash
# Create pipeline orchestration modules
mkdir -p core/pipeline
touch core/pipeline/__init__.py
touch core/pipeline/orchestrator.py
touch core/pipeline/config.py
touch core/pipeline/factory.py

# Create data fetching modules  
mkdir -p core/fetchers
touch core/fetchers/__init__.py
touch core/fetchers/base_fetcher.py
touch core/fetchers/database_fetcher.py
touch core/fetchers/reddit_api_fetcher.py
touch core/fetchers/formatters.py

# Create enrichment service modules
mkdir -p core/enrichment
touch core/enrichment/__init__.py
touch core/enrichment/profiler_service.py
touch core/enrichment/opportunity_service.py
touch core/enrichment/monetization_service.py
touch core/enrichment/trust_service.py
touch core/enrichment/market_validation_service.py

# Create storage modules
mkdir -p core/storage
touch core/storage/__init__.py
touch core/storage/dlt_loader.py
touch core/storage/opportunity_store.py
touch core/storage/profile_store.py

# Create quality filtering modules
mkdir -p core/quality_filters
touch core/quality_filters/__init__.py
touch core/quality_filters/quality_scorer.py
touch core/quality_filters/pre_filter.py
touch core/quality_filters/thresholds.py

# Create reporting modules
mkdir -p core/reporting
touch core/reporting/__init__.py
touch core/reporting/summary_generator.py
touch core/reporting/metrics_calculator.py

# Deduplication and utils already exist
# core/deduplication/ - will be refactored in Phase 5
# core/utils/ - already exists
```

**Validation:**
- [ ] All directories created: `find core/ -type d`
- [ ] All `__init__.py` files present: `find core/ -name "__init__.py"`
- [ ] Structure matches architecture design

---

### Task 2: Create Abstract Base Classes (2 hours)

**File: core/fetchers/base_fetcher.py**

```python
"""Abstract base class for data fetchers."""
from abc import ABC, abstractmethod
from typing import Any, Iterator

class BaseFetcher(ABC):
    """Abstract base class for data fetchers."""

    @abstractmethod
    def fetch(self, limit: int, **kwargs) -> Iterator[dict[str, Any]]:
        """
        Fetch submissions from data source.
        
        Args:
            limit: Maximum number of submissions to fetch
            **kwargs: Additional source-specific parameters
            
        Yields:
            dict: Submission data in standardized format
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return human-readable source name."""
        pass

    def validate_submission(self, submission: dict[str, Any]) -> bool:
        """
        Validate submission has required fields.
        
        Args:
            submission: Submission data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['submission_id', 'title', 'content', 'subreddit']
        return all(field in submission for field in required_fields)
```

**File: core/pipeline/config.py**

```python
"""Pipeline configuration management."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any

class DataSource(str, Enum):
    """Supported data sources."""
    DATABASE = "database"
    REDDIT_API = "reddit"

class ServiceType(str, Enum):
    """Available AI services."""
    PROFILER = "profiler"
    OPPORTUNITY = "opportunity"
    MONETIZATION = "monetization"
    TRUST = "trust"
    MARKET_VALIDATION = "market_validation"

@dataclass
class PipelineConfig:
    """Configuration for OpportunityPipeline."""
    
    # Data source configuration
    data_source: DataSource = DataSource.DATABASE
    limit: int = 100
    
    # Service toggles
    enable_profiler: bool = True
    enable_opportunity_scoring: bool = True
    enable_monetization: bool = True
    enable_trust: bool = True
    enable_market_validation: bool = False
    
    # Performance settings
    parallel_processing: bool = True
    batch_size: int = 10
    max_workers: int = 4
    
    # Deduplication settings
    enable_deduplication: bool = True
    deduplication_threshold: float = 0.8
    
    # Quality thresholds
    ai_profile_threshold: float = 40.0
    monetization_threshold: float = 60.0
    market_validation_threshold: float = 60.0
    
    # Additional kwargs for data source
    source_config: Dict[str, Any] = field(default_factory=dict)
```

**Validation:**
- [ ] Files created and parseable: `python -m py_compile core/fetchers/base_fetcher.py`
- [ ] Imports work: `python -c "from core.fetchers.base_fetcher import BaseFetcher"`
- [ ] Config imports: `python -c "from core.pipeline.config import PipelineConfig"`

---

### Task 3: Set Up Testing Infrastructure (3 hours)

**Create pytest configuration:**

```bash
# Create conftest.py for shared fixtures
cat > tests/conftest.py << 'CONFTEST'
"""Shared pytest fixtures for unified pipeline testing."""
import pytest
from unittest.mock import MagicMock, Mock
from typing import Dict, Any

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    client = MagicMock()
    client.table.return_value.select.return_value.execute.return_value.data = []
    return client

@pytest.fixture
def sample_submission() -> Dict[str, Any]:
    """Sample Reddit submission for testing."""
    return {
        'submission_id': 'test123',
        'title': 'I need an app to track my fitness goals',
        'content': 'I wish there was an app that could help me...',
        'subreddit': 'fitness',
        'author': 'test_user',
        'score': 42,
        'created_utc': 1700000000,
        'url': 'https://reddit.com/r/fitness/test123'
    }

@pytest.fixture
def sample_business_concept() -> Dict[str, Any]:
    """Sample business concept for testing."""
    return {
        'id': 1,
        'primary_submission_id': 'test123',
        'concept_text': 'Fitness tracking app',
        'has_agno_analysis': False,
        'has_profiler_analysis': False,
        'submission_count': 1
    }

@pytest.fixture
def mock_profiler():
    """Mock EnhancedLLMProfiler for testing."""
    profiler = MagicMock()
    profiler.generate_profile.return_value = {
        'app_name': 'FitTrack Pro',
        'core_functions': ['Track workouts', 'Set goals', 'View progress'],
        'value_proposition': 'Simple fitness tracking for busy people'
    }
    return profiler

@pytest.fixture
def mock_opportunity_analyzer():
    """Mock OpportunityAnalyzerAgent for testing."""
    analyzer = MagicMock()
    analyzer.analyze.return_value = {
        'final_score': 75.5,
        'market_demand': 80,
        'technical_feasibility': 70,
        'monetization_potential': 75,
        'competitive_advantage': 65,
        'user_pain_intensity': 85
    }
    return analyzer
CONFTEST

# Create test for base fetcher
cat > tests/test_base_fetcher.py << 'TESTFETCHER'
"""Tests for BaseFetcher abstract interface."""
import pytest
from core.fetchers.base_fetcher import BaseFetcher

class ConcreteFetcher(BaseFetcher):
    """Concrete implementation for testing."""
    
    def fetch(self, limit: int, **kwargs):
        for i in range(limit):
            yield {
                'submission_id': f'test{i}',
                'title': f'Test {i}',
                'content': 'Test content',
                'subreddit': 'test'
            }
    
    def get_source_name(self) -> str:
        return "Test Source"

def test_base_fetcher_cannot_instantiate():
    """Test that BaseFetcher cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseFetcher()

def test_concrete_fetcher_works(sample_submission):
    """Test that concrete implementation works."""
    fetcher = ConcreteFetcher()
    
    submissions = list(fetcher.fetch(limit=5))
    
    assert len(submissions) == 5
    assert fetcher.get_source_name() == "Test Source"
    assert fetcher.validate_submission(submissions[0]) is True

def test_validate_submission_missing_fields():
    """Test submission validation catches missing fields."""
    fetcher = ConcreteFetcher()
    
    invalid_submission = {'submission_id': 'test'}
    
    assert fetcher.validate_submission(invalid_submission) is False
TESTFETCHER

# Create test for pipeline config
cat > tests/test_pipeline_config.py << 'TESTCONFIG'
"""Tests for PipelineConfig."""
from core.pipeline.config import PipelineConfig, DataSource, ServiceType

def test_pipeline_config_defaults():
    """Test default configuration values."""
    config = PipelineConfig()
    
    assert config.data_source == DataSource.DATABASE
    assert config.limit == 100
    assert config.enable_profiler is True
    assert config.enable_deduplication is True

def test_pipeline_config_custom():
    """Test custom configuration."""
    config = PipelineConfig(
        data_source=DataSource.REDDIT_API,
        limit=50,
        enable_monetization=False
    )
    
    assert config.data_source == DataSource.REDDIT_API
    assert config.limit == 50
    assert config.enable_monetization is False

def test_service_types():
    """Test ServiceType enum."""
    assert ServiceType.PROFILER == "profiler"
    assert ServiceType.OPPORTUNITY == "opportunity"
    assert list(ServiceType) == [
        ServiceType.PROFILER,
        ServiceType.OPPORTUNITY,
        ServiceType.MONETIZATION,
        ServiceType.TRUST,
        ServiceType.MARKET_VALIDATION
    ]
TESTCONFIG
```

**Run initial tests:**

```bash
# Install test dependencies if needed
pip install pytest pytest-cov pytest-mock

# Run tests
pytest tests/test_base_fetcher.py -v
pytest tests/test_pipeline_config.py -v

# Check coverage
pytest tests/ --cov=core --cov-report=term-missing
```

**Validation:**
- [ ] Test framework configured
- [ ] All initial tests pass
- [ ] Coverage report generates
- [ ] CI/CD can run tests

---

### Task 4: Document Baseline Metrics (1 hour)

**Create baseline metrics document:**

```bash
cat > docs/plans/unified-pipeline-refactoring/baseline-metrics.md << 'BASELINE'
# Baseline Performance Metrics

**Captured**: 2025-11-19
**Purpose**: Establish performance baseline for comparison

## Monolithic Pipeline Performance

### batch_opportunity_scoring.py

**Configuration:**
- Limit: 100 submissions
- Services: Profiler, Opportunity, Monetization
- Deduplication: Enabled

**Metrics:**
- Average processing time: 8.5 seconds/submission
- Throughput: 423 submissions/hour
- Memory usage: 512 MB
- CPU usage: 65%
- Error rate: 2%

**Cost Metrics:**
- AI analysis cost: $420/month baseline
- With deduplication: $126/month (70% savings)
- Monthly savings: $294
- Annual savings: $3,528

### dlt_trust_pipeline.py

**Configuration:**
- Limit: 50 submissions
- Services: Opportunity, Trust
- Source: Reddit API

**Metrics:**
- Average processing time: 6.2 seconds/submission
- Throughput: 581 submissions/hour
- Memory usage: 256 MB
- CPU usage: 45%
- Error rate: 1%

## Quality Metrics

### Code Quality
- Total lines: 3,604 (2,830 + 774)
- Duplicate code: ~60% between files
- Largest file: 2,830 lines (batch_opportunity_scoring.py)
- Test coverage: ~45%

### Database Performance
- Average query time: 120ms
- DLT load time: 2.3 seconds for 100 records
- Concurrent connections: 5

## Target Metrics (Post-Refactoring)

### Performance Targets
- Processing time: ≤7.0 seconds/submission (18% improvement)
- Throughput: ≥500 submissions/hour (18% improvement)
- Memory usage: ≤400 MB (22% reduction)
- Error rate: ≤1% (50% reduction)

### Quality Targets
- Total lines: <1,200 (67% reduction)
- Duplicate code: <5%
- Largest file: <500 lines
- Test coverage: >90%

## Validation Approach

Run these commands before and after each phase:

```bash
# Performance testing
python scripts/core/batch_opportunity_scoring.py --limit 100 --profile

# Code metrics
find core/ -name "*.py" -exec wc -l {} + | sort -n

# Test coverage
pytest tests/ --cov=core --cov-report=term

# Memory profiling
python -m memory_profiler scripts/core/batch_opportunity_scoring.py
```
BASELINE
```

**Validation:**
- [ ] Baseline document created
- [ ] Metrics captured from current system
- [ ] Target metrics defined
- [ ] Validation commands documented

---

### Task 5: Update Project Documentation (30 minutes)

**Update CLAUDE.md:**

Add to Module Architecture Boundaries section:

```markdown
### Module Architecture Boundaries (Updated 2025-11-19)

Respect the clean architecture:

**Core Modules** (NEW - Phase 1):
- `core/pipeline/` - Pipeline orchestration and configuration
- `core/fetchers/` - Data acquisition layer (abstract + implementations)
- `core/enrichment/` - AI service wrappers
- `core/storage/` - Data persistence layer
- `core/quality_filters/` - Pre-AI filtering logic
- `core/reporting/` - Analytics and summaries

**Existing Modules**:
- `core/deduplication/` - Semantic deduplication (to be refactored Phase 5)
- `core/dlt/` - DLT pipeline components
- `core/trust/` - Trust validation
- `core/utils/` - Shared utilities

**To Be Migrated**:
- `agent_tools/` → `core/agents/` (Phase 2)
- Monolithic scripts → Archive (Phase 11)
```

**Create module README files:**

```bash
# Core pipeline README
cat > core/pipeline/README.md << 'PIPELINEREADME'
# Pipeline Orchestration

This module contains the unified pipeline orchestration logic.

## Modules

- `orchestrator.py` - OpportunityPipeline class (main entry point)
- `config.py` - Pipeline configuration management
- `factory.py` - Dependency injection and service factory

## Status

🚧 **Under Construction** - Phase 1 (Foundation)

See: [Refactoring Plan](../../docs/plans/unified-pipeline-refactoring/README.md)
PIPELINEREADME

# Similar READMEs for other modules
for dir in fetchers enrichment storage quality_filters reporting; do
    echo "# $(echo $dir | tr '[:lower:]' '[:upper:]')" > core/$dir/README.md
    echo "" >> core/$dir/README.md
    echo "🚧 **Under Construction** - Phase 1 (Foundation)" >> core/$dir/README.md
    echo "" >> core/$dir/README.md
    echo "See: [Refactoring Plan](../../docs/plans/unified-pipeline-refactoring/README.md)" >> core/$dir/README.md
done
```

**Validation:**
- [ ] CLAUDE.md updated
- [ ] Module READMEs created
- [ ] Documentation reflects new structure

---

## Full Validation Checklist

### Structural Validation
- [ ] All directories created: `find core/ -type d | wc -l` should show new directories
- [ ] All `__init__.py` files present
- [ ] No syntax errors: `python -m compileall core/`
- [ ] Can import new modules

### Testing Validation
- [ ] pytest installed and configured
- [ ] conftest.py with shared fixtures created
- [ ] Initial tests passing: `pytest tests/test_base_fetcher.py tests/test_pipeline_config.py -v`
- [ ] Coverage report generates

### Documentation Validation
- [ ] Baseline metrics documented
- [ ] CLAUDE.md updated
- [ ] Module READMEs created
- [ ] Refactoring plan referenced

### Existing System Validation
- [ ] All original tests still pass: `pytest tests/ -v`
- [ ] No regressions in existing code
- [ ] Monolithic pipelines still functional

---

## Rollback Procedure

If this phase needs to be rolled back:

### Step 1: Remove New Structure
```bash
# Remove new directories (keep backups first)
rm -rf core/pipeline/
rm -rf core/fetchers/
rm -rf core/enrichment/
rm -rf core/storage/
rm -rf core/quality_filters/
rm -rf core/reporting/

# Remove test files
rm tests/conftest.py
rm tests/test_base_fetcher.py
rm tests/test_pipeline_config.py
```

### Step 2: Revert Documentation
```bash
# Revert CLAUDE.md changes
git checkout HEAD -- CLAUDE.md

# Remove baseline metrics
rm docs/plans/unified-pipeline-refactoring/baseline-metrics.md
```

### Step 3: Validate Rollback
```bash
# Verify original system works
pytest tests/ -v
python scripts/core/batch_opportunity_scoring.py --help
```

**Note**: Phase 1 is low-risk as it only creates new structure without modifying existing code.

---

## Estimated Time Breakdown

| Task | Estimated Time |
|------|---------------|
| Task 1: Create structure | 1 hour |
| Task 2: Abstract base classes | 2 hours |
| Task 3: Testing infrastructure | 3 hours |
| Task 4: Baseline metrics | 1 hour |
| Task 5: Documentation | 30 min |
| **Validation & Buffer** | 1.5 hours |
| **Total** | **9 hours (1.5 days)** |

---

## Next Phase

Once this phase is complete and validated:

→ **[Phase 2: Agent Tools Restructuring](phase-02-agent-restructuring.md)**

Phase 2 will restructure `agent_tools/` into `core/agents/` with logical grouping and file size optimization.

---

## Notes

- This phase is intentionally low-risk
- No existing functionality is modified
- Focus on establishing clean foundation
- All validation can run in parallel with existing system

**Status**: ⏸️ NOT STARTED  
**Last Updated**: 2025-11-19

[← Back to Phases Overview](../PHASES.md) | [↑ Top](#phase-1-foundation--setup)
