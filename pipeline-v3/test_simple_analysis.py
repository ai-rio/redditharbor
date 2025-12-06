#!/usr/bin/env python3
"""
Simple test to verify Agno analysis works and returns results
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from transform.agno_analyzer import AgnoOpportunityAnalyzer
from models.reddit import RedditSubmission
from load.onlymaps_database import OnlyMapsDatabaseLoader

def test_simple_analysis():
    """Test Agno analysis and database storage directly"""
    print("=" * 60)
    print("SIMPLE ANALYSIS AND STORAGE TEST")
    print("=" * 60)

    # Create test submission
    test_submission = RedditSubmission(
        id="simple-test-2024",
        title="Need CRM for consulting business",
        text="We're a consulting firm with 10 consultants. Using spreadsheets to track clients and projects. Need client management, project tracking, time tracking, and invoicing. Budget $200/month. Currently looking at solutions.",
        author="consulting_owner",
        upvotes=45,
        downvotes=1,
        score=44,
        comments_count=12,
        subreddit="Entrepreneur",
        created_utc=datetime.now(timezone.utc),
        permalink="https://reddit.com/r/Entrepreneur/comments/simple-test-2024/"
    )

    print(f"Analyzing: {test_submission.title}")
    print()

    # Initialize analyzer
    analyzer = AgnoOpportunityAnalyzer(
        enable_agentops=False,  # Disable to reduce complexity
        enable_embeddings=False
    )

    # Run analysis
    print("Running analysis...")
    result = analyzer.analyze_submission(test_submission)

    # Check if we got a valid result
    if hasattr(result, 'final_score'):
        print("✅ Analysis completed successfully!")
        print(f"   Final Score: {result.final_score}")
        print(f"   App Title: {result.app_idea.title}")
        print(f"   Confidence: {result.confidence_score}")
        print()

        # Now store in database
        print("Storing in database...")
        loader = OnlyMapsDatabaseLoader()

        # Store the analysis
        analyses = [result]
        reddit_submissions = [test_submission]

        try:
            loader.store_analyses(analyses, reddit_submissions)
            print("✅ Data stored successfully!")

            # Verify with direct database query
            print("\nVerifying storage...")
            settings = loader.settings
            from supabase import create_client

            supabase = create_client(
                settings.supabase_url,
                settings.supabase_key
            )

            # Query the stored record
            response = supabase.table('opportunities') \
                .select('*') \
                .eq('submission_id', test_submission.id) \
                .execute()

            if response.data:
                stored = response.data[0]
                print("✅ Data verified in database!")
                print(f"   ID: {stored['id']}")
                print(f"   App Title: {stored['app_title']}")
                print(f"   Final Score: {stored['final_score']}")
                print(f"   Trust Level: {stored['trust_level']}")

                # Show all fields that were populated
                print("\nAll stored fields:")
                for key, value in stored.items():
                    if value is not None and value != '':
                        if isinstance(value, str) and len(value) > 50:
                            print(f"   {key}: {value[:50]}...")
                        else:
                            print(f"   {key}: {value}")

                return True
            else:
                print("❌ Data not found in database after storage!")
                return False

        except Exception as e:
            print(f"❌ Failed to store data: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("❌ Analysis failed - no valid result returned")
        return False

if __name__ == "__main__":
    print("RedditHarbor Pipeline v3 - Simple Analysis Test")
    print("=" * 60)
    print()

    if test_simple_analysis():
        print("\n✅ TEST PASSED - Data is being stored!")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - Data storage issue!")
        sys.exit(1)