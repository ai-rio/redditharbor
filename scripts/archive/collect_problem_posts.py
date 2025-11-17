#!/usr/bin/env python3
"""
Problem-First Data Collection
Collects only Reddit posts that describe real user problems using keyword filtering
"""
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sys

sys.path.append(str(project_root))
import argparse

from core.setup import setup_redditharbor
from core.templates import problem_first_opportunity_research

# Problem keywords - posts MUST contain at least one
PROBLEM_KEYWORDS = [
    # Direct problem statements
    "struggle", "struggling", "struggled",
    "problem", "problems",
    "frustrated", "frustrating",
    "annoying", "annoyed",
    "difficult", "hard", "hARD",
    "complicated", "confusing",
    "waste", "wasting",
    "manual process", "tedious",
    "tired of", "sick of",

    # "I wish" statements
    "i wish", "wish there was", "if only",
    "i need", "looking for",
    "any tool", "any app", "any solution",

    # Pain indicators
    "pain point", "pain", "hate",
    "irksome", "aggravating", "irks",
    "can't figure out", "can't find",
    "unable to", "impossible",
    "time consuming", "slow",

    # Workarounds (indicate problems)
    "workaround", "I use", "I do",
    "manual", "DIY", "I created",
    "I built", "I made"
]

# Avoid collecting these (not problem posts)
FILTER_OUT = [
    "guide", "tutorial", "how to",
    "success", "success story",
    "I did it", "I achieved",
    "tips", "advice", "lessons learned",
    "my experience", "story time"
]


def collect_problem_posts(subreddits, limit_per_subreddit=500):
    """
    Collect posts containing problem keywords from specified subreddits
    """
    # Setup pipeline
    pipeline = setup_redditharbor()
    if not pipeline:
        print("❌ Failed to setup RedditHarbor")
        return False

    print("=" * 80)
    print("PROBLEM-FIRST DATA COLLECTION")
    print("=" * 80)
    print(f"\nTarget Subreddits: {', '.join(subreddits)}")
    print(f"Limit per subreddit: {limit_per_subreddit}")
    print(f"Problem keywords: {len(PROBLEM_KEYWORDS)}")
    print("\nCollecting posts that contain problem indicators...")

    # Use the problem-first template
    problem_first_opportunity_research(pipeline, subreddits)

    print("\n" + "=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Check Supabase Studio (http://127.0.0.1:54323)")
    print("2. Run AI analysis: python scripts/generate_opportunity_insights_openrouter.py")
    print("3. Review generated app opportunities")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Collect Reddit posts describing real user problems"
    )
    parser.add_argument(
        "--subreddits",
        nargs="+",
        default=["opensource", "SideProject", "productivity", "freelance", "personalfinance"],
        help="Subreddits to collect from (default: opensource SideProject productivity freelance personalfinance)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Number of posts per subreddit to collect"
    )

    args = parser.parse_args()

    success = collect_problem_posts(args.subreddits, args.limit)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
