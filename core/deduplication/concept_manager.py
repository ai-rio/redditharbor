"""Business concept management for deduplication.

This module provides unified management of business concepts for semantic
deduplication. Extracted from batch_opportunity_scoring.py to centralize
concept lookup and analysis status tracking.

Key Features:
- Get or create business concepts
- Track analysis status (Agno, Profiler)
- Query concepts by submission ID
- Update concept metadata
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BusinessConceptManager:
    """
    Manage business concepts for semantic deduplication.

    Business concepts group semantically similar submissions together to
    enable analysis deduplication and cost savings. This class provides
    unified access to concept management operations.

    Attributes:
        client: Initialized Supabase client
        table: Name of business_concepts table

    Examples:
        >>> from supabase import create_client
        >>> client = create_client(url, key)
        >>> manager = BusinessConceptManager(client)
        >>> concept = manager.get_or_create_concept(
        ...     submission_id='abc123',
        ...     concept_text='Project management tool'
        ... )
        >>> manager.update_analysis_status(concept['id'], 'agno', True)
    """

    def __init__(self, supabase_client: Any):
        """
        Initialize business concept manager.

        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client
        self.table = "business_concepts"

    def get_or_create_concept(
        self, submission_id: str, concept_text: str
    ) -> Optional[dict[str, Any]]:
        """
        Get existing concept or create new one.

        Looks up concept by primary_submission_id. If not found, creates
        a new concept with default analysis flags set to False.

        Args:
            submission_id: Primary submission ID for the concept
            concept_text: Text description of the business concept

        Returns:
            dict: Business concept record with all fields, or None if failed
                Contains: id, primary_submission_id, concept_text,
                has_agno_analysis, has_profiler_analysis, submission_count

        Examples:
            >>> concept = manager.get_or_create_concept('sub123', 'Fitness tracker')
            >>> assert concept['primary_submission_id'] == 'sub123'
            >>> assert concept['has_agno_analysis'] is False
        """
        try:
            # Try to find existing concept
            response = (
                self.client.table(self.table)
                .select("*")
                .eq("primary_submission_id", submission_id)
                .execute()
            )

            if response.data:
                logger.debug(f"Found existing concept for submission {submission_id}")
                return response.data[0]

            # Create new concept
            new_concept = {
                "primary_submission_id": submission_id,
                "concept_text": concept_text,
                "has_agno_analysis": False,
                "has_profiler_analysis": False,
                "submission_count": 1,
            }

            response = self.client.table(self.table).insert(new_concept).execute()

            if response.data:
                logger.info(
                    f"Created new business concept for submission {submission_id}"
                )
                return response.data[0]

            logger.warning(
                f"Failed to create concept for submission {submission_id}: No data returned"
            )
            return None

        except Exception as e:
            logger.error(f"Error in get_or_create_concept for {submission_id}: {e}")
            return None

    def update_analysis_status(
        self, concept_id: int, analysis_type: str, status: bool = True
    ) -> bool:
        """
        Update analysis status flag for concept.

        Sets the has_agno_analysis or has_profiler_analysis flag for a
        business concept. Used to track which analyses have been completed.

        Args:
            concept_id: ID of the business concept
            analysis_type: Type of analysis ('agno' or 'profiler')
            status: Status value to set (default: True)

        Returns:
            bool: True if update succeeded, False otherwise

        Raises:
            ValueError: If analysis_type is not 'agno' or 'profiler'

        Examples:
            >>> manager.update_analysis_status(42, 'agno', True)
            True
            >>> manager.update_analysis_status(42, 'profiler', False)
            True
        """
        try:
            field_map = {
                "agno": "has_agno_analysis",
                "profiler": "has_profiler_analysis",
            }

            field = field_map.get(analysis_type)
            if not field:
                raise ValueError(
                    f"Unknown analysis type: {analysis_type}. "
                    f"Must be 'agno' or 'profiler'"
                )

            self.client.table(self.table).update({field: status}).eq(
                "id", concept_id
            ).execute()

            logger.debug(f"Updated {analysis_type} status to {status} for concept {concept_id}")
            return True

        except ValueError:
            raise  # Re-raise ValueError for invalid analysis type
        except Exception as e:
            logger.error(
                f"Error updating analysis status for concept {concept_id}: {e}"
            )
            return False

    def get_concept_for_submission(
        self, submission_id: str
    ) -> Optional[dict[str, Any]]:
        """
        Get business concept associated with submission.

        Looks up concept by checking both primary_submission_id and
        related_submissions array. This handles both primary submissions
        and duplicate submissions.

        Args:
            submission_id: Submission ID to look up

        Returns:
            dict: Business concept record, or None if not found

        Examples:
            >>> concept = manager.get_concept_for_submission('sub123')
            >>> if concept:
            ...     print(f"Concept ID: {concept['id']}")
        """
        try:
            # Query by primary_submission_id OR related_submissions contains ID
            response = (
                self.client.table(self.table)
                .select("*")
                .or_(
                    f"primary_submission_id.eq.{submission_id},"
                    f"related_submissions.cs.{{{submission_id}}}"
                )
                .execute()
            )

            if response.data:
                return response.data[0]

            logger.debug(f"No concept found for submission {submission_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting concept for submission {submission_id}: {e}")
            return None

    def get_concept_by_id(self, concept_id: int) -> Optional[dict[str, Any]]:
        """
        Get business concept by ID.

        Direct lookup of concept by its unique ID.

        Args:
            concept_id: ID of the business concept

        Returns:
            dict: Business concept record, or None if not found

        Examples:
            >>> concept = manager.get_concept_by_id(42)
            >>> assert concept['id'] == 42
        """
        try:
            response = (
                self.client.table(self.table).select("*").eq("id", concept_id).execute()
            )

            if response.data:
                return response.data[0]

            logger.debug(f"No concept found with ID {concept_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting concept by ID {concept_id}: {e}")
            return None

    def increment_submission_count(self, concept_id: int) -> bool:
        """
        Increment submission count for a concept.

        Increments the submission_count field to track how many submissions
        are grouped under this concept.

        Args:
            concept_id: ID of the business concept

        Returns:
            bool: True if increment succeeded, False otherwise

        Examples:
            >>> manager.increment_submission_count(42)
            True
        """
        try:
            # Get current count
            concept = self.get_concept_by_id(concept_id)
            if not concept:
                logger.warning(
                    f"Cannot increment count: Concept {concept_id} not found"
                )
                return False

            new_count = concept.get("submission_count", 0) + 1

            self.client.table(self.table).update({"submission_count": new_count}).eq(
                "id", concept_id
            ).execute()

            logger.debug(f"Incremented submission count to {new_count} for concept {concept_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error incrementing submission count for concept {concept_id}: {e}"
            )
            return False
