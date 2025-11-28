"""
RedditHarbor Pipeline v2 - Storage Module

This module provides storage and database integration capabilities for the pipeline.
MIGRATED: Now defaults to SQLAlchemy loader for reliable data persistence with explicit
transaction control, eliminating DLT silent failures.

Components:
- sqlalchemy_loader: Primary SQLAlchemy-based loader (NEW DEFAULT)
- dlt_compatibility_adapter: DLT-compatible interface for SQLAlchemy
- dlt_loader: Legacy DLT loader (available for fallback)

Author: Phase 4 DLT to SQLAlchemy Migration
Version: SQLAlchemy Default
"""

# Constants (available without importing loaders)
DEFAULT_PIPELINE_NAME = "reddit_opportunity_pipeline_v2"
DEFAULT_TABLE_NAME = "app_opportunities"
DEFAULT_PRIMARY_KEY = "submission_id"
DEFAULT_WRITE_DISPOSITION = "merge"

# Loader availability flags
SQLALCHEMY_AVAILABLE = True
DLT_AVAILABLE = True

# Import SQLAlchemy components (only - DLT completely removed)
try:
    from .sqlalchemy_loader import SQLAlchemyLoader, LoadResult, SQLAlchemyLoadError
    SQLALCHEMY_IMPORT_SUCCESS = True
except ImportError as e:
    SQLALCHEMY_IMPORT_SUCCESS = False
    SQLAlchemyLoader = None
    LoadResult = None
    SQLAlchemyLoadError = None

# DLT compatibility adapter completely removed
DLTCompatibilityAdapter = None

# DLT components completely removed
# No lazy loading - DLT has been fully replaced by SQLAlchemy

# Factory function for SQLAlchemy loader (SQLALCHEMY ONLY)
def create_loader(
    connection_string: str,
    loader_type: str = "sqlalchemy",  # Only sqlalchemy supported
    **kwargs
):
    """
    Create a data loader instance.

    Args:
        connection_string: Database connection string
        loader_type: Type of loader to create (only "sqlalchemy" supported)
        **kwargs: Additional loader-specific parameters

    Returns:
        SQLAlchemy loader instance
    """
    if loader_type == "sqlalchemy":
        if not SQLALCHEMY_IMPORT_SUCCESS:
            raise ImportError("SQLAlchemy loader components not available")
        return SQLAlchemyLoader(connection_string, **kwargs)

    else:
        raise ValueError(f"Unknown loader type: {loader_type}. Only 'sqlalchemy' is supported.")


# Convenience function for loading opportunities (NEW SQLAlchemy DEFAULT)
def load_opportunities(
    data: list,
    connection_string: str,
    table_name: str = DEFAULT_TABLE_NAME,
    write_disposition: str = DEFAULT_WRITE_DISPOSITION,
    loader_type: str = "sqlalchemy",  # Changed default
    **kwargs
) -> LoadResult:
    """
    Load opportunity data using the specified loader.

    Args:
        data: List of opportunity records to load
        connection_string: Database connection string
        table_name: Target table name (currently ignored by SQLAlchemy, uses DEFAULT_TABLE_NAME)
        write_disposition: Write disposition (merge, append, replace)
        loader_type: Type of loader to use ("sqlalchemy" or "dlt")
        **kwargs: Additional loader-specific parameters

    Returns:
        LoadResult with operation details
    """
    loader = create_loader(connection_string, loader_type, **kwargs)
    if loader_type == "sqlalchemy":
        # SQLAlchemy loader has different signature
        return loader.load_opportunities(data, write_disposition)
    else:
        # DLT loader signature (for backward compatibility)
        return loader.load_opportunities(data, table_name, write_disposition)


# DLT compatibility function removed
def load_opportunities_to_supabase(data: list, **kwargs):
    """Legacy function - now redirects to SQLAlchemy loader."""
    return load_opportunities(data, loader_type="sqlalchemy", **kwargs)


# Export public API (SQLAlchemy ONLY)
__all__ = [
    # Primary classes (SQLAlchemy only)
    "SQLAlchemyLoader",
    "LoadResult",
    "SQLAlchemyLoadError",

    # Factory functions (SQLAlchemy only)
    "create_loader",
    "load_opportunities",

    # Legacy function (redirects to SQLAlchemy)
    "load_opportunities_to_supabase",

    # Constants (always available)
    "DEFAULT_PIPELINE_NAME",
    "DEFAULT_TABLE_NAME",
    "DEFAULT_PRIMARY_KEY",
    "DEFAULT_WRITE_DISPOSITION",

    # Availability flags
    "SQLALCHEMY_AVAILABLE",
    "SQLALCHEMY_IMPORT_SUCCESS"
]

# Version information
__version__ = "2.0.0"  # Major version bump for SQLAlchemy default
__author__ = "RedditHarbor Pipeline v2 Team"
__migration_status__ = "SQLAlchemy Only (DLT Completely Removed)"
