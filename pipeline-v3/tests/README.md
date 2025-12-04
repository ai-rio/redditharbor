# AgnoOpportunityAnalyzer Test Suite

This directory contains the comprehensive test suite for the AgnoOpportunityAnalyzer implementation.

## Test Architecture

The test suite is organized into several categories:

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── __init__.py
│   └── test_*              # Individual component tests
├── integration/             # Integration tests for system components
│   ├── __init__.py
│   ├── conftest.py         # Integration test fixtures
│   └── test_*             # Integration test cases
├── performance/            # Performance and load testing
│   ├── __init__.py
│   ├── conftest.py         # Performance test fixtures
│   ├── test_agno_analyzer_performance.py
│   └── test_edge_cases.py  # Edge case tests
├── helpers/               # Test utilities and fixtures
│   ├── __init__.py
│   ├── base_test.py       # Base test classes
│   ├── mock_agno_agents.py # Mock implementations
│   ├── test_data_factory.py # Test data generation
│   └── assertion_helpers.py # Custom assertions
└── README.md             # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Focus**:
  - Individual agent behavior (WTP, Market Segment, Price Point, Payment Behavior)
  - Response parsing logic
  - Consensus calculation
  - Field normalization
- **Markers**: `@pytest.mark.unit`

### Integration Tests (`tests/integration/`)
- **Purpose**: Test interactions between components
- **Focus**:
  - Complete batch processing workflow
  - Database interactions with Supabase
  - AgentOps integration
  - Duplicate handling and analysis copying
  - Error handling scenarios
- **Markers**: `@pytest.mark.integration`

### Performance Tests (`tests/performance/`)
- **Purpose**: Test performance characteristics and scalability
- **Focus**:
  - Throughput under different loads
  - Memory usage scaling
  - Concurrent processing performance
  - Load testing scenarios
- **Markers**: `@pytest.mark.performance`

### Edge Case Tests (`tests/performance/test_edge_cases.py`)
- **Purpose**: Test robustness and error handling
- **Focus**:
  - Malformed responses
  - Network timeouts
  - Invalid input data
  - Rate limiting scenarios
  - Resource exhaustion
- **Markers**: `@pytest.mark.edge_case`

## Running Tests

### Using the Test Runner Script

```bash
# IMPORTANT: Always activate .venv first to prevent dependency conflicts!
source .venv/bin/activate

# Run all tests
python run_tests.py

# Run specific test type
python run_tests.py unit
python run_tests.py integration
python run_tests.py performance
python run_tests.py edge_case

# Run with coverage
python run_tests.py --coverage

# Run with verbose output
python run_tests.py --verbose
```

### Using pytest directly

```bash
# IMPORTANT: Always activate .venv first to prevent dependency conflicts!
source .venv/bin/activate

# Run all tests
pytest

# Run specific category
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest --cov=core/agents --cov=scripts/core --cov-report=html

# Run with markers
pytest -m unit
pytest -m integration
pytest -m performance
pytest -m edge_case

# Run in parallel
pytest -n auto  # Uses all available CPUs
pytest -n 4     # Use 4 CPUs
```

### Performance Benchmarking

```bash
# IMPORTANT: Always activate .venv first to prevent dependency conflicts!
source .venv/bin/activate

# Run performance benchmarks
pytest tests/performance/ --benchmark-only

# Run with specific benchmark options
pytest tests/performance/ --benchmark-only --benchmark-sort=mean
pytest tests/performance/ --benchmark-only --benchmark-group-by=name

# Save benchmark results
pytest tests/performance/ --benchmark-only --benchmark-json=benchmark_results.json
```

## Test Data Management

### Test Data Factory

The `test_data_factory.py` provides utilities for generating test data:

```python
from tests.helpers.test_data_factory import RedditSubmissionFactory, AgentResponseFactory

# Create batch submissions
submissions = RedditSubmissionFactory.create_batch_submissions(10)

# Create submissions with specific characteristics
submissions = RedditSubmissionFactory.create_batch_submissions(20, {
    'high_wtp_b2b': 10,
    'low_wtp_b2c': 5,
    'mixed_segment': 5
})

# Create single submission
submission = RedditSubmissionFactory.create_single_submission('high_wtp_b2b')

# Create mock agent responses
wtp_response = AgentResponseFactory.create_wtp_response()
segment_response = AgentResponseFactory.create_segment_response()
```

### Test Fixtures

The test suite provides comprehensive fixtures:

- `mock_supabase`: Mock Supabase client
- `mock_analyzer`: Mock Agno analyzer
- `test_batch_data`: Sample batch data
- `performance_monitor`: Performance monitoring utilities
- `edge_case_submissions`: Edge case test scenarios

