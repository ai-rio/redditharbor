# Comprehensive Test Suite for Pipeline Quality Filtering

This directory contains comprehensive test coverage for the pipeline orchestrator's quality filtering functionality, including unit tests, integration tests, and performance tests.

## Test Structure

### Core Test Files

#### `test_pipeline_orchestrator_quality_filtering.py`
**Primary test file for quality filtering functionality**
- Tests the `_filter_by_quality` method with various scenarios
- Spam filtering validation
- Low-quality content filtering (content_quality_score < 40)
- Min score and min confidence threshold filtering
- Edge cases (empty lists, all spam, all high quality)
- Integration tests for complete pipeline execution
- Statistics accuracy and logging behavior

#### `test_analysis_quality_scoring.py`
**Tests for analysis result quality scoring models**
- `AnalysisResult` model validation and quality constraints
- `AppIdea` quality validation (title case, concept specificity)
- `MarketMetrics` consistency validation
- Spam vs quality score boundary validation
- Embedding vector validation
- Cross-model score consistency checks

#### `test_pipeline_performance.py`
**Performance and load testing**
- Large dataset filtering performance (1000-5000 analyses)
- Memory usage monitoring
- Concurrent processing simulation
- End-to-end pipeline performance
- Database storage performance
- Memory leak detection

#### `conftest.py`
**Pytest configuration and shared fixtures**
- Common test fixtures for analyses, submissions, and configurations
- Performance tracking utilities
- Custom pytest markers
- Test data generation helpers

## Test Categories

### Quality Filtering Tests (`@pytest.mark.quality_filtering`)
Focus on the core quality filtering logic:

- **Spam Detection**: Tests that spam content is properly identified and filtered
- **Content Quality**: Validates filtering based on content_quality_score threshold
- **Score Thresholds**: Tests min_score and min_confidence filtering
- **Boundary Values**: Edge cases around threshold values
- **Statistics Accuracy**: Ensures filtering statistics are correct

### Integration Tests (`@pytest.mark.integration`)
End-to-end pipeline testing:

- **Complete Pipeline Flow**: Full pipeline execution with quality filtering
- **Database Integration**: Storage with quality fields
- **Staging Layer**: Submission staging and deduplication
- **Error Handling**: Pipeline behavior under error conditions
- **Configuration Testing**: Different pipeline configurations

### Performance Tests (`@pytest.mark.performance`)
Performance and scalability testing:

- **Large Dataset Processing**: Filtering performance with 1000+ analyses
- **Memory Usage**: Memory consumption during processing
- **Concurrent Processing**: Multi-threading simulation
- **Load Testing**: Stress testing with varied conditions
- **Benchmarking**: Performance metrics and thresholds

## Running Tests

### Quick Start

```bash
# Run all tests
uv run pytest tests/ -v

# Run only quality filtering tests
uv run pytest tests/ -m "quality_filtering" -v

# Run with coverage
uv run pytest tests/ --cov=orchestration --cov=models --cov-report=html
```

### Using the Test Runner

```bash
# Run all tests with detailed reporting
python tests/run_tests.py

# Run only quality filtering tests
python tests/run_tests.py --quality-filtering

# Run only performance tests
python tests/run_tests.py --performance

# Run fast tests only (skip performance/slow tests)
python tests/run_tests.py --fast

# Run with coverage report
python tests/run_tests.py --coverage

# Run specific test file
python tests/run_tests.py --file tests/test_pipeline_orchestrator_quality_filtering.py

# Run tests matching pattern
python tests/run_tests.py --pattern "test_filter_by_quality"

# Run with parallel execution
python tests/run_tests.py --parallel 4
```

### Detailed Test Suites

```bash
# Run all test suites with detailed reporting
python tests/run_tests.py --suites
```

## Test Configuration

### Environment Variables

- `TEST_NO_OPENAI=1`: Disable OpenAI API calls during testing
- `PYTEST_CURRENT_TEST`: Set automatically by pytest

### Customizing Test Parameters

Edit the fixtures in `conftest.py` to modify:

- **Dataset Sizes**: Adjust number of generated test items
- **Quality Distributions**: Modify spam/low/medium/high quality ratios
- **Threshold Values**: Change default filtering thresholds
- **Performance Benchmarks**: Adjust performance assertion thresholds

## Test Coverage Areas

### 1. Quality Filtering Logic

✅ **Spam Filtering**
- High-scoring content marked as spam is filtered first
- Spam indicators are properly tracked
- Spam content has low quality score constraint

✅ **Content Quality Filtering**
- Content below quality threshold (40) is filtered
- Boundary value testing (exactly 40, just below 40)
- Quality score consistency with spam flag

