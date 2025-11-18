#!/usr/bin/env python3
"""
RedditHarbor Schema Validator using Supabase CLI

Validates the database schema against expected patterns and checks for common issues.
This helps ensure data integrity and schema consistency.

Usage:
    python utils/schema_validator.py
    python utils/schema_validator.py --check foreign-keys
    python utils/schema_validator.py --check indexes

Requirements:
    - Supabase CLI installed and configured
    - Supabase project running locally (supabase start)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class SchemaValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.schema_dumps_dir = project_root / "schema_dumps"
        self.results_dir = self.schema_dumps_dir / "validation_results"
        self.results_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_supabase_query(self, sql_query: str) -> list[dict[str, Any]]:
        """Execute a SQL query and return results as list of dictionaries."""
        try:
            clean_query = sql_query.strip().replace('"', '\\"').replace('\n', ' ')

            result = subprocess.run(
                ["supabase", "db", "--command", f"{clean_query}", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                return json.loads(result.stdout)
            return []

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running SQL query: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON result: {e}")
            return []
        except FileNotFoundError:
            print("❌ Supabase CLI not found. Please install it with: npm install -g supabase")
            return []

    def check_foreign_key_consistency(self) -> dict[str, Any]:
        """Check foreign key consistency and orphaned records."""
        print("🔗 Checking foreign key consistency...")

        # Get all foreign key constraints
        fk_query = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public';
        """

        foreign_keys = self.run_supabase_query(fk_query)
        issues = []

        for fk in foreign_keys:
            # Check for orphaned records
            orphan_check = f"""
            SELECT COUNT(*) as orphaned_count
            FROM {fk['table_name']} t1
            LEFT JOIN {fk['foreign_table_name']} t2
              ON t1.{fk['column_name']} = t2.{fk['foreign_column_name']}
            WHERE t1.{fk['column_name']} IS NOT NULL
              AND t2.{fk['foreign_column_name']} IS NULL;
            """

            result = self.run_supabase_query(orphan_check)
            if result and result[0]['orphaned_count'] > 0:
                issues.append({
                    'table': fk['table_name'],
                    'column': fk['column_name'],
                    'foreign_table': fk['foreign_table_name'],
                    'foreign_column': fk['foreign_column_name'],
                    'orphaned_count': result[0]['orphaned_count']
                })

        return {
            'total_foreign_keys': len(foreign_keys),
            'issues': issues,
            'status': 'PASS' if len(issues) == 0 else 'FAIL'
        }

    def check_index_coverage(self) -> dict[str, Any]:
        """Check index coverage for commonly queried columns."""
        print("📚 Checking index coverage...")

        # Get all indexes
        index_query = """
        SELECT
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public';
        """

        indexes = self.run_supabase_query(index_query)

        # Common patterns that should be indexed
        expected_patterns = [
            ('opportunities_unified', 'submission_id'),
            ('opportunities_unified', 'app_name'),
            ('opportunity_assessments', 'opportunity_id'),
            ('submissions', 'redditor_id'),
            ('submissions', 'subreddit_id'),
            ('comments', 'redditor_id'),
            ('comments', 'submission_id'),
        ]

        missing_indexes = []
        table_indexes = {}

        for idx in indexes:
            table = idx['tablename']
            if table not in table_indexes:
                table_indexes[table] = []
            table_indexes[table].append(idx['indexdef'])

        for table, column in expected_patterns:
            if table not in table_indexes:
                missing_indexes.append(f"{table}.{column} - No indexes on table")
                continue

            has_column_index = any(
                column in idx_def.lower()
                for idx_def in table_indexes[table]
            )

            if not has_column_index:
                missing_indexes.append(f"{table}.{column} - Column not indexed")

        return {
            'total_indexes': len(indexes),
            'tables_with_indexes': len(table_indexes),
            'missing_indexes': missing_indexes,
            'status': 'PASS' if len(missing_indexes) == 0 else 'WARNING'
        }

    def check_table_consistency(self) -> dict[str, Any]:
        """Check for table consistency issues."""
        print("🔍 Checking table consistency...")

        issues = []

        # Check for tables with no data
        empty_tables_query = """
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename NOT LIKE 'backup_%'
          AND tablename NOT LIKE '%_backup_%'
        EXCEPT
        SELECT schemaname, tablename
        FROM (
            SELECT schemaname, tablename, COUNT(*) as row_count
            FROM information_schema.columns
            WHERE table_schema = 'public'
            GROUP BY schemaname, tablename
        ) t
        WHERE EXISTS (
            SELECT 1 FROM {schema}.{table} LIMIT 1
        );
        """

        # Check for tables without primary keys
        no_pk_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
          AND table_name NOT LIKE 'backup_%'
          AND table_name NOT LIKE '%_backup_%'
        EXCEPT
        SELECT tc.table_name
        FROM information_schema.table_constraints tc
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = 'public';
        """

        # Check for inconsistent naming patterns
        naming_query = """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND (tablename LIKE '%backup%'
               OR tablename LIKE '___%'
               OR tablename ~ '[A-Z]{3,}')
        ORDER BY tablename;
        """

        empty_tables = self.run_supabase_query(empty_tables_query)
        no_pk_tables = self.run_supabase_query(no_pk_query)
        naming_issues = self.run_supabase_query(naming_query)

        if empty_tables:
            issues.extend([f"Empty table: {t['tablename']}" for t in empty_tables])

        if no_pk_tables:
            issues.extend([f"No primary key: {t['table_name']}" for t in no_pk_tables])

        if naming_issues:
            issues.extend([f"Naming issue: {t['tablename']}" for t in naming_issues])

        return {
            'issues': issues,
            'status': 'PASS' if len(issues) == 0 else 'WARNING'
        }

    def check_data_quality(self) -> dict[str, Any]:
        """Check data quality metrics."""
        print("📊 Checking data quality...")

        quality_metrics = {}

        # Check for NULL values in critical columns
        null_checks = [
            ("opportunities_unified", "app_name", "App name should not be NULL"),
            ("opportunities_unified", "problem_statement", "Problem statement should not be NULL"),
            ("opportunity_assessments", "opportunity_id", "Opportunity ID should not be NULL"),
        ]

        null_issues = []
        for table, column, description in null_checks:
            null_check_query = f"""
            SELECT COUNT(*) as null_count, COUNT(*) as total_count
            FROM {table}
            WHERE {column} IS NULL;
            """

            result = self.run_supabase_query(null_check_query)
            if result and result[0]['null_count'] > 0:
                null_percentage = (result[0]['null_count'] / result[0]['total_count']) * 100
                null_issues.append({
                    'table': table,
                    'column': column,
                    'description': description,
                    'null_count': result[0]['null_count'],
                    'total_count': result[0]['total_count'],
                    'null_percentage': round(null_percentage, 2)
                })

        # Check for duplicate records
        duplicate_checks = [
            ("opportunities_unified", "app_name", "App names should be unique"),
        ]

        duplicate_issues = []
        for table, column, description in duplicate_checks:
            duplicate_check_query = f"""
            SELECT COUNT(*) - COUNT(DISTINCT {column}) as duplicate_count,
                   COUNT(*) as total_count
            FROM {table}
            WHERE {column} IS NOT NULL;
            """

            result = self.run_supabase_query(duplicate_check_query)
            if result and result[0]['duplicate_count'] > 0:
                duplicate_issues.append({
                    'table': table,
                    'column': column,
                    'description': description,
                    'duplicate_count': result[0]['duplicate_count'],
                    'total_count': result[0]['total_count']
                })

        quality_metrics['null_issues'] = null_issues
        quality_metrics['duplicate_issues'] = duplicate_issues
        quality_metrics['status'] = 'PASS' if len(null_issues) == 0 and len(duplicate_issues) == 0 else 'WARNING'

        return quality_metrics

    def generate_validation_report(self, results: dict[str, Any]) -> str:
        """Generate a comprehensive validation report."""
        report = f"""# RedditHarbor Schema Validation Report

