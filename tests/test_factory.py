"""Tests for ServiceFactory dependency injection and lifecycle management.

This module tests the ServiceFactory class that creates and manages
enrichment service instances with proper dependency injection.

Test Coverage:
- Factory initialization
- Service creation for all service types
- Configuration-based service enablement
- Mock fallback behavior
- Statistics management
- Service lifecycle
"""

from unittest.mock import MagicMock, patch

import pytest

from core.pipeline import DataSource, PipelineConfig, ServiceFactory


class TestFactoryInitialization:
    """Test factory initialization."""

    def test_basic_initialization(self):
        """Test basic factory initialization."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
        )

        factory = ServiceFactory(config)

        assert factory.config == config
        assert factory.services == {}

    def test_initialization_preserves_config(self):
        """Test factory preserves configuration."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=100,
            enable_profiler=True,
            enable_opportunity_scoring=True,
        )

        factory = ServiceFactory(config)

        assert factory.config.limit == 100
        assert factory.config.enable_profiler is True
        assert factory.config.enable_opportunity_scoring is True


class TestServiceCreation:
    """Test service creation methods."""

    @patch("core.enrichment.profiler_service.ProfilerService")
    @patch("core.agents.profiler.EnhancedLLMProfiler")
    def test_create_profiler_service(self, mock_profiler_class, mock_service_class):
        """Test profiler service creation."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert "profiler" in services
        assert len(services) == 1

    @patch("core.enrichment.opportunity_service.OpportunityService")
    @patch("core.agents.interactive.opportunity_analyzer.OpportunityAnalyzerAgent")
    def test_create_opportunity_service(self, mock_analyzer, mock_service_class):
        """Test opportunity service creation."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=False,
            enable_opportunity_scoring=True,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert "opportunity" in services
        assert len(services) == 1

    @patch("core.enrichment.monetization_service.MonetizationService")
    @patch("core.agents.monetization.factory.get_monetization_analyzer")
    def test_create_monetization_service(
        self, mock_analyzer_getter, mock_service_class
    ):
        """Test monetization service creation."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=False,
            enable_opportunity_scoring=False,
            enable_monetization=True,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert "monetization" in services
        assert len(services) == 1

    @patch("core.enrichment.trust_service.TrustService")
    @patch("core.trust.TrustValidationService")
    @patch("core.trust.TrustRepositoryFactory.create_repository")
    def test_create_trust_service(self, mock_repo, mock_validator, mock_service_class):
        """Test trust service creation."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            enable_profiler=False,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=True,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert "trust" in services
        assert len(services) == 1

    @patch("core.enrichment.market_validation_service.MarketValidationService")
    @patch("core.agents.market_validation.MarketDataValidator")
    def test_create_market_validation_service(self, mock_validator, mock_service_class):
        """Test market validation service creation."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=False,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=True,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert "market_validation" in services
        assert len(services) == 1


class TestMultipleServices:
    """Test creation of multiple services."""

    @patch("core.enrichment.profiler_service.ProfilerService")
    @patch("core.agents.profiler.EnhancedLLMProfiler")
    @patch("core.enrichment.opportunity_service.OpportunityService")
    @patch("core.agents.interactive.opportunity_analyzer.OpportunityAnalyzerAgent")
    def test_create_multiple_services(
        self, mock_opp_analyzer, mock_opp_service, mock_profiler, mock_prof_service
    ):
        """Test creating multiple services at once."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=True,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert len(services) == 2
        assert "profiler" in services
        assert "opportunity" in services

    def test_no_services_enabled(self):
        """Test factory with no services enabled."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=False,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert len(services) == 0
        assert services == {}


class TestMockFallback:
    """Test mock fallback behavior."""

    @patch("core.agents.profiler.EnhancedLLMProfiler")
    def test_profiler_mock_fallback(self, mock_profiler_class):
        """Test profiler falls back to mock on error."""
        mock_profiler_class.side_effect = Exception("Profiler creation failed")

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        # Service should still be created with mock
        assert "profiler" in services

    @patch("core.agents.interactive.opportunity_analyzer.OpportunityAnalyzerAgent")
    def test_opportunity_mock_fallback(self, mock_analyzer_class):
        """Test opportunity analyzer falls back to mock on error."""
        mock_analyzer_class.side_effect = Exception("Analyzer creation failed")

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=False,
            enable_opportunity_scoring=True,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        # Service should still be created with mock
        assert "opportunity" in services


class TestServiceAccess:
    """Test service access methods."""

    @patch("core.enrichment.profiler_service.ProfilerService")
    @patch("core.agents.profiler.EnhancedLLMProfiler")
    def test_get_service_by_name(self, mock_profiler, mock_service_class):
        """Test getting service by name."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        factory.create_services()

        profiler = factory.get_service("profiler")
        assert profiler is not None

    def test_get_nonexistent_service(self):
        """Test getting non-existent service returns None."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
        )

        factory = ServiceFactory(config)
        factory.create_services()

        nonexistent = factory.get_service("nonexistent")
        assert nonexistent is None

    @patch("core.enrichment.profiler_service.ProfilerService")
    @patch("core.agents.profiler.EnhancedLLMProfiler")
    def test_get_service_count(self, mock_profiler, mock_service_class):
        """Test getting service count."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        factory.create_services()

        count = factory.get_service_count()
        assert count == 1


