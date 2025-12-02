#!/usr/bin/env python3
"""Debug exactly where the DLT import is coming from in SQLAlchemy loader"""

import sys
import os
from pathlib import Path

# Add pipeline-v2 to path
pipeline_v2_path = Path(__file__).parent / "pipeline-v2"
sys.path.insert(0, str(pipeline_v2_path))

# Set environment to match pipeline
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"

print("=== Debugging SQLAlchemy Import Chain ===")

print("\nStep 1: Testing SQLAlchemy imports...")
try:
    from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, DateTime, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
    from sqlalchemy.pool import QueuePool
    print("✅ SQLAlchemy imports work")
except ImportError as e:
    print(f"❌ SQLAlchemy import failed: {e}")

print("\nStep 2: Testing path setup (as done in sqlalchemy_loader.py)...")
project_root = os.path.abspath(os.path.join(pipeline_v2_path, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"✅ Added project root to path: {project_root}")

print("\nStep 3: Testing core.utils.id_resolver import (as done in sqlalchemy_loader.py)...")
try:
    from core.utils.id_resolver import resolve_submission_id, ResolutionResult
    print("✅ core.utils.id_resolver import works")
except ImportError as e:
    print(f"❌ core.utils.id_resolver import failed: {e}")
    import traceback
    traceback.print_exc()

print("\nStep 4: Testing the exact storage.sqlalchemy_loader import...")
try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ storage.sqlalchemy_loader import works")
except ImportError as e:
    print(f"❌ storage.sqlalchemy_loader import failed: {e}")
    print("🔥 This is where the DLT error is coming from!")
    import traceback
    traceback.print_exc()

print("\nStep 5: Testing the create_sqlalchemy_loader function...")
try:
    loader = create_sqlalchemy_loader("postgresql://postgres:postgres@127.0.0.1:54331/postgres")
    print("✅ create_sqlalchemy_loader works")
except Exception as e:
    print(f"❌ create_sqlalchemy_loader failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Summary ===")
print("If Step 4 fails with 'No module named dlt.common', then:")
print("1. Something in storage.sqlalchemy_loader is importing DLT")
print("2. Something in the import chain is importing DLT")
print("3. There might be a circular import or lazy loading issue")