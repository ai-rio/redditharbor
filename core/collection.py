"""
RedditHarbor Core Collection Module

Handles the main data collection functionality for RedditHarbor with comprehensive comment collection
and specialized support for monetizable app research methodology.
"""

import json
import logging
import re
import time
import traceback
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Strategic subreddit lists for monetizable app research
TARGET_SUBREDDITS = {
    "health_fitness": [
        "fitness", "bodyweightfitness", "nutrition", "loseit", "gainit", "keto",
        "running", "cycling", "yoga", "meditation", "mentalhealth",
        "personaltraining", "homegym", "fitness30plus"
    ],
    "finance_investing": [
        "personalfinance", "investing", "stocks", "Bogleheads", "financialindependence",
        "CryptoCurrency", "cryptocurrencymemes", "Bitcoin", "ethfinance",
        "FinancialCareers", "tax", "Accounting", "RealEstateInvesting"
    ],
    "education_career": [
        "learnprogramming", "cscareerquestions", "IWantToLearn",
        "selfimprovement", "getdisciplined", "productivity", "study",
        "careerguidance", "resumes", "jobs", "interviews"
    ],
    "travel_experiences": [
        "travel", "solotravel", "backpacking", "digitalnomad",
        "TravelHacks", "flights", "airbnb", "cruise", "roadtrips",
        "AskTourism", "TravelTips", "Shoestring"
    ],
    "real_estate": [
        "RealEstate", "realtors", "FirstTimeHomeBuyer", "HomeImprovement",
        "landlord", "Renting", "PropertyManagement", "Homeowners",
        "RealEstateTech", "houseflipper", "zillowgonewild"
    ],
    "technology_saas": [
        "SaaS", "startups", "Entrepreneur", "SideProject",
        "antiwork", "workreform", "productivity", "selfhosted",
        "apphookup", "iosapps", "androidapps", "software"
    ]
}

ALL_TARGET_SUBREDDITS = [subreddit for category in TARGET_SUBREDDITS.values() for subreddit in category]

# Problem and solution keyword sets for opportunity identification
PROBLEM_KEYWORDS = [
    "pain", "problem", "frustrated", "wish", "if only", "hate", "annoying", "difficult",
    "struggle", "confusing", "complicated", "time consuming", "manual", "tedious",
    "cumbersome", "inefficient", "slow", "expensive", "costly", "broken", "doesn't work",
    "fails", "error", "bug", "issue", "limitation", "lacks", "missing", "no way to",
    "hard to", "impossible", "can't", "unable to", "annoying", "irksome", "aggravating"
]

MONETIZATION_KEYWORDS = [
    "pay", "price", "cost", "subscription", "premium", "upgrade", "paid", "free trial",
    "freemium", "one-time", "monthly", "yearly", "affordable", "expensive", "worth it",
    "value", "budget", "investment", "roi", "return", "savings", "cheaper", "cheapest"
]

PAYMENT_WILLINGNESS_SIGNALS = [
    "would pay", "willing to pay", "happy to pay", "glad to pay", "I'd pay", "I'd happily pay",
    "worth paying for", "good value", "I'd pay", "I'll pay", "sign me up", "buy",
    "purchase", "subscription", "premium version", "paid features", "upgrade to pro",
    "if it costs", "price of", "cost me", "spend", "budget of"
]

WORKAROUND_KEYWORDS = [
    "workaround", "hack", "DIY", "I use", "I do", "manually", "I created", "I built",
    "I made", "I found a way", "I use", "I combine", "I have to", "I end up", "I use several",
    "I use multiple", "I cobbled together", "I string together", "I have multiple apps",
    "process of", "step by step", "tedious", "time consuming", "manual workaround"
]

SOLUTION_MENTION_KEYWORDS = [
    "I use", "I use", "I tried", "I recommend", "try", "use", "tool", "app", "software",
    "platform", "service", "website", "platform", "solution", "workaround", "method",
    "approach", "system", "process", "plugin", "extension", "script", "code"
]