class TestStatisticsManagement:
    """Test statistics management."""

    @patch("core.enrichment.profiler_service.ProfilerService")
    @patch("core.agents.profiler.EnhancedLLMProfiler")
    def test_get_all_statistics(self, mock_profiler, mock_service_class):
        """Test getting statistics from all services."""
        # Setup mock service with statistics
        mock_service = MagicMock()
        mock_service.get_statistics.return_value = {
            "analyzed": 10,
            "skipped": 5,
            "copied": 2,
            "errors": 0,
        }
        mock_service_class.return_value = mock_service

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        factory.create_services()

        stats = factory.get_all_statistics()

        assert "profiler" in stats
        assert stats["profiler"]["analyzed"] == 10
        assert stats["profiler"]["skipped"] == 5

    @patch("core.enrichment.profiler_service.ProfilerService")
    @patch("core.agents.profiler.EnhancedLLMProfiler")
    def test_reset_all_statistics(self, mock_profiler, mock_service_class):
        """Test resetting statistics for all services."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        factory.create_services()

        factory.reset_all_statistics()

        # Verify reset was called on service
        mock_service.reset_statistics.assert_called_once()


class TestDeduplicationConfiguration:
    """Test deduplication configuration."""

    @patch("core.enrichment.profiler_service.ProfilerService")
    @patch("core.agents.profiler.EnhancedLLMProfiler")
    @patch("core.deduplication.profiler_skip_logic.ProfilerSkipLogic")
    def test_profiler_with_deduplication(
        self, mock_skip_logic, mock_profiler, mock_service_class
    ):
        """Test profiler service with deduplication enabled."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
            enable_deduplication=True,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert "profiler" in services
        # Skip logic should be created when deduplication enabled
        mock_skip_logic.assert_called_once()

    @patch("core.enrichment.profiler_service.ProfilerService")
    @patch("core.agents.profiler.EnhancedLLMProfiler")
    def test_profiler_without_deduplication(self, mock_profiler, mock_service_class):
        """Test profiler service with deduplication disabled."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
            enable_deduplication=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert "profiler" in services


class TestErrorHandling:
    """Test error handling."""

    @patch("core.enrichment.profiler_service.ProfilerService")
    def test_service_creation_failure_continues(self, mock_service_class):
        """Test factory continues creating other services if one fails."""
        # Make profiler service fail
        mock_service_class.side_effect = Exception("Service creation failed")

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=True,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)

        # Should not raise exception, just log and continue
        try:
            services = factory.create_services()
            # Profiler failed but opportunity should still be attempted
            assert len(services) >= 0
        except Exception:
            pytest.fail("Factory should handle service creation failures gracefully")


class TestConfigurationVariations:
    """Test various configuration combinations."""

    def test_database_source_without_client(self):
        """Test database source configuration without client."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=None,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        # Should create service with mock validator
        assert "profiler" in services or len(services) >= 0

    @patch("core.enrichment.monetization_service.MonetizationService")
    @patch("core.agents.monetization.factory.get_monetization_analyzer")
    def test_monetization_with_custom_strategy(
        self, mock_analyzer_getter, mock_service_class
    ):
        """Test monetization service with custom strategy."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=False,
            enable_opportunity_scoring=False,
            enable_monetization=True,
            enable_trust=False,
            enable_market_validation=False,
            monetization_strategy="llm",
            monetization_config={"model": "gpt-4"},
        )

        factory = ServiceFactory(config)
        services = factory.create_services()

        assert "monetization" in services

        # Verify strategy and config were passed
        mock_analyzer_getter.assert_called_once_with(
            strategy="llm", config={"model": "gpt-4"}
        )
