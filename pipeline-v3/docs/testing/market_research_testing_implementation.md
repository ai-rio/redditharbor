# Market Research Testing Implementation

## Overview

Comprehensive test suite for Phase 3.6 Jina Market Research Integration following TDD methodology with VCR.py integration and performance testing.

## Test Suite Structure

### 1. Unit Tests (TDD Approach)
**File**: `tests/transform/test_market_research_agent_tdd.py`

Follows RED-GREEN-REFACTOR methodology:

#### Test Classes:
- **TestValidationScoreCalculation**: Tests validation score logic
  - High score with all evidence
  - Moderate score with partial evidence
  - Zero score with no evidence
  - Score weight application
  - Billion-dollar market boost

- **TestDataQualityScore**: Tests data quality assessment
  - High quality with reputable sources
  - Medium quality with mixed sources
  - Zero quality with no data
  - Launch engagement calculation

- **TestCostTracking**: Tests cost tracking functionality
  - Initialization and accumulation
  - Disabled tracking behavior
  - Division by zero handling
  - Cost reset functionality
  - Mock cost calculation

- **TestConfigurationValidation**: Tests agent configuration
  - Custom validation threshold
  - Max competitors/launches limits
  - Real Jina detection
  - Force mock implementation

- **TestErrorHandling**: Tests error scenarios
  - Missing input data
  - None input fields
  - Exception in validation
  - Jina client init failure
  - Async context manager

- **TestReasoningGeneration**: Tests reasoning from evidence
  - Comprehensive with all evidence
  - Competitors only
  - No evidence
  - Confidence scores

- **TestDataConversion**: Tests format conversion
  - Evidence to dict conversion
  - Competitor pricing format
  - Error result format

### 2. VCR.py Integration Tests
**File**: `tests/transform/test_market_research_agent_vcr.py`

Records and replays real Jina API interactions:

#### Test Classes:
- **TestJinaClientVCR**:
  - Real web search functionality
  - Real content extraction
  - Real pricing extraction
  - Real market size extraction
  - Real product launch extraction
  - Rate limiting behavior
  - Retry logic on failure
  - Error propagation on max retries

- **TestJinaCacheVCR**:
  - Cache hit/miss tracking
  - TTL behavior by data type
  - Cost savings estimation
  - In-memory fallback
  - Cache key generation

- **TestMarketResearchAgentIntegrationVCR**:
  - End-to-end market validation
  - Concurrent validations
  - Graceful degradation on API failure

### 3. Performance Tests
**File**: `tests/transform/test_market_research_performance.py`

Comprehensive performance benchmarking:

#### Test Classes:
- **TestMarketResearchPerformance**:
  - Market validation performance
  - Concurrent validation performance
  - Cache performance
  - Cost tracking performance
  - Memory efficiency
  - Score calculation performance
  - Reasoning generation performance
  - Data conversion performance

- **TestJinaClientPerformance**:
  - HTTP request performance
  - Concurrent HTTP performance

- **TestCachePerformance**:
  - Cache scalability
  - Large dataset performance

### 4. Integration Tests (Fixed)
**File**: `tests/transform/test_agno_market_research_integration_fixed.py`

Tests for MarketResearchAgent integration into AgnoOpportunityAnalyzer:

#### Test Classes:
- **TestMarketResearchAgentIntegration**:
  - MarketResearchAgent in team
  - Agent properties validation
  - High score analysis
  - Low score analysis
  - Cost tracking
  - Backward compatibility
  - Configuration support
  - Decision logic
  - Error handling

- **TestMarketResearchAgentAsyncIntegration**:
  - Async run functionality
  - Context manager behavior
  - Cost tracking across validations

## Configuration

### VCR.py Configuration
```python
vcr_config = vcr.VCR(
    cassette_library_dir=str(VCR_CASSETTE_DIR),
    record_mode="once",
    match_on=["uri", "method", "body"],
    filter_headers=["authorization", "x-api-key", "cookie"],
    filter_post_data_parameters=["api_key", "token"],
    decode_compressed_response=True,
    record_on_exception=True,
    before_record_response=filter_sensitive_data,
)
```

### Test Markers
- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.slow`: Slow tests
- `@pytest.mark.api`: Tests with external API calls
- `@pytest.mark.redis`: Tests requiring Redis
- `@pytest.mark.tdd`: TDD tests
- `@pytest.mark.vcr`: Tests using VCR.py
- `@pytest.mark.benchmark`: Benchmark tests

## Running Tests

### Prerequisites
1. Install dependencies (including VCR.py):
```bash
pip install vcrpy
```

2. Redis (optional, for cache tests):
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest
```

### Running All Tests
```bash
# Using the test runner script
python run_market_research_tests.py

# Or directly with pytest
pytest tests/transform/test_market_research_* -v
```

### Running Specific Test Categories
```bash
# Unit tests only
pytest tests/transform/test_market_research_agent_tdd.py -v

# VCR tests (records first run)
pytest tests/transform/test_market_research_agent_vcr.py -v --record-mode=once

# Performance tests
pytest tests/transform/test_market_research_performance.py -v --benchmark

# Integration tests
pytest tests/transform/test_agno_market_research_integration_fixed.py -v
```

### Recording VCR Cassettes
```bash
# First run (records API interactions)
pytest tests/transform/test_market_research_agent_vcr.py -k "test_real_jina" --record-mode=once

# Subsequent runs (replays recordings)
pytest tests/transform/test_market_research_agent_vcr.py -k "test_real_jina"
```

## Test Data

### Fixtures
- `sample_reddit_submission`: Mock Reddit submission
- `sample_app_idea`: Mock app idea
- `sample_market_validation_data`: Complete validation data
- `mock_redis_connection`: Redis connection (or fakeredis fallback)
- `benchmark_data`: Generated test data for performance tests

### VCR Cassettes
Stored in `tests/fixtures/vcr_cassettes/`:
- API requests and responses
- Sensitive data filtered automatically
- One-time recording, infinite replay

## Performance Benchmarks

### Targets
- Market validation: <1s single, <2s average batch
- Cache operations: <10ms write, <5ms read
- Concurrent requests: Linear scaling improvement
- Memory usage: <100MB for 1000 validations
- Cost tracking: <10% overhead

### Metrics Tracked
- Response time distribution (min, max, mean, p50, p95, p99)
- Requests per second
- Cache hit rates
- Cost per validation
- Memory usage growth
- Cost savings from caching

## CI/CD Integration

### GitHub Actions Workflow
```yaml
- name: Run Market Research Tests
  run: |
    python run_market_research_tests.py --cov=transform/market_research_agent

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Quality Gates
- Test coverage >80%
- All unit tests passing
- Performance benchmarks within targets
- No critical integration failures

## Troubleshooting

### Common Issues

1. **VCR Recording Fails**
   - Check API keys are set
   - Ensure target URLs are accessible
   - Verify network connectivity

2. **Redis Tests Skipped**
   - Start Redis server
   - Check Redis URL configuration
   - Install fakeredis as fallback

3. **Performance Test Failures**
   - Check system resources
   - Close unnecessary applications
   - Run on dedicated test environment

4. **Import Errors**
   - Install missing dependencies
   - Check Python path configuration
   - Verify virtual environment

## Future Enhancements

1. **Property-Based Testing**: Use hypothesis for edge case generation
2. **Load Testing**: Integrate with locust for stress testing
3. **Contract Testing**: Verify API contract compliance
4. **Visual Regression**: Screenshot comparison for UI components
5. **Mutation Testing**: Verify test suite effectiveness with mutmut