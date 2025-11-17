# Archive Scripts

These scripts are no longer actively used but are preserved for reference.

## Purpose

This directory contains completed one-time scripts and deprecated functionality that may be useful for reference or future reactivation.

## Recently Archived (2025-11-16)

### Scripts Consolidated from archive/ (14 files)
Legacy scripts moved from root archive directory:

**Analysis Scripts**
- **analyze_function_distribution.py** - Function count distribution analysis
- **analyze_function_distribution_simple.py** - Simplified function analysis

**Certification & Testing**
- **certify_problem_first.py** - Problem-first certification
- **problem_first_test.py** - Problem-first testing
- **test_47_demos.py** - Demo testing (47 test cases)
- **test_commercial_insights.py** - Commercial insights testing
- **test_specific_post.py** - Specific post testing

**Data Collection**
- **collect_problem_posts.py** - Problem posts collector
- **filter_problems.py** - Problem filtering utility
- **find_test_candidates.py** - Test candidate finder

**Database Utilities**
- **check_comments.py** - Comment validation
- **check_commercial_data.py** - Commercial data checks
- **fix_comment_linkage.py** - Comment linkage fixes
- **fix_linkage.py** - General linkage fixes

### Test Scripts from Root Directory (17 files)
Development and debugging scripts cleaned up from project root:

**Connection Pool Tests**
- **test_connection_pool_minimal.py** - Minimal connection pool test
- **test_dspy_connection_pool.py** - DSPy connection pool validation
- **test_llm_connection_pool.py** - LLM connection pool testing

**Evidence-Based Profiling Tests**
- **test_evidence_based_profiling.py** - Evidence-based AI profiling tests
- **test_evidence_integration.py** - Evidence integration validation
- **test_evidence_structure.py** - Evidence data structure tests

**Market Validation Tests**
- **test_market_validation_integration.py** - Jina Reader API integration tests
- **test_jina_api_live.py** - Live Jina API testing
- **test_jina_simple.py** - Simple Jina API validation

**Batch Processing Tests**
- **test_first_batch.py** - First batch processing test
- **test_single_opportunity.py** - Single opportunity scoring test
- **test_exact_execution.py** - Exact execution validation
- **test_tqdm_loop.py** - Progress bar loop testing
- **debug_batch_processing.py** - Batch processing debugger
- **diagnostic_batch_test.py** - Diagnostic batch testing

**Agent Tests**
- **test_agent_call.py** - Agent call validation

**Utility Tests**
- **test_imports.py** - Import validation test

See `test_scripts_readme.md` for detailed documentation.

## Previously Archived (2025-11-14)

### Documentation Utilities
- **chunk_claude_docs.py** - Split large documentation files into LLM-manageable chunks using semchunk
- **enhance_chunk_index.py** - Analyzed chunks to extract context and create meaningful indexes

### Organization Utilities (Completed)
- **organize_scripts.py** - Script organization tool that created the current directory structure
- **script_analysis.py** - Analysis tool that categorized scripts for proper organization

### Pipeline & Testing Scripts
- **run_pipeline.py** - Legacy pipeline runner
- **ab_threshold_testing.py** - A/B threshold testing script
- **test_full_pipeline_workflow.py** - Full pipeline workflow test
- **test_trust_validation_real.py** - Trust validation testing
- **cleanup_empty_opportunities.py** - Database cleanup utility

## Usage

Archived scripts should not be run directly unless specifically needed for historical reference.

```bash
# If needed, run from project root
python scripts/archive/test_imports.py
```

## Related Directories

- `tests/` - Official unit and integration tests
- `scripts/testing/` - Active testing scripts
- `scripts/database/` - Database migration scripts
