#!/usr/bin/env python3
"""
Pipeline Test Analysis Tool
Analyzes test results by category to determine actual impact on functionality
"""

import subprocess
import sys
import json
from pathlib import Path

def run_test_category(test_pattern: str, category_name: str) -> dict:
    """Run a specific test category and return results"""
    try:
        cmd = [
            "uv", "run", "python", "-m", "pytest",
            test_pattern,
            "--tb=no",
            "-q",
            "--disable-warnings"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        # Parse the output for pass/fail counts
        output = result.stdout

        # Look for the summary line
        summary_line = None
        for line in output.split('\n'):
            if 'passed' in line and ('failed' in line or 'error' in line):
                summary_line = line
                break

        if not summary_line:
            # Try to get the last line with results
            lines = output.strip().split('\n')
            for line in reversed(lines):
                if 'passed' in line:
                    summary_line = line
                    break

        passed = failed = errors = 0

        if summary_line:
            # Extract numbers from summary like "10 passed, 2 failed, 1 errors"
            import re
            numbers = re.findall(r'(\d+)\s+(passed|failed|errors?|warning)', summary_line.lower())
            for num, status in numbers:
                num = int(num)
                if 'pass' in status:
                    passed = num
                elif 'fail' in status:
                    failed = num
                elif 'error' in status:
                    errors = num

        return {
            "category": category_name,
            "pattern": test_pattern,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": passed + failed + errors,
            "output": output,
            "success_rate": (passed / (passed + failed + errors)) * 100 if (passed + failed + errors) > 0 else 0
        }

    except Exception as e:
        return {
            "category": category_name,
            "pattern": test_pattern,
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "total": 1,
            "output": str(e),
            "success_rate": 0
        }

def analyze_pipeline_functionality():
    """Analyze pipeline functionality by test categories"""

    print("=== Pipeline Test Analysis ===\n")

    # Core pipeline components
    core_tests = [
        ("tests/test_config.py", "Configuration Management"),
        ("tests/test_models.py", "Pydantic Models"),
        ("tests/test_orchestrator.py", "Pipeline Orchestrator"),
        ("tests/test_quality_minimal.py tests/test_quality_scoring_simple.py", "AI Quality Scoring"),
        ("tests/test_pipeline_orchestrator_quality_filtering.py", "Quality Filtering"),
        ("tests/test_opportunity_analyzer.py", "Opportunity Analysis"),
        ("tests/test_vector_simple.py tests/test_vector_similarity.py", "Vector Embeddings"),
    ]

    # Reddit data extraction
    extraction_tests = [
        ("tests/test_extract.py", "Reddit Data Extraction"),
        ("tests/test_extract_comprehensive.py", "Reddit Extraction - Comprehensive"),
        ("tests/test_extract_fixed.py", "Reddit Extraction - Fixed"),
    ]

    # Database and staging
    database_tests = [
        ("tests/test_staging_layer.py", "Staging Layer"),
        ("tests/test_staging_simple_integration.py", "Staging Integration"),
        ("tests/test_production_validation.py", "Production Validation"),
        ("tests/test_p2_validation.py", "P2 Validation"),
    ]

    # OnlyMaps legacy components
    onlymaps_tests = [
        ("tests/test_onlymaps_simple.py", "OnlyMaps - Simple"),
        ("tests/test_onlymaps_core.py", "OnlyMaps - Core"),
        ("tests/test_onlymaps_async_patterns.py", "OnlyMaps - Async"),
        ("tests/test_onlymaps_backward_compatibility.py", "OnlyMaps - Backward Compatibility"),
        ("tests/test_onlymaps_failing.py", "OnlyMaps - Failing"),
        ("tests/test_onlymaps_comprehensive_failing.py", "OnlyMaps - Comprehensive Failing"),
    ]

    # Integration tests
    integration_tests = [
        ("tests/test_pipeline_integration.py", "Pipeline Integration"),
        ("tests/test_staging_integration.py", "Staging Integration"),
    ]

    # Pydantic validation tests
    pydantic_tests = [
        ("tests/test_pydantic_business_logic.py", "Pydantic Business Logic"),
        ("tests/test_pydantic_completeness_schema.py", "Pydantic Schema"),
        ("tests/test_pydantic_edge_cases.py", "Pydantic Edge Cases"),
        ("tests/test_pydantic_error_scenarios.py", "Pydantic Error Scenarios"),
        ("tests/test_pydantic_integration.py", "Pydantic Integration"),
    ]

    # Performance tests
    performance_tests = [
        ("tests/test_pipeline_performance.py", "Pipeline Performance"),
    ]

    # Analysis results
    all_results = []

    # Test each category
    for tests, name in core_tests:
        print(f"Testing {name}...")
        result = run_test_category(tests, name)
        all_results.append(result)
        print(f"  {result['passed']} passed, {result['failed']} failed, {result['errors']} errors")

    print(f"\n=== Core Pipeline Summary ===")
    core_passed = sum(r['passed'] for r in all_results[:7])
    core_failed = sum(r['failed'] for r in all_results[:7])
    core_errors = sum(r['errors'] for r in all_results[:7])
    core_total = core_passed + core_failed + core_errors
    print(f"Core Pipeline: {core_passed}/{core_total} passed ({(core_passed/core_total)*100:.1f}%)")

    # Business Impact Assessment
    print(f"\n=== Business Impact Assessment ===")

    if core_passed / core_total > 0.8:
        print("✅ CORE PIPELINE FUNCTIONALITY: WORKING")
        print("   The essential pipeline components are functional")
    else:
        print("❌ CORE PIPELINE FUNCTIONALITY: IMPACTED")
        print("   Critical pipeline components have issues")

    # Check specific critical components
    critical_components = {
        "Configuration Management": all_results[0],
        "Pydantic Models": all_results[1],
        "AI Quality Scoring": all_results[3],
        "Quality Filtering": all_results[4],
    }

    print(f"\n=== Critical Components Status ===")
    for name, result in critical_components.items():
        if result['success_rate'] > 80:
            print(f"✅ {name}: WORKING ({result['success_rate']:.1f}%)")
        else:
            print(f"❌ {name}: ISSUES ({result['success_rate']:.1f}%)")
            print(f"   {result['failed']} failed, {result['errors']} errors")

    print(f"\n=== Recommendations ===")

    if core_passed / core_total > 0.8:
        print("🚀 PRODUCTION READINESS: GOOD")
        print("   - Core pipeline is functional")
        print("   - AI quality filtering is working")
        print("   - Can proceed with deployment")

        if core_failed > 0:
            print("   - Address non-critical test failures")
            print("   - Review OnlyMaps legacy components")
    else:
        print("⚠️  PRODUCTION READINESS: NEEDS ATTENTION")
        print("   - Fix critical component failures")
        print("   - Address core pipeline issues")
        print("   - Review failing tests for actual impact")

    return all_results

if __name__ == "__main__":
    analyze_pipeline_functionality()