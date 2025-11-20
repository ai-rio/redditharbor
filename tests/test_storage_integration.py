"""Integration tests for storage layer with enrichment services.

Tests the integration between storage services and enrichment pipeline,
validating end-to-end data flow from enrichment to storage.
"""

import pytest
from unittest.mock import MagicMock, patch
from core.storage import OpportunityStore, ProfileStore, HybridStore, DLTLoader


class TestEnrichmentPipelineIntegration:
    """Test storage integration with enrichment services pattern."""

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_opportunity_enrichment_to_storage(self, mock_pipeline_func):
        """Test opportunity enrichment results can be stored."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Simulate enrichment service output
        enriched_opportunities = [
            {
                "submission_id": "enrich_opp_1",
                "problem_description": "Users spend too much time managing tasks",
                "app_concept": "AI-powered task management platform",
                "core_functions": ["Smart scheduling", "Auto-prioritization", "Team sync"],
                "value_proposition": "Save 5 hours per week on task management",
                "target_user": "Small to medium teams",
                "monetization_model": "Subscription: $15/user/month",
                "opportunity_score": 78.5,
                "final_score": 82.0,
                "status": "enriched",
            }
        ]

        store = OpportunityStore()
        success = store.store(enriched_opportunities)

        assert success is True
        assert store.stats.loaded == 1
        assert store.stats.failed == 0

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_trust_validation_to_storage(self, mock_pipeline_func):
        """Test trust validation results can be stored."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Simulate trust validation output
        validated_profiles = [
            {
                "submission_id": "trust_prof_1",
                "reddit_id": "r_trust1",
                "title": "Looking for feedback on my SaaS idea",
                "selftext": "I've been working on this for 6 months...",
                "author": "validated_user",
                "subreddit": "Entrepreneur",
                "trust_score": 85.5,
                "trust_level": "high",
                "market_validation_score": 72.0,
            }
        ]

        store = ProfileStore()
        success = store.store(validated_profiles)

        assert success is True
        assert store.stats.loaded == 1

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_full_pipeline_enrichment_to_storage(self, mock_pipeline_func):
        """Test complete pipeline: profiling → trust → opportunity → storage."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Simulate full enrichment pipeline output
        fully_enriched = [
            {
                # Submission data
                "submission_id": "full_pipe_1",
                "reddit_id": "r_full1",
                "title": "Revolutionary productivity app idea",
                "selftext": "After years of research...",
                "author": "innovator_user",
                "subreddit": "SaaS",
                # Trust validation
                "trust_score": 88.0,
                "trust_level": "high",
                # Market validation
                "market_validation_score": 75.5,
                # Opportunity analysis
                "problem_description": "Professionals waste 15+ hours weekly on manual scheduling",
                "app_concept": "AI calendar that auto-schedules based on priorities",
                "core_functions": ["AI scheduling", "Priority detection", "Calendar sync"],
                "value_proposition": "Reclaim 15 hours per week",
                "target_user": "Busy professionals",
                "monetization_model": "Premium: $29/month",
                "opportunity_score": 82.5,
                "final_score": 85.0,
                "status": "validated",
            }
        ]

        # Use HybridStore for complete pipeline storage
        store = HybridStore()
        success = store.store(fully_enriched)

        assert success is True
        assert store.stats.loaded == 1
        # HybridStore should call load twice (opportunities + profiles)
        assert mock_pipeline.run.call_count == 2

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_batch_enrichment_storage(self, mock_pipeline_func):
        """Test batch enrichment can be stored efficiently."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Simulate batch enrichment output
        batch_enriched = [
            {
                "submission_id": f"batch_enrich_{i}",
                "problem_description": f"Problem {i}",
                "app_concept": f"App concept {i}",
                "core_functions": [f"Feature {i}"],
                "value_proposition": f"Value {i}",
                "target_user": "Users",
                "monetization_model": "Subscription",
                "opportunity_score": 70.0 + i,
            }
            for i in range(20)
        ]

        loader = MagicMock(spec=DLTLoader)
        loader.load_batch.return_value = {
            "total_records": 20,
            "batches": 2,
            "successful_batches": 2,
            "failed_batches": 0,
            "success_rate": 1.0,
            "loaded": 20,
            "failed": 0,
        }

        store = OpportunityStore(loader=loader)
        result = store.store_batch(batch_enriched, batch_size=10)

        assert result["success_rate"] == 1.0
        assert result["total_records"] == 20


