#!/usr/bin/env python3
"""
Collect Commercial Data with DLT Pipeline

This script collects Reddit data from business-focused subreddits using the DLT pipeline
with commercial signal detection for monetizable app discovery.

Features:
- DLT-powered collection with problem keyword filtering
- Commercial signal detection (business keywords, monetization indicators)
- Deduplication via merge write disposition
- Batch loading to Supabase
- Statistics reporting

Target Subreddits:
- smallbusiness: Small business owners and entrepreneurs
- startups: Startup founders and team members
- SaaS: Software as a Service discussions
- entrepreneur: General entrepreneurship
- indiehackers: Independent software builders

Usage:
    # Collect with default settings
    python scripts/collect_commercial_data.py

    # Collect with custom limit
    python scripts/collect_commercial_data.py --limit 100

    # Test mode (no API calls)
    python scripts/collect_commercial_data.py --test
"""

import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import DLT collection functions
from core.dlt_collection import collect_problem_posts, load_to_supabase

# Commercial and monetization keywords for filtering
BUSINESS_KEYWORDS = [
    "business", "company", "professional", "client", "revenue", "b2b", "commercial",
    "customer", "sales", "profit", "growth", "market", "product", "service",
    "startup", "founder", "entrepreneur", "venture", "funding", "investor"
]

MONETIZATION_KEYWORDS = [
    "pay", "price", "cost", "subscription", "premium", "upgrade", "paid", "free trial",
    "freemium", "one-time", "monthly", "yearly", "affordable", "expensive", "worth it",
    "value", "budget", "investment", "roi", "return", "savings", "cheaper", "cheapest",
    "revenue", "profit", "income", "earnings", "money", "dollar", "pricing"
]

# Top 5 business-focused subreddits for commercial data collection
TOP_COMMERCIAL_SUBREDDITS = [
    "smallbusiness",
    "startups",
    "SaaS",
    "entrepreneur",
    "indiehackers"
]


def contains_commercial_keywords(text: str, min_keywords: int = 1) -> bool:
    """
    Check if text contains commercial/business keywords.

    Args:
        text: Text to check
        min_keywords: Minimum number of commercial keywords required

    Returns:
        True if text contains at least min_keywords commercial keywords
    """
    if not text:
        return False

    text_lower = text.lower()
    found_keywords = []

    # Check business keywords
    for keyword in BUSINESS_KEYWORDS:
        if keyword in text_lower:
            found_keywords.append(keyword)

    # Check monetization keywords
    for keyword in MONETIZATION_KEYWORDS:
        if keyword in text_lower:
            found_keywords.append(keyword)

    return len(found_keywords) >= min_keywords


def filter_commercial_posts(
    problem_posts: list[dict[str, Any]],
    min_commercial_keywords: int = 1
) -> list[dict[str, Any]]:
    """
    Filter problem posts for commercial relevance.

    Keeps posts that contain both:
    1. Problem keywords (from collect_problem_posts)
    2. Commercial/business keywords

    Args:
        problem_posts: List of problem posts from DLT collection
        min_commercial_keywords: Minimum commercial keywords required

    Returns:
        List of commercially-relevant problem posts
    """
    commercial_posts = []

    for post in problem_posts:
        # Combine title and selftext for analysis
        full_text = f"{post.get('title', '')} {post.get('selftext', '')}"

        # Check for commercial keywords
        if contains_commercial_keywords(full_text, min_commercial_keywords):
            # Extract found commercial keywords
            full_text_lower = full_text.lower()
            found_business = [kw for kw in BUSINESS_KEYWORDS if kw in full_text_lower]
            found_monetization = [kw for kw in MONETIZATION_KEYWORDS if kw in full_text_lower]
            all_commercial_keywords = list(set(found_business + found_monetization))

            # Add commercial metadata
            post["commercial_keywords_found"] = all_commercial_keywords
            post["commercial_keyword_count"] = len(all_commercial_keywords)
            post["business_keywords"] = found_business
            post["monetization_keywords"] = found_monetization

            commercial_posts.append(post)

    return commercial_posts


