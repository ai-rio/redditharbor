#!/usr/bin/env python3
"""
End-to-End Cost Tracking Pipeline Test
Tests the complete pipeline with cost tracking from LLM profiler to database storage
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env.local')

try:
    from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
    from core.dlt_cost_tracking import (
        load_opportunities_with_costs,
        generate_cost_report,
        validate_cost_data
    )
    from core.cost_tracking_error_handler import validate_and_handle_costs
    from supabase import create_client
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed")
    sys.exit(1)


def test_llm_profiler_cost_tracking() -> Dict[str, Any]:
    """
    Test the LLM profiler with cost tracking.

    Returns:
        Test results with cost data
    """
    print("🧠 Testing LLM Profiler with Cost Tracking...")

    test_results = {
        'success': False,
        'profiles_generated': 0,
        'total_cost_usd': 0.0,
        'total_tokens': 0,
        'profiles': [],
        'errors': []
    }

    try:
        # Initialize LLM profiler
        profiler = EnhancedLLMProfiler()
        print("✓ LLM profiler initialized")

        # Test data with varying complexity
        test_opportunities = [
            {
                'text': "I'm so frustrated with budgeting apps. They're all too expensive and none of them sync properly with my bank. I just want something simple that works and doesn't cost $15/month. Why is there no good solution for this?",
                'title': "Looking for a better budgeting app",
                'subreddit': "personalfinance",
                'score': 72.5,
                'expected_cost_range': (0.001, 0.010)
            },
            {
                'text': "My team wastes hours every week manually copying data between spreadsheets. We need something that can automatically sync our sales data from CRM to Google Sheets. The existing solutions are either too expensive or don't have the integrations we need.",
                'title': "Need automated CRM to Sheets sync",
                'subreddit': "productivity",
                'score': 68.0,
                'expected_cost_range': (0.001, 0.010)
            },
            {
                'text': "I keep forgetting to take my medications on time. I've tried pill boxes and phone alarms, but I still miss doses. There has to be a smarter way to manage medication schedules with reminders and tracking.",
                'title': "Struggling with medication adherence",
                'subreddit': "health",
                'score': 65.5,
                'expected_cost_range': (0.001, 0.010)
            }
        ]

        profiles = []
        total_cost = 0.0
        total_tokens = 0

        for i, test_opp in enumerate(test_opportunities):
            print(f"\n  Processing test opportunity {i+1}/3...")

            try:
                # Generate profile with cost tracking
                profile, cost_data = profiler.generate_app_profile_with_costs(
                    text=test_opp['text'],
                    title=test_opp['title'],
                    subreddit=test_opp['subreddit'],
                    score=test_opp['score']
                )

                # Validate cost data
                if 'total_cost_usd' in cost_data:
                    cost = cost_data['total_cost_usd']
                    tokens = cost_data.get('total_tokens', 0)

                    # Check if cost is within expected range
                    min_cost, max_cost = test_opp['expected_cost_range']
                    if min_cost <= cost <= max_cost:
                        print(f"    ✓ Cost ${cost:.6f} within expected range")
                    else:
                        print(f"    ⚠️  Cost ${cost:.6f} outside expected range ${min_cost:.6f}-${max_cost:.6f}")

                    total_cost += cost
                    total_tokens += tokens

                    print(f"    📊 Cost: ${cost:.6f}, Tokens: {tokens:,}, Latency: {cost_data.get('latency_seconds', 0):.2f}s")

                profiles.append({
                    'opportunity_id': f'test_opp_{i+1}',
                    'app_name': profile.get('app_name', 'Unknown'),
                    'final_score': test_opp['score'],
                    'cost_tracking': cost_data,
                    'profile_data': profile
                })

            except Exception as e:
                error_msg = f"Failed to generate profile {i+1}: {e}"
                test_results['errors'].append(error_msg)
                print(f"    ❌ {error_msg}")
                continue

        test_results['profiles_generated'] = len(profiles)
        test_results['total_cost_usd'] = total_cost
        test_results['total_tokens'] = total_tokens
        test_results['profiles'] = profiles
        test_results['success'] = len(profiles) > 0

        print(f"\n  📈 LLM Profiler Results:")
        print(f"    - Profiles generated: {len(profiles)}")
        print(f"    - Total cost: ${total_cost:.6f}")
        print(f"    - Total tokens: {total_tokens:,}")
        print(f"    - Avg cost per profile: ${total_cost/len(profiles):.6f}" if profiles else "    - No profiles generated")

    except Exception as e:
        error_msg = f"LLM profiler test failed: {e}"
        test_results['errors'].append(error_msg)
        print(f"  ❌ {error_msg}")

    return test_results


def test_dlt_cost_tracking(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Test DLT cost tracking integration.

    Args:
        profiles: List of profiles with cost tracking data

    Returns:
        DLT test results
    """
    print("\n🔄 Testing DLT Cost Tracking Integration...")

    test_results = {
        'success': False,
        'profiles_processed': 0,
        'dlt_load_success': False,
        'validation_passed': False,
        'load_info': {},
        'errors': []
    }

    if not profiles:
        test_results['errors'].append("No profiles to test with DLT")
        return test_results

    try:
        # Validate cost data before DLT loading
        print("  🔍 Validating cost data...")
        validation = validate_cost_data(profiles)

        print(f"    ✓ Total opportunities: {validation['total_opportunities']}")
        print(f"    ✓ With cost data: {validation['with_cost_data']}")
        print(f"    ✓ Total cost: ${validation['total_cost_usd']:.6f}")
        print(f"    ✓ Total tokens: {validation['total_tokens']:,}")

        if validation['invalid_cost_data'] > 0:
            print(f"    ⚠️  Invalid cost data: {validation['invalid_cost_data']}")
            for error in validation['errors'][:3]:
                print(f"      - {error}")

        test_results['validation_passed'] = len(validation['errors']) == 0

        # Test DLT loading with cost tracking
        print("  📤 Testing DLT load with cost tracking...")

        # Prepare opportunities for DLT (add required fields)
        dlt_opportunities = []
        for i, profile in enumerate(profiles):
            dlt_opp = {
                'opportunity_id': profile['opportunity_id'],
                'app_name': profile['app_name'],
                'function_count': len(profile['profile_data'].get('core_functions', [])),
                'function_list': profile['profile_data'].get('core_functions', []),
                'original_score': profile['final_score'],
                'final_score': profile['final_score'],
                'status': 'scored',
                'constraint_applied': True,
                'ai_insight': f"Test profile for cost tracking validation",
                'cost_tracking': profile['cost_tracking']
            }
            dlt_opportunities.append(dlt_opp)

        # Load via DLT (without actually running the full pipeline to avoid test data pollution)
        from core.dlt_cost_tracking import workflow_results_with_cost_tracking

        # Test the resource function
        enhanced_opportunities = list(workflow_results_with_cost_tracking(dlt_opportunities))

        if enhanced_opportunities:
            print(f"    ✓ DLT resource processed {len(enhanced_opportunities)} opportunities")

            # Verify cost tracking fields are mapped correctly
            cost_mapping_correct = True
            for opp in enhanced_opportunities:
                if not opp.get('cost_tracking_enabled'):
                    cost_mapping_correct = False
                    break

            if cost_mapping_correct:
                print("    ✓ Cost tracking fields mapped correctly")
                test_results['profiles_processed'] = len(enhanced_opportunities)
                test_results['dlt_load_success'] = True
            else:
                test_results['errors'].append("Cost tracking field mapping failed")
        else:
            test_results['errors'].append("DLT resource returned no data")

        test_results['success'] = (
            test_results['validation_passed'] and
            test_results['dlt_load_success'] and
            len(test_results['errors']) == 0
        )

    except Exception as e:
        error_msg = f"DLT cost tracking test failed: {e}"
        test_results['errors'].append(error_msg)
        print(f"    ❌ {error_msg}")

    return test_results


