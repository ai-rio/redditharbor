#!/usr/bin/env python3
"""
MASSIVE SCALE COLLECTION FOR THRESHOLD 70+ TESTING
Target: 5000-10000 posts from 20+ ultra-premium subreddits
Goal: Find 70+ scores with maximum data coverage

Reddit API Scaling Strategies:
1. Multiple sort types per subreddit (new, hot, top[time filters], rising)
2. 20+ ultra-premium subreddits
3. limit=None for maximum posts
4. Time-filtered top posts (day, week, month, year, all)
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

# Massive list of ultra-premium, high-pain subreddits
# Target: 20+ subreddits with proven monetization signals
ULTRA_PREMIUM_SUBREDDITS = {
    # VC/Investment (High-stakes, high-value)
    "venturecapital": {
        "limit": 500,  # Increased from 200
        "pain_signals": ["deal flow", "due diligence", "portfolio", "valuation", "fund management"],
        "monetization": "Ultra-high ($100-500/month)"
    },
    "financialindependence": {
        "limit": 500,
        "pain_signals": ["portfolio management", "tax optimization", "retirement planning", "wealth"],
        "monetization": "High ($49-199/month)"
    },
    "investing": {
        "limit": 500,
        "pain_signals": ["portfolio", "asset allocation", "risk management", "market timing"],
        "monetization": "Medium-High ($19-79/month)"
    },
    "realestateinvesting": {
        "limit": 500,
        "pain_signals": ["deal analysis", "market analysis", "financing", "property management"],
        "monetization": "High ($29-99/month)"
    },
    "startups": {
        "limit": 500,
        "pain_signals": ["scaling", "funding", "customer acquisition", "retention", "growth"],
        "monetization": "High ($29-99/month)"
    },
    # Business Operations
    "business": {
        "limit": 400,
        "pain_signals": ["operations", "management", "growth", "efficiency", "process"],
        "monetization": "Medium ($19-49/month)"
    },
    "SaaS": {
        "limit": 400,
        "pain_signals": ["churn", "acquisition", "pricing", "mrr", "retention"],
        "monetization": "High ($29-99/month)"
    },
    "smallbusiness": {
        "limit": 400,
        "pain_signals": ["operations", "marketing", "cash flow", "hiring", "growth"],
        "monetization": "Medium ($19-49/month)"
    },
    "b2bmarketing": {
        "limit": 400,
        "pain_signals": ["lead generation", "conversion", "roi", "customer acquisition"],
        "monetization": "High ($29-99/month)"
    },
    "entrepreneur": {
        "limit": 400,
        "pain_signals": ["scaling", "funding", "customers", "operations", "growth"],
        "monetization": "High ($29-99/month)"
    },
    "freelance": {
        "limit": 400,
        "pain_signals": ["client acquisition", "pricing", "payments", "time management"],
        "monetization": "Medium ($19-49/month)"
    },
    "consulting": {
        "limit": 400,
        "pain_signals": ["client acquisition", "pricing", "project management", "deliverables"],
        "monetization": "High ($29-99/month)"
    },
    # Additional High-Value Niches
    "digitalmarketing": {
        "limit": 300,
        "pain_signals": ["seo", "ppc", "conversion", "roi", "attribution"],
        "monetization": "Medium ($19-49/month)"
    },
    "ecommerce": {
        "limit": 300,
        "pain_signals": ["conversion", "abandonment", "acquisition", "retention"],
        "monetization": "High ($29-99/month)"
    },
    "webdev": {
        "limit": 300,
        "pain_signals": ["performance", "seo", "conversion", "maintenance"],
        "monetization": "Medium ($19-49/month)"
    },
    "socialmedia": {
        "limit": 300,
        "pain_signals": ["engagement", "growth", "conversion", "roi"],
        "monetization": "Medium ($19-49/month)"
    },
    "projectmanagement": {
        "limit": 300,
        "pain_signals": ["coordination", "deadlines", "resources", "stakeholders"],
        "monetization": "Medium ($19-49/month)"
    },
    "productivity": {
        "limit": 300,
        "pain_signals": ["time management", "automation", "workflow", "efficiency"],
        "monetization": "Medium ($19-49/month)"
    },
    "contractors": {
        "limit": 300,
        "pain_signals": ["leads", "pricing", "project management", "payments"],
        "monetization": "High ($29-99/month)"
    },
    "accounting": {
        "limit": 300,
        "pain_signals": ["taxes", "bookkeeping", "cash flow", "reporting"],
        "monetization": "High ($29-99/month)"
    }
}

# Time filters for top posts (get top posts from different periods)
TIME_FILTERS = ["day", "week", "month", "year", "all"]

# Sort types to collect for maximum coverage
SORT_TYPES = ["top"]  # Focus on top posts for quality

def collect_from_subreddit_all_sort_types(subreddit_name: str, base_limit: int) -> list[dict]:
    """
    Collect from a subreddit using multiple sort types and time filters.
    
    Args:
        subreddit_name: Name of subreddit
        base_limit: Base limit per sort type
    
    Returns:
        List of all collected posts
    """
    all_posts = []

    # Calculate per-type limit
    posts_per_type = max(50, base_limit // 10)  # Distribute across ~10 different sort types

    print(f"\n  Collecting from r/{subreddit_name}...")
    print(f"    Base limit: {base_limit}")
    print(f"    Posts per sort type: {posts_per_type}")

    # 1. Top posts with different time filters
    for time_filter in TIME_FILTERS:
        try:
            posts = collect_problem_posts(
                subreddits=[subreddit_name],
                limit=posts_per_type,
                sort_type="top",
                test_mode=False
            )

            if posts:
                all_posts.extend(posts)
                print(f"    ✓ top({time_filter}): {len(posts)} posts")
        except Exception as e:
            print(f"    ✗ Error with top({time_filter}): {e}")

    # 2. Hot posts
    try:
        posts = collect_problem_posts(
            subreddits=[subreddit_name],
            limit=posts_per_type,
            sort_type="hot",
            test_mode=False
        )
        if posts:
            all_posts.extend(posts)
            print(f"    ✓ hot: {len(posts)} posts")
    except Exception as e:
        print(f"    ✗ Error with hot: {e}")

    # 3. Rising posts
    try:
        posts = collect_problem_posts(
            subreddits=[subreddit_name],
            limit=posts_per_type,
            sort_type="rising",
            test_mode=False
        )
        if posts:
            all_posts.extend(posts)
            print(f"    ✓ rising: {len(posts)} posts")
    except Exception as e:
        print(f"    ✗ Error with rising: {e}")

    # 4. New posts (recent problems)
    try:
        posts = collect_problem_posts(
            subreddits=[subreddit_name],
            limit=posts_per_type,
            sort_type="new",
            test_mode=False
        )
        if posts:
            all_posts.extend(posts)
            print(f"    ✓ new: {len(posts)} posts")
    except Exception as e:
        print(f"    ✗ Error with new: {e}")

    print(f"  Total from r/{subreddit_name}: {len(all_posts)} posts")
    return all_posts

def main():
    print("\n" + "="*80)
    print("MASSIVE SCALE COLLECTION FOR THRESHOLD 70+ TESTING")
    print("="*80)

    total_target = sum(info['limit'] for info in ULTRA_PREMIUM_SUBREDDITS.values())

    print("\nCurrent State: 594 submissions")
    print(f"Target: {total_target} posts from {len(ULTRA_PREMIUM_SUBREDDITS)} subreddits")
    print("Goal: Find 70+ scores with maximum data coverage")
    print("\nStrategy:")
    print("  • Multiple sort types per subreddit (top[time filters] + hot + rising + new)")
    print(f"  • {len(ULTRA_PREMIUM_SUBREDDITS)} ultra-premium subreddits")
    print("  • Expected total: 10,000-15,000 posts")
    print("  • Expected problem posts: 1,000-3,000 (10-20% filter rate)")

    print("\n" + "="*80)
    print("SUBREDDIT STRATEGY")
    print("="*80)

    # Group by category
    categories = {
        "VC/Investment": ["venturecapital", "financialindependence", "investing", "realestateinvesting", "startups"],
        "Business Operations": ["business", "SaaS", "smallbusiness", "b2bmarketing", "entrepreneur", "freelance", "consulting"],
        "Niche Services": ["digitalmarketing", "ecommerce", "webdev", "socialmedia", "projectmanagement", "productivity", "contractors", "accounting"]
    }

    for category, subs in categories.items():
        print(f"\n{category}:")
        for sub in subs:
            if sub in ULTRA_PREMIUM_SUBREDDITS:
                info = ULTRA_PREMIUM_SUBREDDITS[sub]
                print(f"  r/{sub:25} - {info['limit']:3} posts - {info['monetization']}")

    all_posts = []
    subreddit_stats = {}

    print("\n" + "="*80)
    print("COLLECTING FROM ALL SUBREDDITS")
    print("="*80)

    for subreddit_name, info in ULTRA_PREMIUM_SUBREDDITS.items():
        print(f"\n{'='*80}")
        print(f"Processing r/{subreddit_name}...")
        print(f"{'='*80}")

        try:
            posts = collect_from_subreddit_all_sort_types(subreddit_name, info['limit'])

            # Add metadata
            for post in posts:
                post['collection_phase'] = 'Massive Scale 70+ Test'
                post['collection_date'] = datetime.now().isoformat()
                post['subreddit_type'] = 'ultra_premium'
                post['pain_signals'] = info.get('pain_signals', [])
                post['monetization_tier'] = info.get('monetization', '')

            all_posts.extend(posts)
            subreddit_stats[subreddit_name] = len(posts)

        except Exception as e:
            print(f"✗ Error processing r/{subreddit_name}: {e}")
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
    print("COLLECTION SUMMARY - MASSIVE SCALE 70+ TEST")
    print("="*80)
    print("Massive Scale Collection Complete!")
    print(f"New posts collected: {len(all_posts)}")
    print(f"Database total: ~{594 + len(all_posts)} submissions")
    print(f"Target reached: {'✅ YES' if 594 + len(all_posts) >= 1000 else '❌ NO'}")
    print()
    print("Expected Results:")
    if 594 + len(all_posts) >= 5000:
        print("  • High probability of finding 70+ scores (1-5 opportunities)")
        print("  • Exceptional quality from diverse, high-pain data")
        print("  • Validation of 70+ threshold with massive scale")
    elif 594 + len(all_posts) >= 1000:
        print("  • Good chance of finding some 60+ scores")
        print("  • May need more data for 70+")
    else:
        print("  • Need more data to reach meaningful scale")
    print()
    print("Next step: Run batch scoring with threshold 70.0")
    print("  export SCORE_THRESHOLD=70.0")
    print("  python3 scripts/batch_opportunity_scoring.py")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
