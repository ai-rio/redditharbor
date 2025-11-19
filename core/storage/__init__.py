"""Storage layer for RedditHarbor.

This package provides unified storage services for all data persistence operations,
replacing scattered DLT code in monolithic scripts.

Components:
- DLTLoader: Unified DLT loading infrastructure
- OpportunityStore: Storage for opportunity analysis results
- ProfileStore: Storage for AI profiles
- HybridStore: Storage for hybrid submissions (trust pipeline)

Usage:
    from core.storage import DLTLoader
    from core.dlt import PK_SUBMISSION_ID

    loader = DLTLoader()
    loader.load(data, "app_opportunities", primary_key=PK_SUBMISSION_ID)
"""

from .dlt_loader import DLTLoader, LoadStatistics

__all__ = [
    "DLTLoader",
    "LoadStatistics",
]
