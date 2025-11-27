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

# Import SQLAlchemy components (new default)
try:
    from .sqlalchemy_loader import SQLAlchemyLoader, LoadResult, SQLAlchemyLoadError
    from .dlt_compatibility_adapter import DLTCompatibilityAdapter
    SQLALCHEMY_IMPORT_SUCCESS = True
except ImportError as e:
    SQLALCHEMY_IMPORT_SUCCESS = False
    SQLAlchemyLoader = None
    LoadResult = None
    SQLAlchemyLoadError = None
    DLTCompatibilityAdapter = None

# Import DLT components (legacy support)
class LazyDLTModule:
    """Module-level lazy loading for DLT components."""

    def __init__(self):
        self._dlt_module = None
        self._imported = False

    def _ensure_imported(self):
        """Import DLT module only when needed."""
        if not self._imported:
            import importlib
            self._dlt_module = importlib.import_module('.dlt_loader', package=__package__)
            self._imported = True

    @property
    def DLTLoader(self):
        self._ensure_imported()
        return self._dlt_module.DLTLoader

    @property
    def DLTLoaderError(self):
        self._ensure_imported()
        return self._dlt_module.DLTLoaderError

    @property
    def DLTCredentialError(self):
        self._ensure_imported()
        return self._dlt_module.DLTCredentialError

    @property
    def DLTConnectionError(self):
        self._ensure_imported()
        return self._dlt_module.DLTConnectionError

    @property
    def create_dlt_loader(self):
        self._ensure_imported()
        return self._dlt_module.create_dlt_loader

    @property
    def load_opportunities_to_supabase(self):
        self._ensure_imported()
        return self._dlt_module.load_opportunities_to_supabase

# Create lazy module instance for DLT
_lazy_dlt = LazyDLTModule()

# Factory function for SQLAlchemy loader (NEW DEFAULT)
def create_loader(
    connection_string: str,
    loader_type: str = "sqlalchemy",  # Changed default from "dlt" to "sqlalchemy"
    **kwargs
):
    """
    Create a data loader instance.

    Args:
        connection_string: Database connection string
        loader_type: Type of loader to create ("sqlalchemy" or "dlt")
        **kwargs: Additional loader-specific parameters

    Returns:
        Loader instance (SQLAlchemyLoader by default)
    """
    if loader_type == "sqlalchemy":
        if not SQLALCHEMY_IMPORT_SUCCESS:
            raise ImportError("SQLAlchemy loader components not available")
        return SQLAlchemyLoader(connection_string, **kwargs)

    elif loader_type == "dlt":
        return _lazy_dlt.create_dlt_loader(connection_string, **kwargs)

    else:
        raise ValueError(f"Unknown loader type: {loader_type}")


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


# DLT compatibility function (legacy support)
def load_opportunities_to_supabase(data: list, **kwargs):
    """Legacy function for DLT compatibility. Use load_opportunities() instead."""
    return load_opportunities(data, loader_type="dlt", **kwargs)


# Module-level lazy loading for backward compatibility
def __getattr__(name):
    """Module-level lazy loading for backward compatibility."""
    # DLT-related attributes (legacy support)
    if name in ["DLTLoader", "DLTLoaderError", "DLTCredentialError", "DLTConnectionError"]:
        return getattr(_lazy_dlt, name)
    elif name in ["create_dlt_loader", "load_opportunities_to_supabase"]:
        return getattr(_lazy_dlt, name)

    # SQLAlchemy-related attributes (new default)
    elif name in ["SQLAlchemyLoader", "LoadResult", "SQLAlchemyLoadError", "DLTCompatibilityAdapter"]:
        if not SQLALCHEMY_IMPORT_SUCCESS:
            raise AttributeError(f"SQLAlchemy components not available: {name}")
        return globals()[name]

    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Export public API
__all__ = [
    # Primary classes (SQLAlchemy - NEW DEFAULT)
    "SQLAlchemyLoader",
    "LoadResult",
    "SQLAlchemyLoadError",
    "DLTCompatibilityAdapter",

    # Factory functions (SQLAlchemy default)
    "create_loader",
    "load_opportunities",

    # Legacy DLT support (backward compatibility)
    "load_opportunities_to_supabase",
    "DLTLoader",
    "DLTLoaderError",
    "DLTCredentialError",
    "DLTConnectionError",
    "create_dlt_loader",

    # Constants (always available)
    "DEFAULT_PIPELINE_NAME",
    "DEFAULT_TABLE_NAME",
    "DEFAULT_PRIMARY_KEY",
    "DEFAULT_WRITE_DISPOSITION",

    # Availability flags
    "SQLALCHEMY_AVAILABLE",
    "DLT_AVAILABLE",
    "SQLALCHEMY_IMPORT_SUCCESS"
]

# Version information
__version__ = "2.0.0"  # Major version bump for SQLAlchemy default
__author__ = "RedditHarbor Pipeline v2 Team"
__migration_status__ = "SQLAlchemy Default (Phase 4 Complete)"
