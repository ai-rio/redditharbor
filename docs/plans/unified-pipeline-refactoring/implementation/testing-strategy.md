# Testing Strategy

Consolidated testing approach for unified pipeline refactoring.

---

## Testing Pyramid

```
         E2E Tests
        /          \
    Integration Tests
   /                  \
     Unit Tests
```

**Target Coverage**:
- Unit Tests: 90%+
- Integration Tests: 80%+
- E2E Tests: Critical paths only

---

## Unit Testing

**Framework**: pytest  
**Coverage Tool**: pytest-cov  
**Mocking**: pytest-mock, unittest.mock

### Standards
- One test file per module: `test_module_name.py`
- Test functions prefixed with `test_`
- Use fixtures for common setup
- Aim for 100% coverage on utilities
- Mock external dependencies

### Example
```python
def test_map_subreddit_to_sector():
    assert map_subreddit_to_sector('SaaS') == 'Technology'
    assert map_subreddit_to_sector('unknown') == 'General'
```

---

## Integration Testing

Test interactions between modules.

### Key Areas
- Fetchers + Formatters
- Enrichment Services + Deduplication
- Storage + DLT
- Orchestrator + All Services

### Example
```python
def test_database_fetcher_with_formatters():
    fetcher = DatabaseFetcher(supabase_client)
    submissions = list(fetcher.fetch(limit=10))
    
    assert all('submission_text' in sub for sub in submissions)
    assert all('formatted_at' in sub for sub in submissions)
```

---

## End-to-End Testing

Full pipeline execution tests.

```python
def test_complete_pipeline_database_source():
    """Test full pipeline with database source."""
    config = PipelineConfig(
        data_source='database',
        limit=10,
        enable_profiler=True,
        enable_opportunity_scoring=True
    )
    
    pipeline = OpportunityPipeline(config)
    result = pipeline.run()
    
    assert result['success'] is True
    assert result['stats']['fetched'] > 0
    assert result['stats']['analyzed'] > 0
```

---

## Side-by-Side Validation

Compare unified pipeline to monolithic pipelines.

```python
def test_unified_vs_monolith_profiler():
    """Validate profiler results match."""
    submission = load_test_submission()
    
    # Run monolith
    monolith_result = run_batch_profiler(submission)
    
    # Run unified
    unified_result = profiler_service.enrich(submission)
    
    assert monolith_result['app_name'] == unified_result['app_name']
    assert set(monolith_result['core_functions']) == set(unified_result['core_functions'])
```

---

## Performance Testing

Benchmark key operations.

```python
def test_pipeline_performance():
    """Ensure processing time within target."""
    import time
    
    start = time.time()
    pipeline.run(limit=100)
    duration = time.time() - start
    
    avg_time = duration / 100
    assert avg_time <= 7.0, f"Processing too slow: {avg_time}s"
```

---

## Test Data

### Fixtures
Use shared fixtures for consistency:
- `sample_submission` - Standard test submission
- `mock_supabase` - Mocked Supabase client
- `mock_profiler` - Mocked AI profiler

### Test Database
- Use separate test database
- Seed with known data
- Clean up after tests

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ --cov=core --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov-report=term-missing

# Run specific test file
pytest tests/test_profiler_service.py -v

# Run tests matching pattern
pytest tests/ -k "profiler" -v

# Run with markers
pytest tests/ -m "integration" -v
```

---

For detailed testing per phase, see individual phase documentation.
