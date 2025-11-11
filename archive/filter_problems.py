#!/usr/bin/env python3
"""
Problem Filter for Existing Data
Analyzes existing submissions and flags posts that describe real user problems
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from supabase import create_client

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env.local')

# Problem keywords from collection.py
PROBLEM_KEYWORDS = [
    "pain", "problem", "frustrated", "wish", "if only", "hate", "annoying", "difficult",
    "struggle", "confusing", "complicated", "time consuming", "manual", "tedious",
    "cumbersome", "inefficient", "slow", "expensive", "costly", "broken", "doesn't work",
    "fails", "error", "bug", "issue", "limitation", "lacks", "missing", "no way to",
    "hard to", "impossible", "can't", "unable to", "annoying", "irksome", "aggravating"
]


def extract_problem_keywords(text: str):
    """Extract problem keywords from text"""
    if not text:
        return []

    text_lower = text.lower()
    found_keywords = []

    for keyword in PROBLEM_KEYWORDS:
        if keyword in text_lower:
            count = text_lower.count(keyword)
            found_keywords.extend([keyword] * count)

    return list(set(found_keywords))


def is_problem_post(title: str, text: str, min_keywords=2):
    """
    Determine if a post describes a real problem
    Returns (is_problem, keywords_found, confidence_score)
    """
    combined_text = f"{title} {text}".lower()

    # Count problem keywords
    found_keywords = extract_problem_keywords(combined_text)
    keyword_count = len(found_keywords)

    # Filter out non-problem posts
    filter_out_terms = [
        "guide", "tutorial", "how to", "success", "success story",
        "I did it", "I achieved", "tips", "advice", "lessons learned",
        "my experience", "story time", "I learned", "I found that"
    ]

    if any(term in combined_text for term in filter_out_terms):
        return False, found_keywords, 0.0

    # Calculate confidence score
    # Higher score = more likely to be a real problem
    confidence = min(keyword_count / min_keywords, 1.0) * 100

    is_problem = keyword_count >= min_keywords and confidence >= 50

    return is_problem, found_keywords, confidence


def filter_existing_problems():
    """Analyze existing submissions and flag problem posts"""
    # Connect to Supabase
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

    print("=" * 80)
    print("PROBLEM FILTER - ANALYZING EXISTING DATA")
    print("=" * 80)

    # Get all submissions
    print("\nFetching submissions...")
    result = supabase.table("submissions").select("id, title, text, subreddit").execute()

    if not result.data:
        print("❌ No submissions found")
        return

    submissions = result.data
    print(f"Total submissions: {len(submissions)}")

    # Analyze each submission
    print("\nAnalyzing for problem indicators...")
    problem_posts = []
    non_problem_posts = []

    for submission in submissions:
        title = submission.get('title', '')
        text = submission.get('text', '')
        subreddit = submission.get('subreddit', '')

        is_prob, keywords, conf = is_problem_post(title, text)

        if is_prob:
            problem_posts.append({
                'id': submission['id'],
                'title': title,
                'subreddit': subreddit,
                'confidence': conf,
                'keywords': keywords
            })
        else:
            non_problem_posts.append({
                'id': submission['id'],
                'title': title,
                'subreddit': subreddit
            })

    # Sort problem posts by confidence
    problem_posts.sort(key=lambda x: x['confidence'], reverse=True)

    # Display results
    print(f"\n{'='*80}")
    print(f"RESULTS: {len(problem_posts)} PROBLEM POSTS FOUND")
    print(f"{'='*80}\n")

    print("TOP PROBLEM POSTS (sorted by confidence):\n")

    for i, post in enumerate(problem_posts[:20], 1):
        print(f"{i}. r/{post['subreddit']} (Confidence: {post['confidence']:.0f}%)")
        print(f"   {post['title'][:80]}...")
        print(f"   Keywords: {', '.join(post['keywords'][:5])}")
        print()

    # Save detailed results
    output_file = project_root / "problem_posts_analysis.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_submissions': len(submissions),
                'problem_posts': len(problem_posts),
                'non_problem_posts': len(non_problem_posts),
                'problem_percentage': (len(problem_posts) / len(submissions)) * 100
            },
            'problem_posts': problem_posts[:50],  # Top 50
            'non_problem_count_by_subreddit': {}
        }, f, indent=2)

    print(f"Detailed results saved to: {output_file}")
    print(f"\n{len(problem_posts)} problem posts identified out of {len(submissions)} total")
    print(f"That's {(len(problem_posts) / len(submissions)) * 100:.1f}% problem posts!")

    if len(problem_posts) > 0:
        print("\n✅ RECOMMENDATION:")
        print(f"   Run AI analysis on these {len(problem_posts)} posts:")
        print(f"   python scripts/generate_opportunity_insights_openrouter.py --mode database --limit {min(10, len(problem_posts))}")


if __name__ == "__main__":
    filter_existing_problems()
