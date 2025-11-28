#!/usr/bin/env python3
"""Debug which core agent is triggering DLT imports"""

import sys
import os
import logging
from pathlib import Path

# Set up paths
pipeline_v2_root = Path(__file__).parent / "pipeline-v2"
project_root = Path(__file__).parent
sys.path.insert(0, str(pipeline_v2_root))
sys.path.insert(1, str(project_root))

# Set up logging
logging.basicConfig(level=logging.WARNING, format='%(filename)s:%(lineno)d - %(levelname)s - %(message)s')

# Set environment
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"

print("=== Debugging Core Agent Imports ===")

print("\n1. Checking DLT modules before any imports...")
dlt_modules_before = [m for m in sys.modules.keys() if 'dlt' in m]
print(f"DLT modules before: {dlt_modules_before}")

print("\n2. Testing MonetizationAgnoAnalyzer import...")
try:
    from core.agents.monetization.agno_analyzer import MonetizationAgnoAnalyzer
    print("✅ MonetizationAgnoAnalyzer import works")
except Exception as e:
    print(f"❌ MonetizationAgnoAnalyzer import failed: {e}")

dlt_modules_after_monetization = [m for m in sys.modules.keys() if 'dlt' in m]
print(f"DLT modules after monetization: {dlt_modules_after_monetization}")

if len(dlt_modules_after_monetization) > len(dlt_modules_before):
    print("🔥 MonetizationAgnoAnalyzer is importing DLT!")

print("\n3. Testing EnhancedLLMProfiler import...")
try:
    from core.agents.profiler.enhanced_profiler import EnhancedLLMProfiler
    print("✅ EnhancedLLMProfiler import works")
except Exception as e:
    print(f"❌ EnhancedLLMProfiler import failed: {e}")

dlt_modules_after_profiler = [m for m in sys.modules.keys() if 'dlt' in m]
print(f"DLT modules after profiler: {dlt_modules_after_profiler}")

if len(dlt_modules_after_profiler) > len(dlt_modules_after_monetization):
    print("🔥 EnhancedLLMProfiler is importing DLT!")

print("\n4. Testing TrustValidator import...")
try:
    from trust.validator import TrustValidator
    print("✅ TrustValidator import works")
except Exception as e:
    print(f"❌ TrustValidator import failed: {e}")

dlt_modules_after_trust = [m for m in sys.modules.keys() if 'dlt' in m]
print(f"DLT modules after trust: {dlt_modules_after_trust}")

if len(dlt_modules_after_trust) > len(dlt_modules_after_profiler):
    print("🔥 TrustValidator is importing DLT!")

print("\n5. NOW testing SQLAlchemy import after all core agents...")
try:
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ SQLAlchemy import works")
except ImportError as e:
    print(f"❌ SQLAlchemy import FAILED: {e}")
    print("🔥 This confirms DLT modules are causing the conflict!")

print(f"\nFinal DLT modules in sys.modules: {[m for m in sys.modules.keys() if 'dlt' in m]}")