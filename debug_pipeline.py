#!/usr/bin/env python3
"""Debug pipeline test"""

import sys
from pathlib import Path

# Add paths
test_utils_path = Path('scripts/testing/integration').resolve()
project_root = Path('.').resolve()
sys.path.insert(0, str(test_utils_path))
sys.path.insert(1, str(project_root))

# Import settings
import importlib.util
spec = importlib.util.spec_from_file_location("main_config", project_root / "config" / "settings.py")
main_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_config)
SUPABASE_URL = main_config.SUPABASE_URL
SUPABASE_KEY = main_config.SUPABASE_KEY

from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource
from supabase import create_client

print("Creating pipeline...")

# Create Supabase client
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create configuration exactly like the test
config = PipelineConfig(
    data_source=DataSource.DATABASE,
    limit=1,
    enable_profiler=True,
    enable_opportunity_scoring=True,
    enable_monetization=True,
    enable_trust=True,
    enable_market_validation=True,
    ai_profile_threshold=0.0,
    monetization_threshold=0.0,
    market_validation_threshold=0.0,
    return_data=True,
    dry_run=False,
    supabase_client=supabase_client,
    source_config={
        "table_name": "submissions",
        "filter_column": "submission_id",
        "filter_value": "hybrid_1",
    }
)

pipeline = OpportunityPipeline(config)

print(f"Services loaded: {len(pipeline.services)}")
print(f"Service names: {list(pipeline.services.keys())}")

print("\nRunning pipeline...")
result = pipeline.run()

print(f"Pipeline success: {result.get('success', False)}")
print(f"Data returned: {len(result.get('data', []))} items")

if result.get('data'):
    print("\nFirst enriched submission:")
    submission = result['data'][0]
    print(f"Keys: {list(submission.keys())}")