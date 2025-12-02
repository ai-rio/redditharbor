"""Analysis Cache for Deduplication.

This module provides simplified caching layer for AI analysis results,
supporting the 70% cost reduction strategy through intelligent result reuse.

Purpose:
    Acts as an abstraction layer over the database for caching and retrieving
    expensive AI analysis results. Enables quick lookups and validation of
    existing analyses before making new AI calls.

Cached Analyses:
    1. Agno Monetization Analysis (~$0.10/call)
       - Willingness to pay scores
       - Customer segments
       - Payment sentiment indicators
       - Revenue potential metrics

    2. AI Profiler Results (~$0.005/call)
       - App names and concepts
       - Core functions arrays
       - Value propositions
       - Market opportunity scores

Architecture:
    The cache operates on business concept IDs as keys. Each concept groups
    semantically similar submissions, allowing analysis results to be shared
    across duplicates.

Usage Pattern:
    1. Check if concept has cached analysis
    2. If cached: retrieve and copy to new submission
    3. If not cached: run fresh analysis and cache result
    4. Update concept metadata to enable future cache hits

Integration:
    Works in conjunction with concept_tracker.py functions:
    - concept_tracker.should_run_*: Checks cache via has_*_analysis flags
    - concept_tracker.copy_*_from_primary: Uses this module's retrieval functions
    - concept_tracker.update_concept_*_stats: Enables future cache hits
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AnalysisCache:
    """
    Cache layer for expensive AI analysis results.

    Provides simple get/set/exists operations for both Agno monetization
    analysis and AI profiler results, keyed by business concept ID.

    Attributes:
        client: Initialized Supabase client
        agno_table: Table name for monetization analysis
        profiler_table: Table name for AI profiles
        concept_table: Table name for business concepts

    Examples:
        >>> cache = AnalysisCache(supabase_client)
        >>> if cache.has_agno_analysis(concept_id=42):
        ...     analysis = cache.get_agno_analysis(concept_id=42)
        ... else:
        ...     analysis = run_expensive_agno_analysis()
        ...     cache.set_agno_analysis(concept_id=42, analysis=analysis)
    """

    def __init__(self, supabase_client: Any):
        """
        Initialize analysis cache.

        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client
        self.agno_table = "llm_monetization_analysis"
        self.profiler_table = "workflow_results"
        self.concept_table = "business_concepts"

    def has_agno_analysis(self, concept_id: int) -> bool:
        """
        Check if concept has cached Agno monetization analysis.

        Fast boolean check using the has_agno_analysis flag on business_concepts.
        Avoids expensive table scans of llm_monetization_analysis.

        Args:
            concept_id: Business concept ID to check

        Returns:
            bool: True if analysis exists in cache, False otherwise

        Examples:
            >>> if cache.has_agno_analysis(42):
            ...     print("Analysis cached, can skip expensive AI call")
        """
        try:
            response = (
                self.client.table(self.concept_table)
                .select("has_agno_analysis")
                .eq("id", concept_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0].get("has_agno_analysis", False)

            return False

        except Exception as e:
            logger.error(f"Error checking Agno cache for concept {concept_id}: {e}")
            return False

    def get_agno_analysis(
        self, concept_id: int, primary_only: bool = True
    ) -> dict[str, Any] | None:
        """
        Retrieve cached Agno monetization analysis.

        Returns the most recent analysis for the given business concept.
        By default, only returns original analyses (not copies).

        Args:
            concept_id: Business concept ID to retrieve analysis for
            primary_only: If True, only return original analyses (default: True)

        Returns:
            dict[str, Any] | None: Analysis data with all fields, or None if not found

        Examples:
            >>> analysis = cache.get_agno_analysis(42)
            >>> if analysis:
            ...     wtp_score = analysis['willingness_to_pay_score']
            ...     logger.info(f"Retrieved cached WTP score: {wtp_score}")
        """
        try:
            query = (
                self.client.table(self.agno_table)
                .select("*")
                .eq("business_concept_id", concept_id)
            )

            if primary_only:
                query = query.eq("copied_from_primary", False)

            response = query.execute()

            if not response.data or len(response.data) == 0:
                return None

            # Return most recent analysis
            if len(response.data) == 1:
                return response.data[0]
            else:
                return max(response.data, key=lambda x: x.get("analyzed_at", ""))

        except Exception as e:
            logger.error(f"Error retrieving Agno analysis for concept {concept_id}: {e}")
            return None

    def has_profiler_analysis(self, concept_id: int) -> bool:
        """
        Check if concept has cached AI profiler analysis.

        Fast boolean check using the has_profiler_analysis flag on business_concepts.
        Avoids expensive table scans of workflow_results.

        Args:
            concept_id: Business concept ID to check

        Returns:
            bool: True if profile exists in cache, False otherwise

        Examples:
            >>> if cache.has_profiler_analysis(42):
            ...     print("Profile cached, can skip expensive AI profiling")
        """
        try:
            response = (
                self.client.table(self.concept_table)
                .select("has_profiler_analysis")
                .eq("id", concept_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0].get("has_profiler_analysis", False)

            return False

        except Exception as e:
            logger.error(
                f"Error checking profiler cache for concept {concept_id}: {e}"
            )
            return False

    def get_profiler_analysis(
        self, concept_id: int, primary_only: bool = True
    ) -> dict[str, Any] | None:
        """
        Retrieve cached AI profiler analysis.

        Returns the most recent profile for the given business concept.
        By default, only returns original profiles (not copies).

        Critical for maintaining consistent core_functions arrays across
        duplicate submissions.

        Args:
            concept_id: Business concept ID to retrieve profile for
            primary_only: If True, only return original profiles (default: True)

        Returns:
            dict[str, Any] | None: Profile data with all fields, or None if not found
                Includes: app_name, core_functions, value_proposition, etc.

        Examples:
            >>> profile = cache.get_profiler_analysis(42)
            >>> if profile:
            ...     core_funcs = profile['core_functions']
            ...     logger.info(f"Retrieved cached core functions: {core_funcs}")
        """
        try:
            query = (
                self.client.table(self.profiler_table)
                .select("*")
                .eq("business_concept_id", concept_id)
            )

            if primary_only:
                query = query.eq("copied_from_primary", False)

            response = query.execute()

            if not response.data or len(response.data) == 0:
                return None

            # Return most recent profile
            if len(response.data) == 1:
                return response.data[0]
            else:
                return max(response.data, key=lambda x: x.get("processed_at", ""))

        except Exception as e:
            logger.error(
                f"Error retrieving profiler analysis for concept {concept_id}: {e}"
            )
            return None

    def get_concept_metadata(self, concept_id: int) -> dict[str, Any] | None:
        """
        Retrieve business concept metadata.

        Returns complete concept record including analysis flags, submission counts,
        and related metadata.

        Args:
            concept_id: Business concept ID to retrieve

        Returns:
            dict[str, Any] | None: Concept data, or None if not found
                Includes: id, primary_submission_id, concept_text,
                has_agno_analysis, has_profiler_analysis, submission_count

        Examples:
            >>> concept = cache.get_concept_metadata(42)
            >>> if concept:
            ...     logger.info(f"Concept has {concept['submission_count']} submissions")
            ...     logger.info(f"Agno: {concept['has_agno_analysis']}")
            ...     logger.info(f"Profiler: {concept['has_profiler_analysis']}")
        """
        try:
            response = (
                self.client.table(self.concept_table)
                .select("*")
                .eq("id", concept_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error retrieving concept metadata for {concept_id}: {e}")
            return None
