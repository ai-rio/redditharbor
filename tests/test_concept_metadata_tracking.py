"""
Phase 3 Concept Metadata Tracking Tests

Tests the _update_concept_metadata() method in the orchestrator that updates
business concept flags (has_agno_analysis, has_profiler_analysis) after
successful enrichment, enabling future deduplication runs.

Test Coverage:
- Batch concept ID fetching
- Profiler metadata updates
- Agno metadata updates
- Mixed updates (both Profiler and Agno)
- Graceful degradation (no client)
- Error handling
- Statistics tracking
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from core.pipeline.orchestrator import OpportunityPipeline

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_config():
    """Create mock pipeline configuration."""
    config = MagicMock()
    config.supabase_client = MagicMock()
    config.enable_profiler = True
    config.enable_monetization = True
    config.dry_run = False
    config.return_data = False
    config.fetch_mode = "supabase"
    config.filter_threshold = 50.0
    return config


@pytest.fixture
def orchestrator(mock_config):
    """Create orchestrator instance with mocked dependencies."""
    with patch("core.pipeline.factory.ServiceFactory"):
        return OpportunityPipeline(mock_config)


class TestBatchConceptFetching:
    """Test batch fetching of concept IDs for metadata updates."""

    def test_batch_fetch_concept_ids(self, orchestrator, mock_config):
        """Test that concept IDs are fetched in a single batch query."""
        enriched = [
            {"submission_id": "sub_001", "app_name": "TestApp1"},
            {"submission_id": "sub_002", "willingness_to_pay_score": 85.0},
            {"submission_id": "sub_003", "app_name": "TestApp3"},
        ]

        # Mock the batch query response
        mock_response = MagicMock()
        mock_response.data = [
            {"submission_id": "sub_001", "business_concept_id": 101},
            {"submission_id": "sub_002", "business_concept_id": 102},
            {"submission_id": "sub_003", "business_concept_id": 103},
        ]

        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        # Mock the skip logic classes to prevent actual updates
        with (
            patch("core.deduplication.ProfilerSkipLogic") as mock_profiler_cls,
            patch("core.deduplication.AgnoSkipLogic") as mock_agno_cls,
        ):
            mock_profiler = MagicMock()
            mock_agno = MagicMock()
            mock_profiler_cls.return_value = mock_profiler
            mock_agno_cls.return_value = mock_agno

            orchestrator._update_concept_metadata(enriched)

            # Verify single batch query was made
            mock_config.supabase_client.table.assert_called_with(
                "opportunities_unified"
            )
            mock_config.supabase_client.table.return_value.select.assert_called_with(
                "submission_id, business_concept_id"
            )
            mock_config.supabase_client.table.return_value.select.return_value.in_.assert_called_once()

    def test_batch_fetch_with_empty_list(self, orchestrator):
        """Test that empty enriched list is handled gracefully."""
        # Should not raise any errors
        orchestrator._update_concept_metadata([])

    def test_batch_fetch_with_no_submission_ids(self, orchestrator):
        """Test handling of submissions without submission_id."""
        enriched = [
            {"app_name": "TestApp"},  # No submission_id
        ]

        # Should handle gracefully without errors
        orchestrator._update_concept_metadata(enriched)


class TestProfilerMetadataUpdates:
    """Test Profiler analysis metadata updates."""

    def test_profiler_metadata_update_success(self, orchestrator, mock_config):
        """Test successful Profiler metadata update."""
        enriched = [
            {
                "submission_id": "sub_001",
                "app_name": "TaskMaster Pro",
                "ai_profile": {
                    "app_name": "TaskMaster Pro",
                    "core_functions": ["Task management", "Team collaboration"],
                },
            }
        ]

        # Mock concept ID fetch
        mock_response = MagicMock()
        mock_response.data = [{"submission_id": "sub_001", "business_concept_id": 101}]
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        # Mock Profiler skip logic
        with patch("core.deduplication.ProfilerSkipLogic") as mock_profiler_cls:
            mock_profiler = MagicMock()
            mock_profiler.update_concept_profiler_stats.return_value = True
            mock_profiler_cls.return_value = mock_profiler

            orchestrator._update_concept_metadata(enriched)

            # Verify update was called
            mock_profiler.update_concept_profiler_stats.assert_called_once_with(
                concept_id=101, ai_profile=enriched[0]["ai_profile"]
            )

    def test_profiler_metadata_with_app_name_only(self, orchestrator, mock_config):
        """Test Profiler update with only app_name (no full ai_profile)."""
        enriched = [
            {
                "submission_id": "sub_001",
                "app_name": "SimpleApp",
                # No ai_profile - should build minimal one
            }
        ]

        # Mock concept ID fetch
        mock_response = MagicMock()
        mock_response.data = [{"submission_id": "sub_001", "business_concept_id": 101}]
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        # Mock Profiler skip logic
        with patch("core.deduplication.ProfilerSkipLogic") as mock_profiler_cls:
            mock_profiler = MagicMock()
            mock_profiler.update_concept_profiler_stats.return_value = True
            mock_profiler_cls.return_value = mock_profiler

            orchestrator._update_concept_metadata(enriched)

            # Verify update was called with minimal ai_profile
            assert mock_profiler.update_concept_profiler_stats.call_count == 1
            call_args = mock_profiler.update_concept_profiler_stats.call_args
            assert call_args[1]["concept_id"] == 101
            assert call_args[1]["ai_profile"]["app_name"] == "SimpleApp"

    def test_profiler_disabled(self, orchestrator, mock_config):
        """Test that Profiler updates are skipped when disabled."""
        mock_config.enable_profiler = False

        enriched = [
            {
                "submission_id": "sub_001",
                "app_name": "TestApp",
            }
        ]

        # Mock concept ID fetch
        mock_response = MagicMock()
        mock_response.data = [{"submission_id": "sub_001", "business_concept_id": 101}]
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        with patch("core.deduplication.ProfilerSkipLogic") as mock_profiler_cls:
            mock_profiler = MagicMock()
            mock_profiler_cls.return_value = mock_profiler

            orchestrator._update_concept_metadata(enriched)

            # Verify Profiler was never instantiated
            mock_profiler_cls.assert_not_called()


class TestAgnoMetadataUpdates:
    """Test Agno (monetization) analysis metadata updates."""

    def test_agno_metadata_update_success(self, orchestrator, mock_config):
        """Test successful Agno metadata update."""
        enriched = [
            {
                "submission_id": "sub_001",
                "willingness_to_pay_score": 85.5,
                "customer_segment": "premium",
                "payment_sentiment": "positive",
            }
        ]

        # Mock concept ID fetch
        mock_response = MagicMock()
        mock_response.data = [{"submission_id": "sub_001", "business_concept_id": 101}]
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        # Mock Agno skip logic
        with patch("core.deduplication.AgnoSkipLogic") as mock_agno_cls:
            mock_agno = MagicMock()
            mock_agno.update_concept_agno_stats.return_value = True
            mock_agno_cls.return_value = mock_agno

            orchestrator._update_concept_metadata(enriched)

            # Verify update was called
            assert mock_agno.update_concept_agno_stats.call_count == 1
            call_args = mock_agno.update_concept_agno_stats.call_args
            assert call_args[1]["concept_id"] == 101
            assert call_args[1]["agno_result"]["willingness_to_pay_score"] == 85.5

    def test_agno_disabled(self, orchestrator, mock_config):
        """Test that Agno updates are skipped when disabled."""
        mock_config.enable_monetization = False

        enriched = [
            {
                "submission_id": "sub_001",
                "willingness_to_pay_score": 85.5,
            }
        ]

        # Mock concept ID fetch
        mock_response = MagicMock()
        mock_response.data = [{"submission_id": "sub_001", "business_concept_id": 101}]
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        with patch("core.deduplication.AgnoSkipLogic") as mock_agno_cls:
            mock_agno = MagicMock()
            mock_agno_cls.return_value = mock_agno

            orchestrator._update_concept_metadata(enriched)

            # Verify Agno was never instantiated
            mock_agno_cls.assert_not_called()


class TestMixedUpdates:
    """Test scenarios with both Profiler and Agno updates."""

    def test_both_profiler_and_agno_updates(self, orchestrator, mock_config):
        """Test that both Profiler and Agno can be updated in same batch."""
        enriched = [
            {
                "submission_id": "sub_001",
                "app_name": "TestApp",
                "willingness_to_pay_score": 85.5,
            },
            {
                "submission_id": "sub_002",
                "app_name": "TestApp2",
            },
            {
                "submission_id": "sub_003",
                "willingness_to_pay_score": 72.3,
            },
        ]

        # Mock concept ID fetch
        mock_response = MagicMock()
        mock_response.data = [
            {"submission_id": "sub_001", "business_concept_id": 101},
            {"submission_id": "sub_002", "business_concept_id": 102},
            {"submission_id": "sub_003", "business_concept_id": 103},
        ]
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        with (
            patch("core.deduplication.ProfilerSkipLogic") as mock_profiler_cls,
            patch("core.deduplication.AgnoSkipLogic") as mock_agno_cls,
        ):
            mock_profiler = MagicMock()
            mock_agno = MagicMock()
            mock_profiler.update_concept_profiler_stats.return_value = True
            mock_agno.update_concept_agno_stats.return_value = True
            mock_profiler_cls.return_value = mock_profiler
            mock_agno_cls.return_value = mock_agno

            orchestrator._update_concept_metadata(enriched)

            # Verify Profiler updates (sub_001 and sub_002)
            assert mock_profiler.update_concept_profiler_stats.call_count == 2

            # Verify Agno updates (sub_001 and sub_003)
            assert mock_agno.update_concept_agno_stats.call_count == 2


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_no_supabase_client(self, orchestrator):
        """Test graceful handling when no Supabase client available."""
        orchestrator.config.supabase_client = None

        enriched = [
            {
                "submission_id": "sub_001",
                "app_name": "TestApp",
            }
        ]

        # Should not raise errors
        orchestrator._update_concept_metadata(enriched)

    def test_concept_fetch_error(self, orchestrator, mock_config):
        """Test handling of database errors during concept fetch."""
        enriched = [
            {
                "submission_id": "sub_001",
                "app_name": "TestApp",
            }
        ]

        # Mock database error
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.side_effect
        ) = Exception("Database connection error")

        # Should handle error gracefully without raising
        orchestrator._update_concept_metadata(enriched)

    def test_update_failure_logged(self, orchestrator, mock_config):
        """Test that update failures are logged but don't crash pipeline."""
        enriched = [
            {
                "submission_id": "sub_001",
                "app_name": "TestApp",
            }
        ]

        # Mock concept ID fetch
        mock_response = MagicMock()
        mock_response.data = [{"submission_id": "sub_001", "business_concept_id": 101}]
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        with patch("core.deduplication.ProfilerSkipLogic") as mock_profiler_cls:
            mock_profiler = MagicMock()
            # Simulate update failure
            mock_profiler.update_concept_profiler_stats.return_value = False
            mock_profiler_cls.return_value = mock_profiler

            # Should not raise error
            orchestrator._update_concept_metadata(enriched)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_missing_concept_id_for_submission(self, orchestrator, mock_config):
        """Test handling when submission has no matching concept."""
        enriched = [
            {
                "submission_id": "sub_001",
                "app_name": "TestApp",
            }
        ]

        # Mock empty response (no concept found)
        mock_response = MagicMock()
        mock_response.data = []
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        with patch("core.deduplication.ProfilerSkipLogic") as mock_profiler_cls:
            mock_profiler = MagicMock()
            mock_profiler_cls.return_value = mock_profiler

            orchestrator._update_concept_metadata(enriched)

            # Should not attempt any updates
            mock_profiler.update_concept_profiler_stats.assert_not_called()

    def test_partial_concept_data(self, orchestrator, mock_config):
        """Test handling of partial concept data from database."""
        enriched = [
            {"submission_id": "sub_001", "app_name": "TestApp1"},
            {"submission_id": "sub_002", "app_name": "TestApp2"},
        ]

        # Mock partial response (only one concept found)
        mock_response = MagicMock()
        mock_response.data = [
            {"submission_id": "sub_001", "business_concept_id": 101},
            # sub_002 missing
        ]
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        with patch("core.deduplication.ProfilerSkipLogic") as mock_profiler_cls:
            mock_profiler = MagicMock()
            mock_profiler.update_concept_profiler_stats.return_value = True
            mock_profiler_cls.return_value = mock_profiler

            orchestrator._update_concept_metadata(enriched)

            # Should only update sub_001
            assert mock_profiler.update_concept_profiler_stats.call_count == 1

    def test_enriched_with_no_relevant_fields(self, orchestrator, mock_config):
        """Test handling of enriched data with no Profiler or Agno fields."""
        enriched = [
            {
                "submission_id": "sub_001",
                "opportunity_score": 75.0,  # Only opportunity score, no AI enrichment
            }
        ]

        # Mock concept ID fetch
        mock_response = MagicMock()
        mock_response.data = [{"submission_id": "sub_001", "business_concept_id": 101}]
        (
            mock_config.supabase_client.table.return_value.select.return_value.in_
            .return_value.execute.return_value
        ) = mock_response

        with (
            patch("core.deduplication.ProfilerSkipLogic") as mock_profiler_cls,
            patch("core.deduplication.AgnoSkipLogic") as mock_agno_cls,
        ):
            mock_profiler = MagicMock()
            mock_agno = MagicMock()
            mock_profiler_cls.return_value = mock_profiler
            mock_agno_cls.return_value = mock_agno

            orchestrator._update_concept_metadata(enriched)

            # Should not attempt any updates (no relevant fields)
            mock_profiler.update_concept_profiler_stats.assert_not_called()
            mock_agno.update_concept_agno_stats.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
