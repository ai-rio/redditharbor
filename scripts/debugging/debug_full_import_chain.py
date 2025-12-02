#!/usr/bin/env python3
"""Debug the full import chain to see what triggers DLT import"""

import sys
import os
import logging
from pathlib import Path
from datetime import UTC, datetime
from typing import Any

# Exact same path setup as main.py
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

# Set up logging exactly like main.py
logging.basicConfig(level=logging.WARNING, format='%(filename)s:%(lineno)d - %(levelname)s - %(message)s')

# Set environment
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"

print("=== Debugging Full Import Chain ===")

# Import all the modules that main.py imports BEFORE SQLAlchemy

print("\n1. Importing praw...")
try:
    import praw
    from prawcore import ResponseException
    print("✅ praw imports work")
except Exception as e:
    print(f"❌ praw import failed: {e}")

print("\n2. Loading dotenv...")
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env.local', override=True)
    print("✅ dotenv loading works")
except Exception as e:
    print(f"❌ dotenv loading failed: {e}")

print("\n3. Importing config settings...")
try:
    from config.settings import ERROR_LOG_DIR, REDDIT_PUBLIC, REDDIT_SECRET, REDDIT_USER_AGENT, SUPABASE_KEY, SUPABASE_URL
    print("✅ config settings imports work")
except Exception as e:
    print(f"❌ config settings imports failed: {e}")

print("\n4. Importing filters...")
try:
    from pipeline_v2.filters.quality import filter_submissions_batch, should_analyze_with_ai
    print("✅ filters imports work")
except Exception as e:
    print(f"❌ filters imports failed: {e}")

print("\n5. Importing deduplication...")
try:
    from pipeline_v2.deduplication.concept_tracker import (
        copy_agno_from_primary, copy_profiler_from_primary, should_run_agno_analysis,
        should_run_profiler_analysis, update_concept_agno_stats, update_concept_profiler_stats
    )
    print("✅ deduplication imports work")
except Exception as e:
    print(f"❌ deduplication imports failed: {e}")

print("\n6. Importing analysis...")
try:
    from analysis import OpportunityAnalyzer
    print("✅ analysis imports work")
except Exception as e:
    print(f"❌ analysis imports failed: {e}")

print("\n7. Importing core agents...")
try:
    from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer
    from core.agents.profiler.enhanced_profiler import EnhancedLLMProfiler
    print("✅ core agents imports work")
except Exception as e:
    print(f"❌ core agents imports failed: {e}")

print("\n8. Importing trust validator...")
try:
    from trust.validator import TrustValidator
    print("✅ trust validator imports work")
except Exception as e:
    print(f"❌ trust validator imports failed: {e}")

print("\n9. NOW testing the SQLAlchemy import...")
print("Modules loaded before SQLAlchemy import:", [m for m in sys.modules.keys() if 'storage' in m or 'dlt' in m])

try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    SQLALCHEMY_STORAGE_AVAILABLE = True
    logging.info(f"✅ SQLAlchemy storage imported successfully")
    print("✅ SQLAlchemy import works after all other imports")
except ImportError as e:
    SQLALCHEMY_STORAGE_AVAILABLE = False
    logging.warning(f"❌ SQLAlchemy storage module not available: {e}")
    print(f"❌ SQLAlchemy import FAILED: {e}")
    print("🔥 One of the previous imports is causing the DLT dependency!")

print("\n10. Checking if DLT is now in sys.modules...")
dlt_modules = [m for m in sys.modules.keys() if 'dlt' in m]
print("DLT modules in sys.modules:", dlt_modules)