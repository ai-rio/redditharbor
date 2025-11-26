#!/usr/bin/env python3
"""
Step 4: Test DLT data loading to app_opportunities table
"""

import sys
import os
from datetime import datetime

# Add pipeline-v2 to path
sys.path.insert(0, os.path.dirname(__file__))

def test_dlt_data_loading():
    """Test DLT loading sample data to app_opportunities table"""
    print("📦 Testing DLT Data Loading to app_opportunities")
    print("=" * 55)

    try:
        import dlt
        print("✅ DLT imported successfully")

        # Create sample data
        sample_opportunity = {
            'submission_id': 'test_dlt_001',
            'title': 'Looking for recommendations for budget fitness tracker',
            'url': 'https://reddit.com/r/fitness/comments/test123/looking_for_fitness_tracker',
            'subreddit': 'fitness',
            'author': 'fitness_enthusiast_2025',
            'score': 42,
            'created_utc': datetime.now(),
            'num_comments': 15,

            # AI Analysis Fields
            'opportunity_score': 78.5,
            'opportunity_category': 'Health & Fitness',
            'opportunity_reasoning': 'User seeking budget-friendly fitness tracking solutions indicates potential market for affordable fitness apps and services',

            # Monetization Analysis Fields
            'monetization_score': 65.2,
            'monetization_keywords': ['fitness', 'tracker', 'budget', 'health'],
            'monetization_confidence': 0.75,

            # Profiling Analysis Fields
            'user_intent': 'Product Research',
            'user_persona': 'Health Conscious Consumer',
            'expertise_level': 'Beginner',

            # Trust Validation Fields
            'trust_score': 82.0,
            'trust_badge': 'SILVER',
            'activity_score': 75.0,
            'engagement_score': 68.0,
            'trend_score': 45.0,
            'validity_score': 85.0,
            'quality_score': 79.0,
            'ai_confidence_score': 88.0,

            # Metadata
            'processed_at': datetime.now(),
            'updated_at': datetime.now()
        }

        print(f"📋 Sample opportunity: {sample_opportunity['title'][:50]}...")
        print(f"🎯 Opportunity Score: {sample_opportunity['opportunity_score']}")
        print(f"🛡️ Trust Score: {sample_opportunity['trust_score']} ({sample_opportunity['trust_badge']})")

        # Create DLT pipeline
        print("\n🔧 Creating DLT pipeline...")
        pipeline = dlt.pipeline(
            pipeline_name="test_data_loading",
            destination="postgres",  # DLT uses 'postgres' for Supabase
            dataset_name="public"
        )
        print("✅ DLT pipeline created")

        # Test the data loading
        print("\n📤 Loading data to app_opportunities table...")

        # Use DLT to load the data with merge disposition
        info = pipeline.run(
            [sample_opportunity],
            table_name="app_opportunities",
            write_disposition="merge",
            primary_key="submission_id"
        )

        print(f"✅ Data loaded successfully!")
        print(f"📊 Load info: {info}")
        # pipeline.pipeline_url not available in this version

        # Verify the data was actually loaded
        print("\n🔍 Verifying data was loaded...")
        import sqlalchemy as sa

        engine = sa.create_engine("postgresql://postgres:postgres@127.0.0.1:54331/postgres")

        with engine.connect() as conn:
            result = conn.execute(sa.text("""
                SELECT submission_id, title, opportunity_score, trust_score, trust_badge
                FROM app_opportunities
                WHERE submission_id = :submission_id
            """), {'submission_id': 'test_dlt_001'})

            loaded_record = result.fetchone()

            if loaded_record:
                print(f"✅ Record verified in database!")
                print(f"   - Title: {loaded_record[1][:40]}...")
                print(f"   - Opportunity Score: {loaded_record[2]}")
                print(f"   - Trust Score: {loaded_record[3]} ({loaded_record[4]})")
            else:
                print("❌ Record not found in database!")
                return False

        print("\n🧹 Cleaning up test record...")
        with engine.connect() as conn:
            conn.execute(sa.text("""
                DELETE FROM app_opportunities
                WHERE submission_id = 'test_dlt_001'
            """))
            print("✅ Test record cleaned up")

        print("\n🎉 DLT DATA LOADING TEST COMPLETE")
        print("=" * 55)
        return True

    except Exception as e:
        print(f"❌ Error in DLT data loading: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dlt_data_loading()

    if success:
        print("\n✅ Step 4 PASSED: DLT can load data to app_opportunities table")
    else:
        print("\n❌ Step 4 FAILED: DLT data loading issues")
        sys.exit(1)