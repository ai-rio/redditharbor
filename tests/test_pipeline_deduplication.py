"""Test unified pipeline deduplication logic.

This test suite validates the deduplication integration in Phase 1,
ensuring that existing enrichment is copied instead of re-analyzed.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.pipeline import DataSource, OpportunityPipeline, PipelineConfig


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    client = MagicMock()
    return client


@pytest.fixture
def basic_config(mock_supabase):
    """Create basic pipeline config with deduplication enabled."""
    return PipelineConfig(
        data_source=DataSource.DATABASE,
        limit=10,
        enable_profiler=True,
        enable_monetization=True,
        supabase_client=mock_supabase,
        dry_run=True,  # Don't actually store during tests
    )


@pytest.fixture
def sample_submissions():
    """Sample submissions for testing."""
    return [
        {
            "submission_id": "sub_001",
            "title": "Test Submission 1",
            "selftext": "This is a test submission with enough text for quality filters.",
            "score": 100,
            "num_comments": 50,
        },
        {
            "submission_id": "sub_002",
            "title": "Test Submission 2",
            "selftext": "Another test submission with different content and good engagement.",
            "score": 150,
            "num_comments": 75,
        },
    ]


class TestBatchFetchConceptMetadata:
    """Test batch fetching of concept metadata for deduplication."""

    def test_batch_fetch_with_existing_concepts(self, basic_config, sample_submissions):
        """Test that batch fetch retrieves concept metadata correctly."""
        pipeline = OpportunityPipeline(basic_config)

        # Mock opportunities_unified response
        basic_config.supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value.data = [
            {"submission_id": "sub_001", "business_concept_id": "concept_123"},
            {"submission_id": "sub_002", "business_concept_id": "concept_456"},
        ]

        # Mock business_concepts response
        mock_table_chain = basic_config.supabase_client.table.return_value
        mock_select_chain = mock_table_chain.select.return_value
        mock_in_chain = mock_select_chain.in_.return_value

        # First call: opportunities_unified
        # Second call: business_concepts
        mock_in_chain.execute.side_effect = [
            MagicMock(
                data=[
                    {"submission_id": "sub_001", "business_concept_id": "concept_123"},
                    {"submission_id": "sub_002", "business_concept_id": "concept_456"},
                ]
            ),
            MagicMock(
                data=[
                    {
                        "id": "concept_123",
                        "has_agno_analysis": True,
                        "has_profiler_analysis": True,
                    },
                    {
                        "id": "concept_456",
                        "has_agno_analysis": False,
                        "has_profiler_analysis": True,
                    },
                ]
            ),
        ]

        metadata = pipeline._batch_fetch_concept_metadata(sample_submissions)

        assert len(metadata) == 2
        assert metadata["sub_001"]["concept_id"] == "concept_123"
        assert metadata["sub_001"]["has_agno"] is True
        assert metadata["sub_001"]["has_profiler"] is True
        assert metadata["sub_002"]["concept_id"] == "concept_456"
        assert metadata["sub_002"]["has_agno"] is False
        assert metadata["sub_002"]["has_profiler"] is True

    def test_batch_fetch_with_no_concepts(self, basic_config, sample_submissions):
        """Test batch fetch when no concepts exist."""
        pipeline = OpportunityPipeline(basic_config)

        # Mock empty response
        basic_config.supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []

        metadata = pipeline._batch_fetch_concept_metadata(sample_submissions)

        assert metadata == {}

    def test_batch_fetch_without_supabase_client(self, sample_submissions):
        """Test batch fetch gracefully handles missing Supabase client."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            supabase_client=None,  # No client
        )
        pipeline = OpportunityPipeline(config)

        metadata = pipeline._batch_fetch_concept_metadata(sample_submissions)

        assert metadata == {}

    def test_batch_fetch_with_database_error(self, basic_config, sample_submissions):
        """Test batch fetch handles database errors gracefully."""
        pipeline = OpportunityPipeline(basic_config)

        # Mock database error
        basic_config.supabase_client.table.return_value.select.return_value.in_.return_value.execute.side_effect = Exception(
            "Database connection failed"
        )

        metadata = pipeline._batch_fetch_concept_metadata(sample_submissions)

        # Should return empty dict on error, not crash
        assert metadata == {}


