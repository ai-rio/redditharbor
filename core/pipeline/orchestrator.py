"""Unified opportunity discovery pipeline orchestrator.

This module provides the OpportunityPipeline class that replaces both
monolithic pipelines (batch_opportunity_scoring.py and dlt_trust_pipeline.py)
with a unified, configurable architecture.

Key Features:
- Unified pipeline for both data sources (database, Reddit API)
- Integrate all enrichment services (profiler, opportunity, trust, market validation)
- Configurable service enablement (enable/disable any service)
- Comprehensive error handling and statistics tracking
- Storage using Phase 7 services (OpportunityStore, HybridStore)

Architecture:
    Config -> Fetcher -> Enrichment Services -> Storage

Example:
    >>> from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource
    >>>
    >>> config = PipelineConfig(
    ...     data_source=DataSource.DATABASE,
    ...     limit=100,
    ...     enable_profiler=True,
    ...     enable_opportunity_scoring=True
    ... )
    >>> pipeline = OpportunityPipeline(config)
    >>> result = pipeline.run()
    >>> print(f"Processed {result['stats']['analyzed']} submissions")
"""

import logging
from typing import Any

from core.enrichment.base_service import BaseEnrichmentService
from core.fetchers.base_fetcher import BaseFetcher
from core.pipeline.config import DataSource, PipelineConfig
from core.pipeline.factory import ServiceFactory
from core.storage import HybridStore, OpportunityStore, ProfileStore

logger = logging.getLogger(__name__)


