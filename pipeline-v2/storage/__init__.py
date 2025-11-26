"""
RedditHarbor Pipeline v2 - Storage Module

This module provides storage and database integration capabilities for the pipeline,
including DLT (Data Load Tool) integration for loading validated opportunity data
to Supabase (PostgreSQL) with proper merge disposition and error handling.

Components:
- dlt_loader: DLT pipeline manager for Supabase integration
- Future: Additional storage backends and utilities

Author: Phase 5 Storage Implementation
Version: Pipeline-v2 compatible
"""

# Import DLT loader for external access
try:
    from .dlt_loader import (
        DLTLoader,
        DLTLoaderError,
        DLTCredentialError,
        DLTConnectionError,
        create_dlt_loader,
        load_opportunities_to_supabase,
        DEFAULT_PIPELINE_NAME,
        DEFAULT_TABLE_NAME,
        DEFAULT_PRIMARY_KEY,
        DEFAULT_WRITE_DISPOSITION
    )
    DLT_AVAILABLE = True
except ImportError as e:
    # DLT or dependencies not available
    DLT_AVAILABLE = False
    DLTLoader = None
    DLTLoaderError = None
    DLTCredentialError = None
    DLTConnectionError = None
    create_dlt_loader = None
    load_opportunities_to_supabase = None

    # Define constants even if DLT is not available
    DEFAULT_PIPELINE_NAME = "reddit_opportunity_pipeline_v2"
    DEFAULT_TABLE_NAME = "app_opportunities"
    DEFAULT_PRIMARY_KEY = "submission_id"
    DEFAULT_WRITE_DISPOSITION = "merge"

# Export public API
__all__ = [
    # Main classes
    "DLTLoader",
    "DLTLoaderError",
    "DLTCredentialError",
    "DLTConnectionError",

    # Factory functions
    "create_dlt_loader",
    "load_opportunities_to_supabase",

    # Constants
    "DEFAULT_PIPELINE_NAME",
    "DEFAULT_TABLE_NAME",
    "DEFAULT_PRIMARY_KEY",
    "DEFAULT_WRITE_DISPOSITION",

    # Availability flag
    "DLT_AVAILABLE"
]

# Version information
__version__ = "1.0.0"
__author__ = "RedditHarbor Pipeline v2 Team"