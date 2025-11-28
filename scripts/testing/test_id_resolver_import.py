#!/usr/bin/env python3
"""Test importing core.utils.id_resolver in isolation"""

import sys
from pathlib import Path

# Add pipeline-v2 to path
pipeline_v2_path = Path(__file__).parent / "pipeline-v2"
sys.path.insert(0, str(pipeline_v2_path))

print("=== Testing ID Resolver Import ===")

try:
    from core.utils.id_resolver import resolve_submission_id, ResolutionResult
    print("✅ core.utils.id_resolver import works")
except ImportError as e:
    print(f"❌ core.utils.id_resolver import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing core.utils import ===")

try:
    import core.utils
    print("✅ core.utils import works")
except ImportError as e:
    print(f"❌ core.utils import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing core import ===")

try:
    import core
    print("✅ core import works")
except ImportError as e:
    print(f"❌ core import failed: {e}")
    import traceback
    traceback.print_exc()