class OpportunityPipeline:
    """
    Unified pipeline for opportunity discovery.

    Orchestrates the complete pipeline flow:
    1. Fetch submissions from configured data source
    2. Apply quality filtering (if enabled)
    3. Enrich with AI services (configurable)
    4. Store results using appropriate storage service
    5. Generate summary statistics

    Attributes:
        config: PipelineConfig with all settings
        stats: Dictionary tracking pipeline statistics
        services: Dictionary of initialized enrichment services

    Examples:
        >>> config = PipelineConfig(
        ...     data_source=DataSource.DATABASE,
        ...     limit=50,
        ...     enable_profiler=True,
        ...     enable_opportunity_scoring=True,
        ...     enable_trust=False
        ... )
        >>> pipeline = OpportunityPipeline(config)
        >>> result = pipeline.run()
        >>> assert result['success'] is True
        >>> assert result['stats']['fetched'] <= 50
    """

    def __init__(self, config: PipelineConfig):
        """
        Initialize OpportunityPipeline.

        Args:
            config: PipelineConfig instance with all pipeline settings
        """
        self.config = config
        self.stats = {
            "fetched": 0,
            "filtered": 0,
            "analyzed": 0,
            "copied": 0,  # NEW: Track copied submissions (deduplication)
            "stored": 0,
            "errors": 0,
            "skipped": 0,
        }
        self.services: dict[str, BaseEnrichmentService] = {}
        self._initialize_services()

    def _initialize_services(self) -> None:
        """
        Initialize enabled enrichment services using ServiceFactory.

        Delegates service creation to ServiceFactory for cleaner separation
        of concerns and better dependency management.
        """
        factory = ServiceFactory(self.config)
        self.services = factory.create_services()
        logger.info(f"Initialized {len(self.services)} services via ServiceFactory")

    def run(self, **kwargs) -> dict[str, Any]:
        """
        Execute complete pipeline.

        Orchestrates the full pipeline flow from fetching to storage.
        All kwargs are passed to the fetcher's fetch() method.

        Args:
            **kwargs: Additional parameters passed to fetcher (e.g., subreddit filters)

        Returns:
            dict: Pipeline results with keys:
                - success (bool): Whether pipeline completed successfully
                - stats (dict): Processing statistics
                - summary (dict): Human-readable summary
                - opportunities (list): Enriched submissions (if requested)

        Examples:
            >>> pipeline = OpportunityPipeline(config)
            >>> result = pipeline.run(min_score=50)
            >>> print(result['summary']['success_rate'])
        """
        try:
            logger.info(
                f"[OK] Starting pipeline with {self.config.data_source.value} source"
            )
            logger.info(f"   Services enabled: {', '.join(self.services.keys())}")

            # 1. Fetch submissions
            try:
                fetcher = self._create_fetcher()
            except ValueError as e:
                # Re-raise validation errors - these should fail fast
                raise e
            submissions = list(fetcher.fetch(limit=self.config.limit, **kwargs))
            self.stats["fetched"] = len(submissions)
            logger.info(f"[OK] Fetched {len(submissions)} submissions")

            # 2. Quality filtering
            if self.config.enable_quality_filter:
                submissions = self._apply_quality_filter(submissions)
                filtered_count = self.stats["fetched"] - len(submissions)
                self.stats["filtered"] = filtered_count
                logger.info(
                    f"[OK] Quality filter: {len(submissions)} passed, "
                    f"{filtered_count} filtered"
                )

            # 3. AI enrichment with deduplication
            enriched = []

            # DEDUPLICATION: Batch-fetch concept metadata (2 queries total)
            concept_metadata = {}
            if self.config.supabase_client:
                concept_metadata = self._batch_fetch_concept_metadata(submissions)
                logger.info(
                    f"[OK] Deduplication check: {len(concept_metadata)} concepts found"
                )

            for sub in submissions:
                try:
                    sub_id = sub.get("submission_id")
                    metadata = concept_metadata.get(sub_id, {})

                    # DEDUPLICATION: Check if we can copy existing analysis
                    should_copy = False
                    if metadata:
                        # Check if either Agno or Profiler has existing analysis
                        has_agno = metadata.get("has_agno", False)
                        has_profiler = metadata.get("has_profiler", False)

                        # Copy if ANY required service has existing analysis
                        should_copy = (
                            self.config.enable_monetization and has_agno
                        ) or (self.config.enable_profiler and has_profiler)

                    if should_copy:
                        # COPY: Reuse existing analysis ($0 cost)
                        result = self._copy_existing_enrichment(
                            sub, metadata["concept_id"]
                        )
                        if result:
                            enriched.append(result)
                            self.stats["copied"] += 1
                            logger.debug(
                                f"[OK] Copied analysis for {sub_id} "
                                f"(concept: {metadata['concept_id']})"
                            )
                        else:
                            # Copy failed - fall back to fresh analysis
                            logger.warning(
                                f"[WARN] Copy failed for {sub_id}, "
                                "running fresh analysis"
                            )
                            result, service_errors = (
                                self._enrich_submission_with_error_tracking(sub)
                            )
                            if result:
                                enriched.append(result)
                                self.stats["analyzed"] += 1
                            else:
                                self.stats["skipped"] += 1
                            self.stats["errors"] += service_errors
                    else:
                        # ANALYZE: Run fresh AI analysis ($0.075 cost)
                        result, service_errors = (
                            self._enrich_submission_with_error_tracking(sub)
                        )
                        if result:
                            enriched.append(result)
                            self.stats["analyzed"] += 1
                        else:
                            self.stats["skipped"] += 1

                        # Add service errors to pipeline error count
                        self.stats["errors"] += service_errors

                except Exception as e:
                    sub_id = sub.get("submission_id", "unknown")
                    logger.error(f"[ERROR] Enrichment error for {sub_id}: {e}")
                    self.stats["errors"] += 1

            logger.info(
                f"[OK] Enriched {len(enriched)} submissions "
                f"(analyzed: {self.stats['analyzed']}, copied: {self.stats['copied']})"
            )

            # 4. Storage
            if enriched and not self.config.dry_run:
                success = self._store_results(enriched)
                if success:
                    self.stats["stored"] = len(enriched)
                    logger.info(f"[OK] Stored {len(enriched)} results")

                    # ⭐ PHASE 3: Update concept metadata for future deduplication
                    self._update_concept_metadata(enriched)
            elif self.config.dry_run:
                logger.info("[OK] Dry run mode - skipping storage")
                self.stats["stored"] = 0

            # 5. Generate summary
            summary = self._generate_summary()

            # 6. Log service statistics
            self._log_service_statistics()

            return {
                "success": True,
                "stats": self.stats,
                "summary": summary,
                "opportunities": enriched if self.config.return_data else [],
            }

        except Exception as e:
            logger.error(f"[ERROR] Pipeline error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "stats": self.stats,
                "summary": self._generate_summary(),
            }

    def _create_fetcher(self) -> BaseFetcher:
        """
        Create appropriate fetcher based on config.

        Returns:
            BaseFetcher: Initialized fetcher instance

        Raises:
            ValueError: If data source is unknown or required client is missing
        """
        if self.config.data_source == DataSource.DATABASE:
            if not self.config.supabase_client:
                raise ValueError("Supabase client required for database source")

            from core.fetchers.database_fetcher import DatabaseFetcher

            return DatabaseFetcher(
                client=self.config.supabase_client,
                config=self.config.source_config or {},
            )

        elif self.config.data_source == DataSource.REDDIT_API:
            if not self.config.reddit_client:
                raise ValueError("Reddit client required for Reddit API source")

            from core.fetchers.reddit_api_fetcher import RedditAPIFetcher

            return RedditAPIFetcher(
                client=self.config.reddit_client, config=self.config.source_config or {}
            )

        else:
            raise ValueError(f"Unknown data source: {self.config.data_source}")

    def _apply_quality_filter(
        self, submissions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Apply quality thresholds to filter submissions.

        Filters based on minimum score, comment count, and text length
        defined in config.

        Args:
            submissions: List of submission dictionaries

        Returns:
            list: Filtered submissions meeting quality criteria
        """
        filtered = []
        for sub in submissions:
            # Check minimum score
            if sub.get("score", 0) < self.config.min_score:
                continue

            # Check minimum comments
            if sub.get("num_comments", 0) < self.config.min_comments:
                continue

            # Check minimum text length
            text = sub.get("selftext", "") or sub.get("text", "")
            if len(text) < self.config.min_text_length:
                continue

            filtered.append(sub)

        return filtered

    def _batch_fetch_concept_metadata(
        self, submissions: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """
        Batch-fetch concept metadata for all submissions.

        Reduces N*3 queries to 2 batch queries total, improving performance
        by ~75x for deduplication checks.

        Args:
            submissions: List of submission dictionaries

        Returns:
            dict: submission_id → {concept_id, has_agno, has_profiler}
        """
        if not self.config.supabase_client:
            logger.warning("No Supabase client - skipping concept metadata fetch")
            return {}

        submission_ids = [
            s.get("submission_id") for s in submissions if s.get("submission_id")
        ]

        if not submission_ids:
            return {}

        try:
            # Batch Query 1: Get all concept_ids at once
            concepts_response = (
                self.config.supabase_client.table("opportunities_unified")
                .select("submission_id, business_concept_id")
                .in_("submission_id", submission_ids)
                .execute()
            )

            # Build submission → concept mapping
            submission_to_concept = {
                row["submission_id"]: row["business_concept_id"]
                for row in concepts_response.data
                if row.get("business_concept_id")
            }

            # Batch Query 2: Get analysis flags for all concepts at once
            concept_ids = list(set(submission_to_concept.values()))
            if not concept_ids:
                return {}

            flags_response = (
                self.config.supabase_client.table("business_concepts")
                .select("id, has_agno_analysis, has_profiler_analysis")
                .in_("id", concept_ids)
                .execute()
            )

            # Build concept → flags mapping
            concept_flags = {
                row["id"]: {
                    "has_agno": row.get("has_agno_analysis", False),
                    "has_profiler": row.get("has_profiler_analysis", False),
                }
                for row in flags_response.data
            }

            # Combine mappings
            metadata = {}
            for sub_id, concept_id in submission_to_concept.items():
                flags = concept_flags.get(
                    concept_id, {"has_agno": False, "has_profiler": False}
                )
                metadata[sub_id] = {"concept_id": concept_id, **flags}

            logger.info(
                f"[OK] Batch-fetched metadata for {len(metadata)} submissions "
                f"(2 queries vs {len(submission_ids) * 3} queries)"
            )
            return metadata

        except Exception as e:
            logger.error(f"[ERROR] Failed to batch-fetch concept metadata: {e}")
            return {}

    def _enrich_submission(self, submission: dict[str, Any]) -> dict[str, Any] | None:
        """
        Apply all enabled enrichment services.

        Enriches submission with all enabled services. Each service adds
        its analysis fields to the result dictionary.

        Args:
            submission: Submission data dictionary

        Returns:
            dict: Enriched submission with all service results, or None if
                enrichment fails
        """
        result = {**submission}  # Copy original data
        service_errors = 0

        # Apply each enabled service
        for service_name, service in self.services.items():
            try:
                enrichment = service.enrich(submission)
                if enrichment:
                    result.update(enrichment)
                    sub_id = submission.get("submission_id")
                    logger.debug(f"[OK] {service_name} enriched {sub_id}")
            except Exception as e:
                service_errors += 1
                sub_id = submission.get("submission_id")
                logger.error(f"[ERROR] {service_name} failed for {sub_id}: {e}")
                # Continue with other services

        # If all services failed and we had services, consider it a failure
        if (
            service_errors > 0
            and len(self.services) > 0
            and service_errors == len(self.services)
        ):
            sub_id = submission.get("submission_id")
            logger.error(
                f"[ERROR] All {service_errors} services failed for {sub_id}"
            )
            # Don't return None, just return the original submission with error tracking
            # The pipeline will track the error count separately

        return result

    def _enrich_submission_with_error_tracking(
        self, submission: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, int]:
        """
        Apply all enabled enrichment services with error tracking.

        Enriches submission with all enabled services. Each service adds
        its analysis fields to the result dictionary. Returns both the result
        and the count of service errors.

        Args:
            submission: Submission data dictionary

        Returns:
            tuple: (enriched_submission or None, service_error_count)
        """
        result = {**submission}  # Copy original data
        service_errors = 0

        # Apply each enabled service
        for service_name, service in self.services.items():
            try:
                enrichment = service.enrich(submission)
                if enrichment:
                    result.update(enrichment)
                    sub_id = submission.get("submission_id")
                    logger.debug(f"[OK] {service_name} enriched {sub_id}")
            except Exception as e:
                service_errors += 1
                sub_id = submission.get("submission_id")
                logger.error(f"[ERROR] {service_name} failed for {sub_id}: {e}")
                # Continue with other services

        # If all services failed and we had services, consider it a failure
        if (
            service_errors > 0
            and len(self.services) > 0
            and service_errors == len(self.services)
        ):
            sub_id = submission.get("submission_id")
            logger.error(
                f"[ERROR] All {service_errors} services failed for {sub_id}"
            )
            # Still return result but track errors at pipeline level

        return result, service_errors

    def _copy_existing_enrichment(
        self, submission: dict[str, Any], concept_id: str
    ) -> dict[str, Any] | None:
        """
        Copy existing enrichment with evidence flow preservation.

        CRITICAL: Agno → Profiler dependency requires copying in order.
        Profiler uses Agno evidence to inform app_concept generation.

        Args:
            submission: Submission data
            concept_id: Business concept ID with existing analysis

        Returns:
            Enriched submission with copied data, or None if copy fails
        """
        result = {**submission}  # Start with original
        copy_success = False

        # STEP 1: Copy Agno analysis FIRST (generates evidence)
        agno_evidence = None
        if self.config.enable_monetization and "monetization" in self.services:
            try:
                from core.deduplication import AgnoSkipLogic

                skip_logic = AgnoSkipLogic(self.config.supabase_client)

                # Copy Agno analysis using unified API signature
                agno_data = skip_logic.copy_agno_analysis(
                    submission=submission,
                    concept_id=concept_id,
                    supabase=self.config.supabase_client,
                )

                if agno_data:
                    result.update(agno_data)
                    copy_success = True

                    # Extract evidence structure for profiler
                    agno_evidence = {
                        "willingness_to_pay_score": agno_data.get(
                            "willingness_to_pay_score"
                        ),
                        "customer_segment": agno_data.get("customer_segment"),
                        "sentiment_toward_payment": agno_data.get("payment_sentiment"),
                        "urgency_level": agno_data.get("urgency_level"),
                        "mentioned_price_points": agno_data.get(
                            "mentioned_price_points"
                        ),
                        "existing_payment_behavior": agno_data.get(
                            "existing_payment_behavior"
                        ),
                        "payment_friction_indicators": agno_data.get(
                            "payment_friction_indicators"
                        ),
                        "confidence": agno_data.get("confidence"),
                    }
                    logger.info(
                        f"[OK] Copied Agno analysis + extracted evidence for "
                        f"{submission.get('submission_id')}"
                    )
                else:
                    logger.warning(
                        "[WARN] Failed to copy Agno - "
                        "profiler will run without evidence"
                    )
            except Exception as e:
                logger.error(f"[ERROR] Agno copy failed: {e}")

        # STEP 2: Copy Profiler analysis SECOND (uses evidence if available)
        if self.config.enable_profiler and "profiler" in self.services:
            try:
                from core.deduplication import ProfilerSkipLogic

                skip_logic = ProfilerSkipLogic(self.config.supabase_client)

                # Copy profiler analysis using monolith API signature
                profiler_data = skip_logic.copy_profiler_analysis(
                    submission=submission,
                    concept_id=concept_id,
                    supabase=self.config.supabase_client,
                )

                if profiler_data:
                    result.update(profiler_data)
                    copy_success = True
                    # Store evidence reference for audit trail
                    result["profiler_evidence_source"] = (
                        "copied_agno" if agno_evidence else "none"
                    )
                    logger.info(
                        f"[OK] Copied profiler analysis for "
                        f"{submission.get('submission_id')}"
                    )
                else:
                    logger.warning(
                        f"[WARN] Failed to copy profiler analysis "
                        f"for concept {concept_id}"
                    )
            except Exception as e:
                logger.error(f"[ERROR] Profiler copy failed: {e}")

        # Return result only if at least one service was copied successfully
        if copy_success:
            return result
        else:
            logger.warning(
                f"[WARN] No enrichment copied for {submission.get('submission_id')} "
                f"- falling back to fresh analysis"
            )
            return None

    def _update_concept_metadata(self, enriched: list[dict[str, Any]]) -> None:
        """
        Update concept metadata after successful enrichment.

        Marks concepts as analyzed (has_agno_analysis, has_profiler_analysis)
        so future runs can skip expensive AI calls through deduplication.

        Uses batch query optimization to reduce database load.

        Args:
            enriched: List of successfully enriched and stored submissions

        Example:
            >>> enriched = [{"submission_id": "sub_001", "ai_profile": {...}}]
            >>> pipeline._update_concept_metadata(enriched)
        """
        if not self.config.supabase_client:
            logger.debug("No Supabase client - skipping concept metadata updates")
            return

        if not enriched:
            return

        try:
            # BATCH: Fetch all concept_ids at once (1 query instead of N)
            submission_ids = [
                sub.get("submission_id") for sub in enriched if sub.get("submission_id")
            ]

            if not submission_ids:
                logger.debug("No submission IDs found for concept metadata update")
                return

            concepts_response = (
                self.config.supabase_client.table("opportunities_unified")
                .select("submission_id, business_concept_id")
                .in_("submission_id", submission_ids)
                .execute()
            )

            # Build submission_id → concept_id mapping
            submission_to_concept = {
                row["submission_id"]: row["business_concept_id"]
                for row in concepts_response.data
                if row.get("business_concept_id")
            }

            if not submission_to_concept:
                logger.debug("No concepts found for metadata update")
                return

            # Track statistics
            profiler_updates = 0
            agno_updates = 0
            failed_updates = 0

            # Update Profiler metadata for submissions with AI profiles
            if self.config.enable_profiler:
                from core.deduplication import ProfilerSkipLogic

                skip_logic = ProfilerSkipLogic(self.config.supabase_client)

                for submission in enriched:
                    # Check if submission has profiler analysis
                    if submission.get("ai_profile") or submission.get("app_name"):
                        sub_id = submission.get("submission_id")
                        concept_id = submission_to_concept.get(sub_id)

                        if concept_id:
                            # Prepare ai_profile dict for update
                            ai_profile = submission.get("ai_profile", {})
                            if not ai_profile and submission.get("app_name"):
                                # Build minimal ai_profile if only app_name exists
                                ai_profile = {
                                    "app_name": submission.get("app_name"),
                                    "final_score": submission.get(
                                        "opportunity_score", 0
                                    ),
                                }

                            success = skip_logic.update_concept_profiler_stats(
                                concept_id=concept_id, ai_profile=ai_profile
                            )

                            if success:
                                profiler_updates += 1
                            else:
                                failed_updates += 1

            # Update Agno metadata for submissions with monetization analysis
            if self.config.enable_monetization:
                from core.deduplication import AgnoSkipLogic

                skip_logic = AgnoSkipLogic(self.config.supabase_client)

                for submission in enriched:
                    # Check if submission has Agno analysis
                    if submission.get("willingness_to_pay_score") or submission.get(
                        "monetization_score"
                    ):
                        sub_id = submission.get("submission_id")
                        concept_id = submission_to_concept.get(sub_id)

                        if concept_id:
                            # Prepare agno_result dict for update
                            agno_result = {
                                "willingness_to_pay_score": submission.get(
                                    "willingness_to_pay_score"
                                )
                                or submission.get("monetization_score"),
                                "customer_segment": submission.get("customer_segment"),
                                "payment_sentiment": submission.get(
                                    "payment_sentiment"
                                ),
                                "urgency_level": submission.get("urgency_level"),
                            }

                            success = skip_logic.update_concept_agno_stats(
                                concept_id=concept_id, agno_result=agno_result
                            )

                            if success:
                                agno_updates += 1
                            else:
                                failed_updates += 1

            # Log summary
            if profiler_updates > 0 or agno_updates > 0:
                logger.info(
                    f"[OK] Updated concept metadata: "
                    f"Profiler={profiler_updates}, Agno={agno_updates}, "
                    f"Failed={failed_updates}"
                )
            else:
                logger.debug("No concept metadata updates performed")

        except Exception as e:
            logger.error(f"[ERROR] Failed to update concept metadata: {e}")
            # Don't raise - metadata updates are best-effort

    def _store_results(self, results: list[dict[str, Any]]) -> bool:
        """
        Store results using appropriate storage service.

        Determines storage strategy based on enrichment types and uses
        the appropriate storage service (OpportunityStore, ProfileStore,
        or HybridStore).

        Args:
            results: List of enriched submission dictionaries

        Returns:
            bool: True if storage succeeded, False otherwise
        """
        try:
            # Determine storage strategy based on enabled services
            has_opportunity = self.config.enable_opportunity_scoring
            has_profile = self.config.enable_profiler or self.config.enable_trust

            if has_opportunity and has_profile:
                # Use HybridStore for both opportunity and profile data
                # PHASE 2: Pass supabase_client for trust data preservation
                store = HybridStore(supabase_client=self.config.supabase_client)
                logger.info("Using HybridStore for combined data")
            elif has_opportunity:
                # Use OpportunityStore for opportunity data only
                store = OpportunityStore()
                logger.info("Using OpportunityStore for opportunity data")
            else:
                # Use ProfileStore for profile data only
                store = ProfileStore()
                logger.info("Using ProfileStore for profile data")

            success = store.store(results)

            # Log storage statistics
            storage_stats = store.get_statistics()
            logger.info(
                f"[OK] Storage stats - Loaded: {storage_stats['loaded']}, "
                f"Failed: {storage_stats['failed']}, "
                f"Skipped: {storage_stats.get('skipped', 0)}"
            )
            return success

        except Exception as e:
            logger.error(f"L Storage error: {e}", exc_info=True)
            logger.error(f"[ERROR] Storage error: {e}", exc_info=True)
            return False

    def _generate_summary(self) -> dict[str, Any]:
        """
        Generate pipeline summary statistics.

        Returns:
            dict: Summary with human-readable statistics including deduplication metrics
        """
        total_fetched = self.stats["fetched"]
        total_analyzed = self.stats["analyzed"]
        total_copied = self.stats["copied"]
        total_processed = total_analyzed + total_copied
        total_stored = self.stats["stored"]
        total_errors = self.stats["errors"]

        success_rate = (
            (total_processed / total_fetched * 100) if total_fetched > 0 else 0
        )

        # Calculate deduplication metrics
        dedup_rate = (
            (total_copied / total_processed * 100) if total_processed > 0 else 0
        )
        cost_saved = total_copied * 0.075  # $0.075 per copied submission

        return {
            "total_fetched": total_fetched,
            "total_filtered": self.stats["filtered"],
            "total_analyzed": total_analyzed,
            "total_copied": total_copied,  # NEW: Deduplication metric
            "total_processed": total_processed,  # NEW: Total (analyzed + copied)
            "total_stored": total_stored,
            "total_skipped": self.stats["skipped"],
            "total_errors": total_errors,
            "success_rate": round(success_rate, 2),
            "dedup_rate": round(dedup_rate, 2),  # NEW: Deduplication percentage
            "cost_saved": round(cost_saved, 2),  # NEW: Cost savings in dollars
            "services_used": list(self.services.keys()),
        }

    def _log_service_statistics(self) -> None:
        """Log statistics for all enabled services."""
        logger.info("[OK] Service Statistics:")
        for service_name, service in self.services.items():
            stats = service.get_statistics()
            logger.info(
                f"   {service_name}: "
                f"Analyzed={stats['analyzed']}, "
                f"Skipped={stats['skipped']}, "
                f"Copied={stats['copied']}, "
                f"Errors={stats['errors']}"
            )

    def get_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive pipeline statistics.

        Returns:
            dict: Complete statistics including pipeline stats and service stats
        """
        service_stats = {
            name: service.get_statistics() for name, service in self.services.items()
        }

        return {
            "pipeline": self.stats.copy(),
            "services": service_stats,
            "summary": self._generate_summary(),
        }

    def reset_statistics(self) -> None:
        """
        Reset all pipeline and service statistics.

        Useful when reusing pipeline instance for multiple runs.
        """
        self.stats = {
            "fetched": 0,
            "filtered": 0,
            "analyzed": 0,
            "copied": 0,  # NEW: Reset deduplication counter
            "stored": 0,
            "errors": 0,
            "skipped": 0,
        }

        for service in self.services.values():
            service.reset_statistics()