**Generated**: {datetime.now().isoformat()}
**Tool**: Supabase CLI Schema Validator
**Database**: Local Supabase Instance

## Executive Summary

"""

        total_checks = len(results)
        passed_checks = sum(1 for r in results.values() if isinstance(r, dict) and r.get('status') == 'PASS')

        report += f"- **Total Checks**: {total_checks}\n"
        report += f"- **Passed**: {passed_checks}\n"
        report += f"- **Failed/Warnings**: {total_checks - passed_checks}\n"
        report += f"- **Overall Status**: {'✅ PASS' if passed_checks == total_checks else '⚠️ ISSUES FOUND'}\n\n"

        # Detailed results
        for check_name, result in results.items():
            report += f"## {check_name.replace('_', ' ').title()}\n\n"

            if isinstance(result, dict):
                status = result.get('status', 'UNKNOWN')
                status_icon = '✅' if status == 'PASS' else '⚠️' if status == 'WARNING' else '❌'
                report += f"**Status**: {status_icon} {status}\n\n"

                # Include specific details based on check type
                if result.get('issues'):
                    report += "### Issues Found:\n\n"
                    for issue in result['issues']:
                        if isinstance(issue, dict):
                            report += f"- **{issue.get('table', 'Unknown')}.{issue.get('column', 'Unknown')}**: "
                            report += f"{issue.get('orphaned_count', 'Unknown')} orphaned records\n"
                        else:
                            report += f"- {issue}\n"
                    report += "\n"

                if result.get('missing_indexes'):
                    report += "### Missing Indexes:\n\n"
                    for missing in result['missing_indexes']:
                        report += f"- {missing}\n"
                    report += "\n"

                if 'null_issues' in result:
                    null_issues = result['null_issues']
                    if null_issues:
                        report += "### NULL Value Issues:\n\n"
                        for issue in null_issues:
                            report += f"- **{issue['table']}.{issue['column']}**: "
                            report += f"{issue['null_count']}/{issue['total_count']} "
                            report += f"({issue['null_percentage']}%) - {issue['description']}\n"
                        report += "\n"

                if 'duplicate_issues' in result:
                    duplicate_issues = result['duplicate_issues']
                    if duplicate_issues:
                        report += "### Duplicate Issues:\n\n"
                        for issue in duplicate_issues:
                            report += f"- **{issue['table']}.{issue['column']}**: "
                            report += f"{issue['duplicate_count']} duplicates - {issue['description']}\n"
                        report += "\n"

        report += """## Recommendations

