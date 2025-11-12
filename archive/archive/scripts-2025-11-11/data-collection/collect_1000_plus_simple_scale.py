#!/usr/bin/env python3
"""
SIMPLE SCALE-UP TO 1000+ POSTS FOR THRESHOLD 70+ TESTING
Uses existing collect_problem_posts() function with increased limits and more subreddits
Target: 1000+ posts (current: 594)

Strategy:
1. Increase limit per subreddit to 1000 (was 200)
2. Add 15 more ultra-premium subreddits (total: 22)
3. Use "top" sort type for quality
4. Expected: 1000-2000 total posts
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

# Extended list of ultra-premium subreddits (22 total)
# Increased from 7 to 22 subreddits
ULTRA_PREMIUM_SUBREDDITS = [
    # Original 7 (proven high-quality)
    "venturecapital",
    "financialindependence",
    "startups",
    "investing",
    "realestateinvesting",
    "business",
    "SaaS",

    # Additional 15 high-value subreddits
    "smallbusiness",
    "b2bmarketing",
    "entrepreneur",
    "freelance",
    "consulting",
    "digitalmarketing",
    "ecommerce",
    "webdev",
    "socialmedia",
    "projectmanagement",
    "productivity",
    "contractors",
    "accounting",
    "marketing",
    "sales"
]

def main():
    print("\n" + "="*80)
    print("SIMPLE SCALE-UP: COLLECT 1000+ POSTS FOR THRESHOLD 70+")
    print("="*80)

    print("\nCurrent State: 594 submissions")
    print("Target: 1000+ total submissions")
    print("Strategy:")
    print(f"  • {len(ULTRA_PREMIUM_SUBREDDITS)} subreddits (increased from 7)")
    print("  • Limit: 1000 posts per subreddit (increased from 200)")
    print("  • Sort type: top (quality focus)")
    print("  • Expected: 1000-2000 total posts")

    print("\n" + "="*80)
    print("SUBREDDITS")
    print("="*80)

    # Group by category
    categories = {
        "Investment/VC": ["venturecapital", "financialindependence", "investing", "realestateinvesting"],
        "Business": ["startups", "business", "smallbusiness", "entrepreneur"],
        "Tech/SaaS": ["SaaS", "webdev", "productivity", "projectmanagement"],
        "Marketing/Sales": ["b2bmarketing", "digitalmarketing", "ecommerce", "socialmedia", "marketing", "sales"],
        "Services": ["freelance", "consulting", "contractors", "accounting"]
    }

    for category, subs in categories.items():
        print(f"\n{category}:")
        for sub in subs:
            print(f"  r/{sub}")

    all_posts = []
    subreddit_stats = {}

    print("\n" + "="*80)
    print("COLLECTING")
    print("="*80)

    # Use higher limit per subreddit
    LIMIT_PER_SUBREDDIT = 1000  # Increased from 200

    for subreddit_name in ULTRA_PREMIUM_SUBREDDITS:
        print(f"\n{'='*80}")
        print(f"Collecting from r/{subreddit_name}...")
        print(f"Limit: {LIMIT_PER_SUBREDDIT} posts")
        print(f"{'='*80}")

        try:
            posts = collect_problem_posts(
                subreddits=[subreddit_name],
                limit=LIMIT_PER_SUBREDDIT,
                sort_type="top",  # Use "top" for quality
                test_mode=False
            )

            # Add metadata
            for post in posts:
                post['collection_phase'] = 'Simple Scale 70+ Test'
                post['collection_date'] = datetime.now().isoformat()
                post['subreddit_type'] = 'ultra_premium_extended'
                post['pain_signals'] = ['scaling', 'automation', 'efficiency', 'pain_point']
                post['monetization_tier'] = 'High'

            all_posts.extend(posts)
            subreddit_stats[subreddit_name] = len(posts)

            print(f"✓ Collected {len(posts)} posts from r/{subreddit_name}")
            print(f"  Total posts so far: {len(all_posts)}")

        except Exception as e:
            print(f"✗ Error collecting from r/{subreddit_name}: {e}")
            subreddit_stats[subreddit_name] = 0
            continue

    print(f"\n{'='*80}")
    print("LOADING TO SUPABASE")
    print(f"{'='*80}")

    if all_posts:
        try:
            load_submissions_to_supabase(all_posts)
            print(f"\n✅ SUCCESS: Loaded {len(all_posts)} posts to Supabase")
            print(f"  - Subreddits: {len(ULTRA_PREMIUM_SUBREDDITS)}")
            print(f"  - New posts: {len(all_posts)}")
            print(f"  - Database now: ~{594 + len(all_posts)} submissions")
            print("  - DLT deduplication: Active")

            # Print subreddit breakdown
            print("\n  Subreddit breakdown:")
            for sub, count in subreddit_stats.items():
                if count > 0:
                    print(f"    r/{sub}: {count} posts")

        except Exception as e:
            print(f"\n✗ Error loading to Supabase: {e}")
            raise
    else:
        print("\n⚠️  No posts collected")
        return

    print("\n" + "="*80)
    print("COLLECTION SUMMARY - SIMPLE SCALE 70+ TEST")
    print("="*80)
    print("Simple Scale Collection Complete!")
    print(f"New posts collected: {len(all_posts)}")
    print(f"Database total: ~{594 + len(all_posts)} submissions")
    print(f"Target reached: {'✅ YES' if 594 + len(all_posts) >= 1000 else '❌ NO'}")
    print()
    print("Expected Results:")
    if 594 + len(all_posts) >= 2000:
        print("  • High probability of finding 70+ scores (1-5 opportunities)")
        print("  • Massive scale should reveal exceptional opportunities")
    elif 594 + len(all_posts) >= 1000:
        print("  • Good chance of finding 60+ scores")
        print("  • May need more for 70+")
    else:
        print("  • Need more data to reach meaningful scale")
    print()
    print("Next step: Run batch scoring with threshold 70.0")
    print("  export SCORE_THRESHOLD=70.0")
    print("  python3 scripts/batch_opportunity_scoring.py")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
