"""Database loading module for Pipeline v3"""

# Lazy imports to avoid sqlalchemy dependency issues
def get_database_loader():
    """Lazy import of DatabaseLoader to avoid sqlalchemy dependency"""
    from .database import DatabaseLoader
    return DatabaseLoader

def get_onlymaps_database_loader():
    """Lazy import of OnlyMapsDatabaseLoader to avoid sqlalchemy dependency"""
    from .onlymaps_database import OnlyMapsDatabaseLoader
    return OnlyMapsDatabaseLoader

# Import DatabaseLoader directly for compatibility
from .database import DatabaseLoader

__all__ = ["get_database_loader", "get_onlymaps_database_loader", "DatabaseLoader"]
