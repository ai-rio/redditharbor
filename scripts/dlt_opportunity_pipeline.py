"""
DLT Opportunity Pipeline - Loads app opportunities with built-in constraint validation.

This module provides a DLT-native pipeline for loading app opportunities that
automatically enforces the 1-3 core function constraint through DLT resources
and normalization hooks.
"""

from datetime import datetime
from typing import Any

import dlt

from config.dlt_settings import DLT_PIPELINE_CONFIG
from core.dlt.constraint_validator import app_opportunities_with_constraint


def load_app_opportunities_with_constraint(
    opportunities: list[dict[str, Any]],
    write_disposition: str = "merge",
    primary_key: str = "opportunity_id"
) -> dlt.Pipeline:
    """
    Load app opportunities with built-in simplicity constraint validation.

    Uses DLT-native constraint enforcement through the app_opportunities_with_constraint
    resource. Automatically adds constraint metadata and disqualifies 4+ function apps.

    Args:
        opportunities: List of app opportunity dictionaries
        write_disposition: DLT write disposition ('merge', 'replace', 'upsert')
        primary_key: Primary key for merge operations

    Returns:
        dlt.Pipeline: DLT pipeline instance with load results

    Example:
        opportunities = [
            {
                "opportunity_id": "opp_123",
                "app_name": "TestApp",
                "function_list": ["Track calories"],
                "total_score": 85.0
            }
        ]

        load_info = load_app_opportunities_with_constraint(opportunities)
        print(f"Loaded {load_info.load_id}")
    """
    # Create DLT pipeline
    pipeline = dlt.pipeline(**DLT_PIPELINE_CONFIG)

    # Load with constraint validation
    load_info = pipeline.run(
        app_opportunities_with_constraint(opportunities),
        write_disposition=write_disposition,
        primary_key=primary_key
    )

    return load_info


def load_opportunities_replace(opportunities: list[dict[str, Any]]) -> dlt.Pipeline:
    """
    Load opportunities with full refresh (replace disposition).

    Replaces all existing opportunities and re-validates all constraint metadata.
    Useful for full system re-runs or constraint enforcement updates.

    Args:
        opportunities: List of app opportunity dictionaries

    Returns:
        dlt.Pipeline: DLT pipeline instance with load results
    """
    return load_app_opportunities_with_constraint(
        opportunities,
        write_disposition="replace"
    )


def load_opportunities_incremental(
    opportunities: list[dict[str, Any]],
    primary_key: str = "opportunity_id"
) -> dlt.Pipeline:
    """
    Load opportunities incrementally (merge disposition).

    Only loads new opportunities or updates existing ones.
    Maintains constraint validation for all operations.

    Args:
        opportunities: List of new or updated app opportunity dictionaries
        primary_key: Primary key for merge operations

    Returns:
        dlt.Pipeline: DLT pipeline instance with load results
    """
    return load_app_opportunities_with_constraint(
        opportunities,
        write_disposition="merge",
        primary_key=primary_key
    )


def validate_constraints_only(opportunities: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Validate constraints without loading to database.

    Useful for testing or shadow mode validation.
    Returns validation results without database operations.

    Args:
        opportunities: List of app opportunity dictionaries

    Returns:
        Dict[str, Any]: Validation summary with counts and details
    """
    validated = list(app_opportunities_with_constraint(opportunities))

    violations = [o for o in validated if o.get("is_disqualified")]
    approved = [o for o in validated if not o.get("is_disqualified")]

    return {
        "total_opportunities": len(validated),
        "approved_count": len(approved),
        "disqualified_count": len(violations),
        "approved_opportunities": approved,
        "disqualified_opportunities": violations,
        "validation_timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import json

    # Example usage
    sample_opportunities = [
        {
            "opportunity_id": "opp_001",
            "app_name": "SimpleCalorieCounter",
            "function_list": ["Track calories"],
            "total_score": 85.0
        },
        {
            "opportunity_id": "opp_002",
            "app_name": "ComplexApp",
            "function_list": ["F1", "F2", "F3", "F4", "F5"],
            "total_score": 90.0
        }
    ]

    print("Validating constraints (shadow mode)...")
    results = validate_constraints_only(sample_opportunities)
    print(json.dumps(results, indent=2))

    print("\n" + "="*60)
    print("Loading to database (DLT pipeline)...")
    load_info = load_app_opportunities_with_constraint(sample_opportunities)
    print(f"✅ Loaded {len(sample_opportunities)} opportunities")
    print(f"   Load ID: {load_info.load_id}")
    print(f"   Duration: {load_info.duration}ms")
