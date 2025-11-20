"""Service factory for dependency injection and lifecycle management.

This module provides the ServiceFactory class for creating and managing
enrichment service instances. Handles service initialization, configuration,
and lifecycle management with proper dependency injection.

Key Features:
- Centralized service creation with proper dependency injection
- Lazy initialization for efficiency
- Mock fallback for missing dependencies
- Service lifecycle management (create, reset, cleanup)
- Configuration-based service enablement

Example:
    >>> from core.pipeline import PipelineConfig, DataSource
    >>> from core.pipeline.factory import ServiceFactory
    >>>
    >>> config = PipelineConfig(
    ...     data_source=DataSource.DATABASE,
    ...     enable_profiler=True,
    ...     enable_opportunity_scoring=True
    ... )
    >>> factory = ServiceFactory(config)
    >>> services = factory.create_services()
    >>> print(f"Created {len(services)} services")
"""

import logging
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

# Add project root to sys.path to resolve config imports
# Insert at position 1 (after test utils) to ensure main config takes precedence
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(1, str(project_root))

from core.enrichment.base_service import BaseEnrichmentService
from core.pipeline.config import PipelineConfig

logger = logging.getLogger(__name__)


class ServiceFactory:
    """
    Factory for creating and managing enrichment services.

    Provides centralized service creation with dependency injection,
    configuration management, and lifecycle handling. Automatically
    handles missing dependencies with mock fallbacks.

    Attributes:
        config: PipelineConfig with service configuration
        services: Dictionary of created service instances

    Examples:
        >>> config = PipelineConfig(
        ...     data_source=DataSource.DATABASE,
        ...     enable_profiler=True
        ... )
        >>> factory = ServiceFactory(config)
        >>> services = factory.create_services()
        >>> assert "profiler" in services
    """

    def __init__(self, config: PipelineConfig):
        """
        Initialize ServiceFactory.

        Args:
            config: PipelineConfig instance with service settings
        """
        self.config = config
        self.services: dict[str, BaseEnrichmentService] = {}

    def create_services(self) -> dict[str, BaseEnrichmentService]:
        """
        Create all enabled enrichment services.

        Creates service instances based on config flags. Services are
        only created if enabled in config. Handles missing dependencies
        gracefully with mock fallbacks.

        Returns:
            dict: Dictionary mapping service names to service instances

        Examples:
            >>> factory = ServiceFactory(config)
            >>> services = factory.create_services()
            >>> for name, service in services.items():
            ...     print(f"Created: {name}")
        """
        services = {}

        if self.config.enable_profiler:
            profiler_service = self._create_profiler_service()
            if profiler_service:
                services["profiler"] = profiler_service

        if self.config.enable_opportunity_scoring:
            opportunity_service = self._create_opportunity_service()
            if opportunity_service:
                services["opportunity"] = opportunity_service

        if self.config.enable_monetization:
            monetization_service = self._create_monetization_service()
            if monetization_service:
                services["monetization"] = monetization_service

        if self.config.enable_trust:
            trust_service = self._create_trust_service()
            if trust_service:
                services["trust"] = trust_service

        if self.config.enable_market_validation:
            market_service = self._create_market_validation_service()
            if market_service:
                services["market_validation"] = market_service

        self.services = services
        logger.info(f"ServiceFactory created {len(services)} services")
        return services

    def _create_profiler_service(self) -> BaseEnrichmentService | None:
        """
        Create ProfilerService with deduplication support.

        Returns:
            ProfilerService instance or None if creation fails
        """
        try:
            # Temporarily ensure project root is first in path for correct config imports
            original_path = sys.path[:]
            project_root = str(Path(__file__).parent.parent.parent)

            # Move project root to front temporarily
            if project_root in sys.path:
                sys.path.remove(project_root)
            sys.path.insert(0, project_root)

            # Clear any cached config modules to force reimport
            config_modules_to_clear = [k for k in sys.modules.keys() if k.startswith('config')]
            for module in config_modules_to_clear:
                del sys.modules[module]

            try:
                from core.agents.profiler import EnhancedLLMProfiler
                from core.deduplication.profiler_skip_logic import ProfilerSkipLogic
                from core.enrichment.profiler_service import ProfilerService
            finally:
                # Restore original path
                sys.path[:] = original_path

            # Create profiler
            try:
                profiler = EnhancedLLMProfiler()
            except Exception as e:
                logger.warning(f"Could not create profiler, using mock: {e}")
                profiler = self._create_mock_profiler()

            # Create skip logic if deduplication enabled
            skip_logic = None
            if self.config.enable_deduplication and self.config.supabase_client:
                try:
                    skip_logic = ProfilerSkipLogic(self.config.supabase_client)
                except Exception as e:
                    logger.warning(f"Could not create profiler skip logic: {e}")

            service = ProfilerService(
                profiler=profiler,
                skip_logic=skip_logic,
                config={"enable_deduplication": self.config.enable_deduplication},
            )
            logger.info(" Profiler service created")
            return service

        except Exception as e:
            logger.error(f"Failed to create profiler service: {e}")
            return None

    def _create_opportunity_service(self) -> BaseEnrichmentService | None:
        """
        Create OpportunityService for opportunity analysis.

        Returns:
            OpportunityService instance or None if creation fails
        """
        try:
            # Temporarily ensure project root is first in path for correct config imports
            original_path = sys.path[:]
            project_root = str(Path(__file__).parent.parent.parent)

            # Move project root to front temporarily
            if project_root in sys.path:
                sys.path.remove(project_root)
            sys.path.insert(0, project_root)

            try:
                from core.agents.interactive.opportunity_analyzer import (
                    OpportunityAnalyzerAgent,
                )
                from core.enrichment.opportunity_service import OpportunityService
            finally:
                # Restore original path
                sys.path[:] = original_path

            # Create analyzer
            try:
                analyzer = OpportunityAnalyzerAgent()
            except Exception as e:
                logger.warning(
                    f"Could not create opportunity analyzer, using mock: {e}"
                )
                analyzer = self._create_mock_opportunity_analyzer()

            service = OpportunityService(analyzer=analyzer)
            logger.info(" Opportunity service created")
            return service

        except Exception as e:
            logger.error(f"Failed to create opportunity service: {e}")
            return None

    def _create_monetization_service(self) -> BaseEnrichmentService | None:
        """
        Create MonetizationService with strategy-based analyzer.

        Returns:
            MonetizationService instance or None if creation fails
        """
        try:
            # Temporarily ensure project root is first in path for correct config imports
            original_path = sys.path[:]
            project_root = str(Path(__file__).parent.parent.parent)

            # Move project root to front temporarily
            if project_root in sys.path:
                sys.path.remove(project_root)
            sys.path.insert(0, project_root)

            try:
                from core.agents.monetization.factory import get_monetization_analyzer
                from core.enrichment.monetization_service import MonetizationService
            finally:
                # Restore original path
                sys.path[:] = original_path

            # Create analyzer based on strategy
            try:
                analyzer = get_monetization_analyzer(
                    strategy=self.config.monetization_strategy,
                    config=self.config.monetization_config or {},
                )
            except Exception as e:
                logger.warning(
                    f"Could not create monetization analyzer, using mock: {e}"
                )
                analyzer = self._create_mock_monetization_analyzer()

            # Create skip logic if deduplication enabled
            skip_logic = None
            if self.config.enable_deduplication and self.config.supabase_client:
                try:
                    from core.deduplication.monetization_skip_logic import (
                        MonetizationSkipLogic,
                    )

                    skip_logic = MonetizationSkipLogic(self.config.supabase_client)
                    logger.info("Monetization skip logic created")
                except ImportError:
                    logger.info(
                        "Monetization skip logic not available, proceeding without"
                    )
                except Exception as e:
                    logger.warning(f"Could not create monetization skip logic: {e}")

            service = MonetizationService(
                analyzer=analyzer,
                skip_logic=skip_logic,
                config={"enable_deduplication": self.config.enable_deduplication},
            )
            logger.info(" Monetization service created")
            return service

        except Exception as e:
            logger.error(f"Failed to create monetization service: {e}")
            return None

    def _create_trust_service(self) -> BaseEnrichmentService | None:
        """
        Create TrustService for trust validation.

        Returns:
            TrustService instance or None if creation fails
        """
        try:
            from core.enrichment.trust_service import TrustService
            from core.trust import TrustRepositoryFactory, TrustValidationService

            # Create validator
            validator = None
            try:
                if self.config.supabase_client:
                    repository = TrustRepositoryFactory.create_repository(
                        self.config.supabase_client
                    )
                    validator = TrustValidationService(repository)
                else:
                    validator = self._create_mock_trust_validator()
            except Exception as e:
                logger.warning(f"Could not create trust validator, using mock: {e}")
                validator = self._create_mock_trust_validator()

            service = TrustService(validator=validator)
            logger.info(" Trust service created")
            return service

        except Exception as e:
            logger.error(f"Failed to create trust service: {e}")
            return None

    def _create_market_validation_service(self) -> BaseEnrichmentService | None:
        """
        Create MarketValidationService for market data validation.

        Returns:
            MarketValidationService instance or None if creation fails
        """
        try:
            # Temporarily ensure project root is first in path for correct config imports
            original_path = sys.path[:]
            project_root = str(Path(__file__).parent.parent.parent)

            # Move project root to front temporarily
            if project_root in sys.path:
                sys.path.remove(project_root)
            sys.path.insert(0, project_root)

            try:
                from core.agents.market_validation import MarketDataValidator
                from core.enrichment.market_validation_service import (
                    MarketValidationService,
                )
            finally:
                # Restore original path
                sys.path[:] = original_path

            # Create validator
            try:
                validator = MarketDataValidator()
            except Exception as e:
                logger.warning(f"Could not create market validator, using mock: {e}")
                validator = self._create_mock_market_validator()

            service = MarketValidationService(validator=validator)
            logger.info(" Market validation service created")
            return service

        except Exception as e:
            logger.error(f"Failed to create market validation service: {e}")
            return None

    # Mock creation methods
    def _create_mock_profiler(self) -> Any:
        """Create mock profiler for testing."""
        profiler = MagicMock()
        profiler.analyze_profession.return_value = {
            "profession": "Software Engineer",
            "confidence": 0.85,
            "analysis_reasons": ["Mock analysis"],
        }
        return profiler

    def _create_mock_opportunity_analyzer(self) -> Any:
        """Create mock opportunity analyzer for testing."""
        analyzer = MagicMock()
        analyzer.analyze_opportunity.return_value = {
            "opportunity_score": 75.0,
            "confidence": 0.8,
            "reasoning": "Mock analysis",
        }
        return analyzer

    def _create_mock_monetization_analyzer(self) -> Any:
        """Create mock monetization analyzer for testing."""
        analyzer = MagicMock()
        analyzer.analyze_monetization.return_value = {
            "monetization_score": 65.0,
            "confidence": 0.75,
            "monetization_methods": ["Mock method"],
            "analysis_reasons": ["Mock analysis"],
        }
        return analyzer

    def _create_mock_trust_validator(self) -> Any:
        """Create mock trust validator for testing."""
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
                validation_method="comprehensive",
            ),
        )
        return validator

    def _create_mock_market_validator(self) -> Any:
        """Create mock market validator for testing."""
        from dataclasses import dataclass, field
        from datetime import UTC, datetime

        # Create mock ValidationEvidence to match real validator interface
        @dataclass
        class MockValidationEvidence:
            competitor_pricing: list = field(default_factory=list)
            market_size: Any = None
            similar_launches: list = field(default_factory=list)
            validation_score: float = 70.0
            data_quality_score: float = 75.0
            reasoning: str = "Mock market validation"
            urls_fetched: list = field(default_factory=lambda: ["http://example.com"])
            total_cost: float = 0.0

        validator = MagicMock()
        validator.validate_opportunity.return_value = MockValidationEvidence()
        return validator

    def get_service(self, name: str) -> BaseEnrichmentService | None:
        """
        Get service by name.

        Args:
            name: Service name (e.g., "profiler", "opportunity")

        Returns:
            Service instance or None if not found

        Examples:
            >>> factory = ServiceFactory(config)
            >>> factory.create_services()
            >>> profiler = factory.get_service("profiler")
        """
        return self.services.get(name)

    def reset_all_statistics(self) -> None:
        """
        Reset statistics for all created services.

        Examples:
            >>> factory.reset_all_statistics()
        """
        for service in self.services.values():
            service.reset_statistics()
        logger.info("Reset statistics for all services")

    def get_all_statistics(self) -> dict[str, dict[str, int]]:
        """
        Get statistics from all services.

        Returns:
            dict: Dictionary mapping service names to their statistics

        Examples:
            >>> stats = factory.get_all_statistics()
            >>> print(stats["profiler"]["analyzed"])
        """
        return {
            name: service.get_statistics() for name, service in self.services.items()
        }

    def get_service_count(self) -> int:
        """
        Get count of created services.

        Returns:
            int: Number of services created

        Examples:
            >>> count = factory.get_service_count()
            >>> print(f"Created {count} services")
        """
        return len(self.services)
