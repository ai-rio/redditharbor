# DLT Integration Guide for RedditHarbor

## Overview

This guide provides a comprehensive plan for integrating **dlt (data load tool)** into RedditHarbor to automate Reddit data collection, enable incremental loading, and streamline the problem-first opportunity research pipeline.

---

## What is DLT?

**dlt** is an open-source Python library that automates data loading from various sources into well-structured datasets. It handles:

- Automatic schema inference and evolution
- Incremental loading (fetch only new/modified data)
- Built-in error handling and retry logic
- Support for multiple destinations (Supabase, DuckDB, BigQuery, etc.)
- Pipeline orchestration and monitoring

**Key Benefits for RedditHarbor:**
- **80-90% reduction in API calls** through incremental loading
- **Automatic schema management** for nested Reddit data
- **Built-in rate limiting** and error recovery
- **Production-ready** with Airflow integration
- **Simplified code** - 30-40 lines vs 100+ manual implementation

---

## Current Architecture vs DLT Architecture

### Current Architecture

```
Reddit API → Manual Collection Script → Error Handling → Database Insertion
             (100+ lines of code)        (Manual retry)   (Manual schema)
                    ↓
            Supabase Storage
                    ↓
            AI Analysis Script
```

**Pain Points:**
- Duplicate API calls on each run
- Manual error handling and retry logic
- Schema changes require code updates
- No automatic incremental tracking
- High maintenance burden

### DLT Architecture

```
Reddit API → DLT Pipeline → Automatic Schema → Supabase Storage
             (30-40 lines)   (Evolution)       (Incremental)
                    ↓
            Built-in Monitoring
                    ↓
            AI Analysis Pipeline
```

**Improvements:**
- Incremental loading by default
- Automatic error handling
- Schema evolution without code changes
- Built-in cursor management
- Production-ready monitoring

---

## Implementation Phases

### Phase 1: Setup and Testing (Week 1)

#### 1.1 Install DLT with Supabase Support

```bash
# Add dlt to requirements.txt
echo "dlt[supabase]>=1.0.0" >> requirements.txt

# Install with UV
uv pip install -r requirements.txt
```

#### 1.2 Create DLT Configuration

Create `config/dlt_settings.py`:

```python
"""
DLT pipeline configuration for RedditHarbor.

This module configures dlt pipelines for Reddit data collection,
including destination setup, incremental loading strategies, and
schema evolution policies.
"""

import os
from typing import Dict, Any

# DLT destination configuration
DLT_DESTINATION = "supabase"
DLT_DATASET_NAME = "reddit_harbor"

# Supabase connection from existing config
DLT_SUPABASE_CONFIG = {
    "credentials": {
        "project_url": os.getenv("SUPABASE_URL"),
        "api_key": os.getenv("SUPABASE_KEY")
    }
}

# Pipeline configuration
DLT_PIPELINE_CONFIG = {
    "pipeline_name": "reddit_harbor_collection",
    "destination": DLT_DESTINATION,
    "dataset_name": DLT_DATASET_NAME,
}

# Incremental loading configuration
DLT_INCREMENTAL_CONFIG = {
    "submissions": {
        "cursor_column": "created_utc",
        "primary_key": "id",
        "write_disposition": "merge"
    },
    "comments": {
        "cursor_column": "created_utc",
        "primary_key": "id",
        "write_disposition": "merge"
    }
}

# Schema evolution policy
DLT_SCHEMA_CONFIG = {
    "allow_new_columns": True,
    "allow_new_tables": True,
    "allow_column_type_changes": False,  # Strict for production
}
```

#### 1.3 Create Simple Test Pipeline

Create `scripts/test_dlt_pipeline.py`:

