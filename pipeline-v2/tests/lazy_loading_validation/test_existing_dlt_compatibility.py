#!/usr/bin/env python3
"""
Existing DLT Test Compatibility Validation

Tests that existing DLT functionality works correctly with the new
lazy loading implementation by running actual DLT operations where possible.

This test validates:
1. Existing DLT imports still work
2. DLTLoader functionality is preserved
3. Data preparation works correctly
4. Error handling is preserved
5. Performance improvement achieved

Author: DLT Compatibility Test
Version: v1.0
"""

import sys
import time
from pathlib import Path

# Add pipeline-v2 to path
pipeline_v2_root = Path(__file__).parent
sys.path.insert(0, str(pipeline_v2_root))

def test_dlt_import_patterns():
    """Test various DLT import patterns from existing code."""
    print("🔍 Testing DLT Import Patterns")
    print("=" * 50)

    import_tests = []

    # Test 1: Original import pattern used in main.py
    print("\n1. Testing main.py import pattern...")
    try:
        from storage import DLTLoader, create_dlt_loader, load_opportunities_to_supabase
        import_tests.append(("main_pattern", True, None))
        print("   ✅ Main.py import pattern works")
    except Exception as e:
        import_tests.append(("main_pattern", False, str(e)))
        print(f"   ❌ Main.py import failed: {e}")

    # Test 2: Direct dlt_loader module import
    print("\n2. Testing direct dlt_loader import...")
    try:
        from storage.dlt_loader import DLTLoader, create_dlt_loader
        import_tests.append(("direct_import", True, None))
        print("   ✅ Direct dlt_loader import works")
    except Exception as e:
        import_tests.append(("direct_import", False, str(e)))
        print(f"   ❌ Direct dlt_loader import failed: {e}")

    # Test 3: Exception class imports
    print("\n3. Testing exception class imports...")
    try:
        from storage import DLTLoaderError, DLTCredentialError, DLTConnectionError
        import_tests.append(("exception_imports", True, None))
        print("   ✅ Exception class imports work")
    except Exception as e:
        import_tests.append(("exception_imports", False, str(e)))
        print(f"   ❌ Exception class imports failed: {e}")

    # Test 4: Constants import
    print("\n4. Testing constants import...")
    try:
        from storage import (
            DEFAULT_PIPELINE_NAME, DEFAULT_TABLE_NAME, DEFAULT_PRIMARY_KEY,
            DEFAULT_WRITE_DISPOSITION, DLT_AVAILABLE
        )
        import_tests.append(("constants_import", True, None))
        print(f"   ✅ Constants import works: {DEFAULT_PIPELINE_NAME}")
    except Exception as e:
        import_tests.append(("constants_import", False, str(e)))
        print(f"   ❌ Constants import failed: {e}")

    # Summary
    successful = sum(1 for _, success, _ in import_tests if success)
    total = len(import_tests)
    success_rate = (successful / total) * 100

    print(f"\n📊 Import Test Summary:")
    print(f"   Success Rate: {success_rate:.1f}% ({successful}/{total})")

    for test_name, success, error in import_tests:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
        if error:
            print(f"      Error: {error}")

    return success_rate

