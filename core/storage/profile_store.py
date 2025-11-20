"""Profile storage service for enriched Reddit submissions."""

import logging
from typing import Dict, Any, List, Optional

from .dlt_loader import DLTLoader, LoadStatistics
from core.dlt import PK_SUBMISSION_ID

logger = logging.getLogger(__name__)


class ProfileStore:
    """Storage service for enriched Reddit submission profiles.

    Manages storage of Reddit submissions enriched with AI-generated profiles,
    trust scores, market validation, and other enrichment data.
    """

    def __init__(
        self,
        loader: Optional[DLTLoader] = None,
        table_name: str = "submissions",
    ):
        """Initialize ProfileStore.

        Args:
            loader: DLTLoader instance (creates new one if not provided)
            table_name: Target table name (default: "submissions")
        """
        self.loader = loader or DLTLoader()
        self.table_name = table_name
        self.primary_key = PK_SUBMISSION_ID
        self.stats = LoadStatistics()
        logger.info(
            f"ProfileStore initialized (table={table_name}, pk={self.primary_key})"
        )

    def store(self, profiles: List[Dict[str, Any]]) -> bool:
        """Store enriched submission profiles with merge disposition.

        Uses merge disposition to prevent duplicate records based on submission_id.

        Args:
            profiles: List of enriched submission dictionaries with fields:
                - submission_id (required)
                - title (required)
                - selftext (optional)
                - author (optional)
                - subreddit (optional)
                - ai_profile (optional - AI-generated profile data)
                - trust_score (optional - trust validation score)
                - market_validation (optional - market validation results)
                - opportunity_score (optional - opportunity analysis score)

        Returns:
            True if successful, False otherwise

        Example:
            >>> store = ProfileStore()
            >>> profiles = [{
            ...     "submission_id": "xyz789",
            ...     "title": "Looking for feedback on my idea",
            ...     "selftext": "I want to build...",
            ...     "author": "user123",
            ...     "subreddit": "Entrepreneur",
            ...     "ai_profile": {...},
            ...     "trust_score": 85.5,
            ...     "opportunity_score": 72.0
            ... }]
            >>> store.store(profiles)
            True
        """
        if not profiles:
            logger.warning("No profiles to store")
            return False

        # Filter to only profiles with submission_id
        valid_profiles = [prof for prof in profiles if prof.get("submission_id")]

        if not valid_profiles:
            logger.warning("No valid profiles found (all missing submission_id)")
            self.stats.skipped += len(profiles)
            return False

        logger.info(f"Storing {len(valid_profiles)} profiles to {self.table_name}")

        # Fix field mapping: reddit_id -> submission_id for DLT storage compatibility
        mapped_profiles = []
        for prof in valid_profiles:
            mapped_prof = prof.copy()
            # Map reddit_id to submission_id for DLT primary key compatibility
            if 'reddit_id' in mapped_prof and 'submission_id' not in mapped_prof:
                mapped_prof['submission_id'] = mapped_prof['reddit_id']
                # Keep reddit_id for the submissions table as it's the actual Reddit identifier
            mapped_profiles.append(mapped_prof)

        success = self.loader.load(
            data=mapped_profiles,
            table_name=self.table_name,
            write_disposition="merge",
            primary_key=self.primary_key,
        )

        # Update statistics
        if success:
            self.stats.loaded += len(valid_profiles)
            self.stats.total_attempted += len(profiles)
            logger.info(f"Successfully stored {len(valid_profiles)} profiles")
        else:
            self.stats.failed += len(valid_profiles)
            self.stats.total_attempted += len(profiles)
            self.stats.errors.append(f"Failed to store {len(valid_profiles)} profiles")
            logger.error(f"Failed to store profiles to {self.table_name}")

        # Track skipped
        skipped_count = len(profiles) - len(valid_profiles)
        if skipped_count > 0:
            self.stats.skipped += skipped_count
            logger.debug(f"Skipped {skipped_count} invalid profiles")

        return success

    def store_batch(
        self, profiles: List[Dict[str, Any]], batch_size: int = 100
    ) -> Dict[str, Any]:
        """Store profiles in batches for large datasets.

        Args:
            profiles: List of enriched submission dictionaries
            batch_size: Number of records per batch (default: 100)

        Returns:
            Dictionary with batch processing results

        Example:
            >>> store = ProfileStore()
            >>> profiles = [...]  # Large list
            >>> results = store.store_batch(profiles, batch_size=50)
            >>> print(results['success_rate'])
            1.0
        """
        if not profiles:
            logger.warning("No profiles to store in batch")
            return {
                "total_records": 0,
                "batches": 0,
                "successful_batches": 0,
                "failed_batches": 0,
                "success_rate": 0.0,
            }

        # Filter to valid profiles
        valid_profiles = [prof for prof in profiles if prof.get("submission_id")]

        if not valid_profiles:
            logger.warning("No valid profiles for batch storage")
            return {
                "total_records": len(profiles),
                "batches": 0,
                "successful_batches": 0,
                "failed_batches": 0,
                "success_rate": 0.0,
            }

        logger.info(
            f"Batch storing {len(valid_profiles)} profiles (batch_size={batch_size})"
        )

        result = self.loader.load_batch(
            data=valid_profiles,
            table_name=self.table_name,
            primary_key=self.primary_key,
            batch_size=batch_size,
            write_disposition="merge",
        )

        # Update statistics
        self.stats.loaded += result.get("loaded", 0)
        self.stats.failed += result.get("failed", 0)
        self.stats.total_attempted += len(valid_profiles)

        logger.info(
            f"Batch storage complete: {result['successful_batches']}/{result['batches']} batches"
        )

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with loaded, failed, skipped counts and success rate
        """
        return self.stats.get_summary()

    def reset_statistics(self) -> None:
        """Reset storage statistics."""
        self.stats = LoadStatistics()
        logger.debug("Statistics reset")
