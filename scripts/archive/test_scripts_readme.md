# Archived Test Scripts

Test and debugging scripts moved from the project root directory during cleanup on 2025-11-16.

## Purpose

These scripts were created during development for:
- Integration testing
- Debugging specific features
- Performance testing
- Feature validation

## Contents

### Connection Pool Tests
- `test_connection_pool_minimal.py` - Minimal connection pool test
- `test_dspy_connection_pool.py` - DSPy connection pool validation
- `test_llm_connection_pool.py` - LLM connection pool testing

### Evidence-Based Profiling Tests
- `test_evidence_based_profiling.py` - Evidence-based AI profiling tests
- `test_evidence_integration.py` - Evidence integration validation
- `test_evidence_structure.py` - Evidence data structure tests

### Market Validation Tests
- `test_market_validation_integration.py` - Jina Reader API integration tests
- `test_jina_api_live.py` - Live Jina API testing
- `test_jina_simple.py` - Simple Jina API validation

### Batch Processing Tests
- `test_first_batch.py` - First batch processing test
- `test_single_opportunity.py` - Single opportunity scoring test
- `test_exact_execution.py` - Exact execution validation
- `test_tqdm_loop.py` - Progress bar loop testing
- `debug_batch_processing.py` - Batch processing debugger
- `diagnostic_batch_test.py` - Diagnostic batch testing

### Agent Tests
- `test_agent_call.py` - Agent call validation

### Utility Tests
- `test_imports.py` - Import validation test

## Usage

These scripts are archived but can still be run if needed:

```bash
# From project root
python archive/test_scripts/test_imports.py
```

## Note

For active testing, use the official test suite in `tests/` or `scripts/testing/`.

## Related Directories

- `tests/` - Official unit and integration tests
- `scripts/testing/` - Active testing scripts
- `scripts/database/` - Database migration and validation scripts
