#!/usr/bin/env .venv/bin/python
"""
RedditHarbor Database Schema Checker
Check what data and columns are stored in Supabase
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from redditharbor.login import supabase

    from config.settings import *
except ImportError as e:
    print(f"Error: Could not import dependencies: {e}")
    sys.exit(1)

def check_database_schema():
    """Check database schema and sample data"""
    print("🔍 RedditHarbor Database Schema Analysis")
    print("=" * 45)

    try:
        # Connect to Supabase
        supabase_client = supabase(
            url=SUPABASE_URL,
            private_key=SUPABASE_KEY
        )

        print("📊 Checking submission table structure...")

        # Get sample submission data to see all columns
        submission_result = supabase_client.table("submission").select("*").limit(2).execute()

        if submission_result.data:
            print(f"✅ Found {len(submission_result.data)} submission records")
            print(f"📋 Submission table columns: {list(submission_result.data[0].keys())}")

            print("\n📄 Sample submission record:")
            for key, value in submission_result.data[0].items():
                print(f"   {key}: {value}")
        else:
            print("❌ No submission data found")

        print("\n👥 Checking redditor table structure...")

        # Get sample redditor data
        redditor_result = supabase_client.table("redditor").select("*").limit(2).execute()

        if redditor_result.data:
            print(f"✅ Found {len(redditor_result.data)} redditor records")
            print(f"📋 Redditor table columns: {list(redditor_result.data[0].keys())}")

            print("\n👤 Sample redditor record:")
            for key, value in redditor_result.data[0].items():
                print(f"   {key}: {value}")
        else:
            print("❌ No redditor data found")

        print("\n💬 Checking comment table structure...")

        # Get sample comment data
        comment_result = supabase_client.table("comment").select("*").limit(2).execute()

        if comment_result.data:
            print(f"✅ Found {len(comment_result.data)} comment records")
            print(f"📋 Comment table columns: {list(comment_result.data[0].keys())}")

            print("\n💭 Sample comment record:")
            for key, value in comment_result.data[0].items():
                print(f"   {key}: {value}")
        else:
            print("❌ No comment data found")

        print("\n📈 Database Summary:")

        # Get counts
        try:
            submission_count = supabase_client.table("submission").select("count", count="exact").execute()
            redditor_count = supabase_client.table("redditor").select("count", count="exact").execute()
            comment_count = supabase_client.table("comment").select("count", count="exact").execute()

            print(f"   • Submissions: {submission_count.count}")
            print(f"   • Redditors: {redditor_count.count}")
            print(f"   • Comments: {comment_count.count}")
        except Exception as e:
            print(f"   ❌ Error getting counts: {e}")

        # Look for date/time related columns
        print("\n🕒 Date/Time Analysis:")
        if submission_result.data:
            date_columns = [col for col in submission_result.data[0].keys() if any(date_word in col.lower() for date_word in ['date', 'time', 'created', 'updated', 'timestamp'])]
            if date_columns:
                print(f"   ✅ Date columns found: {date_columns}")
                for col in date_columns:
                    sample_value = submission_result.data[0].get(col)
                    print(f"      {col}: {sample_value}")
            else:
                print("   ❌ No date columns detected in submissions")

        # Check if Reddit's created_utc is stored
        if submission_result.data:
            reddit_data = submission_result.data[0]
            print("\n🔄 Reddit Data Fields:")
            reddit_fields = [col for col in reddit_data.keys() if any(reddit_word in col.lower() for reddit_word in ['created', 'utc', 'reddit'])]
            if reddit_fields:
                for field in reddit_fields:
                    print(f"   • {field}: {reddit_data[field]}")
            else:
                print("   ❌ No Reddit timestamp fields detected")

    except Exception as e:
        print(f"❌ Error checking database: {e}")
        print("💡 Make sure Supabase is running and accessible")

if __name__ == "__main__":
    check_database_schema()
