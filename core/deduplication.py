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