## Configuration

### pytest.ini
Configures pytest with:
- Coverage settings (80% minimum required)
- Custom markers
- Test discovery rules
- Warning filters

### .coveragerc
Coverage configuration:
- Source paths for coverage measurement
- Exclusion rules
- Report formats (HTML, XML)
- Coverage thresholds

### pyproject.toml
Additional tooling configuration:
- pytest options
- coverage settings
- mypy type checking
- ruff linting rules

## CI/CD Integration

The test suite is configured for GitHub Actions:

- **Test Matrix**: Runs tests on multiple Python versions and test types
- **Performance Benchmarking**: Tracks performance over time
- **Security Scanning**: Runs safety and bandit checks
- **Linting**: Enforces code quality with ruff, black, and mypy
- **Integration Tests**: Full end-to-end testing

## Test Coverage Requirements

- **Minimum Coverage**: 80%
- **Coverage Targets**:
  - `core/agents/`: All agent implementations
  - `scripts/core/`: Core processing logic
- **Exclusions**: Test files, dependencies, and build artifacts

## Mock Strategies

### External Dependencies
- **Supabase**: Mocked for all unit tests
- **OpenRouter API**: Mocked with controlled responses
- **AgentOps**: Mocked for cost tracking verification

### Agent Mocks
- **Individual Agents**: MockWTPAgent, MockSegmentAgent, etc.
- **Team Coordination**: MockAgnoTeam simulates agent coordination
- **Response Generation**: Controlled mock responses for testing

## Custom Assertions

The `assertion_helpers.py` provides specialized assertions:

```python
from tests.helpers.assertion_helpers import AgnoAnalysisAssertions

# Validate analysis completeness
AgnoAnalysisAssertions.assert_analysis_completeness(analysis)

# Check score ranges
AgnoAnalysisAssertions.assert_score_ranges(analysis)

# Validate consensus calculation
AgnoAnalysisAssertions.assert_consensus_calculation(consensus_data, responses)

# Test field normalization
AgnoAnalysisAssertions.assert_field_normalization(data)
```

## Performance Testing

### Performance Metrics
- **Throughput**: Submissions processed per second
- **Latency**: Time per submission
- **Memory Usage**: Peak memory consumption
- **CPU Usage**: Average CPU utilization
- **Concurrency**: Scaling with multiple workers

### Load Testing Scenarios
- **Light Load**: 10 submissions
- **Medium Load**: 50 submissions
- **Heavy Load**: 100+ submissions
- **Rate Limiting**: Simulated API delays
- **Concurrent Access**: Multiple threads processing

## Error Handling Tests

### Network Scenarios
- Timeouts
- Connection errors
- Rate limiting
- Network partitions

### Data Scenarios
- Malformed JSON responses
- Missing required fields
- Invalid data types
- Unicode encoding issues

### System Scenarios
- Memory exhaustion
- Database connection failures
- API key validation
- Configuration errors

## Contributing

### Adding New Tests

1. **Place tests in appropriate directory**
   - Unit tests → `tests/unit/`
   - Integration tests → `tests/integration/`
   - Performance tests → `tests/performance/`

2. **Use appropriate markers**
   ```python
   @pytest.mark.unit
   def test_new_feature():
       pass
   ```

3. **Follow naming conventions**
   - Test files: `test_*.py`
   - Test classes: `Test*`
   - Test functions: `test_*`

4. **Use existing utilities**
   - Mock implementations from `mock_agno_agents.py`
   - Test data from `test_data_factory.py`
   - Custom assertions from `assertion_helpers.py`

### Test Best Practices

1. **Arrange-Act-Assert pattern**
2. **Descriptive test names**
3. **One assertion per test** (when possible)
4. **Use fixtures for setup/teardown**
5. **Mock external dependencies**
6. **Test both success and failure cases**
7. **Keep tests fast and isolated**

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in Python path
2. **Mock Failures**: Check mock setup in conftest.py
3. **Coverage Issues**: Verify .coveragerc configuration
4. **Performance Tests**: Install additional dependencies with `[performance]`

### Debug Tests

```bash
# Run with pdb debugger
pytest --pdb

# Stop on first failure
pytest --xfail

# Show verbose output
pytest -vv

# Run specific test with logging
pytest tests/unit/test_specific.py::test_function -s -v
```

## Future Enhancements

- **Property-based Testing**: With hypothesis library
- **Visual Testing**: With pytest-playwright for UI components
- **Contract Testing**: With pact for API contracts
- **Chaos Testing**: For resilience validation
- **Flaky Test Detection**: With flaky plugin