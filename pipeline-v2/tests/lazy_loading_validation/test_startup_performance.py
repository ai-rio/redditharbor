#!/usr/bin/env python3
"""
Simple Startup Performance Test

Quick test to measure the main pipeline startup time improvement
after implementing DLT lazy loading.

Usage:
    python test_startup_performance.py

Expected Results:
- Before lazy loading: ~5.68s startup time
- After lazy loading: <2s startup time (65%+ improvement)

Author: Pipeline Performance Testing
Version: Startup Performance Test v1.0
"""

import sys
import time
from pathlib import Path

# Add pipeline-v2 to path
pipeline_v2_root = Path(__file__).parent
sys.path.insert(0, str(pipeline_v2_root))

def measure_startup_time():
    """Measure the startup time for main pipeline import."""
    print("🚀 Measuring main pipeline startup time...")
    print("   This tests the import time after DLT lazy loading implementation")
    print("-" * 60)

    # Clear any existing imports to get fresh measurement
    modules_to_remove = [k for k in sys.modules.keys() if k.startswith('main') or k.startswith('pipeline')]
    for module in modules_to_remove:
        sys.modules.pop(module, None)

    # Measure import time
    start_time = time.time()

    try:
        import main
        import_time = time.time() - start_time

        print(f"✅ Main pipeline imported successfully")
        print(f"📊 Import time: {import_time:.3f} seconds")
        print(f"📈 Milliseconds: {import_time * 1000:.1f} ms")

        # Performance analysis
        original_time = 5.68  # Original startup time before lazy loading
        improvement = ((original_time - import_time) / original_time) * 100

        print(f"\n🎯 Performance Analysis:")
        print(f"   Original startup time: {original_time:.2f}s")
        print(f"   Current startup time:  {import_time:.3f}s")
        print(f"   Improvement:           {improvement:.1f}%")

        # Performance rating
        if import_time < 2.0:
            rating = "🏆 EXCELLENT"
            recommendation = "Target achieved! Excellent lazy loading implementation."
        elif import_time < 3.0:
            rating = "✅ GOOD"
            recommendation = "Good improvement, but could be optimized further."
        else:
            rating = "⚠️ NEEDS IMPROVEMENT"
            recommendation = "Lazy loading needs optimization to meet target."

        print(f"   Rating: {rating}")
        print(f"   Recommendation: {recommendation}")

        # Check availability flags
        print(f"\n🔧 Module Availability:")
        print(f"   Quality filters: {getattr(main, 'QUALITY_FILTERS_AVAILABLE', False)}")
        print(f"   Deduplication: {getattr(main, 'DEDUPLICATION_AVAILABLE', False)}")
        print(f"   Opportunity analyzer: {getattr(main, 'OPPORTUNITY_ANALYZER_AVAILABLE', False)}")
        print(f"   Trust validator: {getattr(main, 'TRUST_VALIDATOR_AVAILABLE', False)}")
        print(f"   DLT storage: {getattr(main, 'DLT_STORAGE_AVAILABLE', False)}")
        print(f"   Supabase: {getattr(main, 'SUPABASE_AVAILABLE', False)}")

        return import_time, improvement

    except Exception as e:
        import_time = time.time() - start_time
        print(f"❌ Failed to import main pipeline after {import_time:.3f}s")
        print(f"   Error: {e}")
        return import_time, 0

def test_dlt_lazy_import():
    """Test DLT lazy import timing."""
    print(f"\n🐢 Testing DLT lazy import behavior...")

    # Test fast storage import
    start_time = time.time()
    try:
        from storage import DLT_AVAILABLE, DEFAULT_PIPELINE_NAME, DEFAULT_TABLE_NAME
        storage_import_time = time.time() - start_time

        print(f"✅ Storage module constants imported in {storage_import_time:.4f}s")
        print(f"   DLT_AVAILABLE: {DLT_AVAILABLE}")
        print(f"   DEFAULT_PIPELINE_NAME: {DEFAULT_PIPELINE_NAME}")

    except Exception as e:
        storage_import_time = time.time() - start_time
        print(f"❌ Storage module import failed after {storage_import_time:.4f}s: {e}")

    # Test DLT loader lazy import
    start_time = time.time()
    try:
        from storage import DLTLoader
        dlt_import_time = time.time() - start_time

        print(f"✅ DLTLoader lazy imported in {dlt_import_time:.3f}s")

    except ImportError as e:
        dlt_import_time = time.time() - start_time
        print(f"⚠️ DLT not available (expected): {e}")
    except Exception as e:
        dlt_import_time = time.time() - start_time
        print(f"❌ DLT import failed after {dlt_import_time:.3f}s: {e}")

def main():
    """Main test execution."""
    print("RedditHarbor Pipeline v2 - Startup Performance Test")
    print("Testing DLT Lazy Loading Implementation")
    print("=" * 60)

    # Measure main startup time
    startup_time, improvement = measure_startup_time()

    # Test DLT lazy import behavior
    test_dlt_lazy_import()

    # Final summary
    print(f"\n📋 Summary:")
    print(f"   Startup time: {startup_time:.3f}s")
    print(f"   Improvement: {improvement:.1f}%")

    # Success criteria
    target_met = startup_time < 3.0  # Target: under 3 seconds
    excellent_met = startup_time < 2.0  # Excellent: under 2 seconds

    print(f"\n🎯 Success Criteria:")
    print(f"   Target (<3s): {'✅ MET' if target_met else '❌ NOT MET'}")
    print(f"   Excellent (<2s): {'✅ MET' if excellent_met else '❌ NOT MET'}")

    if target_met:
        print(f"\n🎉 Lazy loading implementation SUCCESS!")
        if excellent_met:
            print(f"   Outstanding performance improvement achieved!")
        else:
            print(f"   Good performance improvement achieved.")
    else:
        print(f"\n⚠️ Lazy loading needs optimization to meet target.")

    return 0 if target_met else 1

if __name__ == "__main__":
    sys.exit(main())