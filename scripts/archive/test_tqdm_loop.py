#!/usr/bin/env python3
"""
Test tqdm loop specifically to see if it causes the hang
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

try:
    from tqdm import tqdm
    print("✅ tqdm imported successfully")
except ImportError:
    print("❌ tqdm not available")
    sys.exit(1)

def main():
    print("=" * 60)
    print("TESTING TQDM LOOP BEHAVIOR")
    print("=" * 60)

    # Get submissions
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table('app_opportunities_trust').select('*').limit(46).execute()
        submissions = response.data
        print(f"✅ Got {len(submissions)} submissions")
    except Exception as e:
        print(f"❌ Failed to get submissions: {e}")
        return

    # Initialize agents
    try:
        agent = OpportunityAnalyzerAgent()
        profiler = EnhancedLLMProfiler()
        print("✅ Agents initialized")
    except Exception as e:
        print(f"❌ Failed to initialize agents: {e}")
        return

    # Test tqdm loop with small batch
    print(f"\nTesting tqdm loop with {len(submissions)} submissions...")
    batch_size = 46
    processed = 0

    try:
        for i in tqdm(range(0, len(submissions), batch_size), desc="Processing batches", unit="batch"):
            batch = submissions[i:i+batch_size]
            print(f"\nStarting batch {i//batch_size + 1} with {len(batch)} items...")

            # Process each item in batch
            for j, submission in enumerate(batch):
                try:
                    print(f"  Processing item {j+1}: {submission.get('title', 'No title')[:30]}...")

                    # Skip AI profiling for now (just analysis)
                    analysis = agent.analyze_opportunity({
                        'title': submission.get('title', ''),
                        'text': submission.get('selftext', ''),
                        'subreddit': submission.get('subreddit', ''),
                        'score': 35.0
                    })

                    processed += 1
                    print(f"  ✅ Item {j+1} processed successfully")

                except Exception as e:
                    print(f"  ❌ Item {j+1} failed: {e}")

            print(f"✅ Batch {i//batch_size + 1} completed")

    except Exception as e:
        print(f"❌ TQDM loop failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"\n✅ TQDM loop completed successfully!")
    print(f"   Total processed: {processed}")

if __name__ == "__main__":
    main()