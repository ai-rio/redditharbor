#!/usr/bin/env python3
"""
UUID Format Fixes Validation Script

This script validates the UUID format fixes and deduplication schema integration
after deployment to ensure data integrity and proper foreign key relationships.

Usage:
    python scripts/testing/validate_uuid_migration.py [--fix-issues] [--dry-run]
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import asyncpg
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import get_database_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/uuid_migration_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UUIDMigrationValidator:
    """Validates UUID format fixes and deduplication schema integration."""

    def __init__(self, fix_issues: bool = False, dry_run: bool = False):
        self.fix_issues = fix_issues
        self.dry_run = dry_run
        self.db_config = get_database_config()
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'summary': {},
            'recommendations': []
        }

        # Ensure log directory exists
        Path("logs").mkdir(exist_ok=True)

        logger.info(f"UUID Migration Validator initialized - Fix issues: {fix_issues}, Dry run: {dry_run}")

    async def get_async_connection(self) -> asyncpg.Connection:
        """Get asyncpg connection for async operations."""
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
            logger.error(f"Async connection failed: {e}")
            raise

    def get_sync_connection(self):
        """Get psycopg2 connection for sync operations."""
        try:
            conn = psycopg2.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database
            )
            return conn
        except Exception as e:
            logger.error(f"Sync connection failed: {e}")
            raise

    async def check_uuid_foreign_key_consistency(self, conn: asyncpg.Connection) -> Dict:
        """Check UUID foreign key consistency across tables."""
        logger.info("Checking UUID foreign key consistency...")

        checks = {}

        # Check app_opportunities UUID consistency
        app_opp_query = """
            SELECT
                COUNT(*) as total_records,
                COUNT(CASE WHEN submission_uuid IS NULL AND submission_id IS NOT NULL THEN 1 END) as missing_uuid,
                COUNT(CASE WHEN submission_uuid IS NOT NULL THEN 1 END) as has_uuid,
                COUNT(CASE WHEN submission_uuid IS NOT NULL AND
                    NOT EXISTS (SELECT 1 FROM submissions s WHERE s.id = submission_uuid) THEN 1 END) as orphaned_uuid
            FROM app_opportunities
        """

        result = await conn.fetchrow(app_opp_query)
        checks['app_opportunities'] = dict(result)

        # Check llm_monetization_analysis UUID consistency
        llm_query = """
            SELECT
                COUNT(*) as total_records,
                COUNT(CASE WHEN submission_uuid IS NULL AND submission_id IS NOT NULL THEN 1 END) as missing_uuid,
                COUNT(CASE WHEN submission_uuid IS NOT NULL THEN 1 END) as has_uuid,
                COUNT(CASE WHEN submission_uuid IS NOT NULL AND
                    NOT EXISTS (SELECT 1 FROM submissions s WHERE s.id = submission_uuid) THEN 1 END) as orphaned_uuid
            FROM llm_monetization_analysis
        """

        result = await conn.fetchrow(llm_query)
        checks['llm_monetization_analysis'] = dict(result)

        # Check workflow_results UUID consistency
        workflow_query = """
            SELECT
                COUNT(*) as total_records,
                COUNT(CASE WHEN submission_uuid IS NULL AND opportunity_id IS NOT NULL THEN 1 END) as missing_uuid,
                COUNT(CASE WHEN submission_uuid IS NOT NULL THEN 1 END) as has_uuid,
                COUNT(CASE WHEN submission_uuid IS NOT NULL AND
                    NOT EXISTS (SELECT 1 FROM submissions s WHERE s.id = submission_uuid) THEN 1 END) as orphaned_uuid
            FROM workflow_results
        """

        result = await conn.fetchrow(workflow_query)
        checks['workflow_results'] = dict(result)

        return checks

    async def check_deduplication_schema_integration(self, conn: asyncpg.Connection) -> Dict:
        """Check deduplication schema integration."""
        logger.info("Checking deduplication schema integration...")

        checks = {}

        # Check opportunities_unified table structure
        structure_query = """
            SELECT
                COUNT(*) as total_records,
                COUNT(CASE WHEN submission_id IS NOT NULL THEN 1 END) as has_submission_link,
                COUNT(CASE WHEN business_concept_id IS NOT NULL THEN 1 END) as has_business_concept,
                COUNT(CASE WHEN semantic_fingerprint IS NOT NULL AND semantic_fingerprint != '' THEN 1 END) as has_fingerprint,
                COUNT(CASE WHEN copied_from_primary THEN 1 END) as copied_records
            FROM opportunities_unified
        """

        result = await conn.fetchrow(structure_query)
        checks['opportunities_unified_structure'] = dict(result)

        # Check foreign key relationships
        fk_query = """
            SELECT
                COUNT(*) as total_opportunities,
                COUNT(CASE WHEN s.id IS NULL THEN 1 END) as orphaned_opportunities,
                COUNT(CASE WHEN bc.id IS NULL AND ou.business_concept_id IS NOT NULL THEN 1 END) as orphaned_business_concepts
            FROM opportunities_unified ou
            LEFT JOIN submissions s ON ou.submission_id = s.id
            LEFT JOIN business_concepts bc ON ou.business_concept_id = bc.id
        """

        result = await conn.fetchrow(fk_query)
        checks['foreign_key_relationships'] = dict(result)

        # Check semantic fingerprint quality
        fingerprint_query = """
            SELECT
                COUNT(*) as total_with_fingerprints,
                AVG(LENGTH(semantic_fingerprint)) as avg_fingerprint_length,
                COUNT(DISTINCT semantic_fingerprint) as unique_fingerprints
            FROM opportunities_unified
            WHERE semantic_fingerprint IS NOT NULL AND semantic_fingerprint != ''
        """

        result = await conn.fetchrow(fingerprint_query)
        checks['semantic_fingerprints'] = dict(result)

        return checks

    async def check_constraint_validation(self, conn: asyncpg.Connection) -> Dict:
        """Check constraint validation."""
        logger.info("Checking constraint validation...")

        checks = {}

        # Check foreign key constraints
        fk_violations_query = """
            SELECT 'app_opportunities_submission_uuid' as constraint_name,
                   COUNT(*) as violations
            FROM app_opportunities ao
            WHERE ao.submission_uuid IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM submissions s WHERE s.id = ao.submission_uuid)

            UNION ALL

            SELECT 'llm_analysis_submission_uuid' as constraint_name,
                   COUNT(*) as violations
            FROM llm_monetization_analysis lma
            WHERE lma.submission_uuid IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM submissions s WHERE s.id = lma.submission_uuid)

            UNION ALL

            SELECT 'workflow_results_opportunity_id' as constraint_name,
                   COUNT(*) as violations
            FROM workflow_results wr
            WHERE wr.opportunity_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM opportunities_unified ou WHERE ou.id = wr.opportunity_id)
        """

        results = await conn.fetch(fk_violations_query)
        checks['foreign_key_violations'] = [dict(row) for row in results]

        # Check data quality constraints
        quality_query = """
            SELECT 'opportunities_unified_trust_score' as check_name,
                   COUNT(*) as violations
            FROM opportunities_unified
            WHERE trust_score < 0 OR trust_score > 100

            UNION ALL

            SELECT 'opportunities_unified_confidence' as check_name,
                   COUNT(*) as violations
            FROM opportunities_unified
            WHERE confidence < 0 OR confidence > 1
        """

        results = await conn.fetch(quality_query)
        checks['data_quality_violations'] = [dict(row) for row in results]

        return checks

    async def fix_missing_uuids(self, conn: asyncpg.Connection) -> int:
        """Fix missing UUID columns if fix_issues is enabled."""
        if not self.fix_issues or self.dry_run:
            logger.info("Skipping UUID fixes (fix_issues=False or dry_run=True)")
            return 0

        logger.info("Fixing missing UUIDs...")

        fixed_count = 0

        # Fix app_opportunities missing UUIDs
        app_opp_fix = """
            UPDATE app_opportunities
            SET submission_uuid = (
                SELECT id FROM submissions s WHERE s.submission_id = app_opportunities.submission_id LIMIT 1
            )
            WHERE submission_uuid IS NULL
            AND submission_id IS NOT NULL
            AND EXISTS (SELECT 1 FROM submissions s WHERE s.submission_id = app_opportunities.submission_id)
        """

        if not self.dry_run:
            result = await conn.execute(app_opp_fix)
            fixed_count += int(result.split()[-1]) if result else 0
        else:
            logger.info("[DRY RUN] Would fix app_opportunities missing UUIDs")

        # Fix llm_monetization_analysis missing UUIDs
        llm_fix = """
            UPDATE llm_monetization_analysis
            SET submission_uuid = (
                SELECT id FROM submissions s WHERE s.submission_id = llm_monetization_analysis.submission_id LIMIT 1
            )
            WHERE submission_uuid IS NULL
            AND submission_id IS NOT NULL
            AND EXISTS (SELECT 1 FROM submissions s WHERE s.submission_id = llm_monetization_analysis.submission_id)
        """

        if not self.dry_run:
            result = await conn.execute(llm_fix)
            fixed_count += int(result.split()[-1]) if result else 0
        else:
            logger.info("[DRY RUN] Would fix llm_monetization_analysis missing UUIDs")

        return fixed_count

    async def check_performance_impact(self, conn: asyncpg.Connection) -> Dict:
        """Check performance impact of the changes."""
        logger.info("Checking performance impact...")

        checks = {}

        # Test key query performance
        test_queries = [
            {
                'name': 'opportunities_by_business_concept',
                'query': """
                    EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                    SELECT * FROM opportunities_unified
                    WHERE business_concept_id IS NOT NULL
                    ORDER BY created_at DESC LIMIT 10
                """
            },
            {
                'name': 'app_opportunities_by_submission_uuid',
                'query': """
                    EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                    SELECT * FROM app_opportunities
                    WHERE submission_uuid = $1
                    LIMIT 1
                """
            }
        ]

        for test in test_queries:
            try:
                if test['name'] == 'app_opportunities_by_submission_uuid':
                    # Need a UUID parameter for this query
                    sample_uuid = await conn.fetchval("""
                        SELECT submission_uuid FROM app_opportunities
                        WHERE submission_uuid IS NOT NULL LIMIT 1
                    """)
                    if sample_uuid:
                        result = await conn.fetchrow(test['query'], sample_uuid)
                else:
                    result = await conn.fetchrow(test['query'])

                if result:
                    plan_data = result[f'QUERY PLAN']
                    execution_time = plan_data[0].get('Execution Time', 0) if plan_data else 0
                    checks[test['name']] = {
                        'execution_time_ms': execution_time,
                        'status': 'good' if execution_time < 1000 else 'needs_review'
                    }
                else:
                    checks[test['name']] = {
                        'execution_time_ms': None,
                        'status': 'no_data'
                    }
            except Exception as e:
                logger.warning(f"Performance test {test['name']} failed: {e}")
                checks[test['name']] = {
                    'execution_time_ms': None,
                    'status': 'error',
                    'error': str(e)
                }

        return checks

    async def run_validation(self) -> Dict:
        """Run complete validation suite."""
        logger.info("Starting UUID migration validation...")

        conn = await self.get_async_connection()

        try:
            # Run all validation checks
            self.validation_results['checks']['uuid_consistency'] = await self.check_uuid_foreign_key_consistency(conn)
            self.validation_results['checks']['deduplication_schema'] = await self.check_deduplication_schema_integration(conn)
            self.validation_results['checks']['constraint_validation'] = await self.check_constraint_validation(conn)
            self.validation_results['checks']['performance_impact'] = await self.check_performance_impact(conn)

            # Fix issues if requested
            fixed_count = await self.fix_missing_uuids(conn)
            self.validation_results['summary']['records_fixed'] = fixed_count

            # Calculate overall status
            total_issues = 0
            for check_category, check_results in self.validation_results['checks'].items():
                if isinstance(check_results, dict):
                    for result in check_results.values():
                        if isinstance(result, dict) and 'violations' in result:
                            total_issues += result.get('violations', 0)
                elif isinstance(check_results, list):
                    for result in check_results:
                        if isinstance(result, dict) and 'violations' in result:
                            total_issues += result.get('violations', 0)

            self.validation_results['summary']['total_issues'] = total_issues
            self.validation_results['summary']['validation_success'] = total_issues == 0

            # Generate recommendations
            self.validation_results['recommendations'] = self._generate_recommendations()

            logger.info(f"Validation completed - Total issues: {total_issues}")
            return self.validation_results

        finally:
            await conn.close()

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        # Check for UUID consistency issues
        uuid_checks = self.validation_results['checks'].get('uuid_consistency', {})
        for table, results in uuid_checks.items():
            if results.get('missing_uuid', 0) > 0:
                recommendations.append(
                    f"Table {table} has {results['missing_uuid']} records with missing UUID columns. "
                    "Run with --fix-issues to resolve."
                )
            if results.get('orphaned_uuid', 0) > 0:
                recommendations.append(
                    f"Table {table} has {results['orphaned_uuid']} orphaned UUID references. "
                    "Review data integrity."
                )

        # Check for deduplication schema issues
        dedup_checks = self.validation_results['checks'].get('deduplication_schema', {})
        if 'foreign_key_relationships' in dedup_checks:
            fk_results = dedup_checks['foreign_key_relationships']
            if fk_results.get('orphaned_opportunities', 0) > 0:
                recommendations.append(
                    f"{fk_results['orphaned_opportunities']} opportunities have missing submission links."
                )

        # Check for constraint violations
        constraint_checks = self.validation_results['checks'].get('constraint_validation', {})
        fk_violations = constraint_checks.get('foreign_key_violations', [])
        for violation in fk_violations:
            if violation.get('violations', 0) > 0:
                recommendations.append(
                    f"Foreign key constraint {violation['constraint_name']} has {violation['violations']} violations."
                )

        # Check for performance issues
        perf_checks = self.validation_results['checks'].get('performance_impact', {})
        for query_name, results in perf_checks.items():
            if results.get('status') == 'needs_review':
                recommendations.append(
                    f"Query {query_name} has slow performance ({results['execution_time_ms']}ms). "
                    "Consider adding indexes."
                )

        if not recommendations:
            recommendations.append("No issues detected. Migration validation successful.")

        return recommendations

    def save_results(self) -> str:
        """Save validation results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/uuid_migration_validation_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)

        logger.info(f"Validation results saved to {filename}")
        return filename


