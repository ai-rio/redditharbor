#!/usr/bin/env python3
"""
Schema Synchronization Validator

Validates that the database schema matches expected migrations and detects drift.
Creates new migrations when schema changes are detected.

Usage:
    python scripts/database/validate_schema_sync.py
    python scripts/database/validate_schema_sync.py --fix
    python scripts/database/validate_schema_sync.py --diff
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any

import psycopg2
from psycopg2.extras import DictCursor

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env.local")

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates and synchronizes database schema with migrations."""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.db_url = os.getenv('DATABASE_URL') or self._get_db_url_from_supabase()

    def _get_db_url_from_supabase(self) -> str:
        """Extract PostgreSQL URL from Supabase URL."""
        # Extract host from SUPABASE_URL and construct PostgreSQL connection
        supabase_host = self.supabase_url.replace('https://', '').replace('http://', '')
        return f"postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    def get_actual_schema(self) -> Dict[str, Any]:
        """Extract current database schema."""
        schema = {
            'tables': {},
            'indexes': {},
            'constraints': {},
            'functions': {}
        }

        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor(cursor_factory=DictCursor)

            # Get tables and columns
            cursor.execute("""
                SELECT
                    table_name,
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)

            for row in cursor.fetchall():
                table_name = row['table_name']
                if table_name not in schema['tables']:
                    schema['tables'][table_name] = {
                        'columns': {},
                        'primary_keys': [],
                        'foreign_keys': []
                    }

                schema['tables'][table_name]['columns'][row['column_name']] = {
                    'type': row['data_type'],
                    'nullable': row['is_nullable'] == 'YES',
                    'default': row['column_default'],
                    'max_length': row['character_maximum_length'],
                    'precision': row['numeric_precision'],
                    'scale': row['numeric_scale']
                }

            # Get primary keys
            cursor.execute("""
                SELECT
                    tc.table_name,
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
            """)

            for row in cursor.fetchall():
                schema['tables'][row['table_name']]['primary_keys'].append(row['column_name'])

            # Get indexes
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                    AND indexname NOT LIKE '%_pkey'
            """)

            for row in cursor.fetchall():
                if row['tablename'] not in schema['indexes']:
                    schema['indexes'][row['tablename']] = {}
                schema['indexes'][row['tablename']][row['indexname']] = row['indexdef']

            conn.close()
            return schema

        except Exception as e:
            logger.error(f"Failed to extract schema: {e}")
            raise

    def get_expected_schema_from_migrations(self) -> Dict[str, Any]:
        """Build expected schema by parsing migration files."""
        migrations_dir = project_root / "supabase/migrations"
        schema = {
            'tables': {},
            'indexes': {},
            'constraints': {},
            'functions': {}
        }

        # Get all migration files in order
        migration_files = sorted(migrations_dir.glob("*.sql"))

        for migration_file in migration_files:
            if migration_file.name.startswith("archived") or migration_file.parent.name == "archived":
                continue

            try:
                with open(migration_file, 'r') as f:
                    content = f.read()

                # Parse SQL (simplified - in production, use a proper SQL parser)
                self._parse_migration_sql(content, schema)

            except Exception as e:
                logger.warning(f"Could not parse migration {migration_file}: {e}")

        return schema

    def _parse_migration_sql(self, sql: str, schema: Dict[str, Any]):
        """Parse migration SQL and update schema (simplified)."""
        # This is a simplified parser - in production, use a proper SQL parser
        lines = sql.split('\n')
        current_table = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('--'):
                continue

            # CREATE TABLE
            if line.upper().startswith('CREATE TABLE'):
                parts = line.split()
                if len(parts) >= 3:
                    table_name = parts[2].strip('();')
                    current_table = table_name
                    schema['tables'][table_name] = {
                        'columns': {},
                        'primary_keys': [],
                        'foreign_keys': []
                    }

            # ALTER TABLE ADD COLUMN
            elif line.upper().startswith('ALTER TABLE') and 'ADD COLUMN' in line.upper():
                parts = line.split()
                if len(parts) >= 6:
                    table_name = parts[2]
                    column_name = parts[5].split()[0]
                    column_type = ' '.join(parts[5].split()[1:]) if len(parts[5].split()) > 1 else 'TEXT'

                    if table_name not in schema['tables']:
                        schema['tables'][table_name] = {
                            'columns': {},
                            'primary_keys': [],
                            'foreign_keys': []
                        }

                    schema['tables'][table_name]['columns'][column_name] = {
                        'type': column_type.split()[0],  # Simplified
                        'nullable': True,
                        'default': None
                    }

    def compare_schemas(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
        """Compare actual vs expected schemas and identify drift."""
        drift = {
            'missing_tables': [],
            'extra_tables': [],
            'table_differences': {},
            'missing_indexes': [],
            'extra_indexes': []
        }

        # Compare tables
        actual_tables = set(actual['tables'].keys())
        expected_tables = set(expected['tables'].keys())

        drift['missing_tables'] = list(expected_tables - actual_tables)
        drift['extra_tables'] = list(actual_tables - expected_tables)

        # Compare table structures
        common_tables = actual_tables & expected_tables
        for table_name in common_tables:
            table_drift = self._compare_table_schemas(
                actual['tables'][table_name],
                expected['tables'][table_name]
            )
            if table_drift:
                drift['table_differences'][table_name] = table_drift

        # Compare indexes
        actual_indexes = self._flatten_indexes(actual['indexes'])
        expected_indexes = self._flatten_indexes(expected['indexes'])

        drift['missing_indexes'] = list(set(expected_indexes) - set(actual_indexes))
        drift['extra_indexes'] = list(set(actual_indexes) - set(expected_indexes))

        return drift

    def _compare_table_schemas(self, actual_table: Dict, expected_table: Dict) -> Dict[str, Any]:
        """Compare individual table schemas."""
        drift = {
            'missing_columns': [],
            'extra_columns': [],
            'column_differences': {},
            'missing_primary_keys': [],
            'extra_primary_keys': []
        }

        actual_columns = set(actual_table['columns'].keys())
        expected_columns = set(expected_table['columns'].keys())

        drift['missing_columns'] = list(expected_columns - actual_columns)
        drift['extra_columns'] = list(actual_columns - expected_columns)

        # Compare column types
        common_columns = actual_columns & expected_columns
        for column_name in common_columns:
            actual_col = actual_table['columns'][column_name]
            expected_col = expected_table['columns'][column_name]

            # Simplified type comparison
            if actual_col['type'] != expected_col['type']:
                drift['column_differences'][column_name] = {
                    'actual': actual_col['type'],
                    'expected': expected_col['type']
                }

        # Compare primary keys
        actual_pks = set(actual_table.get('primary_keys', []))
        expected_pks = set(expected_table.get('primary_keys', []))

        drift['missing_primary_keys'] = list(expected_pks - actual_pks)
        drift['extra_primary_keys'] = list(actual_pks - expected_pks)

        # Remove empty drift categories
        return {k: v for k, v in drift.items() if v}

    def _flatten_indexes(self, indexes: Dict[str, Dict[str, str]]) -> Set[str]:
        """Flatten index dict to set of index names."""
        flat_indexes = set()
        for table_name, table_indexes in indexes.items():
            for index_name in table_indexes.keys():
                flat_indexes.add(f"{table_name}.{index_name}")
        return flat_indexes

    def generate_migration(self, drift: Dict[str, Any], migration_name: str = None) -> str:
        """Generate migration SQL for detected drift."""
        if not migration_name:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            migration_name = f"schema_sync_{timestamp}"

        migration_sql = f"""-- Schema Synchronization Migration
-- Generated: {datetime.now().isoformat()}
-- Purpose: Fix schema drift detected by validation script

"""

        # Handle missing tables
        for table_name in drift.get('missing_tables', []):
            logger.warning(f"Missing table detected: {table_name}")
            migration_sql += f"-- TODO: Add CREATE TABLE for {table_name}\n"

        # Handle missing columns
        for table_name, table_drift in drift.get('table_differences', {}).items():
            for column_name in table_drift.get('missing_columns', []):
                logger.warning(f"Missing column detected: {table_name}.{column_name}")
                migration_sql += f"-- TODO: Add ALTER TABLE {table_name} ADD COLUMN {column_name} [TYPE]\n"

        # Handle missing primary keys
        for table_name, table_drift in drift.get('table_differences', {}).items():
            for pk_column in table_drift.get('missing_primary_keys', []):
                migration_sql += f"ALTER TABLE {table_name} ADD PRIMARY KEY ({pk_column});\n"

        # Handle missing indexes
        for index_ref in drift.get('missing_indexes', []):
            migration_sql += f"-- TODO: Add CREATE INDEX for {index_ref}\n"

        if migration_sql.strip() == migration_sql.split('\n')[0].strip():
            migration_sql += "-- No schema drift detected - database is in sync!\n"

        return migration_sql

    def save_migration_file(self, migration_name: str, migration_sql: str):
        """Save migration to file."""
        migrations_dir = project_root / "supabase/migrations"
        migration_file = migrations_dir / f"{migration_name}.sql"

        with open(migration_file, 'w') as f:
            f.write(migration_sql)

        logger.info(f"Migration saved: {migration_file}")
        return migration_file

    def run_validation(self, generate_fix: bool = False, show_diff: bool = False) -> bool:
        """Run schema validation."""
        logger.info("Extracting actual database schema...")
        actual_schema = self.get_actual_schema()

        logger.info("Building expected schema from migrations...")
        expected_schema = self.get_expected_schema_from_migrations()

        logger.info("Comparing schemas...")
        drift = self.compare_schemas(actual_schema, expected_schema)

        # Check for any drift
        has_drift = any([
            drift['missing_tables'],
            drift['extra_tables'],
            drift['table_differences'],
            drift['missing_indexes'],
            drift['extra_indexes']
        ])

        if show_diff:
            self._print_drift_report(drift)

        if has_drift:
            logger.warning("🚨 SCHEMA DRIFT DETECTED!")

            if generate_fix:
                logger.info("Generating migration fix...")
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                migration_name = f"schema_sync_{timestamp}"
                migration_sql = self.generate_migration(drift, migration_name)
                migration_file = self.save_migration_file(migration_name, migration_sql)

                logger.info(f"✅ Migration generated: {migration_file}")
                logger.info("Review the migration and run: supabase db push")
            else:
                logger.error("Run with --fix to generate migration")
                return False
        else:
            logger.info("✅ Schema is in sync with migrations!")

        return not has_drift

    def _print_drift_report(self, drift: Dict[str, Any]):
        """Print detailed drift report."""
        print("\n" + "="*60)
        print("🔍 SCHEMA DRIFT REPORT")
        print("="*60)

        if drift['missing_tables']:
            print(f"\n❌ Missing Tables: {drift['missing_tables']}")

        if drift['extra_tables']:
            print(f"\n➕ Extra Tables: {drift['extra_tables']}")

        if drift['table_differences']:
            print(f"\n📋 Table Differences:")
            for table_name, table_drift in drift['table_differences'].items():
                print(f"  📄 {table_name}:")
                if table_drift.get('missing_columns'):
                    print(f"    ❌ Missing columns: {table_drift['missing_columns']}")
                if table_drift.get('extra_columns'):
                    print(f"    ➕ Extra columns: {table_drift['extra_columns']}")
                if table_drift.get('column_differences'):
                    print(f"    ⚠️  Type differences:")
                    for col, diff in table_drift['column_differences'].items():
                        print(f"      {col}: {diff['actual']} (actual) vs {diff['expected']} (expected)")

        if drift['missing_indexes']:
            print(f"\n🔍 Missing Indexes: {drift['missing_indexes']}")

        if drift['extra_indexes']:
            print(f"\n➕ Extra Indexes: {drift['extra_indexes']}")

        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Validate schema synchronization")
    parser.add_argument('--fix', action='store_true', help='Generate migration fix')
    parser.add_argument('--diff', action='store_true', help='Show detailed diff')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        validator = SchemaValidator()
        success = validator.run_validation(generate_fix=args.fix, show_diff=args.diff)
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()