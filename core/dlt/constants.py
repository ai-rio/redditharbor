#!/usr/bin/env python3
"""
DLT Primary Key Constants Module

This module provides centralized management of primary key constants used across
DLT (Data Load Tool) resources to prevent hard-coded dependencies and enable
safe schema consolidation.

Critical for Phase 3 schema consolidation - removes hard-coded primary key
strings that would break DLT merge logic when columns are renamed.

Usage:
    from core.dlt.constants import PK_SUBMISSION_ID, PK_OPPORTUNITY_ID

    @dlt.resource(
        name="app_opportunities",
        write_disposition="merge",
        primary_key=PK_SUBMISSION_ID
    )
    def app_opportunities_resource(data):
        yield data

"""

from __future__ import annotations

from enum import Enum, auto
from typing import Final, Literal


class PrimaryKeyType(Enum):
    """Enumeration of supported primary key types for validation."""
    SUBMISSION_ID = auto()
    OPPORTUNITY_ID = auto()
    COMMENT_ID = auto()
    DISPLAY_NAME = auto()
    ID = auto()


# Primary Key Constants - Single Source of Truth
PK_SUBMISSION_ID: Final[str] = "submission_id"
PK_OPPORTUNITY_ID: Final[str] = "opportunity_id"
PK_COMMENT_ID: Final[str] = "comment_id"
PK_DISPLAY_NAME: Final[str] = "display_name"
PK_ID: Final[str] = "id"


# Legacy aliases for backward compatibility
LEGACY_PK_MAP: Final[dict[str, str]] = {
    "submission_id": PK_SUBMISSION_ID,
    "opportunity_id": PK_OPPORTUNITY_ID,
    "comment_id": PK_COMMENT_ID,
    "display_name": PK_DISPLAY_NAME,
    "id": PK_ID,
}


# DLT Resource Primary Key Mappings
DLT_RESOURCE_PK_MAP: Final[dict[str, str]] = {
    # App Opportunities DLT Resources
    "app_opportunities": PK_SUBMISSION_ID,
    "app_opportunities_trust": PK_SUBMISSION_ID,

    # Opportunity Analysis Resources
    "opportunity_analysis": PK_SUBMISSION_ID,
    "workflow_results_with_costs": PK_OPPORTUNITY_ID,

    # Reddit Source Resources
    "active_subreddits": PK_DISPLAY_NAME,
    "validated_comments": PK_ID,
    "activity_trends": PK_DISPLAY_NAME,

    # Collection Resources
    "submissions": PK_SUBMISSION_ID,
    "comments": PK_COMMENT_ID,

    # Cost Tracking Resources
    "cost_tracking": PK_OPPORTUNITY_ID,
    "workflow_results": PK_OPPORTUNITY_ID,
}


# Table Schema Primary Key Definitions
TABLE_PRIMARY_KEYS: Final[dict[str, str]] = {
    # Core tables
    "submissions": PK_SUBMISSION_ID,
    "comments": PK_COMMENT_ID,
    "redditors": PK_ID,

    # Application tables
    "app_opportunities": PK_SUBMISSION_ID,
    "opportunity_analysis": PK_SUBMISSION_ID,
    "workflow_results": PK_OPPORTUNITY_ID,

    # Activity tracking tables
    "active_subreddits": PK_DISPLAY_NAME,
    "activity_trends": PK_DISPLAY_NAME,
    "validated_comments": PK_ID,
}


# Type definitions for primary key validation
SubmissionPK = Literal[PK_SUBMISSION_ID]
OpportunityPK = Literal[PK_OPPORTUNITY_ID]
CommentPK = Literal[PK_COMMENT_ID]
DisplayNamePK = Literal[PK_DISPLAY_NAME]
IdPK = Literal[PK_ID]
PrimaryKeyType = Literal[PK_SUBMISSION_ID, PK_OPPORTUNITY_ID, PK_COMMENT_ID, PK_DISPLAY_NAME, PK_ID]


def validate_primary_key(pk: str, expected_type: PrimaryKeyType | None = None) -> bool:
    """
    Validate that a primary key string is recognized and optionally matches expected type.

    Args:
        pk: Primary key string to validate
        expected_type: Optional expected primary key type for additional validation

    Returns:
        True if primary key is valid (and matches expected type if provided)

    Raises:
        ValueError: If primary key is not recognized or doesn't match expected type
    """
    valid_keys = {
        PK_SUBMISSION_ID: "submission_id",
        PK_OPPORTUNITY_ID: "opportunity_id",
        PK_COMMENT_ID: "comment_id",
        PK_DISPLAY_NAME: "display_name",
        PK_ID: "id",
    }

    if pk not in valid_keys:
        raise ValueError(f"Unrecognized primary key: {pk}. Valid keys: {list(valid_keys.keys())}")

    if expected_type is not None:
        # Use enum value to determine expected key
        if expected_type == PrimaryKeyType.SUBMISSION_ID:
            expected_key = PK_SUBMISSION_ID
            expected_name = "submission_id"
        elif expected_type == PrimaryKeyType.OPPORTUNITY_ID:
            expected_key = PK_OPPORTUNITY_ID
            expected_name = "opportunity_id"
        elif expected_type == PrimaryKeyType.COMMENT_ID:
            expected_key = PK_COMMENT_ID
            expected_name = "comment_id"
        elif expected_type == PrimaryKeyType.DISPLAY_NAME:
            expected_key = PK_DISPLAY_NAME
            expected_name = "display_name"
        elif expected_type == PrimaryKeyType.ID:
            expected_key = PK_ID
            expected_name = "id"
        else:
            raise ValueError(f"Unknown expected primary key type: {expected_type}")

        if pk != expected_key:
            raise ValueError(f"Primary key mismatch: expected {expected_key} for {expected_name}, got {pk}")

    return True