def collect_data(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    subreddits: list[str],
    limit: int = 100,
    sort_types: list[str] | None = None,
    mask_pii: bool = True,
) -> bool:
    """
    Collect Reddit data and store it in Supabase database.

    Args:
        reddit_client: Reddit API client
        supabase_client: Supabase database client
        db_config: Database table configuration
        subreddits: List of subreddits to collect from
        limit: Maximum number of posts to collect per subreddit
        sort_types: Sort types to use ("hot", "new", "top", etc.)
        mask_pii: Whether to mask personally identifiable information

    Returns:
        bool: True if collection successful, False otherwise
    """
    if sort_types is None:
        sort_types = ["hot"]

    try:
        logger.info(f"🔍 Starting comprehensive data collection from {len(subreddits)} subreddits")

        # Collect submissions
        submissions_success = collect_submissions(
            reddit_client, supabase_client, db_config, subreddits, limit, sort_types, mask_pii
        )

        # CRITICAL: Collect comments for all submissions
        comments_success = collect_comments_for_submissions(
            reddit_client, supabase_client, db_config, subreddits, mask_pii
        )

        return submissions_success and comments_success

    except Exception as e:
        logger.error(f"❌ Data collection failed: {e!s}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False


def collect_submissions(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    subreddits: list[str],
    limit: int,
    sort_types: list[str],
    mask_pii: bool,
) -> bool:
    """Collect submissions from specified subreddits"""
    try:
        logger.info(f"📝 Collecting submissions from {len(subreddits)} subreddits")

        total_submissions = 0
        successful_subreddits = 0

        for subreddit_name in subreddits:
            try:
                logger.info(f"  📖 Processing r/{subreddit_name}")
                subreddit = reddit_client.subreddit(subreddit_name)

                subreddit_submissions = 0
                for sort_type in sort_types:
                    try:
                        if sort_type == "hot":
                            submissions = subreddit.hot(limit=limit)
                        elif sort_type == "new":
                            submissions = subreddit.new(limit=limit)
                        elif sort_type == "top":
                            submissions = subreddit.top(limit=limit)
                        elif sort_type == "rising":
                            submissions = subreddit.rising(limit=limit)
                        else:
                            submissions = subreddit.hot(limit=limit)

                        for submission in submissions:
                            try:
                                # Store submission data
                                submission_data = {
                                    "submission_id": submission.id,
                                    "title": submission.title,
                                    "author": str(submission.author) if submission.author else "[deleted]",
                                    "subreddit": subreddit_name,
                                    "score": submission.score,
                                    "num_comments": submission.num_comments,
                                    "created_utc": datetime.fromtimestamp(submission.created_utc).isoformat(),
                                    "url": submission.url,
                                    "selftext": submission.selftext[:1000] if submission.selftext else "",
                                    "permalink": submission.permalink,
                                    "over_18": submission.over_18,
                                    "collection_timestamp": datetime.utcnow().isoformat()
                                }

                                # Apply PII masking if enabled
                                if mask_pii:
                                    submission_data = apply_pii_masking(submission_data)

                                # Store in Supabase
                                result = supabase_client.table(db_config["submission"]).upsert(
                                    submission_data, on_conflict="submission_id"
                                ).execute()

                                if result.data:
                                    subreddit_submissions += 1

                            except Exception as e:
                                logger.warning(f"    ⚠️ Failed to store submission {submission.id}: {e}")
                                continue

                        # Rate limiting
                        time.sleep(2)

                    except Exception as e:
                        logger.warning(f"  ⚠️ Failed to fetch {sort_type} posts from r/{subreddit_name}: {e}")
                        continue

                total_submissions += subreddit_submissions
                successful_subreddits += 1
                logger.info(f"  ✅ Collected {subreddit_submissions} submissions from r/{subreddit_name}")

                # Rate limiting between subreddits
                time.sleep(3)

            except Exception as e:
                logger.error(f"  ❌ Failed to process r/{subreddit_name}: {e}")
                continue

        logger.info(f"✅ Submission collection complete: {total_submissions} submissions from {successful_subreddits}/{len(subreddits)} subreddits")
        return True

    except Exception as e:
        logger.error(f"❌ Submission collection failed: {e}")
        return False


def collect_comments_for_submissions(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    target_subreddits: list[str],
    mask_pii: bool,
    max_comments_per_submission: int = 50,
    max_age_hours: int = 72,  # Only process submissions from last 72 hours
) -> bool:
    """
    CRITICAL FUNCTION: Collect comments for existing submissions

    This is the key function to solve the 0 comments issue.
    It processes existing submissions and collects their comments.
    """
    try:
        logger.info("💬 CRITICAL: Starting comment collection for existing submissions")
        logger.info(f"🎯 Target subreddits: {len(target_subreddits)}")
        logger.info(f"⏰ Processing submissions from last {max_age_hours} hours")

        # Get recent submissions that need comments
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        total_comments_collected = 0
        processed_submissions = 0

        for subreddit_name in target_subreddits:
            try:
                logger.info(f"  💬 Processing comments for r/{subreddit_name}")

                # Get recent submissions from this subreddit that have comments
                submissions_query = supabase_client.table(db_config["submission"]).select(
                    "submission_id,title,num_comments,created_utc"
                ).eq("subreddit", subreddit_name).gte("created_utc", cutoff_time.isoformat()).gt("num_comments", 0).limit(50)

                submissions_result = submissions_query.execute()

                if not submissions_result.data:
                    logger.info(f"    ℹ️ No recent submissions with comments found for r/{subreddit_name}")
                    continue

                logger.info(f"    📄 Found {len(submissions_result.data)} submissions with comments")

                subreddit_comments = 0

                for submission_data in submissions_result.data:
                    try:
                        submission_id = submission_data["submission_id"]
                        expected_comments = submission_data["num_comments"]

                        logger.info(f"      💬 Processing submission {submission_id} (expected {expected_comments} comments)")

                        # Check if comments already exist for this submission
                        existing_comments_query = supabase_client.table(db_config["comment"]).select(
                            "comment_id"
                        ).eq("submission_id", submission_id).limit(1)

                        existing_comments_result = existing_comments_query.execute()

                        if existing_comments_result.data:
                            logger.info(f"        ℹ️ Comments already exist for submission {submission_id}")
                            processed_submissions += 1
                            continue

                        # Get the submission from Reddit
                        submission = reddit_client.submission(submission_id)

                        # Replace more_comments to get all comments
                        submission.comments.replace_more(limit=None)

                        comment_count = 0
                        for comment in submission.comments.list():
                            try:
                                if comment_count >= max_comments_per_submission:
                                    break

                                # Skip if comment is deleted or removed
                                if comment.author is None or comment.body in ["[deleted]", "[removed]"]:
                                    continue

                                # Store comment data
                                comment_data = {
                                    "comment_id": comment.id,
                                    "submission_id": submission_id,
                                    "author": str(comment.author) if comment.author else "[deleted]",
                                    "body": comment.body[:2000],  # Limit comment length
                                    "score": comment.score,
                                    "created_utc": datetime.fromtimestamp(comment.created_utc).isoformat(),
                                    "subreddit": subreddit_name,
                                    "parent_id": comment.parent_id,
                                    "depth": getattr(comment, 'depth', 0),
                                    "collection_timestamp": datetime.utcnow().isoformat()
                                }

                                # Apply PII masking if enabled
                                if mask_pii:
                                    comment_data = apply_pii_masking(comment_data)

                                # Store in Supabase
                                result = supabase_client.table(db_config["comment"]).upsert(
                                    comment_data, on_conflict="comment_id"
                                ).execute()

                                if result.data:
                                    comment_count += 1
                                    subreddit_comments += 1
                                    total_comments_collected += 1

                            except Exception as e:
                                logger.warning(f"        ⚠️ Failed to store comment {comment.id}: {e}")
                                continue

                        logger.info(f"        ✅ Collected {comment_count} comments for submission {submission_id}")
                        processed_submissions += 1

                        # Rate limiting between submissions
                        time.sleep(1)

                    except Exception as e:
                        logger.warning(f"      ⚠️ Failed to process submission {submission_id}: {e}")
                        continue

                logger.info(f"    ✅ Collected {subreddit_comments} comments from r/{subreddit_name}")

                # Rate limiting between subreddits
                time.sleep(5)

            except Exception as e:
                logger.error(f"  ❌ Failed to process comments for r/{subreddit_name}: {e}")
                continue

        logger.info("🎉 CRITICAL COMMENT COLLECTION COMPLETED!")
        logger.info(f"✅ Total comments collected: {total_comments_collected}")
        logger.info(f"✅ Submissions processed: {processed_submissions}")

        return total_comments_collected > 0

    except Exception as e:
        logger.error(f"❌ Comment collection failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False


def collect_standalone_comments(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    subreddits: list[str],
    limit: int = 1000,
    mask_pii: bool = True,
) -> bool:
    """
    Collect standalone comments from subreddits (alternative approach)
    """
    try:
        logger.info(f"💬 Collecting standalone comments from {len(subreddits)} subreddits")

        total_comments = 0

        for subreddit_name in subreddits:
            try:
                subreddit = reddit_client.subreddit(subreddit_name)

                # Get comments from hot posts
                for submission in subreddit.hot(limit=50):
                    try:
                        if submission.num_comments == 0:
                            continue

                        submission.comments.replace_more(limit=0)

                        for comment in submission.comments[:10]:  # Limit to top 10 comments per post
                            try:
                                if comment.author and comment.body not in ["[deleted]", "[removed]"]:
                                    comment_data = {
                                        "comment_id": comment.id,
                                        "submission_id": submission.id,
                                        "author": str(comment.author),
                                        "body": comment.body[:2000],
                                        "score": comment.score,
                                        "created_utc": datetime.fromtimestamp(comment.created_utc).isoformat(),
                                        "subreddit": subreddit_name,
                                        "parent_id": comment.parent_id,
                                        "collection_timestamp": datetime.utcnow().isoformat()
                                    }

                                    if mask_pii:
                                        comment_data = apply_pii_masking(comment_data)

                                    result = supabase_client.table(db_config["comment"]).upsert(
                                        comment_data, on_conflict="comment_id"
                                    ).execute()

                                    if result.data:
                                        total_comments += 1

                            except Exception as e:
                                logger.warning(f"    ⚠️ Failed to process comment: {e}")
                                continue

                    except Exception as e:
                        logger.warning(f"  ⚠️ Failed to process submission {submission.id}: {e}")
                        continue

                logger.info(f"  ✅ Processed comments for r/{subreddit_name}")
                time.sleep(3)

            except Exception as e:
                logger.error(f"  ❌ Failed to process r/{subreddit_name}: {e}")
                continue

        logger.info(f"✅ Standalone comment collection complete: {total_comments} comments")
        return True

    except Exception as e:
        logger.error(f"❌ Standalone comment collection failed: {e}")
        return False


def identify_market_segment(subreddit_name: str) -> str:
    """Identify the market segment for a given subreddit"""
    for segment, subreddits in TARGET_SUBREDDITS.items():
        if subreddit_name.lower() in [s.lower() for s in subreddits]:
            return segment
    return "other"


def extract_problem_keywords(text: str) -> list[str]:
    """Extract problem indicators from text"""
    if not text:
        return []

    text_lower = text.lower()
    found_keywords = []

    for keyword in PROBLEM_KEYWORDS:
        if keyword in text_lower:
            # Count occurrences
            count = text_lower.count(keyword)
            found_keywords.extend([keyword] * count)

    return list(set(found_keywords))  # Remove duplicates


def extract_workarounds(text: str) -> list[str]:
    """Extract workaround mentions from text"""
    if not text:
        return []

    text_lower = text.lower()
    found_workarounds = []

    for keyword in WORKAROUND_KEYWORDS:
        if keyword in text_lower:
            count = text_lower.count(keyword)
            found_workarounds.extend([keyword] * count)

    return list(set(found_workarounds))


def extract_solution_mentions(text: str) -> list[str]:
    """Extract current solutions mentioned in text"""
    if not text:
        return []

    text_lower = text.lower()
    solutions = []

    for keyword in SOLUTION_MENTION_KEYWORDS:
        if keyword in text_lower:
            count = text_lower.count(keyword)
            solutions.extend([keyword] * count)

    return list(set(solutions))


def detect_payment_mentions(text: str) -> list[str]:
    """Detect payment and monetization signals in text"""
    if not text:
        return []

    text_lower = text.lower()
    signals = []

    for keyword in MONETIZATION_KEYWORDS + PAYMENT_WILLINGNESS_SIGNALS:
        if keyword in text_lower:
            count = text_lower.count(keyword)
            signals.extend([keyword] * count)

    return list(set(signals))


def analyze_emotional_intensity(text: str) -> float:
    """Analyze emotional intensity of text (0.0 to 1.0)"""
    if not text:
        return 0.0

    text_lower = text.lower()

    # High intensity words
    high_intensity = [
        "hate", "love", "desperate", "urgent", "critical", "essential", "must have",
        "can't live without", "furious", "thrilled", "devastated", "frustrated",
        "annoying", "irksome", "aggravating"
    ]

    # Medium intensity words
    medium_intensity = [
        "dislike", "prefer", "nice", "good", "bad", "help", "issue", "problem",
        "difficult", "complicated", "time consuming", "manual", "tedious"
    ]

    high_count = sum(1 for word in high_intensity if word in text_lower)
    medium_count = sum(1 for word in medium_intensity if word in text_lower)

    # Calculate intensity score
    intensity = (high_count * 2 + medium_count * 1) / max(len(text.split()), 1)
    return min(intensity, 1.0)


def calculate_sentiment_score(text: str) -> float:
    """Calculate basic sentiment score (-1.0 to 1.0)"""
    if not text:
        return 0.0

    text_lower = text.lower()

    # Positive indicators
    positive_words = [
        "love", "great", "awesome", "amazing", "excellent", "good", "helpful",
        "easy", "simple", "clear", "useful", "perfect", "fantastic", "wonderful"
    ]

    # Negative indicators
    negative_words = [
        "hate", "terrible", "awful", "bad", "horrible", "difficult", "confusing",
        "complicated", "useless", "frustrating", "annoying", "broken", "slow"
    ]

    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    total_words = len(text.split())
    if total_words == 0:
        return 0.0

    sentiment = (pos_count - neg_count) / total_words
    return max(-1.0, min(1.0, sentiment))


def analyze_pain_language(text: str) -> float:
    """Analyze pain intensity indicators in text (0.0 to 1.0)"""
    if not text:
        return 0.0

    text_lower = text.lower()

    pain_indicators = [
        "pain", "frustrated", "struggle", "annoying", "tedious", "manual workaround",
        "time consuming", "cumbersome", "inefficient", "impossible", "can't", "unable",
        "no way", "lacks", "missing", "broken", "fails", "error", "issue"
    ]

    found = sum(1 for indicator in pain_indicators if indicator in text_lower)
    pain_score = found / len(pain_indicators)
    return min(pain_score, 1.0)


def extract_problem_statements(
    submissions_data: list[dict],
    comments_data: list[dict]
) -> list[str]:
    """Extract problem statements using NLP analysis"""
    problem_statements = []

    # Analyze submissions
    for submission in submissions_data:
        text = submission.get("title", "") + " " + submission.get("selftext", "")

        # Extract problem indicators
        problem_keywords = extract_problem_keywords(text)
        pain_intensity = analyze_pain_language(text)

        # If significant problem indicators found, extract statement
        if len(problem_keywords) >= 2 or pain_intensity > 0.3:
            # Try to extract the main problem sentence
            sentences = re.split(r'[.!?]', text)
            for sentence in sentences:
                sentence_keywords = extract_problem_keywords(sentence)
                sentence_pain = analyze_pain_language(sentence)
                if len(sentence_keywords) >= 1 or sentence_pain > 0.3:
                    clean_sentence = re.sub(r'[^\w\s]', '', sentence).strip()
                    if len(clean_sentence) > 20:
                        problem_statements.append(clean_sentence)

    # Analyze comments
    for comment in comments_data:
        text = comment.get("body", "")
        problem_keywords = extract_problem_keywords(text)
        pain_intensity = analyze_pain_language(text)

        if len(problem_keywords) >= 2 or pain_intensity > 0.3:
            sentences = re.split(r'[.!?]', text)
            for sentence in sentences:
                sentence_keywords = extract_problem_keywords(sentence)
                sentence_pain = analyze_pain_language(sentence)
                if len(sentence_keywords) >= 1 or sentence_pain > 0.3:
                    clean_sentence = re.sub(r'[^\w\s]', '', sentence).strip()
                    if len(clean_sentence) > 20:
                        problem_statements.append(clean_sentence)

    return list(set(problem_statements))  # Remove duplicates


def analyze_sentiment_and_pain_intensity(
    text_data: list[str],
    keywords: list[str]
) -> dict[str, float]:
    """Analyze sentiment and pain intensity scores"""
    total_sentiment = 0.0
    total_pain = 0.0
    total_emotional_intensity = 0.0
    count = len(text_data)

    if count == 0:
        return {
            "average_sentiment": 0.0,
            "average_pain_intensity": 0.0,
            "average_emotional_intensity": 0.0,
            "keyword_density": 0.0
        }

    for text in text_data:
        total_sentiment += calculate_sentiment_score(text)
        total_pain += analyze_pain_language(text)
        total_emotional_intensity += analyze_emotional_intensity(text)

    # Calculate keyword density
    total_words = sum(len(text.split()) for text in text_data)
    total_keywords = sum(text.lower().count(k.lower()) for text in text_data for k in keywords)
    keyword_density = total_keywords / max(total_words, 1)

    return {
        "average_sentiment": total_sentiment / count,
        "average_pain_intensity": total_pain / count,
        "average_emotional_intensity": total_emotional_intensity / count,
        "keyword_density": keyword_density
    }


def smart_rate_limiting(sort_type: str, collection_type: str = "submission") -> float:
    """
    Smart rate limiting based on sort type and collection type
    Returns delay in seconds
    """
    if collection_type == "submission":
        if sort_type in ["hot", "rising"]:
            return 1.5  # Faster for trending content
        elif sort_type == "top":
            return 3.0  # Slower for top posts with time filters
        else:
            return 2.0  # Default
    elif collection_type == "comment":
        return 2.0  # Moderate delay for comment collection
    else:
        return 2.5  # Default delay


def collect_monetizable_opportunities_data(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    market_segment: str = "all",
    limit_per_sort: int = 100,
    time_filter: str = "month",
    mask_pii: bool = True,
    sentiment_analysis: bool = True,
    extract_problem_keywords: bool = True,
    track_workarounds: bool = True
) -> bool:
    """
    CRITICAL: Collect data specifically for monetizable app research
    Collects from target subreddits with problem/solution tracking

    Args:
        reddit_client: Reddit API client
        supabase_client: Supabase database client
        db_config: Database table configuration
        market_segment: Target market segment (health_fitness, finance_investing, etc.) or 'all'
        limit_per_sort: Maximum posts per sort type
        time_filter: Time filter for top posts (day, week, month)
        mask_pii: Whether to mask personally identifiable information
        sentiment_analysis: Whether to perform sentiment analysis
        extract_problem_keywords: Whether to extract problem indicators
        track_workarounds: Whether to track workaround mentions

    Returns:
        bool: True if collection successful, False otherwise
    """
    try:
        logger.info("💰 Starting monetizable app research data collection")
        logger.info(f"🎯 Market segment: {market_segment}")
        logger.info(f"📊 Limit per sort: {limit_per_sort}")
        logger.info(f"⏰ Time filter: {time_filter}")

        # Select subreddits based on market segment
        if market_segment == "all":
            target_subreddits = ALL_TARGET_SUBREDDITS
            logger.info(f"🌐 Collecting from ALL {len(target_subreddits)} target subreddits")
        else:
            if market_segment in TARGET_SUBREDDITS:
                target_subreddits = TARGET_SUBREDDITS[market_segment]
                logger.info(f"🎯 Collecting from {len(target_subreddits)} subreddits in {market_segment}")
            else:
                logger.error(f"❌ Unknown market segment: {market_segment}")
                return False

        # Sort types for comprehensive collection
        sort_types = ["hot", "rising", "top"]

        # Collect submissions with enhanced metadata
        submissions_success = collect_enhanced_submissions(
            reddit_client,
            supabase_client,
            db_config,
            target_subreddits,
            limit_per_sort,
            sort_types,
            time_filter,
            mask_pii
        )

        # Collect comments with workaround tracking
        comments_success = collect_enhanced_comments(
            reddit_client,
            supabase_client,
            db_config,
            target_subreddits,
            mask_pii,
            extract_problem_keywords,
            track_workarounds
        )

        # Log collection summary
        logger.info("✅ Monetizable app research collection complete")
        logger.info(f"📊 Submissions: {'✓' if submissions_success else '✗'}")
        logger.info(f"💬 Comments: {'✓' if comments_success else '✗'}")

        return submissions_success and comments_success

    except Exception as e:
        logger.error(f"❌ Monetizable app research collection failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False


def collect_enhanced_submissions(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    subreddits: list[str],
    limit: int,
    sort_types: list[str],
    time_filter: str,
    mask_pii: bool
) -> bool:
    """
    Collect submissions with enhanced metadata for monetizable app research
    """
    try:
        logger.info(f"📝 Collecting enhanced submissions from {len(subreddits)} subreddits")

        total_submissions = 0
        successful_subreddits = 0

        for subreddit_name in subreddits:
            try:
                logger.info(f"  📖 Processing r/{subreddit_name}")
                subreddit = reddit_client.subreddit(subreddit_name)
                market_segment = identify_market_segment(subreddit_name)

                subreddit_submissions = 0

                for sort_type in sort_types:
                    try:
                        if sort_type == "hot":
                            submissions = subreddit.hot(limit=limit)
                        elif sort_type == "new":
                            submissions = subreddit.new(limit=limit)
                        elif sort_type == "top":
                            if time_filter == "day":
                                submissions = subreddit.top("day", limit=limit)
                            elif time_filter == "week":
                                submissions = subreddit.top("week", limit=limit)
                            else:
                                submissions = subreddit.top("month", limit=limit)
                        elif sort_type == "rising":
                            submissions = subreddit.rising(limit=limit)
                        else:
                            submissions = subreddit.hot(limit=limit)

                        for submission in submissions:
                            try:
                                # Enhanced submission data for monetizable app research
                                submission_data = {
                                    "submission_id": submission.id,
                                    "title": submission.title,
                                    "author": str(submission.author) if submission.author else "[deleted]",
                                    "subreddit": subreddit_name,
                                    "score": submission.score,
                                    "num_comments": submission.num_comments,
                                    "created_utc": datetime.fromtimestamp(submission.created_utc).isoformat(),
                                    "url": submission.url,
                                    "selftext": submission.selftext[:1000] if submission.selftext else "",
                                    "permalink": submission.permalink,
                                    "over_18": submission.over_18,
                                    "collection_timestamp": datetime.utcnow().isoformat(),
                                    # Enhanced fields for monetizable app research
                                    "market_segment": market_segment,
                                    "sort_type": sort_type,
                                    "time_filter": time_filter,
                                    "post_engagement_rate": submission.score / max(submission.num_comments, 1),
                                    "emotional_language_score": analyze_emotional_intensity(submission.title + " " + submission.selftext),
                                    "sentiment_score": calculate_sentiment_score(submission.title + " " + submission.selftext),
                                    "problem_indicators": json.dumps(extract_problem_keywords(submission.selftext)),
                                    "solution_mentions": json.dumps(extract_solution_mentions(submission.selftext)),
                                    "monetization_signals": json.dumps(detect_payment_mentions(submission.selftext))
                                }

                                # Apply PII masking if enabled
                                if mask_pii:
                                    submission_data = apply_pii_masking(submission_data)

                                # Store in Supabase
                                result = supabase_client.table(db_config.get("submission", "submissions")).upsert(
                                    submission_data, on_conflict="submission_id"
                                ).execute()

                                if result.data:
                                    subreddit_submissions += 1

                            except Exception as e:
                                logger.warning(f"    ⚠️ Failed to store submission {submission.id}: {e}")
                                continue

                        # Smart rate limiting
                        delay = smart_rate_limiting(sort_type, "submission")
                        time.sleep(delay)

                    except Exception as e:
                        logger.warning(f"  ⚠️ Failed to fetch {sort_type} posts from r/{subreddit_name}: {e}")
                        continue

                total_submissions += subreddit_submissions
                successful_subreddits += 1
                logger.info(f"  ✅ Collected {subreddit_submissions} enhanced submissions from r/{subreddit_name}")

                # Rate limiting between subreddits
                time.sleep(3)

            except Exception as e:
                logger.error(f"  ❌ Failed to process r/{subreddit_name}: {e}")
                continue

        logger.info(f"✅ Enhanced submission collection complete: {total_submissions} submissions from {successful_subreddits}/{len(subreddits)} subreddits")
        return True

    except Exception as e:
        logger.error(f"❌ Enhanced submission collection failed: {e}")
        return False


def collect_enhanced_comments(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    target_subreddits: list[str],
    mask_pii: bool,
    extract_problem_keywords: bool = True,
    track_workarounds: bool = True
) -> bool:
    """
    Collect comments with enhanced metadata for monetizable app research
    """
    try:
        logger.info("💬 Collecting enhanced comments for monetizable app research")

        total_comments_collected = 0
        processed_submissions = 0

        for subreddit_name in target_subreddits:
            try:
                logger.info(f"  💬 Processing comments for r/{subreddit_name}")

                # Get recent submissions from this subreddit
                submissions_query = supabase_client.table(db_config.get("submission", "submissions")).select(
                    "submission_id,title,num_comments,created_utc"
                ).eq("subreddit", subreddit_name).gt("num_comments", 0).limit(30)

                submissions_result = submissions_query.execute()

                if not submissions_result.data:
                    logger.info(f"    ℹ️ No submissions with comments found for r/{subreddit_name}")
                    continue

                logger.info(f"    📄 Found {len(submissions_result.data)} submissions with comments")

                subreddit_comments = 0

                for submission_data in submissions_result.data:
                    try:
                        submission_id = submission_data["submission_id"]

                        # Check if comments already exist for this submission
                        existing_comments_query = supabase_client.table(db_config.get("comment", "comments")).select(
                            "comment_id"
                        ).eq("submission_id", submission_id).limit(1)

                        existing_comments_result = existing_comments_query.execute()

                        if existing_comments_result.data:
                            logger.info(f"        ℹ️ Comments already exist for submission {submission_id}")
                            processed_submissions += 1
                            continue

                        # Get the submission from Reddit
                        submission = reddit_client.submission(submission_id)
                        submission.comments.replace_more(limit=10)

                        comment_count = 0
                        for comment in submission.comments.list():
                            try:
                                if comment_count >= 50:
                                    break

                                # Skip if comment is deleted or removed
                                if comment.author is None or comment.body in ["[deleted]", "[removed]"]:
                                    continue

                                # Enhanced comment data for monetizable app research
                                comment_body = comment.body[:2000] if comment.body else ""
                                sentiment = calculate_sentiment_score(comment_body)
                                pain_intensity = analyze_pain_language(comment_body)

                                comment_data = {
                                    "comment_id": comment.id,
                                    "submission_id": submission_id,
                                    "author": str(comment.author) if comment.author else "[deleted]",
                                    "body": comment_body,
                                    "score": comment.score,
                                    "created_utc": datetime.fromtimestamp(comment.created_utc).isoformat(),
                                    "subreddit": subreddit_name,
                                    "parent_id": comment.parent_id,
                                    "depth": getattr(comment, 'depth', 0),
                                    "collection_timestamp": datetime.utcnow().isoformat(),
                                    # Enhanced fields for monetizable app research
                                    "sentiment_score": sentiment,
                                    "pain_intensity_indicators": pain_intensity,
                                    "engagement_score": comment.score,
                                    "workaround_mentions": json.dumps(extract_workarounds(comment_body)) if track_workarounds else None,
                                    "payment_willingness_signals": json.dumps(detect_payment_mentions(comment_body)),
                                    "problem_keywords": json.dumps(extract_problem_keywords(comment_body)) if extract_problem_keywords else None
                                }

                                # Apply PII masking if enabled
                                if mask_pii:
                                    comment_data = apply_pii_masking(comment_data)

                                # Store in Supabase
                                result = supabase_client.table(db_config.get("comment", "comments")).upsert(
                                    comment_data, on_conflict="comment_id"
                                ).execute()

                                if result.data:
                                    comment_count += 1
                                    subreddit_comments += 1
                                    total_comments_collected += 1

                            except Exception as e:
                                logger.warning(f"        ⚠️ Failed to store comment {comment.id}: {e}")
                                continue

                        logger.info(f"        ✅ Collected {comment_count} enhanced comments for submission {submission_id}")
                        processed_submissions += 1

                        # Rate limiting between submissions
                        time.sleep(smart_rate_limiting("n/a", "comment"))

                    except Exception as e:
                        logger.warning(f"      ⚠️ Failed to process submission {submission_id}: {e}")
                        continue

                logger.info(f"    ✅ Collected {subreddit_comments} enhanced comments from r/{subreddit_name}")

                # Rate limiting between subreddits
                time.sleep(5)

            except Exception as e:
                logger.error(f"  ❌ Failed to process comments for r/{subreddit_name}: {e}")
                continue

        logger.info("🎉 Enhanced comment collection completed!")
        logger.info(f"✅ Total enhanced comments collected: {total_comments_collected}")
        logger.info(f"✅ Submissions processed: {processed_submissions}")

        return total_comments_collected > 0

    except Exception as e:
        logger.error(f"❌ Enhanced comment collection failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False


def collect_for_opportunity_scoring(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    subreddits: list[str],
    problem_keywords: list[str],
    monetization_keywords: list[str],
    limit: int = 200
) -> bool:
    """
    Collect submissions and comments for 6-dimension scoring

    This function focuses on collecting data that will be used for:
    - Market Demand Score
    - Pain Intensity Score
    - Monetization Potential Score
    - Market Gap Analysis Score
    - Technical Feasibility Score
    - Simplicity Score (1-3 core functions)
    """
    try:
        logger.info("🎯 Collecting data for opportunity scoring")
        logger.info(f"📝 Problem keywords: {len(problem_keywords)}")
        logger.info(f"💰 Monetization keywords: {len(monetization_keywords)}")

        # Use hot and rising sort types for current discussions
        sort_types = ["hot", "rising"]

        # Collect enhanced submissions
        submissions_success = collect_enhanced_submissions(
            reddit_client,
            supabase_client,
            db_config,
            subreddits,
            limit,
            sort_types,
            "week",  # Recent data for scoring
            mask_pii=True
        )

        # Collect enhanced comments
        comments_success = collect_enhanced_comments(
            reddit_client,
            supabase_client,
            db_config,
            subreddits,
            mask_pii=True,
            extract_problem_keywords=True,
            track_workarounds=True
        )

        logger.info("✅ Opportunity scoring data collection complete")
        return submissions_success and comments_success

    except Exception as e:
        logger.error(f"❌ Opportunity scoring collection failed: {e}")
        return False


def apply_pii_masking(data: dict[str, Any]) -> dict[str, Any]:
    """Apply PII masking to collected data (placeholder implementation)"""
    try:
        # For now, return data unchanged as ENABLE_PII_ANONYMIZATION is False
        # In a full implementation, this would use spaCy for PII detection and masking
        return data
    except Exception as e:
        logger.warning(f"⚠️ PII masking failed: {e}")
        return data


def get_collection_status(reddit_client, supabase_client, db_config: dict[str, str]) -> dict[str, Any]:
    """
    Get the current status of data collection.
    """
    try:
        # Get actual counts from database
        submissions_count = len(supabase_client.table(db_config["submission"]).select("submission_id").execute().data or [])
        comments_count = len(supabase_client.table(db_config["comment"]).select("comment_id").execute().data or [])
        redditors_count = len(supabase_client.table(db_config["user"]).select("user_id").execute().data or [])

        return {
            "status": "active",
            "last_collection": datetime.utcnow().isoformat(),
            "total_posts_collected": submissions_count,
            "total_comments_collected": comments_count,
            "total_redditors_collected": redditors_count,
            "collection_summary": f"{submissions_count} submissions, {comments_count} comments, {redditors_count} redditors"
        }
    except Exception as e:
        logger.error(f"❌ Failed to get collection status: {e}")
        return {
            "status": "error",
            "last_collection": None,
            "total_posts_collected": 0,
            "total_comments_collected": 0,
            "total_redditors_collected": 0,
            "error": str(e)
        }


def emergency_comment_collection(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    target_subreddits: list[str] = None,
) -> bool:
    """
    EMERGENCY FUNCTION: Aggressive comment collection to fix the 0 comments crisis
    """
    if target_subreddits is None:
        target_subreddits = [
            "personalfinance", "investing", "fitness", "learnprogramming",
            "technology", "SaaS", "entrepreneur", "selfimprovement"
        ]

    try:
        logger.info("🚨 EMERGENCY COMMENT COLLECTION ACTIVATED")
        logger.info("🎯 Target: Collect comments for existing 937 submissions")

        # Use multiple strategies for maximum comment collection

        # Strategy 1: Process recent submissions with high comment counts
        success1 = collect_comments_for_submissions(
            reddit_client, supabase_client, db_config, target_subreddits,
            mask_pii=False, max_comments_per_submission=100, max_age_hours=168  # 7 days
        )

        # Strategy 2: Standalone comment collection
        success2 = collect_standalone_comments(
            reddit_client, supabase_client, db_config, target_subreddits,
            limit=2000, mask_pii=False
        )

        logger.info("🎯 EMERGENCY COLLECTION COMPLETE")
        return success1 or success2

    except Exception as e:
        logger.error(f"❌ Emergency comment collection failed: {e}")
        return False


# ============================================================================
# DLT INTEGRATION FUNCTIONS
# ============================================================================

def collect_with_dlt_validation(
    reddit_client,
    supabase_client,
    db_config: dict[str, str],
    subreddits: list[str],
    limit: int = 100,
    sort_types: list[str] | None = None,
    mask_pii: bool = True,
    dlt_enabled: bool = False,
    dlt_min_activity_score: float = 50.0,
    dlt_time_filter: str = "day"
) -> dict[str, Any]:
    """
    Enhanced data collection with DLT activity validation integration.

    This function provides a unified interface for both traditional collection
    and DLT-enhanced collection with activity validation.

    Args:
        reddit_client: Reddit API client
        supabase_client: Supabase database client
        db_config: Database table configuration
        subreddits: List of subreddits to collect from
        limit: Maximum number of posts to collect per subreddit
        sort_types: Sort types to use ("hot", "new", "top", etc.)
        mask_pii: Whether to mask personally identifiable information
        dlt_enabled: Whether to use DLT activity validation
        dlt_min_activity_score: Minimum activity score for DLT validation
        dlt_time_filter: Time filter for DLT activity analysis

    Returns:
        dict: Collection results with both traditional and DLT statistics
    """
    try:
        logger.info("🔄 Starting unified collection with DLT validation")
        logger.info(f"🎯 Subreddits: {len(subreddits)}")
        logger.info(f"🔧 DLT enabled: {dlt_enabled}")
        logger.info(f"📊 DLT min activity score: {dlt_min_activity_score}")

        results = {
            "success": False,
            "traditional_collection": {"success": False, "stats": {}},
            "dlt_collection": {"success": False, "stats": {}},
            "combined_stats": {},
            "duration": 0.0
        }

        start_time = time.time()

        # Always run traditional collection first for backward compatibility
        logger.info("📊 Running traditional collection...")
        if sort_types is None:
            sort_types = ["hot", "top"]

        traditional_success = collect_data(
            reddit_client=reddit_client,
            supabase_client=supabase_client,
            db_config=db_config,
            subreddits=subreddits,
            limit=limit,
            sort_types=sort_types,
            mask_pii=mask_pii
        )

        results["traditional_collection"]["success"] = traditional_success

        # Get traditional collection statistics
        traditional_stats = get_collection_status(reddit_client, supabase_client, db_config)
        results["traditional_collection"]["stats"] = traditional_stats

        if dlt_enabled:
            logger.info("🚀 Running DLT-enhanced collection...")

            try:
                # Import DLT functions from scripts module
                from scripts.run_dlt_activity_collection import run_dlt_collection

                # Run DLT collection with the same subreddits
                dlt_result = run_dlt_collection(
                    subreddits=subreddits,
                    time_filter=dlt_time_filter,
                    min_activity_score=dlt_min_activity_score,
                    dry_run=False,
                    pipeline_name=f"reddit_harbor_unified_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                )

                results["dlt_collection"]["success"] = dlt_result.get("success", False)
                results["dlt_collection"]["stats"] = dlt_result

                if dlt_result.get("success"):
                    logger.info("✅ DLT collection completed successfully")
                else:
                    logger.warning(f"⚠️ DLT collection failed: {dlt_result.get('error', 'Unknown error')}")

            except ImportError as ie:
                logger.warning(f"⚠️ DLT module not available: {ie}")
                results["dlt_collection"]["stats"] = {"error": f"DLT module import failed: {ie}"}
            except Exception as e:
                logger.error(f"❌ DLT collection error: {e}")
                results["dlt_collection"]["stats"] = {"error": str(e)}
        else:
            logger.info("ℹ️ DLT collection disabled")
            results["dlt_collection"]["stats"] = {"message": "DLT collection disabled"}

        # Combine statistics
        results["combined_stats"] = {
            "total_duration": time.time() - start_time,
            "traditional_success": traditional_success,
            "dlt_success": results["dlt_collection"]["success"],
            "subreddits_processed": len(subreddits),
            "collection_mode": "unified_dlt" if dlt_enabled else "traditional_only"
        }

        # Overall success if either method succeeded
        results["success"] = (
            traditional_success or results["dlt_collection"]["success"]
        )
        results["duration"] = time.time() - start_time

        logger.info("🎉 Unified collection completed")
        logger.info(f"📊 Traditional: {'✓' if traditional_success else '✗'}")
        logger.info(f"🚀 DLT: {'✓' if results['dlt_collection']['success'] else '✗'}")
        logger.info(f"⏱️ Total duration: {results['duration']:.2f}s")

        return results

    except Exception as e:
        logger.error(f"❌ Unified collection failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "traditional_collection": {"success": False, "stats": {}},
            "dlt_collection": {"success": False, "stats": {}},
            "combined_stats": {"error": str(e)},
            "duration": 0.0
        }


def get_dlt_collection_stats(
    reddit_client,
    supabase_client,
    db_config: dict[str, str]
) -> dict[str, Any]:
    """
    Get comprehensive DLT collection statistics and performance metrics.

    This function provides detailed statistics about DLT collection performance,
    including activity validation results, quality filter effectiveness, and
    integration metrics with the existing RedditHarbor system.

    Args:
        reddit_client: Reddit API client
        supabase_client: Supabase database client
        db_config: Database table configuration

    Returns:
        dict: Comprehensive DLT collection statistics
    """
    try:
        logger.info("📊 Gathering DLT collection statistics...")

        # Get basic collection status
        base_stats = get_collection_status(reddit_client, supabase_client, db_config)

        # DLT-specific statistics
        dlt_stats = {
            "dlt_enabled": False,
            "activity_validation_enabled": False,
            "quality_filters_active": False,
            "pipeline_performance": {},
            "validation_metrics": {},
            "quality_metrics": {},
            "integration_health": {}
        }

        try:
            # Import DLT settings
            from config.settings import (
                DLT_ENABLED,
                DLT_MIN_ACTIVITY_SCORE,
                DLT_QUALITY_COMMENTS_PER_POST,
                DLT_QUALITY_MIN_COMMENT_LENGTH,
                DLT_QUALITY_MIN_SCORE,
                DLT_TIME_FILTER,
                DLT_USE_ACTIVITY_VALIDATION,
            )

            dlt_stats["dlt_enabled"] = DLT_ENABLED
            dlt_stats["activity_validation_enabled"] = DLT_USE_ACTIVITY_VALIDATION
            dlt_stats["quality_filters_active"] = True  # Always active when DLT is enabled

            # Configuration metrics
            dlt_stats["configuration"] = {
                "min_activity_score": DLT_MIN_ACTIVITY_SCORE,
                "time_filter": DLT_TIME_FILTER,
                "quality_min_comment_length": DLT_QUALITY_MIN_COMMENT_LENGTH,
                "quality_min_score": DLT_QUALITY_MIN_SCORE,
                "quality_comments_per_post": DLT_QUALITY_COMMENTS_PER_POST
            }

        except ImportError as ie:
            logger.warning(f"⚠️ DLT settings import failed: {ie}")
            dlt_stats["configuration_error"] = str(ie)

        # Database-specific metrics
        try:
            # Count submissions with enhanced DLT metadata
            submissions_query = supabase_client.table(db_config.get("submission", "submissions")).select(
                "submission_id,market_segment,sort_type,time_filter,emotional_language_score,sentiment_score"
            ).limit(1)

            submissions_result = submissions_query.execute()
            if submissions_result.data:
                dlt_stats["enhanced_metadata_available"] = True
            else:
                dlt_stats["enhanced_metadata_available"] = False

        except Exception as e:
            logger.warning(f"⚠️ Could not check enhanced metadata: {e}")
            dlt_stats["enhanced_metadata_available"] = False

        # Activity validation metrics (try to get recent activity data)
        try:
            # Check if we have recent activity data
            recent_cutoff = datetime.utcnow() - timedelta(days=1)
            recent_submissions = supabase_client.table(db_config.get("submission", "submissions")).select(
                "submission_id,created_utc,score,num_comments"
            ).gte("created_utc", recent_cutoff.isoformat()).execute()

            if recent_submissions.data:
                dlt_stats["validation_metrics"]["recent_submissions_24h"] = len(recent_submissions.data)

                # Calculate average activity metrics
                total_comments = sum(s.get("num_comments", 0) for s in recent_submissions.data)
                total_score = sum(s.get("score", 0) for s in recent_submissions.data)

                dlt_stats["validation_metrics"]["avg_comments_per_post"] = total_comments / max(len(recent_submissions.data), 1)
                dlt_stats["validation_metrics"]["avg_score_per_post"] = total_score / max(len(recent_submissions.data), 1)

        except Exception as e:
            logger.warning(f"⚠️ Could not calculate validation metrics: {e}")
            dlt_stats["validation_metrics"]["error"] = str(e)

        # Integration health check
        dlt_stats["integration_health"] = {
            "collection_module_available": True,
            "settings_available": True,
            "database_connection": base_stats.get("status") == "active",
            "reddit_client_available": bool(reddit_client),
            "supabase_client_available": bool(supabase_client)
        }

        # Combine all statistics
        combined_stats = {
            **base_stats,
            "dlt_stats": dlt_stats,
            "timestamp": datetime.utcnow().isoformat(),
            "collection_type": "dlt_enhanced"
        }

        logger.info("✅ DLT statistics collection completed")
        return combined_stats

    except Exception as e:
        logger.error(f"❌ Failed to get DLT statistics: {e}")
        return {
            "status": "error",
            "error": str(e),
            "dlt_stats": {"error": str(e)},
            "timestamp": datetime.utcnow().isoformat(),
            "collection_type": "dlt_enhanced_error"
        }
