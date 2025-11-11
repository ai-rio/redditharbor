#!/usr/bin/env python3
"""
Manual Quick Test - Check specific high-value subreddits
"""

import sys
from pathlib import Path

# Add project root
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

# Test subreddits
SUBREDDITS = {
    "entrepreneur": "Business and startup discussions",
    "startups": "Startup pain points and solutions",
    "smallbusiness": "Small business problems",
    "SaaS": "Software-as-a-Service discussions",
    "indiehackers": "Independent developers",
    "sidehustle": "Making money online",
    "marketing": "Marketing tools and pain points",
    "fitness": "Personal health stories (baseline)",
}

# Monetization signals
PAYMENT = ["pay", "paid", "price", "cost", "buy", "subscription", "premium", "money", "expensive", "cheap"]
GAP = ["wish there", "looking for", "need app", "no solution", "doesn't exist", "frustrated", "problem"]
BUSINESS = ["business", "company", "professional", "client", "revenue", "b2b", "commercial"]

print("Testing subreddits for monetization signals...\n")
print("=" * 70)

results = []

for sub_name, description in SUBREDDITS.items():
    print(f"\n🔍 r/{sub_name} - {description}")

    try:
        subreddit = reddit_client.subreddit(sub_name)

        # Get 5 posts
        posts = list(subreddit.hot(limit=5))

        # Analyze
        total_payment = 0
        total_gap = 0
        total_business = 0
        posts_with_signals = 0

        for post in posts:
            # Post text
            post_text = f"{post.title} {post.selftext or ''}".lower()

            # Count signals
            payment_count = sum(1 for s in PAYMENT if s in post_text)
            gap_count = sum(1 for s in GAP if s in post_text)
            business_count = sum(1 for s in BUSINESS if s in post_text)

            # Comments (top 2 only)
            post.comments.replace_more(limit=0)
            comment_text = ""
            for comment in post.comments[:2]:
                if hasattr(comment, 'body') and comment.body:
                    comment_text += " " + comment.body.lower()

            payment_count += sum(1 for s in PAYMENT if s in comment_text)
            gap_count += sum(1 for s in GAP if s in comment_text)
            business_count += sum(1 for s in BUSINESS if s in comment_text)

            total_payment += payment_count
            total_gap += gap_count
            total_business += business_count

            if payment_count + gap_count + business_count > 0:
                posts_with_signals += 1

        # Calculate score
        total_signals = total_payment + total_gap + total_business
        signal_density = total_signals / len(posts) if posts else 0

        result = {
            "subreddit": sub_name,
            "description": description,
            "payment": total_payment,
            "gap": total_gap,
            "business": total_business,
            "total": total_signals,
            "density": round(signal_density, 2),
            "posts_with_signals": posts_with_signals,
            "score": round(signal_density * 20, 1)  # Simple scoring
        }

        results.append(result)

        print(f"   💰 Payment: {total_payment:2}  💼 Business: {total_business:2}  🔍 Gaps: {total_gap:2}")
        print(f"   📊 Total: {total_signals:2}  Density: {signal_density:.2f}  Score: {result['score']}/100")

    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
        results.append({
            "subreddit": sub_name,
            "error": str(e),
            "score": 0
        })

print("\n" + "=" * 70)
print("RANKED RESULTS")
print("=" * 70)

# Sort by score (excluding errors)
valid_results = [r for r in results if "error" not in r]
valid_results.sort(key=lambda x: x["score"], reverse=True)

for i, result in enumerate(valid_results, 1):
    print(f"\n{i}. r/{result['subreddit']:20} Score: {result['score']:5.1f}/100")
    print(f"   💰: {result['payment']:2}  💼: {result['business']:2}  🔍: {result['gap']:2}  Density: {result['density']:.2f}")

# Top 5 recommendations
print("\n" + "=" * 70)
print("TOP 5 FOR COLLECTION:")
print("=" * 70)

top_5 = valid_results[:5]
for i, r in enumerate(top_5, 1):
    print(f"{i}. r/{r['subreddit']} (Score: {r['score']}/100)")

print("\n✅ Test complete!\n")
