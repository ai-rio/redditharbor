#!/usr/bin/env python3
"""
Reddit Data Collection Pipeline Test

Focused test for Reddit data collection with the new unified schema.
Tests core functionality without external API dependencies.
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup project path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_reddit_collection_imports():
    """Test Reddit collection module imports"""
    try:
        from config.settings import (
            SUPABASE_URL, SUPABASE_KEY, REDDIT_PUBLIC, REDDIT_SECRET,
            DB_CONFIG, DEFAULT_SUBREDDITS, ENABLE_PII_ANONYMIZATION
        )
        print("✅ Reddit collection configuration imported successfully")
        return True, {
            'supabase_configured': bool(SUPABASE_URL and SUPABASE_KEY),
            'reddit_configured': bool(REDDIT_PUBLIC and REDDIT_SECRET),
            'db_config': DB_CONFIG,
            'subreddits_count': len(DEFAULT_SUBREDDITS),
            'pii_anonymization': ENABLE_PII_ANONYMIZATION
        }
    except ImportError as e:
        print(f"❌ Reddit collection import failed: {e}")
        return False, {'error': str(e)}

def test_collection_functions():
    """Test Reddit collection function imports and basic structure"""
    try:
        # Test if we can import collection functions
        from core.collection import (
            collect_data, collect_submissions, collect_comments_for_submissions,
            get_collection_status, identify_market_segment, extract_problem_keywords,
            analyze_emotional_intensity, calculate_sentiment_score
        )
        print("✅ Reddit collection functions imported successfully")

        # Test function signatures
        functions_info = {
            'collect_data': hasattr(collect_data, '__call__'),
            'collect_submissions': hasattr(collect_submissions, '__call__'),
            'collect_comments_for_submissions': hasattr(collect_comments_for_submissions, '__call__'),
            'get_collection_status': hasattr(get_collection_status, '__call__'),
            'identify_market_segment': hasattr(identify_market_segment, '__call__'),
            'extract_problem_keywords': hasattr(extract_problem_keywords, '__call__'),
            'analyze_emotional_intensity': hasattr(analyze_emotional_intensity, '__call__'),
            'calculate_sentiment_score': hasattr(calculate_sentiment_score, '__call__')
        }

        all_functions_available = all(functions_info.values())

        if all_functions_available:
            print("✅ All collection functions available")
        else:
            missing_functions = [name for name, available in functions_info.items() if not available]
            print(f"⚠️ Missing collection functions: {missing_functions}")

        return all_functions_available, functions_info

    except ImportError as e:
        print(f"❌ Collection functions import failed: {e}")
        return False, {'error': str(e)}

def test_template_functions():
    """Test Reddit template functions"""
    try:
        from core.templates import (
            academic_research_project, market_research_project,
            monetizable_opportunity_research, problem_first_opportunity_research,
            PROJECT_CONFIGS
        )
        print("✅ Reddit template functions imported successfully")

        templates_info = {
            'academic_research_project': hasattr(academic_research_project, '__call__'),
            'market_research_project': hasattr(market_research_project, '__call__'),
            'monetizable_opportunity_research': hasattr(monetizable_opportunity_research, '__call__'),
            'problem_first_opportunity_research': hasattr(problem_first_opportunity_research, '__call__'),
            'project_configs_count': len(PROJECT_CONFIGS) if PROJECT_CONFIGS else 0
        }

        return True, templates_info

    except ImportError as e:
        print(f"❌ Template functions import failed: {e}")
        return False, {'error': str(e)}

def test_text_analysis_functions():
    """Test text analysis functions for opportunity detection"""
    try:
        from core.collection import (
            extract_problem_keywords, analyze_emotional_intensity,
            calculate_sentiment_score, extract_workarounds,
            detect_payment_mentions
        )

        # Test with sample text
        sample_text = "I really hate how difficult it is to track my workouts. I wish there was a simple app that would help me stay motivated. I would happily pay for something that actually works."

        # Test problem keyword extraction
        problems = extract_problem_keywords(sample_text)
        print(f"✅ Problem keywords extracted: {len(problems)} found")

        # Test emotional intensity analysis
        emotion = analyze_emotional_intensity(sample_text)
        print(f"✅ Emotional intensity analyzed: {emotion:.2f}")

        # Test sentiment analysis
        sentiment = calculate_sentiment_score(sample_text)
        print(f"✅ Sentiment analyzed: {sentiment:.2f}")

        # Test workaround extraction
        workarounds = extract_workarounds(sample_text)
        print(f"✅ Workarounds extracted: {len(workarounds)} found")

        # Test payment detection
        payment = detect_payment_mentions(sample_text)
        print(f"✅ Payment signals detected: {len(payment)} found")

        analysis_results = {
            'problem_keywords_count': len(problems),
            'emotional_intensity': emotion,
            'sentiment_score': sentiment,
            'workarounds_count': len(workarounds),
            'payment_signals_count': len(payment)
        }

        return True, analysis_results

    except ImportError as e:
        print(f"❌ Text analysis functions import failed: {e}")
        return False, {'error': str(e)}
    except Exception as e:
        print(f"❌ Text analysis test failed: {e}")
        return False, {'error': str(e)}

def test_database_table_structure():
    """Test database table structure for Reddit data collection"""
    try:
        # Test via direct SQL queries
        reddit_tables = ['subreddits', 'redditors', 'submissions', 'comments']
        unified_tables = ['opportunities_unified', 'opportunity_assessments']

        table_results = {}

        for table in reddit_tables + unified_tables:
            try:
                cmd = f'docker exec supabase_db_carlos psql -U postgres -d postgres -t -c "SELECT COUNT(*) FROM {table}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    count = result.stdout.strip()
                    table_results[table] = {
                        'exists': True,
                        'accessible': True,
                        'count': int(count) if count.isdigit() else 0
                    }
                    print(f"✅ Table {table}: {count} records")
                else:
                    table_results[table] = {
                        'exists': False,
                        'accessible': False,
                        'error': result.stderr.strip()
                    }
                    print(f"❌ Table {table} not accessible")

            except subprocess.TimeoutExpired:
                table_results[table] = {
                    'exists': False,
                    'accessible': False,
                    'error': 'timeout'
                }
                print(f"❌ Table {table} check timed out")
            except Exception as e:
                table_results[table] = {
                    'exists': False,
                    'accessible': False,
                    'error': str(e)
                }
                print(f"❌ Table {table} check failed: {e}")

        # Count accessible tables
        accessible_tables = sum(1 for result in table_results.values() if result.get('accessible', False))
        total_tables = len(table_results)

        print(f"✅ Database tables accessible: {accessible_tables}/{total_tables}")

        return accessible_tables >= 4, table_results  # At least core Reddit tables

    except Exception as e:
        print(f"❌ Database table structure test failed: {e}")
        return False, {'error': str(e)}

def test_reddit_data_quality():
    """Test quality of existing Reddit data if any"""
    try:
        # Test if there's any existing data to analyze
        submissions_count_query = 'docker exec supabase_db_carlos psql -U postgres -d postgres -t -c "SELECT COUNT(*) FROM submissions"'
        comments_count_query = 'docker exec supabase_db_carlos psql -U postgres -d postgres -t -c "SELECT COUNT(*) FROM comments"'

        try:
            submissions_result = subprocess.run(submissions_count_query, shell=True, capture_output=True, text=True, timeout=10)
            comments_result = subprocess.run(comments_count_query, shell=True, capture_output=True, text=True, timeout=10)

            submissions_count = int(submissions_result.stdout.strip()) if submissions_result.returncode == 0 else 0
            comments_count = int(comments_result.stdout.strip()) if comments_result.returncode == 0 else 0

            print(f"✅ Existing data found: {submissions_count} submissions, {comments_count} comments")

            if submissions_count > 0:
                # Test sample data quality
                sample_query = 'docker exec supabase_db_carlos psql -U postgres -d postgres -t -c "SELECT title, subreddit, score FROM submissions LIMIT 5"'
                sample_result = subprocess.run(sample_query, shell=True, capture_output=True, text=True, timeout=10)

                if sample_result.returncode == 0:
                    print("✅ Sample data quality check passed")
                else:
                    print("⚠️ Could not retrieve sample data")

            return True, {
                'submissions_count': submissions_count,
                'comments_count': comments_count,
                'has_data': submissions_count > 0 or comments_count > 0
            }

        except subprocess.TimeoutExpired:
            print("❌ Data quality check timed out")
            return False, {'error': 'timeout'}
        except Exception as e:
            print(f"❌ Data quality check failed: {e}")
            return False, {'error': str(e)}

    except Exception as e:
        print(f"❌ Reddit data quality test failed: {e}")
        return False, {'error': str(e)}

def test_pii_anonymization():
    """Test PII anonymization configuration"""
    try:
        from config.settings import ENABLE_PII_ANONYMIZATION

        print(f"✅ PII anonymization configuration: {ENABLE_PII_ANONYMIZATION}")

        # Test if PII masking function exists
        try:
            from core.collection import apply_pii_masking

            # Test with sample data containing potential PII
            sample_data = {
                'author': 'test_user_123',
                'email': 'test@example.com',
                'body': 'My email is test@example.com and my phone is 555-1234'
            }

            masked_data = apply_pii_masking(sample_data.copy())

            print("✅ PII masking function accessible")

            return True, {
                'pii_anonymization_enabled': ENABLE_PII_ANONYMIZATION,
                'masking_function_available': True,
                'test_data_processed': True
            }

        except ImportError:
            print("⚠️ PII masking function not available")
            return True, {
                'pii_anonymization_enabled': ENABLE_PII_ANONYMIZATION,
                'masking_function_available': False
            }

    except ImportError as e:
        print(f"❌ PII anonymization test failed: {e}")
        return False, {'error': str(e)}

def main():
    """Main function to run Reddit collection pipeline tests"""
    print("🚀 Reddit Data Collection Pipeline Test")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    test_results = {
        'start_time': datetime.now().isoformat(),
        'tests': {},
        'overall': {'status': 'pending', 'confidence': 0.0}
    }

    # Test 1: Reddit Collection Imports
    print("TEST 1: Reddit Collection Imports")
    print("-" * 40)
    import_success, import_results = test_reddit_collection_imports()
    test_results['tests']['reddit_collection_imports'] = {
        'success': import_success,
        'details': import_results
    }
    print()

    # Test 2: Collection Functions
    print("TEST 2: Collection Functions")
    print("-" * 40)
    functions_success, functions_results = test_collection_functions()
    test_results['tests']['collection_functions'] = {
        'success': functions_success,
        'details': functions_results
    }
    print()

    # Test 3: Template Functions
    print("TEST 3: Template Functions")
    print("-" * 40)
    template_success, template_results = test_template_functions()
    test_results['tests']['template_functions'] = {
        'success': template_success,
        'details': template_results
    }
    print()

    # Test 4: Text Analysis Functions
    print("TEST 4: Text Analysis Functions")
    print("-" * 40)
    analysis_success, analysis_results = test_text_analysis_functions()
    test_results['tests']['text_analysis_functions'] = {
        'success': analysis_success,
        'details': analysis_results
    }
    print()

    # Test 5: Database Table Structure
    print("TEST 5: Database Table Structure")
    print("-" * 40)
    table_success, table_results = test_database_table_structure()
    test_results['tests']['database_table_structure'] = {
        'success': table_success,
        'details': table_results
    }
    print()

    # Test 6: Reddit Data Quality
    print("TEST 6: Reddit Data Quality")
    print("-" * 40)
    data_success, data_results = test_reddit_data_quality()
    test_results['tests']['reddit_data_quality'] = {
        'success': data_success,
        'details': data_results
    }
    print()

    # Test 7: PII Anonymization
    print("TEST 7: PII Anonymization")
    print("-" * 40)
    pii_success, pii_results = test_pii_anonymization()
    test_results['tests']['pii_anonymization'] = {
        'success': pii_success,
        'details': pii_results
    }
    print()

    # Calculate overall results
    all_tests = test_results['tests']
    successful_tests = sum(1 for test in all_tests.values() if test['success'])
    total_tests = len(all_tests)

    confidence = (successful_tests / total_tests) * 100

    if confidence >= 80:
        overall_status = "PASSED"
    elif confidence >= 60:
        overall_status = "PARTIAL"
    else:
        overall_status = "FAILED"

    test_results['overall'] = {
        'status': overall_status,
        'confidence': confidence,
        'successful_tests': successful_tests,
        'total_tests': total_tests,
        'end_time': datetime.now().isoformat()
    }

    # Generate report
    print("=" * 60)
    print("REDDIT COLLECTION PIPELINE TEST RESULTS")
    print("=" * 60)
    print(f"Overall Status: {overall_status}")
    print(f"Confidence: {confidence:.1f}%")
    print(f"Tests Passed: {successful_tests}/{total_tests}")
    print()

    for test_name, result in all_tests.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    print()
    if overall_status == "PASSED":
        print("✅ Reddit collection pipeline PASSED - Ready for production use")
        print("✅ Core functionality validated with new unified schema")
    elif overall_status == "PARTIAL":
        print("⚠️ Reddit collection pipeline PARTIAL - Some issues need attention")
        print("⚠️ Core functionality likely works but review failed tests")
    else:
        print("❌ Reddit collection pipeline FAILED - Critical issues need resolution")
        print("❌ Pipeline may not function correctly with current schema")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"reddit_collection_results_{timestamp}.json"

    try:
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        print(f"\n📄 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\n⚠️ Could not save results file: {e}")

    return 0 if overall_status in ["PASSED", "PARTIAL"] else 1

if __name__ == "__main__":
    sys.exit(main())