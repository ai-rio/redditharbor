#!/usr/bin/env python3
"""
Simple test script to verify all imports work and pipeline can reach Step 6
"""

import sys
from pathlib import Path

# Add pipeline-v2 to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing imports...")

try:
    print("1. Quality filters...")
    from filters.quality import should_analyze_with_ai, filter_submissions_batch
    print("✓ Quality filters available")

    print("2. Deduplication...")
    from deduplication.concept_tracker import should_run_agno_analysis
    print("✓ Deduplication available")

    print("3. Analysis...")
    from analysis import OpportunityAnalyzer
    print("✓ Analysis available")

    print("4. Trust validation...")
    from trust.validator import TrustValidator
    print("✓ Trust validator available")

    print("5. DLT storage...")
    from storage import DLTLoader, create_dlt_loader
    print("✓ DLT storage available")

    print("\n✓ All imports successful! Pipeline components are ready.")

    # Test DLT functionality
    print("\nTesting DLT configuration...")
    try:
        loader = create_dlt_loader("test_pipeline", use_local_dev=True)
        print("✓ DLT loader created successfully")

        # Test connection validation
        if hasattr(loader, 'validate_connection'):
            connection_ok = loader.validate_connection()
            print(f"✓ DLT connection validation: {connection_ok}")

    except Exception as e:
        print(f"✗ DLT test failed: {e}")

except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()