✅ **Score Threshold Filtering**
- Minimum score threshold enforcement
- Minimum confidence threshold enforcement
- Configurable thresholds via PipelineConfiguration

✅ **Filtering Statistics**
- Accurate counting of filtered items by category
- Percentage calculations
- Detailed filtering reasons for debugging

### 2. Model Validation

✅ **AnalysisResult Model**
- Quality score constraints (spam must have score ≤ 40)
- Trust level validation (LOW, MEDIUM, HIGH)
- Embedding vector validation (type, length, values)
- Cross-model consistency (final score vs market metrics)

✅ **AppIdea Model**
- Title case enforcement
- Content length and quality requirements
- Core function limits (1-3 functions, no duplicates)
- Business feasibility validation

✅ **MarketMetrics Model**
- Value range validation (0-100)
- Precision limits (max 2 decimal places)
- Logical consistency between metrics
- Extreme value combination validation

### 3. Performance & Scalability

✅ **Large Dataset Processing**
- 1000+ analyses filtering performance
- Memory usage monitoring
- Processing rate benchmarks (>200 analyses/sec)

✅ **Concurrent Processing**
- Multi-threading simulation
- Shared resource handling
- Performance under concurrent load

✅ **Memory Management**
- Memory leak detection
- Garbage collection efficiency
- Memory usage patterns

### 4. Integration Testing

✅ **End-to-End Pipeline**
- Complete pipeline execution with quality filtering
- Database storage of quality-filtered results
- Pipeline configuration options

✅ **Component Integration**
- Reddit client → Analyzer → Quality Filter → Database
- Staging layer integration
- Error handling and recovery

## Test Data Generation

### Quality Levels

The test suite generates analyses with four quality levels:

1. **High Quality** (20%): content_quality_score > 80, trust_level="HIGH"
2. **Medium Quality** (50%): content_quality_score 60-80, trust_level="MEDIUM"
3. **Low Quality** (20%): content_quality_score < 40, trust_level="LOW"
4. **Spam** (10%): is_spam=True, content_quality_score ≤ 40

### Dynamic Test Data

Tests use dynamic data generation to:
- Test with realistic dataset sizes
- Vary content quality and characteristics
- Simulate real-world data patterns
- Ensure test reproducibility

## Performance Benchmarks

### Filtering Performance
- **Target**: >200 analyses/second
- **Large Dataset**: <10 seconds for 2000 analyses
- **Memory Usage**: <500MB for 2000 analyses

### End-to-End Pipeline
- **Target**: >30 submissions/second
- **Large Pipeline**: <30 seconds for 1000 submissions
- **Quality Filter Pass Rate**: Varies by data quality (typically 20-80%)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root
2. **Missing Dependencies**: Run `uv sync` to install dependencies
3. **Performance Test Failures**: May be due to system load, try running with fewer parallel workers
4. **Memory Issues**: Some performance tests require significant RAM

### Debug Mode

```bash
# Run with detailed output
uv run pytest tests/ -v -s

# Stop on first failure
uv run pytest tests/ -x

# Run specific test with debugging
uv run pytest tests/test_pipeline_orchestrator_quality_filtering.py::TestPipelineOrchestratorQualityFiltering::test_filter_by_quality_comprehensive_functionality -v -s
```

## Contributing

### Adding New Tests

1. **Follow Naming Conventions**: Use descriptive test names
2. **Use Fixtures**: Leverage existing fixtures for consistency
3. **Add Markers**: Use appropriate pytest markers
4. **Include Performance**: Add performance assertions for relevant tests
5. **Document**: Add docstrings explaining test purpose

### Test Categories

- **Unit Tests**: Fast tests for individual components
- **Integration Tests**: Tests for component interaction
- **Performance Tests**: Tests with performance assertions
- **Edge Case Tests**: Tests for boundary conditions and error cases

## Continuous Integration

These tests are designed to run in CI/CD environments:

- **Fast Tests**: <5 minutes for core functionality
- **Full Suite**: <30 minutes including performance tests
- **Parallel Execution**: Configurable for faster CI runs
- **Coverage Reporting**: Generate coverage reports for quality gates

## Test Reports

After running tests, you can find:

- **Coverage Report**: `htmlcov/index.html` (when using `--coverage`)
- **Test Output**: Console output with detailed results
- **Performance Metrics**: Printed by performance tests
- **Log Files**: `test_output.log` for detailed logging

## Best Practices

1. **Run Tests Before Changes**: Ensure baseline passes
2. **Test Early, Test Often**: Run relevant tests during development
3. **Performance Awareness**: Monitor test performance impact
4. **Isolation**: Tests should be independent and order-agnostic
5. **Clear Assertions**: Use descriptive assertion messages
6. **Mock External Dependencies**: Avoid external API calls in tests