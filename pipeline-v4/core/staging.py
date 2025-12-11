"""
Simple staging layer for deduplication before analysis
Uses JSON file for state persistence with in-memory caching
"""

import json
import logging
from pathlib import Path

from models.reddit import RedditSubmission

logger = logging.getLogger(__name__)


class StagingLayer:
    """
    Simple staging layer for deduplication with JSON state persistence

    Key features:
    - JSON file state persistence in pipeline_staging/processed.json
    - In-memory processed_ids set for fast lookups
    - is_duplicate() method to check if submission was processed
    - checkpoint() method to mark submissions as processed
    - clear() method to reset all state
    - Auto-creation of staging directory
    """

    def __init__(self, staging_dir: str = "pipeline_staging"):
        """
        Initialize staging layer

        Args:
            staging_dir: Directory for staging state files
        """
        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)

        # JSON file for persistence
        self.state_file = self.staging_dir / "processed.json"

        # In-memory cache for fast lookups
        self.processed_ids: set[str] = set()

        # Load existing state if available
        self._load_state()

        logger.info(f"✓ Staging layer initialized with {len(self.processed_ids)} processed IDs")

    def _load_state(self) -> None:
        """Load processed IDs from JSON file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, encoding='utf-8') as f:
                    state_data = json.load(f)
                    self.processed_ids = set(state_data.get('processed_ids', []))
                logger.info(f"✓ Loaded {len(self.processed_ids)} processed IDs from {self.state_file}")
            else:
                logger.info(f"✓ No existing state file at {self.state_file}, starting fresh")
        except Exception as e:
            logger.warning(f"Failed to load staging state: {e}, starting fresh")
            self.processed_ids = set()

    def _save_state(self) -> None:
        """Save processed IDs to JSON file"""
        try:
            state_data = {
                'processed_ids': list(self.processed_ids),
                'count': len(self.processed_ids)
            }

            # Write to temporary file first, then rename to avoid corruption
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2)

            temp_file.rename(self.state_file)
            logger.debug(f"✓ Saved {len(self.processed_ids)} processed IDs to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save staging state: {e}")

    def is_duplicate(self, submission: RedditSubmission) -> bool:
        """
        Check if submission has already been processed

        Args:
            submission: Reddit submission to check

        Returns:
            True if submission was already processed, False otherwise
        """
        return submission.id in self.processed_ids

    def checkpoint(self, submissions: list[RedditSubmission]) -> None:
        """
        Mark submissions as processed by adding their IDs to the state

        Args:
            submissions: List of submissions to mark as processed
        """
        new_ids = [s.id for s in submissions if s.id not in self.processed_ids]

        if new_ids:
            self.processed_ids.update(new_ids)
            self._save_state()
            logger.info(f"✓ Checkpointed {len(new_ids)} new submissions (total: {len(self.processed_ids)})")
        else:
            logger.debug("✓ No new submissions to checkpoint")

    def checkpoint_single(self, submission: RedditSubmission) -> None:
        """
        Mark a single submission as processed

        Args:
            submission: Submission to mark as processed
        """
        if submission.id not in self.processed_ids:
            self.processed_ids.add(submission.id)
            self._save_state()
            logger.debug(f"✓ Checkpointed submission {submission.id}")

    def clear(self) -> None:
        """
        Clear all staging state
        Removes all processed IDs and deletes the state file
        """
        count = len(self.processed_ids)
        self.processed_ids.clear()

        try:
            if self.state_file.exists():
                self.state_file.unlink()
                logger.info(f"✓ Deleted staging state file: {self.state_file}")
        except Exception as e:
            logger.warning(f"Failed to delete staging state file: {e}")

        logger.info(f"✓ Cleared staging state (removed {count} processed IDs)")

    def get_statistics(self) -> dict:
        """
        Get staging layer statistics

        Returns:
            Dictionary with staging statistics
        """
        return {
            'processed_count': len(self.processed_ids),
            'staging_directory': str(self.staging_dir),
            'state_file': str(self.state_file),
            'state_file_exists': self.state_file.exists()
        }
