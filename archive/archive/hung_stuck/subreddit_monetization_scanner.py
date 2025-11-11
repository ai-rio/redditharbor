#!/usr/bin/env python3
"""
Subreddit Monetization Scanner
Discovers subreddits with the highest monetization potential using data-driven analysis.

This script:
- Scans candidate subreddits using Reddit API
- Analyzes posts & comments for monetization signals
- Ranks subreddits by monetization density score
- Recommends top subreddits for data collection
"""

import re
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


class SubredditMonetizationScanner:
    """Scanner for analyzing subreddit monetization potential"""

    # Monetization signals (same as OpportunityAnalyzerAgent)
    PAYMENT_SIGNALS = [
        "willing to pay", "would pay", "happy to pay", "worth the cost",
        "investment", "premium", "pro version", "subscription", "paid",
        "buying", "purchase", "expensive", "cheap", "price", "cost",
        "free trial", "freemium", "monthly fee", "yearly", "one-time",
        "commission", "marketplace", "money", "spend", "spending"
    ]

    GAP_SIGNALS = [
        "no good solution", "nothing available", "wish there was",
        "someone should build", "market gap", "looking for", "need an app",
        "doesn't exist", "no such thing", "can't find", "frustrated with",
        "annoying", "tedious", "manual process", "too complicated",
        "missing feature", "limitations", "pain point", "problem"
    ]

    COMMERCE_SIGNALS = [
        "business", "company", "team", "enterprise", "workplace",
        "professional", "industry", "commercial", "client", "customer",
        "revenue", "profit", "sales", "b2b", "b2c", "roi", "earnings"
    ]

    PRICE_SIGNALS = [
        r"\$\d+", r"\d+\s*dollar", r"\d+\s*usd", r"\d+\s*per month",
        r"\d+\s*/\s*month", r"\d+\s*price", r"costs?", r"charged?",
        r"billing", r"invoice", r"subscription", r"plan", r"tier"
    ]

    def __init__(self, reddit_client):
        """Initialize scanner with Reddit client"""
        self.reddit = reddit_client
        self.results = {}

    def analyze_text_for_signals(self, text: str) -> dict[str, int]:
        """
        Analyze text for monetization signals.

        Args:
            text: Text to analyze

        Returns:
            Dict with signal counts
        """
        text_lower = text.lower()

        # Count payment signals
        payment_count = sum(1 for signal in self.PAYMENT_SIGNALS if signal in text_lower)

        # Count gap signals
        gap_count = sum(1 for signal in self.GAP_SIGNALS if signal in text_lower)

        # Count commerce signals
        commerce_count = sum(1 for signal in self.COMMERCE_SIGNALS if signal in text_lower)

        # Count price mentions
        price_count = sum(1 for pattern in self.PRICE_SIGNALS if re.search(pattern, text_lower))

        return {
            "payment": payment_count,
            "gap": gap_count,
            "commerce": commerce_count,
            "price": price_count
        }

    def scan_subreddit(self, subreddit_name: str, limit: int = 50) -> dict[str, Any]:
        """
        Scan a single subreddit for monetization signals.

        Args:
            subreddit_name: Name of subreddit to scan
            limit: Number of posts to analyze

        Returns:
            Dict with scan results
        """
        print(f"\n  🔍 Scanning r/{subreddit_name}...")

        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            # Collect signals
            all_signals = defaultdict(int)
            posts_analyzed = 0
            posts_with_signals = 0

            # Fetch recent posts
            posts_to_analyze = list(subreddit.hot(limit=limit))

            for submission in posts_to_analyze:
                try:
                    # Combine title and text
                    post_text = f"{submission.title} {submission.selftext or ''}"

                    # Analyze post
                    post_signals = self.analyze_text_for_signals(post_text)

                    # Get top comments (limit to 5 for speed)
                    top_comments = []
                    submission.comments.replace_more(limit=0)  # Get top-level only
                    for comment in submission.comments[:5]:
                        if hasattr(comment, 'body'):
                            top_comments.append(comment.body)

                    # Combine comments
                    comments_text = " ".join(top_comments)

                    # Analyze comments
                    comment_signals = self.analyze_text_for_signals(comments_text)

                    # Combine signals
                    for key in post_signals:
                        all_signals[key] += post_signals[key] + comment_signals[key]

                    # Count posts with signals
                    total_signals = sum(post_signals.values()) + sum(comment_signals.values())
                    if total_signals > 0:
                        posts_with_signals += 1

                    posts_analyzed += 1

                except Exception:
                    # Skip problematic posts
                    continue

            # Calculate monetization density
            total_signals = sum(all_signals.values())
            monetization_density = (total_signals / posts_analyzed) if posts_analyzed > 0 else 0

            # Calculate signal ratios
            signal_ratios = {
                "payment_ratio": (all_signals["payment"] / total_signals) if total_signals > 0 else 0,
                "gap_ratio": (all_signals["gap"] / total_signals) if total_signals > 0 else 0,
                "commerce_ratio": (all_signals["commerce"] / total_signals) if total_signals > 0 else 0,
                "price_ratio": (all_signals["price"] / total_signals) if total_signals > 0 else 0,
            }

            # Calculate overall score (weighted)
            overall_score = (
                signal_ratios["payment_ratio"] * 35 +  # 35% - Willingness to pay
                signal_ratios["gap_ratio"] * 30 +      # 30% - Market gaps
                signal_ratios["commerce_ratio"] * 20 +  # 20% - Business context
                signal_ratios["price_ratio"] * 15       # 15% - Price mentions
            )

            result = {
                "subreddit": subreddit_name,
                "posts_analyzed": posts_analyzed,
                "posts_with_signals": posts_with_signals,
                "signal_density": monetization_density,
                "total_signals": total_signals,
                "signals": dict(all_signals),
                "signal_ratios": signal_ratios,
                "overall_score": round(overall_score, 2),
                "success": True
            }

            print(f"    ✅ Analyzed {posts_analyzed} posts")
            print(f"    📊 Total signals: {total_signals}")
            print(f"    🎯 Overall score: {overall_score:.1f}/100")

            return result

        except Exception as e:
            print(f"    ❌ Error: {e!s}")
            return {
                "subreddit": subreddit_name,
                "error": str(e),
                "success": False
            }

    def scan_multiple_subreddits(self, subreddits: list[str], posts_per_subreddit: int = 50) -> list[dict[str, Any]]:
        """
        Scan multiple subreddits and rank by monetization potential.

        Args:
            subreddits: List of subreddit names to scan
            posts_per_subreddit: Number of posts to analyze per subreddit

        Returns:
            List of ranked results
        """
        print("=" * 80)
        print("SUBREDDIT MONETIZATION SCANNER")
        print("=" * 80)
        print(f"\nScanning {len(subreddits)} subreddits...")
        print(f"Analyzing {posts_per_subreddit} posts per subreddit")
        print()

        results = []

        for subreddit in subreddits:
            result = self.scan_subreddit(subreddit, limit=posts_per_subreddit)
            results.append(result)
            time.sleep(0.5)  # Rate limiting

        # Filter successful results
        successful_results = [r for r in results if r.get("success", False)]

        if not successful_results:
            print("\n⚠️  No successful scans!")
            return []

        # Sort by overall score (descending)
        ranked_results = sorted(successful_results, key=lambda x: x["overall_score"], reverse=True)

        # Store results
        self.results = ranked_results

        return ranked_results

    def print_rankings(self, top_n: int = 10) -> None:
        """
        Print ranked subreddit results.

        Args:
            top_n: Number of top subreddits to display
        """
        if not self.results:
            print("No results to display. Run scan_multiple_subreddits() first.")
            return

        print("\n" + "=" * 80)
        print(f"TOP {min(top_n, len(self.results))} MONETIZABLE SUBREDDITS")
        print("=" * 80)

        for i, result in enumerate(self.results[:top_n], 1):
            signals = result["signals"]
            print(f"\n{i}. r/{result['subreddit']} - Score: {result['overall_score']:.1f}/100")
            print(f"   Posts analyzed: {result['posts_analyzed']}")
            print(f"   Posts with signals: {result['posts_with_signals']} ({result['posts_with_signals']/result['posts_analyzed']*100:.1f}%)")
            print("   Signal breakdown:")
            print(f"     💰 Payment signals: {signals.get('payment', 0)}")
            print(f"     🔍 Gap signals: {signals.get('gap', 0)}")
            print(f"     💼 Commerce signals: {signals.get('commerce', 0)}")
            print(f"     💵 Price mentions: {signals.get('price', 0)}")
            print(f"     📊 Signal density: {result['signal_density']:.2f} per post")

    def save_results(self, filepath: str = None) -> None:
        """
        Save results to JSON file.

        Args:
            filepath: Path to save file (optional)
        """
        if not self.results:
            print("No results to save.")
            return

        if filepath is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"/home/carlos/projects/redditharbor/subreddit_scan_results_{timestamp}.json"

        import json
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Results saved to: {filepath}")

    def get_top_subreddits(self, count: int = 10) -> list[str]:
        """
        Get list of top-scoring subreddits.

        Args:
            count: Number of top subreddits to return

        Returns:
            List of subreddit names
        """
        if not self.results:
            return []

        return [r["subreddit"] for r in self.results[:count]]


