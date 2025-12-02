#!/usr/bin/env python3
"""
DLT Package Initialization

This package provides centralized DLT (Data Load Tool) resources and utilities
for RedditHarbor with standardized primary key management.

The package includes:
- Constants for primary key management
- Resource definitions for Reddit data collection
- Pipeline configurations for data loading

Usage:
    from core.dlt import PK_SUBMISSION_ID, get_resource_primary_key
    from core.dlt.constants import submission_resource_config
"""

# Import constants for easy access
from .constants import (
    PK_COMMENT_ID,
    PK_DISPLAY_NAME,
    PK_ID,
    PK_OPPORTUNITY_ID,
    # Constants
    PK_SUBMISSION_ID,
    CommentPK,
    DisplayNamePK,
    IdPK,
    OpportunityPK,
    # Types
    PrimaryKeyType,
    SubmissionPK,
    get_resource_primary_key,
    get_table_primary_key,
    migrate_legacy_primary_key,
    opportunity_resource_config,
    submission_resource_config,
    validate_merge_disposition_compatibility,
    # Functions
    validate_primary_key,
)
from .constants import (
    PrimaryKeyType as PrimaryKeyLiteralType,
)

__all__ = [
    # Constants
    "PK_SUBMISSION_ID",
    "PK_OPPORTUNITY_ID",
    "PK_COMMENT_ID",
    "PK_DISPLAY_NAME",
    "PK_ID",

    # Types
    "PrimaryKeyType",
    "PrimaryKeyLiteralType",
    "SubmissionPK",
    "OpportunityPK",
    "CommentPK",
    "DisplayNamePK",
    "IdPK",

    # Functions
    "validate_primary_key",
    "get_resource_primary_key",
    "get_table_primary_key",
    "migrate_legacy_primary_key",
    "validate_merge_disposition_compatibility",
    "submission_resource_config",
    "opportunity_resource_config",
]
