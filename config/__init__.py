"""
RedditHarbor Configuration Package

Provides access to all configuration settings with backward compatibility.
"""

# Import all settings
import os

# Backward compatibility for direct imports
import sys

from .settings import *

config_dir = os.path.dirname(__file__)
sys.path.insert(0, config_dir)

# Maintain original redditharbor_config import
try:
    import redditharbor_config as original_config

    # Expose all original variables at package level
    for key in dir(original_config):
        if not key.startswith("_"):
            globals()[key] = getattr(original_config, key)
except ImportError:
    # During migration, settings might not exist yet
    pass

__all__ = [key for key in globals().keys() if not key.startswith("_")]
