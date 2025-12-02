"""
Staging layer implementation for Extract → Transform pipeline flow
Provides temporary storage, deduplication, and checkpoint/restart capabilities
"""

import json
import logging
import uuid
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Union
from dataclasses import dataclass, field
import hashlib

from pydantic import BaseModel, Field, ValidationError

from models.reddit import RedditSubmission

logger = logging.getLogger(__name__)


@dataclass
class StagingConfig:
    """Configuration for staging layer"""
    staging_directory: str
    max_batch_size: int = 100
    deduplication_enabled: bool = True
    checkpoint_interval: int = 50
    enable_persistence: bool = True
    compression_enabled: bool = False
    cleanup_after_hours: int = 24


class StagedSubmission(BaseModel):
    """Model for staged submission with metadata"""
    submission: RedditSubmission
    stage_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    batch_id: str
    content_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CheckpointData(BaseModel):
    """Model for checkpoint data"""
    checkpoint_id: str
    batch_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    submission_ids: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processed_count: int = 0
    total_count: int = 0


class CheckpointManager:
    """Manages checkpoint creation, storage, and recovery"""

    def __init__(self, staging_directory: Union[str, Path]):
        """
        Initialize checkpoint manager

        Args:
            staging_directory: Directory for storing checkpoints
        """
        self.staging_directory = Path(staging_directory)
        self.checkpoints_dir = self.staging_directory / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """
        Save checkpoint data to disk

        Args:
            checkpoint_data: Checkpoint data to save

        Returns:
            Checkpoint ID

        Raises:
            ValueError: If checkpoint data is invalid
        """
        # Validate checkpoint data
        required_fields = ['batch_id', 'submission_ids']
        for field in required_fields:
            if field not in checkpoint_data:
                raise ValueError(f"Invalid checkpoint data: missing required field '{field}'")

        # Create checkpoint model
        checkpoint = CheckpointData(
            checkpoint_id=str(uuid.uuid4()),
            batch_id=checkpoint_data['batch_id'],
            submission_ids=checkpoint_data['submission_ids'],
            metadata=checkpoint_data.get('metadata', {}),
            processed_count=len(checkpoint_data['submission_ids']),
            total_count=checkpoint_data.get('total_count', len(checkpoint_data['submission_ids']))
        )

        # Save to file
        checkpoint_file = self.checkpoints_dir / f"{checkpoint.checkpoint_id}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint.model_dump(), f, indent=2, default=str)

        logger.info(f"✓ Saved checkpoint {checkpoint.checkpoint_id} for batch {checkpoint.batch_id}")
        return checkpoint.checkpoint_id

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve checkpoint data

        Args:
            checkpoint_id: ID of checkpoint to retrieve

        Returns:
            Checkpoint data or None if not found
        """
        checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.json"

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            return checkpoint_data
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        List all available checkpoints

        Returns:
            List of checkpoint information
        """
        checkpoints = []

        for checkpoint_file in self.checkpoints_dir.glob("*.json"):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)

                checkpoints.append({
                    'checkpoint_id': checkpoint_data['checkpoint_id'],
                    'batch_id': checkpoint_data['batch_id'],
                    'timestamp': checkpoint_data['timestamp'],
                    'processed_count': checkpoint_data['processed_count'],
                    'total_count': checkpoint_data['total_count']
                })
            except Exception as e:
                logger.warning(f"Failed to read checkpoint file {checkpoint_file}: {e}")
                continue

        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x['timestamp'], reverse=True)
        return checkpoints

    def get_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent checkpoint

        Returns:
            Latest checkpoint data or None if no checkpoints exist
        """
        checkpoints = self.list_checkpoints()
        return checkpoints[0] if checkpoints else None

    def cleanup_old_checkpoints(self, keep_latest: int = 5) -> int:
        """
        Clean up old checkpoints, keeping only the latest N

        Args:
            keep_latest: Number of recent checkpoints to keep

        Returns:
            Number of checkpoints cleaned up
        """
        checkpoints = self.list_checkpoints()

        if len(checkpoints) <= keep_latest:
            return 0

        # Remove oldest checkpoints
        checkpoints_to_remove = checkpoints[keep_latest:]
        removed_count = 0

        for checkpoint in checkpoints_to_remove:
            checkpoint_file = self.checkpoints_dir / f"{checkpoint['checkpoint_id']}.json"
            try:
                checkpoint_file.unlink()
                removed_count += 1
                logger.info(f"✓ Removed old checkpoint {checkpoint['checkpoint_id']}")
            except Exception as e:
                logger.warning(f"Failed to remove checkpoint {checkpoint['checkpoint_id']}: {e}")

        return removed_count


class StagingLayer:
    """
    Staging layer for Extract → Transform pipeline with deduplication and resilience
    """

    def __init__(self, config: StagingConfig, checkpoint_manager: Optional[CheckpointManager] = None):
        """
        Initialize staging layer

        Args:
            config: Staging configuration
            checkpoint_manager: Optional checkpoint manager (will create if None)
        """
        self.config = config
        self.staging_directory = Path(config.staging_directory)
        self.staging_directory.mkdir(parents=True, exist_ok=True)

        # Initialize checkpoint manager
        self.checkpoint_manager = checkpoint_manager or CheckpointManager(self.staging_directory)

        # Staging state
        self.processed_ids: Set[str] = set()
        self.current_batch: List[StagedSubmission] = []

        # Initialize persistence
        if config.enable_persistence:
            self._load_processed_state()

        logger.info(f"✓ Staging layer initialized in {self.staging_directory}")

    def _generate_content_hash(self, submission: RedditSubmission) -> str:
        """
        Generate content hash for deduplication

        Args:
            submission: Reddit submission

        Returns:
            Content hash string
        """
        content = f"{submission.title}{submission.text}{submission.author}{submission.permalink}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _validate_submission(self, submission: RedditSubmission) -> None:
        """
        Validate submission before staging

        Args:
            submission: Submission to validate

        Raises:
            ValueError: If submission is invalid
        """
        try:
            # Pydantic validation
            submission.model_validate(submission.model_dump())

            # Additional business logic validation
            if not submission.id or len(submission.id) < 3:
                raise ValueError("Invalid submission ID")

            if not submission.title or len(submission.title.strip()) == 0:
                raise ValueError("Invalid submission title")

            if not submission.permalink or not submission.permalink.startswith('https://reddit.com/'):
                raise ValueError("Invalid submission permalink")

        except ValidationError as e:
            raise ValueError(f"Invalid submission data: {e}")
        except Exception as e:
            raise ValueError(f"Invalid submission data: {e}")

    def _save_batch(self, batch_id: str, submissions: List[StagedSubmission]) -> None:
        """
        Save batch data to disk

        Args:
            batch_id: Batch identifier
            submissions: List of staged submissions
        """
        if not self.config.enable_persistence:
            return

        batch_file = self.staging_directory / "batches" / f"{batch_id}.json"
        batch_file.parent.mkdir(exist_ok=True)

        batch_data = {
            'batch_id': batch_id,
            'timestamp': datetime.now(UTC).isoformat(),
            'submissions': [submission.model_dump() for submission in submissions]
        }

        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, default=str)

    def _load_batch(self, batch_id: str) -> List[StagedSubmission]:
        """
        Load batch data from disk

        Args:
            batch_id: Batch identifier

        Returns:
            List of staged submissions
        """
        if not self.config.enable_persistence:
            return []

        batch_file = self.staging_directory / "batches" / f"{batch_id}.json"

        if not batch_file.exists():
            raise FileNotFoundError(f"Batch {batch_id} not found")

        with open(batch_file, 'r', encoding='utf-8') as f:
            batch_data = json.load(f)

        submissions = []
        for sub_data in batch_data['submissions']:
            submission = StagedSubmission.model_validate(sub_data)
            submissions.append(submission)

        return submissions

    def _save_processed_state(self) -> None:
        """Save processed IDs state to disk"""
        if not self.config.enable_persistence:
            return

        state_file = self.staging_directory / "processed_state.json"
        state_data = {
            'processed_ids': list(self.processed_ids),
            'timestamp': datetime.now(UTC).isoformat()
        }

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2)

    def _load_processed_state(self) -> None:
        """Load processed IDs state from disk"""
        state_file = self.staging_directory / "processed_state.json"

        if not state_file.exists():
            return

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            self.processed_ids = set(state_data.get('processed_ids', []))
            logger.info(f"✓ Loaded {len(self.processed_ids)} processed IDs from state")
        except Exception as e:
            logger.warning(f"Failed to load processed state: {e}")
            self.processed_ids = set()

    def start_batch(self) -> str:
        """
        Start a new batch

        Returns:
            New batch ID
        """
        batch_id = str(uuid.uuid4())
        self.current_batch = []

        logger.info(f"✓ Started new batch: {batch_id}")
        return batch_id

    def add_to_batch(self, submission: RedditSubmission, batch_id: str) -> bool:
        """
        Add submission to current batch

        Args:
            submission: Reddit submission to add
            batch_id: Batch identifier

        Returns:
            True if added successfully, False if duplicate
        """
        # Validate submission
        self._validate_submission(submission)

        # Check for duplicates if enabled
        if self.config.deduplication_enabled:
            if submission.id in self.processed_ids:
                logger.debug(f"Skipping duplicate submission: {submission.id}")
                return False

        # Create staged submission
        content_hash = self._generate_content_hash(submission)
        staged_submission = StagedSubmission(
            submission=submission,
            batch_id=batch_id,
            content_hash=content_hash
        )

        self.current_batch.append(staged_submission)
        self.processed_ids.add(submission.id)

        # Checkpoint if interval reached
        if len(self.current_batch) % self.config.checkpoint_interval == 0:
            self.create_checkpoint(batch_id)

        return True

    def store_submissions(self, submissions: List[RedditSubmission]) -> Union[str, List[str]]:
        """
        Store submissions in staging with automatic batch management

        Args:
            submissions: List of Reddit submissions

        Returns:
            Batch ID or list of batch IDs if multiple batches created
        """
        if not submissions:
            return []

        batch_ids = []
        current_batch_id = self.start_batch()

        for submission in submissions:
            # Check batch size limits
            if len(self.current_batch) >= self.config.max_batch_size:
                # Finalize current batch
                self._finalize_batch(current_batch_id)
                batch_ids.append(current_batch_id)

                # Start new batch
                current_batch_id = self.start_batch()

            # Add to current batch
            self.add_to_batch(submission, current_batch_id)

        # Finalize last batch
        if self.current_batch:
            self._finalize_batch(current_batch_id)
            batch_ids.append(current_batch_id)

        # Save state
        self._save_processed_state()

        # Return single batch ID if only one, else list
        return batch_ids[0] if len(batch_ids) == 1 else batch_ids

    def _finalize_batch(self, batch_id: str) -> None:
        """
        Finalize and save current batch

        Args:
            batch_id: Batch identifier
        """
        if self.current_batch:
            self._save_batch(batch_id, self.current_batch)
            logger.info(f"✓ Finalized batch {batch_id} with {len(self.current_batch)} submissions")

    def get_batch(self, batch_id: str) -> List[RedditSubmission]:
        """
        Retrieve batch by ID

        Args:
            batch_id: Batch identifier

        Returns:
            List of Reddit submissions

        Raises:
            FileNotFoundError: If batch not found
        """
        staged_submissions = self._load_batch(batch_id)
        return [staged.submission for staged in staged_submissions]

    def list_batches(self) -> List[str]:
        """
        List all available batch IDs

        Returns:
            List of batch IDs
        """
        batches_dir = self.staging_directory / "batches"
        if not batches_dir.exists():
            return []

        batch_files = list(batches_dir.glob("*.json"))
        return [f.stem for f in batch_files]

    def create_checkpoint(self, batch_id: str) -> Dict[str, Any]:
        """
        Create checkpoint for current batch

        Args:
            batch_id: Batch identifier

        Returns:
            Checkpoint data
        """
        # Get current batch submissions
        staged_submissions = self.current_batch if self.current_batch else self._load_batch(batch_id)
        submission_ids = [staged.submission.id for staged in staged_submissions]

        checkpoint_data = {
            'batch_id': batch_id,
            'submission_ids': submission_ids,
            'metadata': {
                'processed_count': len(self.processed_ids),
                'batch_size': len(staged_submissions),
                'deduplication_enabled': self.config.deduplication_enabled
            }
        }

        checkpoint_id = self.checkpoint_manager.save_checkpoint(checkpoint_data)

        # Return full checkpoint data including timestamp
        full_checkpoint_data = self.checkpoint_manager.get_checkpoint(checkpoint_id)

        logger.info(f"✓ Created checkpoint {checkpoint_id} for batch {batch_id}")
        return full_checkpoint_data

    def recover_from_checkpoint(self, checkpoint_id: str) -> Optional[List[RedditSubmission]]:
        """
        Recover submissions from checkpoint

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            List of recovered submissions or None if recovery failed
        """
        checkpoint_data = self.checkpoint_manager.get_checkpoint(checkpoint_id)

        if not checkpoint_data:
            logger.error(f"Checkpoint {checkpoint_id} not found")
            return None

        try:
            batch_id = checkpoint_data['batch_id']

            # Try to get batch, fallback to current batch if not found
            try:
                submissions = self.get_batch(batch_id)
            except FileNotFoundError:
                # If batch file doesn't exist, check if it's in current batch
                if self.current_batch and self.current_batch[0].batch_id == batch_id:
                    submissions = [staged.submission for staged in self.current_batch]
                else:
                    logger.error(f"Batch {batch_id} not found for checkpoint {checkpoint_id}")
                    return None

            logger.info(f"✓ Recovered {len(submissions)} submissions from checkpoint {checkpoint_id}")
            return submissions

        except Exception as e:
            logger.error(f"Failed to recover from checkpoint {checkpoint_id}: {e}")
            return None

    def rollback_batch(self, batch_id: str) -> bool:
        """
        Rollback and remove a batch

        Args:
            batch_id: Batch identifier

        Returns:
            True if rollback successful
        """
        try:
            # Remove batch file
            batch_file = self.staging_directory / "batches" / f"{batch_id}.json"
            if batch_file.exists():
                batch_file.unlink()

            # Remove related checkpoints
            checkpoints = self.checkpoint_manager.list_checkpoints()
            for checkpoint in checkpoints:
                if checkpoint['batch_id'] == batch_id:
                    checkpoint_file = self.checkpoint_manager.checkpoints_dir / f"{checkpoint['checkpoint_id']}.json"
                    if checkpoint_file.exists():
                        checkpoint_file.unlink()

            # Clear current batch if it matches the rolled back batch
            if self.current_batch and self.current_batch[0].batch_id == batch_id:
                self.current_batch.clear()

            logger.info(f"✓ Rolled back batch {batch_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback batch {batch_id}: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get staging layer statistics

        Returns:
            Statistics dictionary
        """
        batch_count = len(self.list_batches())
        checkpoint_count = len(self.checkpoint_manager.list_checkpoints())

        return {
            'processed_submissions': len(self.processed_ids),
            'active_batches': batch_count,
            'available_checkpoints': checkpoint_count,
            'current_batch_size': len(self.current_batch),
            'staging_directory': str(self.staging_directory),
            'deduplication_enabled': self.config.deduplication_enabled,
            'max_batch_size': self.config.max_batch_size
        }