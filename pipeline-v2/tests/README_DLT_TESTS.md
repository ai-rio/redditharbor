# DLT Supabase Configuration Tests

This directory contains comprehensive TDD (Test-Driven Development) tests for DLT Supabase configuration in the RedditHarbor pipeline-v2 project.

## Overview

The DLT Supabase configuration tests validate:
- DLT secrets.toml configuration loading and parsing
- Supabase destination type configuration
- PostgreSQL/Supabase credential validation
- Connection to Supabase (PostgreSQL) database
- Merge disposition for app_opportunities table
- Error handling for missing/invalid configurations
- Integration with main pipeline orchestration

## Test Files

### 1. `test_dlt_configuration.py`
**Primary test file for DLT configuration loading and validation**

**Test Classes:**
- `TestDLTConfigurationLoading` - Configuration file loading and parsing
- `TestDLTCredentialValidation` - Credential format and validation checks
- `TestDLTDestinationConfiguration` - Destination type and merge disposition configuration
- `TestDLTConfigurationErrorHandling` - Error handling for configuration issues
- `TestDLTIntegrationConfiguration` - Integration-style tests with DLT mocking
- `TestDLTConfigurationFilePathHandling` - Configuration file path resolution

**Key Fixtures:**
- `valid_secrets_toml_content()` - Valid Supabase configuration
- `invalid_secrets_toml_content()` - Configuration missing credentials
- `postgres_direct_secrets_toml()` - Direct PostgreSQL connection string
- `supabase_structured_secrets_toml()` - Structured Supabase credentials
- `temp_secrets_dir()` - Temporary directory for configuration testing

### 2. `test_dlt_supabase_connection.py`
**Primary test file for DLT Supabase connection and merge functionality**

**Test Classes:**
- `TestDLTPipelineCreation` - DLT pipeline creation and configuration
- `TestDLTCredentialsConfiguration` - Credential configuration for Supabase/PostgreSQL
- `TestSupabaseConnection` - Supabase client creation and operations
- `TestDLTSupabaseIntegration` - Integration between DLT and Supabase
- `TestMergeDisposition` - Merge disposition functionality for app_opportunities table
- `TestConnectionErrorHandling` - Connection error handling and recovery
- `TestDLTPerformance` - Performance and scalability testing
- `TestMainPipelineIntegration` - Integration with main pipeline step 6

**Key Fixtures:**
- `mock_supabase_client()` - Mock Supabase client for testing
- `mock_dlt_pipeline()` - Mock DLT pipeline for testing
- `sample_app_opportunities_data()` - Sample data for merge testing
- `mock_postgres_connection()` - Mock PostgreSQL connection

### 3. `test_dlt_validation.py` (Optional)
**Validation script for test structure and dependencies**

Validates that test files can be imported and basic functionality works without requiring the full pytest framework.

### 4. `test_dlt_simple_validation.py` (Optional)
**Simple validation without pytest dependency**

Tests core logic and structure without requiring external dependencies.

### 5. `run_dlt_tests.py` (Optional)
**Simple test runner that mimics pytest functionality**

Runs DLT tests using a minimal test runner that doesn't require the full pytest framework.

## Key Test Scenarios

### Configuration Loading Tests
- ✅ Loading valid secrets.toml files
- ✅ Handling missing configuration files
- ✅ Parsing invalid TOML syntax
- ✅ Loading incomplete configurations
- ✅ File path resolution and creation

### Credential Validation Tests
- ✅ PostgreSQL connection string format validation
- ✅ Supabase host pattern validation
- ✅ Structured credential validation
- ✅ Invalid credential detection
- ✅ Port and field validation

### Destination Configuration Tests
- ✅ Supabase destination configuration
- ✅ PostgreSQL destination configuration (fallback)
- ✅ Merge disposition configuration
- ✅ Destination type compatibility

### Connection Integration Tests
- ✅ DLT pipeline creation with Supabase
- ✅ Supabase client creation and operations
- ✅ Database connection validation
- ✅ Error handling for connection failures

### Merge Disposition Tests
- ✅ Merging new records to app_opportunities table
- ✅ Updating existing records
- ✅ Incremental load configuration
- ✅ Schema validation during merge
- ✅ Error handling during merge operations

### Error Handling Tests
- ✅ Connection failure handling
- ✅ Invalid credentials error handling
- ✅ Connection timeout handling
- ✅ Database error during merge
- ✅ Graceful degradation scenarios

### Performance Tests
- ✅ Large dataset merge performance
- ✅ Batch processing configuration
- ✅ Memory usage optimization

### Pipeline Integration Tests
- ✅ Step 6 integration with main pipeline
- ✅ Empty data handling
- ✅ End-to-end data flow validation

## Running the Tests