### For Production Deployment
1. Address all foreign key consistency issues
2. Add missing indexes for performance optimization
3. Resolve data quality issues (NULL values, duplicates)
4. Implement regular schema validation checks

### For Development
1. Use these validation results to prioritize fixes
2. Set up automated schema validation in CI/CD
3. Monitor data quality metrics regularly

## Tool Usage

Run individual checks:
```bash
python utils/schema_validator.py --check foreign-keys
python utils/schema_validator.py --check indexes
python utils/schema_validator.py --check consistency
python utils/schema_validator.py --check data-quality
```

Run full validation:
```bash
python utils/schema_validator.py
```

---
*Generated by RedditHarbor Schema Validator*
"""

        return report

    def save_report(self, report: str) -> str:
        """Save validation report to file."""
        filename = self.results_dir / f"validation_report_{self.timestamp}.md"

        with open(filename, 'w') as f:
            f.write(report)

        print(f"✅ Validation report saved to: {filename}")
        return str(filename)

def main():
    parser = argparse.ArgumentParser(description="RedditHarbor Schema Validator")
    parser.add_argument("--check", choices=["foreign-keys", "indexes", "consistency", "data-quality"], help="Specific check to run")
    parser.add_argument("--project-root", help="Project root directory (auto-detected)")
    parser.add_argument("--save", action="store_true", help="Save report to file")

    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else Path(__file__).parent.parent.parent
    validator = SchemaValidator(project_root)

    # Check if Supabase is running
    try:
        result = validator.run_supabase_query("SELECT 1")
        if not result:
            print("❌ Supabase is not running. Please start it with:")
            print("   supabase start")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking Supabase status: {e}")
        print("Please ensure Supabase CLI is installed and running:")
        print("   1. npm install -g supabase")
        print("   2. supabase start")
        sys.exit(1)

    print("🔍 Starting RedditHarbor Schema Validation...")
    print(f"📊 Timestamp: {validator.timestamp}")
    print()

    results = {}

    if args.check:
        if args.check == "foreign-keys":
            results['foreign_key_consistency'] = validator.check_foreign_key_consistency()
        elif args.check == "indexes":
            results['index_coverage'] = validator.check_index_coverage()
        elif args.check == "consistency":
            results['table_consistency'] = validator.check_table_consistency()
        elif args.check == "data-quality":
            results['data_quality'] = validator.check_data_quality()
    else:
        # Run all checks
        results['foreign_key_consistency'] = validator.check_foreign_key_consistency()
        results['index_coverage'] = validator.check_index_coverage()
        results['table_consistency'] = validator.check_table_consistency()
        results['data_quality'] = validator.check_data_quality()

    # Generate and display report
    report = validator.generate_validation_report(results)
    print(report)

    if args.save:
        validator.save_report(report)

if __name__ == "__main__":
    main()
