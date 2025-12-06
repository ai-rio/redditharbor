#!/usr/bin/env python3
"""
Test script to verify data persistence from Agno analysis
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
from config.settings import get_settings

def test_data_persistence():
    """Test that Agno analysis results are actually stored in the database"""
    print("=" * 60)
    print("TESTING DATA PERSISTENCE")
    print("=" * 60)

    # Create test submission
    test_submission = RedditSubmission(
        id="persistence-test-2024",
        title="Need accounting software for our construction business",
        text="We're a small construction company with 15 employees. Currently using QuickBooks (too complex at $600/year) and Excel spreadsheets. Need something simple for job costing, invoicing, and payroll. Budget around $100/month. We need mobile app support for field workers.",
        author="construction_owner",
        upvotes=34,
        downvotes=2,
        score=32,
        comments_count=19,
        subreddit="Entrepreneur",
        created_utc=datetime.now(timezone.utc),
        permalink="https://reddit.com/r/Entrepreneur/comments/persistence-test-2024/"
    )

    print(f"Test submission: {test_submission.title}")
    print(f"Content length: {len(test_submission.text)} characters")
    print()

    # Initialize analyzer
    print("Initializing analyzer...")
    analyzer = AgnoOpportunityAnalyzer(
        enable_agentops=True,
        enable_embeddings=False
    )
    print("✓ Analyzer initialized")
    print()

    # Run analysis
    print("Running analysis...")
    analysis_start = datetime.now()
    result = analyzer.analyze_submission(test_submission)
    analysis_time = (datetime.now() - analysis_start).total_seconds()

    print(f"✓ Analysis completed in {analysis_time:.2f}s")
    print(f"App Title: {result.app_idea.title}")
    print(f"Final Score: {result.final_score:.1f}")
    print(f"Confidence: {result.confidence_score:.1f}%")
    print()

    # Store results in database
    print("Storing results in database...")
    loader = OnlyMapsDatabaseLoader()

    # Prepare data for storage
    analyses = [result]
    reddit_submissions = [test_submission]

    try:
        loader.store_analyses(analyses, reddit_submissions)
        print("✓ Data stored successfully")
        print()

        # Verify data was stored
        print("Verifying data persistence...")
        settings = get_settings()

        # Query the database directly
        from supabase import create_client

        supabase = create_client(
            settings.supabase_url,
            settings.supabase_key
        )

        # Query the latest record
        response = supabase.table('opportunities') \
            .select('*') \
            .eq('submission_id', test_submission.id) \
            .execute()

        if response.data:
            stored = response.data[0]
            print("✅ DATA SUCCESSFULLY STORED!")
            print(f"   - Record ID: {stored['id']}")
            print(f"   - Submission ID: {stored['submission_id']}")
            print(f"   - App Title: {stored['app_title']}")
            print(f"   - Final Score: {stored['final_score']}")
            print(f"   - Trust Level: {stored['trust_level']}")
            print(f"   - Created At: {stored['created_at']}")

            # Check if Agno fields are populated
            agno_fields = [
                'agno_wtp_score',
                'agno_segment_confidence',
                'agno_price_potential',
                'agno_behavior_score',
                'agno_consensus_confidence',
                'agno_segment_type',
                'agno_agents_count',
                'agno_analysis_cost_usd',
                'agno_agent_metadata',
                'agno_validation_status'
            ]

            print("\n   Agno Fields Status:")
            agno_populated = 0
            for field in agno_fields:
                value = stored.get(field)
                if value is not None and value != '':
                    print(f"   ✅ {field}: {value}")
                    agno_populated += 1
                else:
                    print(f"   ❌ {field}: NULL/Empty")

            print(f"\n   Agno Fields Populated: {agno_populated}/{len(agno_fields)}")

            return True
        else:
            print("❌ DATA NOT FOUND in database after storage!")
            return False

    except Exception as e:
        print(f"❌ Failed to store data: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_before():
    """Check database state before test"""
    print("Checking database state before test...")

    settings = get_settings()
    from supabase import create_client

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_key
    )

    # Count total opportunities
    response = supabase.table('opportunities').select('count', count='exact').execute()
    count = response.count if hasattr(response, 'count') else 0
    print(f"   Current opportunities count: {count}")

    # Check for our test ID
    response = supabase.table('opportunities') \
        .select('id, submission_id, created_at') \
        .eq('submission_id', 'persistence-test-2024') \
        .execute()

    if response.data:
        print(f"   ⚠️  Test record already exists: {response.data[0]['id']}")
        print("   Deleting old test record...")
        supabase.table('opportunities') \
            .delete() \
            .eq('submission_id', 'persistence-test-2024') \
            .execute()
        print("   ✓ Old test record deleted")
    else:
        print("   ✓ No existing test record found")

    print()

if __name__ == "__main__":
    print("RedditHarbor Pipeline v3 - Data Persistence Test")
    print("=" * 60)
    print()

    # Check database state
    check_database_before()

    # Run persistence test
    if test_data_persistence():
        print("\n✅ DATA PERSISTENCE TEST PASSED!")
        print("Analysis results are being properly stored in the database.")
        sys.exit(0)
    else:
        print("\n❌ DATA PERSISTENCE TEST FAILED!")
        print("Analysis results are NOT being stored in the database.")
        sys.exit(1)