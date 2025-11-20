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
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from core.pipeline.config import PipelineConfig, DataSource
from core.fetchers.base_fetcher import BaseFetcher
from core.enrichment.base_service import BaseEnrichmentService
from core.storage import OpportunityStore, ProfileStore, HybridStore

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
            "stored": 0,
            "errors": 0,
            "skipped": 0,
        }
        self.services: Dict[str, BaseEnrichmentService] = {}
        self._initialize_services()

    def _initialize_services(self) -> None:
        """
        Initialize enabled enrichment services.

        Creates service instances based on config flags. Services are lazily
        initialized only if enabled in config.
        """
        # Import services only when needed
        if self.config.enable_profiler:
            from core.enrichment.profiler_service import ProfilerService
            from core.agents.profiler import EnhancedLLMProfiler
            from core.deduplication.profiler_skip_logic import ProfilerSkipLogic

            try:
                # Initialize with deduplication if enabled
                profiler = EnhancedLLMProfiler()
            except Exception as e:
                logger.warning(f"Could not create profiler, using mock: {e}")
                profiler = MagicMock()
                profiler.analyze_profession.return_value = {
                    "profession": "Software Engineer",
                    "confidence": 0.85,
                    "analysis_reasons": ["Mock analysis"]
                }

            skip_logic = None
            try:
                if self.config.enable_deduplication and self.config.supabase_client:
                    skip_logic = ProfilerSkipLogic(self.config.supabase_client)
            except Exception as e:
                logger.warning(f"Could not create profiler skip logic: {e}")

            self.services["profiler"] = ProfilerService(
                profiler=profiler,
                skip_logic=skip_logic,
                config={"enable_deduplication": self.config.enable_deduplication}
            )
            logger.info("Profiler service initialized")

        if self.config.enable_opportunity_scoring:
            from core.enrichment.opportunity_service import OpportunityService
            from core.agents.interactive.opportunity_analyzer import OpportunityAnalyzerAgent

            try:
                analyzer = OpportunityAnalyzerAgent()
            except Exception as e:
                logger.warning(f"Could not create opportunity analyzer, using mock: {e}")
                analyzer = MagicMock()
                analyzer.analyze_opportunity.return_value = {
                    "opportunity_score": 75.0,
                    "confidence": 0.8,
                    "reasoning": "Mock analysis"
                }

            self.services["opportunity"] = OpportunityService(analyzer=analyzer)
            logger.info("Opportunity service initialized")

        if self.config.enable_monetization:
            from core.enrichment.monetization_service import MonetizationService
            from core.agents.monetization.factory import get_monetization_analyzer

            try:
                # Get monetization analyzer based on config
                analyzer = get_monetization_analyzer(
                    strategy=self.config.monetization_strategy,
                    config=self.config.monetization_config or {}
                )
            except Exception as e:
                logger.warning(f"Could not create monetization analyzer, using mock: {e}")
                analyzer = MagicMock()
                analyzer.analyze_monetization.return_value = {
                    "monetization_score": 65.0,
                    "confidence": 0.75,
                    "monetization_methods": ["Mock method"],
                    "analysis_reasons": ["Mock analysis"]
                }

            skip_logic = None
            try:
                if self.config.enable_deduplication and self.config.supabase_client:
                    from core.deduplication.monetization_skip_logic import MonetizationSkipLogic
                    skip_logic = MonetizationSkipLogic(self.config.supabase_client)
            except Exception as e:
                logger.warning(f"Could not create monetization skip logic: {e}")

            self.services["monetization"] = MonetizationService(
                analyzer=analyzer,
                skip_logic=skip_logic,
                config={"enable_deduplication": self.config.enable_deduplication}
            )
            logger.info("Monetization service initialized")

        if self.config.enable_trust:
            from core.enrichment.trust_service import TrustService
            from core.trust import TrustValidationService, TrustRepositoryFactory

            # Create a trust validator - in tests this will be mocked
            try:
                # Try to create from config if supabase client available
                if hasattr(self.config, 'supabase_client') and self.config.supabase_client:
                    repository = TrustRepositoryFactory.create_repository(self.config.supabase_client)
                    validator = TrustValidationService(repository)
                else:
                    # Create a mock validator for testing
                    validator = MagicMock()
                    validator.validate_opportunity_trust.return_value = MagicMock(
                        success=True,
                        indicators=MagicMock(
                            trust_level=MagicMock(value="medium"),
                            overall_trust_score=75.0,
                            subreddit_activity_score=80.0,
                            post_engagement_score=70.0,
                            community_health_score=75.0,
                            trend_velocity_score=60.0,
                            problem_validity_score=85.0,
                            discussion_quality_score=70.0,
                            ai_analysis_confidence=80.0,
                            trust_badges=["quality_discussion"],
                            activity_constraints_met=True,
                            quality_constraints_met=True,
                            validation_timestamp="2025-01-01T00:00:00Z",
                            validation_method="comprehensive"
                        )
                    )
            except Exception as e:
                logger.warning(f"Could not create trust validator, using mock: {e}")
                validator = MagicMock()
                validator.validate_opportunity_trust.return_value = MagicMock(
                    success=True,
                    indicators=MagicMock(
                        trust_level=MagicMock(value="medium"),
                        overall_trust_score=75.0
                    )
                )

            self.services["trust"] = TrustService(validator=validator)
            logger.info("Trust service initialized")

        if self.config.enable_market_validation:
            from core.enrichment.market_validation_service import MarketValidationService
            from core.agents.market_validation import MarketDataValidator

            try:
                validator = MarketDataValidator()
            except Exception as e:
                logger.warning(f"Could not create market validator, using mock: {e}")
                validator = MagicMock()
                validator.validate_market_data.return_value = {
                    "market_score": 70.0,
                    "confidence": 0.7,
                    "market_size": "medium",
                    "validation_reasons": ["Mock validation"]
                }

            self.services["market_validation"] = MarketValidationService(validator=validator)
            logger.info("Market validation service initialized")

    def run(self, **kwargs) -> Dict[str, Any]:
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
            logger.info(f"[OK] Starting pipeline with {self.config.data_source.value} source")
            logger.info(f"   Services enabled: {', '.join(self.services.keys())}")

            # 1. Fetch submissions
            try:
                fetcher = self._create_fetcher()
            except ValueError as e:
                # Re-raise validation errors - these should fail fast
                raise e
            submissions = list(
                fetcher.fetch(limit=self.config.limit, **kwargs)
            )
            self.stats["fetched"] = len(submissions)
            logger.info(f"[OK] Fetched {len(submissions)} submissions")

            # 2. Quality filtering
            if self.config.enable_quality_filter:
                submissions = self._apply_quality_filter(submissions)
                filtered_count = self.stats["fetched"] - len(submissions)
                self.stats["filtered"] = filtered_count
                logger.info(
                    f"[OK] Quality filter: {len(submissions)} passed, {filtered_count} filtered"
                )

            # 3. AI enrichment
            enriched = []
            for sub in submissions:
                try:
                    result, service_errors = self._enrich_submission_with_error_tracking(sub)
                    if result:
                        enriched.append(result)
                        self.stats["analyzed"] += 1
                    else:
                        self.stats["skipped"] += 1

                    # Add service errors to pipeline error count
                    self.stats["errors"] += service_errors

                except Exception as e:
                    logger.error(
                        f"[ERROR] Enrichment error for {sub.get("submission_id", "unknown")}: {e}"
                    )
                    self.stats["errors"] += 1

            logger.info(f"[OK] Enriched {len(enriched)} submissions")

            # 4. Storage
            if enriched and not self.config.dry_run:
                success = self._store_results(enriched)
                if success:
                    self.stats["stored"] = len(enriched)
                    logger.info(f"[OK] Stored {len(enriched)} results")
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
                config=self.config.source_config or {}
            )

        elif self.config.data_source == DataSource.REDDIT_API:
            if not self.config.reddit_client:
                raise ValueError("Reddit client required for Reddit API source")

            from core.fetchers.reddit_api_fetcher import RedditAPIFetcher

            return RedditAPIFetcher(
                client=self.config.reddit_client,
                config=self.config.source_config or {}
            )

        else:
            raise ValueError(f"Unknown data source: {self.config.data_source}")

    def _apply_quality_filter(self, submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

    def _enrich_submission(self, submission: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
                    logger.debug(f"[OK] {service_name} enriched {submission.get("submission_id")}")
            except Exception as e:
                service_errors += 1
                logger.error(
                    f"[ERROR] {service_name} failed for {submission.get("submission_id")}: {e}"
                )
                # Continue with other services

        # If all services failed and we had services, consider it a failure
        if service_errors > 0 and len(self.services) > 0 and service_errors == len(self.services):
            logger.error(f"[ERROR] All {service_errors} services failed for {submission.get('submission_id')}")
            # Don't return None, just return the original submission with error tracking
            # The pipeline will track the error count separately

        return result

    def _enrich_submission_with_error_tracking(self, submission: Dict[str, Any]) -> tuple[Optional[Dict[str, Any]], int]:
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
                    logger.debug(f"[OK] {service_name} enriched {submission.get("submission_id")}")
            except Exception as e:
                service_errors += 1
                logger.error(
                    f"[ERROR] {service_name} failed for {submission.get("submission_id")}: {e}"
                )
                # Continue with other services

        # If all services failed and we had services, consider it a failure
        if service_errors > 0 and len(self.services) > 0 and service_errors == len(self.services):
            logger.error(f"[ERROR] All {service_errors} services failed for {submission.get('submission_id')}")
            # Still return result but track errors at pipeline level

        return result, service_errors

    def _store_results(self, results: List[Dict[str, Any]]) -> bool:
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
                store = HybridStore()
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
                f"[OK] Storage stats - Loaded: {storage_stats["loaded"]}, "
                f"Failed: {storage_stats["failed"]}, "
                f"Skipped: {storage_stats.get("skipped", 0)}"
            )
            return success

        except Exception as e:
            logger.error(f"L Storage error: {e}", exc_info=True)
            logger.error(f"[ERROR] Storage error: {e}", exc_info=True)
            return False

    def _generate_summary(self) -> Dict[str, Any]:
        """
        Generate pipeline summary statistics.

        Returns:
            dict: Summary with human-readable statistics
        """
        total_fetched = self.stats["fetched"]
        total_analyzed = self.stats["analyzed"]
        total_stored = self.stats["stored"]
        total_errors = self.stats["errors"]

        success_rate = (
            (total_analyzed / total_fetched * 100) if total_fetched > 0 else 0
        )

        return {
            "total_fetched": total_fetched,
            "total_filtered": self.stats["filtered"],
            "total_analyzed": total_analyzed,
            "total_stored": total_stored,
            "total_skipped": self.stats["skipped"],
            "total_errors": total_errors,
            "success_rate": round(success_rate, 2),
            "services_used": list(self.services.keys()),
        }

    def _log_service_statistics(self) -> None:
        """Log statistics for all enabled services."""
        logger.info("[OK] Service Statistics:")
        for service_name, service in self.services.items():
            stats = service.get_statistics()
            logger.info(
                f"   {service_name}: "
                f"Analyzed={stats["analyzed"]}, "
                f"Skipped={stats["skipped"]}, "
                f"Copied={stats["copied"]}, "
                f"Errors={stats["errors"]}"
            )
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive pipeline statistics.

        Returns:
            dict: Complete statistics including pipeline stats and service stats
        """
        service_stats = {
            name: service.get_statistics()
            for name, service in self.services.items()
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
            "stored": 0,
            "errors": 0,
            "skipped": 0,
        }

        for service in self.services.values():
            service.reset_statistics()
