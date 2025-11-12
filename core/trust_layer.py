#!/usr/bin/env python3
"""
RedditHarbor Trust Layer System
Comprehensive activity validation and trust indicators for opportunity discovery

This module provides:
- Activity validation with multiple trust indicators
- Trend analysis and community health metrics
- Credibility scoring system
- Trust badge generation for opportunities
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple

import praw

# Configure logging
logger = logging.getLogger(__name__)


class TrustLevel(Enum):
    """Trust levels for opportunities"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class TrustIndicators:
    """Trust indicators for opportunity validation"""

    # Activity indicators
    subreddit_activity_score: float = 0.0
    post_engagement_score: float = 0.0
    community_health_score: float = 0.0
    trend_velocity_score: float = 0.0

    # Content quality indicators
    problem_validity_score: float = 0.0
    discussion_quality_score: float = 0.0
    ai_analysis_confidence: float = 0.0

    # Trust metrics
    overall_trust_score: float = 0.0
    trust_level: TrustLevel = TrustLevel.LOW
    trust_badges: List[str] = None

    # Validation metadata
    validation_timestamp: str = ""
    validation_method: str = ""
    activity_constraints_met: bool = False
    quality_constraints_met: bool = False


class TrustLayerValidator:
    """Comprehensive trust validation for RedditHarbor opportunities"""

    def __init__(self, activity_threshold: float = 25.0):
        self.activity_threshold = activity_threshold
        self.trust_weights = {
            "subreddit_activity": 0.25,      # 25% - community engagement
            "post_engagement": 0.20,       # 20% - post interaction
            "trend_velocity": 0.15,          # 15% - emerging vs established
            "problem_validity": 0.15,         # 15% - AI confidence
            "discussion_quality": 0.15,       # 15% - comment quality
            "ai_confidence": 0.10             # 10% - analysis quality
        }

    def validate_opportunity_trust(self, submission_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> TrustIndicators:
        """
        Comprehensive trust validation for a single opportunity

        Args:
            submission_data: Reddit submission data
            ai_analysis: AI analysis results

        Returns:
            TrustIndicators object with comprehensive trust metrics
        """
        indicators = TrustIndicators()
        indicators.validation_timestamp = datetime.now().isoformat()
        indicators.validation_method = "comprehensive_trust_layer"

        try:
            # 1. Activity validation
            activity_score = self._validate_subreddit_activity(submission_data)
            indicators.subreddit_activity_score = activity_score
            indicators.activity_constraints_met = activity_score >= self.activity_threshold

            # 2. Post engagement validation
            engagement_score = self._validate_post_engagement(submission_data)
            indicators.post_engagement_score = engagement_score

            # 3. Trend analysis
            trend_score = self._calculate_trend_velocity(submission_data)
            indicators.trend_velocity_score = trend_score

            # 4. Problem validation
            problem_score = self._validate_problem_validity(submission_data, ai_analysis)
            indicators.problem_validity_score = problem_score

            # 5. Discussion quality
            discussion_score = self._validate_discussion_quality(submission_data)
            indicators.discussion_quality_score = discussion_score

            # 6. AI confidence
            ai_confidence = self._validate_ai_confidence(ai_analysis)
            indicators.ai_analysis_confidence = ai_confidence

            # 7. Quality constraints check
            indicators.quality_constraints_met = self._check_quality_constraints(ai_analysis)

            # 8. Calculate overall trust score
            indicators.overall_trust_score = self._calculate_overall_trust_score(indicators)
            indicators.trust_level = self._determine_trust_level(indicators.overall_trust_score)
            indicators.trust_badges = self._generate_trust_badges(indicators)

            logger.info(f"✅ Trust validation completed: {indicators.trust_level.value} trust (score: {indicators.overall_trust_score:.1f})")

        except Exception as e:
            logger.error(f"❌ Error in trust validation: {e}")
            # Return minimal trust indicators on error
            indicators.overall_trust_score = 10.0
            indicators.trust_level = TrustLevel.LOW
            indicators.trust_badges = ["basic_validation"]

        return indicators

    def _validate_subreddit_activity(self, submission_data: Dict[str, Any]) -> float:
        """Validate subreddit activity using Reddit API"""
        try:
            from config.settings import REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT

            reddit = praw.Reddit(
                client_id=REDDIT_PUBLIC,
                client_secret=REDDIT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )

            subreddit_name = submission_data.get('subreddit', '')
            if not subreddit_name:
                return 0.0

            subreddit = reddit.subreddit(subreddit_name)

            # Use existing activity validation
            from core.activity_validation import calculate_activity_score
            activity_score = calculate_activity_score(subreddit, time_filter="day")

            # Normalize to 0-100 scale for trust scoring
            normalized_score = min(100.0, activity_score * 2)  # Scale up for better trust scoring

            return round(normalized_score, 2)

        except Exception as e:
            logger.warning(f"Error validating subreddit activity: {e}")
            return 0.0

    def _validate_post_engagement(self, submission_data: Dict[str, Any]) -> float:
        """Validate post engagement metrics"""
        try:
            upvotes = submission_data.get('upvotes', 0)
            comments = submission_data.get('comments_count', 0)

            # Calculate engagement score
            # Upvotes: log scale (0-100 points)
            if upvotes <= 0:
                upvote_score = 0
            elif upvotes <= 10:
                upvote_score = upvotes * 10
            elif upvotes <= 100:
                upvote_score = 100 + (upvotes - 10) * 5
            else:
                upvote_score = 100 + (upvotes - 100) * 2

            # Comments: linear scale (0-100 points)
            comment_score = min(100, comments)

            # Combined engagement score (70% upvotes, 30% comments)
            engagement_score = (upvote_score * 0.7) + (comment_score * 0.3)

            return round(engagement_score, 2)

        except Exception as e:
            logger.warning(f"Error validating post engagement: {e}")
            return 0.0

    def _calculate_trend_velocity(self, submission_data: Dict[str, str]) -> float:
        """Calculate trend velocity based on post timing and engagement patterns"""
        try:
            created_utc = submission_data.get('created_utc', 0)
            upvotes = submission_data.get('upvotes', 0)
            comments = submission_data.get('comments_count', 0)

            if created_utc <= 0:
                return 0.0

            # Calculate time since post creation
            created_time = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            time_diff = datetime.now(timezone.utc) - created_time
            hours_old = time_diff.total_seconds() / 3600

            # Trend velocity based on engagement rate over time
            total_engagement = upvotes + comments

            if hours_old <= 1:
                # Very recent (1 hour): high velocity potential
                velocity_score = min(100, total_engagement * 10)
            elif hours_old <= 24:
                # Recent (1 day): good velocity
                velocity_score = min(100, total_engagement * 5)
            elif hours_old <= 168:  # 1 week
                velocity_score = min(100, total_engagement * 2)
            else:
                # Older posts: lower velocity but stable
                velocity_score = min(100, total_engagement)

            # Apply time decay for very old posts
            if hours_old > 168:  # More than 1 week
                decay_factor = max(0.1, 1.0 - (hours_old - 168) / 720)  # Decay over 1 month
                velocity_score *= decay_factor

            return round(velocity_score, 2)

        except Exception as e:
            logger.warning(f"Error calculating trend velocity: {e}")
            return 0.0

    def _validate_problem_validity(self, submission_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> float:
        """Validate problem validity using AI analysis confidence"""
        try:
            # Check AI analysis completeness
            problem_desc = ai_analysis.get('problem_description', '')
            app_concept = ai_analysis.get('app_concept', '')

            if not problem_desc or len(problem_desc.strip()) < 20:
                return 0.0

            if not app_concept or len(app_concept.strip()) < 20:
                return 0.0

            # Check for problem keywords in original text
            text = submission_data.get('text', '') or submission_data.get('content', '')
            from core.collection import PROBLEM_KEYWORDS

            problem_keywords_found = len([kw for kw in PROBLEM_KEYWORDS if kw in text.lower()])

            # Calculate problem validity score
            keyword_score = min(100, problem_keywords_found * 20)
            length_score = min(100, len(problem_desc) / 2)

            validity_score = (keyword_score * 0.6) + (length_score * 0.4)

            return round(validity_score, 2)

        except Exception as e:
            logger.warning(f"Error validating problem validity: {e}")
            return 0.0

    def _validate_discussion_quality(self, submission_data: Dict[str, Any]) -> float:
        """Validate discussion quality based on comment patterns"""
        try:
            comments_count = submission_data.get('comments_count', 0)

            if comments_count == 0:
                return 0.0
            elif comments_count <= 5:
                return comments_count * 20  # Linear for small discussions
            elif comments_count <= 50:
                return 100 + (comments_count - 5) * 2  # Bonus for medium discussions
            else:
                return 100  # Max score for large discussions

        except Exception as e:
            logger.warning(f"Error validating discussion quality: {e}")
            return 0.0

    def _validate_ai_confidence(self, ai_analysis: Dict[str, Any]) -> float:
        """Validate AI analysis confidence"""
        try:
            final_score = ai_analysis.get('final_score', 0)

            # Check AI score range and consistency
            if final_score >= 70:
                return 90.0  # High confidence
            elif final_score >= 50:
                return 70.0  # Medium confidence
            elif final_score >= 30:
                return 50.0  # Low confidence
            else:
                return 30.0  # Very low confidence

        except Exception as e:
            logger.warning(f"Error validating AI confidence: {e}")
            return 0.0

    def _check_quality_constraints(self, ai_analysis: Dict[str, Any]) -> bool:
        """Check if quality constraints are met"""
        try:
            # Check function count constraint
            core_functions = ai_analysis.get('core_functions', [])
            if not isinstance(core_functions, list) or len(core_functions) > 3:
                return False

            # Check for complete app concept
            app_concept = ai_analysis.get('app_concept', '')
            if not app_concept or len(app_concept.strip()) < 20:
                return False

            # Check for problem description
            problem_desc = ai_analysis.get('problem_description', '')
            if not problem_desc or len(problem_desc.strip()) < 20:
                return False

            return True

        except Exception as e:
            logger.warning(f"Error checking quality constraints: {e}")
            return False

    def _calculate_overall_trust_score(self, indicators: TrustIndicators) -> float:
        """Calculate overall trust score from individual indicators"""
        try:
            overall_score = (
                indicators.subreddit_activity_score * self.trust_weights["subreddit_activity"] +
                indicators.post_engagement_score * self.trust_weights["post_engagement"] +
                indicators.trend_velocity_score * self.trust_weights["trend_velocity"] +
                indicators.problem_validity_score * self.trust_weights["problem_validity"] +
                indicators.discussion_quality_score * self.trust_weights["discussion_quality"] +
                indicators.ai_analysis_confidence * self.trust_weights["ai_confidence"]
            )

            return round(overall_score, 2)

        except Exception as e:
            logger.error(f"Error calculating overall trust score: {e}")
            return 10.0

    def _determine_trust_level(self, trust_score: float) -> TrustLevel:
        """Determine trust level based on trust score"""
        if trust_score >= 85:
            return TrustLevel.VERY_HIGH
        elif trust_score >= 70:
            return TrustLevel.HIGH
        elif trust_score >= 50:
            return TrustLevel.MEDIUM
        else:
            return TrustLevel.LOW

    def _generate_trust_badges(self, indicators: TrustIndicators) -> List[str]:
        """Generate trust badges based on validation results"""
        badges = []

        # Activity badge
        if indicators.activity_constraints_met:
            if indicators.subreddit_activity_score >= 80:
                badges.append("🔥 Highly Active Community")
            elif indicators.subreddit_activity_score >= 60:
                badges.append("✅ Active Community")
            else:
                badges.append("⚠️ Low Activity")

        # Engagement badge
        if indicators.post_engagement_score >= 70:
            badges.append("📈 High Engagement")
        elif indicators.post_engagement_score >= 40:
            badges.append("📊 Good Engagement")

        # Trend badge
        if indicators.trend_velocity_score >= 80:
            badges.append("🚀 Trending Topic")
        elif indicators.trend_score >= 50:
            badges.append("📈 Emerging Trend")

        # Quality badge
        if indicators.quality_constraints_met:
            badges.append("✅ Quality Verified")

        # AI confidence badge
        if indicators.ai_analysis_confidence >= 70:
            badges.append("🤖 High AI Confidence")
        elif indicators.ai_analysis_confidence >= 50:
            badges.append("🤖 AI Verified")

        # Overall trust badge
        if indicators.trust_level == TrustLevel.VERY_HIGH:
            badges.append("🏆 Premium Quality")
        elif indicators.trust_level == TrustLevel.HIGH:
            badges.append("🌟 High Trust")
        elif indicators.trust_level == TrustLevel.MEDIUM:
            badges.append("🟡 Moderate Trust")
        else:
            badges.append("⚠️ Basic Validation")

        return badges

    def generate_trust_report(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive trust report for batch analysis"""
        print("🔍 GENERATING TRUST LAYER REPORT")
        print("=" * 60)

        if not opportunities:
            return {"error": "No opportunities provided"}

        # Validate all opportunities
        validated_opportunities = []
        for i, opp in enumerate(opportunities):
            try:
                trust_indicators = self.validate_opportunity_trust(opp, opp)

                # Add trust data to opportunity
                opp.update({
                    'trust_score': trust_indicators.overall_trust_score,
                    'trust_level': trust_indicators.trust_level.value,
                    'trust_badges': trust_indicators.trust_badges,
                    'activity_score': trust_indicators.subreddit_activity_score,
                    'engagement_score': trust_indicators.post_engagement_score,
                    'trend_score': trust_indicators.trend_velocity_score,
                    'quality_constraints_met': trust_indicators.quality_constraints_met,
                    'validation_timestamp': trust_indicators.validation_timestamp
                })

                validated_opportunities.append(opp)

                print(f"  {i+1}/{len(opportunities)}: {opp.get('app_name', 'Unknown')} - {trust_indicators.trust_level.value} trust ({trust_indicators.overall_trust_score:.1f})")

            except Exception as e:
                logger.error(f"Error validating opportunity {i+1}: {e}")
                continue

        # Generate summary statistics
        trust_distribution = {
            'very_high': len([opp for opp in validated_opportunities if opp.get('trust_level') == 'very_high']),
            'high': len([opp for opp in validated_opportunities if opp.get('trust_level') == 'high']),
            'medium': len([opp for opp in validated_opportunities if opp.get('trust_level') == 'medium']),
            'low': len([opp for opp in validated_opportunities if opp.get('trust_level') == 'low'])
        }

        total_validated = len(validated_opportunities)
        avg_trust_score = sum(opp.get('trust_score', 0) for opp in validated_opportunities) / total_validated if total_validated > 0 else 0

        report = {
            'total_opportunities': total_validated,
            'average_trust_score': round(avg_trust_score, 1),
            'trust_distribution': trust_distribution,
            'opportunities': validated_opportunities,
            'validation_timestamp': datetime.now().isoformat(),
            'activity_threshold': self.activity_threshold
        }

        print(f"\n📊 TRUST SUMMARY:")
        print(f"  Total opportunities validated: {total_validated}")
        print(f"  Average trust score: {avg_trust_score:.1f}")
        print(f"  Very High trust: {trust_distribution['very_high']}")
        print(f"  High trust: {trust_distribution['high']}")
        print(f"  Medium trust: {trust_distribution['medium']}")
        print(f"  Low trust: {trust_distribution['low']}")

        return report


# Example usage and testing function
def example_usage():
    """Example usage of trust layer validation"""
    try:
        validator = TrustLayerValidator(activity_threshold=25.0)

        # Example submission data
        example_submission = {
            'submission_id': 'test123',
            'title': 'Example Post',
            'text': 'This is a test post about a problem we need to solve',
            'subreddit': 'productivity',
            'upvotes': 150,
            'comments_count': 25,
            'created_utc': 1700000000
        }

        # Example AI analysis
        example_ai_analysis = {
            'app_name': 'TestApp',
            'problem_description': 'This is a clear problem statement that needs solving',
            'app_concept': 'This app would solve the problem effectively',
            'core_functions': ['Function 1', 'Function 2'],
            'final_score': 75.0
        }

        # Validate trust
        trust_indicators = validator.validate_opportunity_trust(example_submission, example_ai_analysis)

        print(f"Trust validation completed: {trust_indicators.trust_level.value}")
        print(f"Trust score: {trust_indicators.overall_trust_score}")
        print(f"Trust badges: {trust_indicators.trust_badges}")

    except Exception as e:
        logger.error(f"Example usage failed: {e}")


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    example_usage()