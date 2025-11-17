#!/usr/bin/env python3
"""
Test the exact first batch call that's causing the hang
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from config import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client

def main():
    print("=" * 60)
    print("TESTING EXACT FIRST BATCH CALL")
    print("=" * 60)

    # Get submissions exactly like the batch script
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table('app_opportunities_trust').select('*').execute()
        submissions = response.data
        print(f"✅ Got {len(submissions)} submissions")
    except Exception as e:
        print(f"❌ Failed to get submissions: {e}")
        return

    # Remove duplicates exactly like the batch script
    seen_content = set()
    unique_submissions = []
    duplicates_removed = 0

    for sub in submissions:
        content = f"{sub.get('title', '')} {sub.get('selftext', '')}"
        content_hash = hash(content[:500])  # First 500 chars

        if content_hash not in seen_content:
            seen_content.add(content_hash)
            unique_submissions.append(sub)
        else:
            duplicates_removed += 1

    print(f"✅ Removed {duplicates_removed} duplicates, {len(unique_submissions)} unique")

    # Initialize agents exactly like the batch script
    try:
        agent = OpportunityAnalyzerAgent()
        profiler = EnhancedLLMProfiler()
        print("✅ Agents initialized")
    except Exception as e:
        print(f"❌ Failed to initialize agents: {e}")
        return

    # Test the exact first batch call
    print(f"\nTesting first batch call...")
    batch_size = 100
    batch = unique_submissions[0:batch_size]
    batch_num = 1
    score_threshold = 30.0

    print(f"Batch: {len(batch)} submissions")
    print(f"About to call process_batch...")

    try:
        # Import and call process_batch from the actual script
        sys.path.append(str(project_root / 'scripts' / 'core'))
        from batch_opportunity_scoring import process_batch

        print("process_batch imported, calling it now...")
        results, scored_opps, ai_profiles_count = process_batch(
            batch, agent, batch_num, profiler, score_threshold
        )

        print(f"✅ First batch completed successfully!")
        print(f"   Results: {len(results)}")
        print(f"   Scored opportunities: {len(scored_opps)}")
        print(f"   AI profiles: {ai_profiles_count}")

    except Exception as e:
        print(f"❌ First batch failed: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()