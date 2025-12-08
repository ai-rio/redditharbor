"""
Integration test for staging layer with pipeline orchestrator
Demonstrates complete TDD implementation working end-to-end
"""

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import List

import pytest

from models.reddit import RedditSubmission
from orchestration.pipeline_orchestrator import (
    PipelineConfiguration,
    PipelineOrchestrator,
)
from staging.staging_layer import StagingConfig, StagingLayer


class TestStagingIntegration:
    """Integration tests for staging layer with pipeline orchestrator"""

    @pytest.fixture
    def temp_staging_dir(self):
        """Create temporary directory for staging tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_submissions(self):
        """Create sample Reddit submissions for testing"""
        return [
            RedditSubmission(
                id="integration001",
                title="Integration Test Post 1",
                text="This is integration test content 1",
                author="test_user1",
                upvotes=25,
                downvotes=2,
                score=23,
                comments_count=8,
                subreddit="testintegration",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/testintegration/integration001"
            ),
            RedditSubmission(
                id="integration002",
                title="Integration Test Post 2",
                text="This is integration test content 2",
                author="test_user2",
                upvotes=30,
                downvotes=3,
                score=27,
                comments_count=12,
                subreddit="testintegration",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/testintegration/integration002"
            )
        ]

    def test_pipeline_with_staging_layer_integration(self, temp_staging_dir, sample_submissions):
        """Test that pipeline orchestrator can be initialized with staging layer"""
        # Create staging configuration
        staging_config = StagingConfig(
            staging_directory=str(temp_staging_dir),
            max_batch_size=10,
            deduplication_enabled=True,
            checkpoint_interval=5
        )

        # Create staging layer
        staging_layer = StagingLayer(staging_config)

        # Create pipeline configuration with staging enabled
        pipeline_config = PipelineConfiguration(
            enable_staging=True,
            staging_batch_size=10,
            enable_deduplication=True,
            enable_checkpoints=True,
            checkpoint_interval=5,
            test_mode=True,  # Use test mode to avoid external dependencies
            dry_run=True
        )

        # Initialize pipeline orchestrator with staging layer
        orchestrator = PipelineOrchestrator(
            staging_layer=staging_layer,
            settings=None  # Will use default settings
        )

        # Verify orchestrator has staging layer
        assert orchestrator.staging_layer is not None
        assert orchestrator.staging_layer.config == staging_config

        # Test that submissions can be staged through the pipeline workflow
        # (We'll test the _stage_submissions method directly)
        staged_submissions, staging_time = orchestrator._stage_submissions(
            sample_submissions, pipeline_config
        )

        # Verify staging worked correctly
        assert len(staged_submissions) == len(sample_submissions)
        assert staging_time >= 0.0

        # Verify deduplication tracking
        for submission in sample_submissions:
            assert submission.id in staging_layer.processed_ids

    def test_staging_layer_prevents_duplicate_processing(self, temp_staging_dir, sample_submissions):
        """Test that staging layer prevents duplicate submissions"""
        staging_config = StagingConfig(
            staging_directory=str(temp_staging_dir),
            max_batch_size=10,
            deduplication_enabled=True
        )

        staging_layer = StagingLayer(staging_config)

        # Store submissions first time
        batch_ids_1 = staging_layer.store_submissions(sample_submissions)
        initial_count = len(staging_layer.processed_ids)

        # Try to store same submissions again
        batch_ids_2 = staging_layer.store_submissions(sample_submissions)
        final_count = len(staging_layer.processed_ids)

        # Should not process duplicates
        assert initial_count == final_count
        assert len(sample_submissions) == final_count

    def test_checkpoint_recovery_workflow(self, temp_staging_dir, sample_submissions):
        """Test complete checkpoint and recovery workflow"""
        staging_config = StagingConfig(
            staging_directory=str(temp_staging_dir),
            max_batch_size=5,
            deduplication_enabled=True,
            checkpoint_interval=2
        )

        staging_layer = StagingLayer(staging_config)

        # Store submissions with automatic checkpointing
        batch_id = staging_layer.store_submissions(sample_submissions)

        # Create explicit checkpoint
        checkpoint_data = staging_layer.create_checkpoint(batch_id)

        # Create new staging layer instance
        new_staging_layer = StagingLayer(staging_config)

        # Recover from checkpoint
        recovered_submissions = new_staging_layer.recover_from_checkpoint(checkpoint_data['checkpoint_id'])

        assert recovered_submissions is not None
        assert len(recovered_submissions) == len(sample_submissions)

        # Verify submission IDs match
        recovered_ids = [sub.id for sub in recovered_submissions]
        original_ids = [sub.id for sub in sample_submissions]
        assert set(recovered_ids) == set(original_ids)

    def test_staging_configuration_validation(self, temp_staging_dir):
        """Test staging configuration validation"""
        # Test valid configuration
        valid_config = StagingConfig(
            staging_directory=str(temp_staging_dir),
            max_batch_size=100,
            deduplication_enabled=True
        )

        staging_layer = StagingLayer(valid_config)
        assert staging_layer.config == valid_config
        assert staging_layer.staging_directory.exists()

    def test_staging_layer_statistics(self, temp_staging_dir, sample_submissions):
        """Test staging layer statistics reporting"""
        staging_config = StagingConfig(
            staging_directory=str(temp_staging_dir),
            max_batch_size=10,
            deduplication_enabled=True
        )

        staging_layer = StagingLayer(staging_config)

        # Store submissions
        staging_layer.store_submissions(sample_submissions)

        # Get statistics
        stats = staging_layer.get_statistics()

        assert 'processed_submissions' in stats
        assert 'active_batches' in stats
        assert 'available_checkpoints' in stats
        assert 'deduplication_enabled' in stats
        assert 'max_batch_size' in stats

        assert stats['processed_submissions'] == len(sample_submissions)
        assert stats['deduplication_enabled'] is True
        assert stats['max_batch_size'] == 10

    def test_pipeline_configuration_staging_options(self):
        """Test pipeline configuration includes staging options"""
        config = PipelineConfiguration(
            enable_staging=True,
            staging_batch_size=25,
            enable_deduplication=True,
            enable_checkpoints=True,
            checkpoint_interval=10
        )

        assert config.enable_staging is True
        assert config.staging_batch_size == 25
        assert config.enable_deduplication is True
        assert config.enable_checkpoints is True
        assert config.checkpoint_interval == 10

        # Test default values
        default_config = PipelineConfiguration()
        assert default_config.enable_staging is True  # Should be enabled by default
        assert default_config.staging_batch_size == 50
        assert default_config.enable_deduplication is True
        assert default_config.enable_checkpoints is True
        assert default_config.checkpoint_interval == 25
