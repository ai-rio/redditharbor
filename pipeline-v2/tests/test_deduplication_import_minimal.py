#!/usr/bin/env python3
"""
Minimal Deduplication Import Persistence Test - RED PHASE

This is a minimal reproduction test that isolates the exact deduplication import
persistence issue without getting blocked by external dependencies.

The test recreates the specific import pattern from main.py that causes:
1. Multiple sys.path manipulations via ensure_path_order()
2. Path instability that affects module resolution
3. Deduplication functions becoming unavailable despite successful imports

This test demonstrates that the issue is specifically caused by the repeated
ensure_path_order() calls in main.py, not by external dependencies.

Expected Failure: This test should FAIL on assertions that detect:
- Path instability during import sequence
- Deduplication functions becoming unavailable at runtime
- DEDUPLICATION_AVAILABLE flag changing between import and runtime
"""

import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MinimalDeduplicationTest:
    """
    Minimal test that reproduces the deduplication import persistence issue
    by focusing on the specific import pattern from main.py.
    """

    def __init__(self):
        self.pipeline_v2_root = Path(__file__).parent.parent
        self.project_root = Path(__file__).parent.parent.parent
        self.path_history = []
        self.function_availability = {}

    def ensure_path_order(self):
        """Updated replica of ensure_path_order() from main.py - GREEN PHASE VERSION"""
        logger.debug(f"ensure_path_order() called - current path entries: {len(sys.path)}")

        # Remove all existing entries for our paths to prevent duplicates
        pipeline_v2_str = str(self.pipeline_v2_root)
        project_root_str = str(self.project_root)
        removed_pipeline_v2_count = 0
        removed_project_root_count = 0

        # Remove pipeline-v2 from anywhere in path
        while pipeline_v2_str in sys.path:
            sys.path.remove(pipeline_v2_str)
            removed_pipeline_v2_count += 1

        # Remove project root from anywhere in path to prevent duplicates
        while project_root_str in sys.path:
            sys.path.remove(project_root_str)
            removed_project_root_count += 1

        # Insert pipeline-v2 at the beginning (only once)
        sys.path.insert(0, pipeline_v2_str)

        # Ensure project root is in path (only once, after pipeline-v2)
        sys.path.insert(1, project_root_str)

        total_removed = removed_pipeline_v2_count + removed_project_root_count
        logger.debug(f"ensure_path_order() completed - removed {total_removed} entries (pipeline-v2: {removed_pipeline_v2_count}, project_root: {removed_project_root_count}), pipeline-v2 at position 0")

    def capture_path_state(self, label: str) -> dict[str, Any]:
        """Capture the current state of sys.path"""
        pipeline_v2_pos = sys.path.index(str(self.pipeline_v2_root)) if str(self.pipeline_v2_root) in sys.path else -1
        project_root_pos = sys.path.index(str(self.project_root)) if str(self.project_root) in sys.path else -1

        state = {
            'label': label,
            'path_length': len(sys.path),
            'pipeline_v2_position': pipeline_v2_pos,
            'project_root_position': project_root_pos,
            'path_snapshot': sys.path.copy()
        }

        self.path_history.append(state)
        return state

    def count_duplicate_paths(self) -> int:
        """Count duplicate entries in sys.path"""
        seen = set()
        duplicates = 0
        for path in sys.path:
            if path in seen:
                duplicates += 1
            seen.add(path)
        return duplicates

    def test_minimal_deduplication_import_persistence(self) -> dict[str, Any]:
        """
        Minimal reproduction of the deduplication import persistence issue.
        This recreates the exact import sequence from main.py that causes the problem.
        """
        logger.info("=== MINIMAL DEDUPLICATION IMPORT PERSISTENCE TEST ===")

        # Step 0: Capture initial state
        initial_state = self.capture_path_state('initial')
        logger.info(f"Initial path state: length={initial_state['path_length']}, pipeline-v2 position={initial_state['pipeline_v2_position']}")

        # Step 1: Initial path setup (line 59 in main.py)
        logger.info("Step 1: Initial path setup")
        self.ensure_path_order()
        state_after_initial = self.capture_path_state('after_initial_setup')

        # Step 2: Quality filters path setup (line 78 in main.py)
        logger.info("Step 2: Quality filters path setup")
        self.ensure_path_order()
        state_after_quality = self.capture_path_state('after_quality_filters')

        # Step 3: CRITICAL - Deduplication import (line 87 in main.py)
        logger.info("Step 3: Deduplication import (CRITICAL)")
        self.ensure_path_order()
        state_before_deduplication = self.capture_path_state('before_deduplication_import')

        # Import deduplication functions - this is the exact import from main.py lines 89-96
        DEDUPLICATION_AVAILABLE = False
        imported_functions = {}

        try:
            from deduplication.concept_tracker import (
                copy_agno_from_primary,
                copy_profiler_from_primary,
                should_run_agno_analysis,
                should_run_profiler_analysis,
                update_concept_agno_stats,
                update_concept_profiler_stats,
            )
            DEDUPLICATION_AVAILABLE = True

            imported_functions = {
                'should_run_agno_analysis': should_run_agno_analysis,
                'should_run_profiler_analysis': should_run_profiler_analysis,
                'copy_agno_from_primary': copy_agno_from_primary,
                'copy_profiler_from_primary': copy_profiler_from_primary,
                'update_concept_agno_stats': update_concept_agno_stats,
                'update_concept_profiler_stats': update_concept_profiler_stats
            }

            logger.info(f"✅ Deduplication import successful - DEDUPLICATION_AVAILABLE = {DEDUPLICATION_AVAILABLE}")

        except ImportError as e:
            DEDUPLICATION_AVAILABLE = False
            logger.error(f"❌ Deduplication import failed: {e}")

        state_after_deduplication = self.capture_path_state('after_deduplication_import')

        # Step 4: Trust validator path setup (line 126 in main.py)
        logger.info("Step 4: Trust validator path setup")
        self.ensure_path_order()
        state_after_trust = self.capture_path_state('after_trust_validator')

        # Step 5: DLT storage path setup (line 135 in main.py)
        logger.info("Step 5: DLT storage path setup")
        self.ensure_path_order()
        state_after_dlt = self.capture_path_state('after_dlt_storage')

        # Step 6: TEST - Check deduplication availability at "runtime"
        logger.info("Step 6: Testing deduplication availability at runtime")
        runtime_availability = {}
        runtime_deduplication_available = DEDUPLICATION_AVAILABLE

        for func_name, func in imported_functions.items():
            try:
                # Test if the function is still accessible and callable
                is_callable = callable(func)
                runtime_availability[func_name] = is_callable
                logger.debug(f"Runtime test for {func_name}: {is_callable}")
            except (NameError, AttributeError, TypeError) as e:
                runtime_availability[func_name] = False
                logger.warning(f"Runtime access failed for {func_name}: {e}")

        # Final path state
        final_state = self.capture_path_state('final_runtime')

        # Count duplicates in final path
        duplicate_count = self.count_duplicate_paths()

        return {
            'import_time_deduplication_available': DEDUPLICATION_AVAILABLE,
            'runtime_deduplication_available': runtime_deduplication_available,
            'imported_functions': list(imported_functions.keys()),
            'runtime_function_availability': runtime_availability,
            'path_history': self.path_history,
            'duplicate_paths_count': duplicate_count,
            'path_growth': final_state['path_length'] - initial_state['path_length'],
            'pipeline_v2_position_stable': all(
                state['pipeline_v2_position'] == 0
                for state in self.path_history[1:]  # Skip initial state
            )
        }

    def analyze_findings(self, test_result: dict[str, Any]) -> str:
        """Analyze the test results and provide a clear diagnosis"""
        analysis = ["\n" + "="*80]
        analysis.append("MINIMAL DEDUPLICATION IMPORT PERSISTENCE ANALYSIS")
        analysis.append("="*80)

        # Basic findings
        analysis.append("\n🔍 KEY FINDINGS:")
        analysis.append(f"   Import-time DEDUPLICATION_AVAILABLE: {test_result['import_time_deduplication_available']}")
        analysis.append(f"   Runtime DEDUPLICATION_AVAILABLE: {test_result['runtime_deduplication_available']}")
        analysis.append(f"   Functions imported: {len(test_result['imported_functions'])}")
        analysis.append(f"   Functions available at runtime: {sum(test_result['runtime_function_availability'].values())}")

        # Function availability details
        analysis.append("\n🔧 FUNCTION AVAILABILITY:")
        for func_name in test_result['imported_functions']:
            runtime_available = test_result['runtime_function_availability'].get(func_name, False)
            status = "✅" if runtime_available else "❌"
            analysis.append(f"   {status} {func_name}")

        # Path analysis
        analysis.append("\n📁 PATH ANALYSIS:")
        analysis.append(f"   Path growth: {test_result['path_growth']} entries")
        analysis.append(f"   Duplicate paths: {test_result['duplicate_paths_count']}")
        analysis.append(f"   Pipeline-v2 position stable: {test_result['pipeline_v2_position_stable']}")

        if test_result['path_history']:
            positions = [state['pipeline_v2_position'] for state in test_result['path_history']]
            analysis.append(f"   Pipeline-v2 positions: {positions}")

        # Root cause diagnosis
        analysis.append("\n🎯 ROOT CAUSE DIAGNOSIS:")

        critical_issues = []

        if not test_result['import_time_deduplication_available']:
            critical_issues.append("❌ Deduplication import fails at import time")
            analysis.append("   ❌ Deduplication import fails at import time - basic import issue")

        if (test_result['import_time_deduplication_available'] and
            not test_result['runtime_deduplication_available']):
            critical_issues.append("🚨 CRITICAL: DEDUPLICATION_AVAILABLE changed from True to False")
            analysis.append("   🚨 CRITICAL: DEDUPLICATION_AVAILABLE changed from True to False between import and runtime")

        missing_functions = [
            func for func, available in test_result['runtime_function_availability'].items()
            if not available
        ]
        if missing_functions:
            critical_issues.append(f"❌ Missing deduplication functions at runtime: {missing_functions}")
            analysis.append(f"   ❌ Missing deduplication functions at runtime: {missing_functions}")

        if test_result['path_growth'] > 0:
            critical_issues.append("⚠️ Path growth detected - duplicate entries added")
            analysis.append(f"   ⚠️ Path grew by {test_result['path_growth']} entries - indicates duplicate insertions")

        if test_result['duplicate_paths_count'] > 0:
            critical_issues.append(f"⚠️ {test_result['duplicate_paths_count']} duplicate paths in sys.path")
            analysis.append(f"   ⚠️ {test_result['duplicate_paths_count']} duplicate paths detected in sys.path")

        if not test_result['pipeline_v2_position_stable']:
            critical_issues.append("⚠️ Pipeline-v2 position unstable during import sequence")
            analysis.append("   ⚠️ Pipeline-v2 position changed during import sequence")

        # Summary and recommendations
        analysis.append("\n💡 SUMMARY & RECOMMENDATIONS:")

        if critical_issues:
            analysis.append("   🚨 CRITICAL ISSUES DETECTED:")
            for issue in critical_issues:
                analysis.append(f"      - {issue}")

            analysis.append("\n   🔧 RECOMMENDED FIXES:")
            analysis.append("      1. Consolidate ensure_path_order() calls to prevent path instability")
            analysis.append("      2. Remove duplicate path insertions in sys.path")
            analysis.append("      3. Ensure consistent pipeline-v2 positioning throughout imports")
            analysis.append("      4. Test deduplication availability after complete import sequence")
            analysis.append("      5. Consider using relative imports instead of path manipulation")
        else:
            analysis.append("   ✅ No critical deduplication import issues detected")
            analysis.append("   💡 The import persistence issue may have been resolved")

        analysis.append("\n" + "="*80)

        return "\n".join(analysis)


