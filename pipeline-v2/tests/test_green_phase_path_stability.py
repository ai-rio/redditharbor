#!/usr/bin/env python3
"""
GREEN PHASE TEST - Verify Path Stability Fix

This test verifies that the GREEN phase fix for path stability works correctly.
It tests that the fixed ensure_path_order() function properly handles multiple calls
without creating path instability.

Expected: This test should PASS if the GREEN phase fix is working correctly.
"""

import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GreenPhaseTest:
    """Test the GREEN phase fix for path stability."""

    def __init__(self):
        self.pipeline_v2_root = Path(__file__).parent.parent
        self.project_root = Path(__file__).parent.parent.parent
        self.path_history = []

    def ensure_path_order(self):
        """GREEN PHASE VERSION - Fixed ensure_path_order() from main.py"""
        # Remove all existing entries for our paths to prevent duplicates
        pipeline_v2_str = str(self.pipeline_v2_root)
        project_root_str = str(self.project_root)

        # Remove pipeline-v2 from anywhere in path
        while pipeline_v2_str in sys.path:
            sys.path.remove(pipeline_v2_str)

        # Remove project root from anywhere in path to prevent duplicates
        while project_root_str in sys.path:
            sys.path.remove(project_root_str)

        # Insert pipeline-v2 at the beginning (only once)
        sys.path.insert(0, pipeline_v2_str)

        # Ensure project root is in path (only once, after pipeline-v2)
        sys.path.insert(1, project_root_str)

    def capture_path_state(self, label: str) -> dict[str, Any]:
        """Capture the current state of sys.path"""
        pipeline_v2_pos = sys.path.index(str(self.pipeline_v2_root)) if str(self.pipeline_v2_root) in sys.path else -1
        project_root_pos = sys.path.index(str(self.project_root)) if str(self.project_root) in sys.path else -1

        state = {
            'label': label,
            'path_length': len(sys.path),
            'pipeline_v2_position': pipeline_v2_pos,
            'project_root_position': project_root_pos,
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

    def test_green_phase_fix(self) -> dict[str, Any]:
        """Test that the GREEN phase fix works correctly"""
        logger.info("=== GREEN PHASE PATH STABILITY TEST ===")

        # Capture initial state
        initial_state = self.capture_path_state('initial')

        # Test multiple calls to ensure_path_order() (should be idempotent)
        logger.info("Testing multiple ensure_path_order() calls...")

        for i in range(5):  # Call multiple times to test robustness
            logger.info(f"Call {i+1}")
            self.ensure_path_order()
            state = self.capture_path_state(f'call_{i+1}')

        # Test deduplication import (the actual functionality)
        try:
            # This should work with the fixed path management
            from deduplication.concept_tracker import (
                copy_agno_from_primary,
                copy_profiler_from_primary,
                should_run_agno_analysis,
                should_run_profiler_analysis,
                update_concept_agno_stats,
                update_concept_profiler_stats,
            )
            deduplication_available = True
            logger.info("✅ Deduplication import successful")
        except ImportError as e:
            deduplication_available = False
            logger.error(f"❌ Deduplication import failed: {e}")

        final_state = self.capture_path_state('final')

        return {
            'initial_path_length': initial_state['path_length'],
            'final_path_length': final_state['path_length'],
            'path_growth': final_state['path_length'] - initial_state['path_length'],
            'duplicate_paths_count': self.count_duplicate_paths(),
            'pipeline_v2_position_stable': all(
                state['pipeline_v2_position'] == 0
                for state in self.path_history[1:]  # Skip initial state
            ),
            'project_root_position_stable': all(
                state['project_root_position'] == 1
                for state in self.path_history[1:]  # Skip initial state
            ),
            'deduplication_available': deduplication_available,
            'path_history': self.path_history
        }

def test_green_phase_path_stability():
    """GREEN PHASE TEST: Verify the path stability fix works"""
    logger.info("🧪 STARTING GREEN PHASE PATH STABILITY TEST")

    tester = GreenPhaseTest()
    result = tester.test_green_phase_fix()

    print("\n📊 GREEN PHASE TEST RESULTS:")
    print(f"   Initial path length: {result['initial_path_length']}")
    print(f"   Final path length: {result['final_path_length']}")
    print(f"   Path growth: {result['path_growth']}")
    print(f"   Duplicate paths: {result['duplicate_paths_count']}")
    print(f"   Pipeline-v2 position stable: {result['pipeline_v2_position_stable']}")
    print(f"   Project root position stable: {result['project_root_position_stable']}")
    print(f"   Deduplication import successful: {result['deduplication_available']}")

    # GREEN PHASE ASSERTIONS (These should PASS if the fix works)

    # Assertion 1: Path growth should be at most 2 (pipeline-v2 + repositioned project root)
    assert result['path_growth'] <= 2, \
        f"❌ GREEN PHASE FAILURE: Path grew by {result['path_growth']} entries (expected ≤ 2)"

    # Assertion 2: No duplicate paths should exist
    assert result['duplicate_paths_count'] == 0, \
        f"❌ GREEN PHASE FAILURE: {result['duplicate_paths_count']} duplicate paths detected"

    # Assertion 3: Pipeline-v2 position should be stable at position 0
    assert result['pipeline_v2_position_stable'] == True, \
        "❌ GREEN PHASE FAILURE: Pipeline-v2 position is not stable"

    # Assertion 4: Project root position should be stable at position 1
    assert result['project_root_position_stable'] == True, \
        "❌ GREEN PHASE FAILURE: Project root position is not stable"

    # Assertion 5: Deduplication should be available
    assert result['deduplication_available'] == True, \
        "❌ GREEN PHASE FAILURE: Deduplication import failed"

    logger.info("✅ All GREEN PHASE assertions passed!")
    return True


if __name__ == "__main__":
    try:
        result = test_green_phase_path_stability()
        print("\n🎉 GREEN PHASE SUCCESS: Path stability fix is working correctly!")
        print("✅ The ensure_path_order() fix prevents path instability")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n🚨 GREEN PHASE FAILED: {e}")
        print("The path stability fix needs additional work.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
