#!/usr/bin/env python3
"""
Test the exact agent.analyze_opportunity call that's causing the hang
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent
from config import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client

def main():
    print("=" * 60)
    print("TESTING AGENT ANALYZE CALL")
    print("=" * 60)

    # Get first submission
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table('app_opportunities_trust').select('*').limit(1).execute()
        submission = response.data[0]
        print(f"✅ Got submission: {submission.get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"❌ Failed to get submission: {e}")
        return

    # Initialize agent
    try:
        agent = OpportunityAnalyzerAgent()
        print("✅ Agent initialized")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return

    # Test format_submission_for_agent function
    print(f"\nTesting format_submission_for_agent...")
    try:
        # Import the function
        sys.path.append(str(project_root / 'scripts' / 'core'))
        from batch_opportunity_scoring import format_submission_for_agent

        formatted = format_submission_for_agent(submission)
        print(f"✅ Formatted submission: {formatted.get('title', 'No title')[:50]}...")
        print(f"   Keys: {list(formatted.keys())}")

    except Exception as e:
        print(f"❌ format_submission_for_agent failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test the agent call that's hanging
    print(f"\nTesting agent.analyze_opportunity...")
    print("About to call agent.analyze_opportunity...")

    try:
        analysis = agent.analyze_opportunity(formatted)
        print(f"✅ Agent analysis completed!")
        print(f"   Final score: {analysis.get('final_score', 0)}")
        print(f"   Keys: {list(analysis.keys())}")

    except Exception as e:
        print(f"❌ Agent analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()