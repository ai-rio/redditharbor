#!/usr/bin/env python3
"""
Advanced Niche Collection - High-Value Subreddit Testing
Based on enhanced-chunks Scenario 1: Custom Subreddit Focus

Targets high-stakes subreddits with VC-level problems and urgent pain points
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv(project_root / '.env.local')

import dlt

from core.dlt import PK_ID
from core.dlt_collection import collect_problem_posts

# High-value niches from enhanced-chunks documentation
HIGH_VALUE_NICHES = {
    "venturecapital": {
        "description": "VC-level startup insights and funding challenges",
        "priority": "EXTREME",
        "expected_pain_level": "Very High",
        "monetization_potential": "Enterprise ($1M+ ARR)"
    },
    "biotech": {
        "description": "High-regulation, high-value biotech problems",
        "priority": "EXTREME",
        "expected_pain_level": "Very High",
        "monetization_potential": "Enterprise ($500K+ ARR)"
    },
    "cybersecurity": {
        "description": "Urgent, high-cost security problems",
        "priority": "HIGH",
        "expected_pain_level": "High",
        "monetization_potential": "Enterprise ($250K+ ARR)"
    },
    "realestateinvesting": {
        "description": "High-stakes financial decisions and investments",
        "priority": "HIGH",
        "expected_pain_level": "High",
        "monetization_potential": "B2B SaaS ($100K+ ARR)"
    },
    "financialcareers": {
        "description": "Career transition pain points in finance",
        "priority": "HIGH",
        "expected_pain_level": "High",
        "monetization_potential": "B2C SaaS ($50K+ ARR)"
    },
    "productmanagement": {
        "description": "Product strategy and growth challenges",
        "priority": "HIGH",
        "expected_pain_level": "Medium-High",
        "monetization_potential": "B2B SaaS ($100K+ ARR)"
    },
    "datascience": {
        "description": "Advanced analytics and ML implementation challenges",
        "priority": "MEDIUM-HIGH",
        "expected_pain_level": "Medium-High",
        "monetization_potential": "B2B SaaS ($150K+ ARR)"
    },
    "devops": {
        "description": "Infrastructure and scaling pain points",
        "priority": "MEDIUM-HIGH",
        "expected_pain_level": "Medium-High",
        "monetization_potential": "B2B SaaS ($200K+ ARR)"
    }
}

def collect_niche_data(niches: dict, posts_per_niche: int = 100, sort_type: str = "top") -> dict:
    """
    Collect data from high-value niche subreddits

    Args:
        niches: Dictionary of niche configurations
        posts_per_niche: Number of posts to collect per niche
        sort_type: "hot", "top", or "new"

    Returns:
        Collection results and analysis
    """
    print("=" * 80)
    print("ADVANCED NICHE COLLECTION - High-Value Subreddit Testing")
    print("=" * 80)
    print(f"Target niches: {len(niches)}")
    print(f"Posts per niche: {posts_per_niche}")
    print(f"Sort type: {sort_type}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    start_time = time.time()
    all_posts = []
    niche_results = {}

    for niche_name, niche_config in niches.items():
        print(f"\n{'='*60}")
        print(f"PROCESSING NICHE: r/{niche_name}")
        print(f"Priority: {niche_config['priority']}")
        print(f"Description: {niche_config['description']}")
        print(f"Expected Pain: {niche_config['expected_pain_level']}")
        print(f"Monetization: {niche_config['monetization_potential']}")
        print(f"{'='*60}")

        try:
            # Collect posts from this niche
            posts = collect_problem_posts(
                subreddits=[niche_name],
                limit=posts_per_niche,
                sort_type=sort_type
            )

            # Store niche results
            niche_results[niche_name] = {
                "posts_collected": len(posts),
                "priority": niche_config['priority'],
                "expected_pain": niche_config['expected_pain_level'],
                "monetization": niche_config['monetization_potential'],
                "success": True
            }

            all_posts.extend(posts)
            print(f"✅ Collected {len(posts)} posts from r/{niche_name}")

            # Rate limiting
            time.sleep(2)

        except Exception as e:
            print(f"❌ Failed to collect from r/{niche_name}: {e}")
            niche_results[niche_name] = {
                "posts_collected": 0,
                "error": str(e),
                "success": False
            }

    # Load all posts to database
    print(f"\n{'='*60}")
    print("LOADING TO DATABASE")
    print(f"{'='*60}")

    try:
        # Load to database using DLT pipeline with proper schema handling
        # Transform posts to match DLT schema expectations
        transformed_posts = []
        for post in all_posts:
            transformed_post = {
                'id': post.get('id', ''),
                'title': post.get('title', ''),
                'selftext': post.get('selftext', ''),
                'url': post.get('url', ''),
                'subreddit': post.get('subreddit', ''),
                'score': post.get('score', 0),
                'num_comments': post.get('num_comments', 0),
                'created_utc': post.get('created_utc', 0),
                'author': post.get('author', ''),
                'is_self': post.get('is_self', False),
                'collected_at': datetime.now().isoformat()
            }
            transformed_posts.append(transformed_post)

        # Create custom pipeline with new dataset to avoid schema conflicts
        connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

        pipeline = dlt.pipeline(
            pipeline_name="niche_collection_pipeline",
            destination=dlt.destinations.postgres(connection_string),
            dataset_name="niche_reddit_data"  # New dataset name
        )

        load_info = pipeline.run(
            transformed_posts,
            table_name="niche_submissions",
            write_disposition="append",
            primary_key=PK_ID
        )
        loaded_count = len(transformed_posts)
        print(f"✅ Loaded {loaded_count} posts to database via DLT (table: niche_submissions)")

    except Exception as e:
        print(f"❌ Failed to load to database: {e}")
        loaded_count = 0

    collection_time = time.time() - start_time

    # Analysis
    print(f"\n{'='*80}")
    print("NICHE COLLECTION ANALYSIS")
    print(f"{'='*80}")

    successful_niches = [n for n, r in niche_results.items() if r.get('success', False)]
    total_collected = sum(r.get('posts_collected', 0) for r in niche_results.values())

    print(f"✅ Collection completed in {collection_time:.2f}s")
    print(f"  - Total niches targeted: {len(niches)}")
    print(f"  - Successful niches: {len(successful_niches)}")
    print(f"  - Total posts collected: {total_collected}")
    print(f"  - Posts loaded to DB: {loaded_count}")
    print(f"  - Collection rate: {total_collected/collection_time:.1f} posts/sec")
    print(f"  - Success rate: {len(successful_niches)/len(niches)*100:.1f}%")

    # Priority breakdown
    print("\n📊 BREAKDOWN BY PRIORITY:")
    priority_counts = {}
    for niche_name, result in niche_results.items():
        if result.get('success', False):
            priority = result.get('priority', 'UNKNOWN')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

    for priority, count in sorted(priority_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {priority}: {count} niches")

    # High-priority niches that failed
    failed_high_priority = [
        n for n, r in niche_results.items()
        if not r.get('success', False) and niches.get(n, {}).get('priority') in ['HIGH', 'EXTREME']
    ]

    if failed_high_priority:
        print("\n⚠️  HIGH-PRIORITY FAILURES:")
        for niche in failed_high_priority:
            print(f"  - r/{niche}: {niche_results[niche].get('error', 'Unknown error')}")

    return {
        "total_posts": total_collected,
        "loaded_posts": loaded_count,
        "successful_niches": len(successful_niches),
        "collection_time": collection_time,
        "niche_results": niche_results,
        "posts": all_posts
    }

def main():
    """Main execution"""
    print("RedditHarbor Advanced Niche Collection")
    print("Based on Enhanced Implementation Strategy - Scenario 1")
    print("")

    # Collect from high-value niches
    results = collect_niche_data(
        niches=HIGH_VALUE_NICHES,
        posts_per_niche=100,  # Higher limit for niche exploration
        sort_type="top"       # Focus on high-engagement content
    )

    if results["total_posts"] > 0:
        print("\n🎉 ADVANCED NICHE COLLECTION SUCCESS!")
        print(f"Collected {results['total_posts']} posts from {results['successful_niches']} high-value niches")
        print("Next step: Run AI opportunity analysis with SCORE_THRESHOLD=35.0")
        print("Command: SCORE_THRESHOLD=35.0 python scripts/batch_opportunity_scoring.py")
        return True
    else:
        print("\n⚠️  No posts collected from niche subreddits")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
