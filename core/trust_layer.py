#!/usr/bin/env python3
"""
RedditHarbor Trust Layer System - Compatibility Layer

DEPRECATED: This module provides backward compatibility for existing code
that imports from core.trust_layer. New code should import from core.trust.

This compatibility layer wraps the new trust validation system while
maintaining the same API as the original implementation.

Migration Guide:
OLD: from core.trust_layer import TrustLayerValidator
NEW: from core.trust import TrustValidationService

The old TrustLayerValidator class is now a wrapper around TrustValidationService.
"""

import logging
import warnings
from typing import Any

# Import new trust validation system
from core.trust import (
    TrustIndicators,
    TrustLevel,
    TrustRepositoryFactory,
    TrustValidationRequest,
    TrustValidationService,
)
from core.trust.config import TrustWeights

# Import old classes for compatibility

# Configure logging
logger = logging.getLogger(__name__)

# Deprecation warning
warnings.warn(
    "core.trust_layer is deprecated. Use core.trust instead. "
    "This compatibility layer will be removed in version 2.0.",
    DeprecationWarning,
    stacklevel=2
)


# Compatibility wrapper for old TrustLevel enum
class TrustLevel:
    """Compatibility wrapper for TrustLevel enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Compatibility dataclass that matches old API
class TrustIndicators:
    """Compatibility wrapper for TrustIndicators dataclass."""

    def __init__(
        self,
        # Activity indicators
        subreddit_activity_score: float = 0.0,
        post_engagement_score: float = 0.0,
        community_health_score: float = 0.0,
        trend_velocity_score: float = 0.0,

        # Content quality indicators
        problem_validity_score: float = 0.0,
        discussion_quality_score: float = 0.0,
        ai_analysis_confidence: float = 0.0,

        # Trust metrics
        overall_trust_score: float = 0.0,
        trust_level: str = TrustLevel.LOW,
        trust_badges: list[str] = None,

        # Validation metadata
        validation_timestamp: str = "",
        validation_method: str = "",
        activity_constraints_met: bool = False,
        quality_constraints_met: bool = False
    ):
        self.subreddit_activity_score = subreddit_activity_score
        self.post_engagement_score = post_engagement_score
        self.community_health_score = community_health_score
        self.trend_velocity_score = trend_velocity_score
        self.problem_validity_score = problem_validity_score
        self.discussion_quality_score = discussion_quality_score
        self.ai_analysis_confidence = ai_analysis_confidence
        self.overall_trust_score = overall_trust_score
        self.trust_level = trust_level
        self.trust_badges = trust_badges or []
        self.validation_timestamp = validation_timestamp
        self.validation_method = validation_method
        self.activity_constraints_met = activity_constraints_met
        self.quality_constraints_met = quality_constraints_met

    def get_confidence_score(self) -> float:
        """Convert AI confidence to numeric score (0-100)"""
        return self.ai_analysis_confidence


class TrustLayerValidator:
    """
    Compatibility wrapper for the old TrustLayerValidator class.

    This class provides the same API as the original TrustLayerValidator
    but internally uses the new TrustValidationService.
    """

    def __init__(self, activity_threshold: float = 25.0):
        """
        Initialize trust layer validator with backward compatibility.

        Args:
            activity_threshold: Minimum activity score for validation
        """
        self.activity_threshold = activity_threshold
        self.trust_weights = TrustWeights.DEFAULT_WEIGHTS

        # Initialize new service lazily to avoid circular imports
        self._service = None
        self._repository = None

        logger.info("TrustLayerValidator initialized (compatibility mode)")

    def _get_service(self) -> TrustValidationService:
        """Get or create the trust validation service."""
        if self._service is None:
            try:
                from config.settings import SUPABASE_KEY, SUPABASE_URL
                from supabase import create_client

                supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                self._repository = TrustRepositoryFactory.create_repository(supabase_client)
                self._service = TrustValidationService(
                    repository=self._repository,
                    activity_threshold=self.activity_threshold
                )

            except Exception as e:
                logger.error(f"Failed to initialize trust validation service: {e}")
                # Create service without repository for basic functionality
                self._service = TrustValidationService(
                    repository=None,  # type: ignore
                    activity_threshold=self.activity_threshold
                )

        return self._service

    def validate_opportunity_trust(self, submission_data: dict[str, Any], ai_analysis: dict[str, Any]) -> TrustIndicators:
        """
        Validate trust for a single opportunity (backward compatibility).

        Args:
            submission_data: Reddit submission data
            ai_analysis: AI analysis results

        Returns:
            TrustIndicators object with trust metrics (old format)
        """
        try:
            service = self._get_service()

            # Convert old format to new request format
            request = TrustValidationRequest(
                submission_id=submission_data.get('submission_id', ''),
                subreddit=submission_data.get('subreddit', ''),
                upvotes=submission_data.get('upvotes', 0),
                comments_count=submission_data.get('comments_count', 0),
                created_utc=submission_data.get('created_utc', 0),
                text=submission_data.get('text') or submission_data.get('content', ''),
                title=submission_data.get('title', ''),
                ai_analysis=ai_analysis,
                activity_threshold=self.activity_threshold,
                trust_weights=self.trust_weights
            )

            # Use new service
            result = service.validate_opportunity_trust(request)

            if result.success:
                # Convert new indicators to old format
                new_indicators = result.indicators
                return TrustIndicators(
                    subreddit_activity_score=new_indicators.subreddit_activity_score,
                    post_engagement_score=new_indicators.post_engagement_score,
                    community_health_score=new_indicators.community_health_score,
                    trend_velocity_score=new_indicators.trend_velocity_score,
                    problem_validity_score=new_indicators.problem_validity_score,
                    discussion_quality_score=new_indicators.discussion_quality_score,
                    ai_analysis_confidence=new_indicators.ai_analysis_confidence,
                    overall_trust_score=new_indicators.overall_trust_score,
                    trust_level=new_indicators.trust_level.value,
                    trust_badges=new_indicators.trust_badges,
                    validation_timestamp=new_indicators.validation_timestamp,
                    validation_method=new_indicators.validation_method,
                    activity_constraints_met=new_indicators.activity_constraints_met,
                    quality_constraints_met=new_indicators.quality_constraints_met
                )
            else:
                # Return minimal trust indicators on error
                return TrustIndicators(
                    overall_trust_score=10.0,
                    trust_level=TrustLevel.LOW,
                    trust_badges=["basic_validation"],
                    validation_timestamp=result.indicators.validation_timestamp,
                    validation_method="comprehensive_trust_layer_error",
                    activity_constraints_met=False,
                    quality_constraints_met=False
                )

        except Exception as e:
            logger.error(f"Error in trust validation (compatibility mode): {e}")
            # Return minimal trust indicators on error
            return TrustIndicators(
                overall_trust_score=10.0,
                trust_level=TrustLevel.LOW,
                trust_badges=["basic_validation"],
                validation_timestamp="",
                validation_method="comprehensive_trust_layer_error",
                activity_constraints_met=False,
                quality_constraints_met=False
            )

    def generate_trust_report(self, opportunities: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Generate comprehensive trust report (backward compatibility).

        Args:
            opportunities: List of opportunity dictionaries

        Returns:
            Dictionary with trust analysis report
        """
        try:
            print("🔍 GENERATING TRUST LAYER REPORT (Compatibility Mode)")
            print("=" * 60)

            if not opportunities:
                return {"error": "No opportunities provided"}

            # Validate all opportunities using new service
            service = self._get_service()
            validated_opportunities = []

            for i, opp in enumerate(opportunities):
                try:
                    # Use old method for validation (which calls new service)
                    trust_indicators = self.validate_opportunity_trust(opp, opp)

                    # Add trust data to opportunity (old format)
                    opp.update({
                        'trust_score': trust_indicators.overall_trust_score,
                        'trust_level': trust_indicators.trust_level,
                        'trust_badges': trust_indicators.trust_badges,
                        'activity_score': trust_indicators.subreddit_activity_score,
                        'engagement_score': trust_indicators.post_engagement_score,
                        'trend_velocity_score': trust_indicators.trend_velocity_score,
                        'quality_constraints_met': trust_indicators.quality_constraints_met,
                        'validation_timestamp': trust_indicators.validation_timestamp
                    })

                    validated_opportunities.append(opp)

                    print(f"  {i+1}/{len(opportunities)}: {opp.get('app_name', 'Unknown')} - {trust_indicators.trust_level} trust ({trust_indicators.overall_trust_score:.1f})")

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
                'validation_timestamp': service.validation_history[-1].indicators.validation_timestamp if service.validation_history else "",
                'activity_threshold': self.activity_threshold
            }

            print("\n📊 TRUST SUMMARY:")
            print(f"  Total opportunities validated: {total_validated}")
            print(f"  Average trust score: {avg_trust_score:.1f}")
            print(f"  Very High trust: {trust_distribution['very_high']}")
            print(f"  High trust: {trust_distribution['high']}")
            print(f"  Medium trust: {trust_distribution['medium']}")
            print(f"  Low trust: {trust_distribution['low']}")

            return report

        except Exception as e:
            logger.error(f"Error generating trust report: {e}")
            return {"error": str(e)}


