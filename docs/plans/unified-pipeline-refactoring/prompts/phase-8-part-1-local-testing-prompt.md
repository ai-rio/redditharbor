# Phase 8 Part 1: OpportunityPipeline Orchestrator - Local AI Testing

**Context**: Testing OpportunityPipeline orchestrator that unifies both monolithic pipelines.

**Files Created**:
- `core/pipeline/orchestrator.py` (480 lines) - OpportunityPipeline class
- `core/pipeline/__init__.py` - Module exports
- `tests/test_orchestrator.py` (640 lines, 18 tests)

**Dependencies**: Phase 7 complete (storage services), Phase 6 complete (enrichment services)

---

## Testing Instructions

### Step 1: Run Unit Tests
```bash
pytest tests/test_orchestrator.py -v
```

**Expected**: 18 tests pass with mocked dependencies

### Step 2: Review Code Quality
```bash
ruff check core/pipeline/orchestrator.py tests/test_orchestrator.py
ruff format core/pipeline/orchestrator.py tests/test_orchestrator.py
```

**Expected**: No linting errors, proper formatting

### Step 3: Test Import and Basic Initialization
```bash
python3 -c "
from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource
config = PipelineConfig(data_source=DataSource.DATABASE, limit=10)
pipeline = OpportunityPipeline(config)
print(f'✓ Pipeline initialized with {len(pipeline.services)} services')
print(f'✓ Stats: {pipeline.stats}')
"
```

**Expected**: Pipeline initializes successfully

### Step 4: Integration Test with Mock Data
Create `scripts/testing/test_orchestrator_integration.py`:

```python
from unittest.mock import MagicMock
from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource

# Mock Supabase client
mock_client = MagicMock()

# Create config
config = PipelineConfig(
    data_source=DataSource.DATABASE,
    supabase_client=mock_client,
    limit=5,
    enable_profiler=False,
    enable_opportunity_scoring=False,
    dry_run=True,
)

# Create pipeline
pipeline = OpportunityPipeline(config)

# Mock fetcher to return test data
from unittest.mock import patch
mock_fetcher = MagicMock()
mock_fetcher.fetch.return_value = iter([
    {
        "submission_id": "test1",
        "title": "Test submission",
        "subreddit": "test",
        "score": 100,
        "num_comments": 50,
        "selftext": "Test content",
    }
])

with patch("core.fetchers.database_fetcher.DatabaseFetcher", return_value=mock_fetcher):
    result = pipeline.run()

    print(f"✓ Pipeline executed successfully: {result['success']}")
    print(f"✓ Fetched: {result['stats']['fetched']}")
    print(f"✓ Analyzed: {result['stats']['analyzed']}")
    print(f"✓ Summary: {result['summary']}")
```

**Expected**: Pipeline runs successfully with mock data

### Step 5: Validate Service Initialization Patterns

Check each service initializes correctly:

```python
from core.pipeline import PipelineConfig, DataSource
from core.pipeline.orchestrator import OpportunityPipeline
from unittest.mock import MagicMock, patch

# Test profiler initialization
with patch("core.agents.profiler.EnhancedLLMProfiler"):
    with patch("core.deduplication.profiler_skip_logic.ProfilerSkipLogic"):
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            enable_profiler=True,
            limit=10,
        )
        pipeline = OpportunityPipeline(config)
        assert "profiler" in pipeline.services
        print("✓ Profiler service initialized")

# Test opportunity initialization
with patch("core.agents.interactive.opportunity_analyzer.OpportunityAnalyzerAgent"):
    config = PipelineConfig(
        data_source=DataSource.DATABASE,
        supabase_client=MagicMock(),
        enable_opportunity_scoring=True,
        limit=10,
    )
    pipeline = OpportunityPipeline(config)
    assert "opportunity" in pipeline.services
    print("✓ Opportunity service initialized")
```

**Expected**: Services initialize without errors

### Step 6: Validate Statistics Tracking

```python
from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource
from unittest.mock import MagicMock, patch

config = PipelineConfig(
    data_source=DataSource.DATABASE,
    supabase_client=MagicMock(),
    limit=10,
)

pipeline = OpportunityPipeline(config)

# Check initial stats
assert pipeline.stats["fetched"] == 0
assert pipeline.stats["analyzed"] == 0
print("✓ Initial statistics correct")

# Test reset
pipeline.stats["fetched"] = 100
pipeline.reset_statistics()
assert pipeline.stats["fetched"] == 0
print("✓ Statistics reset works")

# Test get_statistics
stats = pipeline.get_statistics()
assert "pipeline" in stats
assert "services" in stats
assert "summary" in stats
print("✓ get_statistics returns complete data")
```

**Expected**: Statistics tracking works correctly

---

## Success Criteria

- ✅ All 18 unit tests pass
- ✅ No linting or formatting errors
- ✅ Pipeline initializes with all service combinations
- ✅ Mock integration test runs successfully
- ✅ Service initialization patterns validated
- ✅ Statistics tracking validated
- ✅ Code quality: clear, well-documented, follows patterns

---

## Report Template

```markdown
# Phase 8 Part 1: OpportunityPipeline Testing Report

**Date**: YYYY-MM-DD
**Tester**: Local AI

## Test Results

### Unit Tests
- Total: 18
- Passed: X
- Failed: Y
- Coverage: Z%

### Integration Tests
- Mock data test: PASS/FAIL
- Service initialization: PASS/FAIL
- Statistics tracking: PASS/FAIL

### Code Quality
- Linting: PASS/FAIL
- Formatting: PASS/FAIL
- Documentation: PASS/FAIL

## Issues Found

1. [Issue description]
   - Location: file:line
   - Fix applied: [description]

## Files Modified

- `core/pipeline/orchestrator.py` - [changes if any]
- `tests/test_orchestrator.py` - [changes if any]

## Conclusion

[PERFECT SUCCESS / SUCCESS WITH FIXES / NEEDS REVIEW]

Total tests: X/18 passing
Code quality: [assessment]
Ready for Phase 8 Part 2: [YES/NO]
```

---

**Next**: Phase 8 Part 2 - Service Container (factory.py)
