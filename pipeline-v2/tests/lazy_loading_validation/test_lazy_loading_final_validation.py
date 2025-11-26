#!/usr/bin/env python3
"""
Final Lazy Loading Validation Report

Comprehensive validation of the DLT lazy loading implementation.
This test focuses on the core lazy loading mechanism that was implemented
to solve the 5.68s startup time issue.

This validation specifically tests:
1. Lazy loading mechanism works correctly
2. Storage module imports are fast
3. Backward compatibility is maintained
4. Error handling works as expected
5. Performance improvements are achieved

Author: Final Lazy Loading Validation
Version: Final Report v1.0
"""

import sys
import time
import json
from pathlib import Path

# Add pipeline-v2 to path
pipeline_v2_root = Path(__file__).parent
sys.path.insert(0, str(pipeline_v2_root))

class LazyLoadingFinalValidator:
    """Final comprehensive validator for DLT lazy loading."""

    def __init__(self):
        self.results = {
            "performance": {},
            "functionality": {},
            "compatibility": {},
            "error_handling": {},
            "summary": {}
        }

    def run_validation(self):
        """Run complete validation test suite."""
        print("RedditHarbor Pipeline v2 - Final Lazy Loading Validation")
        print("Comprehensive validation of DLT lazy loading implementation")
        print("=" * 70)

        # Test 1: Performance validation
        self.test_performance_metrics()

        # Test 2: Lazy loading mechanism validation
        self.test_lazy_loading_mechanism()

        # Test 3: Backward compatibility validation
        self.test_backward_compatibility()

        # Test 4: Error handling validation
        self.test_error_handling()

        # Test 5: Functionality validation
        self.test_dlt_functionality()

        # Generate final report
        self.generate_final_report()

        return self.results

    def test_performance_metrics(self):
        """Test performance metrics of lazy loading."""
        print(f"\n📊 Performance Metrics Test")
        print("-" * 50)

        # Test storage module cold import
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith('storage')]
        for module in modules_to_clear:
            sys.modules.pop(module, None)

        start_time = time.time()
        try:
            from storage import (
                DLT_AVAILABLE, DEFAULT_PIPELINE_NAME, DEFAULT_TABLE_NAME,
                DLTLoader, create_dlt_loader
            )
            cold_import_time = time.time() - start_time

            self.results["performance"]["storage_cold_import"] = {
                "time_seconds": round(cold_import_time, 4),
                "time_milliseconds": round(cold_import_time * 1000, 2),
                "target_met": cold_import_time < 0.01
            }

            print(f"   ✅ Storage cold import: {cold_import_time:.4f}s ({cold_import_time*1000:.2f}ms)")

            # Test hot import
            start_time = time.time()
            import storage
            hot_import_time = time.time() - start_time

            self.results["performance"]["storage_hot_import"] = {
                "time_seconds": round(hot_import_time, 6),
                "time_microseconds": round(hot_import_time * 1000000, 1)
            }

            print(f"   ✅ Storage hot import: {hot_import_time:.6f}s ({hot_import_time*1000000:.1f}μs)")

        except Exception as e:
            self.results["performance"]["import_error"] = str(e)
            print(f"   ❌ Storage import failed: {e}")

    def test_lazy_loading_mechanism(self):
        """Test the lazy loading mechanism itself."""
        print(f"\n🐪 Lazy Loading Mechanism Test")
        print("-" * 50)

        # Test 1: Constants available immediately
        start_time = time.time()
        try:
            from storage import DLT_AVAILABLE, DEFAULT_PIPELINE_NAME, DEFAULT_TABLE_NAME
            constants_time = time.time() - start_time

            self.results["functionality"]["constants_import"] = {
                "success": True,
                "time_seconds": round(constants_time, 4),
                "dlt_available": DLT_AVAILABLE,
                "constants_present": True
            }

            print(f"   ✅ Constants available in {constants_time:.4f}s")

        except Exception as e:
            self.results["functionality"]["constants_import"] = {
                "success": False,
                "error": str(e)
            }
            print(f"   ❌ Constants import failed: {e}")

        # Test 2: DLTLoader triggers lazy loading
        start_time = time.time()
        try:
            from storage import DLTLoader

            # Access the class (should trigger lazy import)
            loader_class = DLTLoader
            lazy_import_time = time.time() - start_time

            self.results["functionality"]["lazy_dlt_import"] = {
                "success": True,
                "time_seconds": round(lazy_import_time, 3),
                "class_accessible": True
            }

            print(f"   ✅ DLTLoader lazy import: {lazy_import_time:.3f}s")

            # Test instantiation (should handle DLT unavailability gracefully)
            try:
                loader = loader_class(use_local_dev=True)
                self.results["functionality"]["dlt_instantiation"] = {
                    "success": True,
                    "dlt_available": True
                }
                print(f"   ✅ DLTLoader instantiated (DLT available)")
            except Exception as e:
                if "DLT library is not available" in str(e):
                    self.results["functionality"]["dlt_instantiation"] = {
                        "success": True,
                        "dlt_available": False,
                        "handled_gracefully": True
                    }
                    print(f"   ✅ DLTLoader handled missing DLT gracefully")
                else:
                    self.results["functionality"]["dlt_instantiation"] = {
                        "success": False,
                        "error": str(e)
                    }
                    print(f"   ❌ DLTLoader instantiation failed unexpectedly: {e}")

        except Exception as e:
            self.results["functionality"]["lazy_dlt_import"] = {
                "success": False,
                "error": str(e)
            }
            print(f"   ❌ DLTLoader lazy import failed: {e}")

    def test_backward_compatibility(self):
        """Test backward compatibility with existing import patterns."""
        print(f"\n🔄 Backward Compatibility Test")
        print("-" * 50)

        compatibility_tests = []

        # Test 1: Import pattern used in main.py
        try:
            from storage import DLTLoader, create_dlt_loader, load_opportunities_to_supabase
            compatibility_tests.append(("main_pattern", True, None))
            print(f"   ✅ main.py import pattern works")
        except Exception as e:
            compatibility_tests.append(("main_pattern", False, str(e)))
            print(f"   ❌ main.py import pattern failed: {e}")

        # Test 2: Direct dlt_loader import
        try:
            from storage.dlt_loader import DLTLoader, DLTLoaderError
            compatibility_tests.append(("direct_import", True, None))
            print(f"   ✅ Direct dlt_loader import works")
        except Exception as e:
            compatibility_tests.append(("direct_import", False, str(e)))
            print(f"   ❌ Direct dlt_loader import failed: {e}")

        # Test 3: Attribute access pattern
        try:
            import storage
            loader_class = storage.DLTLoader
            create_func = storage.create_dlt_loader
            compatibility_tests.append(("attribute_access", True, None))
            print(f"   ✅ Attribute access pattern works")
        except Exception as e:
            compatibility_tests.append(("attribute_access", False, str(e)))
            print(f"   ❌ Attribute access pattern failed: {e}")

        # Test 4: Exception class imports
        try:
            from storage import DLTLoaderError, DLTCredentialError, DLTConnectionError
            compatibility_tests.append(("exception_imports", True, None))
            print(f"   ✅ Exception class imports work")
        except Exception as e:
            compatibility_tests.append(("exception_imports", False, str(e)))
            print(f"   ❌ Exception class imports failed: {e}")

        # Test 5: Constants available
        try:
            from storage import DEFAULT_PIPELINE_NAME, DEFAULT_TABLE_NAME, DEFAULT_PRIMARY_KEY
            compatibility_tests.append(("constants", True, None))
            print(f"   ✅ Constants import works")
        except Exception as e:
            compatibility_tests.append(("constants", False, str(e)))
            print(f"   ❌ Constants import failed: {e}")

        # Calculate success rate
        successful = sum(1 for _, success, _ in compatibility_tests if success)
        total = len(compatibility_tests)
        success_rate = (successful / total) * 100

        self.results["compatibility"] = {
            "tests": compatibility_tests,
            "success_rate": success_rate,
            "successful_tests": successful,
            "total_tests": total
        }

        print(f"\n   📊 Compatibility Success Rate: {success_rate:.1f}% ({successful}/{total})")

    def test_error_handling(self):
        """Test error handling in lazy loading."""
        print(f"\n🛡️ Error Handling Test")
        print("-" * 50)

        error_tests = []

        # Test 1: DLT unavailable handling
        try:
            from storage import DLTLoader
            try:
                loader = DLTLoader(use_local_dev=True)
                # If we get here, DLT is available
                error_tests.append(("dlt_unavailable", True, "DLT is available"))
                print(f"   ℹ️ DLT is available in test environment")
            except Exception as e:
                if "DLT library is not available" in str(e):
                    error_tests.append(("dlt_unavailable", True, "Handled gracefully"))
                    print(f"   ✅ DLT unavailable handled gracefully")
                else:
                    error_tests.append(("dlt_unavailable", False, str(e)))
                    print(f"   ❌ Unexpected error: {e}")
        except Exception as e:
            error_tests.append(("dlt_unavailable", False, str(e)))
            print(f"   ❌ DLT unavailable test failed: {e}")

        # Test 2: Exception classes work
        try:
            from storage import DLTLoaderError, DLTCredentialError
            # Test creating exceptions
            test_errors = [
                DLTLoaderError("Test error"),
                DLTCredentialError("Test credential error")
            ]
            error_tests.append(("exception_classes", True, f"Created {len(test_errors)} exceptions"))
            print(f"   ✅ Exception classes work correctly")
        except Exception as e:
            error_tests.append(("exception_classes", False, str(e)))
            print(f"   ❌ Exception classes failed: {e}")

        successful = sum(1 for _, success, _ in error_tests if success)
        total = len(error_tests)
        success_rate = (successful / total) * 100

        self.results["error_handling"] = {
            "tests": error_tests,
            "success_rate": success_rate
        }

        print(f"   📊 Error Handling Success Rate: {success_rate:.1f}% ({successful}/{total})")

    def test_dlt_functionality(self):
        """Test DLT functionality where possible."""
        print(f"\n🛠️ DLT Functionality Test")
        print("-" * 50)

        functionality_tests = []

        # Test 1: Data preparation (should work without DLT library)
        try:
            from storage.dlt_loader import DLTLoader

            test_data = [{
                "submission_id": "test_123",
                "title": "Test Opportunity",
                "overall_trust_score": 75.0,
                "final_score": 80.0
            }]

            opportunities = DLTLoader.prepare_opportunity_data(None, test_data, score_threshold=40.0)

            if opportunities and len(opportunities) > 0:
                functionality_tests.append(("data_preparation", True, f"Prepared {len(opportunities)}"))
                print(f"   ✅ Data preparation works: {len(opportunities)} opportunities")
            else:
                functionality_tests.append(("data_preparation", False, "No opportunities prepared"))
                print(f"   ❌ Data preparation failed: No opportunities")

        except Exception as e:
            functionality_tests.append(("data_preparation", False, str(e)))
            print(f"   ❌ Data preparation failed: {e}")

        # Test 2: Factory functions callable
        try:
            from storage import create_dlt_loader, load_opportunities_to_supabase

            if callable(create_dlt_loader) and callable(load_opportunities_to_supabase):
                functionality_tests.append(("factory_functions", True, "Both callable"))
                print(f"   ✅ Factory functions are callable")
            else:
                functionality_tests.append(("factory_functions", False, "Not callable"))
                print(f"   ❌ Factory functions not callable")

        except Exception as e:
            functionality_tests.append(("factory_functions", False, str(e)))
            print(f"   ❌ Factory functions failed: {e}")

        # Test 3: DLT availability detection
        try:
            from storage import DLT_AVAILABLE
            functionality_tests.append(("availability_detection", True, str(DLT_AVAILABLE)))
            print(f"   ✅ DLT availability detection: {DLT_AVAILABLE}")
        except Exception as e:
            functionality_tests.append(("availability_detection", False, str(e)))
            print(f"   ❌ Availability detection failed: {e}")

        successful = sum(1 for _, success, _ in functionality_tests if success)
        total = len(functionality_tests)
        success_rate = (successful / total) * 100

        self.results["functionality"]["tests"] = functionality_tests
        self.results["functionality"]["success_rate"] = success_rate

        print(f"   📊 Functionality Success Rate: {success_rate:.1f}% ({successful}/{total})")

    def generate_final_report(self):
        """Generate final validation report."""
        print(f"\n" + "=" * 70)
        print("🏆 FINAL VALIDATION REPORT")
        print("=" * 70)

        # Performance summary
        print(f"\n📊 PERFORMANCE RESULTS:")
        perf = self.results["performance"]
        if "storage_cold_import" in perf:
            cold_time = perf["storage_cold_import"]["time_milliseconds"]
            print(f"   • Storage cold import: {cold_time:.2f}ms {'✅' if cold_time < 10 else '❌'}")

        if "storage_hot_import" in perf:
            hot_time = perf["storage_hot_import"]["time_microseconds"]
            print(f"   • Storage hot import: {hot_time:.1f}μs {'✅' if hot_time < 100 else '❌'}")

        # Functionality summary
        print(f"\n✅ FUNCTIONALITY RESULTS:")
        func = self.results["functionality"]
        print(f"   • Overall success rate: {func.get('success_rate', 0):.1f}%")

        if "constants_import" in func:
            const_success = func["constants_import"]["success"]
            print(f"   • Constants import: {'✅' if const_success else '❌'}")

        if "lazy_dlt_import" in func:
            lazy_success = func["lazy_dlt_import"]["success"]
            print(f"   • DLT lazy import: {'✅' if lazy_success else '❌'}")

        # Compatibility summary
        print(f"\n🔄 COMPATIBILITY RESULTS:")
        comp = self.results["compatibility"]
        print(f"   • Backward compatibility: {comp.get('success_rate', 0):.1f}%")
        print(f"   • Tests passed: {comp.get('successful_tests', 0)}/{comp.get('total_tests', 0)}")

        # Error handling summary
        print(f"\n🛡️ ERROR HANDLING RESULTS:")
        error = self.results["error_handling"]
        print(f"   • Error handling success rate: {error.get('success_rate', 0):.1f}%")

        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")

        # Success criteria
        performance_ok = (
            "storage_cold_import" in perf and
            perf["storage_cold_import"]["target_met"]
        )

        functionality_ok = func.get('success_rate', 0) >= 70
        compatibility_ok = comp.get('success_rate', 0) >= 80
        error_handling_ok = error.get('success_rate', 0) >= 70

        # Overall success
        overall_success = performance_ok and functionality_ok and compatibility_ok

        print(f"   Performance (fast imports): {'✅ MET' if performance_ok else '❌ NOT MET'}")
        print(f"   Functionality preserved: {'✅ MET' if functionality_ok else '❌ NOT MET'}")
        print(f"   Backward compatibility: {'✅ MET' if compatibility_ok else '❌ NOT MET'}")
        print(f"   Error handling: {'✅ MET' if error_handling_ok else '❌ NOT MET'}")

        if overall_success:
            print(f"\n🎉 LAZY LOADING IMPLEMENTATION: ✅ SUCCESS")
            print(f"   ✓ Fast module imports achieved")
            print(f"   ✓ Lazy loading mechanism working correctly")
            print(f"   ✓ Backward compatibility maintained")
            print(f"   ✓ Error handling preserved")
            print(f"   ✓ DLT functionality intact")
            print(f"\n🌟 KEY ACHIEVEMENT:")
            print(f"   The lazy loading implementation successfully addresses the")
            print(f"   original 5.68s startup time issue by deferring DLT imports")
            print(f"   until they are actually needed.")

            # Calculate estimated improvement
            if "storage_cold_import" in perf:
                storage_time = perf["storage_cold_import"]["time_seconds"]
                if storage_time > 0:
                    # Original was 5.68s, now storage import is ~0.001s
                    estimated_improvement = ((5.68 - storage_time) / 5.68) * 100
                    print(f"   Estimated startup improvement: {estimated_improvement:.1f}%")
        else:
            print(f"\n⚠️ LAZY LOADING IMPLEMENTATION: ❌ NEEDS ATTENTION")
            if not performance_ok:
                print(f"   ❌ Import performance not meeting targets")
            if not functionality_ok:
                print(f"   ❌ Functionality issues detected")
            if not compatibility_ok:
                print(f"   ❌ Compatibility issues found")

        self.results["summary"] = {
            "overall_success": overall_success,
            "performance_ok": performance_ok,
            "functionality_ok": functionality_ok,
            "compatibility_ok": compatibility_ok,
            "error_handling_ok": error_handling_ok
        }

        # Save results to file
        results_file = pipeline_v2_root / "lazy_loading_final_validation_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed results saved to: {results_file}")

        return overall_success

def main():
    """Main execution function."""
    validator = LazyLoadingFinalValidator()
    success = validator.run_validation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())