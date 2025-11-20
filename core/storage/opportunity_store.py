"""Opportunity storage service for app_opportunities table."""

import logging
from typing import Any

from core.dlt import PK_SUBMISSION_ID

from .dlt_loader import DLTLoader, LoadStatistics

# JSONB column type hints for proper PostgreSQL storage
APP_OPPORTUNITIES_COLUMNS = {
    # Basic fields
    "submission_id": {"data_type": "text", "nullable": False},
    "problem_description": {"data_type": "text"},
    "app_concept": {"data_type": "text"},
    "core_functions": {"data_type": "text"},
    "value_proposition": {"data_type": "text"},
    "target_user": {"data_type": "text"},
    "monetization_model": {"data_type": "text"},
    "opportunity_score": {"data_type": "double"},
    "final_score": {"data_type": "double"},
    "status": {"data_type": "text"},

    # ProfilerService enrichment fields - CRITICAL JSONB FIELDS
    "ai_profile": {"data_type": "json"},
    "app_name": {"data_type": "text"},
    "app_category": {"data_type": "text"},
    "profession": {"data_type": "text"},
    "core_problems": {"data_type": "json"},

    # OpportunityService enrichment fields - CRITICAL JSONB FIELDS
    "dimension_scores": {"data_type": "json"},
    "priority": {"data_type": "text"},
    "confidence": {"data_type": "double"},
    "evidence_based": {"data_type": "bool"},

    # TrustService enrichment fields - CRITICAL JSONB FIELDS
    "trust_level": {"data_type": "text"},
    "trust_badges": {"data_type": "json"},

    # MonetizationService enrichment fields
    "monetization_score": {"data_type": "double"},

    # MarketValidationService enrichment fields
    "market_validation_score": {"data_type": "double"},

    # Metadata fields
    "analyzed_at": {"data_type": "timestamp"},
    "enrichment_version": {"data_type": "text"},
    "pipeline_source": {"data_type": "text"},

    # Reddit metadata fields
    "title": {"data_type": "text"},
    "subreddit": {"data_type": "text"},
    "reddit_score": {"data_type": "bigint"},
}

logger = logging.getLogger(__name__)