def get_resource_primary_key(resource_name: str) -> str:
    """
    Get the primary key for a DLT resource by name.

    Args:
        resource_name: Name of the DLT resource

    Returns:
        Primary key string for the resource

    Raises:
        KeyError: If resource name is not found in the mapping
    """
    if resource_name not in DLT_RESOURCE_PK_MAP:
        available_resources = list(DLT_RESOURCE_PK_MAP.keys())
        raise KeyError(f"Resource '{resource_name}' not found. Available resources: {available_resources}")

    return DLT_RESOURCE_PK_MAP[resource_name]


def get_table_primary_key(table_name: str) -> str:
    """
    Get the primary key for a database table by name.

    Args:
        table_name: Name of the database table

    Returns:
        Primary key string for the table

    Raises:
        KeyError: If table name is not found in the mapping
    """
    if table_name not in TABLE_PRIMARY_KEYS:
        available_tables = list(TABLE_PRIMARY_KEYS.keys())
        raise KeyError(f"Table '{table_name}' not found. Available tables: {available_tables}")

    return TABLE_PRIMARY_KEYS[table_name]


def migrate_legacy_primary_key(legacy_pk: str) -> str:
    """
    Migrate a legacy hard-coded primary key to the centralized constant.

    Args:
        legacy_pk: Legacy hard-coded primary key string

    Returns:
        Centralized primary key constant

    Raises:
        KeyError: If legacy primary key is not recognized
    """
    if legacy_pk not in LEGACY_PK_MAP:
        available_legacy = list(LEGACY_PK_MAP.keys())
        raise KeyError(f"Legacy primary key '{legacy_pk}' not recognized. Available: {available_legacy}")

    return LEGACY_PK_MAP[legacy_pk]


def validate_merge_disposition_compatibility(
    write_disposition: str,
    primary_key: str | None
) -> bool:
    """
    Validate that merge disposition is compatible with primary key configuration.

    Args:
        write_disposition: DLT write disposition ('merge', 'append', 'replace')
        primary_key: Primary key string (None for non-merge operations)

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    if write_disposition == "merge" and not primary_key:
        raise ValueError("Merge disposition requires a primary key for deduplication")

    if write_disposition != "merge" and primary_key:
        # Warning: primary key specified for non-merge operation
        import warnings
        warnings.warn(
            f"Primary key '{primary_key}' specified with write_disposition '{write_disposition}'. "
            "Primary keys are only used for merge operations.",
            UserWarning,
            category=UserWarning
        )

    if primary_key:
        validate_primary_key(primary_key)

    return True


# Convenience functions for common DLT resource patterns
def submission_resource_config(
    write_disposition: str = "merge"
) -> dict[str, str | bool]:
    """
    Get standard configuration for submission-based DLT resources.

    Args:
        write_disposition: DLT write disposition (default: 'merge')

    Returns:
        Dictionary with resource configuration
    """
    validate_merge_disposition_compatibility(write_disposition, PK_SUBMISSION_ID)

    return {
        "write_disposition": write_disposition,
        "primary_key": PK_SUBMISSION_ID if write_disposition == "merge" else None
    }


def opportunity_resource_config(
    write_disposition: str = "merge"
) -> dict[str, str | bool]:
    """
    Get standard configuration for opportunity-based DLT resources.

    Args:
        write_disposition: DLT write disposition (default: 'merge')

    Returns:
        Dictionary with resource configuration
    """
    validate_merge_disposition_compatibility(write_disposition, PK_OPPORTUNITY_ID)

    return {
        "write_disposition": write_disposition,
        "primary_key": PK_OPPORTUNITY_ID if write_disposition == "merge" else None
    }


# Export all public symbols
__all__ = [
    # Enum types
    "PrimaryKeyType",

    # Constants
    "PK_SUBMISSION_ID",
    "PK_OPPORTUNITY_ID",
    "PK_COMMENT_ID",
    "PK_DISPLAY_NAME",
    "PK_ID",

    # Type aliases
    "SubmissionPK",
    "OpportunityPK",
    "CommentPK",
    "DisplayNamePK",
    "IdPK",
    "PrimaryKeyType",

    # Mappings
    "DLT_RESOURCE_PK_MAP",
    "TABLE_PRIMARY_KEYS",
    "LEGACY_PK_MAP",

    # Validation functions
    "validate_primary_key",
    "get_resource_primary_key",
    "get_table_primary_key",
    "migrate_legacy_primary_key",
    "validate_merge_disposition_compatibility",

    # Configuration functions
    "submission_resource_config",
    "opportunity_resource_config",
]


# Runtime validation of constants integrity
def _validate_constants_integrity() -> None:
    """Internal function to validate constants integrity at import time."""
    # Ensure all constants are unique
    pk_values = [PK_SUBMISSION_ID, PK_OPPORTUNITY_ID, PK_COMMENT_ID, PK_DISPLAY_NAME, PK_ID]
    if len(pk_values) != len(set(pk_values)):
        raise ValueError("Primary key constants must be unique")

    # Ensure mapping values match constants
    for pk in DLT_RESOURCE_PK_MAP.values():
        if pk not in pk_values:
            raise ValueError(f"DLT resource mapping contains unknown primary key: {pk}")

    for pk in TABLE_PRIMARY_KEYS.values():
        if pk not in pk_values:
            raise ValueError(f"Table mapping contains unknown primary key: {pk}")


# Run integrity check at import
_validate_constants_integrity()
