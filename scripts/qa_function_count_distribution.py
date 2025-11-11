#!/usr/bin/env python3
"""
QA Test: Function Count Distribution Analysis
Verifies that the function-count bias fix actually resolved the 95%+ bias to 2 functions

This script analyzes the distribution of function counts in:
1. app_opportunities.core_functions (JSONB array)
2. workflow_results.function_list (JSONB array)
3. workflow_results.function_count (INTEGER)

Expected outcome after fix:
- Distribution should be more varied (not 95%+ at 2 functions)
- Validation should catch any mismatches between count and list length
- Both tables should have consistent function data
"""

import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import SUPABASE_KEY, SUPABASE_URL
from supabase import create_client


def analyze_function_count_distribution() -> dict[str, Any]:
    """
    Analyze function count distribution across both tables.

    Returns:
        Dict with analysis results including:
        - Distribution statistics
        - Mismatch detection
        - Bias assessment
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("="*80)
    print("QA TEST: Function Count Distribution Analysis")
    print("="*80)
    print()

    # 1. Analyze app_opportunities table
    print("📊 Analyzing app_opportunities.core_functions...")
    app_result = supabase.table('app_opportunities').select('submission_id, core_functions').execute()

    app_counts = []
    app_distribution = Counter()

    for row in app_result.data:
        core_funcs = row.get('core_functions', [])
        if core_funcs:
            count = len(core_funcs)
            app_counts.append(count)
            app_distribution[count] += 1

    total_app = len(app_counts)
    print(f"  Total opportunities with core_functions: {total_app}")

    if total_app > 0:
        print("\n  Distribution:")
        for count in sorted(app_distribution.keys()):
            percentage = (app_distribution[count] / total_app) * 100
            print(f"    {count} functions: {app_distribution[count]:3d} ({percentage:5.1f}%)")

        # Calculate bias metric
        two_func_percentage = (app_distribution.get(2, 0) / total_app) * 100 if total_app > 0 else 0
        print(f"\n  📈 Bias Metric: {two_func_percentage:.1f}% have exactly 2 functions")

        if two_func_percentage > 90:
            print(f"  ⚠️  WARNING: Still heavily biased to 2 functions (>{two_func_percentage:.0f}%)")
        elif two_func_percentage > 70:
            print(f"  ⚡ Moderate bias to 2 functions ({two_func_percentage:.0f}%)")
        else:
            print(f"  ✅ Good distribution (only {two_func_percentage:.0f}% at 2 functions)")

    print()

    # 2. Analyze workflow_results table
    print("📊 Analyzing workflow_results.function_list...")
    wf_result = supabase.table('workflow_results').select(
        'opportunity_id, function_count, function_list'
    ).execute()

    wf_counts = []
    wf_distribution = Counter()
    mismatches = []

    for row in wf_result.data:
        function_list = row.get('function_list', [])
        function_count = row.get('function_count', 0)

        if function_list:
            actual_count = len(function_list)
            wf_counts.append(actual_count)
            wf_distribution[actual_count] += 1

            # Check for mismatch
            if actual_count != function_count:
                mismatches.append({
                    'opportunity_id': row.get('opportunity_id'),
                    'declared_count': function_count,
                    'actual_count': actual_count
                })

    total_wf = len(wf_counts)
    print(f"  Total opportunities with function_list: {total_wf}")

    if total_wf > 0:
        print("\n  Distribution:")
        for count in sorted(wf_distribution.keys()):
            percentage = (wf_distribution[count] / total_wf) * 100
            print(f"    {count} functions: {wf_distribution[count]:3d} ({percentage:5.1f}%)")

        # Calculate bias metric
        two_func_percentage_wf = (wf_distribution.get(2, 0) / total_wf) * 100 if total_wf > 0 else 0
        print(f"\n  📈 Bias Metric: {two_func_percentage_wf:.1f}% have exactly 2 functions")

        if two_func_percentage_wf > 90:
            print(f"  ⚠️  WARNING: Still heavily biased to 2 functions (>{two_func_percentage_wf:.0f}%)")
        elif two_func_percentage_wf > 70:
            print(f"  ⚡ Moderate bias to 2 functions ({two_func_percentage_wf:.0f}%)")
        else:
            print(f"  ✅ Good distribution (only {two_func_percentage_wf:.0f}% at 2 functions)")

    print()

    # 3. Check for validation mismatches
    print("🔍 Checking for function_count/function_list mismatches...")
    if mismatches:
        print(f"  ❌ FOUND {len(mismatches)} mismatches:")
        for mm in mismatches[:5]:
            print(f"    - {mm['opportunity_id']}: declared={mm['declared_count']}, actual={mm['actual_count']}")
        if len(mismatches) > 5:
            print(f"    ... and {len(mismatches) - 5} more")
    else:
        print("  ✅ No mismatches found - validation working correctly!")

    print()

    # 4. Summary and verdict
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    results = {
        'app_opportunities': {
            'total': total_app,
            'distribution': dict(app_distribution),
            'two_func_percentage': two_func_percentage if total_app > 0 else 0
        },
        'workflow_results': {
            'total': total_wf,
            'distribution': dict(wf_distribution),
            'two_func_percentage': two_func_percentage_wf if total_wf > 0 else 0,
            'mismatches': len(mismatches)
        }
    }

    # Verdict
    print("📋 Test Results:")
    print()

    if total_app == 0 and total_wf == 0:
        print("  ⚠️  NO DATA: No opportunities found with function data")
        print("  → Run batch scoring with SCORE_THRESHOLD=25.0 to generate test data")
        verdict = "NO_DATA"
    elif total_app < 10 or total_wf < 10:
        print(f"  ⚠️  INSUFFICIENT DATA: Only {max(total_app, total_wf)} opportunities")
        print("  → Need 50+ opportunities for meaningful distribution analysis")
        print("  → Current results may not be representative")
        verdict = "INSUFFICIENT_DATA"
    else:
        # With sufficient data, assess the fix
        avg_bias = (results['app_opportunities']['two_func_percentage'] +
                    results['workflow_results']['two_func_percentage']) / 2

        if avg_bias > 90:
            print(f"  ❌ BIAS STILL PRESENT: {avg_bias:.1f}% still at 2 functions")
            print("  → The fix did NOT resolve the distribution issue")
            print("  → LLM prompt may still be too biased")
            verdict = "FAILED"
        elif avg_bias > 70:
            print(f"  ⚡ PARTIAL IMPROVEMENT: {avg_bias:.1f}% at 2 functions")
            print("  → Some improvement but still moderate bias")
            print("  → May need to adjust LLM prompt scoring")
            verdict = "PARTIAL"
        else:
            print(f"  ✅ BIAS RESOLVED: Only {avg_bias:.1f}% at 2 functions")
            print("  → Good distribution across 1-3 functions")
            print("  → Fix appears to be working correctly")
            verdict = "PASSED"

        if mismatches:
            print(f"\n  ⚠️  VALIDATION ISSUES: {len(mismatches)} count/list mismatches found")
            print("  → Pre-flight validation may not be catching all cases")
        else:
            print("\n  ✅ VALIDATION WORKING: No count/list mismatches")

    print()
    print("="*80)

    return {
        'results': results,
        'verdict': verdict,
        'mismatches': mismatches
    }


def main():
    """Run the QA analysis"""
    try:
        analysis = analyze_function_count_distribution()

        # Exit with appropriate code
        verdict = analysis['verdict']
        if verdict == "PASSED":
            sys.exit(0)
        elif verdict in ["NO_DATA", "INSUFFICIENT_DATA"]:
            sys.exit(1)
        else:
            sys.exit(2)

    except Exception as e:
        print(f"\n❌ Error running QA analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
