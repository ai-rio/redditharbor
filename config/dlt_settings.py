"""
DLT pipeline configuration for RedditHarbor.

This module configures dlt pipelines for Reddit data collection,
including destination setup, incremental loading strategies, and
schema evolution policies.
"""

from config.settings import SUPABASE_KEY, SUPABASE_URL

# DLT destination configuration
DLT_DESTINATION = "postgres"
DLT_DATASET_NAME = "reddit_harbor"

# Supabase connection from existing config
DLT_SUPABASE_CONFIG = {
    "credentials": {
        "url": SUPABASE_URL,
        "service_role_key": SUPABASE_KEY
    }
}

# Pipeline configuration
DLT_PIPELINE_CONFIG = {
    "pipeline_name": "reddit_harbor_collection",
    "destination": DLT_DESTINATION,
    "dataset_name": DLT_DATASET_NAME,
}

# Incremental loading configuration
DLT_INCREMENTAL_CONFIG = {
    "submissions": {
        "cursor_column": "created_utc",
        "primary_key": "id",
        "write_disposition": "merge"
    },
    "comments": {
        "cursor_column": "created_utc",
        "primary_key": "id",
        "write_disposition": "merge"
    }
}

# Schema evolution policy
DLT_SCHEMA_CONFIG = {
    "allow_new_columns": True,
    "allow_new_tables": True,
    "allow_column_type_changes": False,  # Strict for production
}
