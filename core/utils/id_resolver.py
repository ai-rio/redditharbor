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
from typing import Any, Literal

# Constants
REDDITHARBOR_NAMESPACE: uuid.UUID = uuid.uuid5(
    uuid.NAMESPACE_DNS, "redditharbor-pipeline"
)
REDDIT_URL_PATTERN: Pattern[str] = re.compile(
    r"reddit\.com(?:/r/[^/]+)?/comments/([a-zA-Z0-9]+)"
)
UUID_PATTERN: Pattern[str] = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


@dataclass
class ResolutionResult:
    """
    Result of ID resolution attempt containing canonical UUID and metadata.

    Attributes:
        uuid: The resolved submissions.id UUID or None
        source: Source of UUID ("database", "passthrough", "generated") or None
        original_input: What was passed in (stringified)
        error: Error message if resolution failed
        metadata: Additional resolution metadata
    """
    uuid: str | None
    source: Literal["database", "passthrough", "generated"] | None
    original_input: str
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

    Raises:
        ValueError: If input_string is empty or whitespace-only
    """
    if not input_string or not input_string.strip():
        raise ValueError("Input string cannot be empty")

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
    input_value: str | dict[str, Any] | None,
    *,
    require_db_existence: bool = False,
    fallback_to_generated: bool = True,
    supabase_client: Any = None,
) -> ResolutionResult | None:
    """
    Resolve various ID formats to canonical RedditHarbor UUID.

    Args:
        input_value: Input ID in various formats (UUID, Reddit ID, URL, dict)
        require_db_existence: Whether to require database existence for valid UUIDs
        fallback_to_generated: Whether to generate UUID for unknown inputs
        supabase_client: Database client (Phase 1: ignored)

    Returns:
        ResolutionResult containing canonical UUID and resolution metadata,
        or None for null/empty inputs
    """
    # Store the original input as string for the result
    original_input = str(input_value) if input_value is not None else "None"

    try:
        # 1. Null/Empty Check - Return None immediately
        if input_value is None or (
            isinstance(input_value, str) and not input_value.strip()
        ):
            return None

        # Handle dictionary input - extract ID first
        processed_value = input_value
        extraction_method = None
        dict_metadata = {}

        if isinstance(input_value, dict):
            extracted_id, key_used = extract_id_from_dict(input_value)
            if extracted_id:
                processed_value = extracted_id
                extraction_method = f"dict_{key_used}"
                dict_metadata["original_dict_keys"] = list(input_value.keys())
                dict_metadata["extraction_method"] = extraction_method
            else:
                return ResolutionResult(
                    uuid=None,
                    source=None,
                    original_input=original_input,
                    error="Invalid dict format: missing submission_id and reddit_id",
                    metadata={"available_keys": list(input_value.keys())}
                )

        # At this point, processed_value should be a string
        if not isinstance(processed_value, str):
            return ResolutionResult(
                uuid=None,
                source=None,
                original_input=original_input,
                error=(
            f"Invalid input type: {type(processed_value)}. "
            "Expected str, dict, or None."
        )
            )

        processed_value = processed_value.strip()

        # 2. UUID Validation - Passthrough path
        if is_valid_uuid(processed_value):
            # If database existence is required, we would query here
            # For Phase 1, we just passthrough the UUID
            return ResolutionResult(
                uuid=processed_value.lower(),  # Normalize case
                source="passthrough",
                original_input=original_input,
                metadata=dict_metadata
            )

        # 3. URL Extraction
        reddit_id = extract_reddit_id_from_url(processed_value)
        if reddit_id:
            # Process the extracted reddit_id the same way as direct input
            # for deterministic behavior across different input formats
            generated_uuid = generate_deterministic_uuid(reddit_id)
            return ResolutionResult(
                uuid=generated_uuid,
                source="generated",
                original_input=original_input,
                metadata={
                    **dict_metadata,
                    "extracted_reddit_id": reddit_id,
                    "url_pattern": "comments"
                }
            )

        # 4. Database lookup (Phase 1: skipped, always generate)
        # In Phase 2, this would query submissions.reddit_id = processed_value
        # For now, we fall through to generation

        # 5. UUID Generation for all other valid inputs
        if fallback_to_generated:
            generated_uuid = generate_deterministic_uuid(processed_value)
            metadata = dict_metadata.copy()
            if extraction_method:
                metadata["fallback_used"] = True

            return ResolutionResult(
                uuid=generated_uuid,
                source="generated",
                original_input=original_input,
                metadata=metadata
            )

        # 6. Error Fallback - no generation allowed
        return ResolutionResult(
            uuid=None,
            source=None,
            original_input=original_input,
            error=(
            "Unable to resolve submission ID and fallback_to_generated=False: "
            f"{processed_value[:50]}..."
        )
        )

    except Exception as e:
        return ResolutionResult(
            uuid=None,
            source=None,
            original_input=original_input,
            error=f"Error during ID resolution: {e!s}"
        )
