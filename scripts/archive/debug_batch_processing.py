#!/usr/bin/env python3
"""
Debug Batch Processing Step by Step
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
    print("DEBUGGING BATCH PROCESSING STEP BY STEP")
    print("=" * 60)

    # Step 1: Connect to database
    print("\n1. Testing database connection...")
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table('app_opportunities_trust').select('count', count='exact').execute()
        print(f"   ✅ Database connected: {response.count} records")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return

    # Step 2: Get submissions
    print("\n2. Fetching submissions...")
    try:
        response = supabase.table('app_opportunities_trust').select('*').limit(3).execute()
        submissions = response.data
        print(f"   ✅ Fetched {len(submissions)} submissions")
    except Exception as e:
        print(f"   ❌ Fetch failed: {e}")
        return

    # Step 3: Initialize agents
    print("\n3. Initializing agents...")
    try:
        agent = OpportunityAnalyzerAgent()
        profiler = EnhancedLLMProfiler()
        print(f"   ✅ Agent initialized: {type(agent).__name__}")
        print(f"   ✅ Profiler initialized: {type(profiler).__name__}")
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        return

    # Step 4: Process one submission
    print("\n4. Processing single submission...")
    try:
        submission = submissions[0]
        print(f"   Processing: {submission.get('title', 'No title')[:50]}...")

        # Analyze
        print("   Running opportunity analysis...")
        analysis = agent.analyze_opportunity({
            'title': submission.get('title', ''),
            'text': submission.get('selftext', ''),
            'subreddit': submission.get('subreddit', ''),
            'score': 35.0
        })
        print(f"   ✅ Analysis complete: score {analysis.get('final_score', 0)}")

    except Exception as e:
        print(f"   ❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 5: Test AI profiling
    print("\n5. Testing AI profiling...")
    try:
        print("   Calling AI profiler...")
        profile = profiler.generate_app_profile(
            title=submission.get('title', ''),
            subreddit=submission.get('subreddit', ''),
            score=35.0,
            text=submission.get('selftext', '')
        )
        print(f"   ✅ AI profiling complete: {profile.get('app_name', 'No name')}")

    except Exception as e:
        print(f"   ❌ AI profiling failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n✅ All steps completed successfully!")

if __name__ == "__main__":
    main()