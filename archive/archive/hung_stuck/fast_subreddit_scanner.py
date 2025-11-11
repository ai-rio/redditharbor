#!/usr/bin/env python3
"""
Fast Subreddit Monetization Scanner
Optimized version for quick analysis of multiple subreddits
"""

import re
import sys
import time
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit

from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT


class FastMonetizationScanner:
    """Fast scanner for subreddit monetization potential"""

    # Compact signal sets
    PAYMENT_SIGNALS = ["pay", "paid", "price", "cost", "buy", "subscription", "premium", "money", "spend", "expensive", "cheap"]
    GAP_SIGNALS = ["no solution", "wish there", "looking for", "need app", "doesn't exist", "frustrated", "manual", "problem"]
    COMMERCE_SIGNALS = ["business", "company", "professional", "client", "revenue", "b2b", "b2c"]
    PRICE_REGEX = [r"\$\d+", r"\d+\s*dollar", r"\d+\s*/\s*month"]

    def __init__(self, reddit_client):
        self.reddit = reddit_client

    def count_signals(self, text: str) -> dict[str, int]:
        """Count monetization signals in text"""
        text_lower = text.lower()

        payment = sum(1 for s in self.PAYMENT_SIGNALS if s in text_lower)
        gap = sum(1 for s in self.GAP_SIGNALS if s in text_lower)
        commerce = sum(1 for s in self.COMMERCE_SIGNALS if s in text_lower)
        price = sum(1 for pattern in self.PRICE_REGEX if re.search(pattern, text_lower))

        return {"payment": payment, "gap": gap, "commerce": commerce, "price": price}

    def scan_subreddit_fast(self, subreddit_name: str, limit: int = 30) -> dict[str, Any]:
        """Fast scan of a subreddit"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            # Collect all text first (more efficient)
            all_texts = []
            post_count = 0

            for submission in subreddit.hot(limit=limit):
                try:
                    # Combine title and text
                    post_text = f"{submission.title} {submission.selftext or ''}"
                    all_texts.append(post_text)

                    # Get top 3 comments
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments[:3]:
                        if hasattr(comment, 'body') and comment.body:
                            all_texts.append(comment.body)

                    post_count += 1

                except Exception:
                    continue

            # Analyze all text at once
            total_signals = {"payment": 0, "gap": 0, "commerce": 0, "price": 0}
            posts_with_signals = 0

            for text in all_texts:
                signals = self.count_signals(text)
                for key in total_signals:
                    total_signals[key] += signals[key]

                if sum(signals.values()) > 0:
                    posts_with_signals += 1

            # Calculate score
            total = sum(total_signals.values())
            if post_count > 0:
                density = total / post_count
                # Weighted score
                score = (
                    (total_signals["payment"] / max(total, 1)) * 35 +
                    (total_signals["gap"] / max(total, 1)) * 30 +
                    (total_signals["commerce"] / max(total, 1)) * 20 +
                    (total_signals["price"] / max(total, 1)) * 15
                )
            else:
                density = 0
                score = 0

            return {
                "subreddit": subreddit_name,
                "posts_analyzed": post_count,
                "total_signals": total,
                "density": round(density, 2),
                "score": round(score, 1),
                "signals": total_signals,
                "success": True
            }

        except Exception as e:
            return {
                "subreddit": subreddit_name,
                "error": str(e),
                "success": False
            }

    def scan_batch(self, subreddits: list[str]) -> list[dict[str, Any]]:
        """Scan multiple subreddits quickly"""
        print("=" * 70)
        print("FAST SUBREDDITE MONETIZATION SCANNER")
        print("=" * 70)
        print(f"\nScanning {len(subreddits)} subreddits...")
        print()

        results = []
        start_time = time.time()

        for i, sub in enumerate(subreddits, 1):
            print(f"[{i}/{len(subreddits)}] Scanning r/{sub}...", end=" ")
            result = self.scan_subreddit_fast(sub, limit=30)

            if result["success"]:
                score = result["score"]
                density = result["density"]
                print(f"✅ Score: {score:.1f}/100, Density: {density:.2f}")
            else:
                print(f"❌ {result.get('error', 'Unknown error')}")

            results.append(result)

        elapsed = time.time() - start_time
        print(f"\n⏱️  Completed in {elapsed:.1f} seconds")

        # Sort by score
        successful = [r for r in results if r.get("success", False)]
        successful.sort(key=lambda x: x["score"], reverse=True)

        return successful


def main():
    """Main execution"""

    # Initialize Reddit
    print("Initializing Reddit client...")
    reddit_client = reddit(
        public_key=REDDIT_PUBLIC,
        secret_key=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    print("✅ Connected!\n")

    # Initialize scanner
    scanner = FastMonetizationScanner(reddit_client)

    # Candidate subreddits (curated list)
    CANDIDATE_SUBREDDITS = [
        "entrepreneur", "startups", "smallbusiness", "business",
        "indiehackers", "marketing", "SaaS", "nocode",
        "personalfinance", "investing", "fire", "sidehustle",
        "programming", "webdev", "MachineLearning", "artificial",
        "productivity", "getmotivated", "LifeProTips",
        "freelance", "jobs", "careerguidance", "resumes",
        "ecommerce", "AmazonSeller", "digitalnomad",
        "fitness", "nutrition", "mentalhealth", "loseit"
    ]

    # Scan all
    results = scanner.scan_batch(CANDIDATE_SUBREDDITS)

    # Display top results
    print("\n" + "=" * 70)
    print("TOP 15 MONETIZABLE SUBREDDITS")
    print("=" * 70)

    for i, result in enumerate(results[:15], 1):
        signals = result["signals"]
        print(f"\n{i:2}. r/{result['subreddit']:25} Score: {result['score']:5.1f}/100")
        print(f"    💰 Payment: {signals['payment']:3}  🔍 Gaps: {signals['gap']:3}  💼 Business: {signals['commerce']:3}  💵 Price: {signals['price']:3}")

    # Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)

    top_5 = [r["subreddit"] for r in results[:5]]
    top_10 = [r["subreddit"] for r in results[:10]]

    print("\n🥇 TOP 5 FOR COLLECTION:")
    print(f"   {', '.join(top_5)}")

    print("\n🎯 TOP 10 FOR COLLECTION:")
    print(f"   {', '.join(top_10)}")

    # Save results
    import json
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filepath = f"/home/carlos/projects/redditharbor/scan_results_{timestamp}.json"
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Full results saved to: {filepath}")
    print("\n✅ Scan complete!\n")


if __name__ == "__main__":
    main()