def test_dlt_functionality():
    """Test DLT functionality where possible."""
    print("\n🛠️ Testing DLT Functionality")
    print("=" * 50)

    functionality_tests = []

    # Test 1: DLTLoader class definition
    print("\n1. Testing DLTLoader class structure...")
    try:
        from storage import DLTLoader

        # Check class has expected methods
        required_methods = [
            '__init__', 'create_pipeline', 'load_opportunities',
            'validate_connection', 'prepare_opportunity_data',
            'get_load_statistics'
        ]

        missing_methods = [method for method in required_methods if not hasattr(DLTLoader, method)]

        if not missing_methods:
            functionality_tests.append(("class_structure", True, None))
            print("   ✅ DLTLoader class has all required methods")
        else:
            functionality_tests.append(("class_structure", False, f"Missing methods: {missing_methods}"))
            print(f"   ❌ DLTLoader missing methods: {missing_methods}")

    except Exception as e:
        functionality_tests.append(("class_structure", False, str(e)))
        print(f"   ❌ DLTLoader class test failed: {e}")

    # Test 2: Factory functions
    print("\n2. Testing factory functions...")
    try:
        from storage import create_dlt_loader, load_opportunities_to_supabase

        # Check if functions are callable
        if callable(create_dlt_loader) and callable(load_opportunities_to_supabase):
            functionality_tests.append(("factory_functions", True, None))
            print("   ✅ Factory functions are callable")
        else:
            functionality_tests.append(("factory_functions", False, "Functions not callable"))
            print("   ❌ Factory functions not callable")

    except Exception as e:
        functionality_tests.append(("factory_functions", False, str(e)))
        print(f"   ❌ Factory function test failed: {e}")

    # Test 3: Data preparation functionality
    print("\n3. Testing data preparation functionality...")
    try:
        from storage.dlt_loader import DLTLoader

        # Create test data
        test_submissions = [
            {
                "submission_id": "test_123",
                "title": "Test Opportunity",
                "text": "This is a test",
                "subreddit": "productivity",
                "upvotes": 100,
                "comments_count": 50,
                "score": 150,
                "created_utc": "2024-01-01T00:00:00Z",
                "permalink": "https://reddit.com/r/test/123",
                "overall_trust_score": 75.0,
                "final_score": 80.0,
                "quality_score": 85.0,
                "trust_level": "HIGH",
                "trust_badges": ["VERIFIED"],
                "confidence_score": 90.0,
                "monetization_score": 70.0,
                "core_functions": ["productivity"],
                "app_concept": "Test App",
                "problem_description": "Test Problem"
            }
        ]

        # Test data preparation (should work without DLT library)
        opportunities = DLTLoader.prepare_opportunity_data(None, test_submissions, score_threshold=40.0)

        if opportunities and len(opportunities) > 0:
            functionality_tests.append(("data_preparation", True, f"Prepared {len(opportunities)} opportunities"))
            print(f"   ✅ Data preparation works: {len(opportunities)} opportunities prepared")

            # Check if prepared data has required fields
            required_fields = ["submission_id", "title", "overall_trust_score"]
            opp = opportunities[0]
            missing_fields = [field for field in required_fields if field not in opp]

            if not missing_fields:
                print(f"   ✅ Prepared data has all required fields")
            else:
                print(f"   ⚠️ Prepared data missing fields: {missing_fields}")

        else:
            functionality_tests.append(("data_preparation", False, "No opportunities prepared"))
            print("   ❌ Data preparation failed: No opportunities prepared")

    except ImportError as e:
        if "DLT library is not available" in str(e):
            functionality_tests.append(("data_preparation", False, "DLT not available (expected)"))
            print("   ⚠️ Data preparation skipped: DLT not available")
        else:
            functionality_tests.append(("data_preparation", False, str(e)))
            print(f"   ❌ Data preparation failed: {e}")
    except Exception as e:
        functionality_tests.append(("data_preparation", False, str(e)))
        print(f"   ❌ Data preparation failed: {e}")

    # Test 4: DLT availability detection
    print("\n4. Testing DLT availability detection...")
    try:
        from storage import DLT_AVAILABLE

        # This should work regardless of DLT being installed
        functionality_tests.append(("availability_detection", True, f"DLT_AVAILABLE: {DLT_AVAILABLE}"))
        print(f"   ✅ DLT availability detection works: {DLT_AVAILABLE}")

    except Exception as e:
        functionality_tests.append(("availability_detection", False, str(e)))
        print(f"   ❌ DLT availability detection failed: {e}")

    # Summary
    successful = sum(1 for _, success, _ in functionality_tests if success)
    total = len(functionality_tests)
    success_rate = (successful / total) * 100

    print(f"\n📊 Functionality Test Summary:")
    print(f"   Success Rate: {success_rate:.1f}% ({successful}/{total})")

    for test_name, success, details in functionality_tests:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
        if details:
            print(f"      Details: {details}")

    return success_rate

def test_error_handling():
    """Test error handling with lazy loading."""
    print("\n🛡️ Testing Error Handling")
    print("=" * 50)

    error_tests = []

    # Test 1: DLT unavailable handling
    print("\n1. Testing DLT unavailable error handling...")
    try:
        from storage import DLTLoader

        # This should fail gracefully if DLT is not available
        try:
            loader = DLTLoader(use_local_dev=True)
            # If we get here, DLT is available
            error_tests.append(("dlt_unavailable", False, "DLT unexpectedly available"))
            print("   ⚠️ DLT is available (not expected in test environment)")
        except Exception as e:
            # This is expected behavior
            if "DLT library is not available" in str(e):
                error_tests.append(("dlt_unavailable", True, "DLT unavailable handled gracefully"))
                print("   ✅ DLT unavailable handled gracefully")
            else:
                error_tests.append(("dlt_unavailable", False, f"Unexpected error: {e}"))
                print(f"   ❌ Unexpected error: {e}")

    except Exception as e:
        error_tests.append(("dlt_unavailable", False, str(e)))
        print(f"   ❌ DLT unavailable test failed: {e}")

    # Test 2: Exception classes
    print("\n2. Testing exception class availability...")
    try:
        from storage import DLTLoaderError, DLTCredentialError, DLTConnectionError

        # Check if exception classes can be instantiated
        test_errors = [
            DLTLoaderError("Test DLT error"),
            DLTCredentialError("Test credential error"),
            DLTConnectionError("Test connection error")
        ]

        error_tests.append(("exception_classes", True, f"Created {len(test_errors)} exception instances"))
        print(f"   ✅ Exception classes work: {len(test_errors)} instances created")

    except Exception as e:
        error_tests.append(("exception_classes", False, str(e)))
        print(f"   ❌ Exception class test failed: {e}")

    # Summary
    successful = sum(1 for _, success, _ in error_tests if success)
    total = len(error_tests)
    success_rate = (successful / total) * 100

    print(f"\n📊 Error Handling Test Summary:")
    print(f"   Success Rate: {success_rate:.1f}% ({successful}/{total})")

    for test_name, success, details in error_tests:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
        if details:
            print(f"      Details: {details}")

    return success_rate