```python
"""
Test DLT pipeline for Reddit data collection.

This script validates DLT integration by collecting a small sample
of Reddit data and loading it into Supabase.
"""

import dlt
from dlt.sources.rest_api import rest_api_source
from config.dlt_settings import DLT_PIPELINE_CONFIG, DLT_SUPABASE_CONFIG

def test_reddit_collection():
    """Test basic Reddit data collection with DLT."""

    # Create pipeline
    pipeline = dlt.pipeline(**DLT_PIPELINE_CONFIG)

    # Configure Reddit REST API source
    reddit_source = rest_api_source({
        "client": {
            "base_url": "https://oauth.reddit.com",
            "auth": {
                "type": "bearer",
                "token": os.getenv("REDDIT_ACCESS_TOKEN")
            }
        },
        "resources": [
            {
                "name": "submissions",
                "endpoint": {
                    "path": "r/opensource/new",
                    "params": {
                        "limit": 10  # Small test sample
                    }
                }
            }
        ]
    })

    # Run pipeline
    load_info = pipeline.run(reddit_source)

    # Validate results
    print(f"✓ Loaded {load_info.metrics.table_counts} rows")
    print(f"✓ Schema: {load_info.schema.tables.keys()}")
    print(f"✓ Destination: {pipeline.destination}")

    return load_info

if __name__ == "__main__":
    test_reddit_collection()
```

#### 1.4 Run Test and Validate

```bash
# Run test pipeline
python scripts/test_dlt_pipeline.py

# Verify data in Supabase Studio
# http://127.0.0.1:54323
```

**Success Criteria:**
- ✓ 10 submissions loaded successfully
- ✓ Schema auto-created in Supabase
- ✓ No errors in pipeline execution
- ✓ Data visible in Supabase Studio

---

### Phase 2: Problem-First Collection with Incremental Loading (Week 1-2)

#### 2.1 Create DLT-Based Collection Pipeline

Create `core/dlt_collection.py`:

```python
"""
DLT-based Reddit data collection for problem-first approach.

This module replaces manual collection logic with DLT pipelines,
enabling incremental loading, automatic schema management, and
built-in error handling.
"""

import dlt
from typing import List, Optional
from datetime import datetime
from config.dlt_settings import (
    DLT_PIPELINE_CONFIG,
    DLT_INCREMENTAL_CONFIG
)

# Problem detection keywords (from existing filter logic)
PROBLEM_KEYWORDS = [
    "struggle", "problem", "frustrated", "wish", "can't", "difficult",
    "annoying", "hate", "pain", "slow", "expensive", "broken", "error",
    # ... (import from existing scripts/filter_problems.py)
]

def create_problem_first_source(subreddits: List[str], limit: int = 100):
    """
    Create DLT source for problem-first Reddit collection.

    Args:
        subreddits: List of subreddit names to collect from
        limit: Maximum posts per subreddit

    Returns:
        DLT source configured for incremental problem post collection
    """

    resources = []

    for subreddit in subreddits:
        # Configure resource for each subreddit
        resource = {
            "name": f"submissions_{subreddit}",
            "endpoint": {
                "path": f"r/{subreddit}/new",
                "params": {
                    "limit": limit,
                    # DLT handles incremental 'after' parameter automatically
                }
            },
            "primary_key": "id",
            "write_disposition": "merge",
            # Filter for problem keywords
            "include": {
                "title": PROBLEM_KEYWORDS,  # DLT can filter on response
                "selftext": PROBLEM_KEYWORDS
            }
        }
        resources.append(resource)

    # Create REST API source
    source = rest_api_source({
        "client": {
            "base_url": "https://oauth.reddit.com",
            "auth": {
                "type": "bearer",
                "token": os.getenv("REDDIT_ACCESS_TOKEN")
            }
        },
        "resources": resources
    })

    # Apply incremental loading hints
    for resource_name in [r["name"] for r in resources]:
        resource = getattr(source, resource_name)
        resource.apply_hints(
            incremental=dlt.sources.incremental(
                "created_utc",
                initial_value=datetime(2025, 1, 1).timestamp()
            ),
            primary_key="id"
        )

    return source


def collect_problem_posts(
    subreddits: List[str],
    limit: int = 100,
    full_refresh: bool = False
) -> dlt.common.pipeline.LoadInfo:
    """
    Collect problem posts from Reddit using DLT.

    Args:
        subreddits: List of subreddit names
        limit: Posts per subreddit (only applies to full refresh)
        full_refresh: If True, ignore incremental state and reload all

    Returns:
        LoadInfo object with pipeline execution details
    """

    # Create pipeline
    pipeline = dlt.pipeline(**DLT_PIPELINE_CONFIG)

    # Create problem-first source
    source = create_problem_first_source(subreddits, limit)

    # Run pipeline
    if full_refresh:
        # Clear state and reload
        pipeline.drop_state()

    load_info = pipeline.run(source)

    # Log results
    print(f"✓ Collection complete:")
    print(f"  - Rows loaded: {load_info.metrics.table_counts}")
    print(f"  - Tables: {list(load_info.schema.tables.keys())}")
    print(f"  - Incremental: {not full_refresh}")

    return load_info


if __name__ == "__main__":
    # Example: Collect from multiple subreddits
    subreddits = ["opensource", "SideProject", "productivity"]
    collect_problem_posts(subreddits, limit=200)
```

