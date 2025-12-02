#!/usr/bin/env python3
"""
Supabase Opportunities Loader

Direct Supabase implementation for loading app opportunities.
Replaces DLT pipeline to fix UUID handling and simplify codebase.
"""

import logging
import sys
import uuid as uuid_module
from pathlib import Path
from typing import Any

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.utils.core_functions_serialization import dlt_standardize_core_functions

logger = logging.getLogger(__name__)


def get_supabase_client():
    """
    Get configured Supabase client.

    Returns:
        Supabase client instance

    Raises:
        ValueError: If Supabase credentials not configured
    """
    from config.settings import SUPABASE_KEY, SUPABASE_URL
    from supabase import create_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase credentials not configured")

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _is_valid_uuid(value: Any) -> bool:
    """
    Validate UUID format.

    Args:
        value: Value to validate

    Returns:
        True if valid UUID, False otherwise
    """
    if not value:
        return False
    try:
        uuid_module.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


def load_app_opportunities(ai_profiles: list[dict[str, Any]]) -> bool:
    """
    Load AI profiles to opportunities table via Supabase.

    Replaces DLT pipeline with direct Supabase insertion.
    Fixes UUID blocker by using native UUID handling.

    Args:
        ai_profiles: List of AI-generated opportunity profiles with fields:
            - id (required, UUID, primary key)
            - problem_statement (required for filtering)
            - title (required)
            - description (optional)
            - target_audience (optional)
            - submission_id (optional, UUID, foreign key)
            - core_functions (optional, auto-standardized to JSON)

    Returns:
        True if successful, False otherwise

    Example:
        >>> profiles = [{
        ...     "id": "550e8400-e29b-41d4-a716-446655440000",
        ...     "title": "Test App",
        ...     "problem_statement": "Teams waste time...",
        ...     "core_functions": ["Feature 1", "Feature 2"]
        ... }]
        >>> load_app_opportunities(profiles)
        True
    """
    if not ai_profiles:
        print("⚠️  No AI profiles to load")
        return False

    # Filter profiles with non-empty problem_statement (matches DB schema)
    # Also support old field name 'problem_description' for backwards compat
    ai_only = [
        p
        for p in ai_profiles
        if (p.get("problem_statement") or "").strip()
        or (p.get("problem_description") or "").strip()
    ]

    if not ai_only:
        print("⚠️  No AI-generated profiles found")
        return False

    # Standardize core_functions (list → JSON string for JSONB)
    standardized = [dlt_standardize_core_functions(p) for p in ai_only]

    # Validate UUIDs and filter invalid profiles
    valid_profiles = []
    for profile in standardized:
        profile_id = profile.get("id")
        submission_id = profile.get("submission_id")

        # Validate id (required)
        if not _is_valid_uuid(profile_id):
            logger.warning(f"Skipping profile with invalid id: {profile_id}")
            continue

        # Validate submission_id (optional, but must be valid if present)
        if submission_id and not _is_valid_uuid(submission_id):
            logger.warning(
                f"Skipping profile with invalid submission_id: {submission_id}"
            )
            continue

        # Validate required field: title
        if not profile.get("title"):
            logger.warning(
                f"Skipping profile missing required field 'title': {profile_id}"
            )
            continue

        valid_profiles.append(profile)

    if not valid_profiles:
        print("⚠️  No valid profiles after validation")
        return False

    print(f"\n📤 Loading {len(valid_profiles)} profiles to opportunities...")

    try:
        client = get_supabase_client()

        # Batch upsert to opportunities table
        # Using upsert for idempotency and proper deduplication
        # on_conflict='id' ensures updates on duplicate IDs
        client.table("opportunities").upsert(
            valid_profiles,
            on_conflict='id'
        ).execute()

        print(f"✓ Loaded {len(valid_profiles)} profiles successfully!")
        return True

    except Exception as e:
        print(f"✗ Failed to load profiles: {e}")
        logger.error(f"Supabase upsert failed: {e}", exc_info=True)
        return False


# Example usage
if __name__ == "__main__":
    import uuid as uuid_module

    test_profile = {
        "id": str(uuid_module.uuid4()),
        "title": "Test App Opportunity",
        "problem_statement": "Teams waste 10+ hours weekly juggling multiple tools",
        "description": "An integrated project management platform",
        "core_functions": ["Time tracking", "Gantt charts", "Task dashboard"],
        "target_audience": "Small to mid-sized teams",
        "submission_id": str(uuid_module.uuid4())
    }

    print("Testing Supabase opportunities loader...")
    success = load_app_opportunities([test_profile])

    if success:
        print("\n✅ Test passed! Supabase upsert working.")
    else:
        print("\n❌ Test failed!")
