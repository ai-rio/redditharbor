# Archived Scripts - RedditHarbor

This directory contains archived scripts that are no longer actively used in the RedditHarbor pipeline. They are preserved for historical reference and potential future use.

## Directory Structure

### hung_stuck/ (5 scripts)
Scripts that were hanging or had rate-limiting issues. Replaced by `manual_subreddit_test.py`.

- `fast_subreddit_scanner.py` - Hangs on Reddit API calls
- `robust_scanner.py` - PRAW version incompatibility issues
- `subreddit_monetization_scanner.py` - Complex scanner, hung during execution
- `test_comment_collection.py` - Duplicate test, multiple instances running
- `quick_collection_test.py` - Duplicate test, replaced by `collect_commercial_data.py`

### old_versions/ (5 scripts)
Old versions of current scripts. Kept for reference.

- `generate_opportunity_insights.py` - Old version, use `generate_opportunity_insights_openrouter.py`
- `generate_opportunity_insights_with_rate_limit.py` - Previous implementation
- `enhanced_full_scale_collection.py` - Duplicate of `full_scale_collection.py`
- `enhanced_monetizable_collection.py` - Legacy implementation
- `example_monetizable_collection.py` - Example/draft only

### duplicate_tests/ (7 scripts)
Duplicate or temporary test scripts.

- `test_simple_collection.py` - Simple test (use `test_scanner.py` instead)
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

## Summary

- **Total Archived:** 43 scripts
- **Reason for Archival:**
  - Hung/stuck: 5 scripts
  - Old versions: 5 scripts
  - Duplicates: 7 scripts
  - Temporary fixes: 3 scripts
  - Demos/examples: 3 scripts
  - Domain-specific: 4 scripts
  - Replaced by main pipeline: 6 scripts
  - Not core functionality: 10 scripts

## Current Active Scripts

The following scripts remain in `/home/carlos/projects/redditharbor/scripts/`:

1. **Collection:**
   - `full_scale_collection.py` - Main production collection
   - `collect_commercial_data.py` - Commercial subreddit collection

2. **Scanning:**
   - `manual_subreddit_test.py` - Subreddit monetization scanner
   - `test_scanner.py` - Simple scanner test

3. **Analysis:**
   - `batch_opportunity_scoring.py` - Opportunity scoring
   - `generate_opportunity_insights_openrouter.py` - AI insights

4. **Research:**
   - `research_monetizable_opportunities.py` - Research workflow
   - `research.py` - Research framework
   - `intelligent_research_analyzer.py` - Research analyzer

5. **Utilities:**
   - `run_monetizable_collection.py` - Collection orchestrator
   - `automated_opportunity_collector.py` - Automation
   - `check_database_schema.py` - Schema validation
   - `verify_monetizable_implementation.py` - Verification

Total: 14 scripts (13 + __init__.py)

## Reactivating Archived Scripts

If you need to restore an archived script:
```bash
# Example: restore hung scanner
cp archive/hung_stuck/manual_subreddit_test.py ../scripts/
```

However, the active scripts are the recommended and tested versions.
