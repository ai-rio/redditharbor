#!/usr/bin/env python3
"""Debug the exact import pattern from main.py to find DLT trigger"""

import sys
import os
import logging
from pathlib import Path

# Exact same path setup as main.py
pipeline_v2_root = Path(__file__).parent / "pipeline-v2"
project_root = Path(__file__).parent
sys.path.insert(0, str(pipeline_v2_root))
sys.path.insert(1, str(project_root))

# Set up logging exactly like main.py
logging.basicConfig(level=logging.WARNING)

# Set environment
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"

print("=== Debugging Exact Main.py Import Pattern ===")
print(f"Pipeline-v2 path: {pipeline_v2_root}")
print(f"Project root: {project_root}")
print(f"sys.path[0]: {sys.path[0]}")
print(f"sys.path[1]: {sys.path[1]}")

print("\nStep 1: Testing the exact import pattern from main.py lines 154-161...")
try:
    # This is exactly what main.py does
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    SQLALCHEMY_STORAGE_AVAILABLE = True
    logging.info(f"✅ SQLAlchemy storage imported successfully")
    print("✅ Exact main.py import pattern works")
except ImportError as e:
    SQLALCHEMY_STORAGE_AVAILABLE = False
    logging.warning(f"❌ SQLAlchemy storage module not available: {e}")
    print(f"❌ Exact main.py import pattern failed: {e}")
    print("🔥 This is the exact error from main.py!")
    import traceback
    traceback.print_exc()

print("\nStep 2: Check if there are any circular imports...")
print("Testing storage module import first...")
try:
    import storage
    print("✅ storage module imports fine")
except Exception as e:
    print(f"❌ storage module import failed: {e}")

print("\nTesting storage.sqlalchemy_loader import after storage import...")
try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ sqlalchemy_loader imports fine after storage import")
except Exception as e:
    print(f"❌ sqlalchemy_loader import failed after storage import: {e}")

print("\nStep 3: Check module loading order...")
print("Current modules loaded:", [m for m in sys.modules.keys() if 'storage' in m or 'dlt' in m])