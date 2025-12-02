# Database Scripts

These scripts perform database maintenance and cleanup operations.

## Python Scripts

- **clean_database_slate.py** - Clear all data while preserving structure
- **add_missing_constraints.py** - Add missing database constraints
- **apply_market_validation_migration.py** - Apply market validation schema changes
- **check_all_tables.py** - Check status of all database tables
- **check_assessment_tables.py** - Verify assessment table schemas
- **check_backup_tables.py** - Validate backup table integrity
- **check_db_status.py** - Overall database health check
- **check_table_schemas.py** - Validate table schemas
- **create_cost_analysis_views.py** - Create views for cost analysis
- **deploy_trust_schema_fix.py** - Deploy trust-related schema fixes
- **execute_migration_via_rpc.py** - Execute migrations via RPC calls
- **investigate_schemas.py** - Analyze database schemas
- **investigate_trust_schema.py** - Deep dive into trust schema
- **migrate_core_functions_format.py** - Migrate core functions format
- **migration_cleanup_execute.py** - Execute migration cleanup
- **migration_final_cleanup.py** - Final migration cleanup
- **run_cost_tracking_migration.py** - Run cost tracking migration
- **test_schema.py** - Test database schema
- **verify_final_migration.py** - Verify migration completion

## SQL Scripts

### Schema & Migration Scripts
- **apply-schema-fixes.sql** - Apply critical schema fixes
- **enable_cost_tracking.sql** - Enable cost tracking functionality
- **fix-critical-schema-issues.sql** - Fix critical schema issues
- **fix_cost_tracking_functions.sql** - Fix cost tracking function definitions
- **fix_uuid_format.sql** - Fix UUID format issues
- **fix_uuid_format_clean.sql** - Clean UUID format fixes
- **fix_submissions_uuid_format.sql** - Fix UUID format in submissions table

### Data Management Scripts
- **agno_validation_inserts.sql** - Insert validation data for agno
- **create_proper_opportunity_links.sql** - Create proper opportunity table links
- **link_all_remaining_submissions.sql** - Link remaining submissions to proper entities
- **populate_missing_submission_ids.sql** - Populate missing submission IDs
- **explore_integration_results.sql** - Explore integration results

### Testing & Validation Scripts
- **test_cost_tracking_functions.sql** - Test cost tracking functions
- **test_deduplication_pipeline.sql** - Test deduplication pipeline functionality

## Usage

Use with caution! Database scripts perform destructive operations. Always backup your data before running migrations or cleanup scripts.

## Categories

- **Migration Scripts**: Use for schema changes and data migrations
- **Data Management**: Use for data population and linking operations
- **Testing & Validation**: Use for testing functionality and validating results
- **Maintenance**: Use for routine database maintenance and cleanup
