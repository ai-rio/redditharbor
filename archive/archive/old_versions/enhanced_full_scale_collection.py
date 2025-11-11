#!/usr/bin/env python3
"""
Enhanced Full-Scale RedditHarbor Data Collection
Collects from all 73 target subreddits with enhanced metadata
Built from proven full_scale_collection.py with inline enhancements
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
    handlers=[
        logging.FileHandler(f'error_log/enhanced_full_scale_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Target subreddits by market segment (from core/collection.py)
TARGET_SUBREDDITS = {
    "health_fitness": [
        "fitness", "bodyweightfitness", "nutrition", "loseit", "gainit", "keto",
        "running", "cycling", "yoga", "meditation", "mentalhealth", "personaltraining",
        "homegym", "fitness30plus"
    ],
    "finance_investing": [
        "personalfinance", "investing", "stocks", "Bogleheads",
        "financialindependence", "CryptoCurrency", "cryptocurrencymemes",
        "Bitcoin", "ethfinance", "FinancialCareers", "tax",
        "Accounting", "RealEstateInvesting"
    ],
    "education_career": [
        "learnprogramming", "cscareerquestions", "IWantToLearn", "selfimprovement",
        "getdisciplined", "productivity", "study", "careerguidance", "resumes",
        "jobs", "interviews"
    ],
    "travel_experiences": [
        "travel", "solotravel", "backpacking", "digitalnomad", "expats",
        "travel_intel", "TravelHacks", "onebag", "shoestring", "Roadtrip",
        "travel_tips", "Wanderlust"
    ],
    "real_estate": [
        "RealEstate", "realestateinvesting", "FirstTimeHomeBuyer", "Landlord",
        "Homeowners", "CommercialRealEstate", "realtors", "HomeImprovement",
        "Mortgages", "RentalInvesting", "HousingMarket"
    ],
    "technology_saas": [
        "SaaS", "startups", "Entrepreneur", "webdev", "programming",
        "digitalnomad", "buildinpublic", "microsaas", "indiehackers",
        "EntrepreneurRideAlong", "alphaandbetausers", "roastmystartup"
    ]
}

# Flatten all subreddits
ALL_SUBREDDITS = []
for segment in TARGET_SUBREDDITS.values():
    ALL_SUBREDDITS.extend(segment)

# Enhanced metadata extraction keywords (from core/collection.py)
PROBLEM_KEYWORDS = [
    "problem", "issue", "struggle", "difficult", "hard", "frustrated", "annoying",
    "pain", "challenge", "stuck", "help", "advice", "how do i", "can't figure out",
    "doesn't work", "broken", "failing", "confused", "lost", "need", "looking for",
    "any suggestions", "alternatives", "better way", "waste of time", "inefficient",
    "complicated", "overwhelming", "impossible", "nightmare", "hate", "sucks",
    "terrible", "worst", "awful", "disaster"
]

SOLUTION_MENTION_KEYWORDS = [
    "using", "tried", "found", "works for me", "solution", "fixed", "solved",
    "tool", "app", "software", "service", "platform", "website", "recommend",
    "alternative", "better than", "switched to", "replaced", "upgrade",
    "workaround", "hack", "tip", "trick"
]

PAYMENT_WILLINGNESS_SIGNALS = [
    "willing to pay", "happy to pay", "worth paying", "subscription", "premium",
    "paid version", "upgrade", "invest in", "budget for", "spend on",
    "pay for", "cost", "price", "pricing", "expensive", "cheap", "free alternative"
]

# Enhancement functions
def calculate_sentiment_score(text: str) -> float:
    """Calculate sentiment score using TextBlob (-1.0 to 1.0)"""
    try:
        if not text or not text.strip():
            return 0.0
        blob = TextBlob(text)
        return round(blob.sentiment.polarity, 4)
    except Exception as e:
        logger.warning(f"Sentiment calculation failed: {e}")
        return 0.0

def extract_problem_keywords(text: str) -> str:
    """Extract problem keywords from text"""
    try:
        if not text:
            return ""
        text_lower = text.lower()
        found_keywords = [kw for kw in PROBLEM_KEYWORDS if kw in text_lower]
        return ", ".join(found_keywords[:10])  # Limit to 10 keywords
    except Exception as e:
        logger.warning(f"Problem keyword extraction failed: {e}")
        return ""

def extract_solution_mentions(text: str) -> str:
    """Extract solution mentions from text"""
    try:
        if not text:
            return ""
        text_lower = text.lower()
        found_keywords = [kw for kw in SOLUTION_MENTION_KEYWORDS if kw in text_lower]
        return ", ".join(found_keywords[:10])
    except Exception as e:
        logger.warning(f"Solution mention extraction failed: {e}")
        return ""

def get_or_create_subreddit_id(supabase_client, subreddit_name: str) -> str:
    """Get or create subreddit ID in database"""
    try:
        # Check if subreddit exists
        result = supabase_client.table('subreddits').select('id').eq('name', subreddit_name).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]['id']

        # Create new subreddit
        insert_result = supabase_client.table('subreddits').insert({
            'name': subreddit_name,
            'created_at': datetime.utcnow().isoformat()
        }).execute()

        return insert_result.data[0]['id']
    except Exception as e:
        logger.error(f"Failed to get/create subreddit {subreddit_name}: {e}")
        return None

def get_or_create_redditor_id(supabase_client, author_name: str) -> str:
    """Get or create redditor ID in database"""
    try:
        if not author_name or author_name in ['[deleted]', 'AutoModerator']:
            return None

        # Check if redditor exists
        result = supabase_client.table('redditors').select('redditor_id').eq('name', author_name).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]['redditor_id']

        # Create new redditor
        insert_result = supabase_client.table('redditors').insert({
            'name': author_name,
            'redditor_id': author_name,
            'created_at': datetime.utcnow().isoformat()
        }).execute()

        return insert_result.data[0]['redditor_id']
    except Exception as e:
        logger.warning(f"Failed to get/create redditor {author_name}: {e}")
        return None

logger.info(f"🎯 Starting Enhanced Full-Scale Collection from {len(ALL_SUBREDDITS)} subreddits")
logger.info(f"📊 Market segments: {list(TARGET_SUBREDDITS.keys())}")

def main():
    try:
        logger.info("="*80)
        logger.info("🚀 ENHANCED FULL-SCALE COLLECTION")
        logger.info("="*80)
        logger.info(f"📊 Target: {len(ALL_SUBREDDITS)} subreddits across {len(TARGET_SUBREDDITS)} market segments")
        logger.info("🔍 Enhanced Features: sentiment analysis, problem extraction, solution tracking")
        logger.info("="*80)

        # Create clients
        logger.info("\n🔑 Creating Reddit and Supabase clients...")
        reddit_client = reddit(
            public_key=REDDIT_PUBLIC,
            secret_key=REDDIT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        supabase_client = supabase(
            url=SUPABASE_URL,
            private_key=SUPABASE_KEY
        )

        # Collection parameters
        sort_types = ["hot", "top", "rising"]
        limit_per_sort = 50
        time_filter = "month"

        logger.info("\n📝 Collection parameters:")
        logger.info(f"   - Subreddits: {len(ALL_SUBREDDITS)}")
        logger.info(f"   - Sort types: {sort_types}")
        logger.info(f"   - Limit per sort: {limit_per_sort}")
        logger.info(f"   - Time filter: {time_filter}")
        logger.info(f"   - Expected submissions: ~{len(ALL_SUBREDDITS) * len(sort_types) * limit_per_sort}")

        # Collect from each market segment
        total_submissions = 0
        total_enhanced = 0

        for segment_name, subreddits in TARGET_SUBREDDITS.items():
            logger.info(f"\n{'='*80}")
            logger.info(f"📈 COLLECTING: {segment_name.upper()}")
            logger.info(f"{'='*80}")
            logger.info(f"📍 Subreddits ({len(subreddits)}): {', '.join(subreddits)}")

            segment_submissions = 0
            segment_enhanced = 0

            for subreddit_name in subreddits:
                logger.info(f"\n🔍 Processing r/{subreddit_name}...")

                try:
                    subreddit = reddit_client.subreddit(subreddit_name)
                    subreddit_id = get_or_create_subreddit_id(supabase_client, subreddit_name)

                    if not subreddit_id:
                        logger.warning(f"   ⚠️  Could not create subreddit ID for {subreddit_name}")
                        continue

                    sub_count = 0

                    for sort_type in sort_types:
                        try:
                            # Fetch submissions based on sort type
                            if sort_type == "hot":
                                submissions = subreddit.hot(limit=limit_per_sort)
                            elif sort_type == "top":
                                submissions = subreddit.top(time_filter=time_filter, limit=limit_per_sort)
                            elif sort_type == "rising":
                                submissions = subreddit.rising(limit=limit_per_sort)

                            for submission in submissions:
                                try:
                                    # Get or create author
                                    author_name = str(submission.author) if submission.author else '[deleted]'
                                    redditor_id = get_or_create_redditor_id(supabase_client, author_name)

                                    # Combine title and selftext for analysis
                                    full_text = f"{submission.title} {submission.selftext}"

                                    # Calculate enhanced metadata
                                    sentiment_score = calculate_sentiment_score(full_text)
                                    problem_keywords = extract_problem_keywords(full_text)
                                    solution_mentions = extract_solution_mentions(full_text)

                                    # Prepare submission data
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
                                        # Enhanced fields
                                        'sentiment_score': sentiment_score,
                                        'problem_keywords': problem_keywords,
                                        'solution_mentions': solution_mentions
                                    }

                                    # Check if submission exists, then insert or update
                                    existing = supabase_client.table('submissions').select('id').eq('submission_id', submission.id).execute()

                                    if existing.data and len(existing.data) > 0:
                                        # Update existing
                                        result = supabase_client.table('submissions').update(submission_data).eq('submission_id', submission.id).execute()
                                    else:
                                        # Insert new
                                        result = supabase_client.table('submissions').insert(submission_data).execute()

                                    sub_count += 1
                                    if problem_keywords or solution_mentions:
                                        segment_enhanced += 1

                                except Exception as e:
                                    logger.warning(f"      Failed to process submission {submission.id}: {e}")
                                    continue

                            # Rate limiting
                            time.sleep(2.0 if sort_type == "top" else 1.5)

                        except Exception as e:
                            logger.error(f"   ❌ Failed {sort_type} for r/{subreddit_name}: {e}")
                            continue

                    logger.info(f"   ✅ r/{subreddit_name}: {sub_count} submissions")
                    segment_submissions += sub_count
                    total_submissions += sub_count

                except Exception as e:
                    logger.error(f"   ❌ r/{subreddit_name}: Error - {e!s}")
                    continue

            total_enhanced += segment_enhanced
            logger.info(f"\n✅ {segment_name} segment complete:")
            logger.info(f"   📊 Submissions: {segment_submissions}")
            logger.info(f"   🎯 With Enhanced Data: {segment_enhanced}")

        # Final summary
        logger.info(f"\n{'='*80}")
        logger.info("🎉 ENHANCED FULL-SCALE COLLECTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"📊 Total Submissions: {total_submissions}")
        logger.info(f"🎯 With Enhanced Metadata: {total_enhanced}")
        logger.info(f"🏆 Success! Enhanced data collected from {len(ALL_SUBREDDITS)} subreddits")

        # Verify in database
        logger.info("\n🔍 Verifying database...")
        subs_result = supabase_client.table('submissions').select('id', count='exact').execute()
        sentiment_result = supabase_client.table('submissions').select('id', count='exact').not_.is_('sentiment_score', 'null').execute()
        problems_result = supabase_client.table('submissions').select('id', count='exact').neq('problem_keywords', '').execute()
        solutions_result = supabase_client.table('submissions').select('id', count='exact').neq('solution_mentions', '').execute()

        logger.info("✅ Database verified:")
        logger.info(f"   📝 Total Submissions: {subs_result.count}")
        logger.info(f"   🎭 With Sentiment: {sentiment_result.count}")
        logger.info(f"   🔍 With Problems: {problems_result.count}")
        logger.info(f"   💡 With Solutions: {solutions_result.count}")

        return True

    except Exception as e:
        logger.error(f"❌ Collection failed: {e!s}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
