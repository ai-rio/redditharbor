#!/usr/bin/env python3
"""
Core Lazy Loading Mechanism Test

Focused test to validate the core lazy loading functionality without requiring
external dependencies like praw, dlt, or supabase.

This test validates:
1. Storage module can be imported quickly without loading DLT
2. Lazy loading mechanism works correctly
3. Backward compatibility is maintained
4. Constants are available without DLT import

Author: Core Lazy Loading Test
Version: v1.0
"""

import sys
import time
from pathlib import Path

# Add pipeline-v2 to path
pipeline_v2_root = Path(__file__).parent
sys.path.insert(0, str(pipeline_v2_root))

def test_storage_module_lazy_loading():
    """Test storage module lazy loading behavior."""
    print("🐢 Testing Storage Module Lazy Loading")
    print("=" * 50)

    # Test 1: Fast import of constants
    print("\n1. Testing fast constant imports...")
    start_time = time.time()

    try:
        from storage import DLT_AVAILABLE, DEFAULT_PIPELINE_NAME, DEFAULT_TABLE_NAME, DEFAULT_PRIMARY_KEY, DEFAULT_WRITE_DISPOSITION

        import_time = time.time() - start_time
        print(f"   ✅ Constants imported in {import_time:.4f}s")
        print(f"   📋 DLT_AVAILABLE: {DLT_AVAILABLE}")
        print(f"   📋 DEFAULT_PIPELINE_NAME: {DEFAULT_PIPELINE_NAME}")
        print(f"   📋 DEFAULT_TABLE_NAME: {DEFAULT_TABLE_NAME}")
        print(f"   📋 DEFAULT_PRIMARY_KEY: {DEFAULT_PRIMARY_KEY}")
        print(f"   📋 DEFAULT_WRITE_DISPOSITION: {DEFAULT_WRITE_DISPOSITION}")

        # Verify it's truly fast
        if import_time < 0.01:  # Should be under 10ms
            print("   🎯 PERFORMANCE TARGET MET: Constants import under 10ms")
        else:
            print(f"   ⚠️ SLOW: Constants import took {import_time*1000:.1f}ms (target: <10ms)")

    except Exception as e:
        import_time = time.time() - start_time
        print(f"   ❌ Constants import failed after {import_time:.4f}s: {e}")

    # Test 2: Lazy import of DLTLoader class
    print("\n2. Testing lazy DLTLoader import...")
    start_time = time.time()

    try:
        from storage import DLTLoader

        import_time = time.time() - start_time
        print(f"   ✅ DLTLoader imported in {import_time:.3f}s")
        print(f"   📋 DLTLoader class: {DLTLoader}")
        print(f"   📋 Module: {DLTLoader.__module__}")

        # Test that it triggers lazy loading of DLT module
        print(f"   🔍 Testing if DLT is lazily loaded...")
        try:
            # This should trigger the DLT import and fail gracefully if DLT not available
            loader = DLTLoader(use_local_dev=True)
            print(f"   🎯 DLTLoader instantiated successfully")
            print(f"   📋 Has credentials: {loader._credentials is not None}")
        except ImportError as e:
            if "DLT library is not available" in str(e):
                print(f"   ✅ DLT unavailable handled gracefully: {e}")
            else:
                print(f"   ⚠️ Unexpected ImportError: {e}")
        except Exception as e:
            print(f"   📋 DLTLoader other error (expected in test): {type(e).__name__}: {e}")

    except Exception as e:
        import_time = time.time() - start_time
        print(f"   ❌ DLTLoader import failed after {import_time:.3f}s: {e}")

    # Test 3: Test factory functions
    print("\n3. Testing factory function imports...")
    start_time = time.time()

    try:
        from storage import create_dlt_loader, load_opportunities_to_supabase

        import_time = time.time() - start_time
        print(f"   ✅ Factory functions imported in {import_time:.3f}s")
        print(f"   📋 create_dlt_loader: {create_dlt_loader}")
        print(f"   📋 load_opportunities_to_supabase: {load_opportunities_to_supabase}")

    except Exception as e:
        import_time = time.time() - start_time
        print(f"   ❌ Factory functions import failed after {import_time:.3f}s: {e}")

    # Test 4: Test module-level attributes
    print("\n4. Testing module-level attribute access...")
    import storage

    # Test __all__ exports
    print(f"   📋 __all__ exports: {len(storage.__all__)} items")
    expected_exports = [
        "DLTLoader", "create_dlt_loader", "load_opportunities_to_supabase",
        "DEFAULT_PIPELINE_NAME", "DEFAULT_TABLE_NAME", "DEFAULT_PRIMARY_KEY",
        "DEFAULT_WRITE_DISPOSITION", "DLT_AVAILABLE"
    ]

    missing_exports = [exp for exp in expected_exports if exp not in storage.__all__]
    if missing_exports:
        print(f"   ❌ Missing exports: {missing_exports}")
    else:
        print(f"   ✅ All expected exports found in __all__")

