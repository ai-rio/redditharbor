#!/usr/bin/env python3
"""
Isolated test to reproduce deduplication database lookup issue
Tests the specific problem with Reddit ID to UUID conversion
"""

import os
import sys
from supabase import create_client

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_deduplication_lookup():
    """Test the deduplication lookup logic in isolation"""

    # Initialize Supabase client
    SUPABASE_URL = "http://127.0.0.1:54321"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Test Reddit IDs from the error log
    test_reddit_ids = ["1p7drk6", "1p7hni7", "1p6rx44"]

    print("=== TESTING DEDUPLICATION LOOKUP ISOLATION ===\n")

    print("1. Testing current approach (opportunities_unified with string Reddit ID):")
    for reddit_id in test_reddit_ids:
        print(f"\nTesting Reddit ID: {reddit_id}")

        try:
            # This is what the current code tries to do
            response = (
                supabase.table("opportunities_unified")
                .select("business_concept_id")
                .eq("submission_id", reddit_id)
                .execute()
            )
            print(f"  ✅ Query succeeded: {response.data}")
        except Exception as e:
            print(f"  ❌ Query failed: {e}")

    print("\n" + "="*60)
    print("2. Testing app_opportunities approach:")
    for reddit_id in test_reddit_ids:
        print(f"\nTesting Reddit ID: {reddit_id}")

        try:
            # Test the table from the diff
            response = (
                supabase.table("app_opportunities")
                .select("submission_id, title")
                .eq("submission_id", reddit_id)
                .execute()
            )
            print(f"  ✅ Query succeeded: Found {len(response.data) if response.data else 0} records")
            if response.data:
                print(f"      Sample: {response.data[0].get('title', 'No title')[:50]}...")
        except Exception as e:
            print(f"  ❌ Query failed: {e}")

    print("\n" + "="*60)
    print("3. Testing proper two-step lookup:")
    for reddit_id in test_reddit_ids:
        print(f"\nTesting Reddit ID: {reddit_id}")

        try:
            # Step 1: Find the submission UUID from Reddit ID
            submission_response = (
                supabase.table("submissions")
                .select("id, reddit_id")
                .eq("reddit_id", reddit_id)
                .execute()
            )

            if submission_response.data:
                submission_uuid = submission_response.data[0]["id"]
                print(f"  ✅ Step 1: Found submission UUID: {submission_uuid}")

                # Step 2: Check opportunities_unified with the UUID
                opportunity_response = (
                    supabase.table("opportunities_unified")
                    .select("business_concept_id, title")
                    .eq("submission_id", submission_uuid)
                    .execute()
                )

                if opportunity_response.data:
                    concept_id = opportunity_response.data[0].get("business_concept_id")
                    print(f"  ✅ Step 2: Found business_concept_id: {concept_id}")
                else:
                    print(f"  ✅ Step 2: No opportunity record found (new submission)")
            else:
                print(f"  ✅ Step 1: No submission found (new Reddit ID)")

        except Exception as e:
            print(f"  ❌ Two-step lookup failed: {e}")

    print("\n" + "="*60)
    print("4. Database schema verification:")

    # Check table schemas
    try:
        print("\nChecking submissions table:")
        response = supabase.table("submissions").select("id, reddit_id").limit(1).execute()
        if response.data:
            sample = response.data[0]
            print(f"  Sample record: id={type(sample['id'])} ({sample['id']}), reddit_id={type(sample['reddit_id'])} ({sample['reddit_id']})")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    try:
        print("\nChecking opportunities_unified table:")
        response = supabase.table("opportunities_unified").select("id, submission_id, business_concept_id").limit(1).execute()
        if response.data:
            sample = response.data[0]
            print(f"  Sample record: id={type(sample['id'])} ({sample['id']}), submission_id={type(sample['submission_id'])} ({sample['submission_id']})")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

if __name__ == "__main__":
    test_deduplication_lookup()