#!/usr/bin/env python3
"""
Test version - scan just 1 subreddit to verify logic
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit

from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT

# Initialize Reddit
print("Connecting to Reddit...")
reddit_client = reddit(
    public_key=REDDIT_PUBLIC,
    secret_key=REDDIT_SECRET,
    user_agent=REDDIT_USER_AGENT
)
print("✅ Connected!\n")

# Test with r/entrepreneur
print("Testing with r/entrepreneur...")
subreddit = reddit_client.subreddit("entrepreneur")

print("Fetching 10 posts...")
posts = list(subreddit.hot(limit=10))

print(f"\nAnalyzing {len(posts)} posts...\n")

# Simple monetization check
payment_signals = ["pay", "subscription", "premium", "buy", "price", "cost", "money"]
count = 0

for post in posts:
    text = f"{post.title} {post.selftext or ''}".lower()
    signals_found = [s for s in payment_signals if s in text]

    if signals_found:
        count += 1
        print(f"Post: {post.title[:50]}...")
        print(f"  Signals: {signals_found}")
        print()

print(f"\nFound {count}/{len(posts)} posts with payment signals ({count/len(posts)*100:.1f}%)")

# Test comments on first post
print("\n" + "="*60)
print("Testing comment analysis on first post...")
print("="*60)

first_post = posts[0]
print(f"\nPost: {first_post.title[:80]}")

# Get top 3 comments
first_post.comments.replace_more(limit=0)
comments = first_post.comments[:3]

print(f"\nAnalyzing {len(comments)} top comments...")

for i, comment in enumerate(comments, 1):
    if hasattr(comment, 'body'):
        text = comment.body.lower()
        signals_found = [s for s in payment_signals if s in text]
        if signals_found:
            print(f"\nComment {i}: {comment.body[:100]}...")
            print(f"  Signals: {signals_found}")

print("\n✅ Test complete!")