class OpportunityStore:
    """Storage service for opportunity analysis results.

    Manages storage of AI-generated app opportunity profiles to the app_opportunities table
    with automatic deduplication via merge disposition.
    """

    def __init__(
        self,
        loader: DLTLoader | None = None,
        table_name: str = "app_opportunities",
    ):
        """Initialize OpportunityStore.

        Args:
            loader: DLTLoader instance (creates new one if not provided)
            table_name: Target table name (default: "app_opportunities")
        """
        self.loader = loader or DLTLoader()
        self.table_name = table_name
        self.primary_key = PK_SUBMISSION_ID
        self.stats = LoadStatistics()
        logger.info(
            f"OpportunityStore initialized (table={table_name}, pk={self.primary_key})"
        )

    def store(self, opportunities: list[dict[str, Any]]) -> bool:
        """Store opportunity analysis results with merge disposition.

        Uses merge disposition to prevent duplicate records based on submission_id.

        Args:
            opportunities: List of opportunity dictionaries with fields:
                - submission_id (required)
                - problem_description (required)
                - app_concept (required)
                - core_functions (required)
                - value_proposition (required)
                - target_user (required)
                - monetization_model (required)
                - opportunity_score (optional)
                - title, subreddit, reddit_score, status (optional)

        Returns:
            True if successful, False otherwise

        Example:
            >>> store = OpportunityStore()
            >>> opportunities = [{
            ...     "submission_id": "abc123",
            ...     "problem_description": "Teams waste time...",
            ...     "app_concept": "Integrated PM platform",
            ...     "core_functions": ["Time tracking", "Gantt charts"],
            ...     "value_proposition": "Save 10 hours/week",
            ...     "target_user": "Small teams",
            ...     "monetization_model": "Subscription",
            ...     "opportunity_score": 75.0
            ... }]
            >>> store.store(opportunities)
            True
        """
        if not opportunities:
            logger.warning("No opportunities to store")
            self.stats.skipped += len(opportunities)
            return False

        # Filter to only opportunities with AI-generated content
        valid_opportunities = [
            opp for opp in opportunities if opp.get("problem_description")
        ]

        if not valid_opportunities:
            logger.warning(
                "No valid opportunities found (all missing problem_description)"
            )
            self.stats.skipped += len(opportunities)
            return False

        logger.info(
            f"Storing {len(valid_opportunities)} opportunities to {self.table_name}"
        )

        # Fix field mapping: reddit_id -> submission_id for DLT storage compatibility
        mapped_opportunities = []
        for opp in valid_opportunities:
            mapped_opp = opp.copy()
            # Map reddit_id to submission_id for DLT primary key compatibility
            if 'reddit_id' in mapped_opp and 'submission_id' not in mapped_opp:
                mapped_opp['submission_id'] = mapped_opp['reddit_id']
                # Optional: remove the original reddit_id to avoid confusion
                # mapped_opp.pop('reddit_id', None)
            mapped_opportunities.append(mapped_opp)

        success = self.loader.load(
            data=mapped_opportunities,
            table_name=self.table_name,
            write_disposition="merge",
            primary_key=self.primary_key,
            columns=APP_OPPORTUNITIES_COLUMNS,  # CRITICAL: JSONB type hints for proper storage
        )

        # Update statistics
        if success:
            self.stats.loaded += len(valid_opportunities)
            self.stats.total_attempted += len(opportunities)
            logger.info(
                f"Successfully stored {len(valid_opportunities)} opportunities"
            )
        else:
            self.stats.failed += len(valid_opportunities)
            self.stats.total_attempted += len(opportunities)
            self.stats.errors.append(
                f"Failed to store {len(valid_opportunities)} opportunities"
            )
            logger.error(f"Failed to store opportunities to {self.table_name}")

        # Track skipped
        skipped_count = len(opportunities) - len(valid_opportunities)
        if skipped_count > 0:
            self.stats.skipped += skipped_count
            logger.debug(f"Skipped {skipped_count} invalid opportunities")

        return success

    def store_batch(
        self, opportunities: list[dict[str, Any]], batch_size: int = 100
    ) -> dict[str, Any]:
        """Store opportunities in batches for large datasets.

        Args:
            opportunities: List of opportunity dictionaries
            batch_size: Number of records per batch (default: 100)

        Returns:
            Dictionary with batch processing results

        Example:
            >>> store = OpportunityStore()
            >>> opportunities = [...]  # Large list
            >>> results = store.store_batch(opportunities, batch_size=50)
            >>> print(results['success_rate'])
            1.0
        """
        if not opportunities:
            logger.warning("No opportunities to store in batch")
            return {
                "total_records": 0,
                "batches": 0,
                "successful_batches": 0,
                "failed_batches": 0,
                "success_rate": 0.0,
            }

        # Filter to valid opportunities
        valid_opportunities = [
            opp for opp in opportunities if opp.get("problem_description")
        ]

        if not valid_opportunities:
            logger.warning("No valid opportunities for batch storage")
            return {
                "total_records": len(opportunities),
                "batches": 0,
                "successful_batches": 0,
                "failed_batches": 0,
                "success_rate": 0.0,
            }

        logger.info(
            f"Batch storing {len(valid_opportunities)} opportunities (batch_size={batch_size})"
        )

        result = self.loader.load_batch(
            data=valid_opportunities,
            table_name=self.table_name,
            primary_key=self.primary_key,
            batch_size=batch_size,
            write_disposition="merge",
        )

        # Update statistics
        self.stats.loaded += result.get("loaded", 0)
        self.stats.failed += result.get("failed", 0)
        self.stats.total_attempted += len(valid_opportunities)

        logger.info(
            f"Batch storage complete: {result['successful_batches']}/{result['batches']} batches"
        )

        return result

    def get_statistics(self) -> dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with loaded, failed, skipped counts and success rate
        """
        return self.stats.get_summary()

    def reset_statistics(self) -> None:
        """Reset storage statistics."""
        self.stats = LoadStatistics()
        logger.debug("Statistics reset")
