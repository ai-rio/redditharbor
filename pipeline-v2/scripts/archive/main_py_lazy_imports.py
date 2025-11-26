
# Add these lazy imports at the top of main.py to replace heavy imports
import sys
import os

# Add pipeline-v2 to path
sys.path.insert(0, os.path.dirname(__file__))

class LazyModule:
    """Lazy import wrapper for heavy dependencies"""
    def __init__(self, module_name):
        self.module_name = module_name
        self._module = None

    def __getattr__(self, name):
        if self._module is None:
            import importlib
            self._module = importlib.import_module(self.module_name)
        return getattr(self._module, name)

# Create lazy modules for heavy dependencies
pandas = LazyModule('pandas')
sqlalchemy = LazyModule('sqlalchemy')

# Replace:
# import pandas as pd
# from sqlalchemy import create_engine

# With:
# Use pandas directly (will load on first access)
# Use sqlalchemy directly (will load on first access)
