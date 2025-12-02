# Testing Documentation

**Directory**: Testing strategies, frameworks, and reports

---

## Overview

This directory contains comprehensive testing documentation for the unified pipeline refactoring project, including testing frameworks, strategies, and execution reports.

## Structure

### 📋 Testing Framework & Strategy

- **[testing-framework.md](testing-framework.md)** - Overall testing approach and strategy
- **[phase-8-comprehensive-testing-plan.md](phase-8-comprehensive-testing-plan.md)** - Detailed testing plan for Phase 8
- **[phase-8-full-pipeline-testing-framework.md](phase-8-full-pipeline-testing-framework.md)** - Complete pipeline testing framework

### 📊 Local AI Testing Reports

**Current Reports** in the `local-ai-report/` directory:
- **[local-ai-report/README.md](local-ai-report/README.md)** - Overview of testing reports
- **Active Phase Reports**: Current phase testing results and validation
- **Schema Reports**: Database schema validation and migration reports
- **Integration Reports**: End-to-end integration testing outcomes

**Archived Reports** in the `archive/` directory:
- **[archive/phase-reports-2025-11/](archive/phase-reports-2025-11/)** - November 2025 phase testing reports
- Contains completed phase reports for phases 5-8
- Historical testing data for reference and compliance

## Testing Coverage

### Unit Testing
- **Coverage Target**: >90% for all extracted modules
- **Framework**: pytest with comprehensive mocking
- **Focus**: Individual component functionality and edge cases

### Integration Testing
- **Scope**: Module interactions and data flow validation
- **Environment**: Staging with production-like data
- **Focus**: Service integration and configuration validation

### End-to-End Testing
- **Scope**: Complete pipeline execution with both data sources
- **Validation**: Byte-for-byte comparison with monoliths
- **Performance**: Throughput, memory usage, and latency benchmarks

### Schema Testing
- **Database**: PostgreSQL schema validation and migration testing
- **DLT**: Data pipeline schema evolution and compatibility
- **Integrity**: Data consistency and validation rules

## Usage

### Before Implementation
1. Review `testing-framework.md` for overall approach
2. Understand testing requirements for your phase
3. Set up testing environment according to framework guidelines

### During Development
1. Follow the specific phase testing plans
2. Run comprehensive tests after each major task
3. Document testing results in execution logs

### Validation
1. Complete all required test suites
2. Verify performance targets are met
3. Generate and review testing reports

### Reporting
1. Update `local-ai-report/` with latest test results
2. Track progress against testing framework requirements
3. Document any issues or blockers found

## Test Categories

### Schema Tests
- **Phase 0**: Initial schema validation and fixes
- **Migration**: Database schema migration testing
- **Integrity**: Data consistency and validation

### Phase Tests
- **Phase 1**: Foundation and setup testing
- **Phase 2**: Agent restructuring validation
- **Phase 3**: Utility extraction testing
- **Phase 4**: Data fetching layer testing
- **Phase 5**: Deduplication system testing
- **Phase 6**: AI enrichment services testing
- **Phase 7**: Storage layer testing
- **Phase 8**: Unified orchestrator testing

### Integration Tests
- **Single Submission**: End-to-end single record processing
- **Batch Processing**: Bulk data processing validation
- **Trust Preservation**: Trust system integrity testing

## Performance Benchmarks

All testing includes performance validation against baseline metrics:
- **Processing Time**: ≤7.0 seconds per submission
- **Throughput**: ≥500 submissions/hour
- **Memory Usage**: ≤400MB
- **Error Rate**: ≤1%

---

**Related**: [Main README](../README.md) | [Phase Files](../phases/) | [Implementation Details](../implementation/) | [Planning Documents](../planning/)