async def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(description="UUID Migration Validation")
    parser.add_argument(
        '--fix-issues',
        action='store_true',
        help='Attempt to fix found issues automatically'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no changes made)'
    )
    parser.add_argument(
        '--output-format',
        choices=['text', 'json'],
        default='text',
        help='Output format for results'
    )

    args = parser.parse_args()

    # Initialize validator
    validator = UUIDMigrationValidator(fix_issues=args.fix_issues, dry_run=args.dry_run)

    try:
        # Run validation
        results = await validator.run_validation()

        # Save results
        results_file = validator.save_results()

        # Output results
        if args.output_format == 'json':
            print(json.dumps(results, indent=2, default=str))
        else:
            print("\n" + "="*60)
            print("UUID MIGRATION VALIDATION RESULTS")
            print("="*60)
            print(f"Timestamp: {results['timestamp']}")
            print(f"Total Issues: {results['summary']['total_issues']}")
            print(f"Validation Success: {results['summary']['validation_success']}")
            print(f"Records Fixed: {results['summary'].get('records_fixed', 0)}")

            print("\nRECOMMENDATIONS:")
            for recommendation in results['recommendations']:
                print(f"  • {recommendation}")

            print(f"\nDetailed results saved to: {results_file}")

            # Exit with appropriate code
            sys.exit(0 if results['summary']['validation_success'] else 1)

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())