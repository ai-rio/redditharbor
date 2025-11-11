#!/usr/bin/env python3
"""
Create Comment Table - Initialize the comment table with proper schema
"""

import sys
from pathlib import Path

from supabase import Client, create_client

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_comment_table():
    """Create the comment table with proper schema"""
    try:
        # Import configuration
        from config.settings import SUPABASE_KEY, SUPABASE_URL

        # Setup Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        print("🔧 CREATING COMMENT TABLE")
        print("=" * 50)

        # The actual SQL to create the comment table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS comment (
            comment_id VARCHAR(10) PRIMARY KEY,
            submission_id VARCHAR(10) NOT NULL,
            redditor_id INTEGER,
            created_at TIMESTAMPTZ NOT NULL,
            text TEXT,
            permalink VARCHAR(1000),
            score INTEGER DEFAULT 0,
            edited BOOLEAN DEFAULT FALSE,
            removed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (submission_id) REFERENCES submission(submission_id),
            FOREIGN KEY (redditor_id) REFERENCES redditor(redditor_id)
        );
        """

        print("📝 SQL to execute:")
        print(create_table_sql)
        print("\n⚠️ Note: This requires direct database access or admin privileges")
        print("   The current Supabase client may not have table creation permissions")

        # Try to insert a simple comment to see what columns are actually expected
        print("\n🔍 Testing comment insert to understand expected schema...")

        # Get a sample submission
        sample_submission = supabase.table("submission").select("submission_id").limit(1).execute()

        if sample_submission.data:
            submission_id = sample_submission.data[0]["submission_id"]
            print(f"📄 Using submission: {submission_id}")

            # Try different column combinations to find the correct schema
            test_comment_variants = [
                {
                    "comment_id": "test_schema_1",
                    "submission_id": submission_id,
                    "text": "test comment with text column",
                    "created_at": "2025-01-01T00:00:00Z"
                },
                {
                    "comment_id": "test_schema_2",
                    "submission_id": submission_id,
                    "body": "test comment with body column",
                    "created_at": "2025-01-01T00:00:00Z"
                },
                {
                    "comment_id": "test_schema_3",
                    "submission_id": submission_id,
                    "comment_text": "test comment with comment_text column",
                    "created_at": "2025-01-01T00:00:00Z"
                }
            ]

            for i, test_comment in enumerate(test_comment_variants, 1):
                try:
                    result = supabase.table("comment").insert(test_comment).execute()
                    print(f"✅ Schema variant {i} SUCCESS: {result.data}")

                    # Clean up
                    supabase.table("comment").delete().eq("comment_id", test_comment["comment_id"]).execute()
                    print(f"✅ Cleaned up test comment {i}")

                except Exception as e:
                    print(f"❌ Schema variant {i} failed: {e}")

            # Try to see if we can list table columns via information_schema
            print("\n🔍 Attempting to get comment table schema...")
            try:
                # This might not work with the REST API, but worth a try
                schema_query = supabase.table("comment").select("*").limit(0).execute()
                if hasattr(schema_query, 'data') and schema_query.data:
                    print("✅ Comment table exists, can access columns")
                else:
                    print("❌ Cannot access comment table schema")
            except Exception as e:
                print(f"❌ Cannot get comment schema: {e}")

        else:
            print("❌ No submissions found to test with")

    except Exception as e:
        print(f"❌ Comment table creation failed: {e}")

if __name__ == "__main__":
    create_comment_table()
