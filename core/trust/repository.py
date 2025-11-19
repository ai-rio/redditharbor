"""
Trust Validation System - Repository Pattern

Abstract data access layer for trust validation operations.
This repository provides a clean interface to trust data storage
and handles all database-specific operations.

Usage:
    from core.trust.repository import TrustRepository
    from core.trust.models import TrustIndicators

    repository = TrustRepository(supabase_client)
    indicators = repository.get_trust_indicators("submission_id_123")
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from core.trust.config import (
    CORE_TRUST_COLUMNS,
    ENGAGEMENT_COLUMNS,
    METADATA_COLUMNS,
    QUALITY_COLUMNS,
    TrustColumns,
    TrustTables,
)
from core.trust.models import TrustIndicators

logger = logging.getLogger(__name__)


class TrustRepositoryInterface(ABC):
    """Abstract interface for trust data operations."""

    @abstractmethod
    def get_trust_indicators(self, submission_id: str) -> TrustIndicators | None:
        """Get trust indicators for a submission."""
        pass

    @abstractmethod
    def save_trust_indicators(self, submission_id: str, indicators: TrustIndicators) -> bool:
        """Save trust indicators for a submission."""
        pass

    @abstractmethod
    def update_trust_indicators(self, submission_id: str, updates: dict[str, Any]) -> bool:
        """Update specific trust indicators."""
        pass

    @abstractmethod
    def get_batch_trust_indicators(self, submission_ids: list[str]) -> dict[str, TrustIndicators]:
        """Get trust indicators for multiple submissions."""
        pass

    @abstractmethod
    def delete_trust_indicators(self, submission_id: str) -> bool:
        """Delete trust indicators for a submission."""
        pass

    @abstractmethod
    def exists_trust_indicators(self, submission_id: str) -> bool:
        """Check if trust indicators exist for a submission."""
        pass


class SupabaseTrustRepository(TrustRepositoryInterface):
    """Supabase implementation of trust repository."""

    def __init__(self, supabase_client):
        """Initialize with Supabase client."""
        self.client = supabase_client
        self.default_table = TrustTables.APP_OPPORTUNITIES

    def get_trust_indicators(self, submission_id: str) -> TrustIndicators | None:
        """Get trust indicators for a submission."""
        try:
            # Try app_opportunities table first (primary storage)
            result = self.client.table(self.default_table).select(
                *CORE_TRUST_COLUMNS,
                *ENGAGEMENT_COLUMNS,
                *QUALITY_COLUMNS,
                *METADATA_COLUMNS
            ).eq(TrustColumns.SUBMISSION_ID, submission_id).execute()

            if result.data:
                return self._dict_to_indicators(result.data[0])

            # Fallback to submissions table
            result = self.client.table(TrustTables.SUBMISSIONS).select(
                TrustColumns.TRUST_SCORE,
                TrustColumns.TRUST_BADGE
            ).eq(TrustColumns.SUBMISSION_ID, submission_id).execute()

            if result.data:
                return self._dict_to_indicators(result.data[0])

            logger.warning(f"No trust indicators found for submission_id: {submission_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting trust indicators for {submission_id}: {e}")
            return None

    def save_trust_indicators(self, submission_id: str, indicators: TrustIndicators) -> bool:
        """Save trust indicators for a submission."""
        try:
            trust_data = indicators.to_dict()
            trust_data[TrustColumns.SUBMISSION_ID] = submission_id

            # Use upsert to handle both insert and update
            result = self.client.table(self.default_table).upsert(
                trust_data,
                on_conflict=TrustColumns.SUBMISSION_ID
            ).execute()

            if result.data:
                logger.info(f"Saved trust indicators for {submission_id}")
                return True
            else:
                logger.error(f"Failed to save trust indicators for {submission_id}")
                return False

        except Exception as e:
            logger.error(f"Error saving trust indicators for {submission_id}: {e}")
            return False

    def update_trust_indicators(self, submission_id: str, updates: dict[str, Any]) -> bool:
        """Update specific trust indicators."""
        try:
            result = self.client.table(self.default_table).update(
                updates
            ).eq(TrustColumns.SUBMISSION_ID, submission_id).execute()

            if result.data:
                logger.info(f"Updated trust indicators for {submission_id}")
                return True
            else:
                logger.warning(f"No records updated for {submission_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating trust indicators for {submission_id}: {e}")
            return False

    def get_batch_trust_indicators(self, submission_ids: list[str]) -> dict[str, TrustIndicators]:
        """Get trust indicators for multiple submissions."""
        try:
            # Build IN clause query
            result = self.client.table(self.default_table).select(
                TrustColumns.SUBMISSION_ID,
                *CORE_TRUST_COLUMNS,
                *ENGAGEMENT_COLUMNS,
                *QUALITY_COLUMNS,
                *METADATA_COLUMNS
            ).in_(TrustColumns.SUBMISSION_ID, submission_ids).execute()

            indicators_map = {}
            for row in result.data:
                submission_id = row[TrustColumns.SUBMISSION_ID]
                indicators_map[submission_id] = self._dict_to_indicators(row)

            logger.info(f"Retrieved {len(indicators_map)} trust indicators for batch request")
            return indicators_map

        except Exception as e:
            logger.error(f"Error getting batch trust indicators: {e}")
            return {}

    def delete_trust_indicators(self, submission_id: str) -> bool:
        """Delete trust indicators for a submission."""
        try:
            result = self.client.table(self.default_table).delete().eq(
                TrustColumns.SUBMISSION_ID, submission_id
            ).execute()

            if result.data:
                logger.info(f"Deleted trust indicators for {submission_id}")
                return True
            else:
                logger.warning(f"No records deleted for {submission_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting trust indicators for {submission_id}: {e}")
            return False

    def exists_trust_indicators(self, submission_id: str) -> bool:
        """Check if trust indicators exist for a submission."""
        try:
            result = self.client.table(self.default_table).select(
                TrustColumns.SUBMISSION_ID
            ).eq(TrustColumns.SUBMISSION_ID, submission_id).execute()

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error checking trust indicators existence for {submission_id}: {e}")
            return False

    def _dict_to_indicators(self, data: dict[str, Any]) -> TrustIndicators:
        """Convert database dictionary to TrustIndicators model."""
        # Filter out None values and handle type conversion
        filtered_data = {}

        # Map all trust columns to model fields
        field_mapping = {
            TrustColumns.TRUST_SCORE: "trust_score",
            TrustColumns.TRUST_BADGE: "trust_badges",
            TrustColumns.TRUST_LEVEL: "trust_level",
            TrustColumns.ACTIVITY_SCORE: "activity_score",
            TrustColumns.ENGAGEMENT_LEVEL: "engagement_level",
            TrustColumns.TREND_VELOCITY: "trend_velocity",
            TrustColumns.PROBLEM_VALIDITY: "problem_validity",
            TrustColumns.DISCUSSION_QUALITY: "discussion_quality",
            TrustColumns.AI_CONFIDENCE_LEVEL: "ai_confidence_level",
            TrustColumns.VALIDATION_TIMESTAMP: "validation_timestamp",
            TrustColumns.VALIDATION_METHOD: "validation_method",
            TrustColumns.CONFIDENCE_SCORE: "confidence_score",
            TrustColumns.QUALITY_CONSTRAINTS_MET: "quality_constraints_met",
            TrustColumns.ACTIVITY_CONSTRAINTS_MET: "activity_constraints_met",
            TrustColumns.SUBREDDIT_ACTIVITY_SCORE: "subreddit_activity_score",
            TrustColumns.POST_ENGAGEMENT_SCORE: "post_engagement_score",
            TrustColumns.COMMUNITY_HEALTH_SCORE: "community_health_score",
            TrustColumns.TREND_VELOCITY_SCORE: "trend_velocity_score",
            TrustColumns.PROBLEM_VALIDITY_SCORE: "problem_validity_score",
            TrustColumns.DISCUSSION_QUALITY_SCORE: "discussion_quality_score",
            TrustColumns.AI_ANALYSIS_CONFIDENCE: "ai_analysis_confidence",
            TrustColumns.OVERALL_TRUST_SCORE: "overall_trust_score"
        }

        for db_column, model_field in field_mapping.items():
            if db_column in data and data[db_column] is not None:
                # Handle single trust_badge to list conversion
                if db_column == TrustColumns.TRUST_BADGE:
                    if isinstance(data[db_column], str):
                        filtered_data[model_field] = [data[db_column]]
                    elif isinstance(data[db_column], list):
                        filtered_data[model_field] = data[db_column]
                    else:
                        filtered_data[model_field] = []
                else:
                    filtered_data[model_field] = data[db_column]

        return TrustIndicators.from_dict(filtered_data)


class StagingTrustRepository(SupabaseTrustRepository):
    """Repository for staging table (public_staging schema)."""

    def __init__(self, supabase_client):
        """Initialize with staging table."""
        super().__init__(supabase_client)
        self.default_table = TrustTables.PUBLIC_STAGING_APP_OPPORTUNITIES


class TrustRepositoryFactory:
    """Factory for creating trust repositories with appropriate configuration."""

    @staticmethod
    def create_repository(supabase_client, table_name: str = None) -> TrustRepositoryInterface:
        """Create appropriate repository based on table name."""
        if table_name == TrustTables.PUBLIC_STAGING_APP_OPPORTUNITIES:
            return StagingTrustRepository(supabase_client)
        else:
            return SupabaseTrustRepository(supabase_client)

    @staticmethod
    def create_multi_table_repository(supabase_client) -> "MultiTableTrustRepository":
        """Create repository that can work with multiple tables."""
        return MultiTableTrustRepository(supabase_client)


class MultiTableTrustRepository(TrustRepositoryInterface):
    """Repository that can work with multiple trust tables."""

    def __init__(self, supabase_client):
        """Initialize with multiple table support."""
        self.client = supabase_client
        self.primary_table = TrustTables.APP_OPPORTUNITIES
        self.staging_table = TrustTables.PUBLIC_STAGING_APP_OPPORTUNITIES
        self.submissions_table = TrustTables.SUBMISSIONS

    def get_trust_indicators(self, submission_id: str) -> TrustIndicators | None:
        """Get trust indicators from any available table."""
        # Try primary table first
        indicators = self._get_from_table(submission_id, self.primary_table)
        if indicators:
            return indicators

        # Try staging table
        indicators = self._get_from_table(submission_id, self.staging_table)
        if indicators:
            return indicators

        # Try submissions table (limited fields)
        indicators = self._get_from_table(submission_id, self.submissions_table)
        if indicators:
            return indicators

        return None

    def save_trust_indicators(self, submission_id: str, indicators: TrustIndicators) -> bool:
        """Save trust indicators to primary table."""
        repo = SupabaseTrustRepository(self.client)
        return repo.save_trust_indicators(submission_id, indicators)

    def update_trust_indicators(self, submission_id: str, updates: dict[str, Any]) -> bool:
        """Update trust indicators in primary table."""
        repo = SupabaseTrustRepository(self.client)
        return repo.update_trust_indicators(submission_id, updates)

    def get_batch_trust_indicators(self, submission_ids: list[str]) -> dict[str, TrustIndicators]:
        """Get trust indicators from primary table."""
        repo = SupabaseTrustRepository(self.client)
        return repo.get_batch_trust_indicators(submission_ids)

    def delete_trust_indicators(self, submission_id: str) -> bool:
        """Delete trust indicators from primary table."""
        repo = SupabaseTrustRepository(self.client)
        return repo.delete_trust_indicators(submission_id)

    def exists_trust_indicators(self, submission_id: str) -> bool:
        """Check if trust indicators exist in any table."""
        return (
            self._exists_in_table(submission_id, self.primary_table) or
            self._exists_in_table(submission_id, self.staging_table) or
            self._exists_in_table(submission_id, self.submissions_table)
        )

    def _get_from_table(self, submission_id: str, table_name: str) -> TrustIndicators | None:
        """Get trust indicators from specific table."""
        try:
            columns = CORE_TRUST_COLUMNS + ENGAGEMENT_COLUMNS + QUALITY_COLUMNS + METADATA_COLUMNS

            # For submissions table, only select available columns
            if table_name == self.submissions_table:
                columns = [TrustColumns.TRUST_SCORE, TrustColumns.TRUST_BADGE]

            result = self.client.table(table_name).select(*columns).eq(
                TrustColumns.SUBMISSION_ID, submission_id
            ).execute()

            if result.data:
                repo = SupabaseTrustRepository(self.client)
                repo.default_table = table_name
                return repo._dict_to_indicators(result.data[0])

        except Exception as e:
            logger.debug(f"Could not get trust indicators from {table_name} for {submission_id}: {e}")

        return None

    def _exists_in_table(self, submission_id: str, table_name: str) -> bool:
        """Check if trust indicators exist in specific table."""
        try:
            result = self.client.table(table_name).select(
                TrustColumns.SUBMISSION_ID
            ).eq(TrustColumns.SUBMISSION_ID, submission_id).execute()

            return len(result.data) > 0

        except Exception:
            return False


# Repository decorator for caching and error handling
def repository_error_handler(func):
    """Decorator for repository error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Repository error in {func.__name__}: {e}")
            raise
    return wrapper