#### 2.2 Test Incremental Loading

```bash
# First run: Load all data
python -c "from core.dlt_collection import collect_problem_posts; \
collect_problem_posts(['opensource'], limit=50, full_refresh=True)"

# Second run: Only new data (should be 0-5 rows)
python -c "from core.dlt_collection import collect_problem_posts; \
collect_problem_posts(['opensource'], limit=50)"

# Verify incremental worked
python -c "import dlt; \
p = dlt.pipeline('reddit_harbor_collection', destination='supabase'); \
print(p.last_trace.steps)"
```

**Success Criteria:**
- ✓ First run loads 50 posts
- ✓ Second run loads only new posts (0-5)
- ✓ API calls reduced by 80%+
- ✓ Incremental state tracked automatically

---

### Phase 3: AI Insights Pipeline Integration (Week 2)

#### 3.1 Chain DLT Collection with AI Analysis

Create `scripts/dlt_opportunity_pipeline.py`:

```python
"""
End-to-end DLT pipeline: Reddit collection → AI analysis → Storage.

This pipeline chains problem-first collection with AI opportunity
generation, using DLT for both data loading and insights storage.
"""

import dlt
from core.dlt_collection import collect_problem_posts
from scripts.generate_opportunity_insights_openrouter import generate_insights

def run_opportunity_pipeline(subreddits: List[str], limit: int = 100):
    """
    Run complete opportunity research pipeline.

    Steps:
        1. Collect problem posts from Reddit (incremental)
        2. Generate AI insights for new posts
        3. Store insights in Supabase (merge on post_id)

    Args:
        subreddits: List of subreddit names
        limit: Max posts per subreddit (first run only)
    """

    # Step 1: Collect problem posts
    print("Step 1: Collecting problem posts...")
    collection_info = collect_problem_posts(subreddits, limit)

    # Step 2: Get newly loaded posts
    pipeline = dlt.pipeline("reddit_harbor_collection", destination="supabase")
    new_posts = pipeline.last_trace.steps[0].load_packages[0].data

    print(f"Step 2: Generating insights for {len(new_posts)} new posts...")
    insights = []

    for post in new_posts:
        insight = generate_insights(post)
        if insight:  # Only valid opportunities
            insights.append(insight)

    # Step 3: Store insights (merge to avoid duplicates)
    print(f"Step 3: Storing {len(insights)} insights...")
    insights_info = pipeline.run(
        insights,
        table_name="opportunity_analysis",
        write_disposition="merge",
        primary_key="post_id"
    )

    # Report results
    print("\n✓ Pipeline Complete:")
    print(f"  - Posts collected: {len(new_posts)}")
    print(f"  - Insights generated: {len(insights)}")
    print(f"  - Success rate: {len(insights)/len(new_posts)*100:.1f}%")

    return insights_info


if __name__ == "__main__":
    subreddits = ["opensource", "SideProject", "productivity"]
    run_opportunity_pipeline(subreddits, limit=100)
```

