#!/usr/bin/env python3
"""Debug storage module import to see if LazyDLTModule is triggering DLT import"""

import sys
import os
from pathlib import Path

# Add pipeline-v2 to path
pipeline_v2_path = Path(__file__).parent / "pipeline-v2"
sys.path.insert(0, str(pipeline_v2_path))

# Set environment to match pipeline
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"

print("=== Debugging Storage Import ===")

print("\nStep 1: Testing direct storage.sqlalchemy_loader import...")
try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ Direct sqlalchemy_loader import works")
except ImportError as e:
    print(f"❌ Direct sqlalchemy_loader import failed: {e}")

print("\nStep 2: Testing storage module import (the way main.py does it)...")
try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ storage.sqlalchemy_loader import works")
except ImportError as e:
    print(f"❌ storage.sqlalchemy_loader import failed: {e}")

print("\nStep 3: Testing if storage module has lazy DLT loading...")
try:
    import storage
    print("✅ storage module imported successfully")

    # Check if accessing any attribute triggers DLT import
    print("Available attributes in storage module:")
    print([attr for attr in dir(storage) if not attr.startswith('_')])

    # Try to access SQLAlchemy components
    print("\nTesting SQLAlchemy access...")
    loader = create_sqlalchemy_loader("postgresql://postgres:postgres@127.0.0.1:54331/postgres")
    print("✅ SQLAlchemy loader created successfully")

except ImportError as e:
    print(f"❌ storage module import failed: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 4: Testing storage module attribute access...")
try:
    from storage import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ Storage SQLAlchemy imports work")
except ImportError as e:
    print(f"❌ Storage SQLAlchemy imports failed: {e}")
    print("🔥 This would trigger the DLT import error!")
    import traceback
    traceback.print_exc()