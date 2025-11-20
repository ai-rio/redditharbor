"""Monetization analysis deduplication logic.

This module provides Agno (monetization) analysis deduplication to prevent
redundant AI analyses and preserve cost savings. Extracted from
batch_opportunity_scoring.py to enable reuse across pipelines.

Key Features:
- Check if Agno analysis should run
- Copy analysis from primary submissions
- Track deduplication statistics
- Update business concept metadata
"""

import logging
from datetime import datetime
from typing import Any

from core.deduplication.concept_manager import BusinessConceptManager

logger = logging.getLogger(__name__)


class AgnoSkipLogic:
    """
    Handle monetization analysis deduplication.

    Manages the skip logic for Agno (monetization) analyses by checking if
    a business concept already has an analysis and copying it to duplicate
    submissions when possible.

    Attributes:
        client: Initialized Supabase client
        concept_manager: BusinessConceptManager instance
        stats: Deduplication statistics tracking

    Examples:
        >>> from supabase import create_client
        >>> client = create_client(url, key)
        >>> skip_logic = AgnoSkipLogic(client)
        >>> should_run, reason = skip_logic.should_run_agno_analysis(
        ...     submission={'submission_id': 'sub123'},
        ...     business_concept_id=42
        ... )
        >>> if not should_run:
        ...     analysis = skip_logic.copy_agno_analysis('primary_id', 'sub123')
    """

    def __init__(self, supabase_client: Any):
        """
        Initialize Agno skip logic.

        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client
        self.concept_manager = BusinessConceptManager(supabase_client)
        self.stats = {"skipped": 0, "fresh": 0, "copied": 0, "errors": 0}

    def should_run_agno_analysis(
        self,
        submission: dict[str, Any],
        business_concept_id: int | None = None,
    ) -> tuple[bool, str | None]:
        """
        Determine if Agno analysis should run.

        Checks if the business concept already has an Agno analysis. If it
        does, skips analysis and returns False to trigger copying instead.

        Args:
            submission: Submission data dictionary
            business_concept_id: Optional concept ID (if None, treated as unique)

        Returns:
            tuple: (should_run, reason)
                - should_run: True if analysis should run, False if should skip
                - reason: String describing the decision

        Examples:
            >>> should_run, reason = skip_logic.should_run_agno_analysis(
            ...     {'submission_id': 'sub123'},
            ...     business_concept_id=None
            ... )
            >>> assert should_run is True  # No concept = first submission
        """
        # No concept ID means this is a unique submission (first of its kind)
        if not business_concept_id:
            self.stats["fresh"] += 1
            return True, "No business concept (first submission)"

        try:
            # Check if concept already has Agno analysis
            concept = self.concept_manager.get_concept_by_id(business_concept_id)

            if concept and concept.get("has_agno_analysis"):
                self.stats["skipped"] += 1
                return (
                    False,
                    f"Concept {concept['id']} already has Agno analysis",
                )

            self.stats["fresh"] += 1
            return True, "No existing Agno analysis found"

        except Exception as e:
            logger.error(
                f"Error checking Agno skip for submission "
                f"{submission.get('submission_id')}: {e}"
            )
            self.stats["errors"] += 1
            return True, "Error during check, running analysis as fallback"

    def update_concept_agno_stats(
        self,
        concept_id: int,
        agno_result: dict[str, Any],
    ) -> bool:
        """
        Update business concept with Agno analysis metadata.

        Calls database RPC function to update concept's has_agno_analysis flag
        and track willingness-to-pay scores.

        Args:
            concept_id: Business concept ID to update
            agno_result: Dictionary containing Agno analysis results

        Returns:
            bool: True if update succeeded, False otherwise

        Examples:
            >>> agno_result = {'willingness_to_pay_score': 85.0}
            >>> skip_logic.update_concept_agno_stats(42, agno_result)
            True
        """
        try:
            # Extract WTP score from Agno result
            wtp_score = agno_result.get("willingness_to_pay_score")
            if wtp_score is not None:
                wtp_score = float(wtp_score)

            # Call database function to update Agno tracking
            response = self.client.rpc(
                "update_agno_analysis_tracking",
                {
                    "p_concept_id": int(concept_id),
                    "p_has_analysis": True,
                    "p_wtp_score": wtp_score,
                },
            ).execute()

            if response.data and len(response.data) > 0:
                success = response.data[0].get("update_agno_analysis_tracking", False)
                if success:
                    logger.info(
                        f"Updated Agno stats for concept {concept_id} (WTP: {wtp_score})"
                    )
                    return True
                else:
                    logger.warning(
                        f"Failed to update Agno stats for concept {concept_id}"
                    )
                    return False
            else:
                logger.warning(
                    f"No response from update_agno_analysis_tracking for "
                    f"concept {concept_id}"
                )
                return False

        except Exception as e:
            logger.error(f"Error updating concept Agno stats for {concept_id}: {e}")
            self.stats["errors"] += 1
            return False

    def get_statistics(self) -> dict[str, int]:
        """
        Get deduplication statistics.

        Returns:
            dict: Statistics with keys:
                - skipped: Number of analyses skipped
                - fresh: Number of new analyses run
                - copied: Number of analyses copied
                - errors: Number of errors encountered

        Examples:
            >>> stats = skip_logic.get_statistics()
            >>> print(f"Saved {stats['skipped'] + stats['copied']} analyses")
        """
        return self.stats.copy()

    def copy_agno_analysis(
        self,
        submission: dict | None = None,
        concept_id: int | None = None,
        supabase=None,
        *,
        source_submission_id: str | None = None,
        target_submission_id: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Copy Agno analysis for deduplication pipeline integration.

        This method provides a unified interface for both the orchestrator
        (submission dict interface) and the original monolith pipeline
        (source/target ID interface).

        Args:
            submission: Current submission data (orchestrator interface)
            concept_id: Business concept ID with existing analysis
            supabase: Supabase client (optional, uses self.client if None)
            source_submission_id: Primary submission ID (original interface)
            target_submission_id: Target submission ID (original interface)

        Returns:
            dict: Copied analysis data, or None if copy failed
        """
        # Handle orchestrator interface (submission dict)
        if submission is not None and concept_id is not None:
            target_submission_id = submission.get("submission_id")
            if not target_submission_id:
                logger.error("No submission_id found in submission data")
                return None

            # Use provided client or fall back to instance client
            client = supabase if supabase is not None else self.client

            # Find primary analysis for this concept
            response = (
                client.table("llm_monetization_analysis")
                .select("*")
                .eq("business_concept_id", concept_id)
                .eq("copied_from_primary", False)
                .execute()
            )

            if not response.data:
                logger.warning(
                    f"No primary Agno analysis found for concept {concept_id}"
                )
                return None

            # Get the most recent primary analysis
            primary_analysis = max(
                response.data, key=lambda x: x.get("analyzed_at", "")
            )

            source_submission_id = primary_analysis.get("submission_id")

            # Create analysis data for orchestrator return (without inserting)
            copied_data = {
                "willingness_to_pay_score": primary_analysis.get(
                    "willingness_to_pay_score"
                ),
                "customer_segment": primary_analysis.get("customer_segment"),
                "payment_sentiment": primary_analysis.get("payment_sentiment"),
                "urgency_level": primary_analysis.get("urgency_level"),
                "mentioned_price_points": primary_analysis.get(
                    "mentioned_price_points"
                ),
                "existing_payment_behavior": primary_analysis.get(
                    "existing_payment_behavior"
                ),
                "payment_friction_indicators": primary_analysis.get(
                    "payment_friction_indicators"
                ),
                "confidence": primary_analysis.get("confidence"),
                "llm_monetization_score": primary_analysis.get(
                    "llm_monetization_score"
                ),
                "keyword_monetization_score": primary_analysis.get(
                    "keyword_monetization_score"
                ),
                "price_sensitivity_score": primary_analysis.get(
                    "price_sensitivity_score"
                ),
                "revenue_potential_score": primary_analysis.get(
                    "revenue_potential_score"
                ),
                "reasoning": primary_analysis.get("reasoning"),
                "subreddit_multiplier": primary_analysis.get("subreddit_multiplier"),
                "model_used": primary_analysis.get("model_used"),
                "score_delta": primary_analysis.get("score_delta"),
                # Tracking metadata
                "copied_from_primary": True,
                "primary_opportunity_id": primary_analysis.get("opportunity_id"),
                "copy_timestamp": datetime.now().isoformat(),
            }

            # Store copy in database for audit trail
            try:
                record_data = {
                    "opportunity_id": f"opp_{target_submission_id}",
                    "submission_id": target_submission_id,
                    "business_concept_id": concept_id,
                    **copied_data,
                }

                client.table("llm_monetization_analysis").insert(record_data).execute()

            except Exception as db_error:
                # Log warning but don't fail the copy operation
                logger.warning(f"Failed to store Agno copy in database: {db_error}")

            self.stats["copied"] += 1
            logger.info(
                f"Copied Agno analysis for concept {concept_id} to submission {target_submission_id}"
            )
            return copied_data

        # Handle original monolith interface (source/target IDs)
        elif source_submission_id and target_submission_id:
            return self._copy_agno_analysis_original(
                source_submission_id, target_submission_id, concept_id
            )

        else:
            logger.error("Invalid combination of arguments for copy_agno_analysis")
            return None

    def _copy_agno_analysis_original(
        self,
        source_submission_id: str,
        target_submission_id: str,
        concept_id: int,
    ) -> dict[str, Any] | None:
        """
        Original implementation of copy_agno_analysis.

        This method maintains compatibility with the original monolith pipeline
        interface while allowing the new unified interface to be supported.
        """
        try:
            # Fetch source analysis from llm_monetization_analysis table
            response = (
                self.client.table("llm_monetization_analysis")
                .select("*")
                .eq("business_concept_id", concept_id)
                .eq("copied_from_primary", False)  # Get original, not a copy
                .execute()
            )

            if not response.data:
                logger.warning(f"No Agno analysis found for concept {concept_id}")
                return None

            # Get the most recent analysis if multiple exist
            if len(response.data) == 1:
                source_analysis = response.data[0]
            else:
                source_analysis = max(
                    response.data, key=lambda x: x.get("analyzed_at", "")
                )

            # Create copied analysis with updated metadata
            copied_analysis = {
                "opportunity_id": f"opp_{target_submission_id}",
                "submission_id": target_submission_id,
                "llm_monetization_score": source_analysis.get("llm_monetization_score"),
                "keyword_monetization_score": source_analysis.get(
                    "keyword_monetization_score"
                ),
                "customer_segment": source_analysis.get("customer_segment"),
                "willingness_to_pay_score": source_analysis.get(
                    "willingness_to_pay_score"
                ),
                "price_sensitivity_score": source_analysis.get(
                    "price_sensitivity_score"
                ),
                "revenue_potential_score": source_analysis.get(
                    "revenue_potential_score"
                ),
                "payment_sentiment": source_analysis.get("payment_sentiment"),
                "urgency_level": source_analysis.get("urgency_level"),
                "existing_payment_behavior": source_analysis.get(
                    "existing_payment_behavior"
                ),
                "mentioned_price_points": source_analysis.get("mentioned_price_points"),
                "payment_friction_indicators": source_analysis.get(
                    "payment_friction_indicators"
                ),
                "confidence": source_analysis.get("confidence"),
                "reasoning": source_analysis.get("reasoning"),
                "subreddit_multiplier": source_analysis.get("subreddit_multiplier"),
                "model_used": source_analysis.get("model_used"),
                "score_delta": source_analysis.get("score_delta"),
                # Metadata for tracking
                "copied_from_primary": True,
                "primary_opportunity_id": source_analysis.get("opportunity_id"),
                "business_concept_id": concept_id,
                "copy_timestamp": datetime.now().isoformat(),
            }

            # Insert copied analysis
            response = (
                self.client.table("llm_monetization_analysis")
                .insert(copied_analysis)
                .execute()
            )

            if response.data:
                self.stats["copied"] += 1
                logger.info(
                    f"Copied Agno analysis from {source_submission_id} to "
                    f"{target_submission_id} for concept {concept_id}"
                )
                return response.data[0]

            logger.warning(
                f"Failed to insert copied Agno analysis for {target_submission_id}"
            )
            return None

        except Exception as e:
            logger.error(f"Error copying Agno analysis for concept {concept_id}: {e}")
            self.stats["errors"] += 1
            return None

    def reset_statistics(self) -> None:
        """
        Reset deduplication statistics to zero.

        Useful when reusing skip logic instance for multiple batches.

        Examples:
            >>> skip_logic.reset_statistics()
            >>> assert skip_logic.stats['skipped'] == 0
        """
        self.stats = {"skipped": 0, "fresh": 0, "copied": 0, "errors": 0}
