"""
RedditHarbor Core Functionality Package

Contains the main setup, templates, and collection logic for RedditHarbor.
"""

# Import main functions for easy access
try:
    from .collection import collect_data, get_collection_status
    from .setup import setup_redditharbor

    __all__ = ["collect_data", "get_collection_status", "setup_redditharbor"]
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")
    __all__ = []