# Convenience function for easy migration
def migrate_to_new_trust_system():
    """
    Helper function to guide migration to the new trust system.

    Returns:
        Migration guide and recommendations
    """
    return {
        "deprecated_module": "core.trust_layer",
        "new_module": "core.trust",
        "migration_steps": [
            "Replace: from core.trust_layer import TrustLayerValidator",
            "With: from core.trust import create_trust_service",
            "Replace: validator = TrustLayerValidator()",
            "With: service = create_trust_service(supabase_client)",
            "Replace: indicators = validator.validate_opportunity_trust(data, ai_data)",
            "With: result = service.validate_opportunity_trust(request)",
            "Replace: trust_indicators = result.indicators"
        ],
        "benefits": [
            "Type safety with comprehensive data models",
            "Repository pattern for database abstraction",
            "Support for multiple tables and schemas",
            "Audit trail and validation history",
            "Configurable weights and thresholds",
            "Comprehensive error handling and logging",
            "Batch validation support",
            "Service-level statistics and monitoring"
        ],
        "timeline": "Compatibility layer will be removed in version 2.0"
    }


# Export old classes for backward compatibility
__all__ = [
    'TrustIndicators',
    'TrustLayerValidator',
    'TrustLevel',
    'migrate_to_new_trust_system'
]
