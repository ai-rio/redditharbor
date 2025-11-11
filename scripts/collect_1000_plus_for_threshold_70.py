#!/usr/bin/env python3
"""
Scale-Up Collection for Threshold 70+ Testing
Target: 1000+ posts from ultra-premium subreddits
Goal: Find exceptional opportunities at 70+ scores (top 0.1%)

Based on E2E guide findings:
- 60+ scores may require 1000+ posts
- 70+ scores are exceptional (top 0.1%)
- Need VC-level, high-stakes pain from ultra-premium subreddits
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

# Ultra-premium, ultra-high-value subreddits
# Target: 1000+ total posts for 70+ threshold testing
ULTRA_PREMIUM_SUBREDDITS = {
    "venturecapital": {
        "description": "VC-level investment pain, ultra-high stakes",
        "limit": 200,
        "pain_signals": ["deal flow", "due diligence", "portfolio", "valuation", "fund management"],
        "monetization": "Ultra-high ($100-500/month)"
    },
    "financialindependence": {
        "description": "High net worth individuals, strong pain signals",
        "limit": 200,
        "pain_signals": ["portfolio management", "tax optimization", "retirement planning", "wealth"],
        "monetization": "High ($49-199/month)"
    },
    "startups": {
        "description": "Startup founders, proven willingness to pay",
        "limit": 200,
        "pain_signals": ["scaling", "funding", "customer acquisition", "retention", "growth"],
        "monetization": "High ($29-99/month)"
    },
    "investing": {
        "description": "Investment strategy and portfolio pain",
        "limit": 150,
        "pain_signals": ["portfolio", "asset allocation", "risk management", "market timing"],
        "monetization": "Medium-High ($19-79/month)"
    },
    "realestateinvesting": {
        "description": "Real estate investors, high-stakes decisions",
        "limit": 150,
        "pain_signals": ["deal analysis", "market analysis", "financing", "property management"],
        "monetization": "High ($29-99/month)"
    },
    "business": {
        "description": "General business operational pain",
        "limit": 100,
        "pain_signals": ["operations", "management", "growth", "efficiency", "process"],
        "monetization": "Medium ($19-49/month)"
    },
    "SaaS": {
        "description": "Software business pain points",
        "limit": 100,
        "pain_signals": ["churn", "acquisition", "pricing", "mrr", "retention"],
        "monetization": "High ($29-99/month)"
    }
}

def main():
    print("\n" + "="*80)
    print("SCALE-UP: COLLECT 1000+ POSTS FOR THRESHOLD 70+ TESTING")
    print("="*80)
    print("\nCurrent State: 217 submissions")
    print("Target: 1000+ total submissions (need ~800+ more)")
    print("Goal: Find 1-5 opportunities at 70+ scores (top 0.1%)")
    print("\nUltra-Premium Strategy:")
    print("  • VC-level pain (venturecapital) - 200 posts")
    print("  • High net worth (financialindependence) - 200 posts")
    print("  • Serial entrepreneurs (startups) - 200 posts")
    print("  • Investment professionals (investing) - 150 posts")
    print("  • Real estate investors (realestateinvesting) - 150 posts")
    print("  • Business operators (business) - 100 posts")
    print("  • SaaS businesses (SaaS) - 100 posts")

    print("\n" + "="*80)
    print("TARGET SUBREDDITS")
    print("="*80)
    total_target = 0
    for sub, info in ULTRA_PREMIUM_SUBREDDITS.items():
        total_target += info['limit']
        print(f"  r/{sub:25} - {info['description']:50} (limit: {info['limit']:3})")
        print(f"    {'':27} Monetization: {info['monetization']}")
    print(f"\n  Total target: {total_target} posts")
    print(f"  Final total: ~{217 + total_target} submissions")
    print()

    all_posts = []
    total_collected = 0
    subreddit_stats = {}

    for subreddit, info in ULTRA_PREMIUM_SUBREDDITS.items():
        print(f"{'='*80}")
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
                post['collection_phase'] = 'Threshold 70+ Scale-Up'
                post['collection_date'] = datetime.now().isoformat()
                post['subreddit_type'] = 'ultra_premium'
                post['pain_signals'] = info.get('pain_signals', [])
                post['monetization_tier'] = info.get('monetization', '')

            all_posts.extend(posts)
            total_collected += len(posts)
            subreddit_stats[subreddit] = len(posts)

            print(f"✓ Collected {len(posts)} posts from r/{subreddit}")
            print(f"  Total posts so far: {total_collected}")

        except Exception as e:
            print(f"✗ Error collecting from r/{subreddit}: {e}")
            subreddit_stats[subreddit] = 0
            continue

    print(f"\n{'='*80}")
    print("LOADING TO SUPABASE")
    print(f"{'='*80}")

    if all_posts:
        try:
            load_submissions_to_supabase(all_posts)
            print(f"\n✅ SUCCESS: Loaded {total_collected} posts to Supabase")
            print(f"  - Subreddits: {list(ULTRA_PREMIUM_SUBREDDITS.keys())}")
            print(f"  - New posts: {total_collected}")
            print(f"  - Database now: ~{217 + total_collected} submissions")
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
    print("COLLECTION SUMMARY - THRESHOLD 70+ SCALE-UP")
    print("="*80)
    print("Ultra-Premium Scale-Up Complete!")
    print(f"New posts collected: {total_collected}")
    print(f"Database total: ~{217 + total_collected} submissions")
    print(f"Target reached: {'✅ YES' if 217 + total_collected >= 1000 else '❌ NO (need more)'}")
    print()
    print("Expected Results:")
    if 217 + total_collected >= 1000:
        print("  • 1-5 opportunities at 70+ (top 0.1% of 1000+ posts)")
        print("  • Exceptional quality from ultra-premium data")
        print("  • Validation of 70+ threshold reality")
    elif 217 + total_collected >= 500:
        print("  • May find some 60+ opportunities")
        print("  • Additional collection may be needed for 70+")
    else:
        print("  • Need more data to reach 1000+ target")
    print()
    print("Next step: Run batch scoring with threshold 70.0")
    print("  export SCORE_THRESHOLD=70.0")
    print("  python3 scripts/batch_opportunity_scoring.py")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
