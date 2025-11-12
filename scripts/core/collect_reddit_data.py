#!/usr/bin/env python3
"""
Script 1 of 4: Collect Reddit Data
RedditHarbor Clean Pipeline - Data Collection Module

Collects Reddit posts and stores them in the database.
Single responsibility: Reddit API → Database submissions table
"""

import sys
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY, REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT
import praw
from praw.models import Submission

class RedditDataCollector:
    """Clean Reddit data collection for the 4-script pipeline"""

    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.reddit = None
        self.setup_reddit_client()

    def setup_reddit_client(self):
        """Initialize Reddit API client"""
        try:
            self.reddit = praw.Reddit(
                client_id=REDDIT_PUBLIC,
                client_secret=REDDIT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )
            print("✅ Reddit API client initialized")
        except Exception as e:
            print(f"❌ Reddit client setup failed: {e}")
            raise

    def get_target_subreddits(self) -> List[str]:
        """Define target subreddits for collection"""
        return [
            # High-value subreddits
            'productivity',
            'selfimprovement',
            'entrepreneur',
            'startups',
            'personalfinance',
            'financialindependence',
            'investing',
            'stocks',
            'technology',
            'programming',
            'learnprogramming',
            'saas',
            'sidehustle',
            'freelance',
            'digitalnomad',
            'SoftwareEngineering'
        ]

    def collect_submissions(self, subreddit_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Collect submissions from a single subreddit"""
        submissions = []

        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            print(f"📥 Collecting from r/{subreddit_name} (limit: {limit})")

            # Get hot submissions
            for submission in subreddit.hot(limit=limit):
                # Basic validation
                if not submission.title or len(submission.title.strip()) < 10:
                    continue

                # Store submission data
                submission_data = {
                    'submission_id': submission.id,
                    'title': submission.title.strip(),
                    'text': submission.selftext if submission.is_self else '',
                    'content': submission.selftext if submission.is_self else '',
                    'url': submission.url,
                    'subreddit': subreddit_name.lower(),
                    'upvotes': int(submission.score),
                    'comments_count': int(submission.num_comments),
                    'created_at': datetime.fromtimestamp(submission.created_utc).isoformat(),
                    'collected_at': datetime.now().isoformat()
                }

                submissions.append(submission_data)

            print(f"✅ Collected {len(submissions)} submissions from r/{subreddit_name}")

        except Exception as e:
            print(f"❌ Error collecting from r/{subreddit_name}: {e}")

        return submissions

    def store_submissions(self, submissions: List[Dict[str, Any]]) -> int:
        """Store submissions in database"""
        if not submissions:
            return 0

        try:
            # Batch insert
            response = self.supabase.table('submissions').insert(submissions).execute()

            if response.data:
                print(f"✅ Stored {len(response.data)} submissions in database")
                return len(response.data)
            else:
                print("⚠️ No submissions stored (possible duplicates)")
                return 0

        except Exception as e:
            print(f"❌ Error storing submissions: {e}")
            return 0

    def run_collection(self, target_subreddits: List[str] = None, submissions_per_subreddit: int = 50):
        """Main collection method"""
        print("🚀 Starting Reddit data collection...")
        print(f"Target subreddits: {len(target_subreddits or self.get_target_subreddits())}")
        print(f"Submissions per subreddit: {submissions_per_subreddit}")
        print("")

        if target_subreddits is None:
            target_subreddits = self.get_target_subreddits()

        total_collected = 0
        total_stored = 0

        for subreddit in target_subreddits:
            print(f"\n{'='*50}")
            print(f"Processing: r/{subreddit}")
            print(f"{'='*50}")

            # Collect submissions
            submissions = self.collect_submissions(subreddit, submissions_per_subreddit)
            total_collected += len(submissions)

            # Store in database
            stored = self.store_submissions(submissions)
            total_stored += stored

            # Rate limiting
            time.sleep(1)

        print(f"\n{'='*50}")
        print("COLLECTION SUMMARY")
        print(f"{'='*50}")
        print(f"Total subreddits processed: {len(target_subreddits)}")
        print(f"Total submissions collected: {total_collected}")
        print(f"Total submissions stored: {total_stored}")
        print(f"Success rate: {total_stored/total_collected*100:.1f}%" if total_collected > 0 else "N/A")

        return total_stored

def main():
    """Main execution function"""
    print("RedditHarbor Data Collection Pipeline")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    # Load environment variables
    load_dotenv(Path(__file__).parent.parent / '.env.local')

    try:
        collector = RedditDataCollector()

        # Run collection with default settings
        stored_count = collector.run_collection(
            target_subreddits=None,  # Use default list
            submissions_per_subreddit=50
        )

        if stored_count > 0:
            print(f"\n🎉 Successfully collected {stored_count} Reddit submissions!")
            print("Next step: python scripts/analyze_opportunities.py")
            return True
        else:
            print("\n⚠️ No submissions were stored")
            return False

    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        return False

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        import os
    except ImportError:
        print("⚠️ python-dotenv not installed, install with: pip install python-dotenv")
        os = None
        def load_dotenv(path):
            pass

    success = main()
    sys.exit(0 if success else 1)