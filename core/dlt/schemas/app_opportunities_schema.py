"""
DLT Schema Definition for App Opportunities with Constraint Metadata.

This module defines the DLT schema for app_opportunities table with all constraint
enforcement fields including core_functions count, simplicity_score, is_disqualified,
validation_timestamp, and constraint_violations tracking table.
"""

import dlt


def get_app_opportunities_schema() -> dlt.Schema:
    """
    Create DLT schema for app_opportunities with constraint metadata.

    Note: DLT 1.x auto-generates schema from resources. This function returns
    a base schema object that will be expanded by DLT as data is loaded.

    Returns:
        dlt.Schema: Base DLT schema with constraint-aware naming
    """
    # Create base schema - DLT will auto-populate with resource fields
    app_opportunities_schema = dlt.Schema("reddit_harbor")

    # DLT will automatically infer columns from loaded data
    # This base schema just defines the dataset name

    return app_opportunities_schema


def get_constraint_summary_schema() -> dlt.Schema:
    """
    Create DLT schema for constraint compliance summary.

    Aggregated view of constraint compliance across all opportunities.

    Note: DLT 1.x auto-generates schema from resources. This returns a base schema.

    Returns:
        dlt.Schema: Base DLT schema for summary metrics
    """
    constraint_summary_schema = dlt.Schema("constraint_summary")
    # DLT will auto-populate columns from resource data
    return constraint_summary_schema


# Export schemas
app_opportunities_schema = get_app_opportunities_schema()
constraint_summary_schema = get_constraint_summary_schema()

# Schema metadata for documentation
SCHEMA_DOCUMENTATION = {
    "app_opportunities": {
        "description": "Main table for app opportunities with constraint enforcement",
        "constraint_fields": [
            "core_functions: Number of core functions (0-10, max allowed is 3)",
            "simplicity_score: Score based on function count (100/85/70/0)",
            "is_disqualified: Boolean flag for 4+ function violations",
            "validation_timestamp: When constraint was validated",
            "validation_status: APPROVED/DISQUALIFIED with function count",
            "violation_reason: Detailed reason for disqualification"
        ]
    },
    "constraint_violations": {
        "description": "Tracking table for all constraint violations",
        "purpose": "Audit trail for compliance monitoring and analysis"
    },
    "constraint_summary": {
        "description": "Aggregated daily summary of constraint compliance",
        "purpose": "High-level metrics for monitoring constraint effectiveness"
    }
}
