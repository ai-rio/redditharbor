#!/usr/bin/env python3
"""Test minimal main.py with only essential imports"""

import sys
import os
import logging
from pathlib import Path

# Set up paths exactly like main.py
pipeline_v2_root = Path(__file__).parent / "pipeline-v2"
project_root = Path(__file__).parent

def ensure_path_order():
    """Ensure pipeline-v2 directory stays first in sys.path for local imports."""
    pipeline_v2_str = str(pipeline_v2_root)
    project_root_str = str(project_root)

    while pipeline_v2_str in sys.path:
        sys.path.remove(pipeline_v2_str)
    while project_root_str in sys.path:
        sys.path.remove(project_root_str)

    sys.path.insert(0, pipeline_v2_str)
    sys.path.insert(1, project_root_str)

ensure_path_order()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set environment
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"

print("=== Testing Minimal Import Pattern ===")

print("1. Testing ONLY SQLAlchemy import (no other imports)...")

try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    SQLALCHEMY_STORAGE_AVAILABLE = True
    print("✅ SQLAlchemy import works in isolation")
except ImportError as e:
    print(f"❌ SQLAlchemy import failed: {e}")

print("\n2. Testing with praw import first...")
try:
    import praw
    print("✅ praw imported")
except Exception as e:
    print(f"❌ praw import failed: {e}")

try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ SQLAlchemy import works after praw")
except ImportError as e:
    print(f"❌ SQLAlchemy import failed after praw: {e}")

print("\n3. Testing with config import...")
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env.local', override=True)
    print("✅ dotenv loaded")
except Exception as e:
    print(f"❌ dotenv import failed: {e}")

try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ SQLAlchemy import works after config")
except ImportError as e:
    print(f"❌ SQLAlchemy import failed after config: {e}")

print(f"\n4. Current DLT modules: {[m for m in sys.modules.keys() if 'dlt' in m]}")

print("\n5. Testing ALL imports from main.py in order (except analysis)...")

# Import each section step by step and check DLT modules
imports_to_test = [
    ("praw", "import praw"),
    ("prawcore", "from prawcore import ResponseException"),
    ("dotenv", "from dotenv import load_dotenv"),
    ("config", "from config.settings import ERROR_LOG_DIR, REDDIT_PUBLIC"),
    ("filters", "from pipeline_v2.filters.quality import filter_submissions_batch"),
    ("deduplication", "from pipeline_v2.deduplication.concept_tracker import should_run_agno_analysis"),
    ("monetization", "from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer"),
    ("profiler", "from core.agents.profiler.enhanced_profiler import EnhancedLLMProfiler"),
]

for name, import_cmd in imports_to_test:
    print(f"\nTesting {name}...")
    try:
        exec(import_cmd)
        print(f"✅ {name} imported")
    except Exception as e:
        print(f"❌ {name} failed: {e}")

    dlt_modules = [m for m in sys.modules.keys() if 'dlt' in m]
    print(f"DLT modules after {name}: {dlt_modules}")

    # Test SQLAlchemy after each import
    try:
        exec("from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader")
        print(f"✅ SQLAlchemy still works after {name}")
    except ImportError as e:
        print(f"❌ SQLAlchemy BROKEN after {name}: {e}")
        print(f"🔥 {name} is causing the DLT import conflict!")
        break