class TestMultiServiceCoordination:
    """Test coordination between multiple storage services."""

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_shared_loader_across_services(self, mock_pipeline_func):
        """Test multiple services sharing same DLTLoader."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Create shared loader
        shared_loader = DLTLoader()

        # Create multiple stores with shared loader
        opp_store = OpportunityStore(loader=shared_loader)
        profile_store = ProfileStore(loader=shared_loader)
        hybrid_store = HybridStore(loader=shared_loader)

        # All should share same loader
        assert opp_store.loader is shared_loader
        assert profile_store.loader is shared_loader
        assert hybrid_store.loader is shared_loader

        # Test operations
        opp_data = [
            {
                "submission_id": "shared_opp",
                "problem_description": "Problem",
                "app_concept": "App",
                "core_functions": ["F1"],
                "value_proposition": "Value",
                "target_user": "Users",
                "monetization_model": "Model",
            }
        ]

        profile_data = [
            {
                "submission_id": "shared_prof",
                "reddit_id": "r_shared",
                "title": "Title",
                "author": "author",
            }
        ]

        assert opp_store.store(opp_data) is True
        assert profile_store.store(profile_data) is True

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_sequential_enrichment_stages(self, mock_pipeline_func):
        """Test sequential enrichment stages can store to same tables."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        store = OpportunityStore()

        # Stage 1: Initial profiling
        stage1_data = [
            {
                "submission_id": "seq_1",
                "problem_description": "Initial problem analysis",
                "app_concept": "Initial concept",
                "core_functions": ["F1"],
                "value_proposition": "Initial value",
                "target_user": "Users",
                "monetization_model": "Model",
            }
        ]

        # Stage 2: Enhanced with opportunity scoring
        stage2_data = [
            {
                "submission_id": "seq_1",  # Same ID
                "problem_description": "Refined problem analysis",
                "app_concept": "Refined concept",
                "core_functions": ["F1", "F2"],
                "value_proposition": "Enhanced value",
                "target_user": "Targeted users",
                "monetization_model": "Premium model",
                "opportunity_score": 75.0,  # Added in stage 2
            }
        ]

        # Stage 3: Final validation
        stage3_data = [
            {
                "submission_id": "seq_1",  # Same ID
                "problem_description": "Final problem analysis",
                "app_concept": "Final concept",
                "core_functions": ["F1", "F2", "F3"],
                "value_proposition": "Final value",
                "target_user": "Validated users",
                "monetization_model": "Validated model",
                "opportunity_score": 82.5,
                "final_score": 85.0,  # Added in stage 3
                "status": "validated",
            }
        ]

        # All stages should succeed with merge disposition
        assert store.store(stage1_data) is True
        assert store.store(stage2_data) is True
        assert store.store(stage3_data) is True

        assert store.stats.loaded == 3  # 3 successful loads
        assert store.stats.failed == 0


class TestErrorHandlingInIntegration:
    """Test error handling in integrated scenarios."""

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_partial_enrichment_failure_recovery(self, mock_pipeline_func):
        """Test storage handles partial enrichment failures gracefully."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Mix of successful and failed enrichments
        mixed_results = [
            {
                "submission_id": "success_1",
                "problem_description": "Valid enrichment",
                "app_concept": "Valid app",
                "core_functions": ["F1"],
                "value_proposition": "Value",
                "target_user": "Users",
                "monetization_model": "Model",
            },
            {
                "submission_id": "failed_1",
                # Missing problem_description - enrichment failed
                "app_concept": "Incomplete",
            },
            {
                "submission_id": "success_2",
                "problem_description": "Another valid enrichment",
                "app_concept": "Another valid app",
                "core_functions": ["F1"],
                "value_proposition": "Value",
                "target_user": "Users",
                "monetization_model": "Model",
            },
        ]

        store = OpportunityStore()
        success = store.store(mixed_results)

        # Should succeed but skip failed enrichments
        assert success is True
        assert store.stats.loaded == 2  # Only 2 valid
        assert store.stats.skipped == 1  # 1 failed enrichment skipped

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_enrichment_service_timeout_handling(self, mock_pipeline_func):
        """Test storage handles enrichment service timeouts."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Simulate enrichment with timeout indicators
        timeout_results = [
            {
                "submission_id": "timeout_1",
                "problem_description": "Partial enrichment before timeout",
                "app_concept": "Incomplete due to timeout",
                "core_functions": ["F1"],
                "value_proposition": "Partial",
                "target_user": "Unknown",
                "monetization_model": "TBD",
                "status": "timeout",  # Indicates enrichment timeout
            }
        ]

        store = OpportunityStore()
        # Should still store what was enriched
        success = store.store(timeout_results)
        assert success is True
        assert store.stats.loaded == 1


class TestEndToEndDataFlow:
    """Test complete end-to-end data flow scenarios."""

    @patch("core.storage.dlt_loader.dlt.pipeline")
    def test_complete_enrichment_pipeline(self, mock_pipeline_func):
        """Test complete enrichment pipeline end-to-end."""
        mock_pipeline = MagicMock()
        mock_load_info = MagicMock()
        mock_pipeline.run.return_value = mock_load_info
        mock_pipeline_func.return_value = mock_pipeline

        # Step 1: Raw submission
        raw_submission = {
            "submission_id": "e2e_test_1",
            "reddit_id": "r_e2e1",
            "title": "Need feedback on my app idea",
            "selftext": "I've been working on this for months...",
            "author": "entrepreneur_123",
            "subreddit": "Entrepreneur",
        }

        # Step 2: After trust validation (ProfileStore)
        profile_store = ProfileStore()
        trust_enriched = {
            **raw_submission,
            "trust_score": 82.5,
            "trust_level": "high",
        }
        assert profile_store.store([trust_enriched]) is True

        # Step 3: After opportunity profiling (OpportunityStore)
        opp_store = OpportunityStore()
        opportunity_enriched = {
            "submission_id": "e2e_test_1",
            "problem_description": "Teams struggle with async communication",
            "app_concept": "AI-powered async collaboration platform",
            "core_functions": ["Smart threading", "Auto-summaries", "Priority detection"],
            "value_proposition": "Reduce meeting time by 50%",
            "target_user": "Remote teams",
            "monetization_model": "Team subscription: $199/month",
            "opportunity_score": 78.0,
        }
        assert opp_store.store([opportunity_enriched]) is True

        # Step 4: After market validation (HybridStore for final)
        hybrid_store = HybridStore()
        fully_validated = {
            **trust_enriched,
            **opportunity_enriched,
            "market_validation_score": 75.0,
            "final_score": 80.5,
            "status": "validated",
        }
        assert hybrid_store.store([fully_validated]) is True

        # Verify all stages succeeded
        assert profile_store.stats.loaded == 1
        assert opp_store.stats.loaded == 1
        assert hybrid_store.stats.loaded == 1