class TestCopyExistingEnrichment:
    """Test copying existing enrichment with evidence chaining."""

    @patch("core.deduplication.AgnoSkipLogic")
    @patch("core.deduplication.ProfilerSkipLogic")
    def test_copy_both_services_success(
        self, mock_profiler_skip, mock_agno_skip, basic_config, sample_submissions
    ):
        """Test successful copy of both Agno and Profiler analysis."""
        pipeline = OpportunityPipeline(basic_config)

        # Mock Agno copy
        mock_agno_instance = MagicMock()
        mock_agno_instance.copy_agno_analysis.return_value = {
            "willingness_to_pay_score": 85,
            "customer_segment": "B2B SaaS",
            "payment_sentiment": "positive",
            "urgency_level": "high",
        }
        mock_agno_skip.return_value = mock_agno_instance

        # Mock Profiler copy
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.copy_profiler_analysis.return_value = {
            "app_name": "Test App",
            "core_functions": '["feature1", "feature2"]',
        }
        mock_profiler_skip.return_value = mock_profiler_instance

        result = pipeline._copy_existing_enrichment(
            sample_submissions[0], "concept_123"
        )

        assert result is not None
        assert result["willingness_to_pay_score"] == 85
        assert result["customer_segment"] == "B2B SaaS"
        assert result["app_name"] == "Test App"
        assert result["profiler_evidence_source"] == "copied_agno"

    @patch("core.deduplication.AgnoSkipLogic")
    def test_copy_agno_only(self, mock_agno_skip, sample_submissions):
        """Test copy with only Agno enabled."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            enable_monetization=True,
            enable_profiler=False,  # Disabled
            supabase_client=MagicMock(),
        )
        pipeline = OpportunityPipeline(config)

        # Mock Agno copy
        mock_agno_instance = MagicMock()
        mock_agno_instance.copy_agno_analysis.return_value = {
            "willingness_to_pay_score": 75,
        }
        mock_agno_skip.return_value = mock_agno_instance

        result = pipeline._copy_existing_enrichment(
            sample_submissions[0], "concept_123"
        )

        assert result is not None
        assert result["willingness_to_pay_score"] == 75
        assert "profiler_evidence_source" not in result

    @patch("core.deduplication.ProfilerSkipLogic")
    def test_copy_profiler_only(self, mock_profiler_skip, sample_submissions):
        """Test copy with only Profiler enabled."""
        config = PipelineConfig(
            data_source=DataSource.DATABASE,
            enable_monetization=False,  # Disabled
            enable_profiler=True,
            supabase_client=MagicMock(),
        )
        pipeline = OpportunityPipeline(config)

        # Mock Profiler copy
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.copy_profiler_analysis.return_value = {
            "app_name": "Test App",
        }
        mock_profiler_skip.return_value = mock_profiler_instance

        result = pipeline._copy_existing_enrichment(
            sample_submissions[0], "concept_123"
        )

        assert result is not None
        assert result["app_name"] == "Test App"
        assert result["profiler_evidence_source"] == "none"

    @patch("core.deduplication.AgnoSkipLogic")
    @patch("core.deduplication.ProfilerSkipLogic")
    def test_copy_failure_returns_none(
        self, mock_profiler_skip, mock_agno_skip, basic_config, sample_submissions
    ):
        """Test that failed copy returns None for fallback."""
        pipeline = OpportunityPipeline(basic_config)

        # Mock both copies failing
        mock_agno_instance = MagicMock()
        mock_agno_instance.copy_agno_analysis.return_value = None
        mock_agno_skip.return_value = mock_agno_instance

        mock_profiler_instance = MagicMock()
        mock_profiler_instance.copy_profiler_analysis.return_value = None
        mock_profiler_skip.return_value = mock_profiler_instance

        result = pipeline._copy_existing_enrichment(
            sample_submissions[0], "concept_123"
        )

        assert result is None


class TestDeduplicationStatistics:
    """Test deduplication statistics tracking."""

    def test_stats_include_copied_field(self, basic_config):
        """Test that stats dict includes 'copied' field."""
        pipeline = OpportunityPipeline(basic_config)

        assert "copied" in pipeline.stats
        assert pipeline.stats["copied"] == 0

    def test_summary_includes_dedup_metrics(self, basic_config):
        """Test that summary includes deduplication metrics."""
        pipeline = OpportunityPipeline(basic_config)

        # Simulate some processing
        pipeline.stats["fetched"] = 100
        pipeline.stats["analyzed"] = 30
        pipeline.stats["copied"] = 70

        summary = pipeline._generate_summary()

        assert "total_copied" in summary
        assert "total_processed" in summary
        assert "dedup_rate" in summary
        assert "cost_saved" in summary

        assert summary["total_copied"] == 70
        assert summary["total_processed"] == 100  # analyzed + copied
        assert summary["dedup_rate"] == 70.0  # 70 of 100
        assert summary["cost_saved"] == 5.25  # 70 * $0.075

    def test_cost_savings_calculation(self, basic_config):
        """Test cost savings calculation is correct."""
        pipeline = OpportunityPipeline(basic_config)

        test_cases = [
            (0, 0.0),
            (10, 0.75),
            (50, 3.75),
            (100, 7.5),
        ]

        for copied_count, expected_savings in test_cases:
            pipeline.stats["copied"] = copied_count
            summary = pipeline._generate_summary()
            assert summary["cost_saved"] == expected_savings

    def test_reset_statistics_includes_copied(self, basic_config):
        """Test that reset_statistics resets copied counter."""
        pipeline = OpportunityPipeline(basic_config)

        # Set some stats
        pipeline.stats["copied"] = 50

        # Reset
        pipeline.reset_statistics()

        assert pipeline.stats["copied"] == 0


class TestDeduplicationIntegration:
    """Integration tests for deduplication in full pipeline."""

    @patch("core.pipeline.orchestrator.ServiceFactory")
    @patch("core.fetchers.database_fetcher.DatabaseFetcher")
    def test_pipeline_uses_deduplication(
        self, mock_fetcher_class, mock_factory_class, basic_config, sample_submissions
    ):
        """Test that pipeline uses deduplication during run."""
        # Mock fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = iter(sample_submissions)
        mock_fetcher_class.return_value = mock_fetcher

        # Mock services
        mock_factory = MagicMock()
        mock_factory.create_services.return_value = {}
        mock_factory_class.return_value = mock_factory

        # Mock batch fetch to return existing concepts
        with patch.object(
            OpportunityPipeline, "_batch_fetch_concept_metadata"
        ) as mock_batch_fetch:
            mock_batch_fetch.return_value = {
                "sub_001": {
                    "concept_id": "concept_123",
                    "has_agno": True,
                    "has_profiler": True,
                },
            }

            # Mock copy method
            with patch.object(
                OpportunityPipeline, "_copy_existing_enrichment"
            ) as mock_copy:
                mock_copy.return_value = {**sample_submissions[0], "copied": True}

                pipeline = OpportunityPipeline(basic_config)
                pipeline.run()

                # Verify batch fetch was called
                assert mock_batch_fetch.called

                # Verify copy was attempted for sub_001
                assert mock_copy.called

    def test_dedup_rate_calculation_edge_cases(self, basic_config):
        """Test dedup rate calculation with edge cases."""
        pipeline = OpportunityPipeline(basic_config)

        # Case 1: No processing
        pipeline.stats["analyzed"] = 0
        pipeline.stats["copied"] = 0
        summary = pipeline._generate_summary()
        assert summary["dedup_rate"] == 0

        # Case 2: 100% deduplication
        pipeline.stats["analyzed"] = 0
        pipeline.stats["copied"] = 100
        summary = pipeline._generate_summary()
        assert summary["dedup_rate"] == 100.0

        # Case 3: 0% deduplication
        pipeline.stats["analyzed"] = 100
        pipeline.stats["copied"] = 0
        summary = pipeline._generate_summary()
        assert summary["dedup_rate"] == 0.0

        # Case 4: 50% deduplication
        pipeline.stats["analyzed"] = 50
        pipeline.stats["copied"] = 50
        summary = pipeline._generate_summary()
        assert summary["dedup_rate"] == 50.0


class TestEvidenceChaining:
    """Test evidence chaining from Agno to Profiler."""

    @patch("core.deduplication.AgnoSkipLogic")
    @patch("core.deduplication.ProfilerSkipLogic")
    def test_agno_executes_before_profiler(
        self, mock_profiler_skip, mock_agno_skip, basic_config, sample_submissions
    ):
        """Test that Agno copy executes before Profiler copy."""
        pipeline = OpportunityPipeline(basic_config)

        call_order = []

        # Track call order
        def agno_copy(*args, **kwargs):
            call_order.append("agno")
            return {"willingness_to_pay_score": 85}

        def profiler_copy(*args, **kwargs):
            call_order.append("profiler")
            return {"app_name": "Test"}

        mock_agno_instance = MagicMock()
        mock_agno_instance.copy_agno_analysis.side_effect = agno_copy
        mock_agno_skip.return_value = mock_agno_instance

        mock_profiler_instance = MagicMock()
        mock_profiler_instance.copy_profiler_analysis.side_effect = profiler_copy
        mock_profiler_skip.return_value = mock_profiler_instance

        pipeline._copy_existing_enrichment(sample_submissions[0], "concept_123")

        # Verify execution order
        assert call_order == ["agno", "profiler"]

    @patch("core.deduplication.AgnoSkipLogic")
    @patch("core.deduplication.ProfilerSkipLogic")
    def test_evidence_extraction_from_agno(
        self, mock_profiler_skip, mock_agno_skip, basic_config, sample_submissions
    ):
        """Test that evidence is extracted from Agno for Profiler."""
        pipeline = OpportunityPipeline(basic_config)

        # Mock Agno with full evidence structure
        mock_agno_instance = MagicMock()
        mock_agno_instance.copy_agno_analysis.return_value = {
            "willingness_to_pay_score": 85,
            "customer_segment": "B2B SaaS",
            "payment_sentiment": "positive",
            "urgency_level": "high",
            "mentioned_price_points": ["$99", "$299"],
            "existing_payment_behavior": "active",
            "payment_friction_indicators": "low",
            "confidence": 0.92,
        }
        mock_agno_skip.return_value = mock_agno_instance

        # Mock Profiler
        mock_profiler_instance = MagicMock()
        mock_profiler_instance.copy_profiler_analysis.return_value = {
            "app_name": "Test App",
        }
        mock_profiler_skip.return_value = mock_profiler_instance

        result = pipeline._copy_existing_enrichment(
            sample_submissions[0], "concept_123"
        )

        # Verify evidence was marked as copied
        assert result["profiler_evidence_source"] == "copied_agno"