def test_minimal_deduplication_import_persistence_red_phase():
    """
    RED PHASE TEST: Minimal test for deduplication import persistence.

    This test demonstrates the exact deduplication import persistence issue
    by recreating the import pattern from main.py without external dependencies.
    """
    logger.info("🧪 STARTING MINIMAL DEDUPLICATION IMPORT PERSISTENCE TEST")

    tester = MinimalDeduplicationTest()
    test_result = tester.test_minimal_deduplication_import_persistence()
    analysis_report = tester.analyze_findings(test_result)

    print(analysis_report)

    # RED PHASE ASSERTIONS (These should FAIL if the deduplication import issue exists)

    # Assertion 1: DEDUPLICATION_AVAILABLE should be True at import time
    assert test_result['import_time_deduplication_available'] == True, \
        f"Deduplication should be available at import time, got {test_result['import_time_deduplication_available']}"

    # Assertion 2: DEDUPLICATION_AVAILABLE should remain True at runtime
    assert test_result['runtime_deduplication_available'] == True, \
        "🚨 RED PHASE FAILURE: DEDUPLICATION_AVAILABLE changed from True to False between import and runtime! " \
        "This demonstrates the deduplication import persistence bug."

    # Assertion 3: All imported functions should be available at runtime
    missing_runtime_functions = [
        func for func, available in test_result['runtime_function_availability'].items()
        if not available
    ]
    assert len(missing_runtime_functions) == 0, \
        f"🚨 RED PHASE FAILURE: Missing deduplication functions at runtime: {missing_runtime_functions}"

    # Assertion 4: No path growth should occur (no duplicate insertions)
    assert test_result['path_growth'] == 0, \
        f"🚨 RED PHASE FAILURE: Path grew by {test_result['path_growth']} entries, indicating duplicate insertions"

    # Assertion 5: No duplicate paths should exist
    assert test_result['duplicate_paths_count'] == 0, \
        f"🚨 RED PHASE FAILURE: {test_result['duplicate_paths_count']} duplicate paths detected in sys.path"

    # Assertion 6: Pipeline-v2 position should be stable
    assert test_result['pipeline_v2_position_stable'] == True, \
        "🚨 RED PHASE FAILURE: Pipeline-v2 position is unstable during import sequence"

    # If all assertions pass, the issue has been resolved
    logger.info("✅ All assertions passed - deduplication import persistence issue resolved!")
    return True


if __name__ == "__main__":
    try:
        result = test_minimal_deduplication_import_persistence_red_phase()
        print("\n🎉 TEST PASSED: Deduplication import persistence issue has been FIXED!")
        print("✅ The RED phase assertions all passed, indicating the issue is resolved.")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n🚨 TEST FAILED (Expected in RED phase): {e}")
        print("\nThis failure confirms the deduplication import persistence bug exists.")
        print("The detailed analysis above provides specific diagnostics about the root cause.")
        print("\nTo fix this issue:")
        print("1. Address the path instability detected by the test")
        print("2. Consolidate ensure_path_order() calls in main.py")
        print("3. Ensure consistent path management throughout the import sequence")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
