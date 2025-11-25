#!/usr/bin/env python3
"""
Direct Supabase Reddit Data Collection (DLT Replacement)

This module replaces DLT with direct Supabase client for Reddit data collection.
No more schema mismatches, no more UUID normalization issues.

Features:
- Direct Supabase upsert with proper UUID handling
- Problem keyword filtering (PROBLEM_KEYWORDS)
- Batch processing with proper error handling
- Native PostgreSQL UUID support
- Idempotent upserts using reddit_id as conflict key

Main Functions:
- collect_and_store_submissions(): Collect Reddit posts and store directly
- store_submissions(): Batch upsert submissions to Supabase
"""

import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / '.env.local')

# Import Reddit client
import praw

# Import problem keywords
from core.fetchers.collection import PROBLEM_KEYWORDS

# Import ID resolver for canonical UUID generation
from core.utils.id_resolver import resolve_submission_id

# Import Supabase client
from supabase import create_client, Client

# Configure logging
logger = logging.getLogger(__name__)

# Problem-first filtering: minimum keywords required
MIN_PROBLEM_KEYWORDS = 1

# Pre-AI quality filtering thresholds
MIN_ENGAGEMENT_SCORE = 5   # Minimum upvotes
MIN_COMMENT_COUNT = 1      # Minimum comments
MIN_QUALITY_SCORE = 15.0   # Minimum quality score before storage

# Subreddits for collection
TARGET_SUBREDDITS = [
    "opensource", "SideProject", "productivity", "freelance", "personalfinance"
]

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54330')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Business logic filtering: Monetization signals
MONETIZATION_SIGNALS = [
    # Willingness to pay phrases
    "would pay", "willing to pay", "happy to pay", "i'd pay", "i'll pay",
    "subscription", "worth $", "worth paying", "premium", "paid version",
    # Commercial gap mentions
    "nothing good exists", "existing solutions suck", "can't find anything",
    "no good options", "everything is bad", "all options are terrible",
    "existing tools don't work", "current solutions are expensive",
    # Revenue model discussions
    "freemium", "saas", "pricing", "business model", "pay monthly",
    "pay yearly", "one-time payment", "affordable price", "free trial",
    "upgrade to pro", "premium features"
]

# Business logic filtering: Feature/function indicators
FEATURE_INDICATORS = [
    "feature", "function", "functionality", "capability", "can do",
    "does", "ability to", "allows", "enables", "supports"
]

# Business logic filtering: Simple list patterns
LIST_PATTERNS = [
    r'\d+\.',  # Numbered lists: 1. 2. 3.
    r'[-•*]',  # Bullet points: - • *
    r'\n\s*\d+\)',  # Parenthetical numbers: 1) 2) 3)
]


def get_supabase_client() -> Client:
    """Get configured Supabase client."""
    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_KEY environment variable not set")

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_reddit_client() -> praw.Reddit:
    """Initialize and return Reddit client."""
    reddit_public = os.getenv("REDDIT_PUBLIC")
    reddit_secret = os.getenv("REDDIT_SECRET")
    reddit_user_agent = os.getenv("REDDIT_USER_AGENT")

    return praw.Reddit(
        client_id=reddit_public,
        client_secret=reddit_secret,
        user_agent=reddit_user_agent
    )


def contains_problem_keywords(text: str, min_keywords: int = MIN_PROBLEM_KEYWORDS) -> bool:
    """
    Check if text contains problem keywords.

    Args:
        text: Text to check
        min_keywords: Minimum number of problem keywords required

    Returns:
        True if text contains at least min_keywords problem keywords
    """
    if not text:
        return False

    text_lower = text.lower()
    keyword_count = sum(1 for keyword in PROBLEM_KEYWORDS if keyword.lower() in text_lower)
    return keyword_count >= min_keywords


