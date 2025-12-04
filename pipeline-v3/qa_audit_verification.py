#!/usr/bin/env python3
"""
Automated QA Audit Verification Script for Phase 3 Jina Integration
Run this script to verify all claims in the QA checkpoint report.

Usage:
    python qa_audit_verification.py

Expected Results:
- TDD Test Suite: 36/36 tests passing
- Jina Client Tests: 13/13 tests passing
- Production Modules: All imports and functionality working
- Overall Status: PASSED
"""

import subprocess
import sys
import asyncio
import json
import os
import re

def run_command(cmd, description, timeout=60):
    """Run command and return success status"""
    print(f"\n🔍 {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if result.returncode == 0:
            print(f"✅ {description}: SUCCESS")
            # Extract test count from output
            if "passed" in result.stdout:
                match = re.search(r'(\d+)\s+passed', result.stdout)
                if match:
                    print(f"   Tests passed: {match.group(1)}")
                # Also show failures if any
                match_fail = re.search(r'(\d+)\s+failed', result.stdout)
                if match_fail:
                    print(f"   Tests failed: {match_fail.group(1)}")
            return True, result.stdout
        else:
            print(f"❌ {description}: FAILED")
            print(f"   Return code: {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr[:500]}...")
            return False, result.stderr

    except subprocess.TimeoutExpired:
        print(f"❌ {description}: TIMEOUT after {timeout}s")
        return False, "Command timed out"
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")
        return False, str(e)

async def test_production_imports():
    """Test production module imports"""
    print("\n🔍 Testing Production Module Imports")

    results = {}

    # Test PrometheusMetrics
    try:
        from production.monitoring import PrometheusMetrics
        results['prometheus_metrics'] = True
        print("✅ PrometheusMetrics import: SUCCESS")
        print(f"   Class: {PrometheusMetrics.__name__}")
        print(f"   Module: {PrometheusMetrics.__module__}")
    except Exception as e:
        results['prometheus_metrics'] = False
        print(f"❌ PrometheusMetrics import: FAILED - {e}")

    # Test HealthCheckEndpoint
    try:
        from production.health import HealthCheckEndpoint
        results['health_endpoint'] = True
        print("✅ HealthCheckEndpoint import: SUCCESS")
        print(f"   Class: {HealthCheckEndpoint.__name__}")
        print(f"   Module: {HealthCheckEndpoint.__module__}")
    except Exception as e:
        results['health_endpoint'] = False
        print(f"❌ HealthCheckEndpoint import: FAILED - {e}")

    # Test combined import
    try:
        from production import PrometheusMetrics, HealthCheckEndpoint
        results['combined_import'] = True
        print("✅ Combined import: SUCCESS")
    except Exception as e:
        results['combined_import'] = False
        print(f"❌ Combined import: FAILED - {e}")

    # Test functionality
    if results.get('health_endpoint'):
        try:
            health_checker = HealthCheckEndpoint()
            print("✅ HealthCheckEndpoint instance: SUCCESS")

            # Test basic functionality
            status = await health_checker.get_health_status()
            results['health_functionality'] = True
            print("✅ Health check functionality: SUCCESS")
            print(f"   Status: {status.get('status', 'unknown')}")
            print(f"   Components: {len(status.get('components', {}))}")

            # Test readiness
            readiness = await health_checker.readiness_check()
            print(f"   Ready: {readiness.get('ready', False)}")

            # Test liveness
            liveness = await health_checker.liveness_check()
            print(f"   Alive: {liveness.get('alive', False)}")
            print(f"   Uptime: {liveness.get('uptime_seconds', 0):.1f}s")

        except Exception as e:
            results['health_functionality'] = False
            print(f"❌ Health check functionality: FAILED - {e}")

    return results

def verify_configuration():
    """Verify configuration files"""
    print("\n🔍 Verifying Configuration Files")

    results = {}

    # Check pytest.ini
    try:
        if os.path.exists('pytest.ini'):
            with open('pytest.ini', 'r') as f:
                content = f.read()
                if 'asyncio_mode = auto' in content:
                    results['pytest_config'] = True
                    print("✅ pytest.ini async configuration: CORRECT")
                else:
                    results['pytest_config'] = False
                    print("❌ pytest.ini async configuration: MISSING")
        else:
            results['pytest_config'] = False
            print("❌ pytest.ini file: NOT FOUND")
    except Exception as e:
        results['pytest_config'] = False
        print(f"❌ pytest.ini check: FAILED - {e}")

    # Check pyproject.toml for pytest-asyncio
    try:
        if os.path.exists('pyproject.toml'):
            with open('pyproject.toml', 'r') as f:
                content = f.read()
                if 'pytest-asyncio' in content:
                    results['pytest_asyncio_dep'] = True
                    print("✅ pytest-asyncio dependency: PRESENT")
                else:
                    results['pytest_asyncio_dep'] = False
                    print("❌ pytest-asyncio dependency: MISSING")
        else:
            results['pytest_asyncio_dep'] = False
            print("❌ pyproject.toml file: NOT FOUND")
    except Exception as e:
        results['pytest_asyncio_dep'] = False
        print(f"❌ pyproject.toml check: FAILED - {e}")

    # Check production module structure
    try:
        production_exists = os.path.exists('production') and os.path.isdir('production')
        monitoring_exists = os.path.exists('production/monitoring.py')
        health_exists = os.path.exists('production/health.py')
        init_exists = os.path.exists('production/__init__.py')

        results['production_structure'] = all([production_exists, monitoring_exists, health_exists, init_exists])

        if production_exists:
            print("✅ production/ directory: EXISTS")
        else:
            print("❌ production/ directory: MISSING")

        if monitoring_exists:
            print("✅ production/monitoring.py: EXISTS")
        else:
            print("❌ production/monitoring.py: MISSING")

        if health_exists:
            print("✅ production/health.py: EXISTS")
        else:
            print("❌ production/health.py: MISSING")

        if init_exists:
            print("✅ production/__init__.py: EXISTS")
        else:
            print("❌ production/__init__.py: MISSING")

    except Exception as e:
        results['production_structure'] = False
        print(f"❌ Production structure check: FAILED - {e}")

    return results

async def main():
    """Main audit verification"""
    print("=" * 70)
    print("🔍 PHASE 3 JINA INTEGRATION - QA AUDIT VERIFICATION")
    print("=" * 70)
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    print(f"Virtual environment: {os.getenv('VIRTUAL_ENV', 'Not detected')}")

    # Check if we're in the right directory
    if not os.path.exists('tests') or not os.path.exists('transform'):
        print("\n❌ ERROR: Not in pipeline-v3 directory!")
        print("Please run this script from: /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3")
        return False

    audit_results = {
        'timestamp': str(asyncio.get_event_loop().time()),
        'working_directory': os.getcwd(),
        'tdd_tests': False,
        'jina_tests': False,
        'production_imports': {},
        'configuration': {},
        'overall_status': 'FAILED'
    }

    # Test 1: TDD Test Suite
    success, output = run_command([
        sys.executable, '-m', 'pytest',
        'tests/transform/test_market_research_agent_tdd.py',
        '-q'
    ], "TDD Test Suite Verification", timeout=120)

    audit_results['tdd_tests'] = success
    if success:
        match = re.search(r'(\d+)\s+passed', output)
        failed_match = re.search(r'(\d+)\s+failed', output)

        passed_count = int(match.group(1)) if match else 0
        failed_count = int(failed_match.group(1)) if failed_match else 0

        if passed_count == 36 and failed_count == 0:
            print("   ✅ Expected 36/36 tests passing: CONFIRMED")
        else:
            print(f"   ❌ Expected 36/36 tests passing: GOT {passed_count}/{passed_count + failed_count}")
            audit_results['tdd_tests'] = False

    # Test 2: Jina Client Test Suite
    success, output = run_command([
        sys.executable, '-m', 'pytest',
        'tests/transform/test_jina_client.py',
        '-q'
    ], "Jina Client Test Suite Verification", timeout=120)

    audit_results['jina_tests'] = success
    if success:
        match = re.search(r'(\d+)\s+passed', output)
        failed_match = re.search(r'(\d+)\s+failed', output)

        passed_count = int(match.group(1)) if match else 0
        failed_count = int(failed_match.group(1)) if failed_match else 0

        if passed_count == 13 and failed_count == 0:
            print("   ✅ Expected 13/13 tests passing: CONFIRMED")
        else:
            print(f"   ❌ Expected 13/13 tests passing: GOT {passed_count}/{passed_count + failed_count}")
            audit_results['jina_tests'] = False

    # Test 3: Configuration
    audit_results['configuration'] = verify_configuration()

    # Test 4: Production Module Imports
    audit_results['production_imports'] = await test_production_imports()

    # Overall assessment
    all_tdd_pass = audit_results['tdd_tests']
    all_jina_pass = audit_results['jina_tests']
    config_ok = (
        audit_results['configuration'].get('pytest_config', False) and
        audit_results['configuration'].get('pytest_asyncio_dep', False) and
        audit_results['configuration'].get('production_structure', False)
    )
    production_works = (
        audit_results['production_imports'].get('prometheus_metrics', False) and
        audit_results['production_imports'].get('health_endpoint', False) and
        audit_results['production_imports'].get('combined_import', False) and
        audit_results['production_imports'].get('health_functionality', False)
    )

    if all_tdd_pass and all_jina_pass and config_ok and production_works:
        audit_results['overall_status'] = 'PASSED'

    # Final results
    print("\n" + "=" * 70)
    print("🏁 QA AUDIT RESULTS")
    print("=" * 70)

    print(f"TDD Test Suite (36/36): {'✅ PASS' if all_tdd_pass else '❌ FAIL'}")
    print(f"Jina Client Tests (13/13): {'✅ PASS' if all_jina_pass else '❌ FAIL'}")
    print(f"Configuration Files: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Production Modules: {'✅ PASS' if production_works else '❌ FAIL'}")
    print("-" * 70)
    print(f"OVERALL STATUS: {'✅ PASSED' if audit_results['overall_status'] == 'PASSED' else '❌ FAILED'}")

    # Save results
    results_file = 'qa_audit_results.json'
    with open(results_file, 'w') as f:
        json.dump(audit_results, f, indent=2)

    print(f"\n📄 Detailed results saved to: {results_file}")

    # Summary
    if audit_results['overall_status'] == 'PASSED':
        print("\n🎉 ALL CLAIMS IN QA CHECKPOINT REPORT VERIFIED!")
        print("✅ Phase 3 Jina Integration is ready for production deployment")
    else:
        print("\n❌ QA AUDIT FAILED - Some claims could not be verified")
        print("Please review the detailed results and fix any issues before deployment")

    return audit_results['overall_status'] == 'PASSED'

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Audit interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Audit script error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)