def test_error_handling(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Test error handling for cost tracking.

    Args:
        profiles: List of profiles to test with

    Returns:
        Error handling test results
    """
    print("\n🛡️  Testing Cost Tracking Error Handling...")

    test_results = {
        'success': False,
        'validation_errors_handled': False,
        'corruption_errors_handled': False,
        'threshold_errors_handled': False,
        'recovery_successful': False,
        'errors': []
    }

    try:
        # Test 1: Validation error handling
        print("  🔍 Testing validation error handling...")

        # Create invalid cost data
        invalid_profile = profiles[0].copy() if profiles else {}
        invalid_profile['cost_tracking'] = {
            'total_cost_usd': -0.001,  # Negative cost
            'total_tokens': -100,      # Negative tokens
            'model_used': 'test-model'
        }

        validation_success, recovered_opps, validation_summary = validate_and_handle_costs(
            [invalid_profile], max_cost_usd=1.0
        )

        if validation_success and recovered_opps:
            print("    ✓ Validation errors handled successfully")
            test_results['validation_errors_handled'] = True
        else:
            test_results['errors'].append("Validation error handling failed")

        # Test 2: Cost threshold handling
        print("  💰 Testing cost threshold handling...")

        # Create expensive profile
        expensive_profile = profiles[0].copy() if profiles else {}
        expensive_profile['cost_tracking'] = {
            'total_cost_usd': 100.0,  # Very expensive
            'total_tokens': 100000,
            'model_used': 'expensive-model'
        }

        threshold_success, recovered_opps, threshold_summary = validate_and_handle_costs(
            [expensive_profile], max_cost_usd=0.01  # Low threshold
        )

        if threshold_success:
            print("    ✓ Cost threshold errors handled successfully")
            test_results['threshold_errors_handled'] = True
        else:
            test_results['errors'].append("Cost threshold handling failed")

        # Test 3: Mixed quality data
        print("  🔄 Testing mixed quality data handling...")

        mixed_profiles = []
        if profiles:
            # Add some valid profiles
            mixed_profiles.extend(profiles[:2])

            # Add invalid profiles
            mixed_profiles.append(invalid_profile)
            mixed_profiles.append(expensive_profile)

        mixed_success, recovered_mixed, mixed_summary = validate_and_handle_costs(
            mixed_profiles, max_cost_usd=1.0
        )

        if mixed_success and recovered_mixed:
            print(f"    ✓ Mixed quality data handled: {len(recovered_mixed)} recovered from {len(mixed_profiles)}")
            test_results['recovery_successful'] = True
        else:
            test_results['errors'].append("Mixed quality data handling failed")

        # Test 4: Data corruption handling
        print("  🔧 Testing data corruption handling...")

        corrupted_profile = profiles[0].copy() if profiles else {}
        corrupted_profile['cost_tracking'] = {
            'model_used': None,  # Missing model
            'total_tokens': 'not-a-number',  # Invalid type
            'total_cost_usd': float('inf'),  # Invalid value
            'timestamp': 'not-a-date'  # Invalid timestamp
        }

        corruption_success, recovered_corrupted, corruption_summary = validate_and_handle_costs(
            [corrupted_profile], max_cost_usd=1.0
        )

        if corruption_success:
            print("    ✓ Data corruption handled successfully")
            test_results['corruption_errors_handled'] = True
        else:
            test_results['errors'].append("Data corruption handling failed")

        test_results['success'] = (
            test_results['validation_errors_handled'] and
            test_results['threshold_errors_handled'] and
            test_results['recovery_successful'] and
            test_results['corruption_errors_handled']
        )

    except Exception as e:
        error_msg = f"Error handling test failed: {e}"
        test_results['errors'].append(error_msg)
        print(f"    ❌ {error_msg}")

    return test_results


def test_cost_reporting(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Test cost reporting functionality.

    Args:
        profiles: List of profiles with cost data

    Returns:
        Cost reporting test results
    """
    print("\n📊 Testing Cost Reporting...")

    test_results = {
        'success': False,
        'report_generated': False,
        'report_accuracy': False,
        'model_breakdown_correct': False,
        'errors': []
    }

    if not profiles:
        test_results['errors'].append("No profiles for cost reporting test")
        return test_results

    try:
        # Generate cost report
        print("  📈 Generating cost report...")
        report = generate_cost_report(profiles, "Pipeline Test Report")

        if report:
            test_results['report_generated'] = True
            print(f"    ✓ Report generated: {report['title']}")

            # Validate report accuracy
            expected_total_cost = sum(p.get('cost_tracking', {}).get('total_cost_usd', 0) for p in profiles)
            expected_total_tokens = sum(p.get('cost_tracking', {}).get('total_tokens', 0) for p in profiles)

            actual_total_cost = report['summary']['total_cost_usd']
            actual_total_tokens = report['summary']['total_tokens']

            cost_match = abs(actual_total_cost - expected_total_cost) < 0.000001
            token_match = actual_total_tokens == expected_total_tokens

            if cost_match and token_match:
                print("    ✓ Report cost/token totals are accurate")
                test_results['report_accuracy'] = True
            else:
                test_results['errors'].append(
                    f"Report accuracy mismatch: expected ${expected_total_cost:.6f}, got ${actual_total_cost:.6f}"
                )

            # Validate model breakdown
            if 'model_breakdown' in report and report['model_breakdown']:
                models_in_report = set(report['model_breakdown'].keys())
                models_in_data = set(p.get('cost_tracking', {}).get('model_used', 'unknown') for p in profiles)

                if models_in_report == models_in_data:
                    print("    ✓ Model breakdown is correct")
                    test_results['model_breakdown_correct'] = True
                else:
                    test_results['errors'].append("Model breakdown mismatch")

            # Print report summary
            print(f"\n  📋 Report Summary:")
            print(f"    - Total opportunities: {report['summary']['total_opportunities']}")
            print(f"    - Cost tracking coverage: {report['summary']['cost_tracking_coverage']:.1f}%")
            print(f"    - Total cost: ${report['summary']['total_cost_usd']:.6f}")
            print(f"    - Avg cost per profile: ${report['summary']['avg_cost_per_profile']:.6f}")

            if report['model_breakdown']:
                print(f"    - Models used: {len(report['model_breakdown'])}")
                for model, stats in report['model_breakdown'].items():
                    print(f"      * {model}: {stats['count']} profiles, ${stats['cost']:.6f}")

        test_results['success'] = (
            test_results['report_generated'] and
            test_results['report_accuracy'] and
            test_results['model_breakdown_correct'] and
            len(test_results['errors']) == 0
        )

    except Exception as e:
        error_msg = f"Cost reporting test failed: {e}"
        test_results['errors'].append(error_msg)
        print(f"    ❌ {error_msg}")

    return test_results


def test_database_integration() -> Dict[str, Any]:
    """
    Test database integration for cost tracking.

    Returns:
        Database integration test results
    """
    print("\n🗄️  Testing Database Integration...")

    test_results = {
        'success': False,
        'connection_successful': False,
        'table_accessible': False,
        'cost_columns_exist': False,
        'can_insert_cost_data': False,
        'can_query_cost_data': False,
        'errors': []
    }

    try:
        # Test database connection
        print("  🔌 Testing database connection...")
        from config.settings import SUPABASE_URL, SUPABASE_KEY
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        test_results['connection_successful'] = True
        print("    ✓ Database connection successful")

        # Test workflow_results table access
        print("  📋 Testing workflow_results table access...")
        try:
            result = supabase.table("workflow_results").select("count", count="exact").execute()
            test_results['table_accessible'] = True
            print(f"    ✓ Table accessible (current count: {result.count or 0})")
        except Exception as e:
            test_results['errors'].append(f"Table access failed: {e}")

        # Test cost tracking columns exist
        print("  🔍 Testing cost tracking columns...")
        try:
            # Try to query cost tracking columns
            result = supabase.table("workflow_results").select(
                "llm_model_used, llm_total_cost_usd, llm_total_tokens, cost_tracking_enabled"
            ).limit(1).execute()

            test_results['cost_columns_exist'] = True
            print("    ✓ Cost tracking columns exist")
        except Exception as e:
            test_results['errors'].append(f"Cost columns check failed: {e}")

        # Test inserting cost data (using test data that will be cleaned up)
        print("  📝 Testing cost data insertion...")
        test_opportunity_id = f"cost_test_{int(time.time())}"

        try:
            test_insert = {
                "opportunity_id": test_opportunity_id,
                "app_name": "CostTestApp",
                "function_count": 2,
                "function_list": ["Test function 1", "Test function 2"],
                "original_score": 75.0,
                "final_score": 80.0,
                "status": "test",
                "constraint_applied": True,
                "ai_insight": "Test cost tracking functionality",
                "llm_model_used": "claude-haiku-4.5",
                "llm_provider": "openrouter",
                "llm_prompt_tokens": 500,
                "llm_completion_tokens": 300,
                "llm_total_tokens": 800,
                "llm_input_cost_usd": 0.0005,
                "llm_output_cost_usd": 0.0015,
                "llm_total_cost_usd": 0.002,
                "llm_latency_seconds": 1.0,
                "llm_timestamp": datetime.utcnow().isoformat(),
                "cost_tracking_enabled": True,
                "llm_pricing_info": {"input": 1.0, "output": 5.0}
            }

            result = supabase.table("workflow_results").insert(test_insert).execute()
            test_results['can_insert_cost_data'] = True
            print("    ✓ Cost data insertion successful")

            # Test querying cost data
            print("  📊 Testing cost data querying...")
            query_result = supabase.table("workflow_results").select(
                "opportunity_id, llm_model_used, llm_total_cost_usd, llm_total_tokens"
            ).eq("opportunity_id", test_opportunity_id).execute()

            if query_result.data:
                test_results['can_query_cost_data'] = True
                queried_data = query_result.data[0]
                print(f"    ✓ Cost data query successful")
                print(f"      - Model: {queried_data.get('llm_model_used')}")
                print(f"      - Cost: ${queried_data.get('llm_total_cost_usd', 0):.6f}")
                print(f"      - Tokens: {queried_data.get('llm_total_tokens', 0)}")

            # Cleanup test data
            supabase.table("workflow_results").delete().eq("opportunity_id", test_opportunity_id).execute()
            print("    ✓ Test data cleaned up")

        except Exception as e:
            test_results['errors'].append(f"Cost data operations failed: {e}")

        test_results['success'] = (
            test_results['connection_successful'] and
            test_results['table_accessible'] and
            test_results['cost_columns_exist'] and
            test_results['can_insert_cost_data'] and
            test_results['can_query_cost_data'] and
            len(test_results['errors']) == 0
        )

    except Exception as e:
        error_msg = f"Database integration test failed: {e}"
        test_results['errors'].append(error_msg)
        print(f"    ❌ {error_msg}")

    return test_results


def main():
    """
    Main execution function for end-to-end cost tracking pipeline test.
    """
    print("=" * 80)
    print("END-TO-END COST TRACKING PIPELINE TEST")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    all_results = {
        'test_summary': {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'start_time': datetime.utcnow().isoformat(),
            'end_time': None
        },
        'llm_profiler_test': {},
        'dlt_integration_test': {},
        'error_handling_test': {},
        'cost_reporting_test': {},
        'database_integration_test': {},
        'overall_success': False
    }

    # Test 1: LLM Profiler Cost Tracking
    print("🧪 TEST 1: LLM Profiler Cost Tracking")
    llm_results = test_llm_profiler_cost_tracking()
    all_results['llm_profiler_test'] = llm_results
    all_results['test_summary']['total_tests'] += 1
    if llm_results['success']:
        all_results['test_summary']['passed_tests'] += 1
    else:
        all_results['test_summary']['failed_tests'] += 1

    # Test 2: DLT Integration
    print("\n🧪 TEST 2: DLT Cost Tracking Integration")
    if llm_results.get('profiles'):
        dlt_results = test_dlt_cost_tracking(llm_results['profiles'])
        all_results['dlt_integration_test'] = dlt_results
        all_results['test_summary']['total_tests'] += 1
        if dlt_results['success']:
            all_results['test_summary']['passed_tests'] += 1
        else:
            all_results['test_summary']['failed_tests'] += 1
    else:
        print("  ⚠️  Skipping DLT test - no profiles available")
        all_results['dlt_integration_test'] = {'success': False, 'skipped': True}

    # Test 3: Error Handling
    print("\n🧪 TEST 3: Cost Tracking Error Handling")
    error_results = test_error_handling(llm_results.get('profiles', []))
    all_results['error_handling_test'] = error_results
    all_results['test_summary']['total_tests'] += 1
    if error_results['success']:
        all_results['test_summary']['passed_tests'] += 1
    else:
        all_results['test_summary']['failed_tests'] += 1

    # Test 4: Cost Reporting
    print("\n🧪 TEST 4: Cost Reporting")
    if llm_results.get('profiles'):
        reporting_results = test_cost_reporting(llm_results['profiles'])
        all_results['cost_reporting_test'] = reporting_results
        all_results['test_summary']['total_tests'] += 1
        if reporting_results['success']:
            all_results['test_summary']['passed_tests'] += 1
        else:
            all_results['test_summary']['failed_tests'] += 1
    else:
        print("  ⚠️  Skipping reporting test - no profiles available")
        all_results['cost_reporting_test'] = {'success': False, 'skipped': True}

    # Test 5: Database Integration
    print("\n🧪 TEST 5: Database Integration")
    db_results = test_database_integration()
    all_results['database_integration_test'] = db_results
    all_results['test_summary']['total_tests'] += 1
    if db_results['success']:
        all_results['test_summary']['passed_tests'] += 1
    else:
        all_results['test_summary']['failed_tests'] += 1

    # Calculate overall success
    all_results['test_summary']['end_time'] = datetime.utcnow().isoformat()
    all_results['overall_success'] = all_results['test_summary']['passed_tests'] >= 4  # At least 4/5 tests pass

    # Final summary
    print("\n" + "=" * 80)
    print("PIPELINE TEST SUMMARY")
    print("=" * 80)

    print(f"\n📊 Test Results:")
    print(f"  Total tests: {all_results['test_summary']['total_tests']}")
    print(f"  Passed: {all_results['test_summary']['passed_tests']}")
    print(f"  Failed: {all_results['test_summary']['failed_tests']}")
    print(f"  Success rate: {(all_results['test_summary']['passed_tests'] / all_results['test_summary']['total_tests']) * 100:.1f}%")

    print(f"\n🧪 Individual Test Results:")
    tests = [
        ("LLM Profiler Cost Tracking", all_results['llm_profiler_test']),
        ("DLT Integration", all_results['dlt_integration_test']),
        ("Error Handling", all_results['error_handling_test']),
        ("Cost Reporting", all_results['cost_reporting_test']),
        ("Database Integration", all_results['database_integration_test'])
    ]

    for test_name, result in tests:
        status = "✅ PASS" if result.get('success') else "❌ FAIL" if not result.get('skipped') else "⏭️  SKIP"
        print(f"  {status} {test_name}")

    if all_results['overall_success']:
        print(f"\n✅ COST TRACKING PIPELINE TEST SUCCESSFUL")
        print(f"\n🎉 Ready for production deployment!")
        print(f"\n💡 Next steps:")
        print(f"  1. Run the database migration: python scripts/database/run_cost_tracking_migration.py")
        print(f"  2. Create analytics views: python scripts/database/create_cost_analysis_views.py")
        print(f"  3. Update production configuration with cost thresholds")
        print(f"  4. Monitor costs using the new analytics views")
    else:
        print(f"\n❌ COST TRACKING PIPELINE TEST FAILED")
        print(f"\n🔧 Issues to resolve:")

        for test_name, result in tests:
            if not result.get('success') and not result.get('skipped'):
                errors = result.get('errors', [])
                if errors:
                    print(f"  {test_name}:")
                    for error in errors[:2]:  # Show first 2 errors
                        print(f"    - {error}")

    print(f"\n📈 Cost Tracking Summary:")
    if llm_results.get('profiles'):
        print(f"  - Profiles generated: {llm_results['profiles_generated']}")
        print(f"  - Total cost incurred: ${llm_results['total_cost_usd']:.6f}")
        print(f"  - Total tokens used: {llm_results['total_tokens']:,}")
        print(f"  - Average cost per profile: ${llm_results['total_cost_usd'] / llm_results['profiles_generated']:.6f}" if llm_results['profiles_generated'] > 0 else "    - No profiles generated")

    print("=" * 80)
    return 0 if all_results['overall_success'] else 1


if __name__ == "__main__":
    sys.exit(main())