### With pytest (Recommended)
```bash
# Run all DLT tests
pytest tests/test_dlt_configuration.py tests/test_dlt_supabase_connection.py -v

# Run specific test classes
pytest tests/test_dlt_configuration.py::TestDLTConfigurationLoading -v
pytest tests/test_dlt_supabase_connection.py::TestMergeDisposition -v

# Run with markers
pytest tests/ -m dlt_config -v
pytest tests/ -m merge_disposition -v
```

### Without pytest (Development/Validation)
```bash
# Run simple validation
python3 tests/test_dlt_simple_validation.py

# Run with minimal test runner
python3 tests/run_dlt_tests.py
```

## Test Dependencies

### Required for Full Testing:
- `pytest` - Test framework
- `toml` - Configuration file parsing

### Optional Dependencies:
- `dlt` - DLT library (mocked in tests)
- `supabase` - Supabase client library (mocked in tests)

### Graceful Degradation:
The tests are designed to work without external dependencies:
- Missing `toml` module → Tests that require TOML parsing are skipped
- Missing `pytest` framework → Use simple validation scripts
- Missing `dlt` library → Uses comprehensive mocking

## Configuration Format

### Supabase Configuration (secrets.toml)
```toml
[runtime]
log_level = "INFO"

[destination.supabase]
credentials = "postgresql://postgres:postgres@localhost:54322/postgres"

[destination.supabase.credentials]
database = "reddit_harbor"
username = "postgres"
password = "postgres"
host = "localhost"
port = 5432
connect_timeout = 30
sslmode = "require"

[destination.supabase.data_writer]
disposition = "merge"
write_disposition = "merge"
primary_key = "id"
```

### PostgreSQL Direct Configuration
```toml
[runtime]
log_level = "INFO"

[destination.postgres]
credentials = "postgresql://user:pass@host:5432/database"
```

## Test Data Structure

The tests expect app_opportunities data in this format:
```python
{
    "id": "unique_identifier",
    "reddit_id": "t3_abc123",
    "title": "Opportunity title",
    "score": 85.5,
    "trust_score": 92.0,
    "subreddit": "productivity",
    "created_utc": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "analysis_metadata": {
        "opportunity_score": 88.0,
        "monetization_score": 75.0,
        "user_intent": "automation_need"
    }
}
```

## Integration with Main Pipeline

These tests support Step 6 of the main RedditHarbor pipeline:

```python
def pipeline_step_6_load_to_supabase(processed_data):
    """Step 6: Load validated opportunities to Supabase using DLT"""

    # Create DLT pipeline for Supabase
    pipeline = dlt.pipeline(
        pipeline_name="reddit_harbor",
        destination="supabase",
        dataset_name="reddit_data"
    )

    # Load opportunities with merge disposition
    pipeline.run(
        processed_data,
        table_name="app_opportunities",
        write_disposition="merge",
        primary_key="id"
    )
```

## Error Handling Strategy

The tests implement comprehensive error handling:

1. **Configuration Errors** - Missing or invalid configuration files
2. **Connection Errors** - Database connection failures
3. **Credential Errors** - Invalid authentication credentials
4. **Data Validation Errors** - Invalid data format or schema
5. **Performance Errors** - Large dataset handling issues

## Best Practices

### Test Organization
- Tests are organized by functionality (configuration, connection, merge)
- Each test class focuses on a specific aspect
- Fixtures provide reusable test data and mocks
- Clear test names describe what is being tested

### Error Handling
- All external dependencies are mocked
- Tests include both success and failure scenarios
- Error messages are descriptive and helpful
- Graceful degradation when dependencies are missing

### Performance Considerations
- Tests use mocking to avoid real database connections
- Large dataset testing is optional and marked as slow
- Batch processing is tested for scalability

## Future Enhancements

### Additional Test Scenarios
- Real Supabase integration tests (with test instance)
- Performance benchmarks with actual data volumes
- Concurrent access testing
- Disaster recovery testing

### Test Automation
- CI/CD integration for automated testing
- Performance regression testing
- Configuration drift detection
- Data quality monitoring

## Documentation

- Main pipeline documentation: `../README.md`
- DLT documentation: https://dlthub.com/docs/
- Supabase documentation: https://supabase.com/docs/
- pytest documentation: https://docs.pytest.org/

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Add appropriate fixtures for reusable test data
3. Include both success and failure test cases
4. Use mocking for external dependencies
5. Add comprehensive test documentation
6. Update this README if adding new test categories

## TDD Approach

These tests were created following Test-Driven Development principles:

1. **Tests First** - Tests were written before the implementation
2. **Comprehensive Coverage** - Tests cover all expected scenarios
3. **Clear Requirements** - Tests define the expected behavior
4. **Incremental Development** - Implementation can be developed incrementally
5. **Continuous Validation** - Tests can be run continuously during development

The tests serve as both validation and specification for the DLT Supabase configuration implementation.