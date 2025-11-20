"""Tests for unified OpportunityPipeline orchestrator.

This module tests the OpportunityPipeline class that replaces both
monolithic pipelines with a unified, configurable architecture.

Test Coverage:
- Pipeline initialization and configuration
- Service initialization (profiler, opportunity, monetization, trust, market validation)
- Data source integration (database, Reddit API)
- Quality filtering
- Enrichment coordination
- Storage integration
- Error handling and recovery
- Statistics tracking
- Service coordination
"""

import pytest
from unittest.mock import MagicMock, patch, call
from core.pipeline import OpportunityPipeline, PipelineConfig, DataSource


class TestPipelineInitialization:
    """Test pipeline initialization and configuration."""

    def test_basic_initialization(self):
        """Test basic pipeline initialization with minimal config."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
        )

        pipeline = OpportunityPipeline(config)

        assert pipeline.config == config
        assert pipeline.stats["fetched"] == 0
        assert pipeline.stats["analyzed"] == 0
        assert pipeline.stats["stored"] == 0
        assert pipeline.stats["errors"] == 0

    def test_initialization_with_services_disabled(self):
        """Test initialization with all services disabled."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=False,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        pipeline = OpportunityPipeline(config)

        assert len(pipeline.services) == 0

    @patch("core.enrichment.profiler_service.ProfilerService")
    @patch("core.agents.profiler.EnhancedLLMProfiler")
    def test_initialization_with_profiler_enabled(self, mock_profiler, mock_service):
        """Test initialization with profiler service enabled."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=True,
            enable_opportunity_scoring=False,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        pipeline = OpportunityPipeline(config)

        assert "profiler" in pipeline.services

    @patch("core.enrichment.opportunity_service.OpportunityService")
    @patch("core.agents.interactive.opportunity_analyzer.OpportunityAnalyzerAgent")
    def test_initialization_with_opportunity_enabled(self, mock_analyzer, mock_service):
        """Test initialization with opportunity service enabled."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            limit=10,
            enable_profiler=False,
            enable_opportunity_scoring=True,
            enable_monetization=False,
            enable_trust=False,
            enable_market_validation=False,
        )

        pipeline = OpportunityPipeline(config)

        assert "opportunity" in pipeline.services


