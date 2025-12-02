#!/usr/bin/env python3
"""
Market Validation Integration

This module provides integration between the MarketDataValidator and the
RedditHarbor batch processing system.

It handles:
- Integration with batch_opportunity_scoring.py
- Conditional market validation based on scores
- Cost tracking and budget management
- Error handling and fallback strategies
- Performance optimization for large batches

This is the bridge between the existing opportunity scoring pipeline
and the new market validation capabilities.
"""

import json
import logging
import os
from typing import Any

from agent_tools.market_data_validator import MarketDataValidator, ValidationEvidence
from agent_tools.market_validation_persistence import MarketValidationPersistence
from config import settings

logger = logging.getLogger(__name__)


class MarketValidationIntegration:
    """
    Integrates market validation into the opportunity scoring pipeline.

    Usage:
        integration = MarketValidationIntegration()
        integration.validate_opportunities_batch(opportunities)
    """

    def __init__(self):
        """Initialize the integration with default settings."""
        self.validator = None  # Lazy initialization
        self.persistence = MarketValidationPersistence()
        self.total_cost = 0.0
        self.processed_count = 0
        self.validation_count = 0
        self.errors = []

        # Configuration from settings
        self.enabled = settings.MARKET_VALIDATION_ENABLED
        self.threshold = float(os.getenv("MARKET_VALIDATION_THRESHOLD", "60.0"))
        self.max_searches = settings.MARKET_VALIDATION_MAX_SEARCHES
        self.min_competitors = settings.MARKET_VALIDATION_MIN_COMPETITORS

        # Budget management
        self.max_cost_per_batch = float(os.getenv("MARKET_VALIDATION_MAX_COST", "1.00"))
        self.cost_per_validation_estimate = 0.05  # Conservative estimate

        logger.info(
            f"MarketValidationIntegration initialized: "
            f"enabled={self.enabled}, threshold={self.threshold}, "
            f"max_cost=${self.max_cost_per_batch}"
        )

    def should_validate_opportunity(self, opportunity: dict[str, Any]) -> tuple[bool, str]:
        """
        Determine if an opportunity should be market validated.

        Args:
            opportunity: Opportunity data from app_opportunities table

        Returns:
            Tuple of (should_validate: bool, reason: str)
        """
        # Check if feature is enabled
        if not self.enabled:
            return False, "Market validation disabled"

        # Check if already validated
        if opportunity.get("market_validation_timestamp"):
            return False, "Already market validated"

        # Check opportunity score threshold
        score = float(opportunity.get("opportunity_score", 0))
        if score < self.threshold:
            return False, f"Opportunity score {score} below threshold {self.threshold}"

        # Check budget
        if self.total_cost >= self.max_cost_per_batch:
            return False, f"Budget exceeded: ${self.total_cost:.3f} >= ${self.max_cost_per_batch}"

        # Check target market (prioritize certain markets)
        target_user = opportunity.get("target_user", "").lower()
        high_priority_markets = ["enterprise", "b2b", "business", "startup"]
        if any(market in target_user for market in high_priority_markets):
            return True, f"High priority market: {target_user}"

        # Check problem description for validation-worthy keywords
        problem = opportunity.get("problem_description", "").lower()
        validation_keywords = ["expensive", "cost", "pay", "price", "budget", "afford"]
        if any(keyword in problem for keyword in validation_keywords):
            return True, "Problem mentions pricing/cost"

        # For others above threshold, still consider
        return True, f"Opportunity score {score} above threshold"

    def initialize_validator(self) -> bool:
        """
        Initialize the MarketDataValidator with error handling.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.validator:
                self.validator = MarketDataValidator()
                logger.info("MarketDataValidator initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MarketDataValidator: {e}")
            self.errors.append(f"Validator init failed: {e}")
            return False

    def validate_single_opportunity(
        self, opportunity: dict[str, Any]
    ) -> tuple[ValidationEvidence | None, float]:
        """
        Validate a single opportunity with cost tracking.

        Args:
            opportunity: Opportunity data

        Returns:
            Tuple of (evidence: ValidationEvidence or None, cost: float)
        """
        if not self.initialize_validator():
            return None, 0.0

        try:
            start_cost = self.validator.total_cost

            evidence = self.validator.validate_opportunity(
                app_concept=opportunity.get("app_concept", ""),
                target_market=opportunity.get("target_user", ""),
                problem_description=opportunity.get("problem_description", ""),
                max_searches=min(self.max_searches, 3)  # Limit for cost control
            )

            actual_cost = evidence.total_cost
            self.total_cost += actual_cost

            logger.info(
                f"Validated opportunity {opportunity.get('id')[:8]}: "
                f"score={evidence.validation_score:.1f}, cost=${actual_cost:.4f}"
            )

            return evidence, actual_cost

        except Exception as e:
            logger.error(f"Error validating opportunity {opportunity.get('id')}: {e}")
            self.errors.append(f"Validation error: {e}")
            return None, 0.0

    def persist_validation_results(
        self, opportunity_id: str, evidence: ValidationEvidence
    ) -> bool:
        """
        Persist validation results to the database.

        Args:
            opportunity_id: UUID from app_opportunities table
            evidence: ValidationEvidence object

        Returns:
            True if successful, False otherwise
        """
        try:
            success, message = self.persistence.save_validation_evidence(
                app_opportunity_id=opportunity_id,
                evidence=evidence,
                validation_type="jina_reader_market_validation",
                validation_source="jina_api"
            )

            if success:
                self.validation_count += 1
                logger.info(f"Persisted validation for {opportunity_id[:8]}")
            else:
                logger.error(f"Failed to persist validation: {message}")
                self.errors.append(f"Persistence error: {message}")

            return success

        except Exception as e:
            logger.error(f"Error persisting validation results: {e}")
            self.errors.append(f"Persistence exception: {e}")
            return False

    def validate_opportunities_batch(
        self, opportunities: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Validate a batch of opportunities with cost and performance controls.

        Args:
            opportunities: List of opportunity records

        Returns:
            Dictionary with batch results and statistics
        """
        logger.info(f"Starting market validation for {len(opportunities)} opportunities")

        batch_results = {
            "processed": 0,
            "validated": 0,
            "skipped": 0,
            "total_cost": 0.0,
            "errors": [],
            "validation_results": []
        }

        # Reset counters for this batch
        self.total_cost = 0.0
        self.processed_count = 0
        self.validation_count = 0
        self.errors = []

        for opportunity in opportunities:
            self.processed_count += 1

            # Check if we should validate this opportunity
            should_validate, reason = self.should_validate_opportunity(opportunity)

            if not should_validate:
                batch_results["skipped"] += 1
                logger.debug(f"Skipping {opportunity.get('id', 'unknown')[:8]}: {reason}")
                continue

            # Validate the opportunity
            evidence, cost = self.validate_single_opportunity(opportunity)

            if not evidence:
                batch_results["errors"].append(f"Validation failed for {opportunity.get('id')}")
                continue

            # Persist results
            success = self.persist_validation_results(
                opportunity.get("id"), evidence
            )

            if success:
                batch_results["validated"] += 1
                batch_results["validation_results"].append({
                    "opportunity_id": opportunity.get("id"),
                    "app_concept": opportunity.get("app_concept"),
                    "validation_score": evidence.validation_score,
                    "data_quality_score": evidence.data_quality_score,
                    "competitors_found": len(evidence.competitor_pricing),
                    "cost": cost
                })
            else:
                batch_results["errors"].append(f"Persistence failed for {opportunity.get('id')}")

            # Check budget and stop if exceeded
            if self.total_cost >= self.max_cost_per_batch:
                logger.warning(
                    f"Budget limit reached (${self.total_cost:.3f}), stopping batch"
                )
                break

            # Log progress
            if self.processed_count % 10 == 0:
                logger.info(
                    f"Progress: {self.processed_count}/{len(opportunities)} processed, "
                    f"{self.validation_count} validated, ${self.total_cost:.3f} spent"
                )

        # Update batch results
        batch_results.update({
            "processed": self.processed_count,
            "total_cost": self.total_cost,
            "errors": self.errors
        })

        logger.info(
            f"Batch complete: {batch_results['validated']} validated, "
            f"${batch_results['total_cost']:.3f} spent, "
            f"{len(batch_results['errors'])} errors"
        )

        return batch_results

    def get_validation_summary(self) -> dict[str, Any]:
        """
        Get a summary of validation results for the current session.

        Returns:
            Dictionary with session statistics
        """
        return {
            "session_stats": {
                "processed_count": self.processed_count,
                "validation_count": self.validation_count,
                "total_cost": self.total_cost,
                "average_cost_per_validation": (
                    self.total_cost / self.validation_count if self.validation_count > 0 else 0
                ),
                "error_count": len(self.errors),
                "success_rate": (
                    (self.validation_count / self.processed_count * 100)
                    if self.processed_count > 0 else 0
                )
            },
            "configuration": {
                "enabled": self.enabled,
                "threshold": self.threshold,
                "max_searches": self.max_searches,
                "min_competitors": self.min_competitors,
                "max_cost_per_batch": self.max_cost_per_batch
            }
        }

    def get_top_validated_opportunities(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get the top validated opportunities from the database.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of validated opportunities
        """
        try:
            return self.persistence.get_validation_analytics(limit=limit, min_score=50)
        except Exception as e:
            logger.error(f"Error getting top validated opportunities: {e}")
            return []


# ============================================================================
# CONVENIENCE FUNCTIONS FOR BATCH PROCESSING
# ============================================================================

def integrate_market_validation_into_batch(opportunities: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Convenience function to integrate market validation into batch processing.

    This is designed to be called from the batch_opportunity_scoring.py script.

    Args:
        opportunities: List of opportunity records from app_opportunities

    Returns:
        Dictionary with validation results to merge into batch results
    """
    integration = MarketValidationIntegration()
    results = integration.validate_opportunities_batch(opportunities)

    # Add summary to results
    results["summary"] = integration.get_validation_summary()

    return results


def validate_high_value_opportunities(min_score: float = 70.0) -> list[dict[str, Any]]:
    """
    Validate only high-value opportunities.

    Args:
        min_score: Minimum opportunity score to validate

    Returns:
        List of validation results
    """
    try:
        from agent_tools.market_validation_persistence import get_persistence_handler

        # Get high-value opportunities without validation
        persistence = get_persistence_handler()

        # This would need to be implemented to query app_opportunities
        # For now, return empty list as placeholder
        logger.info(f"Would validate opportunities with score >= {min_score}")
        return []

    except Exception as e:
        logger.error(f"Error validating high-value opportunities: {e}")
        return []


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    integration = MarketValidationIntegration()

    # Test with sample opportunity
    sample_opportunity = {
        "id": "test-123",
        "app_concept": "AI expense tracker for freelancers",
        "target_user": "B2C freelancers",
        "problem_description": "Freelancers struggle with expense tracking and tax preparation",
        "opportunity_score": 75.5
    }

    should_validate, reason = integration.should_validate_opportunity(sample_opportunity)
    print(f"Should validate: {should_validate}, Reason: {reason}")

    # Print summary
    summary = integration.get_validation_summary()
    print(f"Configuration: {json.dumps(summary['configuration'], indent=2)}")
