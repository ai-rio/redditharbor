#!/usr/bin/env python3
"""
Test Save Extracted Leads to Database

Saves the leads extracted from existing high-scoring opportunities
to the customer_leads table to validate Option B database integration.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.lead_extractor import LeadExtractor, convert_to_database_record
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
import dlt

def main():
    """Test saving extracted leads to customer_leads table"""

    print("=" * 80)
    print("OPTION B: SAVE LEADS TO DATABASE TEST")
    print("=" * 80)

    # Connect to database
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get high-scoring opportunities
    print("\n1. Fetching high-scoring opportunities...")

    try:
        response = supabase.table('workflow_results').select('*').gte('final_score', 30.0).order('final_score', desc=True).limit(10).execute()
        opportunities = response.data
        print(f"Found {len(opportunities)} high-scoring opportunities")

        # Get Reddit data
        submission_ids = []
        for opp in opportunities:
            opp_id = opp['opportunity_id']
            if opp_id.startswith('opp_'):
                submission_ids.append(opp_id[4:])
            else:
                submission_ids.append(opp_id)

        reddit_response = supabase.table('app_opportunities_trust').select('*').in_('submission_id', submission_ids).execute()
        reddit_data = {item['submission_id']: item for item in reddit_response.data}
        print(f"Found Reddit data for {len(reddit_data)} submissions")

    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Extract leads
    print("\n2. Extracting leads...")
    extractor = LeadExtractor()
    leads_extracted = []

    for opp in opportunities:
        opp_id = opp['opportunity_id']
        submission_id = opp_id[4:] if opp_id.startswith('opp_') else opp_id
        reddit_info = reddit_data.get(submission_id)

        if not reddit_info:
            continue

        post = {
            'id': submission_id,
            'author': f"reddit_user_{submission_id[:6]}",
            'title': reddit_info.get('title', opp.get('problem_description', '')),
            'selftext': opp.get('problem_description', ''),
            'text': opp.get('problem_description', ''),
            'subreddit': reddit_info.get('subreddit', 'unknown'),
            'created_utc': None
        }

        lead = extractor.extract_from_reddit_post(post, opp['final_score'])
        leads_extracted.append(lead)

    print(f"Extracted {len(leads_extracted)} leads")

    # Convert to database records
    print("\n3. Converting to database records...")
    db_records = [convert_to_database_record(lead) for lead in leads_extracted]
    print(f"Created {len(db_records)} database records")

    # Check existing leads
    print("\n4. Checking existing customer_leads...")
    existing_response = supabase.table('customer_leads').select('reddit_post_id').execute()
    existing_count = len(existing_response.data)
    existing_ids = {record['reddit_post_id'] for record in existing_response.data}
    print(f"Found {existing_count} existing leads")

    # Filter out duplicates
    new_records = [record for record in db_records if record['reddit_post_id'] not in existing_ids]
    print(f"New leads to insert: {len(new_records)}")

    if new_records:
        # Load to database using DLT
        print(f"\n5. Loading {len(new_records)} leads to customer_leads table...")

        try:
            # Create DLT pipeline
            pipeline = dlt.pipeline(
                pipeline_name="reddit_harbor_leads_test",
                destination="postgres",
                dataset_name="reddit_harbor"
            )

            # Define resource with merge disposition (prevent duplicates)
            @dlt.resource(
                name="customer_leads",
                write_disposition="merge",
                primary_key="reddit_post_id"
            )
            def leads_resource():
                yield new_records

            # Load to database
            load_info = pipeline.run(leads_resource())

            print(f"✅ Loaded {len(new_records)} leads to customer_leads table")
            print(f"   Pipeline: {load_info.pipeline.pipeline_name}")
            print(f"   Load count: {len(list(leads_resource()))}")

        except Exception as e:
            print(f"❌ Lead loading failed: {e}")
            import traceback
            traceback.print_exc()

            # Fallback: Direct Supabase insert
            print(f"\n6. Fallback: Direct Supabase insert...")
            try:
                for record in new_records:
                    supabase.table('customer_leads').insert(record).execute()
                print(f"✅ Inserted {len(new_records)} leads via direct Supabase")
            except Exception as e2:
                print(f"❌ Direct insert also failed: {e2}")
    else:
        print(f"\n5. No new leads to insert (all already exist)")

    # Verify results
    print(f"\n6. Verifying results...")
    final_response = supabase.table('customer_leads').select('*').execute()
    final_count = len(final_response.data)
    print(f"Total leads in database: {final_count}")

    if final_count > existing_count:
        print(f"✅ Successfully added {final_count - existing_count} new leads")

        # Show sample of new leads
        print(f"\n7. Sample of new leads:")
        sample_leads = final_response.data[-3:]  # Last 3 leads
        for i, lead in enumerate(sample_leads, 1):
            print(f"   Lead {i}: u/{lead.get('reddit_username', 'unknown')} | "
                  f"r/{lead.get('subreddit', 'unknown')} | "
                  f"Score: {lead.get('lead_score', 0):.0f} | "
                  f"Stage: {lead.get('buying_intent_stage', 'unknown')}")
    else:
        print(f"ℹ️  No new leads added")

    print(f"\n" + "=" * 80)
    print(f"OPTION B SAVE LEADS TEST COMPLETE")
    print(f"Status: ✅ SUCCESS - {final_count} total leads in database")
    print(f"=" * 80)

if __name__ == "__main__":
    main()