def main():
    """Main execution function"""

    # Initialize Reddit client
    print("Initializing Reddit client...")
    try:
        reddit_client = reddit(
            public_key=REDDIT_PUBLIC,
            secret_key=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        print("✅ Reddit client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Reddit client: {e}")
        return

    # Initialize scanner
    scanner = SubredditMonetizationScanner(reddit_client)

    # Define candidate subreddits (grouped by category)
    CANDIDATE_SUBREDDITS = {
        "Business & Startups": [
            "entrepreneur", "startups", "smallbusiness", "business",
            "indiehackers", "solopreneurs", "businessowners", "marketing"
        ],
        "Finance & Money": [
            "personalfinance", "investing", "financialindependence",
            "fire", "povertyfinance", "frugal", "sidehustle"
        ],
        "Technology & Development": [
            "programming", "webdev", "MachineLearning", "artificial",
            "SaaS", "nocode", "buildinpublic", "roastmystartup"
        ],
        "Productivity & Tools": [
            "productivity", "getmotivated", "LifeProTips", "decidingtobebetter"
        ],
        "Professional Services": [
            "freelance", "jobs", "careerguidance", "cscareerquestions",
            "resumes", "teaching", "consulting"
        ],
        "E-commerce & Sales": [
            "ecommerce", "AmazonSeller", "digitalnomad", "dropshipping"
        ],
        "Health & Wellness": [
            "fitness", "nutrition", "mentalhealth", "loseit"
        ]
    }

    # Flatten list
    all_subreddits = []
    for category, subs in CANDIDATE_SUBREDDITS.items():
        all_subreddits.extend(subs)

    print(f"\nCandidate subreddits: {len(all_subreddits)}")
    print("\nCategories:")
    for category, subs in CANDIDATE_SUBREDDITS.items():
        print(f"  {category}: {', '.join(subs)}")

    # Scan all subreddits
    print("\n" + "=" * 80)
    print("STARTING SCAN...")
    print("=" * 80)

    results = scanner.scan_multiple_subreddits(all_subreddits, posts_per_subreddit=50)

    # Print rankings
    scanner.print_rankings(top_n=15)

    # Save results
    scanner.save_results()

    # Display top recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS FOR COLLECTION")
    print("=" * 80)

    top_5 = scanner.get_top_subreddits(count=5)
    top_10 = scanner.get_top_subreddits(count=10)

    print("\n🥇 TOP 5 RECOMMENDED SUBREDDITS:")
    for i, sub in enumerate(top_5, 1):
        score = next(r["overall_score"] for r in results if r["subreddit"] == sub)
        print(f"  {i}. r/{sub} (Score: {score:.1f}/100)")

    print("\n🎯 TOP 10 SUBREDDITS FOR COLLECTION:")
    print("   Use these in your collection scripts:")
    print(f"   {top_10}")

    print("\n" + "=" * 80)
    print("SCAN COMPLETE!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
