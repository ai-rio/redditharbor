# Test Infrastructure Scripts

This directory contains test scripts that were used during the DLT integration and system development phase. These scripts validated the data pipeline, connection handling, and incremental loading mechanisms.

## Scripts

### test_dlt_connection.py
- **Purpose:** Tests basic DLT connection to Supabase
- **Status:** Archived after DLT integration completion
- **Reason:** Infrastructure validated, no longer needed for daily operations

### test_dlt_pipeline.py
- **Purpose:** Tests the DLT data pipeline end-to-end
- **Status:** Archived after successful pipeline validation
- **Reason:** Pipeline now production-ready, test script superseded by `final_system_test.py`

### parallel_test_dlt.py
- **Purpose:** Tests parallel DLT operations and threading
- **Status:** Archived after parallel processing validation
- **Reason:** Concurrency mechanisms validated and implemented in production scripts

### test_dlt_with_praw.py
- **Purpose:** Tests DLT integration with PRAW (Python Reddit API Wrapper)
- **Status:** Archived after successful PRAW-DLT integration
- **Reason:** Integration confirmed working, superseded by production collectors

### test_incremental_loading.py
- **Purpose:** Tests incremental data loading mechanisms
- **Status:** Archived after incremental loading implementation
- **Reason:** Incremental loading now part of production pipeline

### test_scanner.py
- **Purpose:** Simple subreddit scanner test
- **Status:** Archived - functionality integrated into production scripts
- **Reason:** Scanner logic now part of `collect_commercial_data.py`

## Usage

These scripts are preserved for reference if troubleshooting similar issues in the future. They demonstrate:
- Connection handling patterns
- Pipeline testing approaches
- Integration testing between PRAW and DLT
- Incremental loading validation

To reactivate for debugging:
```bash
cp /home/carlos/projects/redditharbor/archive/archive/test_infrastructure/[script_name] /home/carlos/projects/redditharbor/scripts/
```
