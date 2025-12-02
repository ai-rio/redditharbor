"""
Simple integration test for staging layer functionality
Demonstrates complete TDD implementation without external dependencies
"""

import pytest
import tempfile
from datetime import datetime, UTC
from pathlib import Path

from models.reddit import RedditSubmission
from staging.staging_layer import StagingLayer, StagingConfig, CheckpointManager


class TestStagingSimpleIntegration:
    """Simple integration tests for staging layer functionality"""

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
                id="simple001",
                title="Simple Test Post 1",
                text="This is simple test content 1",
                author="simple_user1",
                upvotes=15,
                downvotes=1,
                score=14,
                comments_count=5,
                subreddit="testsimple",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/testsimple/simple001"
            ),
            RedditSubmission(
                id="simple002",
                title="Simple Test Post 2",
                text="This is simple test content 2",
                author="simple_user2",
                upvotes=20,
                downvotes=2,
                score=18,
                comments_count=8,
                subreddit="testsimple",
                created_utc=datetime.now(UTC),
                permalink="https://reddit.com/r/testsimple/simple002"
            )
        ]

    def test_complete_staging_workflow(self, temp_staging_dir, sample_submissions):
        """Test complete staging workflow: store → deduplicate → checkpoint → recover"""
        # 1. Initialize staging layer
        staging_config = StagingConfig(
            staging_directory=str(temp_staging_dir),
            max_batch_size=10,
            deduplication_enabled=True,
            checkpoint_interval=5,
            enable_persistence=True
        )

        staging_layer = StagingLayer(staging_config)

        # 2. Store submissions
        batch_id = staging_layer.store_submissions(sample_submissions)

        assert batch_id is not None
        assert len(staging_layer.processed_ids) == len(sample_submissions)

        # 3. Verify deduplication works
        duplicate_submissions = sample_submissions + [sample_submissions[0]]  # Add duplicate
        duplicate_batch_id = staging_layer.store_submissions(duplicate_submissions)

        # Should still only have unique submissions processed
        assert len(staging_layer.processed_ids) == len(sample_submissions)

        # 4. Create checkpoint
        checkpoint_data = staging_layer.create_checkpoint(batch_id)

        assert checkpoint_data is not None
        assert 'checkpoint_id' in checkpoint_data
        assert 'batch_id' in checkpoint_data
        assert 'submission_ids' in checkpoint_data

        # 5. Create new staging layer instance (simulate restart)
        new_staging_layer = StagingLayer(staging_config)

        # 6. Recover from checkpoint
        recovered_submissions = new_staging_layer.recover_from_checkpoint(checkpoint_data['checkpoint_id'])

        assert recovered_submissions is not None
        assert len(recovered_submissions) == len(sample_submissions)

        # 7. Verify recovered data integrity
        recovered_ids = {sub.id for sub in recovered_submissions}
        original_ids = {sub.id for sub in sample_submissions}
        assert recovered_ids == original_ids

    def test_batch_management(self, temp_staging_dir):
        """Test batch size limits and multiple batch handling"""
        staging_config = StagingConfig(
            staging_directory=str(temp_staging_dir),
            max_batch_size=3,  # Small batch size for testing
            deduplication_enabled=True
        )

        staging_layer = StagingLayer(staging_config)

        # Create more submissions than batch size
        large_submission_list = []
        for i in range(7):  # Will create multiple batches
            submission = RedditSubmission(
                id=f"batch_test_{i}",
                title=f"Batch Test {i}",
                text=f"Content {i}",
                author=f"user{i}",
                upvotes=i*5,
                downvotes=0,
                score=i*5,
                comments_count=i+2,
                subreddit="testbatch",
                created_utc=datetime.now(UTC),
                permalink=f"https://reddit.com/r/testbatch/batch_test_{i}"
            )
            large_submission_list.append(submission)

        # Store submissions (should create multiple batches)
        batch_ids = staging_layer.store_submissions(large_submission_list)

        # Should return list of batch IDs
        assert isinstance(batch_ids, list)
        assert len(batch_ids) > 1  # Multiple batches

        # Verify all submissions were processed
        assert len(staging_layer.processed_ids) == len(large_submission_list)

        # Verify each batch respects size limits
        for batch_id in batch_ids:
            batch_submissions = staging_layer.get_batch(batch_id)
            assert len(batch_submissions) <= staging_config.max_batch_size

    def test_error_recovery_and_rollback(self, temp_staging_dir, sample_submissions):
        """Test error recovery and rollback capabilities"""
        staging_config = StagingConfig(
            staging_directory=str(temp_staging_dir),
            enable_persistence=True
        )

        staging_layer = StagingLayer(staging_config)

        # Start a batch and add some submissions
        batch_id = staging_layer.start_batch()
        staging_layer.add_to_batch(sample_submissions[0], batch_id)
        staging_layer.add_to_batch(sample_submissions[1], batch_id)

        # Verify batch has submissions
        assert len(staging_layer.current_batch) == 2

        # Simulate error and rollback
        success = staging_layer.rollback_batch(batch_id)

        assert success is True
        assert len(staging_layer.current_batch) == 0  # Should be empty after rollback

        # Verify batch file is removed
        with pytest.raises(FileNotFoundError):
            staging_layer.get_batch(batch_id)

    def test_checkpoint_manager_functionality(self, temp_staging_dir):
        """Test checkpoint manager independently"""
        checkpoint_manager = CheckpointManager(temp_staging_dir)

        # Create multiple checkpoints
        checkpoints_created = []
        for i in range(3):
            checkpoint_data = {
                'batch_id': f'test_batch_{i}',
                'submission_ids': [f'sub_{i}_1', f'sub_{i}_2'],
                'metadata': {'test_data': f'value_{i}'}
            }
            checkpoint_id = checkpoint_manager.save_checkpoint(checkpoint_data)
            checkpoints_created.append(checkpoint_id)

        # List checkpoints
        checkpoints = checkpoint_manager.list_checkpoints()
        assert len(checkpoints) == 3

        # Get latest checkpoint
        latest = checkpoint_manager.get_latest_checkpoint()
        assert latest is not None
        assert latest['batch_id'] == 'test_batch_2'  # Last one created

        # Cleanup old checkpoints (keep latest 1)
        cleaned = checkpoint_manager.cleanup_old_checkpoints(keep_latest=1)
        assert cleaned == 2  # Should have cleaned 2 old checkpoints

        # Verify only 1 remains
        remaining = checkpoint_manager.list_checkpoints()
        assert len(remaining) == 1

    def test_staging_statistics_and_monitoring(self, temp_staging_dir, sample_submissions):
        """Test staging layer statistics and monitoring capabilities"""
        staging_config = StagingConfig(
            staging_directory=str(temp_staging_dir),
            max_batch_size=10,
            deduplication_enabled=True,
            checkpoint_interval=5
        )

        staging_layer = StagingLayer(staging_config)

        # Store submissions
        batch_id = staging_layer.store_submissions(sample_submissions)

        # Get statistics
        stats = staging_layer.get_statistics()

        # Verify statistics structure
        required_fields = [
            'processed_submissions', 'active_batches', 'available_checkpoints',
            'current_batch_size', 'staging_directory', 'deduplication_enabled',
            'max_batch_size'
        ]

        for field in required_fields:
            assert field in stats

        # Verify statistics values
        assert stats['processed_submissions'] == len(sample_submissions)
        assert stats['active_batches'] >= 1  # At least our batch
        assert stats['deduplication_enabled'] is True
        assert stats['max_batch_size'] == 10

    def test_data_validation_before_staging(self, temp_staging_dir):
        """Test that data validation occurs before staging"""
        staging_layer = StagingLayer(StagingConfig(
            staging_directory=str(temp_staging_dir)
        ))

        # Test with valid submission
        valid_submission = RedditSubmission(
            id="valid123",
            title="Valid Title",
            text="Valid content",
            author="valid_user",
            upvotes=10,
            downvotes=1,
            score=9,
            comments_count=5,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink="https://reddit.com/r/test/valid123"
        )

        # Should work without error
        batch_id = staging_layer.store_submissions([valid_submission])
        assert batch_id is not None
        assert valid_submission.id in staging_layer.processed_ids