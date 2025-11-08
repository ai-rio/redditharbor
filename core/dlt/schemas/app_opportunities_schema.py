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

    Returns:
        dlt.Schema: Configured DLT schema with constraint fields
    """
    # Define schema with constraint fields
    app_opportunities_schema = dlt.Schema("app_opportunities")

    # Add main app_opportunities table with constraint metadata
    app_opportunities_schema.add_table(
        table_name="app_opportunities",
        columns=[
            # Standard opportunity fields
            {"name": "opportunity_id", "type": "text", "primary_key": True},
            {"name": "submission_id", "type": "text", "nullable": True},
            {"name": "app_name", "type": "text", "nullable": False},

            # Core methodology fields
            {"name": "market_demand_score", "type": "double", "nullable": True},
            {"name": "pain_intensity_score", "type": "double", "nullable": True},
            {"name": "monetization_potential_score", "type": "double", "nullable": True},
            {"name": "market_gap_score", "type": "double", "nullable": True},
            {"name": "technical_feasibility_score", "type": "double", "nullable": True},
            {"name": "simplicity_score", "type": "double", "nullable": True},

            # Total composite score
            {"name": "total_score", "type": "double", "nullable": True},

            # Core function count (constraint field)
            {"name": "core_functions", "type": "bigint", "nullable": True},

            # Constraint enforcement fields
            {"name": "is_disqualified", "type": "bool", "nullable": True},
            {"name": "constraint_version", "type": "bigint", "nullable": True, "default": 1},
            {"name": "validation_timestamp", "type": "timestamp", "nullable": True},
            {"name": "violation_reason", "type": "text", "nullable": True},
            {"name": "validation_status", "type": "text", "nullable": True},

            # Function details
            {"name": "function_list", "type": "json", "nullable": True},

            # Business context
            {"name": "business_category", "type": "text", "nullable": True},
            {"name": "target_market", "type": "text", "nullable": True},
            {"name": "monetization_model", "type": "text", "nullable": True},

            # Development details
            {"name": "development_cost_estimate", "type": "bigint", "nullable": True},
            {"name": "mvp_timeline_weeks", "type": "bigint", "nullable": True},
            {"name": "complexity_rating", "type": "text", "nullable": True},

            # Metadata
            {"name": "created_at", "type": "timestamp", "nullable": True, "default": "NOW()"},
            {"name": "updated_at", "type": "timestamp", "nullable": True, "default": "NOW()"},
            {"name": "source_subreddit", "type": "text", "nullable": True},
            {"name": "analysis_version", "type": "text", "nullable": True},
        ]
    )

    # Add constraint violations tracking table
    app_opportunities_schema.add_table(
        table_name="constraint_violations",
        columns=[
            {"name": "violation_id", "type": "text", "primary_key": True},
            {"name": "opportunity_id", "type": "text", "nullable": False},
            {"name": "violation_type", "type": "text", "nullable": False},
            {"name": "function_count", "type": "bigint", "nullable": False},
            {"name": "max_allowed", "type": "bigint", "nullable": False, "default": 3},
            {"name": "violation_reason", "type": "text", "nullable": True},
            {"name": "timestamp", "type": "timestamp", "nullable": True, "default": "NOW()"},
            {"name": "app_name", "type": "text", "nullable": True},
            {"name": "original_score", "type": "double", "nullable": True},
            {"name": "constraint_version", "type": "bigint", "nullable": True, "default": 1},
        ]
    )

    return app_opportunities_schema


def get_constraint_summary_schema() -> dlt.Schema:
    """
    Create DLT schema for constraint compliance summary.

    Aggregated view of constraint compliance across all opportunities.

    Returns:
        dlt.Schema: Configured DLT schema for summary metrics
    """
    constraint_summary_schema = dlt.Schema("constraint_summary")

    constraint_summary_schema.add_table(
        table_name="constraint_summary",
        columns=[
            {"name": "summary_id", "type": "text", "primary_key": True},
            {"name": "date", "type": "date", "nullable": False},
            {"name": "total_opportunities", "type": "bigint", "nullable": False},
            {"name": "approved_count", "type": "bigint", "nullable": False},
            {"name": "disqualified_count", "type": "bigint", "nullable": False},
            {"name": "compliance_rate", "type": "double", "nullable": False},
            {"name": "avg_core_functions", "type": "double", "nullable": True},
            {"name": "avg_simplicity_score", "type": "double", "nullable": True},
            {"name": "timestamp", "type": "timestamp", "nullable": True, "default": "NOW()"},
        ]
    )

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