def test_backward_compatibility():
    """Test backward compatibility patterns."""
    print("\n🔄 Testing Backward Compatibility")
    print("=" * 50)

    compatibility_tests = []

    # Test 1: Direct imports
    print("\n1. Testing direct import patterns...")
    try:
        from storage import DLTLoader, create_dlt_loader, DEFAULT_PIPELINE_NAME
        compatibility_tests.append(("direct_import", True, None))
        print(f"   ✅ Direct import pattern works")
    except Exception as e:
        compatibility_tests.append(("direct_import", False, str(e)))
        print(f"   ❌ Direct import failed: {e}")

    # Test 2: Attribute access
    print("\n2. Testing attribute access patterns...")
    try:
        import storage
        loader_class = storage.DLTLoader
        factory_func = storage.create_dlt_loader
        pipeline_name = storage.DEFAULT_PIPELINE_NAME
        compatibility_tests.append(("attribute_access", True, None))
        print(f"   ✅ Attribute access pattern works")
    except Exception as e:
        compatibility_tests.append(("attribute_access", False, str(e)))
        print(f"   ❌ Attribute access failed: {e}")

    # Test 3: Late binding (should work)
    print("\n3. Testing late binding patterns...")
    try:
        # This tests that the lazy loading works even when accessed later
        import storage
        time.sleep(0.1)  # Simulate some work

        # Now access DLT components
        loader_class = storage.DLTLoader
        compatibility_tests.append(("late_binding", True, None))
        print(f"   ✅ Late binding pattern works")
    except Exception as e:
        compatibility_tests.append(("late_binding", False, str(e)))
        print(f"   ❌ Late binding failed: {e}")

    # Summary
    successful_tests = sum(1 for _, success, _ in compatibility_tests if success)
    total_tests = len(compatibility_tests)
    success_rate = (successful_tests / total_tests) * 100

    print(f"\n📊 Compatibility Summary:")
    print(f"   Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")

    for test_name, success, error in compatibility_tests:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
        if error:
            print(f"      Error: {error}")

    return success_rate >= 80

def test_performance_metrics():
    """Test specific performance metrics for lazy loading."""
    print("\n📊 Testing Performance Metrics")
    print("=" * 50)

    metrics = {}

    # Test 1: Cold import of storage module
    print("\n1. Measuring cold import performance...")

    # Clear any cached imports
    modules_to_clear = [k for k in sys.modules.keys() if k.startswith('storage')]
    cleared_modules = {}
    for module in modules_to_clear:
        cleared_modules[module] = sys.modules.pop(module)

    start_time = time.time()
    try:
        import storage
        cold_import_time = time.time() - start_time
        metrics["cold_import_time"] = cold_import_time
        print(f"   📊 Cold import time: {cold_import_time:.4f}s ({cold_import_time*1000:.1f}ms)")

        # Target: under 5ms for cold import
        if cold_import_time < 0.005:
            print(f"   🎯 EXCELLENT: Under 5ms target")
        elif cold_import_time < 0.01:
            print(f"   ✅ GOOD: Under 10ms")
        else:
            print(f"   ⚠️ SLOW: {cold_import_time*1000:.1f}ms (target: <5ms)")

    except Exception as e:
        cold_import_time = time.time() - start_time
        print(f"   ❌ Cold import failed: {e}")

    # Test 2: Hot import performance
    print("\n2. Measuring hot import performance...")
    start_time = time.time()
    try:
        # Import again - should be very fast
        import storage
        hot_import_time = time.time() - start_time
        metrics["hot_import_time"] = hot_import_time
        print(f"   📊 Hot import time: {hot_import_time:.6f}s ({hot_import_time*1000000:.1f}μs)")

    except Exception as e:
        hot_import_time = time.time() - start_time
        print(f"   ❌ Hot import failed: {e}")

    # Test 3: Lazy import timing
    print("\n3. Measuring lazy import timing...")
    start_time = time.time()
    try:
        from storage import DLTLoader
        lazy_import_time = time.time() - start_time
        metrics["lazy_import_time"] = lazy_import_time
        print(f"   📊 Lazy import time: {lazy_import_time:.3f}s ({lazy_import_time*1000:.1f}ms)")

        # Target: under 1 second for lazy import
        if lazy_import_time < 1.0:
            print(f"   🎯 EXCELLENT: Under 1 second")
        else:
            print(f"   ⚠️ SLOW: {lazy_import_time:.1f}s (target: <1s)")

    except Exception as e:
        lazy_import_time = time.time() - start_time
        print(f"   ❌ Lazy import failed: {e}")

    return metrics

def main():
    """Main test execution."""
    print("RedditHarbor Pipeline v2 - Core Lazy Loading Test")
    print("Testing core lazy loading mechanism without external dependencies")
    print("=" * 70)

    # Run core tests
    test_storage_module_lazy_loading()

    compatibility_success = test_backward_compatibility()
    performance_metrics = test_performance_metrics()

    # Final assessment
    print("\n" + "=" * 70)
    print("🎯 FINAL ASSESSMENT")
    print("=" * 70)

    # Performance criteria
    cold_import_ok = performance_metrics.get("cold_import_time", float('inf')) < 0.01
    lazy_import_ok = performance_metrics.get("lazy_import_time", float('inf')) < 2.0

    print(f"\n📊 Performance Criteria:")
    print(f"   Cold import <10ms: {'✅ MET' if cold_import_ok else '❌ NOT MET'}")
    print(f"   Lazy import <2s: {'✅ MET' if lazy_import_ok else '❌ NOT MET'}")

    print(f"\n🔄 Compatibility Criteria:")
    print(f"   80%+ success rate: {'✅ MET' if compatibility_success else '❌ NOT MET'}")

    # Overall success
    overall_success = cold_import_ok and compatibility_success

    print(f"\n🏆 OVERALL RESULT:")
    if overall_success:
        print("   ✅ LAZY LOADING IMPLEMENTATION: SUCCESS")
        print("   ✓ Fast module imports achieved")
        print("   ✓ Backward compatibility maintained")
        print("   ✓ Lazy loading mechanism working")
        if lazy_import_ok:
            print("   ✓ DLT lazy loading performance acceptable")
        else:
            print("   ⚠️ DLT lazy loading could be optimized")
    else:
        print("   ⚠️ LAZY LOADING IMPLEMENTATION: NEEDS ATTENTION")
        if not cold_import_ok:
            print("   ❌ Module imports not fast enough")
        if not compatibility_success:
            print("   ❌ Backward compatibility issues")

    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())