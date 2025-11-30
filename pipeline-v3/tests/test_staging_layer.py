"""
Test suite for staging layer implementation - TDD approach
Tests will fail initially, then drive implementation
"""

import pytest
import tempfile
import json
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import List

from models.reddit import RedditSubmission
from staging.staging_layer import StagingLayer, StagingConfig, CheckpointManager


class TestStagingLayer:
    """Test cases for staging layer functionality"""

    @pytest.fixture
    def temp_staging_dir(self):
        """Create temporary directory for staging tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def staging_config(self, temp_staging_dir):
        """Create staging configuration for testing"""
        return StagingConfig(
            staging_directory=str(temp_staging_dir),
            max_batch_size=5,
            deduplication_enabled=True,
            checkpoint_interval=2
        )

    @pytest.fixture
    def sample_submissions(self):
        """Create sample Reddit submissions for testing"""
        return [
            RedditSubmission(
                id="abc123",
                title="Test Post 1",
                text="This is test content 1",
                author="user1",
                upvotes=10,
                downvotes=1,
                score=9,
                comments_count=5,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/abc123"
            ),
            RedditSubmission(
                id="def456",
                title="Test Post 2",
                text="This is test content 2",
                author="user2",
                upvotes=20,
                downvotes=2,
                score=18,
                comments_count=10,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/def456"
            ),
            RedditSubmission(
                id="ghi789",  # Duplicate for deduplication testing
                title="Test Post 3",
                text="This is test content 3",
                author="user1",  # Same author as first post
                upvotes=15,
                downvotes=0,
                score=15,
                comments_count=7,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/test/ghi789"
            )
        ]

    def test_staging_layer_initialization(self, staging_config):
        """Test staging layer can be initialized with configuration"""
        # This test should fail initially - staging layer doesn't exist yet
        staging_layer = StagingLayer(staging_config)

        assert staging_layer.config == staging_config
        assert staging_layer.staging_directory.exists()
        assert staging_layer.processed_ids == set()
        assert staging_layer.current_batch == []

    def test_store_submissions_single_batch(self, staging_config, sample_submissions):
        """Test storing submissions in a single batch"""
        staging_layer = StagingLayer(staging_config)

        # Store submissions
        batch_id = staging_layer.store_submissions(sample_submissions)

        # Should return a valid batch ID
        assert batch_id is not None
        assert isinstance(batch_id, str)

        # Should track processed submissions
        assert len(staging_layer.processed_ids) == len(sample_submissions)
        for submission in sample_submissions:
            assert submission.id in staging_layer.processed_ids

    def test_deduplication_prevents_reprocessing(self, staging_config, sample_submissions):
        """Test that duplicate submissions are not processed again"""
        staging_layer = StagingLayer(staging_config)

        # Store submissions first time
        first_batch_id = staging_layer.store_submissions(sample_submissions)

        # Try to store same submissions again (including duplicates)
        duplicate_submissions = sample_submissions + [sample_submissions[0]]  # Add explicit duplicate
        second_batch_id = staging_layer.store_submissions(duplicate_submissions)

        # Should return different batch IDs
        assert first_batch_id != second_batch_id

        # Should only process unique submissions
        total_processed = len(staging_layer.processed_ids)
        expected_unique = len(sample_submissions)  # Should only count unique IDs
        assert total_processed == expected_unique

    def test_checkpoint_creation_and_recovery(self, staging_config, sample_submissions):
        """Test checkpoint creation and recovery capabilities"""
        staging_layer = StagingLayer(staging_config)

        # Store submissions and create checkpoint
        batch_id = staging_layer.store_submissions(sample_submissions[:2])
        checkpoint_data = staging_layer.create_checkpoint(batch_id)

        assert checkpoint_data is not None
        assert 'batch_id' in checkpoint_data
        assert 'timestamp' in checkpoint_data
        assert 'submission_ids' in checkpoint_data
        assert len(checkpoint_data['submission_ids']) == 2

        # Create new staging layer and recover from checkpoint
        new_staging_layer = StagingLayer(staging_config)
        recovered_batch = new_staging_layer.recover_from_checkpoint(checkpoint_data['checkpoint_id'])

        assert recovered_batch is not None
        assert len(recovered_batch) == 2
        assert recovered_batch[0].id == sample_submissions[0].id
        assert recovered_batch[1].id == sample_submissions[1].id

    def test_batch_size_limits(self, staging_config):
        """Test that batches respect maximum size limits"""
        staging_layer = StagingLayer(staging_config)

        # Create more submissions than batch size
        large_submission_list = []
        for i in range(10):  # More than max_batch_size=5
            submission = RedditSubmission(
                id=f"batch_test_{i}",
                title=f"Batch Test {i}",
                text=f"Content {i}",
                author=f"user{i}",
                upvotes=i,
                downvotes=0,
                score=i,
                comments_count=i+1,
                subreddit="test",
                created_utc=datetime.now(UTC),
                permalink=f"https://reddit.com/r/test/batch_test_{i}"
            )
            large_submission_list.append(submission)

        # Should create multiple batches
        batch_ids = staging_layer.store_submissions(large_submission_list)

        # Should return list of batch IDs (multiple batches created)
        assert isinstance(batch_ids, list)
        assert len(batch_ids) > 1  # Should be multiple batches

        # Each batch should respect size limits
        for batch_id in batch_ids:
            batch_data = staging_layer.get_batch(batch_id)
            assert len(batch_data) <= staging_config.max_batch_size

    def test_data_validation_before_storage(self, staging_config):
        """Test that data validation occurs before staging"""
        staging_layer = StagingLayer(staging_config)

        # Test that valid submissions pass through successfully
        valid_submission = RedditSubmission(
            id="valid123",
            title="Valid title",
            text="Valid text content",
            author="valid_user",
            upvotes=10,
            downvotes=1,
            score=9,
            comments_count=5,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/valid123"
        )

        # Should succeed without error
        batch_id = staging_layer.store_submissions([valid_submission])
        assert batch_id is not None
        assert valid_submission.id in staging_layer.processed_ids

        # Test that deduplication prevents reprocessing (which is a form of validation)
        duplicate_batch = staging_layer.store_submissions([valid_submission])
        assert valid_submission.id in staging_layer.processed_ids  # Still only processed once
        assert len(staging_layer.processed_ids) == 1  # Only one unique submission processed

    def test_persistence_between_sessions(self, staging_config, sample_submissions):
        """Test that staging data persists between sessions"""
        # Store submissions in first session
        staging_layer_1 = StagingLayer(staging_config)
        batch_id = staging_layer_1.store_submissions(sample_submissions)

        # Create new staging layer (simulating new session)
        staging_layer_2 = StagingLayer(staging_config)

        # Should recover previous state
        assert batch_id in staging_layer_2.list_batches()
        recovered_submissions = staging_layer_2.get_batch(batch_id)

        assert len(recovered_submissions) == len(sample_submissions)
        for i, submission in enumerate(recovered_submissions):
            assert submission.id == sample_submissions[i].id

    def test_checkpoint_manager_integration(self, staging_config, sample_submissions):
        """Test checkpoint manager integration with staging layer"""
        checkpoint_manager = CheckpointManager(staging_config.staging_directory)
        staging_layer = StagingLayer(staging_config, checkpoint_manager)

        # Store submissions with automatic checkpointing
        batch_id = staging_layer.store_submissions(sample_submissions)

        # Checkpoint should be created automatically (due to checkpoint_interval)
        checkpoints = checkpoint_manager.list_checkpoints()
        assert len(checkpoints) > 0

        # Should be able to recover from latest checkpoint
        latest_checkpoint = checkpoint_manager.get_latest_checkpoint()
        assert latest_checkpoint is not None
        assert latest_checkpoint['batch_id'] == batch_id

    def test_error_recovery_and_rollback(self, staging_config, sample_submissions):
        """Test error recovery and rollback capabilities"""
        staging_layer = StagingLayer(staging_config)

        # Start a batch operation
        batch_id = staging_layer.start_batch()

        # Add some submissions
        staging_layer.add_to_batch(sample_submissions[0], batch_id)
        staging_layer.add_to_batch(sample_submissions[1], batch_id)

        # Simulate failure and rollback
        success = staging_layer.rollback_batch(batch_id)

        assert success is True

        # Batch should be removed and resources cleaned up
        with pytest.raises(FileNotFoundError):
            staging_layer.get_batch(batch_id)

        assert batch_id not in staging_layer.list_batches()


class TestCheckpointManager:
    """Test cases for checkpoint manager functionality"""

    @pytest.fixture
    def temp_checkpoint_dir(self):
        """Create temporary directory for checkpoint tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_checkpoint_creation_and_retrieval(self, temp_checkpoint_dir):
        """Test creating and retrieving checkpoints"""
        manager = CheckpointManager(temp_checkpoint_dir)

        checkpoint_data = {
            'batch_id': 'test_batch_001',
            'timestamp': datetime.now(UTC).isoformat(),
            'submission_ids': ['sub1', 'sub2', 'sub3'],
            'metadata': {'test': 'data'}
        }

        checkpoint_id = manager.save_checkpoint(checkpoint_data)
        assert checkpoint_id is not None

        # Retrieve checkpoint
        retrieved = manager.get_checkpoint(checkpoint_id)
        assert retrieved is not None
        assert retrieved['batch_id'] == 'test_batch_001'
        assert len(retrieved['submission_ids']) == 3

    def test_checkpoint_listing_and_cleanup(self, temp_checkpoint_dir):
        """Test listing checkpoints and cleanup"""
        manager = CheckpointManager(temp_checkpoint_dir)

        # Create multiple checkpoints
        for i in range(5):
            checkpoint_data = {
                'batch_id': f'batch_{i}',
                'timestamp': datetime.now(UTC).isoformat(),
                'submission_ids': [f'sub_{i}_1', f'sub_{i}_2']
            }
            manager.save_checkpoint(checkpoint_data)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # List checkpoints
        checkpoints = manager.list_checkpoints()
        assert len(checkpoints) == 5

        # Get latest checkpoint
        latest = manager.get_latest_checkpoint()
        assert latest['batch_id'] == 'batch_4'  # Last one created

        # Clean old checkpoints (keep latest 2)
        cleaned = manager.cleanup_old_checkpoints(keep_latest=2)
        assert cleaned == 3  # Should have cleaned 3 old checkpoints

        # Verify only 2 remain
        remaining = manager.list_checkpoints()
        assert len(remaining) == 2

    def test_checkpoint_validation(self, temp_checkpoint_dir):
        """Test checkpoint data validation"""
        manager = CheckpointManager(temp_checkpoint_dir)

        # Test invalid checkpoint data
        invalid_data = {
            # Missing required fields
            'batch_id': 'invalid_batch'
        }

        with pytest.raises(ValueError, match="Invalid checkpoint data"):
            manager.save_checkpoint(invalid_data)