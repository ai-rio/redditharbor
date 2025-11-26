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

# Constants (available without importing DLT)
DEFAULT_PIPELINE_NAME = "reddit_opportunity_pipeline_v2"
DEFAULT_TABLE_NAME = "app_opportunities"
DEFAULT_PRIMARY_KEY = "submission_id"
DEFAULT_WRITE_DISPOSITION = "merge"

# DLT availability flag - DLT will be imported lazily
DLT_AVAILABLE = True


# Lazy module-level properties for backward compatibility
class LazyModule:
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
        """Lazy access to DLTLoader class."""
        self._ensure_imported()
        return self._dlt_module.DLTLoader

    @property
    def DLTLoaderError(self):
        """Lazy access to DLTLoaderError class."""
        self._ensure_imported()
        return self._dlt_module.DLTLoaderError

    @property
    def DLTCredentialError(self):
        """Lazy access to DLTCredentialError class."""
        self._ensure_imported()
        return self._dlt_module.DLTCredentialError

    @property
    def DLTConnectionError(self):
        """Lazy access to DLTConnectionError class."""
        self._ensure_imported()
        return self._dlt_module.DLTConnectionError

    @property
    def create_dlt_loader(self):
        """Lazy access to create_dlt_loader function."""
        self._ensure_imported()
        return self._dlt_module.create_dlt_loader

    @property
    def load_opportunities_to_supabase(self):
        """Lazy access to load_opportunities_to_supabase function."""
        self._ensure_imported()
        return self._dlt_module.load_opportunities_to_supabase

# Create lazy module instance
_lazy = LazyModule()

# Expose lazy variables at module level for backward compatibility
def __getattr__(name):
    """Module-level lazy loading for backward compatibility."""
    if hasattr(_lazy, name):
        return getattr(_lazy, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Export public API
__all__ = [
    # Main classes (backward compatibility)
    "DLTLoader",
    "DLTLoaderError",
    "DLTCredentialError",
    "DLTConnectionError",

    # Factory functions (backward compatibility)
    "create_dlt_loader",
    "load_opportunities_to_supabase",

    # Constants (always available)
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