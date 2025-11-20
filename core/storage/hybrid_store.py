"""Hybrid storage service for combined enrichment pipelines."""

import logging
from typing import Any

from core.dlt import PK_SUBMISSION_ID

from .dlt_loader import DLTLoader, LoadStatistics

logger = logging.getLogger(__name__)

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
    "trust_score": {"data_type": "double"},
    "trust_badge": {"data_type": "text"},
    "activity_score": {"data_type": "double"},
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


class HybridStore:
    """Storage service for hybrid submissions with combined enrichment data.

    Manages storage of submissions that have been processed through both
    opportunity and trust pipelines, combining all enrichment data.
    """

    def __init__(
        self,
        loader: DLTLoader | None = None,
        opportunity_table: str = "app_opportunities",
        profile_table: str = "submissions",
        supabase_client: Any = None,
    ):
        """Initialize HybridStore.

        Args:
            loader: DLTLoader instance (creates new one if not provided)
            opportunity_table: Table for opportunity data (default: "app_opportunities")
            profile_table: Table for enriched profiles (default: "submissions")
            supabase_client: Supabase client for trust data fetching (optional)
        """
        self.loader = loader or DLTLoader()
        self.opportunity_table = opportunity_table
        self.profile_table = profile_table
        self.primary_key = PK_SUBMISSION_ID
        self.stats = LoadStatistics()
        self.supabase_client = supabase_client
        logger.info(
            f"HybridStore initialized (opp={opportunity_table}, profile={profile_table})"
        )

    def _fetch_existing_trust_data(
        self, submission_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        """
        Batch-fetch existing trust data for submissions.

        This method prevents trust data loss by retrieving existing trust scores
        and badges BEFORE updating with new AI enrichment. Critical for Phase 2
        deduplication integration.

        Args:
            submission_ids: List of submission IDs to fetch trust data for

        Returns:
            dict: Mapping of submission_id -> trust data fields
                {
                    "submission_id": str,
                    "trust_score": float | None,
                    "trust_badge": str | None,
                    "activity_score": float | None,
                    "trust_level": str | None,
                    "trust_badges": dict | None,
                }

        Example:
            >>> store = HybridStore(supabase_client=client)
            >>> trust_data = store._fetch_existing_trust_data(["sub_001", "sub_002"])
            >>> print(trust_data["sub_001"]["trust_score"])
            85.5

        Note:
            Returns empty dict if no Supabase client configured or on database errors.
            This ensures graceful degradation - trust preservation is best-effort.
        """
        if not self.supabase_client:
            logger.debug("No Supabase client - skipping trust data fetch")
            return {}

        if not submission_ids:
            return {}

        try:
            # Batch query for all trust fields from app_opportunities
            response = (
                self.supabase_client.table(self.opportunity_table)
                .select(
                    "submission_id, trust_score, trust_badge, activity_score, "
                    "trust_level, trust_badges"
                )
                .in_("submission_id", submission_ids)
                .execute()
            )

            # Build lookup dict for fast access
            trust_data = {}
            if response.data:
                for record in response.data:
                    submission_id = record.get("submission_id")
                    if submission_id:
                        trust_data[submission_id] = {
                            "trust_score": record.get("trust_score"),
                            "trust_badge": record.get("trust_badge"),
                            "activity_score": record.get("activity_score"),
                            "trust_level": record.get("trust_level"),
                            "trust_badges": record.get("trust_badges"),
                        }

                logger.info(
                    f"[OK] Fetched trust data for {len(trust_data)}/{len(submission_ids)} submissions"
                )
            else:
                logger.debug("No existing trust data found for submissions")

            return trust_data

        except Exception as e:
            logger.error(f"[ERROR] Failed to fetch trust data: {e}")
            # Return empty dict on error - trust preservation is best-effort
            return {}

    def store(self, hybrid_submissions: list[dict[str, Any]]) -> bool:
        """Store hybrid submissions to both opportunity and profile tables.

        Splits hybrid data into opportunity and profile components and stores
        to respective tables with merge disposition.

        Args:
            hybrid_submissions: List of hybrid submission dictionaries with fields:
                Opportunity fields:
                - submission_id (required)
                - problem_description (optional)
                - app_concept (optional)
                - core_functions (optional)
                - opportunity_score (optional)

                Profile fields:
                - title (optional)
                - selftext (optional)
                - author (optional)
                - subreddit (optional)
                - trust_score (optional)
                - market_validation (optional)

        Returns:
            True if both storage operations successful, False otherwise

        Example:
            >>> store = HybridStore()
            >>> submissions = [{
            ...     "submission_id": "abc123",
            ...     "problem_description": "Teams waste time...",
            ...     "app_concept": "PM platform",
            ...     "opportunity_score": 75.0,
            ...     "title": "Need feedback on my idea",
            ...     "trust_score": 85.5,
            ...     "author": "user123"
            ... }]
            >>> store.store(submissions)
            True
        """
        if not hybrid_submissions:
            logger.warning("No hybrid submissions to store")
            return False

        # PHASE 2: Pre-fetch existing trust data to prevent data loss
        submission_ids = [
            sub.get("submission_id") or sub.get("reddit_id")
            for sub in hybrid_submissions
            if sub.get("submission_id") or sub.get("reddit_id")
        ]
        existing_trust = self._fetch_existing_trust_data(submission_ids)

        # Split into opportunity and profile data
        opportunities = []
        profiles = []

        for submission in hybrid_submissions:
            # Handle field mapping: reddit_id -> submission_id for compatibility
            submission_id = submission.get("submission_id") or submission.get(
                "reddit_id"
            )

            if not submission_id:
                self.stats.skipped += 1
                continue

            # Extract opportunity fields (if has AI-generated content)
            if submission.get("problem_description"):
                # PHASE 2: Get existing trust data for this submission
                trust_data = existing_trust.get(submission_id, {})

                opp_data = {
                    "submission_id": submission_id,  # Use mapped submission_id
                    # Basic fields
                    "problem_description": submission.get("problem_description"),
                    "app_concept": submission.get("app_concept"),
                    "core_functions": (
                        submission.get("core_functions")
                        or submission.get("function_list")
                        or submission.get("functions")
                    ),
                    "value_proposition": submission.get("value_proposition"),
                    "target_user": submission.get("target_user"),
                    "monetization_model": submission.get("monetization_model"),
                    "opportunity_score": submission.get("opportunity_score"),
                    "final_score": (
                        submission.get("final_score")
                        or submission.get("opportunity_score")
                        or submission.get("total_score")
                        or submission.get("overall_score")
                    ),
                    "status": submission.get("status"),
                    # ProfilerService enrichment fields
                    "ai_profile": submission.get("ai_profile"),
                    "app_name": submission.get("app_name"),
                    "app_category": submission.get("app_category"),
                    "profession": submission.get("profession"),
                    "core_problems": submission.get("core_problems"),
                    # OpportunityService enrichment fields
                    "dimension_scores": submission.get("dimension_scores"),
                    "priority": submission.get("priority"),
                    "confidence": submission.get("confidence"),
                    "evidence_based": submission.get("evidence_based"),
                    # PHASE 2: TrustService enrichment fields with preservation
                    # Use new values if provided, otherwise preserve existing
                    "trust_score": submission.get("trust_score")
                    or trust_data.get("trust_score"),
                    "trust_badge": submission.get("trust_badge")
                    or trust_data.get("trust_badge"),
                    "activity_score": submission.get("activity_score")
                    or trust_data.get("activity_score"),
                    "trust_level": submission.get("trust_level")
                    or trust_data.get("trust_level"),
                    "trust_badges": submission.get("trust_badges")
                    or trust_data.get("trust_badges"),
                    # MonetizationService enrichment fields
                    "monetization_score": (
                        submission.get("monetization_score")
                        or submission.get("llm_monetization_score")
                        or submission.get("willingness_to_pay_score")
                    ),
                    # MarketValidationService enrichment fields
                    "market_validation_score": submission.get(
                        "market_validation_score"
                    ),
                    # Metadata fields
                    "analyzed_at": submission.get("analyzed_at"),
                    "enrichment_version": submission.get(
                        "enrichment_version", "v3.0.0"
                    ),
                    "pipeline_source": submission.get(
                        "pipeline_source", "unified_pipeline"
                    ),
                }
                opportunities.append(opp_data)

            # Extract profile fields (all enriched submissions)
            profile_data = {
                "submission_id": submission_id,  # Use mapped submission_id for DLT PK
                "reddit_id": submission_id,  # CRITICAL: Use submission_id as reddit_id for submissions table NOT NULL constraint
                "title": submission.get("title"),
                "selftext": submission.get("selftext"),
                "author": submission.get("author"),
                "subreddit": submission.get("subreddit"),
                "trust_score": submission.get("trust_score"),
                "trust_level": submission.get("trust_level"),
                "market_validation_score": submission.get("market_validation_score"),
                "opportunity_score": submission.get("opportunity_score"),
                "created_utc": submission.get("created_utc"),
                "reddit_score": submission.get("reddit_score"),
            }
            profiles.append(profile_data)

        logger.info(
            f"Storing hybrid data: {len(opportunities)} opportunities, {len(profiles)} profiles"
        )

        # Store opportunities (if any)
        opp_success = True
        if opportunities:
            opp_success = self.loader.load(
                data=opportunities,
                table_name=self.opportunity_table,
                write_disposition="merge",
                primary_key=self.primary_key,
                columns=APP_OPPORTUNITIES_COLUMNS,  # CRITICAL: JSONB type hints for proper storage
            )
            if not opp_success:
                logger.error(
                    f"Failed to store opportunities to {self.opportunity_table}"
                )
                self.stats.errors.append("Opportunity storage failed")

        # Store profiles
        profile_success = True
        if profiles:
            profile_success = self.loader.load(
                data=profiles,
                table_name=self.profile_table,
                write_disposition="merge",
                primary_key=self.primary_key,
            )
            if not profile_success:
                logger.error(f"Failed to store profiles to {self.profile_table}")
                self.stats.errors.append("Profile storage failed")

        # Overall success
        success = opp_success and profile_success

        # Update statistics
        if success:
            self.stats.loaded += len(hybrid_submissions)
            self.stats.total_attempted += len(hybrid_submissions)
            logger.info(
                f"Successfully stored {len(hybrid_submissions)} hybrid submissions"
            )
        else:
            self.stats.failed += len(hybrid_submissions)
            self.stats.total_attempted += len(hybrid_submissions)
            logger.error("Hybrid storage partially or completely failed")

        return success

    def store_batch(
        self, hybrid_submissions: list[dict[str, Any]], batch_size: int = 100
    ) -> dict[str, Any]:
        """Store hybrid submissions in batches for large datasets.

        Args:
            hybrid_submissions: List of hybrid submission dictionaries
            batch_size: Number of records per batch (default: 100)

        Returns:
            Dictionary with batch processing results

        Example:
            >>> store = HybridStore()
            >>> submissions = [...]  # Large list
            >>> results = store.store_batch(submissions, batch_size=50)
            >>> print(results['success_rate'])
            1.0
        """
        if not hybrid_submissions:
            logger.warning("No hybrid submissions to store in batch")
            return {
                "total_records": 0,
                "batches": 0,
                "successful_batches": 0,
                "failed_batches": 0,
                "success_rate": 0.0,
            }

        # Process in batches
        total_batches = (len(hybrid_submissions) + batch_size - 1) // batch_size
        successful_batches = 0
        failed_batches = 0

        logger.info(
            f"Batch storing {len(hybrid_submissions)} hybrid submissions ({total_batches} batches)"
        )

        for i in range(0, len(hybrid_submissions), batch_size):
            batch = hybrid_submissions[i : i + batch_size]
            if self.store(batch):
                successful_batches += 1
            else:
                failed_batches += 1

        success_rate = successful_batches / total_batches if total_batches > 0 else 0.0

        logger.info(
            f"Batch storage complete: {successful_batches}/{total_batches} batches successful"
        )

        return {
            "total_records": len(hybrid_submissions),
            "batches": total_batches,
            "successful_batches": successful_batches,
            "failed_batches": failed_batches,
            "success_rate": success_rate,
        }

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
