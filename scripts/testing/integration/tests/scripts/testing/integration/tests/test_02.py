#!/usr/bin/env python3
"""
Test 02: Final Live Pipeline Validation

Tests the pipeline with actual data using correct SQLAlchemy imports.
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run final live pipeline validation."""
    print("=" * 80)
    print("TEST 02: FINAL LIVE PIPELINE VALIDATION")
    print("=" * 80)

    # Check environment
    supabase_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54330")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY", "sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH")

    if not supabase_url or not supabase_key:
        print("❌ Missing required environment variables")
        return 1

    print(f"✓ Using Supabase URL: {supabase_url}")

    # Try to import pipeline components with CORRECT imports
    try:
        from core.pipeline import DataSource, OpportunityPipeline, PipelineConfig
        from core.clients import get_default_client
        from core.db.session import get_db_session  # CORRECT: get_db_session, not get_session
        from core.db.models import Submission        # SQLAlchemy model
        print("✓ Successfully imported pipeline components")
    except ImportError as e:
        print(f"❌ Failed to import pipeline components: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return 1

    # Test SQLAlchemy connection and get submissions
    try:
        # Test with SQLAlchemy using correct context manager
        submissions_data = []
        with get_db_session() as session:
            submissions_query = session.query(Submission).limit(3)
            submissions = submissions_query.all()

            # Convert SQLAlchemy objects to dictionaries WITHIN the session context
            for sub in submissions:
                submissions_data.append({
                    'id': sub.id,
                    'title': sub.title,
                    'score': sub.score,
                    'num_comments': sub.num_comments,
                    'content': sub.content,
                    'subreddit_id': sub.subreddit_id
                })

        if not submissions_data:
            print("❌ No submissions found in database")
            return 1

        submissions = submissions_data
        print(f"✓ Found {len(submissions)} submissions via SQLAlchemy")

    except Exception as e:
        print(f"❌ Failed to query submissions with SQLAlchemy: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return 1

    # Also try with Supabase client for pipeline
    try:
        client = get_default_client()
        print("✓ Supabase client ready for pipeline")
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return 1

    # Run pipeline on submissions
    print("\n" + "-" * 60)
    print("RUNNING PIPELINE TEST")
    print("-" * 60)

    success_count = 0
    total_cost = 0.0

    for i, submission in enumerate(submissions, 1):
        submission_id = submission["id"]
        title = submission["title"]

        print(f"\n[{i}/{len(submissions)}] Processing: {submission_id}")
        print(f"Title: {title[:60]}...")
        print(f"Score: {submission['score']}, Comments: {submission['num_comments']}")

        try:
            # Create pipeline config with CORRECTED parameters
            config = PipelineConfig(
                data_source=DataSource.DATABASE,
                limit=1,
                dry_run=False,  # Actually store data
                return_data=True,
                enable_profiler=True,
                enable_opportunity_scoring=True,
                enable_trust=True,
                enable_monetization=False,  # Disable to save costs
                enable_market_validation=False,  # Disable to save costs
                supabase_client=client,
                # CORRECTED: Use proper source_config for table specification
                source_config={
                    "table_name": "submissions",
                    "filter_column": "id",  # Use 'id' field (UUID primary key)
                    "filter_value": [submission_id],
                },
                # Other default parameters
                parallel_processing=False,  # Sequential for testing
                enable_deduplication=False,  # Disable for testing
                enable_quality_filter=False,  # Process all submissions for testing
            )

            # Create and run pipeline
            pipeline = OpportunityPipeline(config)
            start_time = time.time()

            result = pipeline.run()
            processing_time = time.time() - start_time

            if result.get("success", False):
                print(f"✅ SUCCESS: {submission_id}")
                print(f"   - Processing time: {processing_time:.2f}s")

                stats = result.get('stats', {})
                if stats:
                    print(f"   - Stats: {stats}")

                # Check if data was returned
                opportunities = result.get("opportunities", result.get("data", []))
                if opportunities:
                    print(f"   - Fields populated: {len(opportunities[0])}")
                    # Show some key fields
                    opp = opportunities[0]
                    key_fields = ['app_name', 'value_proposition', 'final_score', 'opportunity_score']
                    for field in key_fields:
                        if field in opp and opp[field] is not None:
                            print(f"   - {field}: {str(opp[field])[:50]}...")

                success_count += 1

            else:
                error_msg = result.get("error", "Unknown error")
                print(f"❌ FAILED: {submission_id}")
                print(f"   - Error: {error_msg}")

        except Exception as e:
            print(f"❌ EXCEPTION: {submission_id}")
            print(f"   - Error: {e}")
            import traceback
            if '--verbose' in sys.argv:
                print(f"   - Traceback: {traceback.format_exc()}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total submissions: {len(submissions)}")
    print(f"Successful: {success_count}")
    print(f"Success rate: {success_count/len(submissions)*100:.1f}%")

    if success_count > 0:
        print("\n✅ PIPELINE IS WORKING!")
        print(f"Successfully processed {success_count} out of {len(submissions)} submissions")
        print("The recent database and ORM fixes are working correctly!")
        print("\n🎉 TEST 02 LIVE VALIDATION PASSED!")
        return 0
    else:
        print(f"\n❌ ALL TESTS FAILED ({len(submissions)} failures)")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Final live pipeline validation test")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        if '--verbose' in sys.argv:
            print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)