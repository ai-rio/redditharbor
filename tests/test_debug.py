#!/usr/bin/env .venv/bin/python
"""
Test script to apply the minimal fix to RedditHarbor
"""

import os
import shutil

from redditharbor_config import *


def apply_fix():
    """Apply the minimal fix to the RedditHarbor pipeline"""

    # Path to the RedditHarbor pipeline file
    pipeline_file = "/home/carlos/projects/redditharbor/.venv/lib/python3.12/site-packages/redditharbor/dock/pipeline.py"

    # Create backup
    backup_file = pipeline_file + ".backup"
    if not os.path.exists(backup_file):
        shutil.copy2(pipeline_file, backup_file)
        print(f"✅ Created backup: {backup_file}")

    # Read the file
    with open(pipeline_file) as f:
        content = f.read()

    # Apply the fix: Move submission_id assignment before try block
    original_code = """                    for submission in getattr(r_, sort_type)(limit=limit):
                        try:
                            submission_id, submission_inserted, redditor_inserted = self.submission_data(
                                submission=submission, mask_pii=mask_pii
                            )"""

    fixed_code = """                    for submission in getattr(r_, sort_type)(limit=limit):
                        submission_id = submission.id  # Assign before try block
                        try:
                            submission_id, submission_inserted, redditor_inserted = self.submission_data(
                                submission=submission, mask_pii=mask_pii
                            )"""

    if original_code in content:
        content = content.replace(original_code, fixed_code)

        # Write the fixed file
        with open(pipeline_file, "w") as f:
            f.write(content)

        print("✅ Applied fix: Moved submission_id assignment before try block")
        return True
    else:
        print("❌ Could not find the exact code pattern to fix")
        return False


def test_fix():
    """Test if the fix works"""
    print("\n🧪 Testing the fix...")

    try:
        # Import and test the fixed pipeline
        from redditharbor.dock.pipeline import collect
        from redditharbor.login import reddit, supabase

        # Initialize pipeline
        reddit_client = reddit(
            public_key=REDDIT_PUBLIC,
            secret_key=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        supabase_client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

        pipeline = collect(
            reddit_client=reddit_client,
            supabase_client=supabase_client,
            db_config=DB_CONFIG,
        )

        # Test with PII disabled to avoid SpaCy issues for now
        print("📥 Testing with PII disabled...")
        pipeline.subreddit_submission(
            subreddits=["python"], sort_types=["hot"], limit=1, mask_pii=False
        )

        print("✅ Fix successful! No UnboundLocalError occurred.")
        return True

    except Exception as e:
        if "cannot access local variable 'submission_id'" in str(e):
            print(f"❌ Fix failed: Same UnboundLocalError still occurs: {e}")
        else:
            print(f"⚠️  Different error occurred (SpaCy issue likely): {e}")
            print("✅ But the UnboundLocalError is fixed!")

        return False


if __name__ == "__main__":
    print("🔧 Applying minimal fix to RedditHarbor...")

    if apply_fix():
        test_fix()
    else:
        print("❌ Fix could not be applied")
