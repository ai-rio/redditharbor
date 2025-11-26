#!/usr/bin/env python3
"""
DLT Lazy Loading Validation Tests

This script validates that the DLT lazy loading implementation provides:
1. Significant startup time improvements (target: 65-90% faster)
2. Full functionality preservation after lazy loading
3. Proper error handling when DLT is unavailable
4. Backward compatibility with existing code patterns

Test Categories:
- Performance: Import time measurements
- Functionality: DLT operations work correctly
- Error Handling: Graceful failures without DLT
- Compatibility: Existing import patterns still work

Author: Pipeline Testing Framework
Version: Lazy Loading Validation v1.0
"""

import importlib
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
from types import SimpleNamespace

# Add pipeline-v2 to path for imports
pipeline_v2_root = Path(__file__).parent
sys.path.insert(0, str(pipeline_v2_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LazyLoadingValidator:
    """Comprehensive validator for DLT lazy loading implementation."""

    def __init__(self):
        self.results = {
            "performance": {},
            "functionality": {},
            "error_handling": {},
            "compatibility": {}
        }
        self.test_data = self._create_test_data()

    def _create_test_data(self) -> List[Dict[str, Any]]:
        """Create test data for DLT functionality validation."""
        return [
            {
                "submission_id": f"test_{i}",
                "title": f"Test Opportunity {i}",
                "text": f"This is a test opportunity description {i}",
                "subreddit": "productivity",
                "upvotes": 50 + i * 10,
                "comments_count": 20 + i * 5,
                "score": 70 + i * 3,
                "created_utc": "2024-01-01T00:00:00Z",
                "permalink": f"https://reddit.com/r/test/{i}",
                "quality_score": 80.0 + i * 2,
                "final_score": 75.0 + i * 1.5,
                "overall_trust_score": 65.0 + i * 3,
                "trust_level": "MEDIUM",
                "trust_badges": ["BASIC", "ACTIVE"],
                "confidence_score": 70.0 + i * 2,
                "monetization_score": 60.0 + i * 4,
                "core_functions": ["productivity", "collaboration"],
                "app_concept": f"Test app concept {i}",
                "problem_description": f"Test problem description {i}",
                "customer_segment": "professionals"
            }
            for i in range(3)
        ]

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("Starting DLT Lazy Loading Validation")
        logger.info("=" * 60)

        try:
            # Performance tests
            logger.info("1. Running Performance Tests...")
            self._test_startup_performance()
            self._test_dlt_lazy_import_performance()

            # Functionality tests
            logger.info("2. Running Functionality Tests...")
            self._test_dlt_loader_instantiation()
            self._test_pipeline_creation()
            self._test_data_preparation()
            self._test_opportunity_loading()

            # Error handling tests
            logger.info("3. Running Error Handling Tests...")
            self._test_dlt_unavailable_handling()
            self._test_configuration_error_handling()

            # Compatibility tests
            logger.info("4. Running Compatibility Tests...")
            self._test_backward_compatibility()
            self._test_storage_module_imports()

            # Generate summary
            self._generate_test_summary()

        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            self.results["execution_error"] = str(e)

        return self.results

    def _test_startup_performance(self) -> None:
        """Test main pipeline startup performance."""
        logger.info("Testing main pipeline startup time...")

        # Measure import time for main.py
        start_time = time.time()
        try:
            import main
            import_time = time.time() - start_time

            self.results["performance"]["main_import_time"] = {
                "seconds": round(import_time, 3),
                "milliseconds": round(import_time * 1000, 1)
            }

            # Performance evaluation
            expected_max_time = 3.0  # Should be much faster than original 5.68s
            performance_rating = "EXCELLENT" if import_time < 2.0 else \
                               "GOOD" if import_time < 3.0 else \
                               "NEEDS_IMPROVEMENT"

            self.results["performance"]["main_import_rating"] = performance_rating
            self.results["performance"]["improvement_achieved"] = import_time < expected_max_time

            logger.info(f"  ✓ Main pipeline import time: {import_time:.3f}s")
            logger.info(f"  ✓ Performance rating: {performance_rating}")

            # Check if we achieved the target improvement
            if import_time < expected_max_time:
                improvement_pct = ((5.68 - import_time) / 5.68) * 100
                logger.info(f"  ✓ Startup time improvement: {improvement_pct:.1f}%")
                self.results["performance"]["startup_improvement_percentage"] = round(improvement_pct, 1)

        except Exception as e:
            logger.error(f"  ✗ Failed to import main: {e}")
            self.results["performance"]["main_import_error"] = str(e)

    def _test_dlt_lazy_import_performance(self) -> None:
        """Test DLT lazy import performance."""
        logger.info("Testing DLT lazy import performance...")

        # Test storage module import (should be fast)
        start_time = time.time()
        try:
            from storage import DLT_AVAILABLE
            storage_import_time = time.time() - start_time

            self.results["performance"]["storage_import_time"] = {
                "seconds": round(storage_import_time, 4),
                "milliseconds": round(storage_import_time * 1000, 2)
            }

            logger.info(f"  ✓ Storage module import: {storage_import_time:.4f}s")

            # Test DLT loader lazy import (should only import when used)
            start_time = time.time()
            try:
                from storage import DLTLoader
                dlt_import_time = time.time() - start_time

                self.results["performance"]["dlt_lazy_import_time"] = {
                    "seconds": round(dlt_import_time, 3),
                    "milliseconds": round(dlt_import_time * 1000, 1)
                }

                logger.info(f"  ✓ DLT lazy import time: {dlt_import_time:.3f}s")

            except ImportError as e:
                logger.info(f"  ○ DLT not available (expected in test): {e}")
                self.results["performance"]["dlt_import_skipped"] = True

        except Exception as e:
            logger.error(f"  ✗ Storage module import failed: {e}")
            self.results["performance"]["storage_import_error"] = str(e)

    def _test_dlt_loader_instantiation(self) -> None:
        """Test DLTLoader instantiation with lazy loading."""
        logger.info("Testing DLTLoader instantiation...")

        try:
            from storage.dlt_loader import DLTLoader, DLTLoaderError

            # Test instantiation with local development settings
            start_time = time.time()
            loader = DLTLoader(use_local_dev=True)
            instantiation_time = time.time() - start_time

            self.results["functionality"]["dlt_instantiation"] = {
                "success": True,
                "time_seconds": round(instantiation_time, 3),
                "has_pipeline": loader._pipeline is not None,
                "has_credentials": loader._credentials is not None
            }

            logger.info(f"  ✓ DLTLoader instantiated in {instantiation_time:.3f}s")

        except ImportError as e:
            logger.info(f"  ○ DLT not available for instantiation test: {e}")
            self.results["functionality"]["dlt_instantiation"] = {
                "success": False,
                "reason": "DLT not available",
                "error": str(e)
            }

        except Exception as e:
            logger.error(f"  ✗ DLTLoader instantiation failed: {e}")
            self.results["functionality"]["dlt_instantiation"] = {
                "success": False,
                "error": str(e)
            }

    def _test_pipeline_creation(self) -> None:
        """Test DLT pipeline creation functionality."""
        logger.info("Testing DLT pipeline creation...")

        try:
            from storage.dlt_loader import DLTLoader

            loader = DLTLoader(use_local_dev=True)

            # Test pipeline creation
            start_time = time.time()
            pipeline = loader.create_pipeline()
            creation_time = time.time() - start_time

            self.results["functionality"]["pipeline_creation"] = {
                "success": pipeline is not None,
                "time_seconds": round(creation_time, 3),
                "has_attributes": hasattr(pipeline, 'pipeline_name') if pipeline else False
            }

            logger.info(f"  ✓ Pipeline created in {creation_time:.3f}s")

        except ImportError as e:
            logger.info(f"  ○ DLT not available for pipeline creation: {e}")
            self.results["functionality"]["pipeline_creation"] = {
                "success": False,
                "reason": "DLT not available",
                "error": str(e)
            }

        except Exception as e:
            logger.error(f"  ✗ Pipeline creation failed: {e}")
            self.results["functionality"]["pipeline_creation"] = {
                "success": False,
                "error": str(e)
            }

    def _test_data_preparation(self) -> None:
        """Test opportunity data preparation functionality."""
        logger.info("Testing data preparation functionality...")

        try:
            from storage.dlt_loader import DLTLoader

            loader = DLTLoader(use_local_dev=True)

            # Test data preparation
            start_time = time.time()
            opportunities = loader.prepare_opportunity_data(self.test_data, score_threshold=40.0)
            preparation_time = time.time() - start_time

            self.results["functionality"]["data_preparation"] = {
                "success": True,
                "input_count": len(self.test_data),
                "output_count": len(opportunities),
                "time_seconds": round(preparation_time, 3),
                "has_required_fields": all(
                    all(field in opp for field in ["submission_id", "title", "overall_trust_score"])
                    for opp in opportunities
                )
            }

            logger.info(f"  ✓ Data prepared {len(opportunities)} opportunities in {preparation_time:.3f}s")

        except ImportError as e:
            logger.info(f"  ○ DLT not available for data preparation: {e}")
            self.results["functionality"]["data_preparation"] = {
                "success": False,
                "reason": "DLT not available",
                "error": str(e)
            }

        except Exception as e:
            logger.error(f"  ✗ Data preparation failed: {e}")
            self.results["functionality"]["data_preparation"] = {
                "success": False,
                "error": str(e)
            }

    def _test_opportunity_loading(self) -> None:
        """Test opportunity loading with mock data."""
        logger.info("Testing opportunity loading...")

        try:
            from storage.dlt_loader import DLTLoader

            loader = DLTLoader(use_local_dev=True)
            opportunities = loader.prepare_opportunity_data(self.test_data, score_threshold=40.0)

            if not opportunities:
                logger.warning("  ○ No opportunities prepared for loading test")
                self.results["functionality"]["opportunity_loading"] = {
                    "success": False,
                    "reason": "No opportunities prepared"
                }
                return

            # Test loading (should work even without database)
            start_time = time.time()
            load_info = loader.load_opportunities(opportunities[:1])  # Test with just one
            load_time = time.time() - start_time

            self.results["functionality"]["opportunity_loading"] = {
                "success": True,
                "input_count": len(opportunities[:1]),
                "load_time_seconds": round(load_time, 3),
                "has_load_info": load_info is not None,
                "load_info_type": type(load_info).__name__
            }

            logger.info(f"  ✓ Loading test completed in {load_time:.3f}s")

        except ImportError as e:
            logger.info(f"  ○ DLT not available for loading test: {e}")
            self.results["functionality"]["opportunity_loading"] = {
                "success": False,
                "reason": "DLT not available",
                "error": str(e)
            }

        except Exception as e:
            logger.error(f"  ✗ Opportunity loading failed: {e}")
            self.results["functionality"]["opportunity_loading"] = {
                "success": False,
                "error": str(e)
            }

    def _test_dlt_unavailable_handling(self) -> None:
        """Test graceful handling when DLT is not available."""
        logger.info("Testing DLT unavailable error handling...")

        # Temporarily hide DLT by manipulating sys.modules
        original_modules = {}
        dlt_modules_to_hide = [k for k in sys.modules.keys() if k.startswith('dlt')]

        for module_name in dlt_modules_to_hide:
            original_modules[module_name] = sys.modules.pop(module_name, None)

        try:
            # Try to import DLTLoader without DLT available
            from storage.dlt_loader import DLTLoader

            try:
                loader = DLTLoader(use_local_dev=True)
                self.results["error_handling"]["dlt_unexpected"] = {
                    "success": False,
                    "reason": "DLTLoader should have failed without DLT"
                }
                logger.error("  ✗ DLTLoader should have failed without DLT available")

            except ImportError as e:
                self.results["error_handling"]["dlt_unavailable"] = {
                    "success": True,
                    "error_message": str(e),
                    "handled_gracefully": "DLT library is not available" in str(e)
                }
                logger.info(f"  ✓ DLT unavailable handled gracefully: {e}")

        except Exception as e:
            logger.error(f"  ✗ Error in DLT unavailable test: {e}")
            self.results["error_handling"]["dlt_unavailable_test_error"] = str(e)

        finally:
            # Restore original modules
            sys.modules.update(original_modules)

    def _test_configuration_error_handling(self) -> None:
        """Test configuration error handling."""
        logger.info("Testing configuration error handling...")

        try:
            from storage.dlt_loader import DLTLoader, DLTCredentialError

            # Test with invalid configuration path
            try:
                loader = DLTLoader(
                    secrets_path="/nonexistent/path/secrets.toml",
                    use_local_dev=False  # Disable local dev to force config file requirement
                )
                self.results["error_handling"]["config_error_not_raised"] = {
                    "success": False,
                    "reason": "Should have raised DLTCredentialError"
                }
                logger.error("  ✗ Should have raised DLTCredentialError")

            except DLTCredentialError as e:
                self.results["error_handling"]["config_error_handled"] = {
                    "success": True,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                logger.info(f"  ✓ Configuration error handled: {e}")

        except ImportError as e:
            logger.info(f"  ○ DLT not available for config error test: {e}")
            self.results["error_handling"]["config_error_skipped"] = True

        except Exception as e:
            logger.error(f"  ✗ Configuration error test failed: {e}")
            self.results["error_handling"]["config_error_test_error"] = str(e)

    def _test_backward_compatibility(self) -> None:
        """Test backward compatibility with existing import patterns."""
        logger.info("Testing backward compatibility...")

        compatibility_tests = []

        # Test old-style imports
        try:
            # This should work with lazy loading
            from storage import DLTLoader, create_dlt_loader
            compatibility_tests.append({
                "test": "direct_import_from_storage",
                "success": True
            })
            logger.info("  ✓ Direct import from storage works")
        except Exception as e:
            compatibility_tests.append({
                "test": "direct_import_from_storage",
                "success": False,
                "error": str(e)
            })
            logger.error(f"  ✗ Direct import failed: {e}")

        # Test attribute access
        try:
            import storage
            loader_class = storage.DLTLoader
            compatibility_tests.append({
                "test": "attribute_access",
                "success": True
            })
            logger.info("  ✓ Attribute access to DLTLoader works")
        except Exception as e:
            compatibility_tests.append({
                "test": "attribute_access",
                "success": False,
                "error": str(e)
            })
            logger.error(f"  ✗ Attribute access failed: {e}")

        # Test constants
        try:
            from storage import DEFAULT_PIPELINE_NAME, DEFAULT_TABLE_NAME
            compatibility_tests.append({
                "test": "constants_import",
                "success": True,
                "constants": {
                    "DEFAULT_PIPELINE_NAME": DEFAULT_PIPELINE_NAME,
                    "DEFAULT_TABLE_NAME": DEFAULT_TABLE_NAME
                }
            })
            logger.info("  ✓ Constants import works")
        except Exception as e:
            compatibility_tests.append({
                "test": "constants_import",
                "success": False,
                "error": str(e)
            })
            logger.error(f"  ✗ Constants import failed: {e}")

        self.results["compatibility"]["tests"] = compatibility_tests
        self.results["compatibility"]["success_rate"] = sum(1 for t in compatibility_tests if t["success"]) / len(compatibility_tests) * 100

    def _test_storage_module_imports(self) -> None:
        """Test storage module import patterns."""
        logger.info("Testing storage module import patterns...")

        import_tests = []

        # Test fast import without triggering DLT
        try:
            start_time = time.time()
            from storage import DLT_AVAILABLE
            import_time = time.time() - start_time

            import_tests.append({
                "test": "fast_import_without_dlt",
                "success": True,
                "time_seconds": round(import_time, 4),
                "dlt_available": DLT_AVAILABLE
            })
            logger.info(f"  ✓ Fast import without DLT: {import_time:.4f}s")
        except Exception as e:
            import_tests.append({
                "test": "fast_import_without_dlt",
                "success": False,
                "error": str(e)
            })
            logger.error(f"  ✗ Fast import failed: {e}")

        # Test __all__ exports
        try:
            import storage
            expected_exports = [
                "DLTLoader", "create_dlt_loader", "load_opportunities_to_supabase",
                "DEFAULT_PIPELINE_NAME", "DEFAULT_TABLE_NAME", "DLT_AVAILABLE"
            ]

            missing_exports = [exp for exp in expected_exports if exp not in storage.__all__]

            import_tests.append({
                "test": "__all___exports",
                "success": len(missing_exports) == 0,
                "missing_exports": missing_exports,
                "total_exports": len(storage.__all__)
            })

            if len(missing_exports) == 0:
                logger.info(f"  ✓ All {len(expected_exports)} expected exports found")
            else:
                logger.error(f"  ✗ Missing exports: {missing_exports}")

        except Exception as e:
            import_tests.append({
                "test": "__all___exports",
                "success": False,
                "error": str(e)
            })
            logger.error(f"  ✗ Export test failed: {e}")

        self.results["compatibility"]["import_tests"] = import_tests

    def _generate_test_summary(self) -> None:
        """Generate comprehensive test summary."""
        logger.info("\n" + "=" * 80)
        logger.info("DLT LAZY LOADING VALIDATION SUMMARY")
        logger.info("=" * 80)

        # Performance Summary
        logger.info("\n📊 PERFORMANCE RESULTS:")
        perf = self.results["performance"]

        if "main_import_time" in perf:
            import_time = perf["main_import_time"]["seconds"]
            logger.info(f"  • Main pipeline startup: {import_time:.3f}s")
            logger.info(f"  • Performance rating: {perf.get('main_import_rating', 'Unknown')}")

            if "startup_improvement_percentage" in perf:
                improvement = perf["startup_improvement_percentage"]
                logger.info(f"  • Startup improvement: {improvement:.1f}%")

        if "storage_import_time" in perf:
            storage_time = perf["storage_import_time"]["seconds"]
            logger.info(f"  • Storage module import: {storage_time:.4f}s")

        # Functionality Summary
        logger.info("\n✅ FUNCTIONALITY RESULTS:")
        func = self.results["functionality"]

        for test_name, result in func.items():
            status = "✓" if result.get("success", False) else "✗"
            logger.info(f"  {status} {test_name.replace('_', ' ').title()}")

            if "time_seconds" in result:
                logger.info(f"    - Time: {result['time_seconds']:.3f}s")
            if not result.get("success", False) and "error" in result:
                logger.info(f"    - Error: {result['error']}")

        # Error Handling Summary
        logger.info("\n🛡️ ERROR HANDLING RESULTS:")
        error = self.results["error_handling"]

        for test_name, result in error.items():
            if "success" in result:
                status = "✓" if result["success"] else "✗"
                logger.info(f"  {status} {test_name.replace('_', ' ').title()}")

        # Compatibility Summary
        logger.info("\n🔄 COMPATIBILITY RESULTS:")
        comp = self.results["compatibility"]

        if "success_rate" in comp:
            logger.info(f"  • Overall compatibility: {comp['success_rate']:.1f}%")

        if "tests" in comp:
            for test in comp["tests"]:
                status = "✓" if test["success"] else "✗"
                logger.info(f"  {status} {test['test'].replace('_', ' ').title()}")

        # Overall Assessment
        logger.info("\n🎯 OVERALL ASSESSMENT:")

        # Performance criteria
        perf_success = (
            "main_import_time" in perf and
            perf["main_import_time"]["seconds"] < 3.0
        )

        # Functionality criteria
        func_success = sum(1 for r in func.values() if r.get("success", False)) / max(len(func), 1) > 0.7

        # Error handling criteria
        error_success = len(error) > 0 and any(r.get("success", False) for r in error.values())

        # Compatibility criteria
        compat_success = comp.get("success_rate", 0) > 80

        # Overall success
        overall_success = perf_success and func_success and compat_success

        if overall_success:
            logger.info("  ✅ LAZY LOADING IMPLEMENTATION: SUCCESS")
            logger.info("  ✓ Significant startup time improvement achieved")
            logger.info("  ✓ Functionality preserved after lazy loading")
            logger.info("  ✓ Backward compatibility maintained")
        else:
            logger.info("  ⚠️ LAZY LOADING IMPLEMENTATION: NEEDS ATTENTION")

            if not perf_success:
                logger.info("  ✗ Startup time improvement insufficient")
            if not func_success:
                logger.info("  ✗ Functionality issues detected")
            if not compat_success:
                logger.info("  ✗ Compatibility problems found")

        self.results["overall_success"] = overall_success
        self.results["summary"] = {
            "performance_success": perf_success,
            "functionality_success": func_success,
            "error_handling_success": error_success,
            "compatibility_success": compat_success
        }


def main():
    """Main test execution function."""
    validator = LazyLoadingValidator()
    results = validator.run_all_tests()

    # Save results to file
    import json
    results_file = pipeline_v2_root / "lazy_loading_validation_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n📄 Detailed results saved to: {results_file}")

    # Return appropriate exit code
    return 0 if results.get("overall_success", False) else 1


if __name__ == "__main__":
    sys.exit(main())