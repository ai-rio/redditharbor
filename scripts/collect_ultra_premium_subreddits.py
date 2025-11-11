#!/usr/bin/env python3
"""
Ultra-Premium Collection Script for Phase 5: 50+ Score Validation
Targets subreddits with the highest monetization potential and exceptional pain
Goal: Scale to 250+ posts to find 1-2 opportunities at 50+
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
# Target: 250+ total posts (136 current + 120+ new = 256 total)
ULTRA_PREMIUM_SUBREDDITS = {
    "venturecapital": {
        "description": "VC-level investment pain, ultra-high stakes",
        "limit": 30,
        "pain_signals": ["deal flow", "due diligence", "portfolio", "valuation", "fund management"],
        "monetization": "Ultra-high ($100-500/month)"
    },
    "financialindependence": {
        "description": "High net worth individuals, strong pain signals",
        "limit": 40,
        "pain_signals": ["portfolio management", "tax optimization", "retirement planning", "wealth"],
        "monetization": "High ($49-199/month)"
    },
    "startups": {
        "description": "Startup founders, proven willingness to pay",
        "limit": 30,
        "pain_signals": ["scaling", "funding", "customer acquisition", "retention", "growth"],
        "monetization": "High ($29-99/month)"
    },
    "investing": {
        "description": "Investment strategy and portfolio pain",
        "limit": 25,
        "pain_signals": ["portfolio", "asset allocation", "risk management", "market timing"],
        "monetization": "Medium-High ($19-79/month)"
    },
    "business": {
        "description": "General business operational pain",
        "limit": 25,
        "pain_signals": ["operations", "management", "growth", "efficiency", "process"],
        "monetization": "Medium ($19-49/month)"
    }
}

def main():
    print("\n" + "="*80)
    print("PHASE 5: ULTRA-PREMIUM COLLECTION FOR 50+ SCORE VALIDATION")
    print("="*80)
    print("\nCurrent State: 136 submissions")
    print("Target: 250+ submissions (need ~120 more)")
    print("Goal: Find 1-2 opportunities at 50+ scores")
    print("\nUltra-Premium Strategy:")
    print("  • VC-level pain (venturecapital)")
    print("  • High net worth (financialindependence)")
    print("  • Serial entrepreneurs (startups)")
    print("  • Investment professionals (investing)")
    print("  • Business operators (business)")

    print("\n" + "="*80)
    print("TARGET SUBREDDITS")
    print("="*80)
    for sub, info in ULTRA_PREMIUM_SUBREDDITS.items():
        print(f"  r/{sub:25} - {info['description']:50} (limit: {info['limit']:2})")
        print(f"    {'':27} Monetization: {info['monetization']}")
    print()

    all_posts = []
    total_collected = 0

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
                post['collection_phase'] = 'Phase 5'
                post['collection_date'] = datetime.now().isoformat()
                post['subreddit_type'] = 'ultra_premium'
                post['pain_signals'] = info.get('pain_signals', [])
                post['monetization_tier'] = info.get('monetization', '')

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
            print(f"  - Subreddits: {list(ULTRA_PREMIUM_SUBREDDITS.keys())}")
            print(f"  - Total posts: {total_collected}")
            print(f"  - Database now: ~{136 + total_collected} submissions")
            print("  - DLT deduplication: Active")

        except Exception as e:
            print(f"\n✗ Error loading to Supabase: {e}")
            raise
    else:
        print("\n⚠️  No posts collected")
        return

    print("\n" + "="*80)
    print("COLLECTION SUMMARY - PHASE 5")
    print("="*80)
    print("Ultra-Premium Collection Complete!")
    print(f"New posts collected: {total_collected}")
    print(f"Database total: ~{136 + total_collected} submissions")
    print(f"Target reached: {'✅ YES' if 136 + total_collected >= 250 else '❌ NO (need more)'}")
    print()
    print("Expected Results:")
    if 136 + total_collected >= 250:
        print("  • 2-5 opportunities at 50+ (1-2% of 250+ posts)")
        print("  • Higher quality opportunities from ultra-premium data")
        print("  • Guide validation for 50+ threshold")
    else:
        print("  • May need additional collection to reach 250+")
    print()
    print("Next step: Run batch scoring with threshold 50.0")
    print("  export SCORE_THRESHOLD=50.0")
    print("  python3 scripts/batch_opportunity_scoring.py")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
