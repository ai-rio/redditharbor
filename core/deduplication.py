"""
RedditHarbor Semantic Deduplication Engine
Phase 1: String-based deduplication (no ML dependencies)

Task 2 Implementation: SimpleDeduplicator class with fingerprint generation.
This module provides basic deduplication functionality using normalized concept
fingerprints to identify duplicate business concepts from Reddit data.
"""

import hashlib
import logging

try:
    from supabase import Client, create_client
except ImportError:
    Client = None
    create_client = None

logger = logging.getLogger(__name__)


class SimpleDeduplicator:
    """
    Phase 1: String-based deduplication using normalized concept fingerprints.
    No ML dependencies - fast, simple, effective for ~40-50% duplicates.

    This class provides core functionality for:
    - Normalizing business concept text
    - Generating SHA256 fingerprints for deduplication
    - Integration with Supabase for storage and retrieval
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize with Supabase client.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key

        Raises:
            ImportError: If supabase package is not installed
            Exception: If Supabase client creation fails
        """
        if create_client is None:
            raise ImportError(
                "supabase package is required. Install with: pip install supabase"
            )

        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info(f"SimpleDeduplicator initialized with Supabase URL: {supabase_url}")

    def normalize_concept(self, concept: str) -> str:
        """
        Normalize business concept for fingerprinting.

        This method standardizes text by:
        - Converting to lowercase
        - Removing common app-related prefixes
        - Normalizing whitespace
        - Stripping leading/trailing spaces

        Args:
            concept: Raw business concept text

        Returns:
            Normalized concept string
        """
        if not concept:
            return ""

        # Convert to lowercase and strip whitespace
        normalized = concept.lower().strip()

        # Remove common variations and prefixes
        # Order matters: handle specific cases first
        normalized = normalized.replace("app idea:", "idea:")
        normalized = normalized.replace("mobile app", "app")
        normalized = normalized.replace("web app", "app")
        # Only remove standalone "app:" at the beginning
        if normalized.startswith("app:"):
            normalized = normalized[4:]  # Remove "app:" prefix

        # Remove extra whitespace (multiple spaces to single space)
        normalized = " ".join(normalized.split())

        return normalized

    def generate_fingerprint(self, concept: str) -> str:
        """
        Generate SHA256 fingerprint from normalized concept.

        Args:
            concept: Business concept text

        Returns:
            SHA256 hash as hexadecimal string
        """
        normalized = self.normalize_concept(concept)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def find_existing_concept(self, fingerprint: str) -> dict | None:
        """
        Check if business concept already exists in database.

        Args:
            fingerprint: SHA256 fingerprint to search for

        Returns:
            Dictionary with concept data if found, None otherwise
        """
        try:
            response = (
                self.supabase.table("business_concepts")
                .select("*")
                .eq("fingerprint", fingerprint)
                .execute()
            )

            if response.data and len(response.data) > 0:
                fp_prefix = fingerprint[:8]
                logger.info(f"Found existing concept for fingerprint: {fp_prefix}...")
                return response.data[0]
            else:
                fp_prefix = fingerprint[:8]
                logger.debug(
                    f"No existing concept found for fingerprint: {fp_prefix}..."
                )
                return None

        except Exception as e:
            fp_prefix = fingerprint[:8]
            logger.error(
                f"Error finding existing concept for fingerprint {fp_prefix}...: {e}"
            )
            return None

    def create_business_concept(
        self, concept_name: str, fingerprint: str, opportunity_id: str
    ) -> int | None:
        """
        Create new business concept in database.

        Args:
            concept_name: Normalized business concept name
            fingerprint: SHA256 fingerprint of the concept
            opportunity_id: ID of the opportunity that created this concept

        Returns:
            ID of the created concept if successful, None otherwise
        """
        try:
            concept_data = {
                "concept_name": concept_name,
                "fingerprint": fingerprint,
                "opportunity_id": opportunity_id,
                "opportunity_count": 1,  # Start with 1 opportunity
            }

            response = (
                self.supabase.table("business_concepts").insert(concept_data).execute()
            )

            if response.data and len(response.data) > 0:
                concept_id = response.data[0].get("id")
                name_preview = concept_name[:50]
                logger.info(
                    f"Created new business concept '{name_preview}...' with ID: "
                    f"{concept_id}"
                )
                return concept_id
            else:
                name_preview = concept_name[:50]
                logger.error(f"Failed to create business concept '{name_preview}...'")
                return None

        except Exception as e:
            name_preview = concept_name[:50]
            logger.error(f"Error creating business concept '{name_preview}...': {e}")
            return None

    def update_concept_stats(self, concept_id: int) -> None:
        """
        Update concept statistics in database.

        Args:
            concept_id: ID of the concept to update
        """
        try:
            # Call database function to update opportunity count
            response = self.supabase.rpc(
                "update_concept_stats", {"concept_id": concept_id}
            ).execute()

            if response.data:
                logger.info(f"Updated stats for concept ID: {concept_id}")
            else:
                logger.warning(
                    f"No data returned when updating stats for concept ID: {concept_id}"
                )

        except Exception as e:
            logger.error(f"Error updating concept stats for ID {concept_id}: {e}")

    def mark_as_duplicate(
        self, opportunity_id: str, concept_id: int, primary_opportunity_id: str
    ) -> bool:
        """
        Mark an opportunity as a duplicate.

        Args:
            opportunity_id: ID of the opportunity to mark as duplicate
            concept_id: ID of the business concept it belongs to
            primary_opportunity_id: ID of the primary/original opportunity

        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "concept_id": concept_id,
                "is_duplicate": True,
                "primary_opportunity_id": primary_opportunity_id,
                "deduplication_status": "duplicate",
            }

            response = (
                self.supabase.table("opportunities")
                .update(update_data)
                .eq("opportunity_id", opportunity_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                msg = (
                    f"Marked opportunity {opportunity_id} as duplicate of "
                    f"{primary_opportunity_id}"
                )
                logger.info(msg)
                return True
            else:
                logger.error(
                    f"Failed to mark opportunity {opportunity_id} as duplicate"
                )
                return False

        except Exception as e:
            logger.error(
                f"Error marking opportunity {opportunity_id} as duplicate: {e}"
            )
            return False

    def mark_as_unique(self, opportunity_id: str, concept_id: int) -> bool:
        """
        Mark an opportunity as unique (original).

        Args:
            opportunity_id: ID of the opportunity to mark as unique
            concept_id: ID of the business concept it belongs to

        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "concept_id": concept_id,
                "is_duplicate": False,
                "primary_opportunity_id": None,
                "deduplication_status": "unique",
            }

            response = (
                self.supabase.table("opportunities")
                .update(update_data)
                .eq("opportunity_id", opportunity_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                logger.info(f"Marked opportunity {opportunity_id} as unique")
                return True
            else:
                logger.error(f"Failed to mark opportunity {opportunity_id} as unique")
                return False

        except Exception as e:
            logger.error(f"Error marking opportunity {opportunity_id} as unique: {e}")
            return False


# Future extension methods (to be implemented in later tasks)
# These are commented out as they're not part of Task 2 requirements

# def find_existing_concept(self, fingerprint: str) -> Optional[dict]:
#     """Check if business concept already exists in database."""
#     pass

# def create_business_concept(
#     self, concept_name: str, fingerprint: str, opportunity_id: str
# ) -> Optional[int]:
#     """Create new business concept in database."""
#     pass

# def process_opportunity(self, opportunity: dict) -> dict:
#     """Process single opportunity for deduplication."""
#     pass
