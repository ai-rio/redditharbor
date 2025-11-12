#!/usr/bin/env python3
"""
Final Collection Script: Reach 250+ Posts for 50+ Score Validation
Target: Collect ~70 more posts to reach 250+ total
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

# Final push: Additional high-value subreddits
FINAL_COLLECTION_SUBREDDITS = {
    "SaaS": {
        "description": "B2B SaaS pain, proven willingness to pay",
        "limit": 30,
        "pain_signals": ["churn", "acquisition", "retention", "growth", "pricing"]
    },
    "b2bmarketing": {
        "description": "B2B marketing professional pain",
        "limit": 20,
        "pain_signals": ["lead generation", "sales", "conversion", "attribution"]
    },
    "consulting": {
        "description": "Consulting industry pain",
        "limit": 15,
        "pain_signals": ["client management", "delivery", "proposals", "operations"]
    },
    "ecommerce": {
        "description": "E-commerce business pain",
        "limit": 20,
        "pain_signals": ["conversion", "ads", "inventory", "logistics", "customer service"]
    }
}

def main():
    print("\n" + "="*80)
    print("FINAL PUSH: REACH 250+ POSTS FOR 50+ VALIDATION")
    print("="*80)
    print("\nCurrent State: 188 submissions")
    print("Target: 250+ submissions (need ~70 more)")
    print("Goal: Find 1-2 opportunities at 50+ scores")
    print("\nFocus: Additional proven pain points")
    print()

    print("="*80)
    print("TARGET SUBREDDITS")
    print("="*80)
    for sub, info in FINAL_COLLECTION_SUBREDDITS.items():
        print(f"  r/{sub:20} - {info['description']:50} (limit: {info['limit']})")
    print()

    all_posts = []
    total_collected = 0

    for subreddit, info in FINAL_COLLECTION_SUBREDDITS.items():
        print(f"{'='*80}")
        print(f"Collecting from r/{subreddit}...")
        print(f"{'='*80}")

        try:
            posts = collect_problem_posts(
                subreddits=[subreddit],
                limit=info['limit'],
                sort_type="top"
            )

            # Add metadata
            for post in posts:
                post['collection_phase'] = 'Phase 5 Final'
                post['collection_date'] = datetime.now().isoformat()
                post['subreddit_type'] = 'final_push'
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
            print(f"  - Subreddits: {list(FINAL_COLLECTION_SUBREDDITS.keys())}")
            print(f"  - Total posts: {total_collected}")
            print(f"  - Database now: ~{188 + total_collected} submissions")
            print(f"  - Target reached: {'✅ YES' if 188 + total_collected >= 250 else '❌ NO'}")

        except Exception as e:
            print(f"\n✗ Error loading to Supabase: {e}")
            raise
    else:
        print("\n⚠️  No posts collected")
        return

    print("\n" + "="*80)
    print("FINAL COLLECTION COMPLETE")
    print("="*80)
    new_total = 188 + total_collected
    print(f"New posts: {total_collected}")
    print(f"Total submissions: {new_total}")
    print(f"\nExpected 50+ scores: {max(1, int(new_total * 0.01))} (1-2% of {new_total})")
    print(f"50+ threshold: {new_total} posts provides {(new_total/250)*100:.0f}% confidence")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