def has_monetization_signals(text: str) -> bool:
    """
    Check if text contains signals of willingness to pay or commercial viability.

    Based on monetizable app research methodology, this function identifies:
    - Willingness-to-pay phrases: "would pay", "willing to pay", "subscription"
    - Commercial gap mentions: "nothing good exists", "existing solutions suck"
    - Revenue model discussions: "freemium", "saas", "pricing", "business model"

    Args:
        text: Text to analyze for monetization signals

    Returns:
        True if at least one monetization signal found, False otherwise

    Examples:
        >>> has_monetization_signals("I would pay $10/month for this")
        True
        >>> has_monetization_signals("Nothing good exists for this problem")
        True
        >>> has_monetization_signals("This is just a random post")
        False
    """
    if not text:
        return False

    text_lower = text.lower()

    # Check if any monetization signal is present
    has_signal = any(signal in text_lower for signal in MONETIZATION_SIGNALS)

    return has_signal


def meets_simplicity_constraint(text: str) -> bool:
    """
    Check if described solution is simple (1-3 core functions only).

    Based on monetizable app research methodology, apps with 4+ core functions
    are automatically disqualified. This function analyzes text to count
    distinct functions described.

    Function identification approach:
    - Look for explicit feature/function mentions with indicators
    - Parse lists of features (bullet points, numbered lists)
    - Count distinct function descriptions
    - Return True if 1-3 functions, False if 4+ functions
    - Return True by default if can't determine (benefit of doubt)

    Args:
        text: Text to analyze for function/feature count

    Returns:
        True if 1-3 functions or indeterminate, False if 4+ functions

    Examples:
        >>> meets_simplicity_constraint("A timer and break reminder")
        True
        >>> meets_simplicity_constraint("Track habits, set goals, view stats, share progress, compete")
        False
        >>> meets_simplicity_constraint("Just a simple todo list")
        True
    """
    if not text:
        return True  # Benefit of doubt

    text_lower = text.lower()

    # Strategy 1: Count explicit feature/function mentions
    feature_count = 0
    for indicator in FEATURE_INDICATORS:
        if indicator in text_lower:
            # Count occurrences (rough heuristic)
            feature_count += text_lower.count(indicator)

    # If many explicit feature mentions (4+), likely complex
    if feature_count >= 4:
        return False

    # Strategy 2: Detect lists and count items
    list_items = []
    for pattern in LIST_PATTERNS:
        matches = re.findall(pattern, text)
        list_items.extend(matches)

    # If list has 4+ items, likely describing multiple functions
    if len(list_items) >= 4:
        return False

    # Strategy 3: Count comma-separated items in feature descriptions
    # Look for patterns like "track X, set Y, view Z, share W"
    # This catches lists without explicit numbering
    for sentence in text.split('.'):
        sentence_lower = sentence.lower()

        # Count commas in sentences that describe capabilities
        if any(word in sentence_lower for word in ["track", "manage", "monitor", "create", "generate", "send", "receive"]):
            # Count distinct actions separated by commas
            comma_count = sentence_lower.count(",")

            # If 3+ commas in an action sentence, likely 4+ functions
            if comma_count >= 3:
                return False

    # Strategy 4: Count "and" conjunctions in function descriptions
    # Look for patterns like "does X and Y and Z and W"
    if any(keyword in text_lower for keyword in ["can", "does", "allows", "enables"]):
        # Extract sentences with these keywords
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in ["can", "does", "allows", "enables"]):
                # Count "and" occurrences as function separators
                and_count = sentence_lower.count(" and ")
                comma_count = sentence_lower.count(",")
                # If many conjunctions, likely listing multiple functions
                if and_count + comma_count >= 3:
                    return False

    # Default: benefit of doubt (assume simple unless proven complex)
    return True


