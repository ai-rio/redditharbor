#!/usr/bin/env python3
"""
Diagnostic test for batch processing hang issue.
Adds instrumentation at every component boundary to identify the exact hang location.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

print("=" * 80)
print("DIAGNOSTIC BATCH PROCESSING TEST")
print("=" * 80)
print(f"Start time: {datetime.now()}")
print()

# Phase 1: Import verification
print("PHASE 1: Import Verification")
print("-" * 80)

checkpoints = []

def checkpoint(name, data=None):
    """Record a checkpoint with timestamp"""
    ts = datetime.now()
    checkpoints.append({"name": name, "timestamp": ts, "data": data})
    print(f"✓ [{ts.strftime('%H:%M:%S.%f')[:-3]}] {name}")
    if data:
        print(f"  Data: {data}")
    return ts

checkpoint("Starting diagnostic test")

try:
    checkpoint("Importing tqdm")
    from tqdm import tqdm
except ImportError:
    print("✗ tqdm not available")
    sys.exit(1)

try:
    checkpoint("Importing Supabase client")
    from supabase import create_client
except Exception as e:
    print(f"✗ Supabase import failed: {e}")
    sys.exit(1)

try:
    checkpoint("Importing config")
    from config import SUPABASE_KEY, SUPABASE_URL
except Exception as e:
    print(f"✗ Config import failed: {e}")
    sys.exit(1)

try:
    checkpoint("Importing agent tools")
    from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
    from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
except Exception as e:
    print(f"✗ Agent tools import failed: {e}")
    sys.exit(1)

try:
    checkpoint("Importing batch_opportunity_scoring module")
    sys.path.append(str(project_root / 'scripts' / 'core'))
    from batch_opportunity_scoring import (
        process_batch,
        format_submission_for_agent,
        fetch_submissions
    )
except Exception as e:
    print(f"✗ batch_opportunity_scoring import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

checkpoint("All imports successful")

# Phase 2: Database connection
print("\nPHASE 2: Database Connection")
print("-" * 80)

try:
    checkpoint("Creating Supabase client")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    checkpoint("Fetching submissions from database")
    response = supabase.table('app_opportunities_trust').select('*').execute()
    submissions = response.data
    checkpoint("Submissions fetched", f"{len(submissions)} submissions")

except Exception as e:
    print(f"✗ Database connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Phase 3: Agent initialization
print("\nPHASE 3: Agent Initialization")
print("-" * 80)

try:
    checkpoint("Initializing OpportunityAnalyzerAgent")
    agent = OpportunityAnalyzerAgent()

    checkpoint("Initializing EnhancedLLMProfiler")
    profiler = EnhancedLLMProfiler()

    checkpoint("Agents initialized successfully")
except Exception as e:
    print(f"✗ Agent initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Phase 4: Test with increasing batch sizes
print("\nPHASE 4: Batch Processing Test (Progressive Size)")
print("-" * 80)

test_sizes = [1, 5, 10, 25, 46]  # Test with progressively larger batches
score_threshold = 30.0

for test_size in test_sizes:
    if test_size > len(submissions):
        print(f"Skipping test size {test_size} (not enough submissions)")
        continue

    print(f"\n--- Testing with {test_size} submissions ---")
    batch = submissions[:test_size]

    checkpoint(f"Starting process_batch with {test_size} submissions")

    try:
        # Add timeout monitoring
        start_time = time.time()

        print(f"  Calling process_batch(batch={len(batch)}, threshold={score_threshold})...")
        print(f"  If this hangs, the issue is in process_batch")

        # Call process_batch with instrumentation
        results, scored_opps, ai_profiles_count = process_batch(
            batch,
            agent,
            1,  # batch_number
            profiler,
            score_threshold
        )

        elapsed = time.time() - start_time
        checkpoint(
            f"process_batch completed for {test_size} submissions",
            f"elapsed={elapsed:.2f}s, results={len(results)}, ai_profiles={ai_profiles_count}"
        )

        print(f"  ✅ SUCCESS: {test_size} submissions processed in {elapsed:.2f}s")
        print(f"     Results: {len(results)}, AI profiles: {ai_profiles_count}")

    except KeyboardInterrupt:
        print(f"\n✗ HANG DETECTED at batch size {test_size}")
        print(f"  Time elapsed before interrupt: {time.time() - start_time:.2f}s")
        print("\nCheckpoint history:")
        for cp in checkpoints[-10:]:  # Show last 10 checkpoints
            print(f"  [{cp['timestamp'].strftime('%H:%M:%S.%f')[:-3]}] {cp['name']}")
        print("\n⚠️  THE HANG OCCURS INSIDE process_batch")
        print("    Next step: Add instrumentation inside process_batch function")
        sys.exit(1)

    except Exception as e:
        print(f"✗ ERROR at batch size {test_size}: {e}")
        import traceback
        traceback.print_exc()
        break

# Phase 5: Summary
print("\nPHASE 5: Summary")
print("=" * 80)
print(f"End time: {datetime.now()}")
print("\nCheckpoint timeline:")
for i, cp in enumerate(checkpoints):
    if i > 0:
        delta = (cp['timestamp'] - checkpoints[i-1]['timestamp']).total_seconds()
        print(f"  {cp['name']}: {delta:.3f}s")
    else:
        print(f"  {cp['name']}: 0.000s")

print("\n✅ ALL TESTS PASSED - No hang detected")
print("=" * 80)
