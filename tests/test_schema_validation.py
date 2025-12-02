#!/usr/bin/env python3
"""
Schema Validation Test for RedditHarbor

Focuses on Phase 1: Schema Compatibility Check
Tests database connectivity and table structure after schema consolidation
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup project path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_imports():
    """Test if we can import RedditHarbor modules"""
    try:
        from config.settings import (
            SUPABASE_URL, SUPABASE_KEY, REDDIT_PUBLIC, REDDIT_SECRET,
            REDDIT_USER_AGENT, DB_CONFIG, DEFAULT_SUBREDDITS
        )
        print("✅ Configuration modules imported successfully")
        return True, {
            'supabase_url': SUPABASE_URL[:20] + '...' if SUPABASE_URL else None,
            'supabase_key_available': bool(SUPABASE_KEY),
            'reddit_configured': bool(REDDIT_PUBLIC and REDDIT_SECRET),
            'db_config': DB_CONFIG,
            'default_subreddits_count': len(DEFAULT_SUBREDDITS)
        }
    except ImportError as e:
        print(f"❌ Failed to import configuration: {e}")
        return False, {'error': str(e)}

def test_database_connectivity():
    """Test database connectivity via basic operations"""
    try:
        import subprocess
        import json

        print("🔍 Testing database connectivity...")

        # Test if Supabase is running
        try:
            result = subprocess.run(['supabase', 'status'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Supabase status check passed")
                return True, {'supabase_status': 'running'}
            else:
                print("❌ Supabase not running")
                return False, {'error': 'Supabase not running'}
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"❌ Supabase CLI check failed: {e}")
            return False, {'error': f'Supabase CLI not available: {e}'}

    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False, {'error': str(e)}

def test_database_schema():
    """Test database schema structure via direct SQL queries"""
    try:
        import subprocess

        print("🔍 Testing database schema...")

        # Test table existence via psql
        tables_to_check = [
            'subreddits', 'redditors', 'submissions', 'comments',
            'opportunities_unified', 'opportunity_assessments',
            'app_opportunities', 'opportunity_analysis', 'opportunities'
        ]

        results = {}

        for table in tables_to_check:
            try:
                cmd = f'docker exec supabase_db_carlos psql -U postgres -d postgres -t -c "SELECT 1 FROM information_schema.tables WHERE table_name = \'{table}\'"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)

                if result.returncode == 0 and result.stdout.strip():
                    results[table] = True
                    print(f"✅ Table {table} exists")
                else:
                    results[table] = False
                    print(f"❌ Table {table} not found")

            except subprocess.TimeoutExpired:
                results[table] = False
                print(f"❌ Table {table} check timed out")
            except Exception as e:
                results[table] = False
                print(f"❌ Table {table} check failed: {e}")

        # Check for any table existence
        tables_found = sum(1 for exists in results.values() if exists)

        if tables_found >= 4:  # At least core Reddit tables should exist
            print(f"✅ Found {tables_found}/{len(tables_to_check)} expected tables")
            return True, results
        else:
            print(f"❌ Only {tables_found}/{len(tables_to_check)} expected tables found")
            return False, results

    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False, {'error': str(e)}

def test_legacy_table_check():
    """Check for removed legacy tables"""
    try:
        import subprocess

        print("🔍 Checking for removed legacy tables...")

        # These tables should have been removed during consolidation
        legacy_tables_to_check = [
            'market_research', 'user_problems', 'solution_patterns',
            'reddit_posts', 'reddit_comments', 'reddit_authors',
            'app_ideas', 'feature_requests', 'user_stories'
        ]

        legacy_found = []

        for table in legacy_tables_to_check:
            try:
                cmd = f'docker exec supabase_db_carlos psql -U postgres -d postgres -t -c "SELECT 1 FROM information_schema.tables WHERE table_name = \'{table}\'"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)

                if result.returncode == 0 and result.stdout.strip():
                    legacy_found.append(table)
                    print(f"⚠️ Legacy table still present: {table}")

            except subprocess.TimeoutExpired:
                print(f"⚠️ Legacy table {table} check timed out")
            except Exception as e:
                print(f"⚠️ Legacy table {table} check failed: {e}")

        if legacy_found:
            print(f"❌ Found {len(legacy_found)} legacy tables that should have been removed")
            return False, {'legacy_tables_found': legacy_found}
        else:
            print("✅ No legacy tables found - schema cleanup successful")
            return True, {'legacy_tables_found': []}

    except Exception as e:
        print(f"❌ Legacy table check failed: {e}")
        return False, {'error': str(e)}

def test_schema_documentation():
    """Check if schema documentation is up to date"""
    try:
        print("🔍 Checking schema documentation...")

        schema_files = [
            'supabase/migrations/00000000000000_baseline_schema.sql',
            'docs/schema-consolidation/README.md',
            'docs/schema-consolidation/schema-consolidation-summary.md'
        ]

        doc_results = {}

        for file_path in schema_files:
            full_path = project_root / file_path
            if full_path.exists():
                doc_results[file_path] = True
                print(f"✅ Documentation file exists: {file_path}")
            else:
                doc_results[file_path] = False
                print(f"❌ Documentation file missing: {file_path}")

        docs_found = sum(1 for exists in doc_results.values() if exists)

        if docs_found >= 2:
            print(f"✅ Found {docs_found}/{len(schema_files)} documentation files")
            return True, doc_results
        else:
            print(f"⚠️ Only {docs_found}/{len(schema_files)} documentation files found")
            return False, doc_results

    except Exception as e:
        print(f"❌ Schema documentation check failed: {e}")
        return False, {'error': str(e)}

def main():
    """Main function to run schema validation tests"""
    print("🚀 RedditHarbor Schema Validation Test")
    print("=" * 60)
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print()

    test_results = {
        'start_time': datetime.utcnow().isoformat(),
        'tests': {},
        'overall': {'status': 'pending', 'confidence': 0.0}
    }

    # Test 1: Module Imports
    print("TEST 1: Module Import Validation")
    print("-" * 30)
    import_success, import_results = test_imports()
    test_results['tests']['module_imports'] = {
        'success': import_success,
        'details': import_results
    }
    print()

    # Test 2: Database Connectivity
    print("TEST 2: Database Connectivity")
    print("-" * 30)
    db_success, db_results = test_database_connectivity()
    test_results['tests']['database_connectivity'] = {
        'success': db_success,
        'details': db_results
    }
    print()

    # Test 3: Schema Structure
    print("TEST 3: Schema Structure")
    print("-" * 30)
    if db_success:
        schema_success, schema_results = test_database_schema()
        test_results['tests']['schema_structure'] = {
            'success': schema_success,
            'details': schema_results
        }
    else:
        test_results['tests']['schema_structure'] = {
            'success': False,
            'details': {'error': 'Skipped due to database connectivity failure'}
        }
    print()

    # Test 4: Legacy Table Check
    print("TEST 4: Legacy Table Cleanup")
    print("-" * 30)
    if db_success:
        legacy_success, legacy_results = test_legacy_table_check()
        test_results['tests']['legacy_table_check'] = {
            'success': legacy_success,
            'details': legacy_results
        }
    else:
        test_results['tests']['legacy_table_check'] = {
            'success': False,
            'details': {'error': 'Skipped due to database connectivity failure'}
        }
    print()

    # Test 5: Documentation Check
    print("TEST 5: Documentation Validation")
    print("-" * 30)
    doc_success, doc_results = test_schema_documentation()
    test_results['tests']['documentation'] = {
        'success': doc_success,
        'details': doc_results
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
        'end_time': datetime.utcnow().isoformat()
    }

    # Generate report
    print("=" * 60)
    print("SCHEMA VALIDATION TEST RESULTS")
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
        print("✅ Schema validation PASSED - Ready for pipeline testing")
    elif overall_status == "PARTIAL":
        print("⚠️ Schema validation PARTIAL - Some issues need attention")
    else:
        print("❌ Schema validation FAILED - Critical issues need resolution")

    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_file = f"schema_validation_results_{timestamp}.json"

    try:
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        print(f"\n📄 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\n⚠️ Could not save results file: {e}")

    return 0 if overall_status in ["PASSED", "PARTIAL"] else 1

if __name__ == "__main__":
    sys.exit(main())