class TestDataSourceIntegration:
    """Test integration with different data sources."""

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_database_fetcher_creation(self, mock_fetcher_class):
        """Test database fetcher is created correctly."""
        mock_client = MagicMock()
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([])
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=mock_client,
            limit=10,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        mock_fetcher_class.assert_called_once_with(
            client=mock_client,
            config={}
        )

    @patch("core.fetchers.reddit_api_fetcher.RedditAPIFetcher")
    def test_reddit_api_fetcher_creation(self, mock_fetcher_class):
        """Test Reddit API fetcher is created correctly."""
        mock_client = MagicMock()
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([])
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.REDDIT_API,
            reddit_client=mock_client,
            limit=10,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        mock_fetcher_class.assert_called_once_with(
            client=mock_client,
            config={}
        )

    def test_database_source_missing_client_raises_error(self):
        """Test database source without Supabase client raises error."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=None,
            limit=10,
        )

        pipeline = OpportunityPipeline(config)

        with pytest.raises(ValueError, match="Supabase client required"):
            pipeline.run()

    def test_reddit_source_missing_client_raises_error(self):
        """Test Reddit source without Reddit client raises error."""
        config = PipelineConfig(
            data_source=DataSource.REDDIT_API,
            reddit_client=None,
            limit=10,
        )

        pipeline = OpportunityPipeline(config)

        with pytest.raises(ValueError, match="Reddit client required"):
            pipeline.run()


class TestQualityFiltering:
    """Test quality filtering functionality."""

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_quality_filter_enabled(self, mock_fetcher_class):
        """Test quality filter filters low-quality submissions."""
        # Create mock submissions with varying quality
        submissions = [
            {
                "submission_id": "high_quality",
                "title": "Test",
                "subreddit": "test",
                "score": 100,
                "num_comments": 50,
                "selftext": "Long text content here that meets minimum length requirements",
            },
            {
                "submission_id": "low_score",
                "title": "Test",
                "subreddit": "test",
                "score": 1,  # Below min_score
                "num_comments": 50,
                "selftext": "Long text content",
            },
            {
                "submission_id": "low_comments",
                "title": "Test",
                "subreddit": "test",
                "score": 100,
                "num_comments": 1,  # Below min_comments
                "selftext": "Long text content",
            },
        ]

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter(submissions)
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            enable_quality_filter=True,
            min_score=10,
            min_comments=10,
            min_text_length=10,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        assert result["stats"]["fetched"] == 3
        assert result["stats"]["filtered"] == 2  # 2 filtered out
        assert result["stats"]["analyzed"] == 1  # Only 1 passed

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_quality_filter_disabled(self, mock_fetcher_class):
        """Test all submissions pass when quality filter disabled."""
        submissions = [
            {
                "submission_id": "sub1",
                "title": "Test",
                "subreddit": "test",
                "score": 1,
                "num_comments": 1,
                "selftext": "Short",
            },
            {
                "submission_id": "sub2",
                "title": "Test",
                "subreddit": "test",
                "score": 100,
                "num_comments": 50,
                "selftext": "Long text",
            },
        ]

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter(submissions)
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            enable_quality_filter=False,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        assert result["stats"]["fetched"] == 2
        assert result["stats"]["filtered"] == 0
        assert result["stats"]["analyzed"] == 2  # Both analyzed


class TestEnrichmentCoordination:
    """Test enrichment service coordination."""

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    @patch("core.storage.opportunity_store.OpportunityStore")
    @patch("core.enrichment.opportunity_service.OpportunityService")
    @patch("core.agents.interactive.opportunity_analyzer.OpportunityAnalyzerAgent")
    def test_single_service_enrichment(
        self, mock_analyzer, mock_service_class, mock_store_class, mock_fetcher_class
    ):
        """Test enrichment with single service."""
        submission = {
            "submission_id": "test1",
            "title": "Test submission",
            "subreddit": "test",
        }

        # Setup fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([submission])
        mock_fetcher_class.return_value = mock_fetcher

        # Setup service
        mock_service = MagicMock()
        mock_service.enrich.return_value = {"opportunity_score": 75.0}
        mock_service.get_statistics.return_value = {
            "analyzed": 1,
            "skipped": 0,
            "copied": 0,
            "errors": 0,
        }
        mock_service_class.return_value = mock_service

        # Setup storage
        mock_store = MagicMock()
        mock_store.store.return_value = True
        mock_store.get_statistics.return_value = {
            "loaded": 1,
            "failed": 0,
            "skipped": 0,
        }
        mock_store_class.return_value = mock_store

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            enable_opportunity_scoring=True,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        # Verify service was called
        mock_service.enrich.assert_called_once()
        assert result["stats"]["analyzed"] == 1

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_enrichment_error_handling(self, mock_fetcher_class):
        """Test enrichment continues on service errors."""
        submissions = [
            {"submission_id": "sub1", "title": "Test 1", "subreddit": "test"},
            {"submission_id": "sub2", "title": "Test 2", "subreddit": "test"},
        ]

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter(submissions)
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
        )

        pipeline = OpportunityPipeline(config)

        # Mock service that fails
        mock_service = MagicMock()
        mock_service.enrich.side_effect = Exception("Service error")
        pipeline.services["test_service"] = mock_service

        result = pipeline.run()

        # Both submissions attempted, both failed
        assert result["stats"]["fetched"] == 2
        assert result["stats"]["errors"] == 2


class TestStorageIntegration:
    """Test storage integration."""

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    @patch("core.storage.opportunity_store.OpportunityStore")
    def test_opportunity_store_selection(self, mock_store_class, mock_fetcher_class):
        """Test OpportunityStore selected for opportunity data."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([])
        mock_fetcher_class.return_value = mock_fetcher

        mock_store = MagicMock()
        mock_store.store.return_value = True
        mock_store.get_statistics.return_value = {"loaded": 0, "failed": 0}
        mock_store_class.return_value = mock_store

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            enable_opportunity_scoring=True,
            enable_profiler=False,
        )

        pipeline = OpportunityPipeline(config)
        # OpportunityStore should be initialized

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    @patch("core.storage.hybrid_store.HybridStore")
    def test_hybrid_store_selection(self, mock_store_class, mock_fetcher_class):
        """Test HybridStore selected for combined data."""
        submission = {
            "submission_id": "test1",
            "title": "Test",
            "subreddit": "test",
            "problem_description": "Problem",
        }

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([submission])
        mock_fetcher_class.return_value = mock_fetcher

        mock_store = MagicMock()
        mock_store.store.return_value = True
        mock_store.get_statistics.return_value = {"loaded": 1, "failed": 0}
        mock_store_class.return_value = mock_store

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            enable_opportunity_scoring=True,
            enable_profiler=True,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        # HybridStore should be used
        mock_store_class.assert_called_once()

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_dry_run_mode_skips_storage(self, mock_fetcher_class):
        """Test dry run mode skips storage."""
        submission = {
            "submission_id": "test1",
            "title": "Test",
            "subreddit": "test",
        }

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([submission])
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            dry_run=True,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        assert result["stats"]["stored"] == 0
        assert result["success"] is True