def collect_commercial_data(
    subreddits: list[str] = None,
    limit: int = 50,
    sort_type: str = "hot",
    test_mode: bool = False
) -> dict[str, Any]:
    """
    Collect commercial data from business-focused subreddits.

    Args:
        subreddits: List of subreddit names (default: TOP_COMMERCIAL_SUBREDDITS)
        limit: Maximum posts to collect per subreddit
        sort_type: Reddit sort type ('hot', 'new', 'top', 'rising')
        test_mode: If True, use test data instead of real API calls

    Returns:
        Dictionary with collection statistics
    """
    if subreddits is None:
        subreddits = TOP_COMMERCIAL_SUBREDDITS

    print("=" * 80)
    print("COLLECTING HIGH-VALUE COMMERCIAL DATA WITH DLT PIPELINE")
    print("=" * 80)
    print()
    print(f"Target subreddits: {', '.join(subreddits)}")
    print("Collection parameters:")
    print(f"  - Posts per subreddit: {limit}")
    print(f"  - Sort type: {sort_type}")
    print(f"  - Test mode: {test_mode}")
    print()

    # Step 1: Collect problem posts using DLT
    print("📡 Step 1: Collecting problem posts via DLT pipeline...")
    print("-" * 80)
    start_time = time.time()

    problem_posts = collect_problem_posts(
        subreddits=subreddits,
        limit=limit,
        sort_type=sort_type,
        test_mode=test_mode
    )

    collection_time = time.time() - start_time

    if not problem_posts:
        print("\n✗ No problem posts collected")
        return {
            "success": False,
            "total_collected": 0,
            "commercial_posts": 0,
            "collection_time": collection_time
        }

    print(f"\n✓ Collected {len(problem_posts)} problem posts in {collection_time:.2f}s")

    # Step 2: Filter for commercial relevance
    print("\n📊 Step 2: Filtering for commercial relevance...")
    print("-" * 80)

    commercial_posts = filter_commercial_posts(problem_posts, min_commercial_keywords=1)

    print(f"✓ Identified {len(commercial_posts)} commercially-relevant posts")
    print(f"  - Filter rate: {len(commercial_posts)/len(problem_posts)*100:.1f}%")

    if not commercial_posts:
        print("\n⚠️  No commercially-relevant posts found")
        return {
            "success": False,
            "total_collected": len(problem_posts),
            "commercial_posts": 0,
            "collection_time": collection_time
        }

    # Step 3: Load to Supabase via DLT with deduplication
    print("\n💾 Step 3: Loading commercial data to Supabase via DLT...")
    print("-" * 80)

    load_start = time.time()
    success = load_to_supabase(commercial_posts, write_mode="merge")
    load_time = time.time() - load_start

    if success:
        print(f"✓ Successfully loaded {len(commercial_posts)} commercial posts")
        print("  - Table: submissions")
        print("  - Write mode: merge (deduplication enabled)")
        print(f"  - Load time: {load_time:.2f}s")
    else:
        print("✗ Failed to load commercial posts to Supabase")

    # Step 4: Report statistics
    print("\n" + "=" * 80)
    print("COLLECTION STATISTICS")
    print("=" * 80)

    total_time = collection_time + load_time

    # Calculate keyword statistics
    total_commercial_keywords = sum(
        post.get("commercial_keyword_count", 0) for post in commercial_posts
    )
    avg_commercial_keywords = total_commercial_keywords / len(commercial_posts) if commercial_posts else 0

    total_problem_keywords = sum(
        post.get("problem_keyword_count", 0) for post in commercial_posts
    )
    avg_problem_keywords = total_problem_keywords / len(commercial_posts) if commercial_posts else 0

    stats = {
        "success": success,
        "total_collected": len(problem_posts),
        "commercial_posts": len(commercial_posts),
        "filter_rate": len(commercial_posts) / len(problem_posts) * 100 if problem_posts else 0,
        "collection_time": collection_time,
        "load_time": load_time,
        "total_time": total_time,
        "avg_commercial_keywords": avg_commercial_keywords,
        "avg_problem_keywords": avg_problem_keywords,
        "subreddits_processed": len(subreddits)
    }

    print("\nCollection Performance:")
    print(f"  - Total posts collected: {stats['total_collected']}")
    print(f"  - Commercial posts: {stats['commercial_posts']}")
    print(f"  - Filter rate: {stats['filter_rate']:.1f}%")
    print(f"  - Collection time: {stats['collection_time']:.2f}s")
    print(f"  - Load time: {stats['load_time']:.2f}s")
    print(f"  - Total time: {stats['total_time']:.2f}s")
    print("\nKeyword Analysis:")
    print(f"  - Avg commercial keywords per post: {stats['avg_commercial_keywords']:.1f}")
    print(f"  - Avg problem keywords per post: {stats['avg_problem_keywords']:.1f}")
    print("\nSubreddits Processed:")
    for subreddit in subreddits:
        subreddit_posts = [p for p in commercial_posts if p.get("subreddit") == subreddit]
        print(f"  - r/{subreddit}: {len(subreddit_posts)} commercial posts")

    # Sample of collected posts
    if commercial_posts:
        print("\n" + "=" * 80)
        print("SAMPLE COMMERCIAL POSTS")
        print("=" * 80)

        for i, post in enumerate(commercial_posts[:3], 1):
            print(f"\n[{i}] r/{post.get('subreddit')} | Score: {post.get('score')}")
            print(f"Title: {post.get('title', '')[:100]}")
            print(f"Problem Keywords: {', '.join(post.get('problem_keywords_found', [])[:5])}")
            print(f"Commercial Keywords: {', '.join(post.get('commercial_keywords_found', [])[:5])}")
            print(f"Text: {post.get('selftext', '')[:150]}...")

    print("\n" + "=" * 80)
    print("COLLECTION COMPLETE!")
    print("=" * 80)
    print("\nNext step: Analyze commercial signals with OpportunityAnalyzerAgent")
    print()

    return stats


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect commercial data from business-focused subreddits using DLT pipeline"
    )
    parser.add_argument(
        "--subreddits",
        nargs="+",
        default=TOP_COMMERCIAL_SUBREDDITS,
        help="Subreddit names to collect from (default: business-focused subreddits)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Posts to collect per subreddit (default: 50)"
    )
    parser.add_argument(
        "--sort",
        type=str,
        default="hot",
        choices=["new", "hot", "top", "rising"],
        help="Sort type for posts (default: hot)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use test data instead of real API calls"
    )

    args = parser.parse_args()

    # Run collection
    stats = collect_commercial_data(
        subreddits=args.subreddits,
        limit=args.limit,
        sort_type=args.sort,
        test_mode=args.test
    )

    # Exit with appropriate status code
    return 0 if stats["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
