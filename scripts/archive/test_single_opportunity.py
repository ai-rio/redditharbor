#!/usr/bin/env python3
"""
Test Single Opportunity Processing
Debug script to process just one opportunity and identify where it gets stuck
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
from core.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from core.ai_profiler import AIProfiler
import os

def main():
    print("=" * 60)
    print("TESTING SINGLE OPPORTUNITY PROCESSING")
    print("=" * 60)

    # Connect to database
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get top opportunity
    response = supabase.table('workflow_results').select('*').gte('final_score', 34.0).order('final_score', desc=True).limit(1).execute()
    opp = response.data[0] if response.data else None

    if not opp:
        print("No opportunities found")
        return

    print(f"Processing: {opp.get('opportunity_id')} - Score: {opp.get('final_score')}")

    # Get Reddit data
    reddit_response = supabase.table('app_opportunities_trust').select('*').eq('submission_id', opp['opportunity_id'][4:]).execute()
    reddit_data = reddit_response.data[0] if reddit_response.data else None

    if not reddit_data:
        print("No Reddit data found")
        return

    print(f"Reddit: {reddit_data.get('title')[:50]}...")

    # Test AI profiler
    print("\n1. Testing AI Profiler...")
    try:
        profiler = AIProfiler()
        print("   ✓ AI Profiler initialized")

        # Prepare post data
        post_data = {
            'id': opp['opportunity_id'][4:],
            'title': reddit_data.get('title', ''),
            'selftext': reddit_data.get('selftext', ''),
            'subreddit': reddit_data.get('subreddit', ''),
            'author': 'test_user'
        }

        print("   About to call generate_profile...")
        ai_profile = profiler.generate_profile(post_data)
        print(f"   ✓ AI Profile generated: {ai_profile.get('app_name', 'No name')}")
        print(f"   Functions: {len(ai_profile.get('functions', []))}")

    except Exception as e:
        print(f"   ❌ AI Profiler failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n✅ Single opportunity processing completed successfully!")

if __name__ == "__main__":
    main()