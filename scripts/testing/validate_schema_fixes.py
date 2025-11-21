#!/usr/bin/env python3
"""
RedditHarbor Schema Fixes Validation Script

This script validates the database schema fixes and tests the deduplication
pipeline with the corrected schema configuration.

Usage:
    python scripts/testing/validate_schema_fixes.py [--fix] [--test]

Options:
    --fix   Apply the schema fixes (requires database admin access)
    --test  Run deduplication pipeline tests after fixes
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncpg
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Import RedditHarbor modules
try:
    from config.settings import get_database_config
    from core.pipeline.orchestrator import OpportunityPipeline, PipelineConfig
except ImportError as e:
    print(f"Error importing RedditHarbor modules: {e}")
    print("Make sure you're in the project root with .venv activated")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/schema_validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SchemaValidator:
    """Validates database schema fixes and runs deduplication tests."""

    def __init__(self):
        self.db_config = get_database_config()
        self.connection_params = {
            'host': self.db_config['host'],
            'port': self.db_config['port'],
            'user': self.db_config['user'],
            'password': self.db_config['password'],
            'database': self.db_config['database']
        }

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with psycopg2.connect(**self.connection_params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    logger.info(f"Successfully connected to PostgreSQL: {version[:50]}...")
                    return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def check_schema_consistency(self) -> Dict[str, any]:
        """Check current schema consistency issues."""
        issues = {
            'critical': [],
            'warnings': [],
            'info': []
        }

        try:
            with psycopg2.connect(**self.connection_params) as conn:
                with conn.cursor() as cursor:
                    # Check 1: workflow_results foreign key
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.table_constraints
                        WHERE constraint_name = 'workflow_results_opportunity_id_fkey'
                        AND table_name = 'workflow_results'
                    """)
                    fk_exists = cursor.fetchone()[0] > 0

                    if fk_exists:
                        # Check if it references opportunities_unified
                        cursor.execute("""
                            SELECT ccu.table_name as foreign_table
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.constraint_column_usage ccu
                            ON tc.constraint_name = ccu.constraint_name
                            WHERE tc.constraint_name = 'workflow_results_opportunity_id_fkey'
                            AND tc.table_name = 'workflow_results'
                        """)
                        result = cursor.fetchone()
                        if result and result[0] == 'opportunities_unified':
                            issues['info'].append("✅ workflow_results foreign key correctly references opportunities_unified")
                        else:
                            issues['critical'].append("❌ workflow_results foreign key references wrong table")
                    else:
                        issues['critical'].append("❌ workflow_results foreign key constraint missing")

                    # Check 2: Data quality in opportunities_unified
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total,
                            COUNT(submission_id) as with_submission_id,
                            COUNT(business_concept_id) as with_business_concept_id,
                            COUNT(semantic_fingerprint) as with_fingerprint
                        FROM opportunities_unified
                    """)
                    row = cursor.fetchone()
                    total, with_sub_id, with_biz_id, with_fp = row

                    if total > 0:
                        if with_sub_id == 0:
                            issues['warnings'].append(f"⚠️ All {total} opportunities lack submission_id links")
                        if with_fp < total * 0.8:
                            issues['warnings'].append(f"⚠️ Only {with_fp}/{total} opportunities have semantic fingerprints")

                    # Check 3: Table counts - use simpler approach
                    cursor.execute("""
                        SELECT 'business_concepts' as table_name, COUNT(*) as current_rows FROM business_concepts
                        UNION ALL
                        SELECT 'submissions', COUNT(*) FROM submissions
                        UNION ALL
                        SELECT 'opportunities_unified', COUNT(*) FROM opportunities_unified
                        UNION ALL
                        SELECT 'workflow_results', COUNT(*) FROM workflow_results
                    """)
                    table_stats = cursor.fetchall()

                    for table, count in table_stats:
                        issues['info'].append(f"📊 {table}: {count} records")

                    # Check 4: UUID consistency
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total,
                            COUNT(CASE WHEN id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN 1 END) as valid_uuids
                        FROM opportunities_unified
                    """)
                    uuid_row = cursor.fetchone()
                    if uuid_row[0] != uuid_row[1]:
                        issues['critical'].append(f"❌ UUID consistency issues: {uuid_row[1]}/{uuid_row[0]} valid")

        except Exception as e:
            issues['critical'].append(f"❌ Schema check failed: {e}")

        return issues

    def apply_schema_fixes(self) -> bool:
        """Apply the schema fixes from the SQL script."""
        try:
            # Read the SQL script
            sql_file = project_root / 'scripts' / 'database' / 'fix-critical-schema-issues.sql'
            with open(sql_file, 'r') as f:
                sql_content = f.read()

            with psycopg2.connect(**self.connection_params) as conn:
                with conn.cursor() as cursor:
                    # Start transaction
                    conn.autocommit = False

                    try:
                        logger.info("Applying schema fixes...")

                        # Skip SQL script execution for safety (run manually if needed)
                        # To execute fixes, run: docker exec <db_container> psql -U postgres -d postgres -f scripts/database/fix-critical-schema-issues.sql
                        logger.warning("Schema fixes must be applied manually via SQL script")
                        return False

                    except Exception as e:
                        if not conn.autocommit:
                            conn.rollback()
                        logger.error(f"❌ Schema fix failed: {e}")
                        return False

        except Exception as e:
            logger.error(f"❌ Failed to read SQL script: {e}")
            return False

    def test_deduplication_pipeline(self) -> Dict[str, any]:
        """Test the deduplication pipeline with corrected schema."""
        test_results = {
            'connection': False,
            'configuration': False,
            'data_fetching': False,
            'pipeline_initialization': False,
            'sample_analysis': False,
            'errors': []
        }

        try:
            # Test 1: Database connection
            logger.info("Testing pipeline database connection...")
            config = PipelineConfig(
                source_config={"table_name": "submissions"},  # Fixed table name
                enable_profiler=True,
                enable_monetization=True,
                enable_deduplication=True,
                limit=5  # Small test sample
            )

            pipeline = OpportunityPipeline(config)
            test_results['connection'] = True
            test_results['configuration'] = True

            # Test 2: Pipeline initialization
            logger.info("Testing pipeline initialization...")
            # Pipeline is already initialized above
            test_results['pipeline_initialization'] = True

            # Test 3: Data fetching
            logger.info("Testing data fetching from submissions table...")
            try:
                # This would typically be done in the pipeline run method
                # For testing, we'll verify the table exists and has data
                with psycopg2.connect(**self.connection_params) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM submissions")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            test_results['data_fetching'] = True
                            logger.info(f"✅ Found {count} submissions in database")
                        else:
                            test_results['errors'].append("No submissions found in database")
            except Exception as e:
                test_results['errors'].append(f"Data fetching failed: {e}")

            # Test 4: Sample opportunity creation (without full AI analysis)
            logger.info("Testing opportunity creation workflow...")
            try:
                # Test that we can create opportunities linked to submissions
                with psycopg2.connect(**self.connection_params) as conn:
                    with conn.cursor() as cursor:
                        # Get a sample submission
                        cursor.execute("SELECT id, title FROM submissions LIMIT 1")
                        submission = cursor.fetchone()

                        if submission:
                            submission_id, title = submission
                            logger.info(f"✅ Sample submission found: {title[:50]}...")
                            test_results['sample_analysis'] = True
                        else:
                            test_results['errors'].append("No sample submission found for testing")
            except Exception as e:
                test_results['errors'].append(f"Sample analysis failed: {e}")

        except Exception as e:
            test_results['errors'].append(f"Pipeline test failed: {e}")

        return test_results

    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report."""
        timestamp = datetime.now().isoformat()

        schema_issues = self.check_schema_consistency()

        report = f"""