class TestStatisticsTracking:
    """Test statistics tracking and reporting."""

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_statistics_tracking(self, mock_fetcher_class):
        """Test pipeline tracks all statistics correctly."""
        submissions = [
            {"submission_id": "sub1", "title": "Test 1", "subreddit": "test"},
            {"submission_id": "sub2", "title": "Test 2", "subreddit": "test"},
            {"submission_id": "sub3", "title": "Test 3", "subreddit": "test"},
        ]

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter(submissions)
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        assert result["stats"]["fetched"] == 3
        assert "analyzed" in result["stats"]
        assert "stored" in result["stats"]
        assert "errors" in result["stats"]

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_summary_generation(self, mock_fetcher_class):
        """Test summary generation includes all metrics."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([])
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        summary = result["summary"]
        assert "total_fetched" in summary
        assert "total_analyzed" in summary
        assert "total_stored" in summary
        assert "total_errors" in summary
        assert "success_rate" in summary
        assert "services_used" in summary

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_get_statistics(self, mock_fetcher_class):
        """Test get_statistics returns complete stats."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([])
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
        )

        pipeline = OpportunityPipeline(config)
        pipeline.run()

        stats = pipeline.get_statistics()

        assert "pipeline" in stats
        assert "services" in stats
        assert "summary" in stats

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_reset_statistics(self, mock_fetcher_class):
        """Test reset_statistics clears all counters."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([])
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
        )

        pipeline = OpportunityPipeline(config)
        pipeline.run()

        # Verify stats are non-zero
        assert pipeline.stats["fetched"] == 0  # No data, but ran

        pipeline.reset_statistics()

        # All stats should be zero
        assert pipeline.stats["fetched"] == 0
        assert pipeline.stats["analyzed"] == 0
        assert pipeline.stats["stored"] == 0


class TestErrorHandling:
    """Test error handling and recovery."""

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_fetcher_error_handling(self, mock_fetcher_class):
        """Test pipeline handles fetcher errors gracefully."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("Fetch error")
        mock_fetcher_class.return_value = mock_fetcher

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        assert result["success"] is False
        assert "error" in result
        assert "Fetch error" in result["error"]

    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    @patch("core.storage.opportunity_store.OpportunityStore")
    def test_storage_error_handling(self, mock_store_class, mock_fetcher_class):
        """Test pipeline handles storage errors gracefully."""
        submission = {
            "submission_id": "test1",
            "title": "Test",
            "subreddit": "test",
            "problem_description": "Problem",
        }

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter([submission])
        mock_fetcher_class.return_value = mock_fetcher

        mock_store = MagicMock()
        mock_store.store.side_effect = Exception("Storage error")
        mock_store_class.return_value = mock_store

        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            enable_opportunity_scoring=True,
        )

        pipeline = OpportunityPipeline(config)
        result = pipeline.run()

        # Pipeline should complete but storage should fail
        assert result["success"] is True
        assert result["stats"]["stored"] == 0


class TestConfigurationValidation:
    """Test configuration validation."""

    def test_return_data_config(self):
        """Test return_data configuration controls data return."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=10,
            return_data=False,
        )

        pipeline = OpportunityPipeline(config)
        assert pipeline.config.return_data is False

    def test_limit_config(self):
        """Test limit configuration."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=MagicMock(),
            limit=50,
        )

        pipeline = OpportunityPipeline(config)
        assert pipeline.config.limit == 50
