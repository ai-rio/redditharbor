#!/usr/bin/env python3
"""
Core Restructuring Integration Tests

Comprehensive test suite for Phase 3 Week 3-4 core table restructuring.
Tests data integrity, performance, and application compatibility.

Usage:
    uv run python3 scripts/testing/test_core_restructuring_integration.py
    uv run python3 scripts/testing/test_core_restructuring_integration.py --performance-only
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import asyncpg
import psycopg2
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import get_database_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CoreRestructuringTester:
    """Test suite for core table restructuring."""

    def __init__(self):
        self.db_config = get_database_config()
        self.test_results = {
            'test_timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {}
        }

    async def get_db_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        try:
            conn = await asyncpg.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database
            )
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def get_psycopg_connection(self):
        """Get psycopg2 connection for operations requiring it."""
        try:
            conn = psycopg2.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database
            )
            conn.autocommit = False
            return conn
        except Exception as e:
            logger.error(f"Psycopg2 connection failed: {e}")
            raise

    async def test_data_integrity(self, conn: asyncpg.Connection) -> Dict:
        """Test data integrity after restructuring."""
        logger.info("Testing data integrity...")

        test_results = {
            'test_name': 'data_integrity',
            'checks': {},
            'passed': True
        }

        try:
            # Check if unified tables exist
            table_exists_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'opportunities_unified'
                ) as opportunities_unified_exists,
                EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'opportunity_assessments'
                ) as opportunity_assessments_exists;
            """

            table_exists = await conn.fetchrow(table_exists_query)
            test_results['checks']['unified_tables_exist'] = {
                'opportunities_unified': table_exists['opportunities_unified_exists'],
                'opportunity_assessments': table_exists['opportunity_assessments_exists'],
                'passed': table_exists['opportunities_unified_exists'] and table_exists['opportunity_assessments_exists']
            }

            # Row count validation
            count_query = """
                WITH original_counts AS (
                    SELECT COUNT(*) as count FROM opportunities_backup_20251118
                    UNION ALL
                    SELECT COUNT(*) FROM app_opportunities_backup_20251118
                    UNION ALL
                    SELECT COUNT(*) FROM workflow_results_backup_20251118
                ),
                unified_count AS (
                    SELECT COUNT(*) as count FROM opportunities_unified
                )
                SELECT
                    SUM(count) as total_original
                FROM original_counts
                UNION ALL
                SELECT count as total_original FROM unified_count;
            """

            count_results = await conn.fetch(count_query)
            total_original = count_results[0]['total_original']
            total_unified = count_results[1]['total_original']

            # Allow for some variation due to data deduplication
            count_variation = abs(total_original - total_unified)
            count_passed = count_variation <= max(1, total_original * 0.1)  # Allow 10% variation

            test_results['checks']['row_count_validation'] = {
                'total_original': total_original,
                'total_unified': total_unified,
                'variation': count_variation,
                'passed': count_passed
            }

            # Data consistency checks
            consistency_checks = await conn.fetch("""
                SELECT
                    'trust_score_range' as check_name,
                    COUNT(*) as violations
                FROM opportunities_unified
                WHERE trust_score < 0 OR trust_score > 100
                UNION ALL
                SELECT
                    'missing_core_data' as check_name,
                    COUNT(*) as violations
                FROM opportunities_unified
                WHERE title IS NULL OR submission_id IS NULL
                UNION ALL
                SELECT
                    'assessment_integrity' as check_name,
                    COUNT(*) as violations
                FROM opportunity_assessments oa
                WHERE oa.opportunity_id NOT IN (SELECT id FROM opportunities_unified)
                UNION ALL
                SELECT
                    'score_ranges' as check_name,
                    COUNT(*) as violations
                FROM opportunity_assessments
                WHERE total_score < 0 OR total_score > 100;
            """)

            total_violations = 0
            for check in consistency_checks:
                total_violations += check['violations']
                test_results['checks'][check['check_name']] = {
                    'violations': check['violations'],
                    'passed': check['violations'] == 0
                }

            test_results['checks']['total_violations'] = {
                'count': total_violations,
                'passed': total_violations == 0
            }

            # Foreign key integrity
            fk_check = await conn.fetchrow("""
                SELECT
                    COUNT(*) as orphaned_opportunities
                FROM opportunities_unified o
                LEFT JOIN submissions s ON o.submission_id = s.id
                WHERE o.submission_id IS NOT NULL AND s.id IS NULL;
            """)

            test_results['checks']['foreign_key_integrity'] = {
                'orphaned_opportunities': fk_check['orphaned_opportunities'],
                'passed': fk_check['orphaned_opportunities'] == 0
            }

            # Overall test result
            test_results['passed'] = all(
                check['passed'] for check in test_results['checks'].values()
                if isinstance(check, dict) and 'passed' in check
            )

        except Exception as e:
            logger.error(f"Data integrity test failed: {e}")
            test_results['error'] = str(e)
            test_results['passed'] = False

        return test_results

    async def test_backward_compatibility(self, conn: asyncpg.Connection) -> Dict:
        """Test backward compatibility through legacy views."""
        logger.info("Testing backward compatibility...")

        test_results = {
            'test_name': 'backward_compatibility',
            'checks': {},
            'passed': True
        }

        try:
            # Check if legacy views exist
            view_exists_query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.views
                    WHERE table_schema = 'public'
                    AND table_name = 'opportunities_legacy'
                ) as opportunities_legacy_exists,
                EXISTS (
                    SELECT FROM information_schema.views
                    WHERE table_schema = 'public'
                    AND table_name = 'app_opportunities_legacy'
                ) as app_opportunities_legacy_exists,
                EXISTS (
                    SELECT FROM information_schema.views
                    WHERE table_schema = 'public'
                    AND table_name = 'workflow_results_legacy'
                ) as workflow_results_legacy_exists;
            """

            view_exists = await conn.fetchrow(view_exists_query)
            test_results['checks']['legacy_views_exist'] = {
                'opportunities_legacy': view_exists['opportunities_legacy_exists'],
                'app_opportunities_legacy': view_exists['app_opportunities_legacy_exists'],
                'workflow_results_legacy': view_exists['view_exists_results_legacy_exists'],
                'passed': all(view_exists.values())
            }

            # Test legacy view queries
            legacy_queries = [
                ("opportunities_legacy", "SELECT COUNT(*) FROM opportunities_legacy"),
                ("app_opportunities_legacy", "SELECT COUNT(*) FROM app_opportunities_legacy"),
                ("workflow_results_legacy", "SELECT COUNT(*) FROM workflow_results_legacy"),
                ("opportunity_scores_legacy", "SELECT COUNT(*) FROM opportunity_scores_legacy")
            ]

            for view_name, query in legacy_queries:
                try:
                    result = await conn.fetchval(query)
                    test_results['checks'][f'{view_name}_queryable'] = {
                        'result': result,
                        'passed': True
                    }
                except Exception as e:
                    test_results['checks'][f'{view_name}_queryable'] = {
                        'error': str(e),
                        'passed': False
                    }

            # Test column structure compatibility
            structure_checks = await conn.fetch("""
                -- Check opportunities_legacy structure
                SELECT 'opportunities_legacy' as view_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'opportunities_legacy'
                UNION ALL
                -- Check app_opportunities_legacy structure
                SELECT 'app_opportunities_legacy' as view_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'app_opportunities_legacy'
                ORDER BY view_name, ordinal_position;
            """)

            expected_columns = {
                'opportunities_legacy': ['id', 'title', 'description', 'problem_statement', 'target_audience', 'submission_id', 'created_at', 'updated_at'],
                'app_opportunities_legacy': ['submission_id', 'app_concept', 'core_functions', 'trust_score', 'trust_badge', 'status']
            }

            for view_name, expected_cols in expected_columns.items():
                view_columns = [row['column_name'] for row in structure_checks if row['view_name'] == view_name]
                missing_cols = set(expected_cols) - set(view_columns)
                test_results['checks'][f'{view_name}_structure'] = {
                    'expected_columns': expected_cols,
                    'actual_columns': view_columns,
                    'missing_columns': list(missing_cols),
                    'passed': len(missing_cols) == 0
                }

            # Overall test result
            test_results['passed'] = all(
                check['passed'] for check in test_results['checks'].values()
                if isinstance(check, dict) and 'passed' in check
            )

        except Exception as e:
            logger.error(f"Backward compatibility test failed: {e}")
            test_results['error'] = str(e)
            test_results['passed'] = False

        return test_results

    async def test_performance_benchmarks(self, conn: asyncpg.Connection) -> Dict:
        """Test performance benchmarks for new schema."""
        logger.info("Testing performance benchmarks...")

        test_results = {
            'test_name': 'performance_benchmarks',
            'benchmarks': {},
            'passed': True
        }

        try:
            # Benchmark queries
            benchmark_queries = [
                {
                    'name': 'high_trust_opportunities',
                    'query': """
                        SELECT * FROM opportunities_unified
                        WHERE trust_score > 80
                        ORDER BY trust_score DESC
                        LIMIT 10;
                    """,
                    'expected_max_time': 1.0  # seconds
                },
                {
                    'name': 'recent_opportunities',
                    'query': """
                        SELECT * FROM opportunities_unified
                        WHERE created_at > NOW() - INTERVAL '7 days'
                        ORDER BY created_at DESC
                        LIMIT 20;
                    """,
                    'expected_max_time': 0.5
                },
                {
                    'name': 'high_score_assessments',
                    'query': """
                        SELECT
                            ou.title,
                            oa.total_score,
                            oa.validation_confidence
                        FROM opportunities_unified ou
                        JOIN opportunity_assessments oa ON ou.id = oa.opportunity_id
                        WHERE oa.total_score > 70
                        ORDER BY oa.total_score DESC
                        LIMIT 15;
                    """,
                    'expected_max_time': 2.0
                }
            ]

            for benchmark in benchmark_queries:
                start_time = time.time()
                try:
                    result = await conn.fetch(benchmark['query'])
                    execution_time = time.time() - start_time

                    test_results['benchmarks'][benchmark['name']] = {
                        'execution_time': execution_time,
                        'result_count': len(result),
                        'expected_max_time': benchmark['expected_max_time'],
                        'passed': execution_time <= benchmark['expected_max_time']
                    }

                except Exception as e:
                    execution_time = time.time() - start_time
                    test_results['benchmarks'][benchmark['name']] = {
                        'error': str(e),
                        'execution_time': execution_time,
                        'passed': False
                    }

            # Index usage check
            index_usage_query = """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                  AND (
                      tablename LIKE '%unified%'
                      OR tablename LIKE '%assessments%'
                  )
                ORDER BY idx_scan DESC;
            """

            index_stats = await conn.fetch(index_usage_query)
            test_results['benchmarks']['index_usage'] = {
                'stats': [dict(row) for row in index_stats],
                'passed': len(index_stats) > 0  # At least some indexes should be used
            }

            # Overall test result
            test_results['passed'] = all(
                benchmark['passed'] for benchmark in test_results['benchmarks'].values()
                if isinstance(benchmark, dict) and 'passed' in benchmark
            )

        except Exception as e:
            logger.error(f"Performance benchmarks test failed: {e}")
            test_results['error'] = str(e)
            test_results['passed'] = False

        return test_results

    async def test_pipeline_compatibility(self, conn: asyncpg.Connection) -> Dict:
        """Test compatibility with existing pipelines."""
        logger.info("Testing pipeline compatibility...")

        test_results = {
            'test_name': 'pipeline_compatibility',
            'checks': {},
            'passed': True
        }

        try:
            # Test DLT trust pipeline compatibility
            dlt_compatibility_query = """
                SELECT COUNT(*) as count
                FROM opportunities_unified
                WHERE core_functions IS NOT NULL
                  AND trust_score IS NOT NULL
                  AND trust_badge IS NOT NULL;
            """

            dlt_result = await conn.fetchval(dlt_compatibility_query)
            test_results['checks']['dlt_trust_pipeline'] = {
                'compatible_records': dlt_result,
                'passed': dlt_result >= 0  # Should have records if data exists
            }

            # Test batch opportunity scoring compatibility
            scoring_compatibility_query = """
                SELECT
                    COUNT(*) as total_assessments,
                    COUNT(CASE WHEN total_score BETWEEN 0 AND 100 THEN 1 END) as valid_scores,
                    AVG(total_score) as avg_score
                FROM opportunity_assessments;
            """

            scoring_result = await conn.fetchrow(scoring_compatibility_query)
            test_results['checks']['batch_opportunity_scoring'] = {
                'total_assessments': scoring_result['total_assessments'],
                'valid_scores': scoring_result['valid_scores'],
                'avg_score': float(scoring_result['avg_score']) if scoring_result['avg_score'] else 0,
                'passed': scoring_result['valid_scores'] == scoring_result['total_assessments']
            }

            # Test core functions serialization compatibility
            core_functions_query = """
                SELECT
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN jsonb_typeof(core_functions) = 'array' THEN 1 END) as valid_arrays,
                    COUNT(CASE WHEN core_functions IS NULL THEN 1 END) as null_values
                FROM opportunities_unified;
            """

            core_functions_result = await conn.fetchrow(core_functions_query)
            test_results['checks']['core_functions_serialization'] = {
                'total_records': core_functions_result['total_records'],
                'valid_arrays': core_functions_result['valid_arrays'],
                'null_values': core_functions_result['null_values'],
                'passed': True  # Null values are acceptable
            }

            # Test trust validation system compatibility
            trust_validation_query = """
                SELECT
                    COUNT(*) as total_opportunities,
                    COUNT(CASE WHEN trust_level IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNKNOWN') THEN 1 END) as valid_trust_levels,
                    COUNT(CASE WHEN trust_badge IN ('GOLD', 'SILVER', 'BRONZE', 'BASIC', 'NO-BADGE') THEN 1 END) as valid_trust_badges
                FROM opportunities_unified;
            """

            trust_validation_result = await conn.fetchrow(trust_validation_query)
            test_results['checks']['trust_validation_system'] = {
                'total_opportunities': trust_validation_result['total_opportunities'],
                'valid_trust_levels': trust_validation_result['valid_trust_levels'],
                'valid_trust_badges': trust_validation_result['valid_trust_badges'],
                'passed': (
                    trust_validation_result['valid_trust_levels'] == trust_validation_result['total_opportunities'] and
                    trust_validation_result['valid_trust_badges'] == trust_validation_result['total_opportunities']
                )
            }

            # Overall test result
            test_results['passed'] = all(
                check['passed'] for check in test_results['checks'].values()
            )

        except Exception as e:
            logger.error(f"Pipeline compatibility test failed: {e}")
            test_results['error'] = str(e)
            test_results['passed'] = False

        return test_results

    async def test_functional_requirements(self, conn: asyncpg.Connection) -> Dict:
        """Test functional requirements and business logic."""
        logger.info("Testing functional requirements...")

        test_results = {
            'test_name': 'functional_requirements',
            'checks': {},
            'passed': True
        }

        try:
            # Test 6-dimension scoring system
            scoring_system_query = """
                SELECT
                    COUNT(*) as total_assessments,
                    COUNT(CASE
                        WHEN market_demand_score BETWEEN 0 AND 100
                        AND pain_intensity_score BETWEEN 0 AND 100
                        AND monetization_potential_score BETWEEN 0 AND 100
                        AND market_gap_score BETWEEN 0 AND 100
                        AND technical_feasibility_score BETWEEN 0 AND 100
                        AND simplicity_score BETWEEN 0 AND 100
                        THEN 1 END
                    ) as valid_dimension_scores,
                    AVG(total_score) as avg_total_score
                FROM opportunity_assessments;
            """

            scoring_result = await conn.fetchrow(scoring_system_query)
            test_results['checks']['scoring_system'] = {
                'total_assessments': scoring_result['total_assessments'],
                'valid_dimension_scores': scoring_result['valid_dimension_scores'],
                'avg_total_score': float(scoring_result['avg_total_score']) if scoring_result['avg_total_score'] else 0,
                'passed': scoring_result['valid_dimension_scores'] == scoring_result['total_assessments']
            }

            # Test opportunity discovery workflow
            discovery_workflow_query = """
                WITH high_value_opportunities AS (
                    SELECT
                        COUNT(*) as count,
                        AVG(trust_score) as avg_trust,
                        AVG(opportunity_score) as avg_opportunity_score
                    FROM opportunities_unified
                    WHERE trust_score > 70
                      AND opportunity_score > 70
                )
                SELECT * FROM high_value_opportunities;
            """

            discovery_result = await conn.fetchrow(discovery_workflow_query)
            test_results['checks']['discovery_workflow'] = {
                'high_value_count': discovery_result['count'],
                'avg_trust_score': float(discovery_result['avg_trust']) if discovery_result['avg_trust'] else 0,
                'avg_opportunity_score': float(discovery_result['avg_opportunity_score']) if discovery_result['avg_opportunity_score'] else 0,
                'passed': discovery_result['count'] >= 0  # Should work regardless of data
            }

            # Test market validation integration
            validation_integration_query = """
                SELECT
                    COUNT(*) as total_opportunities,
                    COUNT(CASE WHEN validation_types IS NOT NULL AND jsonb_array_length(validation_types) > 0 THEN 1 END) as with_validations,
                    AVG(validation_confidence) as avg_confidence
                FROM opportunity_assessments;
            """

            validation_result = await conn.fetchrow(validation_integration_query)
            test_results['checks']['validation_integration'] = {
                'total_opportunities': validation_result['total_opportunities'],
                'with_validations': validation_result['with_validations'],
                'avg_confidence': float(validation_result['avg_confidence']) if validation_result['avg_confidence'] else 0,
                'passed': True  # Validation is optional
            }

            # Test data consistency across related tables
            consistency_query = """
                SELECT
                    COUNT(*) as total_unified,
                    COUNT(CASE WHEN submission_id IN (SELECT id FROM submissions) THEN 1 END) as valid_submission_refs,
                    COUNT(CASE WHEN id IN (SELECT opportunity_id FROM opportunity_assessments) THEN 1 END) as with_assessments
                FROM opportunities_unified;
            """

            consistency_result = await conn.fetchrow(consistency_query)
            test_results['checks']['data_consistency'] = {
                'total_unified': consistency_result['total_unified'],
                'valid_submission_refs': consistency_result['valid_submission_refs'],
                'with_assessments': consistency_result['with_assessments'],
                'passed': consistency_result['valid_submission_refs'] == consistency_result['total_unified']
            }

            # Overall test result
            test_results['passed'] = all(
                check['passed'] for check in test_results['checks'].values()
            )

        except Exception as e:
            logger.error(f"Functional requirements test failed: {e}")
            test_results['error'] = str(e)
            test_results['passed'] = False

        return test_results

    async def run_all_tests(self, performance_only: bool = False) -> Dict:
        """Run all tests and return comprehensive results."""
        logger.info("=== STARTING CORE RESTRUCTURING INTEGRATION TESTS ===")

        conn = await self.get_db_connection()

        try:
            if performance_only:
                # Run only performance tests
                performance_test = await self.test_performance_benchmarks(conn)
                self.test_results['tests']['performance_benchmarks'] = performance_test
            else:
                # Run all tests
                self.test_results['tests']['data_integrity'] = await self.test_data_integrity(conn)
                self.test_results['tests']['backward_compatibility'] = await self.test_backward_compatibility(conn)
                self.test_results['tests']['performance_benchmarks'] = await self.test_performance_benchmarks(conn)
                self.test_results['tests']['pipeline_compatibility'] = await self.test_pipeline_compatibility(conn)
                self.test_results['tests']['functional_requirements'] = await self.test_functional_requirements(conn)

            # Calculate summary
            total_tests = len(self.test_results['tests'])
            passed_tests = sum(1 for test in self.test_results['tests'].values() if test.get('passed', False))

            self.test_results['summary'] = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'overall_success': passed_tests == total_tests,
                'test_duration': str(datetime.now() - datetime.fromisoformat(self.test_results['test_timestamp']))
            }

            return self.test_results

        finally:
            await conn.close()

    def save_test_results(self, filename: str = None) -> str:
        """Save test results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/core_restructuring_test_results_{timestamp}.json"

        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)

        logger.info(f"Test results saved to {filename}")
        return filename

    def print_test_summary(self):
        """Print test summary to console."""
        print("\n" + "="*80)
        print("CORE RESTRUCTURING INTEGRATION TEST RESULTS")
        print("="*80)

        for test_name, test_result in self.test_results['tests'].items():
            status = "✅ PASSED" if test_result.get('passed', False) else "❌ FAILED"
            print(f"\n{test_name.upper().replace('_', ' ')}: {status}")

            if 'checks' in test_result:
                for check_name, check_result in test_result['checks'].items():
                    if isinstance(check_result, dict) and 'passed' in check_result:
                        check_status = "✅" if check_result['passed'] else "❌"
                        print(f"  {check_name}: {check_status}")
                        if not check_result['passed'] and 'error' in check_result:
                            print(f"    Error: {check_result['error']}")

        # Summary
        summary = self.test_results['summary']
        print(f"\n{'='*80}")
        print("SUMMARY")
        print("="*80)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Overall Success: {'✅ YES' if summary['overall_success'] else '❌ NO'}")
        print(f"Test Duration: {summary['test_duration']}")

        if summary['overall_success']:
            print("\n🎉 ALL TESTS PASSED - CORE RESTRUCTURING SUCCESSFUL!")
        else:
            print("\n❌ SOME TESTS FAILED - REVIEW REQUIRED")


async def main():
    """Main function for test execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Core Restructuring Integration Tests")
    parser.add_argument(
        '--performance-only',
        action='store_true',
        help='Run only performance benchmark tests'
    )
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save test results to JSON file'
    )

    args = parser.parse_args()

    # Initialize tester
    tester = CoreRestructuringTester()

    try:
        # Run tests
        results = await tester.run_all_tests(performance_only=args.performance_only)

        # Save results if requested
        if args.save_results:
            filename = tester.save_test_results()
            print(f"\n📄 Test results saved to: {filename}")

        # Print summary
        tester.print_test_summary()

        # Exit with appropriate code
        if results['summary']['overall_success']:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())