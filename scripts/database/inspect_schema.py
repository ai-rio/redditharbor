#!/usr/bin/env python3
"""
Database Schema Introspection Tool

Uses SQLAlchemy to inspect the actual database schema and identify
why app_name fields aren't being stored properly.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Add project root and load environment
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
load_dotenv(project_root / '.env.local')
load_dotenv(project_root / '.env')

from config.settings import get_psycopg2_config

def inspect_database_schema():
    """Comprehensive database schema inspection to find app_name field issues."""

    try:
        # Get database configuration
        db_config = get_psycopg2_config()

        # Build connection string
        if isinstance(db_config, str):
            connection_string = db_config
        else:
            connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

        print(f"🔍 Connecting to database: {connection_string.split('@')[1]}")

        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        inspector = inspect(engine)

        print("\n" + "="*80)
        print("📊 DATABASE SCHEMA INTROSPECTION REPORT")
        print("="*80)

        # Get all tables
        tables = inspector.get_table_names()
        print(f"\n📋 Found {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  • {table}")

        # Focus on app_opportunities table
        if 'app_opportunities' not in tables:
            print(f"\n❌ ERROR: 'app_opportunities' table not found!")
            print("Available tables:", tables)
            return False

        print(f"\n🔍 DETAILED ANALYSIS: app_opportunities table")
        print("-" * 50)

        # Get column information
        columns = inspector.get_columns('app_opportunities')
        print(f"\n📐 Table Structure ({len(columns)} columns):")

        app_name_found = False
        for column in columns:
            nullable = "NULL" if column['nullable'] else "NOT NULL"
            default = f" DEFAULT {column['default']}" if column['default'] else ""
            print(f"  • {column['name']:20} {column['type']:20} {nullable} {default}")

            if column['name'] == 'app_name':
                app_name_found = True
                print(f"    ✅ app_name column FOUND!")
                print(f"    🔹 Type: {column['type']}")
                print(f"    🔹 Nullable: {column['nullable']}")
                print(f"    🔹 Default: {column['default']}")

        if not app_name_found:
            print(f"    ❌ app_name column NOT FOUND in app_opportunities table!")
            print(f"    🔧 This explains why app_name data isn't being stored!")

        # Check indexes
        indexes = inspector.get_indexes('app_opportunities')
        if indexes:
            print(f"\n🗂️  Indexes ({len(indexes)}):")
            for index in indexes:
                columns_str = ", ".join(index['column_names'])
                unique = "UNIQUE" if index['unique'] else ""
                print(f"  • {index['name']}: ({columns_str}) {unique}")

        # Check foreign keys
        foreign_keys = inspector.get_foreign_keys('app_opportunities')
        if foreign_keys:
            print(f"\n🔗 Foreign Keys ({len(foreign_keys)}):")
            for fk in foreign_keys:
                print(f"  • {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

        # Check actual data in app_opportunities
        print(f"\n📈 Data Analysis:")
        with engine.connect() as conn:
            # Count total records
            result = conn.execute(text("SELECT COUNT(*) FROM app_opportunities"))
            total_count = result.scalar()
            print(f"  • Total records: {total_count}")

            if total_count > 0:
                # Count records with app_name
                result = conn.execute(text("SELECT COUNT(*) FROM app_opportunities WHERE app_name IS NOT NULL"))
                app_name_count = result.scalar()
                print(f"  • Records with app_name: {app_name_count}")

                # Count records with app_category
                result = conn.execute(text("SELECT COUNT(*) FROM app_opportunities WHERE app_category IS NOT NULL"))
                app_category_count = result.scalar()
                print(f"  • Records with app_category: {app_category_count}")

                # Show sample records
                result = conn.execute(text("""
                    SELECT submission_id, app_name, app_category, problem_description
                    FROM app_opportunities
                    LIMIT 3
                """))
                samples = result.fetchall()

                if samples:
                    print(f"\n📝 Sample Records:")
                    for i, row in enumerate(samples, 1):
                        print(f"  {i}. {row[0]}: app_name={row[1]}, app_category={row[2]}")

            # Check our specific test submission
            test_id = "e7763e41-d7bf-4bf1-a004-decff9f0f0c5"
            result = conn.execute(text(f"""
                SELECT submission_id, app_name, app_category, problem_description
                FROM app_opportunities
                WHERE submission_id = '{test_id}'
            """))
            test_record = result.fetchone()

            if test_record:
                print(f"\n✅ Test submission found:")
                print(f"  • submission_id: {test_record[0]}")
                print(f"  • app_name: {test_record[1]}")
                print(f"  • app_category: {test_record[2]}")
            else:
                print(f"\n❌ Test submission NOT found: {test_id}")

        print(f"\n🎯 DIAGNOSIS:")
        if app_name_found:
            print(f"  ✅ app_name column EXISTS in database schema")
            print(f"  ❓ Issue may be in DLT pipeline or data insertion logic")
        else:
            print(f"  ❌ app_name column MISSING from database schema")
            print(f"  🔧 Need to add app_name column to app_opportunities table")

        return app_name_found

    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Starting database schema introspection...")
    success = inspect_database_schema()

    if not success:
        print("\n❌ Schema inspection revealed issues with app_name field")
        sys.exit(1)
    else:
        print("\n✅ Schema inspection completed - app_name field exists in database")
        print("The issue is likely in the data insertion/pipeline logic, not schema")
        sys.exit(0)