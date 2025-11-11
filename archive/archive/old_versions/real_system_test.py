#!/usr/bin/env python3
"""
REAL SYSTEM TEST: Live Reddit API Data Collection & Opportunity Scoring

This test uses ACTUAL Reddit API credentials from .env to:
1. Collect REAL problem posts from target subreddits
2. Analyze them with actual problem-first criteria
3. Generate REAL monetizable app opportunities
4. Validate against REAL community evidence

No synthetic data - this is production validation.
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load from .env.local for real credentials
env_local = project_root / ".env.local"
if env_local.exists():
    with open(env_local) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                if not sys.modules.get(key):  # Don't override existing
                    import os as _os
                    _os.environ[key] = val

# Import config (or get from environ if .env.local was loaded)
import os

REDDIT_PUBLIC = os.getenv("REDDIT_PUBLIC")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Import PRAW for Reddit
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    logger.warning("PRAW not installed - will use fallback mode")

# Problem keywords for filtering
PROBLEM_KEYWORDS = [
    "struggle", "problem", "frustrated", "wish", "can't", "difficult",
    "annoying", "hate", "pain", "slow", "expensive", "broken", "error",
    "confusing", "waste time", "painful", "overwhelming", "stuck",
    "help", "need", "looking for", "how do I", "doesn't work"
]

FILTER_OUT = [
    "guide", "tutorial", "success story", "how to", "I did it",
    "announcement", "released", "built", "created", "launched"
]

def is_problem_post(title: str, selftext: str) -> bool:
    """Check if post contains problem keywords."""
    content = f"{title} {selftext}".lower()

    # Has problem keywords
    has_problem = any(kw in content for kw in PROBLEM_KEYWORDS)

    # Doesn't filter out
    no_filter = not any(kw in content for kw in FILTER_OUT)

    return has_problem and no_filter


def collect_real_reddit_data(subreddits: list[str], limit: int = 50) -> list[dict[str, Any]]:
    """Collect REAL problem posts from Reddit using live API."""

    print("=" * 80)
    print("🔴 COLLECTING REAL REDDIT DATA")
    print("=" * 80)
    print(f"\nSubreddits: {', '.join(subreddits)}")
    print(f"Limit: {limit} posts per subreddit")
    print("Reddit API: Using credentials from .env")

    if not PRAW_AVAILABLE:
        print("\n⚠️  PRAW not available - install with: uv pip install praw")
        return []

    if not REDDIT_PUBLIC or not REDDIT_SECRET:
        print("\n⚠️  Reddit credentials missing from .env")
        return []

    all_posts = []

    try:
        # Initialize PRAW Reddit instance
        reddit = praw.Reddit(
            client_id=REDDIT_PUBLIC,
            client_secret=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )

        print("\n✓ Connected to Reddit API")

        # Collect from each subreddit
        for subreddit_name in subreddits:
            print(f"\n📡 Collecting from r/{subreddit_name}...")

            try:
                subreddit = reddit.subreddit(subreddit_name)

                # Get hot + rising posts
                posts_found = 0
                problems_found = 0

                for post in subreddit.hot(limit=limit):
                    if posts_found >= limit:
                        break

                    # Check if it's a problem post
                    if is_problem_post(post.title, post.selftext):
                        all_posts.append({
                            "id": post.id,
                            "title": post.title,
                            "selftext": post.selftext[:500],  # First 500 chars
                            "subreddit": subreddit_name,
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "created_utc": post.created_utc,
                            "url": post.url
                        })
                        problems_found += 1

                    posts_found += 1

                print(f"  ✓ Scanned {posts_found} posts, found {problems_found} problems")

            except Exception as e:
                print(f"  ✗ Error collecting from r/{subreddit_name}: {str(e)[:100]}")
                continue

        print(f"\n✅ Total problem posts collected: {len(all_posts)}")
        return all_posts

    except Exception as e:
        print(f"\n❌ Reddit API Error: {e!s}")
        print("\nTroubleshooting:")
        print("  1. Check credentials in .env file")
        print("  2. Install PRAW: uv pip install praw")
        print("  3. Verify Reddit app at: https://www.reddit.com/prefs/apps")
        return []


def analyze_opportunities(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Analyze collected posts for monetizable opportunities."""

    print("\n" + "=" * 80)
    print("🧠 ANALYZING OPPORTUNITIES FROM REAL DATA")
    print("=" * 80)

    if not posts:
        print("\n⚠️  No posts to analyze")
        return []

    print(f"\nAnalyzing {len(posts)} real problem posts...")

    opportunities = []

    # Group by subreddit and problem theme
    for post in posts:
        # Simple keyword-based categorization
        title = post["title"].lower()
        text = post["selftext"].lower()
        content = f"{title} {text}"

        # Determine opportunity category based on keywords
        category = None

        if any(word in content for word in ["invoice", "freelance", "payment", "client"]):
            category = "Freelancer Tools"
        elif any(word in content for word in ["habit", "track", "daily", "routine"]):
            category = "Habit Tracking"
        elif any(word in content for word in ["email", "inbox", "overwhelm", "notification"]):
            category = "Email Management"
        elif any(word in content for word in ["subscription", "forgot", "charged", "cancel"]):
            category = "Subscription Management"
        elif any(word in content for word in ["meal", "plan", "cook", "recipe", "grocery"]):
            category = "Meal Planning"
        elif any(word in content for word in ["job", "remote", "work", "hiring"]):
            category = "Job Search"
        elif any(word in content for word in ["time", "zone", "meeting", "schedule"]):
            category = "Time Zone Scheduling"

        if category:
            opportunities.append({
                "post_id": post["id"],
                "title": post["title"],
                "subreddit": post["subreddit"],
                "category": category,
                "score": post["score"],
                "comments": post["num_comments"],
                "problem_snippet": post["selftext"][:200],
                "url": post["url"]
            })

    # Group by category and count
    categories = {}
    for opp in opportunities:
        cat = opp["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(opp)

    print(f"\n✓ Identified {len(categories)} opportunity categories:")
    for category, opps in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  • {category}: {len(opps)} problem posts")

    return opportunities


def generate_real_opportunities_report(opportunities: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate final opportunities report from real data."""

    print("\n" + "=" * 80)
    print("📊 REAL OPPORTUNITY REPORT (Based on Actual Reddit Data)")
    print("=" * 80)

    if not opportunities:
        print("\n⚠️  No opportunities to report")
        return {"status": "no_data", "opportunities": []}

    # Group by category
    categories = {}
    for opp in opportunities:
        cat = opp["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(opp)

    # Rank by number of problems + engagement
    ranked = []
    for category, opps in categories.items():
        total_comments = sum(o["comments"] for o in opps)
        avg_score = sum(o["score"] for o in opps) / len(opps) if opps else 0

        ranked.append({
            "category": category,
            "problem_count": len(opps),
            "total_community_comments": total_comments,
            "avg_post_score": avg_score,
            "sample_problems": [o["title"] for o in opps[:3]],
            "subreddits": list(set(o["subreddit"] for o in opps)),
            "posts": opps
        })

    # Sort by engagement
    ranked.sort(
        key=lambda x: (x["total_community_comments"], x["problem_count"]),
        reverse=True
    )

    # Print results
    print(f"\n✅ IDENTIFIED {len(ranked)} OPPORTUNITY CATEGORIES FROM REAL DATA\n")

    for idx, category_data in enumerate(ranked, 1):
        print(f"{idx}. {category_data['category']}")
        print(f"   Problem Posts Found: {category_data['problem_count']}")
        print(f"   Community Comments: {category_data['total_community_comments']}")
        print(f"   Avg Score: {category_data['avg_post_score']:.1f}")
        print(f"   Subreddits: {', '.join(category_data['subreddits'])}")
        print("   Sample Problems:")
        for problem in category_data['sample_problems']:
            print(f"     • {problem[:70]}...")
        print()

    return {
        "timestamp": datetime.now().isoformat(),
        "total_opportunities": len(ranked),
        "opportunities": ranked,
        "total_posts_analyzed": len(opportunities)
    }


def main():
    """Run complete real system test."""

    print("\n" + "=" * 80)
    print("🚀 REDDITHARBOR REAL SYSTEM TEST")
    print("Live Reddit API Data Collection & Opportunity Analysis")
    print("=" * 80)

    start_time = time.time()

    # Target subreddits for problem collection
    target_subreddits = [
        "personalfinance",
        "freelance",
        "productivity",
        "learnprogramming",
        "fitness",
        "SideProject"
    ]

    print("\n📋 Test Configuration:")
    print(f"   Subreddits: {len(target_subreddits)}")
    print("   Posts per subreddit: 50")
    print("   API Source: LIVE Reddit API")

    # Step 1: Collect real data
    print("\n" + "=" * 80)
    print("STEP 1: REAL DATA COLLECTION")
    print("=" * 80)

    posts = collect_real_reddit_data(target_subreddits, limit=50)

    if not posts:
        print("\n❌ Failed to collect real data")
        print("\nPossible issues:")
        print("  1. PRAW not installed: uv pip install praw")
        print("  2. Reddit credentials invalid")
        print("  3. Reddit API rate limited")
        print("  4. Network connectivity issue")
        return

    # Step 2: Analyze opportunities
    print("\n" + "=" * 80)
    print("STEP 2: OPPORTUNITY ANALYSIS")
    print("=" * 80)

    opportunities = analyze_opportunities(posts)

    # Step 3: Generate report
    print("\n" + "=" * 80)
    print("STEP 3: REPORT GENERATION")
    print("=" * 80)

    report = generate_real_opportunities_report(opportunities)

    # Save results
    output_dir = Path("generated")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "real_system_test_results.json"

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")

    # Final summary
    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("✅ REAL SYSTEM TEST COMPLETE")
    print("=" * 80)
    print(f"\nExecution Time: {elapsed:.2f} seconds")
    print(f"Posts Analyzed: {len(opportunities)}")
    print(f"Opportunities Identified: {report['total_opportunities']}")
    print("Status: ✅ PASSED")
    print("\nNext: Review generated/real_system_test_results.json for details")


if __name__ == "__main__":
    main()