def calculate_quality_score(submission: Any) -> float:
    """
    Calculate quality score BEFORE storage to filter low-quality posts.

    Quality factors:
    - Engagement (upvotes + comments)
    - Problem keyword density
    - Recency (newer = better)

    Returns:
        Float quality score (0-100)
    """
    # Engagement score (0-40 points)
    score = submission.score
    num_comments = submission.num_comments
    engagement = min(40, (score + num_comments * 2) / 2)

    # Problem keyword density (0-30 points)
    full_text = f"{submission.title} {submission.selftext}"
    problem_kw_count = len([kw for kw in PROBLEM_KEYWORDS if kw.lower() in full_text.lower()])
    keyword_score = min(30, problem_kw_count * 10)

    # Recency score (0-30 points)
    age_hours = (time.time() - submission.created_utc) / 3600
    recency_score = max(0, 30 - (age_hours / 24))  # Decay over 24 hours

    total = engagement + keyword_score + recency_score
    return round(total, 2)


def should_store_submission(submission: Any) -> tuple[bool, float]:
    """
    Pre-filter submissions with business logic based on monetizable app research methodology.

    This function filters submissions through multiple quality gates:
    1. Basic engagement checks (minimum score and comments)
    2. Problem keyword presence (pain points, frustrations)
    3. Monetization signals (willingness to pay, commercial gaps)
    4. Simplicity constraint (1-3 core functions maximum)
    5. Quality score threshold (engagement + keyword density + recency)

    Args:
        submission: PRAW submission object

    Returns:
        Tuple of (should_store: bool, quality_score: float)
    """
    # Check minimum engagement
    if submission.score < MIN_ENGAGEMENT_SCORE:
        return False, 0.0

    # Check minimum comments
    if submission.num_comments < MIN_COMMENT_COUNT:
        return False, 0.0

    # Combine title and content for analysis
    full_text = f"{submission.title} {submission.selftext}"

    # Check problem keywords (existing filter)
    if not contains_problem_keywords(full_text):
        return False, 0.0

    # NEW: Check monetization signals
    # Filter out posts without willingness-to-pay or commercial viability signals
    if not has_monetization_signals(full_text):
        return False, 0.0

    # NEW: Check simplicity constraint
    # Filter out complex apps with 4+ core functions
    if not meets_simplicity_constraint(full_text):
        return False, 0.0

    # Calculate quality score (existing scoring)
    quality_score = calculate_quality_score(submission)

    # Check minimum quality threshold
    if quality_score < MIN_QUALITY_SCORE:
        return False, quality_score

    return True, quality_score


def transform_submission(submission: Any) -> Dict[str, Any]:
    """
    Transform Reddit submission to database schema.

    Args:
        submission: PRAW submission object

    Returns:
        Dictionary with submission data matching database schema
    """
    # Extract raw data
    submission_data = {
        "id": submission.id,
        "title": submission.title,
        "selftext": submission.selftext,
        "url": submission.url,
        "score": submission.score,
        "num_comments": submission.num_comments,
        "created_utc": submission.created_utc,
    }

    # Resolve canonical UUID
    resolution = resolve_submission_id(submission_data["id"])
    resolved_id = resolution.uuid  # Extract UUID string from ResolutionResult

    # Get content
    selftext = submission_data.get("selftext", "") or ""

    # Get score and comments
    score_value = submission_data.get("score")
    comments_count = submission_data.get("num_comments")

    # Transform to database schema
    transformed = {
        "id": resolved_id,  # Canonical UUID string
        "reddit_id": str(submission_data["id"]),
        "title": submission_data.get("title"),
        "content": selftext if selftext else None,
        "url": submission_data.get("url"),
        "score": score_value,
        "num_comments": comments_count,
        "created_at": datetime.fromtimestamp(
            submission_data.get("created_utc", time.time())
        ).isoformat(),
    }

    return transformed


