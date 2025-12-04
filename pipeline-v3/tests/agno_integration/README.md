# Agno Integration Test Suite

Test-Driven Development (TDD) test suite for Phase 1: Core Agno Integration

## Test Structure

```
tests/agno_integration/
├── README.md (this file)
├── conftest.py              # Shared fixtures and test configuration
├── test_agno_analyzer.py    # Main AgnoOpportunityAnalyzer tests
├── test_agno_agents.py      # Individual agent tests
├── test_synthesis.py        # Consensus synthesis logic tests
├── test_format_conversion.py # Pipeline v3 format conversion tests
└── integration/
    └── test_pipeline_integration.py  # Full pipeline integration tests
```

## Test Coverage Goals

- `transform/agno_analyzer.py`: >85% coverage
- `transform/agno_agents.py`: >80% coverage
- `transform/agno_synthesis.py`: >90% coverage

## Running Tests

```bash
# Run all Agno tests with coverage
pytest tests/agno_integration/ -v --cov=pipeline-v3/transform --cov-report=html

# Run specific test file
pytest tests/agno_integration/test_agno_analyzer.py -v

# Run with TDD watch mode
pytest-watch tests/agno_integration/
```

## Test Approach (RED-GREEN-REFACTOR)

### RED Phase
1. Write failing tests first
2. Verify tests fail with expected error messages
3. Do NOT implement production code yet

### GREEN Phase
1. Implement minimal code to pass tests
2. Focus only on making tests green
3. No optimization or extra features

### REFACTOR Phase
1. Improve code quality while keeping tests green
2. Remove duplication
3. Improve naming and structure

## Test Dependencies

- pytest
- pytest-cov
- pytest-mock
- agno (multi-agent framework)
- instructor (Pydantic validation)
- litellm (LLM unified API)

## Mock Strategy

- Mock LLM API calls to avoid cost during testing
- Use VCR.py for recording real API responses (integration tests only)
- Mock Agno Team responses for unit tests
- Real EmbeddingStrategy with FakeEmbeddingProvider for embeddings
