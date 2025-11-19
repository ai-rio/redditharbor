"""AI profiler deduplication logic.

This module provides AI profiler analysis deduplication to prevent redundant
analyses and preserve cost savings. Extracted from batch_opportunity_scoring.py
to enable reuse across pipelines.

Key Features:
- Check if profiler analysis should run
- Copy AI profiles from primary submissions
- Prevent semantic fragmentation of core_functions arrays
- Track deduplication statistics
- Update business concept metadata
"""

import logging
from datetime import datetime
from typing import Any, Optional

from core.deduplication.concept_manager import BusinessConceptManager

logger = logging.getLogger(__name__)


class ProfilerSkipLogic:
    """
    Handle AI profiler analysis deduplication.

    Manages the skip logic for AI profiler analyses by checking if a business
    concept already has a profile and copying it to duplicate submissions when
    possible. This prevents semantic fragmentation of core_functions arrays.

    Attributes:
        client: Initialized Supabase client
        concept_manager: BusinessConceptManager instance
        stats: Deduplication statistics tracking

    Examples:
        >>> from supabase import create_client
        >>> client = create_client(url, key)
        >>> skip_logic = ProfilerSkipLogic(client)
        >>> should_run, reason = skip_logic.should_run_profiler_analysis(
        ...     submission={'submission_id': 'sub123'},
        ...     business_concept_id=42
        ... )
        >>> if not should_run:
        ...     profile = skip_logic.copy_profiler_analysis('primary_id', 'sub123', 42)
    """

    def __init__(self, supabase_client: Any):
        """
        Initialize Profiler skip logic.

        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client
        self.concept_manager = BusinessConceptManager(supabase_client)
        self.stats = {"skipped": 0, "fresh": 0, "copied": 0, "errors": 0}

    def should_run_profiler_analysis(
        self,
        submission: dict[str, Any],
        business_concept_id: Optional[int] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if profiler analysis should run.

        Checks if the business concept already has an AI profile. If it does,
        skips analysis and returns False to trigger copying instead.

        Args:
            submission: Submission data dictionary
            business_concept_id: Optional concept ID (if None, treated as unique)

        Returns:
            tuple: (should_run, reason)
                - should_run: True if analysis should run, False if should skip
                - reason: String describing the decision

        Examples:
            >>> should_run, reason = skip_logic.should_run_profiler_analysis(
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
            # Check if concept already has AI profiler analysis
            concept = self.concept_manager.get_concept_by_id(business_concept_id)

            if concept and concept.get("has_ai_profiling"):
                self.stats["skipped"] += 1
                return (
                    False,
                    f"Concept {concept['id']} already has AI profiling",
                )

            self.stats["fresh"] += 1
            return True, "No existing AI profile found"

        except Exception as e:
            logger.error(
                f"Error checking profiler skip for submission "
                f"{submission.get('submission_id')}: {e}"
            )
            self.stats["errors"] += 1
            return True, "Error during check, running profiler as fallback"

    def copy_profiler_analysis(
        self,
        source_submission_id: str,
        target_submission_id: str,
        concept_id: int,
    ) -> Optional[dict[str, Any]]:
        """
        Copy AI profile from source to target submission.

        Retrieves the primary AI profile for a business concept and copies
        it to a new submission with updated metadata. This ensures consistent
        core_functions arrays across duplicate submissions.

        Args:
            source_submission_id: ID of primary submission with profile
            target_submission_id: ID of duplicate submission to copy to
            concept_id: Business concept ID linking the submissions

        Returns:
            dict: Copied profile data, or None if copy failed

        Examples:
            >>> profile = skip_logic.copy_profiler_analysis(
            ...     'primary_sub',
            ...     'duplicate_sub',
            ...     concept_id=42
            ... )
            >>> assert profile['copied_from_primary'] is True
            >>> assert 'core_functions' in profile
        """
        try:
            # Fetch source profile from workflow_results table
            response = (
                self.client.table("workflow_results")
                .select("*")
                .eq("business_concept_id", concept_id)
                .eq("copied_from_primary", False)  # Get original, not a copy
                .execute()
            )

            if not response.data:
                logger.warning(
                    f"No AI profile found for concept {concept_id}"
                )
                return None

            # Get the most recent profile if multiple exist
            if len(response.data) == 1:
                source_profile = response.data[0]
            else:
                source_profile = max(
                    response.data,
                    key=lambda x: x.get("processed_at", "")
                )

            # Create copied profile with updated metadata
            copied_profile = {
                "opportunity_id": f"opp_{target_submission_id}",
                "submission_id": target_submission_id,
                "app_name": source_profile.get("app_name"),
                "core_functions": source_profile.get("core_functions"),
                "value_proposition": source_profile.get("value_proposition"),
                "problem_description": source_profile.get("problem_description"),
                "app_concept": source_profile.get("app_concept"),
                "target_user": source_profile.get("target_user"),
                "monetization_model": source_profile.get("monetization_model"),
                "final_score": source_profile.get("final_score"),
                "market_demand": source_profile.get("market_demand"),
                "pain_intensity": source_profile.get("pain_intensity"),
                "monetization_potential": source_profile.get("monetization_potential"),
                "market_gap": source_profile.get("market_gap"),
                "technical_feasibility": source_profile.get("technical_feasibility"),
                # Metadata for tracking
                "copied_from_primary": True,
                "primary_opportunity_id": source_profile.get("opportunity_id"),
                "business_concept_id": concept_id,
                "copy_timestamp": datetime.now().isoformat(),
            }

            # Insert copied profile
            response = (
                self.client.table("workflow_results")
                .insert(copied_profile)
                .execute()
            )

            if response.data:
                self.stats["copied"] += 1
                logger.info(
                    f"Copied AI profile from {source_submission_id} to "
                    f"{target_submission_id} for concept {concept_id}"
                )
                return response.data[0]

            logger.warning(
                f"Failed to insert copied AI profile for {target_submission_id}"
            )
            return None

        except Exception as e:
            logger.error(
                f"Error copying AI profile for concept {concept_id}: {e}"
            )
            self.stats["errors"] += 1
            return None

    def update_concept_profiler_stats(
        self,
        concept_id: int,
        ai_profile: dict[str, Any],
    ) -> bool:
        """
        Update business concept with AI profile metadata.

        Calls database RPC function to update concept's has_ai_profiling flag
        and track profiler scores.

        Args:
            concept_id: Business concept ID to update
            ai_profile: Dictionary containing AI profile results

        Returns:
            bool: True if update succeeded, False otherwise

        Examples:
            >>> ai_profile = {'final_score': 82.5}
            >>> skip_logic.update_concept_profiler_stats(42, ai_profile)
            True
        """
        try:
            # Extract final score from AI profile
            profiler_score = ai_profile.get("final_score")
            if profiler_score is not None:
                profiler_score = float(profiler_score)

            # Call database function to update profiler tracking
            response = self.client.rpc(
                "update_profiler_analysis_tracking",
                {
                    "p_concept_id": int(concept_id),
                    "p_has_analysis": True,
                    "p_profiler_score": profiler_score,
                },
            ).execute()

            if response.data and len(response.data) > 0:
                success = response.data[0].get("update_profiler_analysis_tracking", False)
                if success:
                    logger.info(
                        f"Updated profiler stats for concept {concept_id} "
                        f"(Score: {profiler_score})"
                    )
                    return True
                else:
                    logger.warning(
                        f"Failed to update profiler stats for concept {concept_id}"
                    )
                    return False
            else:
                logger.warning(
                    f"No response from update_profiler_analysis_tracking for "
                    f"concept {concept_id}"
                )
                return False

        except Exception as e:
            logger.error(
                f"Error updating concept profiler stats for {concept_id}: {e}"
            )
            self.stats["errors"] += 1
            return False

    def get_statistics(self) -> dict[str, int]:
        """
        Get deduplication statistics.

        Returns:
            dict: Statistics with keys:
                - skipped: Number of profiles skipped
                - fresh: Number of new profiles generated
                - copied: Number of profiles copied
                - errors: Number of errors encountered

        Examples:
            >>> stats = skip_logic.get_statistics()
            >>> print(f"Saved {stats['skipped'] + stats['copied']} profiles")
        """
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """
        Reset deduplication statistics to zero.

        Useful when reusing skip logic instance for multiple batches.

        Examples:
            >>> skip_logic.reset_statistics()
            >>> assert skip_logic.stats['skipped'] == 0
        """
        self.stats = {"skipped": 0, "fresh": 0, "copied": 0, "errors": 0}
