"""
Tests for staging layer deduplication
"""

import json
import tempfile
from pathlib import Path
from datetime import UTC, datetime

import pytest

from models.reddit import RedditSubmission
from core.staging import StagingLayer


@pytest.fixture
def temp_staging_dir():
    """Create a temporary staging directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_submission():
    """Create a sample Reddit submission"""
    return RedditSubmission(
        id="test123",
        title="Test Submission",
        text="This is a test submission",
        author="testuser",
        upvotes=10,
        downvotes=1,
        score=9,
        comments_count=5,
        subreddit="test",
        created_utc=datetime.now(UTC),
        permalink="https://reddit.com/r/test/test123"
    )


@pytest.fixture
def staging_layer(temp_staging_dir):
    """Create a staging layer instance"""
    return StagingLayer(temp_staging_dir)


def test_staging_init_empty(temp_staging_dir):
    """Test staging initialization with empty state"""
    staging = StagingLayer(temp_staging_dir)
    assert len(staging.processed_ids) == 0
    assert staging.staging_dir == Path(temp_staging_dir)


def test_staging_init_with_existing_state(temp_staging_dir, sample_submission):
    """Test staging initialization with existing state file"""
    # Create a state file with some processed IDs
    state_file = Path(temp_staging_dir) / "processed.json"
    state_data = {
        'processed_ids': [sample_submission.id, 'another_id'],
        'count': 2
    }
    with open(state_file, 'w') as f:
        json.dump(state_data, f)

    # Initialize staging - should load existing state
    staging = StagingLayer(temp_staging_dir)
    assert len(staging.processed_ids) == 2
    assert sample_submission.id in staging.processed_ids
    assert 'another_id' in staging.processed_ids


def test_is_duplicate(staging_layer, sample_submission):
    """Test duplicate detection"""
    # Initially not a duplicate
    assert not staging_layer.is_duplicate(sample_submission)

    # After checkpointing, it should be a duplicate
    staging_layer.checkpoint_single(sample_submission)
    assert staging_layer.is_duplicate(sample_submission)


def test_checkpoint_single(staging_layer, sample_submission):
    """Test checkpointing a single submission"""
    assert sample_submission.id not in staging_layer.processed_ids

    staging_layer.checkpoint_single(sample_submission)
    assert sample_submission.id in staging_layer.processed_ids

    # Check that state file was created
    state_file = staging_layer.state_file
    assert state_file.exists()

    # Verify state file content
    with open(state_file, 'r') as f:
        state_data = json.load(f)
        assert sample_submission.id in state_data['processed_ids']
        assert state_data['count'] == 1


def test_checkpoint_multiple(staging_layer):
    """Test checkpointing multiple submissions"""
    submissions = [
        RedditSubmission(
            id=f"test{i}",
            title=f"Test {i}",
            text="Content",
            author="user",
            upvotes=1,
            downvotes=0,
            score=1,
            comments_count=0,
            subreddit="test",
            created_utc=datetime.now(UTC),
            permalink=f"https://reddit.com/r/test/test{i}"
        )
        for i in range(5)
    ]

    # Checkpoint all submissions
    staging_layer.checkpoint(submissions)

    # Verify all IDs are in processed set
    for sub in submissions:
        assert sub.id in staging_layer.processed_ids

    # Verify state file
    with open(staging_layer.state_file, 'r') as f:
        state_data = json.load(f)
        assert state_data['count'] == 5


def test_checkpoint_with_duplicates(staging_layer, sample_submission):
    """Test checkpointing with duplicate submissions"""
    # Checkpoint once
    staging_layer.checkpoint_single(sample_submission)
    initial_count = len(staging_layer.processed_ids)

    # Checkpoint again - should not increase count
    staging_layer.checkpoint_single(sample_submission)
    assert len(staging_layer.processed_ids) == initial_count


def test_clear(staging_layer, sample_submission):
    """Test clearing staging state"""
    # Add some submissions
    staging_layer.checkpoint_single(sample_submission)
    assert len(staging_layer.processed_ids) == 1
    assert staging_layer.state_file.exists()

    # Clear state
    staging_layer.clear()

    # Verify everything is cleared
    assert len(staging_layer.processed_ids) == 0
    assert not staging_layer.state_file.exists()


def test_get_statistics(staging_layer, sample_submission):
    """Test getting staging statistics"""
    # Initially empty
    stats = staging_layer.get_statistics()
    assert stats['processed_count'] == 0
    assert stats['state_file_exists'] == False

    # After adding a submission
    staging_layer.checkpoint_single(sample_submission)
    stats = staging_layer.get_statistics()
    assert stats['processed_count'] == 1
    assert stats['state_file_exists'] == True
    assert str(staging_layer.staging_dir) in stats['staging_directory']


def test_corrupted_state_file_handling(temp_staging_dir):
    """Test handling of corrupted state file"""
    # Create a corrupted JSON file
    state_file = Path(temp_staging_dir) / "processed.json"
    with open(state_file, 'w') as f:
        f.write("invalid json content")

    # Initialize staging - should handle gracefully
    staging = StagingLayer(temp_staging_dir)
    assert len(staging.processed_ids) == 0  # Should start fresh


def test_auto_create_directory():
    """Test that staging directory is auto-created"""
    with tempfile.TemporaryDirectory() as tmpdir:
        staging_dir = Path(tmpdir) / "subdir" / "pipeline_staging"
        assert not staging_dir.exists()

        staging = StagingLayer(str(staging_dir))
        assert staging_dir.exists()
        assert staging_dir.is_dir()