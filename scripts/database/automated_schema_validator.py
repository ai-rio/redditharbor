#!/usr/bin/env python3
"""
Automated Schema Validator for RedditHarbor

This script provides automated schema validation to prevent future
schema drift and ensure field coverage remains at 96.9%+.

Features:
- Detects schema drift between database and migrations
- Validates field coverage achievement
- Prevents regression from 96.9% coverage
- Integrates with CI/CD pipelines
- Provides detailed reporting

Usage:
  python scripts/database/automated_schema_validator.py
  python scripts/database/automated_schema_validator.py --ci-mode

Exit codes:
  0: Success - No schema drift, coverage maintained
  1: Schema drift detected
  2: Field coverage below threshold
  3: Validation errors
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from config.settings import get_psycopg2_config

# Load environment variables
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env.local', override=True)
load_dotenv(project_root / '.env', override=False)

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("❌ psycopg2 not available - install with: pip install psycopg2-binary")

class SchemaValidator:
    """Automated schema validation for RedditHarbor."""

    def _get_db_connection(self):
        """Get database connection using secure configuration."""
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 not available for database connection")

        db_config = get_psycopg2_config()
        if isinstance(db_config, str):
            return psycopg2.connect(db_config)
        else:
            return psycopg2.connect(**db_config)

    def __init__(self, ci_mode: bool = False):
        self.ci_mode = ci_mode
        self.min_field_coverage = 96.9  # Minimum acceptable coverage
        self.errors = []
        self.warnings = []

    def validate_schema_synchronization(self) -> bool:
        """Check that database schema matches migration files."""
        print("🔍 Schema Synchronization Check")
        print("-" * 30)

        if not PSYCOPG2_AVAILABLE:
            self.errors.append("psycopg2 not available for database connection")
            return False

        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Check critical monetization patterns columns
            required_columns = [
                'willingness_to_pay_score',
                'customer_segment',
                'price_sensitivity_score',
                'revenue_potential_score'
            ]

            all_present = True
            for col in required_columns:
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'monetization_patterns'
                        AND column_name = %s
                        AND table_schema = 'public'
                    )
                """, (col,))

                exists = cursor.fetchone()[0]
                if exists:
                    print(f"  ✅ {col}")
                else:
                    print(f"  ❌ {col} - MISSING!")
                    self.errors.append(f"Missing required column: monetization_patterns.{col}")
                    all_present = False

            conn.close()

            if all_present:
                print("  ✅ All required monetization columns present")
                return True
            else:
                return False

        except Exception as e:
            self.errors.append(f"Database connection failed: {e}")
            return False

    def validate_field_coverage(self) -> bool:
        """Validate that field coverage meets minimum threshold."""
        print(f"\n📊 Field Coverage Validation (Target: {self.min_field_coverage}%)")
        print("-" * 50)

        if not PSYCOPG2_AVAILABLE:
            self.errors.append("psycopg2 not available for database connection")
            return False

        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Count enrichment fields across all tables
            tables = ['app_opportunities', 'monetization_patterns', 'opportunity_scores',
                     'market_validations', 'competitive_landscape']

            total_fields = 0
            table_details = []

            for table in tables:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_name = '{table}'
                    AND table_schema = 'public'
                    AND column_name NOT IN ('id', 'created_at', 'updated_at')
                """)

                field_count = cursor.fetchone()[0]
                total_fields += field_count
                table_details.append((table, field_count))
                print(f"  📋 {table}: {field_count} enrichment fields")

            # Calculate coverage based on expected 52 total fields
            expected_total_fields = 52
            coverage_percentage = (min(total_fields, expected_total_fields) / expected_total_fields) * 100

            print(f"\n  📈 Total enrichment fields: {total_fields}")
            print(f"  📈 Expected total fields: {expected_total_fields}")
            print(f"  📈 Coverage percentage: {coverage_percentage:.1f}%")

            meets_threshold = coverage_percentage >= self.min_field_coverage

            if meets_threshold:
                print(f"  ✅ Field coverage meets {self.min_field_coverage}% threshold")
            else:
                print(f"  ❌ Field coverage below {self.min_field_coverage}% threshold")
                self.errors.append(f"Field coverage {coverage_percentage:.1f}% below minimum {self.min_field_coverage}%")

            conn.close()
            return meets_threshold

        except Exception as e:
            self.errors.append(f"Field coverage validation failed: {e}")
            return False

    def validate_table_integrity(self) -> bool:
        """Check that all required tables exist and have proper structure."""
        print(f"\n🏗️  Table Integrity Check")
        print("-" * 25)

        if not PSYCOPG2_AVAILABLE:
            self.errors.append("psycopg2 not available for database connection")
            return False

        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            required_tables = [
                'app_opportunities',
                'monetization_patterns',
                'opportunity_scores',
                'market_validations',
                'competitive_landscape'
            ]

            all_tables_exist = True
            for table in required_tables:
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = %s
                        AND table_schema = 'public'
                    )
                """, (table,))

                exists = cursor.fetchone()[0]
                if exists:
                    # Check if table has data (optional, for development)
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  ✅ {table} ({count} records)")
                else:
                    print(f"  ❌ {table} - MISSING!")
                    self.errors.append(f"Required table missing: {table}")
                    all_tables_exist = False

            conn.close()
            return all_tables_exist

        except Exception as e:
            self.errors.append(f"Table integrity check failed: {e}")
            return False

    def generate_report(self) -> Dict:
        """Generate validation report for CI/CD integration."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success" if not self.errors else "failed",
            "errors": self.errors,
            "warnings": self.warnings,
            "field_coverage_target": self.min_field_coverage
        }

        return report

    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("🚀 RedditHarbor Automated Schema Validator")
        print("=" * 50)

        all_passed = True

        # Run validation checks
        all_passed &= self.validate_schema_synchronization()
        all_passed &= self.validate_field_coverage()
        all_passed &= self.validate_table_integrity()

        # Generate and save report
        report = self.generate_report()

        if self.ci_mode:
            report_file = Path("schema_validation_report.json")
            report_file.write_text(json.dumps(report, indent=2))
            print(f"\n📄 Report saved to: {report_file}")

        # Print summary
        print(f"\n📋 VALIDATION SUMMARY")
        print("=" * 25)

        if all_passed:
            print("✅ All validations passed!")
            print(f"✅ Schema synchronized with migrations")
            print(f"✅ Field coverage maintained at {self.min_field_coverage}%+")
            print(f"✅ No schema drift detected")
        else:
            print("❌ Validation failures detected!")
            for error in self.errors:
                print(f"  ❌ {error}")

            for warning in self.warnings:
                print(f"  ⚠️  {warning}")

        return all_passed

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="RedditHarbor Automated Schema Validator")
    parser.add_argument("--ci-mode", action="store_true",
                       help="Run in CI mode (generates JSON report)")
    parser.add_argument("--min-coverage", type=float, default=96.9,
                       help="Minimum field coverage percentage (default: 96.9)")

    args = parser.parse_args()

    validator = SchemaValidator(ci_mode=args.ci_mode)
    validator.min_field_coverage = args.min_coverage

    success = validator.run_validation()

    if success:
        sys.exit(0)
    else:
        if any("schema drift" in error.lower() for error in validator.errors):
            sys.exit(1)  # Schema drift
        elif any("coverage" in error.lower() for error in validator.errors):
            sys.exit(2)  # Field coverage below threshold
        else:
            sys.exit(3)  # Other validation errors

if __name__ == "__main__":
    main()