# Project Archive - RedditHarbor

This directory contains archived **project artifacts** (logs, SQL dumps, reports) that are no longer actively used.

**Note**: All Python scripts have been consolidated to `scripts/archive/` for better organization. This directory now focuses on non-code artifacts.

## Recent Changes (2025-11-16)

- **Python scripts moved** to `scripts/archive/` (14 scripts consolidated)
- **Log files consolidated** to `logs/` subdirectory
- **SQL dumps preserved** in `sql_dumps/`
- **Historical subdirectories** maintained in `archive/` subdirectory

## Directory Structure

### Current Contents

- **README.md** - This file
- **script_organization_report.md** - Documentation of script organization
- **logs/** - Consolidated log files
- **sql_dumps/** - Database SQL dumps
- **cost_tracking_cleanup_2025_11_13/** - Cost tracking migration artifacts
- **recent_cleanup/** - Recently cleaned up files
- **archive/** - Historical subdirectories with categorized content

### Log Files (Preserved for Historical Reference)

- `batch_scoring.log` - Batch scoring operation logs
- `batch_scoring_all.log` - Complete batch scoring logs
- `dashboard8081.log` - Dashboard service logs
- `marimo.log` - Marimo notebook logs

## Archived Code (Now in scripts/archive/)

All Python scripts have been moved to `scripts/archive/` including:
- Analysis scripts (`analyze_function_distribution.py`, etc.)
- Test scripts (`certify_problem_first.py`, `test_*.py`, etc.)
- Utility scripts (`check_*.py`, `fix_*.py`, etc.)

## Historical Subdirectories (archive/archive/)

### test_infrastructure/ (6 scripts) - NEW
DLT integration and pipeline testing scripts used during development.

- `test_dlt_connection.py` - DLT connection validation
- `test_dlt_pipeline.py` - End-to-end DLT pipeline testing
- `parallel_test_dlt.py` - Parallel DLT operations testing
- `test_dlt_with_praw.py` - PRAW-DLT integration testing
- `test_incremental_loading.py` - Incremental loading validation
- `test_scanner.py` - Subreddit scanner testing

### utilities/ (4 scripts) - NEW
Development and monitoring utilities from DLT cutover phase.

- `check_cutover_status.py` - DLT traffic cutover monitoring (0%→50%→100%)
- `check_database_schema.py` - Database schema validation
- `verify_monetizable_implementation.py` - Implementation verification
- `monitor_collection.sh` - Collection process monitoring

### pipeline_management/ (3 scripts) - NEW
DLT integration and traffic cutover orchestration scripts.

- `dlt_opportunity_pipeline.py` - DLT opportunity discovery pipeline
- `dlt_traffic_cuttover.py` - Traffic cutover orchestration (0%→100%)
- `run_monetizable_collection.py` - Monetizable opportunity orchestrator

### research/ (3 scripts) - NEW
Legacy research framework scripts superseded by DLT-based workflows.

- `research.py` - Core research framework with templates
- `research_monetizable_opportunities.py` - Monetizable opportunity research
- `intelligent_research_analyzer.py` - AI-powered research analyzer

### old_versions/ (7 scripts) - UPDATED
Old versions of current scripts. Kept for reference.

- `generate_opportunity_insights.py` - Old version, use `generate_opportunity_insights_openrouter.py`
- `generate_opportunity_insights_with_rate_limit.py` - Previous implementation
- `enhanced_full_scale_collection.py` - Duplicate of `full_scale_collection.py`
- `enhanced_monetizable_collection.py` - Legacy implementation
- `example_monetizable_collection.py` - Example/draft only
- `real_system_test.py` - Superseded by `final_system_test.py`
- `manual_subreddit_test.py` - Legacy scanner, replaced by production collectors

### hung_stuck/ (5 scripts)
Scripts that were hanging or had rate-limiting issues.

- `fast_subreddit_scanner.py` - Hangs on Reddit API calls
- `robust_scanner.py` - PRAW version incompatibility issues
- `subreddit_monetization_scanner.py` - Complex scanner, hung during execution
- `test_comment_collection.py` - Duplicate test, multiple instances running
- `quick_collection_test.py` - Duplicate test, replaced by `collect_commercial_data.py`

### duplicate_tests/ (7 scripts)
Duplicate or temporary test scripts.

- `test_simple_collection.py` - Simple test
- `minimal_test.py` - Minimal test
- `test_enhanced_collection.py` - Enhanced collection test
- `test_batch_scoring.py` - Batch scoring test
- `fresh_test.py` - Temporary test
- `final_test.py` - Temporary test
- `pipeline_test.py` - Pipeline test

### fix_scripts/ (3 scripts)
Temporary fix scripts, functionality now in main pipeline.

- `immediate_comment_fix.py` - Fixed in main pipeline
- `fix_comment_infrastructure.py` - Resolved infrastructure issue
- `fix_spacy_dependency.py` - Dependency fix

### demos/ (3 scripts)
Demo/example scripts for reference.

- `manual_research_demo.py` - Research demo
- `demo.py` - General demo
- `demo_simple.py` - Simple demo

### domain_research/ (4 scripts)
Domain-specific research examples.

- `research_budget_travel.py` - Budget travel research
- `research_chronic_disease.py` - Chronic disease research
- `research_personal_finance.py` - Personal finance research
- `research_skill_acquisition.py` - Skill acquisition research

### data_analysis/ (6 scripts)
Old data analysis scripts, replaced by main pipeline.

- `analyze_existing_reddit_data.py` - Old analysis
- `analyze_real_database_data.py` - Database analysis
- `analyze_research_data.py` - Research data analysis
- `verify_real_data.py` - Verification script
- `verify_opportunity_data.py` - Opportunity verification
- `process_existing_data_for_opportunities.py` - Data processing

### agent_sdk/ (2 scripts)
Agent SDK demonstration scripts.

- `agent_sdk_demo.py` - Agent SDK demo
- `agent_sdk_simple_demo.py` - Simple agent SDK demo

### dashboard_ui/ (2 scripts)
Dashboard and UI components.

- `decision_dashboard.py` - Decision dashboard
- `automated_decision_reporter.py` - Automated reporting UI

### other/ (6 scripts)
Miscellaneous scripts.

- `certification.py` - Certification script
- `comment_table_creator.py` - Table creation utility
- `run_niche_research.py` - Niche research
- `test_research_framework.py` - Research framework test
- `test_env.py` - Environment test
- `collect_real_reddit_data.py` - Duplicate collection

### recent_cleanup/ (16 files) - UPDATED 2025-11-13
Files moved during final production cleanup. Non-essential test scripts, logs, and utilities from production readiness phase.

**Pipeline Validation Logs (8 files)**:
- `pipeline_validation_*.log` - Pipeline execution logs from trust layer testing phase

**Test Scripts (4 files)**:
- `test_llm_profiler.py` - LLM profiling test script
- `dodo.py` - Test utility script
- `test_trust_schema_fix.py` - Trust schema validation test
- `check_db_direct.py` - Direct database connection test

**Note**: Documentation files were moved to appropriate docs/ subdirectories for better organization.

## Summary

- **Total Archived:** 94+ scripts and files
- **Categories:** 15 directories
- **New Categories (Nov 7, 2025):** 5 (test_infrastructure, utilities, pipeline_management, research, recent_cleanup)
- **Recent Cleanup (Nov 8, 2025):** 8 files newly archived from root directory
- **Production Cleanup (Nov 13, 2025):** 16 files newly archived from root and scripts directories

### Archival Breakdown
- **Test infrastructure:** 6 scripts (DLT integration testing)
- **Utilities:** 4 scripts (development and monitoring tools)
- **Pipeline management:** 3 scripts (DLT cutover orchestration)
- **Research:** 3 scripts (legacy research framework)
- **Old versions:** 7 scripts (superseded implementations)
- **Hung/stuck:** 5 scripts (performance issues)
- **Duplicates:** 7 scripts (redundant tests)
- **Temporary fixes:** 3 scripts (resolved issues)
- **Demos/examples:** 3 scripts (reference only)
- **Domain-specific:** 4 scripts (research examples)
- **Data analysis:** 6 scripts (replaced by pipeline)
- **Agent SDK:** 2 scripts (demonstrations)
- **Dashboard UI:** 2 scripts (UI components)
- **Other:** 6 scripts (miscellaneous)
- **Recent cleanup:** 8 files (from root directory organization)

## Current Active Scripts

Following the DLT consolidation (Week 2 Days 11-12), only **6 production scripts** remain in `/home/carlos/projects/redditharbor/scripts/`:

### Core Production Scripts (6)
1. **final_system_test.py** - Comprehensive system validation with live Reddit data
2. **batch_opportunity_scoring.py** - Batch opportunity scoring and ranking
3. **collect_commercial_data.py** - Commercial subreddit data collection
4. **full_scale_collection.py** - Full-scale data collection pipeline
5. **automated_opportunity_collector.py** - Automated opportunity discovery
6. **generate_opportunity_insights_openrouter.py** - AI-powered insights generation

Plus: `__init__.py` (module initialization)

**Total Active:** 7 files (6 scripts + 1 init)

### Recent Cleanup (Nov 8, 2025)

Files moved from root directory to `archive/recent_cleanup/`:

#### Utility Scripts (7)
- `test_full_pipeline_workflow.py` - Pipeline testing utility
- `generate_workflow_analysis.py` - Workflow analysis tool
- `dlt_cli.py` - DLT command-line interface
- `run_full_workflow.py` - Full workflow execution script
- `verify_migration_schema.py` - Migration schema verification

#### Documentation (2)
- `migration_archival_log.txt` - Log of migration activities
- `MIGRATION_SUCCESS_SUMMARY.txt` - Migration success documentation

#### Text Reports (6)
- `WORKFLOW_COMPLETION_REPORT.txt` - Workflow completion report
- `STAGE4_RESULTS_SUMMARY.txt` - Stage 4 results
- `ARCHIVAL_SUCCESS_REPORT.txt` - Archival success documentation
- `QUICK_START_WORKFLOW.md` - Quick start workflow guide
- `STAGE4_SUMMARY.md` - Stage 4 summary
- `STAGE4_COMPLETE.md` - Stage 4 completion report

#### Processed and Archived
All files successfully categorized and archived with proper documentation.

## DLT Integration Timeline

**Week 2 Days 11-12 (Nov 7, 2025):**
- ✅ DLT traffic cutover: 0% → 50% → 100%
- ✅ Dual-write validation successful
- ✅ Legacy pipeline decommissioned
- ✅ 19 scripts archived, 6 production scripts active

## Production Pipeline Architecture

```
automated_opportunity_collector.py
    ↓
collect_commercial_data.py / full_scale_collection.py
    ↓
DLT Pipeline (Supabase)
    ↓
batch_opportunity_scoring.py
    ↓
generate_opportunity_insights_openrouter.py
    ↓
Insights & Reports
```

## Reactivating Archived Scripts

If you need to restore an archived script:
```bash
# Example: restore test infrastructure script
cp /home/carlos/projects/redditharbor/archive/archive/test_infrastructure/test_dlt_pipeline.py /home/carlos/projects/redditharbor/scripts/
```

However, the **6 active production scripts** are the recommended and tested versions.

## Documentation

Each archive category has its own README with detailed information about the scripts, their purpose, and why they were archived. See:

- `test_infrastructure/README.md`
- `utilities/README.md`
- `pipeline_management/README.md`
- `research/README.md`

## Archive Organization Standards

This archive follows the doc-organizer pattern with:
- Clear categorization by purpose
- Individual README files per category
- Detailed archival rationale
- Production replacement guidance
- Reactivation instructions

### cost_tracking_cleanup_2025_11_13/ (2 files)
Cost tracking implementation cleanup files moved during project organization.

- `apply_fix_directly.py` - Direct database fix application utility
- `test_and_fix_cost_tracking.py` - Cost tracking testing and fixing script

These were utility scripts used during the cost tracking feature implementation and are no longer needed in the active codebase.

### recent_cleanup/ (8 files)
Files organized during project documentation cleanup in November 2025. Non-essential test scripts and utilities moved to maintain clean root directory structure.

**Test Scripts (7 files)**:
- enrichment_field_analysis.py - Field analysis for enrichment testing
- manual_agno_persistence_test.py - Manual Agno persistence testing
- test_agno_persistence.py - Agno persistence validation tests
- test_enrichment_fixes.py - Enrichment fixes validation
- test_fix_validation.py - Fix validation testing
- test_jsonb_integration.py - JSONB integration tests
- test_submission_id_mapping.py - Submission ID mapping tests