def store_submissions(submissions: List[Dict[str, Any]]) -> bool:
    """
    Store submissions directly to Supabase using batch upsert.

    Args:
        submissions: List of transformed submission dictionaries

    Returns:
        True if successful, False otherwise
    """
    if not submissions:
        print("⚠️  No submissions to store")
        return False

    print(f"\nStoring {len(submissions)} submissions to Supabase...")
    print("-" * 80)

    try:
        client = get_supabase_client()

        # Batch upsert to submissions table
        # Use reddit_id as conflict key for idempotency
        result = client.table("submissions").upsert(
            submissions,
            on_conflict='reddit_id'
        ).execute()

        print(f"✓ Stored {len(submissions)} submissions successfully!")
        print(f"  - Total rows affected: {len(result.data)}")

        return True

    except Exception as e:
        print(f"✗ Failed to store submissions: {e}")
        logger.error(f"Supabase upsert failed: {e}", exc_info=True)
        return False


def collect_and_store_submissions(
    subreddits: List[str],
    limit: int = 50,
    sort_type: str = "new"
) -> bool:
    """
    Collect Reddit submissions and store directly to Supabase.

    Args:
        subreddits: List of subreddit names
        limit: Posts to collect per subreddit
        sort_type: Sort type (new, hot, top, rising)

    Returns:
        True if successful, False otherwise
    """
    print(f"Collecting problem posts from {len(subreddits)} subreddits...")
    print(f"Limit: {limit} posts per subreddit")
    print(f"Sort type: {sort_type}")
    print("-" * 80)

    reddit = get_reddit_client()
    all_submissions = []

    for subreddit_name in subreddits:
        print(f"\nProcessing r/{subreddit_name}...")

        try:
            subreddit = reddit.subreddit(subreddit_name)

            # Get submissions based on sort type
            if sort_type == "new":
                submissions = subreddit.new(limit=limit)
            elif sort_type == "hot":
                submissions = subreddit.hot(limit=limit)
            elif sort_type == "top":
                submissions = subreddit.top(limit=limit)
            elif sort_type == "rising":
                submissions = subreddit.rising(limit=limit)
            else:
                submissions = subreddit.new(limit=limit)

            # Filter for quality problem posts
            problem_count = 0
            checked_count = 0
            filtered_low_quality = 0

            for submission in submissions:
                checked_count += 1

                # Check if contains problem keywords
                combined_text = f"{submission.title} {submission.selftext}"
                if contains_problem_keywords(combined_text):
                    # Pre-filter quality BEFORE storage
                    should_store, quality_score = should_store_submission(submission)

                    if should_store:
                        # Transform and add to list
                        transformed = transform_submission(submission)
                        all_submissions.append(transformed)
                        problem_count += 1
                    else:
                        filtered_low_quality += 1

            print(f"✓ Checked {checked_count} posts, found {problem_count} quality problem posts")
            if filtered_low_quality > 0:
                print(f"  💾 Filtered {filtered_low_quality} low-quality posts (saved storage)")

        except Exception as e:
            print(f"✗ Error processing r/{subreddit_name}: {e}")
            logger.error(f"Subreddit collection failed: {e}", exc_info=True)

    print(f"\nTotal problem posts collected: {len(all_submissions)}")

    if not all_submissions:
        print("✗ No problem posts found")
        return False

    # Store to Supabase
    return store_submissions(all_submissions)


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect problem posts using direct Supabase storage"
    )
    parser.add_argument(
        "--subreddits",
        nargs="+",
        default=TARGET_SUBREDDITS[:1],  # Default to one subreddit for testing
        help="Subreddit names to collect from"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Posts to collect per subreddit"
    )
    parser.add_argument(
        "--sort",
        type=str,
        default="new",
        choices=["new", "hot", "top", "rising"],
        help="Sort type for posts"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("Supabase Direct Collection")
    print("=" * 80)

    # Collect and store
    start_time = time.time()
    success = collect_and_store_submissions(
        subreddits=args.subreddits,
        limit=args.limit,
        sort_type=args.sort
    )
    duration = time.time() - start_time

    if success:
        print(f"\n✓ Collection completed in {duration:.2f}s")
        print(f"  - Rate: {args.limit / duration:.1f} posts/sec")
        return 0
    else:
        print(f"\n✗ Collection failed after {duration:.2f}s")
        return 1


if __name__ == "__main__":
    sys.exit(main())
