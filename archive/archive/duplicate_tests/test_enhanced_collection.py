#!/usr/bin/env python3
"""
Test Enhanced Collection - Small batch from 2 subreddits only
Validates the enhanced collection logic before full deployment
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from textblob import TextBlob

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redditharbor.login import reddit, supabase

from config.settings import (
    REDDIT_PUBLIC,
    REDDIT_SECRET,
    REDDIT_USER_AGENT,
    SUPABASE_KEY,
    SUPABASE_URL,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Test with just 2 subreddits
TEST_SUBREDDITS = ["startups", "SaaS"]

# Keywords
PROBLEM_KEYWORDS = [
    "problem", "issue", "struggle", "difficult", "hard", "frustrated", "annoying",
    "pain", "challenge", "stuck", "help", "advice", "how do i", "can't figure out",
    "doesn't work", "broken", "failing", "confused", "lost", "need", "looking for"
]

SOLUTION_MENTION_KEYWORDS = [
    "using", "tried", "found", "works for me", "solution", "fixed", "solved",
    "tool", "app", "software", "service", "platform", "recommend"
]

def calculate_sentiment_score(text: str) -> float:
    """Calculate sentiment score using TextBlob"""
    try:
        if not text or not text.strip():
            return 0.0
        blob = TextBlob(text)
        return round(blob.sentiment.polarity, 4)
    except Exception as e:
        logger.warning(f"Sentiment error: {e}")
        return 0.0

def extract_problem_keywords(text: str) -> str:
    """Extract problem keywords"""
    if not text:
        return ""
    text_lower = text.lower()
    found = [kw for kw in PROBLEM_KEYWORDS if kw in text_lower]
    return ", ".join(found[:10])

def extract_solution_mentions(text: str) -> str:
    """Extract solution mentions"""
    if not text:
        return ""
    text_lower = text.lower()
    found = [kw for kw in SOLUTION_MENTION_KEYWORDS if kw in text_lower]
    return ", ".join(found[:10])

def get_or_create_subreddit_id(supabase_client, subreddit_name: str) -> str:
    """Get or create subreddit ID"""
    try:
        result = supabase_client.table('subreddits').select('id').eq('name', subreddit_name).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]['id']

        insert_result = supabase_client.table('subreddits').insert({
            'name': subreddit_name,
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        return insert_result.data[0]['id']
    except Exception as e:
        logger.error(f"Subreddit error: {e}")
        return None

def get_or_create_redditor_id(supabase_client, author_name: str) -> str:
    """Get or create redditor ID"""
    try:
        if not author_name or author_name in ['[deleted]', 'AutoModerator']:
            return None

        result = supabase_client.table('redditors').select('redditor_id').eq('name', author_name).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]['redditor_id']

        insert_result = supabase_client.table('redditors').insert({
            'name': author_name,
            'redditor_id': author_name,
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        return insert_result.data[0]['redditor_id']
    except Exception as e:
        logger.warning(f"Redditor error: {e}")
        return None

def main():
    logger.info("="*80)
    logger.info("🧪 TEST ENHANCED COLLECTION")
    logger.info("="*80)
    logger.info(f"Testing with {len(TEST_SUBREDDITS)} subreddits: {TEST_SUBREDDITS}")

    # Create clients
    logger.info("\n🔑 Creating clients...")
    reddit_client = reddit(
        public_key=REDDIT_PUBLIC,
        secret_key=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    supabase_client = supabase(
        url=SUPABASE_URL,
        private_key=SUPABASE_KEY
    )

    total_submissions = 0
    total_enhanced = 0

    for subreddit_name in TEST_SUBREDDITS:
        logger.info(f"\n🔍 Testing r/{subreddit_name}...")

        try:
            subreddit = reddit_client.subreddit(subreddit_name)
            subreddit_id = get_or_create_subreddit_id(supabase_client, subreddit_name)

            if not subreddit_id:
                logger.error(f"Failed to get subreddit_id for {subreddit_name}")
                continue

            # Only collect 5 hot posts as test
            for submission in subreddit.hot(limit=5):
                try:
                    author_name = str(submission.author) if submission.author else '[deleted]'
                    redditor_id = get_or_create_redditor_id(supabase_client, author_name)

                    full_text = f"{submission.title} {submission.selftext}"

                    # Calculate enhanced metadata
                    sentiment = calculate_sentiment_score(full_text)
                    problems = extract_problem_keywords(full_text)
                    solutions = extract_solution_mentions(full_text)

                    logger.info(f"   📝 {submission.title[:50]}...")
                    logger.info(f"      Sentiment: {sentiment}")
                    logger.info(f"      Problems: {problems[:80]}")
                    logger.info(f"      Solutions: {solutions[:80]}")

                    submission_data = {
                        'submission_id': submission.id,
                        'subreddit_id': subreddit_id,
                        'redditor_id': redditor_id,
                        'subreddit': subreddit_name,
                        'title': submission.title[:300],
                        'content': submission.selftext,
                        'text': submission.selftext,
                        'upvotes': submission.score,
                        'comments_count': submission.num_comments,
                        'url': submission.url,
                        'permalink': submission.permalink,
                        'created_at': datetime.fromtimestamp(submission.created_utc).isoformat(),
                        'is_nsfw': submission.over_18,
                        'sentiment_score': sentiment,
                        'problem_keywords': problems,
                        'solution_mentions': solutions
                    }

                    # Check if submission exists
                    existing = supabase_client.table('submissions').select('id').eq('submission_id', submission.id).execute()

                    if existing.data and len(existing.data) > 0:
                        # Update existing
                        result = supabase_client.table('submissions').update(submission_data).eq('submission_id', submission.id).execute()
                    else:
                        # Insert new
                        result = supabase_client.table('submissions').insert(submission_data).execute()

                    total_submissions += 1
                    if problems or solutions:
                        total_enhanced += 1

                except Exception as e:
                    logger.error(f"Failed to process submission: {e}")
                    continue

            time.sleep(1.5)

        except Exception as e:
            logger.error(f"Failed r/{subreddit_name}: {e}")
            continue

    logger.info(f"\n{'='*80}")
    logger.info("✅ TEST COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"📊 Total Submissions: {total_submissions}")
    logger.info(f"🎯 With Enhanced Data: {total_enhanced}")

    # Verify database
    logger.info("\n🔍 Database verification:")
    subs_result = supabase_client.table('submissions').select('id', count='exact').execute()
    sentiment_result = supabase_client.table('submissions').select('id', count='exact').not_.is_('sentiment_score', 'null').execute()
    problems_result = supabase_client.table('submissions').select('id', count='exact').neq('problem_keywords', '').execute()

    logger.info(f"   Total in DB: {subs_result.count}")
    logger.info(f"   With Sentiment: {sentiment_result.count}")
    logger.info(f"   With Problems: {problems_result.count}")

    if total_submissions > 0 and total_enhanced > 0:
        logger.info("\n✅ TEST PASSED - Enhanced collection working!")
        return True
    else:
        logger.error("\n❌ TEST FAILED - No enhanced data collected")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