---

### Phase 4: Production Deployment with Airflow (Week 3)

#### 4.1 Create Airflow DAG

Create `.airflow/dags/reddit_opportunity_dag.py`:

```python
"""
Airflow DAG for scheduled Reddit opportunity collection.

Schedule: Daily at 2 AM UTC
Strategy: Incremental collection + AI analysis
Retention: Keep 90 days of pipeline state
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from dlt.helpers.airflow_helper import PipelineTasksGroup
from datetime import datetime, timedelta
import dlt

default_args = {
    'owner': 'redditharbor',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'reddit_opportunity_pipeline',
    default_args=default_args,
    description='Incremental Reddit data collection and AI analysis',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    catchup=False,
    max_active_runs=1,
)

# DLT task group
tasks = PipelineTasksGroup(
    "reddit_harbor_collection",
    use_data_folder=False,
    wipe_local_data=True
)

# Import pipeline function
from scripts.dlt_opportunity_pipeline import run_opportunity_pipeline

# Create DLT pipeline
pipeline = dlt.pipeline(
    pipeline_name="reddit_harbor_collection",
    destination="supabase",
    dataset_name="reddit_harbor"
)

# Add pipeline tasks
subreddits = ["opensource", "SideProject", "productivity", "freelance"]
tasks.add_run(
    pipeline,
    run_opportunity_pipeline(subreddits, limit=200),
    decompose="serialize",
    trigger_rule="all_done",
    retries=2,
)
```

#### 4.2 Test Airflow Integration

```bash
# Start Airflow
airflow standalone

# Trigger DAG manually
airflow dags trigger reddit_opportunity_pipeline

# Monitor execution
airflow dags list-runs -d reddit_opportunity_pipeline
```

---

## Migration Plan: Existing Scripts → DLT

### Scripts to Migrate

| Current Script | DLT Replacement | Priority |
|---------------|-----------------|----------|
| `scripts/collect_problem_posts.py` | `core/dlt_collection.py` | High |
| `scripts/generate_opportunity_insights_openrouter.py` | Chain with DLT pipeline | High |
| `scripts/filter_problems.py` | DLT include filters | Medium |
| Manual database insertion | DLT automatic loading | High |
| Error logging to `error_log/` | DLT built-in logging | Medium |

### Step-by-Step Migration

#### Step 1: Parallel Testing (Week 1)

Run both old and new pipelines side-by-side:

```bash
# Old pipeline (baseline)
python scripts/collect_problem_posts.py --subreddits opensource --limit 100

# New DLT pipeline (test)
python core/dlt_collection.py

# Compare results in Supabase Studio
# Verify row counts match
# Check schema consistency
```

#### Step 2: Incremental Migration (Week 2)

Gradually shift traffic to DLT:

- Day 1-2: 10% traffic to DLT (1 subreddit)
- Day 3-4: 50% traffic to DLT (2-3 subreddits)
- Day 5-7: 100% traffic to DLT (all subreddits)

#### Step 3: Deprecate Old Scripts (Week 3)

Once DLT is stable:

```bash
# Archive old scripts
mkdir archive/legacy-collection
mv scripts/collect_problem_posts.py archive/legacy-collection/
mv scripts/filter_problems.py archive/legacy-collection/

# Update documentation
# Remove old script references
# Add DLT documentation
```

---

## Performance Benchmarks

### Expected Improvements

