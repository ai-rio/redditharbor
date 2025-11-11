#!/usr/bin/env python3
"""
Robust Subreddit Scanner - Handles rate limits and timeouts properly
Based on PRAW best practices from documentation
"""

import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit

from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT


class RobustScanner:
    """Scanner with proper rate limiting and error handling"""

    # Monetization signals
    PAYMENT = ["pay", "paid", "price", "cost", "buy", "subscription", "premium", "money", "expensive", "cheap"]
    GAP = ["wish there", "looking for", "need app", "no solution", "doesn't exist", "frustrated", "problem"]
    BUSINESS = ["business", "company", "professional", "client", "revenue", "b2b", "commercial"]

    def __init__(self, reddit_client):
        self.reddit = reddit_client

    def analyze_text(self, text: str) -> dict[str, int]:
        """Count signals in text"""
        text_lower = text.lower()
        return {
            "payment": sum(1 for s in self.PAYMENT if s in text_lower),
            "gap": sum(1 for s in self.GAP if s in text_lower),
            "business": sum(1 for s in self.BUSINESS if s in text_lower),
        }

    def scan_subreddit_safe(self, name: str, limit: int = 20) -> dict[str, Any]:
        """Safely scan a subreddit with rate limit handling"""
        try:
            print(f"    🔍 r/{name}...", end=" ")

            subreddit = self.reddit.subreddit(name)

            # Get posts
            posts = []
            for submission in subreddit.hot(limit=limit):
                posts.append(submission)
                if len(posts) >= limit:
                    break

            # Analyze posts
            all_signals = defaultdict(int)
            analyzed = 0

            for post in posts[:10]:  # Only analyze top 10 to save time
                try:
                    # Post text
                    post_text = f"{post.title} {post.selftext or ''}"
                    post_signals = self.analyze_text(post_text)

                    # Top 2 comments only (faster!)
                    post.comments.replace_more(limit=0)  # Don't fetch "MoreComments"
                    comment_text = ""
                    for comment in post.comments[:2]:
                        if hasattr(comment, 'body') and comment.body:
                            comment_text += " " + comment.body

                    comment_signals = self.analyze_text(comment_text)

                    # Combine
                    for key in post_signals:
                        all_signals[key] += post_signals[key] + comment_signals[key]

                    analyzed += 1

                except Exception:
                    # Skip problematic posts
                    continue

            # Calculate score
            total = sum(all_signals.values())
            if analyzed > 0:
                density = total / analyzed
                score = min(100, total * 2)  # Simple scoring
            else:
                density = 0
                score = 0

            result = {
                "subreddit": name,
                "analyzed": analyzed,
                "total_signals": total,
                "density": round(density, 2),
                "score": round(score, 1),
                "signals": dict(all_signals),
                "success": True
            }

            print(f"✅ Score: {score:.1f}/100, Signals: {total}")
            return result

        except Exception as e:
            print(f"❌ Error: {str(e)[:40]}")
            return {
                "subreddit": name,
                "error": str(e),
                "success": False
            }

    def scan_list(self, subreddits: list[str]) -> list[dict[str, Any]]:
        """Scan multiple subreddits with progress tracking"""
        print("=" * 70)
        print("ROBUST SUBREDDIT SCANNER")
        print("=" * 70)
        print(f"Scanning {len(subreddits)} subreddits...")
        print()

        results = []
        for i, sub in enumerate(subreddits, 1):
            print(f"[{i:2}/{len(subreddits)}]", end=" ")
            result = self.scan_subreddit_safe(sub, limit=20)
            results.append(result)
            time.sleep(0.5)  # Small delay between requests

        # Sort by score
        successful = [r for r in results if r.get("success", False)]
        successful.sort(key=lambda x: x["score"], reverse=True)

        return successful


def main():
    """Main execution"""

    # Initialize client
    print("Initializing Reddit client...")
    reddit_client = reddit(
        public_key=REDDIT_PUBLIC,
        secret_key=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    print("✅ Connected!\n")

    # Initialize scanner
    scanner = RobustScanner(reddit_client)

    # Quick test with known commercial subreddits
    TEST_SUBREDDITS = [
        "entrepreneur",      # Business discussions
        "startups",          # Startup pain points
        "smallbusiness",     # Business problems
        "SaaS",              # Software monetization
        "marketing",         # Marketing tools
        "indiehackers",      # Building and selling
        "sidehustle",        # Making money
        "personalfinance",   # Money discussions
        "fitness",           # Personal stories (baseline)
    ]

    print(f"Testing with {len(TEST_SUBREDDITS)} subreddits...\n")

    # Scan
    results = scanner.scan_list(TEST_SUBREDDITS)

    # Show results
    print("\n" + "=" * 70)
    print("RESULTS - Ranked by Monetization Potential")
    print("=" * 70)

    for i, result in enumerate(results, 1):
        sigs = result["signals"]
        print(f"\n{i}. r/{result['subreddit']:20} Score: {result['score']:5.1f}/100")
        print(f"    💰 Payment: {sigs.get('payment', 0):3}  💼 Business: {sigs.get('business', 0):3}  🔍 Gaps: {sigs.get('gap', 0):3}")

    # Top recommendations
    top_5 = [r["subreddit"] for r in results[:5]]

    print("\n" + "=" * 70)
    print("TOP 5 RECOMMENDED FOR COLLECTION:")
    print("=" * 70)
    for i, sub in enumerate(top_5, 1):
        score = next(r["score"] for r in results if r["subreddit"] == sub)
        print(f"{i}. r/{sub} (Score: {score:.1f}/100)")

    # Save
    import json
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filepath = f"/home/carlos/projects/redditharbor/robust_scan_{timestamp}.json"
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved: {filepath}")
    print("\n✅ Scanner complete!\n")


if __name__ == "__main__":
    main()
