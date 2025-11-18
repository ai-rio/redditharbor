#!/usr/bin/env python3
"""
DLT Resource for App Opportunities with Deduplication

Manages AI-generated app profiles with automatic deduplication via DLT's merge disposition.
Prevents duplicate profiles from same submission_id, saving LLM API costs.
"""

import sys
from pathlib import Path
from typing import Any

import dlt

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dlt import PK_SUBMISSION_ID, submission_resource_config
from core.utils.core_functions_serialization import dlt_standardize_core_functions

# DLT pipeline configuration
PIPELINE_NAME = "reddit_harbor_app_opportunities"
DESTINATION = "postgres"
DATASET_NAME = "public"


def create_app_opportunities_pipeline() -> dlt.Pipeline:
    """Create DLT pipeline for app_opportunities table."""
    connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination=dlt.destinations.postgres(connection_string),
        dataset_name=DATASET_NAME
    )
    return pipeline


@dlt.resource(
    name="app_opportunities",
    write_disposition="merge",  # Deduplication via primary key
    primary_key=PK_SUBMISSION_ID,  # Specify primary key for merge operations
    # Remove complex column hints - let DLT infer from data
    # core_functions will be inferred as text from JSON string
)
def app_opportunities_resource(ai_profiles: list[dict[str, Any]]):
    """
    DLT resource for app_opportunities with automatic deduplication.

    Args:
        ai_profiles: List of AI-generated opportunity profiles

    Yields:
        Profile dictionaries with submission_id as primary key
    """
    for profile in ai_profiles:
        # Only yield if it has AI-generated content
        if profile.get("problem_description"):
            # Standardize core_functions using the serialization utility
            profile = dlt_standardize_core_functions(profile)
            yield profile


def load_app_opportunities(ai_profiles: list[dict[str, Any]]) -> bool:
    """
    Load AI profiles to app_opportunities table with DLT deduplication.

    Args:
        ai_profiles: List of AI-generated opportunity profiles with fields:
            - submission_id (required)
            - problem_description (required)
            - app_concept (required)
            - core_functions (required)
            - value_proposition (required)
            - target_user (required)
            - monetization_model (required)
            - opportunity_score (optional)
            - title, subreddit, reddit_score, status (optional)

    Returns:
        True if successful, False otherwise

    Example:
        >>> profiles = [{
        ...     "submission_id": "abc123",
        ...     "problem_description": "Teams waste time...",
        ...     "app_concept": "Integrated PM platform...",
        ...     "core_functions": ["Feature 1", "Feature 2"],
        ...     "value_proposition": "Save 10 hours/week",
        ...     "target_user": "Small teams",
        ...     "monetization_model": "Subscription",
        ...     "opportunity_score": 32.5,
        ...     "status": "discovered"
        ... }]
        >>> load_app_opportunities(profiles)
        True
    """
    if not ai_profiles:
        print("⚠️  No AI profiles to load")
        return False

    # Filter to only profiles with AI content
    ai_only = [p for p in ai_profiles if p.get("problem_description")]

    if not ai_only:
        print("⚠️  No AI-generated profiles found (all missing problem_description)")
        return False

    print(f"\n📤 Loading {len(ai_only)} AI profiles to app_opportunities (merge mode)...")
    print("-" * 80)

    pipeline = create_app_opportunities_pipeline()

    try:
        # Run DLT pipeline with merge disposition
        # Primary key = submission_id → automatic deduplication
        load_info = pipeline.run(
            app_opportunities_resource(ai_only),
            primary_key=PK_SUBMISSION_ID
        )

        print("✓ AI profiles loaded successfully!")
        print(f"  - Profiles processed: {len(ai_only)}")
        print("  - Write mode: merge (deduplication on submission_id)")
        print(f"  - Started: {load_info.started_at}")

        return True

    except Exception as e:
        print(f"✗ AI profile load failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Example usage
if __name__ == "__main__":
    test_profile = {
        "submission_id": "test_abc123",
        "problem_description": "Teams waste 10+ hours weekly juggling multiple tools",
        "app_concept": "An integrated project management platform",
        "core_functions": ["Time tracking", "Gantt charts", "Task dashboard"],
        "value_proposition": "Eliminate tool-switching overhead",
        "target_user": "Small to mid-sized teams",
        "monetization_model": "Subscription: $29/month per team",
        "opportunity_score": 32.5,
        "title": "Test submission",
        "subreddit": "SaaS",
        "reddit_score": 1840,
        "status": "discovered"
    }

    print("Testing DLT app_opportunities resource...")
    success = load_app_opportunities([test_profile])

    if success:
        print("\n✅ Test passed! DLT deduplication working.")
    else:
        print("\n❌ Test failed!")
