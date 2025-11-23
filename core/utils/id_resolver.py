"""
RedditHarbor Canonical ID Resolver

Provides deterministic resolution of various ID formats to canonical UUIDs
for Reddit submissions, supporting multiple input formats and validation.

Author: Data Engineering Team
Date: 2025-11-23
Version: 1.0.0
"""

import re
import uuid
from dataclasses import dataclass, field
from re import Pattern
from typing import Any

# Constants
REDDITHARBOR_NAMESPACE: uuid.UUID = uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")
REDDIT_URL_PATTERN: Pattern[str] = re.compile(r'reddit\.com/comments/([a-zA-Z0-9]+)')
UUID_PATTERN: Pattern[str] = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


@dataclass
class ResolutionResult:
    """
    Result of ID resolution attempt containing canonical UUID and metadata.

    Attributes:
        canonical_id: Deterministic UUID for the input
        input_type: Type of input provided (uuid, reddit_id, synthetic_id, url, dict, unknown)
        extraction_method: Method used to extract ID (uuid_validation, url_parsing, dict_key, generation)
        reddit_id: Extracted Reddit base36 ID if available
        is_synthetic: Whether the ID was synthetically generated
        error: Error message if resolution failed
        metadata: Additional resolution metadata
    """
    canonical_id: str | None = None
    input_type: str = "unknown"
    extraction_method: str = "unknown"
    reddit_id: str | None = None
    is_synthetic: bool = False
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.

    Args:
        value: String to validate

    Returns:
        True if string is a valid UUID, False otherwise
    """
    if not value or not isinstance(value, str):
        return False
    return bool(UUID_PATTERN.match(value.strip()))


def extract_reddit_id_from_url(url: str) -> str | None:
    """
    Extract Reddit submission ID from a Reddit URL.

    Args:
        url: Reddit URL to parse

    Returns:
        Reddit submission ID if found, None otherwise
    """
    if not url or not isinstance(url, str):
        return None

    match = REDDIT_URL_PATTERN.search(url)
    return match.group(1) if match else None


def generate_deterministic_uuid(input_string: str) -> str:
    """
    Generate a deterministic UUID v5 from an input string.

    Args:
        input_string: String to generate UUID from

    Returns:
        Deterministic UUID string
    """
    if not input_string:
        raise ValueError("Input string cannot be empty for UUID generation")

    return str(uuid.uuid5(REDDITHARBOR_NAMESPACE, input_string.strip()))


def extract_id_from_dict(data: dict[str, Any]) -> tuple[str | None, str | None]:
    """
    Extract ID from dictionary using common key patterns.

    Args:
        data: Dictionary to extract ID from

    Returns:
        Tuple of (extracted_id, key_used) or (None, None) if not found
    """
    if not data or not isinstance(data, dict):
        return None, None

    # Try submission_id first, then reddit_id as fallback
    for key in ["submission_id", "reddit_id"]:
        if key in data:
            value = data[key]
            if value is not None and isinstance(value, str) and value.strip():
                return value.strip(), key

    return None, None


def resolve_submission_id(
    *,
    submission_id: str | dict[str, Any] | None = None,
    supabase_client: Any = None,  # Phase 1: ignored
    allow_generation: bool = True,
    use_cache: bool = True
) -> ResolutionResult:
    """
    Resolve various ID formats to canonical RedditHarbor UUID.

    Args:
        submission_id: Input ID in various formats (UUID, Reddit ID, URL, dict)
        supabase_client: Database client (Phase 1: ignored)
        allow_generation: Whether to generate synthetic IDs for unknown inputs
        use_cache: Whether to use caching (Phase 1: ignored)

    Returns:
        ResolutionResult containing canonical UUID and resolution metadata
    """
    result = ResolutionResult()

    try:
        # 1. Null/Empty Check
        if submission_id is None or (isinstance(submission_id, str) and not submission_id.strip()):
            result.error = "Empty or null submission ID provided"
            return result

        # Handle dictionary input
        if isinstance(submission_id, dict):
            result.input_type = "dict"
            extracted_id, key_used = extract_id_from_dict(submission_id)
            if extracted_id:
                result.extraction_method = f"dict_key_{key_used}"
                submission_id = extracted_id
                result.metadata["original_dict_keys"] = list(submission_id.keys()) if isinstance(submission_id, dict) else []
            else:
                result.error = "No valid ID found in dictionary (missing submission_id or reddit_id keys)"
                return result

        # At this point, submission_id should be a string
        if not isinstance(submission_id, str):
            result.error = f"Invalid input type: {type(submission_id)}. Expected str, uuid, or dict."
            return result

        submission_id = submission_id.strip()

        # 2. UUID Validation
        if is_valid_uuid(submission_id):
            result.input_type = "uuid"
            result.extraction_method = "uuid_validation"
            result.canonical_id = submission_id.lower()  # Normalize case
            return result

        # 3. URL Extraction
        reddit_id = extract_reddit_id_from_url(submission_id)
        if reddit_id:
            result.input_type = "url"
            result.extraction_method = "url_parsing"
            result.reddit_id = reddit_id
            result.canonical_id = generate_deterministic_uuid(f"reddit_id:{reddit_id}")
            return result

        # 4. Reddit ID Detection (base36 pattern)
        if re.match(r'^[a-zA-Z0-9]{6,7}$', submission_id):
            result.input_type = "reddit_id"
            result.extraction_method = "reddit_id_pattern"
            result.reddit_id = submission_id
            result.canonical_id = generate_deterministic_uuid(f"reddit_id:{submission_id}")
            return result

        # 5. Synthetic ID Detection (already has deterministic format)
        if submission_id.startswith('synthetic_') and len(submission_id) > 20:
            result.input_type = "synthetic_id"
            result.extraction_method = "synthetic_detection"
            result.canonical_id = generate_deterministic_uuid(f"synthetic:{submission_id}")
            result.is_synthetic = True
            return result

        # 6. UUID Generation for unknown valid inputs
        if allow_generation and len(submission_id) > 0:
            result.input_type = "unknown"
            result.extraction_method = "generation"
            result.canonical_id = generate_deterministic_uuid(f"unknown:{submission_id}")
            result.is_synthetic = True
            result.metadata["original_input"] = submission_id
            return result

        # 7. Error Fallback
        result.error = f"Unable to resolve submission ID from input: {submission_id[:50]}..."
        return result

    except Exception as e:
        result.error = f"Error during ID resolution: {e!s}"
        return result
