"""
Load Module - Database Loaders for RedditHarbor Pipeline V4

This module provides the unified OpportunityLoader for saving and retrieving
Opportunity records from the database.
"""

from load.loader import Loader, OpportunityLoader

__all__ = ["Loader", "OpportunityLoader"]
