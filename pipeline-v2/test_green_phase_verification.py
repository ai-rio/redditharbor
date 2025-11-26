#!/usr/bin/env python3
"""
Simple verification script to test the GREEN phase test updates.

This script runs a few basic checks to verify that the updated characterization
tests can access and validate the main.py implementation correctly.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_main_import():
    """Test that main.py can be imported and has expected functions."""
    try:
        import main
        print("✅ main.py imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import main.py: {e}")
        return False

def test_step_functions():
    """Test that all 6 step functions exist and are callable."""
    try:
        import main

        expected_step_functions = [
            'step1_fetch_reddit_submissions',
            'step2_pre_ai_quality_filter',
            'step3_deduplication_check',
            'step4_ai_analysis',
            'step5_trust_validation',
            'step6_dlt_integration'
        ]

        missing_functions = []
        for func_name in expected_step_functions:
            if not hasattr(main, func_name):
                missing_functions.append(func_name)
            elif not callable(getattr(main, func_name)):
                missing_functions.append(f"{func_name} (not callable)")

        if missing_functions:
            print(f"❌ Missing or non-callable functions: {missing_functions}")
            return False
        else:
            print("✅ All 6 step functions exist and are callable")
            return True

    except ImportError as e:
        print(f"❌ Failed to test step functions: {e}")
        return False

def test_main_orchestrator():
    """Test main orchestrator functions."""
    try:
        import main

        # Test main function exists
        if not hasattr(main, 'main'):
            print("❌ main() function missing")
            return False
        if not callable(main.main):
            print("❌ main() is not callable")
            return False

        # Test parse_arguments exists
        if not hasattr(main, 'parse_arguments'):
            print("❌ parse_arguments() function missing")
            return False
        if not callable(main.parse_arguments):
            print("❌ parse_arguments() is not callable")
            return False

        print("✅ Main orchestrator functions exist and are callable")
        return True

    except ImportError as e:
        print(f"❌ Failed to test main orchestrator: {e}")
        return False

def test_configuration_imports():
    """Test that required configuration variables are imported."""
    try:
        import main

        expected_config_vars = [
            'REDDIT_PUBLIC', 'REDDIT_SECRET', 'REDDIT_USER_AGENT',
            'SUPABASE_URL', 'SUPABASE_KEY', 'ERROR_LOG_DIR'
        ]

        missing_vars = []
        for var in expected_config_vars:
            if not hasattr(main, var):
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ Missing config variables: {missing_vars}")
            return False
        else:
            print("✅ All configuration variables imported")
            return True

    except ImportError as e:
        print(f"❌ Failed to test configuration imports: {e}")
        return False

def test_dependency_flags():
    """Test that dependency availability flags exist."""
    try:
        import main

        expected_flags = [
            'QUALITY_FILTERS_AVAILABLE',
            'DEDUPLICATION_AVAILABLE',
            'OPPORTUNITY_ANALYZER_AVAILABLE',
            'MONETIZATION_ANALYZER_AVAILABLE',
            'PROFILER_AVAILABLE',
            'TRUST_VALIDATOR_AVAILABLE',
            'SUPABASE_AVAILABLE'
        ]

        missing_flags = []
        invalid_flags = []
        for flag in expected_flags:
            if not hasattr(main, flag):
                missing_flags.append(flag)
            elif not isinstance(getattr(main, flag), bool):
                invalid_flags.append(f"{flag} (not boolean)")

        if missing_flags:
            print(f"❌ Missing availability flags: {missing_flags}")
            return False
        if invalid_flags:
            print(f"❌ Invalid availability flags: {invalid_flags}")
            return False
        else:
            print("✅ All dependency availability flags exist and are boolean")
            return True

    except ImportError as e:
        print(f"❌ Failed to test dependency flags: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🧪 GREEN Phase Test Verification")
    print("=" * 50)

    tests = [
        ("Main Import", test_main_import),
        ("Step Functions", test_step_functions),
        ("Main Orchestrator", test_main_orchestrator),
        ("Configuration Imports", test_configuration_imports),
        ("Dependency Flags", test_dependency_flags)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All GREEN phase verification tests passed!")
        print("✅ The updated characterization tests should now work correctly")
        return 0
    else:
        print("❌ Some verification tests failed")
        print("⚠️  The characterization tests may need further adjustments")
        return 1

if __name__ == "__main__":
    sys.exit(main())