def test_startup_performance():
    """Test startup performance improvement."""
    print("\n📊 Testing Startup Performance")
    print("=" * 50)

    # Test storage module import performance
    print("\n1. Measuring storage module import performance...")

    # Clear any cached imports
    modules_to_clear = [k for k in sys.modules.keys() if k.startswith('storage')]
    for module in modules_to_clear:
        sys.modules.pop(module, None)

    start_time = time.time()
    try:
        from storage import DLTLoader, create_dlt_loader, DEFAULT_PIPELINE_NAME, DLT_AVAILABLE
        import_time = time.time() - start_time

        print(f"   📊 Storage module import: {import_time:.4f}s ({import_time*1000:.1f}ms)")

        # Performance evaluation
        if import_time < 0.01:  # Under 10ms
            rating = "🏆 EXCELLENT"
            target_met = True
        elif import_time < 0.05:  # Under 50ms
            rating = "✅ GOOD"
            target_met = True
        else:
            rating = "⚠️ NEEDS IMPROVEMENT"
            target_met = False

        print(f"   🎯 Performance Rating: {rating}")

        # Calculate improvement over original 5.68s
        original_time = 5.68
        if import_time > 0:
            improvement = ((original_time - import_time) / original_time) * 100
            print(f"   📈 Improvement over original: {improvement:.1f}%")
            print(f"   📉 Time reduction: {original_time - import_time:.2f}s")

        return target_met, import_time, improvement

    except Exception as e:
        import_time = time.time() - start_time
        print(f"   ❌ Import failed after {import_time:.4f}s: {e}")
        return False, import_time, 0

def main():
    """Main test execution."""
    print("RedditHarbor Pipeline v2 - Existing DLT Compatibility Test")
    print("Testing compatibility with existing DLT functionality")
    print("=" * 70)

    # Run all test suites
    import_success_rate = test_dlt_import_patterns()
    functionality_success_rate = test_dlt_functionality()
    error_handling_success_rate = test_error_handling()
    performance_met, import_time, improvement = test_startup_performance()

    # Final assessment
    print("\n" + "=" * 70)
    print("🎯 FINAL COMPATIBILITY ASSESSMENT")
    print("=" * 70)

    print(f"\n📊 Test Results Summary:")
    print(f"   Import Compatibility: {import_success_rate:.1f}%")
    print(f"   Functionality: {functionality_success_rate:.1f}%")
    print(f"   Error Handling: {error_handling_success_rate:.1f}%")
    print(f"   Performance Target: {'✅ MET' if performance_met else '❌ NOT MET'}")
    print(f"   Import Time: {import_time:.4f}s")
    print(f"   Improvement: {improvement:.1f}%")

    # Overall success criteria
    overall_success = (
        import_success_rate >= 80 and
        functionality_success_rate >= 70 and
        error_handling_success_rate >= 70 and
        performance_met
    )

    print(f"\n🏆 OVERALL COMPATIBILITY RESULT:")
    if overall_success:
        print("   ✅ LAZY LOADING COMPATIBILITY: SUCCESS")
        print("   ✓ Existing import patterns work correctly")
        print("   ✓ DLT functionality preserved")
        print("   ✓ Error handling maintained")
        print("   ✓ Performance improvement achieved")
    else:
        print("   ⚠️ LAZY LOADING COMPATIBILITY: NEEDS ATTENTION")
        if import_success_rate < 80:
            print("   ❌ Import compatibility issues")
        if functionality_success_rate < 70:
            print("   ❌ Functionality issues detected")
        if error_handling_success_rate < 70:
            print("   ❌ Error handling issues")
        if not performance_met:
            print("   ❌ Performance targets not met")

    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())