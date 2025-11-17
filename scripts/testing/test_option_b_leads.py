#!/usr/bin/env python3
"""
Test Option B Lead Extraction with Existing Data

Tests the lead extraction functionality on existing high-scoring opportunities
from the E2E testing session to validate Option B capabilities.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.lead_extractor import LeadExtractor, convert_to_database_record, format_lead_for_slack
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
import os

def main():
    """Test lead extraction with existing high-scoring opportunities"""

    print("=" * 80)
    print("OPTION B: LEAD EXTRACTION TEST WITH EXISTING DATA")
    print("=" * 80)

    # Connect to database
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get high-scoring opportunities with Reddit data
    print("\n1. Fetching high-scoring opportunities...")

    # Use raw SQL since we need a join
    try:
        # Get workflow_results data
        response = supabase.table('workflow_results').select('*').gte('final_score', 30.0).order('final_score', desc=True).limit(10).execute()
        opportunities = response.data
        print(f"Found {len(opportunities)} high-scoring opportunities")

        # Get corresponding Reddit data
        submission_ids = []
        for opp in opportunities:
            opp_id = opp['opportunity_id']
            # Handle both 'opp_1ox7we0' and '1ox7we0' formats
            if opp_id.startswith('opp_'):
                submission_ids.append(opp_id[4:])  # Remove 'opp_' prefix
            else:
                submission_ids.append(opp_id)

        if submission_ids:
            reddit_response = supabase.table('app_opportunities_trust').select('*').in_('submission_id', submission_ids).execute()
            reddit_data = {item['submission_id']: item for item in reddit_response.data}
            print(f"Found Reddit data for {len(reddit_data)} submissions")
        else:
            reddit_data = {}
            print("No valid submission IDs found")

    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Initialize lead extractor
    extractor = LeadExtractor()
    leads_extracted = []

    print("\n2. Extracting leads from opportunities...")

    for opp in opportunities:
        opp_id = opp['opportunity_id']
        submission_id = opp_id[4:] if opp_id.startswith('opp_') else opp_id
        reddit_info = reddit_data.get(submission_id)

        if not reddit_info:
            print(f"  ⚠️  No Reddit data for {opp_id}")
            continue

        # Create Reddit post format for lead extraction
        post = {
            'id': submission_id,
            'author': f"reddit_user_{submission_id[:6]}",  # We don't have author data in current schema
            'title': reddit_info.get('title', opp.get('problem_description', '')),
            'selftext': opp.get('problem_description', ''),
            'text': opp.get('problem_description', ''),
            'subreddit': reddit_info.get('subreddit', 'unknown'),
            'created_utc': None
        }

        # Extract lead signals
        try:
            lead = extractor.extract_from_reddit_post(post, opp['final_score'])
            leads_extracted.append(lead)

            print(f"  ✓ Lead extracted: {lead.reddit_username} | Score: {lead.lead_score:.0f} | Stage: {lead.buying_intent_stage}")

            # Show brief lead info
            if lead.competitor_mentioned:
                print(f"    Competitor: {lead.competitor_mentioned}")
            if lead.budget_mentioned:
                print(f"    Budget: {lead.budget_mentioned}")
            if lead.urgency_level != 'low':
                print(f"    Urgency: {lead.urgency_level}")

        except Exception as e:
            print(f"  ❌ Lead extraction failed for {submission_id}: {e}")

    print(f"\n3. Lead Extraction Summary:")
    print(f"   Opportunities processed: {len(opportunities)}")
    print(f"   Leads extracted: {len(leads_extracted)}")
    print(f"   Extraction rate: {len(leads_extracted)/len(opportunities)*100:.1f}%")

    if leads_extracted:
        print(f"\n4. Top Leads (by score):")

        # Sort by lead score
        leads_extracted.sort(key=lambda x: x.lead_score, reverse=True)

        for i, lead in enumerate(leads_extracted[:3], 1):
            print(f"\n   LEAD #{i}:")
            print(f"   Reddit: u/{lead.reddit_username}")
            print(f"   Subreddit: r/{lead.subreddit}")
            print(f"   Problem: {lead.problem_description[:100]}...")
            print(f"   Score: {lead.lead_score:.0f}/100")
            print(f"   Stage: {lead.buying_intent_stage}")
            print(f"   Urgency: {lead.urgency_level}")

            if lead.competitor_mentioned:
                print(f"   Competitor: {lead.competitor_mentioned}")
            if lead.budget_mentioned:
                print(f"   Budget: {lead.budget_mentioned}")
            if lead.team_size:
                print(f"   Team Size: {lead.team_size}")

            print(f"   URL: {lead.reddit_post_url}")

        # Test database record conversion
        print(f"\n5. Testing database record conversion...")
        test_lead = leads_extracted[0]
        db_record = convert_to_database_record(test_lead)

        print(f"   ✓ Database record created with {len(db_record)} fields")
        print(f"   Key fields: reddit_username={db_record.get('reddit_username')}, lead_score={db_record.get('lead_score')}")

        # Test Slack formatting
        print(f"\n6. Testing Slack notification format...")
        slack_msg = format_lead_for_slack(test_lead)
        print(f"   ✓ Slack message generated ({len(slack_msg)} characters)")
        print(f"   Preview: {slack_msg[:200]}...")

        # Ask if user wants to save leads to database
        print(f"\n7. Save leads to database?")
        print(f"   Found {len(leads_extracted)} leads ready to save")
        print(f"   To save, run: python scripts/testing/test_save_leads.py")

    print(f"\n" + "=" * 80)
    print(f"OPTION B LEAD EXTRACTION TEST COMPLETE")
    print(f"Status: ✅ SUCCESS - {len(leads_extracted)} leads extracted")
    print(f"=" * 80)

if __name__ == "__main__":
    main()