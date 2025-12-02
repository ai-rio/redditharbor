#!/usr/bin/env python3
"""
Test script that replicates main.py import logic to verify it works
"""

import sys
import logging
from pathlib import Path

# Replicate main.py path setup
pipeline_v2_root = Path(__file__).parent
project_root = Path(__file__).parent.parent

def ensure_path_order():
    """Ensure pipeline-v2 directory stays first in sys.path for local imports."""
    # Remove pipeline-v2 from anywhere in path
    while str(pipeline_v2_root) in sys.path:
        sys.path.remove(str(pipeline_v2_root))
    # Insert pipeline-v2 at the beginning
    sys.path.insert(0, str(pipeline_v2_root))

    # Ensure project root is in path (for core imports)
    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))

# Set up basic logging for import error handling
logging.basicConfig(level=logging.WARNING)

# Initial path setup
ensure_path_order()

print("Testing main.py import logic...")

# Replicate main.py imports
try:
    # Step 2: Quality filters
    ensure_path_order()
    from filters.quality import should_analyze_with_ai, filter_submissions_batch
    print("✓ Quality filters imported")
except ImportError as e:
    print(f"✗ Quality filters: {e}")

try:
    # Step 3: Deduplication
    ensure_path_order()
    from deduplication.concept_tracker import should_run_agno_analysis
    print("✓ Deduplication imported")
except ImportError as e:
    print(f"✗ Deduplication: {e}")

try:
    # Step 4: Analysis
    from analysis import OpportunityAnalyzer
    print("✓ Analysis imported")
except ImportError as e:
    print(f"✗ Analysis: {e}")

try:
    # Step 5: Trust validation
    ensure_path_order()
    from trust.validator import TrustValidator
    print("✓ Trust validator imported")
except ImportError as e:
    print(f"✗ Trust validator: {e}")

try:
    # DLT storage
    ensure_path_order()
    from storage import DLTLoader, create_dlt_loader, load_opportunities_to_supabase
    print("✓ Storage imported")
except ImportError as e:
    print(f"✗ Storage: {e}")

print("All main.py imports tested!")