| Metric | Before (Manual) | After (DLT) | Improvement |
|--------|----------------|-------------|-------------|
| API Calls (subsequent runs) | 1000 | 50-200 | 80-95% ↓ |
| Code Lines (collection) | 150 | 40 | 73% ↓ |
| Error Handling | Manual | Automatic | ✓ |
| Schema Updates | Manual | Automatic | ✓ |
| Incremental Tracking | None | Built-in | ✓ |
| Production Ready | No | Yes (Airflow) | ✓ |

### Benchmark Test Script

Create `scripts/benchmark_dlt_performance.py`:

```python
"""
Benchmark DLT performance vs manual collection.

Measures:
- API call reduction (incremental loading)
- Execution time
- Memory usage
- Error handling effectiveness
"""

import time
import tracemalloc
from core.dlt_collection import collect_problem_posts

def benchmark_incremental_loading():
    """Measure incremental loading performance."""

    subreddits = ["opensource"]

    # First run (full load)
    print("=== First Run (Full Load) ===")
    tracemalloc.start()
    start_time = time.time()

    info1 = collect_problem_posts(subreddits, limit=100, full_refresh=True)

    elapsed1 = time.time() - start_time
    memory1 = tracemalloc.get_traced_memory()[1] / 1024 / 1024  # MB
    rows1 = info1.metrics.table_counts

    print(f"Time: {elapsed1:.2f}s | Rows: {rows1} | Memory: {memory1:.2f}MB")
    tracemalloc.stop()

    # Second run (incremental)
    print("\n=== Second Run (Incremental) ===")
    tracemalloc.start()
    start_time = time.time()

    info2 = collect_problem_posts(subreddits, limit=100)

    elapsed2 = time.time() - start_time
    memory2 = tracemalloc.get_traced_memory()[1] / 1024 / 1024
    rows2 = info2.metrics.table_counts

    print(f"Time: {elapsed2:.2f}s | Rows: {rows2} | Memory: {memory2:.2f}MB")
    tracemalloc.stop()

    # Calculate improvements
    time_reduction = (1 - elapsed2/elapsed1) * 100
    row_reduction = (1 - rows2/rows1) * 100

    print(f"\n✓ Performance Improvements:")
    print(f"  - Time reduction: {time_reduction:.1f}%")
    print(f"  - API call reduction: {row_reduction:.1f}%")
    print(f"  - Memory efficiency: {memory1/memory2:.1f}x")

if __name__ == "__main__":
    benchmark_incremental_loading()
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Incremental Not Working

**Symptoms:** All data reloaded on every run

**Solution:**
```python
# Check incremental state
import dlt
pipeline = dlt.pipeline("reddit_harbor_collection", destination="supabase")
print(pipeline.state)  # Should show last_value for cursor

# Reset if corrupted
pipeline.drop_state()
```

#### Issue 2: Schema Conflicts

**Symptoms:** Type mismatch errors during loading

**Solution:**
```python
# Allow schema evolution
pipeline.run(source, schema_contract={"allow_new_columns": True})

# Or, refresh schema completely
pipeline.drop_schema()
pipeline.run(source)
```

#### Issue 3: Supabase Connection Errors

**Symptoms:** Auth failures, timeout errors

**Solution:**
```bash
# Verify Supabase is running
supabase status

# Check credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection
python -c "import dlt; dlt.pipeline(destination='supabase').destination_client()"
```

---

## Next Steps

1. ✓ Review this guide
2. Run Phase 1 test pipeline
3. Benchmark incremental loading
4. Migrate one script at a time
5. Deploy to Airflow for production

---

## References

- [DLT Documentation](https://dlthub.com/docs)
- [DLT Incremental Loading Guide](https://dlthub.com/docs/general-usage/incremental-loading)
- [DLT Supabase Destination](https://dlthub.com/docs/dlt-ecosystem/destinations/supabase)
- [RedditHarbor Architecture Docs](../architecture/)

---

*Last Updated: 2025-01-06*
*Status: Ready for implementation*
