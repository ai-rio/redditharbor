#!/usr/bin/env python3
"""
Test Hybrid Strategy with High-Scoring Sample Data

This script injects high-scoring opportunity data into the database
to test the complete hybrid strategy pipeline with both Option A and B.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client

# High-scoring sample opportunities that should trigger hybrid strategy
HIGH_SCORING_OPPORTUNITIES = [
    {
        "title": "Our startup needs a better CRM - budget $5000-10000",
        "text": "Our SaaS startup is growing fast and spreadsheets aren't cutting it anymore. We need a proper CRM solution with API access. Our budget is around $5000-10000 annually for the right solution. Currently managing 200+ customer relationships manually.",
        "subreddit": "Entrepreneur",
        "author": "startup_founder_123",
        "created_utc": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
        "submission_id": f"test_high_{random.randint(1000, 9999)}_1",
        "url": f"https://reddit.com/r/Entrepreneur/comments/test_high_1/"
    },
    {
        "title": "Paying $800/month for Salesforce - looking for alternatives",
        "text": "Our team of 25 people is currently paying $800/month for Salesforce Enterprise. It's becoming too expensive and we're looking for alternatives under $400/month that still have good reporting features. Need to make decision by end of Q1.",
        "subreddit": "sysadmin",
        "author": "it_manager_456",
        "created_utc": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
        "submission_id": f"test_high_{random.randint(1000, 9999)}_2",
        "url": f"https://reddit.com/r/sysadmin/comments/test_high_2/"
    },
    {
        "title": "Need project management tool for 50-person team",
        "text": "Our engineering team is struggling with project coordination. We're currently using multiple tools and need an integrated solution. Budget approved for project management software, looking at options in the $300-500 range monthly.",
        "subreddit": "projectmanagement",
        "author": "engineering_lead_789",
        "created_utc": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
        "submission_id": f"test_high_{random.randint(1000, 9999)}_3",
        "url": f"https://reddit.com/r/projectmanagement/comments/test_high_3/"
    },
    {
        "title": "Company looking for analytics dashboard solution",
        "text": "We're a mid-sized company spending too much time on manual reporting. Need an analytics dashboard with real-time data. Budget around $2000-3000 for implementation. Ready to move forward this quarter.",
        "subreddit": "business",
        "author": "data_analyst_101",
        "created_utc": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
        "submission_id": f"test_high_{random.randint(1000, 9999)}_4",
        "url": f"https://reddit.com/r/business/comments/test_high_4/"
    },
    {
        "title": "Switching from HubSpot - need marketing automation",
        "text": "Our marketing department is paying $1200/month for HubSpot Enterprise. We need a more cost-effective marketing automation platform with similar features. Target budget is under $600/month. Need to make decision in next 6 weeks.",
        "subreddit": "marketing",
        "author": "marketing_director_202",
        "created_utc": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
        "submission_id": f"test_high_{random.randint(1000, 9999)}_5",
        "url": f"https://reddit.com/r/marketing/comments/test_high_5/"
    }
]

def insert_test_opportunities():
    """Insert high-scoring test opportunities into the database"""
    print("🔧 Connecting to Supabase...")

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected successfully!")

        print(f"\n📊 Inserting {len(HIGH_SCORING_OPPORTUNITIES)} high-scoring test opportunities...")

        inserted_count = 0
        for opportunity in HIGH_SCORING_OPPORTUNITIES:
            try:
                # Insert into app_opportunities_trust table
                result = supabase.table('app_opportunities_trust').insert({
                    'submission_id': opportunity['submission_id'],
                    'title': opportunity['title'],
                    'problem_description': opportunity['text'],
                    'subreddit': opportunity['subreddit'],
                    'opportunity_score': random.randint(65, 90),  # High opportunity scores (≥65 to trigger hybrid)
                    'reddit_score': random.randint(800, 2000),  # High Reddit scores
                    'num_comments': random.randint(5, 50),
                    'trust_score': random.uniform(0.7, 0.9),
                    'trust_badge': 'verified',
                    'status': 'new',
                    'target_user': 'B2B SaaS companies' if 'company' in opportunity['text'].lower() or 'team' in opportunity['text'].lower() else 'Individual users',
                    'monetization_model': 'Subscription' if '$' in opportunity['text'] else 'Freemium',
                    '_dlt_load_id': 'test_load_' + opportunity['submission_id'],  # Required DLT column
                    '_dlt_id': 'test_dlt_' + opportunity['submission_id']     # Required DLT column
                }).execute()

                inserted_count += 1
                print(f"  ✅ Inserted: {opportunity['title'][:50]}...")

            except Exception as e:
                print(f"  ❌ Failed to insert {opportunity['submission_id']}: {e}")

        print(f"\n✅ Successfully inserted {inserted_count}/{len(HIGH_SCORING_OPPORTUNITIES)} opportunities")
        return inserted_count

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return 0

def main():
    """Main test function"""
    print("🎯 REDDITHARBOR HYBRID STRATEGY - HIGH SCORE TEST")
    print("="*60)

    # Insert high-scoring test data
    inserted = insert_test_opportunities()

    if inserted > 0:
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Run the hybrid strategy pipeline:")
        print(f"   python scripts/core/batch_opportunity_scoring.py")
        print(f"\n2. Monitor results:")
        print(f"   python scripts/monitor_hybrid_strategy.py")
        print(f"\n3. Check database for:")
        print(f"   • Customer leads in customer_leads table")
        print(f"   • LLM analyses in llm_monetization_analysis table")
        print(f"\n💡 Expected: These high-scoring opportunities should trigger hybrid strategy!")
    else:
        print("\n❌ No opportunities inserted. Check database connection.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())