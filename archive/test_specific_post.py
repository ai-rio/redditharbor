#!/usr/bin/env python3
"""Test AI insights on a specific commercial post"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import supabase

from config.settings import SUPABASE_KEY, SUPABASE_URL


def test_specific_post():
    """Test the new prompt on a commercial post"""
    client = supabase(url=SUPABASE_URL, private_key=SUPABASE_KEY)

    # Get the #7 post: "My client wants to buy exclusivity"
    result = client.table('opportunity_analysis').select('submission_id, title, subreddit').eq('title', 'My client wants to buy exclusivity - what do we think?').execute()

    if result.data:
        submission_id = result.data[0]['submission_id']
        print("=" * 80)
        print(f"TESTING: r/smallbusiness - {result.data[0]['title']}")
        print("=" * 80)
        print(f"\nSubmission ID: {submission_id}")
        print(f"Subreddit: {result.data[0]['subreddit']}")

        # Get full submission with comments
        result = client.table('submissions').select('*').eq('id', submission_id).execute()
        if result.data:
            submission = result.data[0]

            # Get comments
            result = client.table('comments').select('body').eq('submission_id', submission_id).limit(5).execute()
            comments = result.data

            print("\n--- POST CONTENT ---")
            print(f"Title: {submission['title']}")
            print(f"Text: {submission.get('text', 'N/A')[:500]}...")

            print(f"\n--- COMMENTS ({len(comments)}) ---")
            for i, comment in enumerate(comments, 1):
                print(f"{i}. {comment['body'][:200]}...")

            print("\n" + "=" * 80)
            print("This post is ready for AI analysis with the new problem-inference prompt!")
            print("=" * 80)

if __name__ == "__main__":
    test_specific_post()
