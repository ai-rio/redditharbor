#!/usr/bin/env python3
"""
Quick pre-test validation: Verify all submission IDs are clean UUIDs.

This is the minimal validation needed before Phase 8 testing.
"""

import os
import re
import sys
from supabase import create_client


UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


def main():
    print("=" * 80)
    print("PRE-TEST VALIDATION: Clean-Break ID Format Check")
    print("=" * 80)
    print()

    # Load Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54330')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_key:
        print("❌ Error: SUPABASE_KEY environment variable not set")
        print("   Export it or set in .env.local")
        return 1

    print(f"🔗 Connecting to Supabase: {supabase_url}")

    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return 1

    print("✅ Connected successfully")
    print()

    # Check submissions table
    print("🔍 Validating submission ID formats...")
    try:
        result = supabase.table('submissions').select('id, title').execute()
        submissions = result.data
    except Exception as e:
        print(f"❌ Failed to query submissions table: {e}")
        return 1

    if not submissions:
        print("⚠️  Warning: No submissions found in database")
        print("   Tests may fail due to missing data")
        print()
        return 0

    # Check each ID
    invalid_ids = []
    for submission in submissions:
        submission_id = submission.get('id')
        if not UUID_PATTERN.match(submission_id.lower()):
            invalid_ids.append({
                'id': submission_id,
                'title': submission.get('title', 'N/A')[:60]
            })

    # Report results
    print(f"   Total submissions: {len(submissions)}")
    print(f"   Clean UUIDs: {len(submissions) - len(invalid_ids)}")
    print(f"   Non-UUID formats: {len(invalid_ids)}")
    print()

    if invalid_ids:
        print("❌ VALIDATION FAILED")
        print()
        print("Found submissions with non-UUID format:")
        for idx, invalid in enumerate(invalid_ids[:5], 1):
            print(f"   {idx}. ID: {invalid['id']}")
            print(f"      Title: {invalid['title']}...")
        print()
        print("Fix: Ensure clean-break ID normalization is working")
        print("See: docs/clean-break-implementation/00-problem-statement.md")
        print()
        return 1

    print("✅ ID FORMAT VALIDATION PASSED")
    print()
    print("All submission IDs are clean UUIDs!")
    print("Database is ready for Phase 8 integration testing.")
    print()
    print("=" * 80)
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