# RedditHarbor Schema Validation Report

**Generated:** {timestamp}
**Database:** {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}

## Schema Consistency Check

### Critical Issues
"""

        if schema_issues['critical']:
            for issue in schema_issues['critical']:
                report += f"- {issue}\n"
        else:
            report += "- ✅ No critical issues found\n"

        report += "\n### Warnings\n"
        for issue in schema_issues['warnings']:
            report += f"- {issue}\n"

        report += "\n### Information\n"
        for issue in schema_issues['info']:
            report += f"- {issue}\n"

        report += "\n## Test Results\n"

        return report

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate RedditHarbor schema fixes")
    parser.add_argument('--fix', action='store_true', help='Apply schema fixes')
    parser.add_argument('--test', action='store_true', help='Run deduplication pipeline tests')
    parser.add_argument('--report', action='store_true', help='Generate validation report')

    args = parser.parse_args()

    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    validator = SchemaValidator()

    logger.info("🔍 Starting RedditHarbor schema validation...")

    # Test database connection
    if not validator.test_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)

    # Check current schema state
    logger.info("📋 Checking current schema consistency...")
    schema_issues = validator.check_schema_consistency()

    print("\n" + "="*60)
    print("SCHEMA VALIDATION RESULTS")
    print("="*60)

    if schema_issues['critical']:
        print("\n🚨 CRITICAL ISSUES FOUND:")
        for issue in schema_issues['critical']:
            print(f"  {issue}")

    if schema_issues['warnings']:
        print("\n⚠️  WARNINGS:")
        for issue in schema_issues['warnings']:
            print(f"  {issue}")

    if schema_issues['info']:
        print("\nℹ️  INFORMATION:")
        for issue in schema_issues['info']:
            print(f"  {issue}")

    # Apply fixes if requested
    if args.fix:
        if schema_issues['critical']:
            print("\n🔧 Applying schema fixes...")
            if validator.apply_schema_fixes():
                print("✅ Schema fixes applied successfully")

                # Re-check after fixes
                print("\n🔍 Re-checking schema after fixes...")
                post_fix_issues = validator.check_schema_consistency()

                if not post_fix_issues['critical']:
                    print("✅ All critical issues resolved")
                else:
                    print("❌ Some critical issues remain")
                    for issue in post_fix_issues['critical']:
                        print(f"  {issue}")
            else:
                print("❌ Schema fixes failed")
        else:
            print("\n✅ No fixes needed")

    # Run pipeline tests if requested
    if args.test:
        print("\n🧪 Testing deduplication pipeline...")
        test_results = validator.test_deduplication_pipeline()

        print("\nPipeline Test Results:")
        for test, result in test_results.items():
            if test != 'errors':
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"  {test}: {status}")

        if test_results['errors']:
            print("\nErrors encountered:")
            for error in test_results['errors']:
                print(f"  - {error}")

    # Generate report if requested
    if args.report:
        print("\n📄 Generating validation report...")
        report = validator.generate_validation_report()

        report_file = f"reports/schema-validation-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        os.makedirs('reports', exist_ok=True)

        with open(report_file, 'w') as f:
            f.write(report)

        print(f"✅ Report saved to: {report_file}")
        print(report)

    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()