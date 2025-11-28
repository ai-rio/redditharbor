#!/usr/bin/env python3
"""Trace exactly when DLT modules appear in sys.modules"""

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

# Hook into import to detect DLT imports
original_import = __builtins__.__import__

def trace_import(name, *args, **kwargs):
    if 'dlt' in name.lower():
        print(f"🔥 DLT IMPORT DETECTED: {name}")
        print(f"   Call stack:")
        import traceback
        for i, frame in enumerate(traceback.extract_stack()[:-1]):
            print(f"   {i}: {frame.filename}:{frame.lineno} in {frame.name}")
    return original_import(name, *args, **kwargs)

__builtins__.__import__ = trace_import

# Set up logging and environment
logging.basicConfig(level=logging.WARNING)
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"

print("=== Tracing DLT Imports ===")
print("This will show us exactly when and where DLT is imported\n")

# Import main.py step by step to trigger the DLT import
print("1. Importing main components...")

# Import everything that main.py imports, step by step
imports_to_test = [
    ("import argparse", "import argparse"),
    ("import logging", "import logging"),
    ("import os", "import os"),
    ("import sys", "import sys"),
    ("import time", "import time"),
    ("from datetime import UTC, datetime", "from datetime import UTC, datetime"),
    ("from pathlib import Path", "from pathlib import Path"),
    ("from typing import Any", "from typing import Any"),
    ("import praw", "import praw"),
    ("from prawcore import ResponseException", "from prawcore import ResponseException"),
    ("from dotenv import load_dotenv", "from dotenv import load_dotenv"),
    ("load_dotenv", "load_dotenv(project_root / '.env.local', override=True)"),
]

# Import config settings
print("2. Importing config settings...")
try:
    from config.settings import ERROR_LOG_DIR, REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT, SUPABASE_KEY, SUPABASE_URL
    print("✅ Config settings imported")
except Exception as e:
    print(f"❌ Config settings failed: {e}")

# Check DLT modules
dlt_modules = [m for m in sys.modules.keys() if 'dlt' in m]
print(f"DLT modules so far: {dlt_modules}")

# Import deduplication
print("\n3. Importing deduplication...")
try:
    from pipeline_v2.deduplication.concept_tracker import (
        copy_agno_from_primary, copy_profiler_from_primary, should_run_agno_analysis,
        should_run_profiler_analysis, update_concept_agno_stats, update_concept_profiler_stats
    )
    print("✅ Deduplication imported")
except Exception as e:
    print(f"❌ Deduplication failed: {e}")

# Check DLT modules again
dlt_modules = [m for m in sys.modules.keys() if 'dlt' in m]
print(f"DLT modules after deduplication: {dlt_modules}")

# Import core agents
print("\n4. Importing core agents...")
try:
    from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer
    print("✅ Monetization analyzer imported")
except Exception as e:
    print(f"❌ Monetization analyzer failed: {e}")

try:
    from core.agents.profiler.enhanced_profiler import EnhancedLLMProfiler
    print("✅ Enhanced profiler imported")
except Exception as e:
    print(f"❌ Enhanced profiler failed: {e}")

# Check DLT modules again
dlt_modules = [m for m in sys.modules.keys() if 'dlt' in m]
print(f"DLT modules after core agents: {dlt_modules}")

# Now the critical test - try SQLAlchemy import
print("\n5. Testing SQLAlchemy import...")
try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ SQLAlchemy import works!")
except ImportError as e:
    print(f"❌ SQLAlchemy import FAILED: {e}")

print(f"\nFinal DLT modules: {[m for m in sys.modules.keys() if 'dlt' in m]}")