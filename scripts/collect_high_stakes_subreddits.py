#!/usr/bin/env python3
"""
Custom Collection Script for Phase 4: High-Stakes Subreddits
Collects from subreddits with high monetization potential and willingness to pay
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

# Import DLT collection tools
from core.dlt_collection import collect_problem_posts
from scripts.full_scale_collection import load_submissions_to_supabase

# High-stakes, high-monetization subreddits
HIGH_STAKES_SUBREDDITS = {
    "realestateinvesting": {
        "description": "Real estate deal analysis, high-stakes pain",
        "limit": 50,
        "pain_signals": ["deal analysis", "cap rate", "cash flow", "property management", "tenant", "landlord"]
    },
    "financialcareers": {
        "description": "Finance professionals, monetization signals",
        "limit": 40,
        "pain_signals": ["career progression", "compensation", "skills", "certification", "networking"]
    },
    "productivity": {
        "description": "Willingness to pay for productivity gains",
        "limit": 30,
        "pain_signals": ["time management", "focus", "procrastination", "workflow", "efficiency"]
    }
}

def main():
    print("\n" + "="*80)
    print("PHASE 4: COLLECTING HIGH-STAKES SUBREDDITS FOR THRESHOLD 50+ TESTING")
    print("="*80)
    print("\nTarget Strategy: High monetization potential + high-stakes pain")
    print("\nSubreddits:")
    for sub, info in HIGH_STAKES_SUBREDDITS.items():
        print(f"  r/{sub:25} - {info['description']:50} (limit: {info['limit']})")

    all_posts = []
    total_collected = 0

    for subreddit, info in HIGH_STAKES_SUBREDDITS.items():
        print(f"\n{'='*80}")
        print(f"Collecting from r/{subreddit}...")
        print(f"{'='*80}")

        try:
            posts = collect_problem_posts(
                subreddits=[subreddit],
                limit=info['limit'],
                sort_type="top"  # High engagement
            )

            # Add metadata
            for post in posts:
                post['collection_phase'] = 'Phase 4'
                post['collection_date'] = datetime.now().isoformat()
                post['subreddit_type'] = 'high_stakes'
                post['pain_signals'] = info.get('pain_signals', [])

            all_posts.extend(posts)
            total_collected += len(posts)

            print(f"✓ Collected {len(posts)} posts from r/{subreddit}")
            print(f"  Total posts so far: {total_collected}")

        except Exception as e:
            print(f"✗ Error collecting from r/{subreddit}: {e}")
            continue

    print(f"\n{'='*80}")
    print("LOADING TO SUPABASE")
    print(f"{'='*80}")

    if all_posts:
        try:
            load_submissions_to_supabase(all_posts)
            print(f"\n✅ SUCCESS: Loaded {total_collected} posts to Supabase")
            print(f"  - Subreddits: {list(HIGH_STAKES_SUBREDDITS.keys())}")
            print(f"  - Total posts: {total_collected}")
            print("  - Database table: submissions")
            print("  - DLT deduplication: Active")

        except Exception as e:
            print(f"\n✗ Error loading to Supabase: {e}")
            raise
    else:
        print("\n⚠️  No posts collected")
        return

    print("\n" + "="*80)
    print("COLLECTION SUMMARY")
    print("="*80)
    print("Phase 4 Data Collection Complete!")
    print(f"Total posts collected: {total_collected}")
    print(f"Database now contains: ~{100 + total_collected} submissions")
    print("\nNext step: Run batch scoring with threshold 50.0")
    print("  export SCORE_THRESHOLD=50.0")
    print("  python3 scripts/batch_opportunity_scoring.py")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
