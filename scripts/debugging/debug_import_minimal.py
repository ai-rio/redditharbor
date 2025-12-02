#!/usr/bin/env python3
"""
Minimal test to isolate the exact source of the DLT import error
"""

import sys
import os
from pathlib import Path

# Add pipeline-v2 to path to simulate the exact same environment
project_root = Path(__file__).parent
pipeline_v2_path = project_root / "pipeline-v2"
sys.path.insert(0, str(pipeline_v2_path))

print("=== Testing SQLAlchemy Import in Isolation ===")
print(f"Project root: {project_root}")
print(f"Pipeline-v2 path: {pipeline_v2_path}")
print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
print()

print("Step 1: Testing basic SQLAlchemy import...")
try:
    import sqlalchemy
    print("✅ Basic SQLAlchemy import works")
except ImportError as e:
    print(f"❌ Basic SQLAlchemy import failed: {e}")

print()
print("Step 2: Testing storage.sqlalchemy_loader import...")
try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ storage.sqlalchemy_loader import works")
except ImportError as e:
    print(f"❌ storage.sqlalchemy_loader import failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("Step 3: Testing core.utils.id_resolver import...")
try:
    from core.utils.id_resolver import resolve_submission_id, ResolutionResult
    print("✅ core.utils.id_resolver import works")
except ImportError as e:
    print(f"❌ core.utils.id_resolver import failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("Step 4: Testing the exact import pattern from main.py...")
try:
    # This mimics the exact import pattern from main.py lines 154-161
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    SQLALCHEMY_STORAGE_AVAILABLE = True
    print("✅ Main.py SQLAlchemy import pattern works")
except ImportError as e:
    SQLALCHEMY_STORAGE_AVAILABLE = False
    print(f"❌ Main.py SQLAlchemy import pattern failed: {e}")
    print(f"📍 This is the exact error you're seeing in the pipeline!")

print()
print("Step 5: Testing environment variables...")
db_url = os.getenv("DATABASE_URL", "Not set")
print(f"DATABASE_URL: {db_url}")

print()
print("=== Summary ===")
if SQLALCHEMY_STORAGE_AVAILABLE:
    print("✅ SQLAlchemy storage should work in pipeline")
else:
    print("❌ SQLAlchemy storage will fail in pipeline")
    print("🔧 The issue is likely a path/dependency problem when running via UV shell script")