#!/usr/bin/env python3
"""
Specialized Enrichment Tables Inspector

Uses SQLAlchemy to inspect the actual schema of specialized enrichment tables
and understand why they're empty despite test logs showing successful storage.
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

def inspect_enrichment_tables():
    """Comprehensive inspection of specialized enrichment tables."""

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
        print("📊 SPECIALIZED ENRICHMENT TABLES INSPECTION")
        print("="*80)

        # List of specialized enrichment tables we expect to be populated
        enrichment_tables = [
            'opportunity_scores',
            'monetization_patterns',
            'market_validations',
            'competitive_landscape'
        ]

        # Get all actual tables
        all_tables = inspector.get_table_names()
        print(f"\n📋 All tables in database ({len(all_tables)}):")
        for table in sorted(all_tables):
            print(f"  • {table}")

        # Check which enrichment tables exist
        existing_enrichment_tables = [t for t in enrichment_tables if t in all_tables]
        missing_enrichment_tables = [t for t in enrichment_tables if t not in all_tables]

        print(f"\n✅ Existing enrichment tables: {existing_enrichment_tables}")
        print(f"❌ Missing enrichment tables: {missing_enrichment_tables}")

        # Inspect each existing enrichment table
        for table_name in existing_enrichment_tables:
            print(f"\n🔍 DETAILED ANALYSIS: {table_name}")
            print("-" * 50)

            # Get column information
            columns = inspector.get_columns(table_name)
            print(f"\n📐 Table Structure ({len(columns)} columns):")

            primary_keys = inspector.get_pk_constraint(table_name)['constrained_columns']
            foreign_keys = inspector.get_foreign_keys(table_name)

            for column in columns:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                default = f" DEFAULT {column['default']}" if column['default'] else ""
                pk_marker = " 🔑" if column['name'] in primary_keys else ""
                fk_marker = " 🔗" if any(column['name'] in fk['constrained_columns'] for fk in foreign_keys) else ""

                column_type_str = str(column['type'])
                print(f"  • {column['name']:25} {column_type_str:20} {nullable}{default}{pk_marker}{fk_marker}")

            # Primary keys
            if primary_keys:
                print(f"\n🔑 Primary Keys: {primary_keys}")
            else:
                print(f"\n❌ No primary keys found!")

            # Foreign keys
            if foreign_keys:
                print(f"\n🔗 Foreign Keys:")
                for fk in foreign_keys:
                    print(f"  • {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

            # Indexes
            indexes = inspector.get_indexes(table_name)
            if indexes:
                print(f"\n🗂️  Indexes ({len(indexes)}):")
                for index in indexes:
                    columns_str = ", ".join(index['column_names'])
                    unique = "UNIQUE" if index['unique'] else ""
                    print(f"  • {index['name']}: ({columns_str}) {unique}")

            # Check actual data
            print(f"\n📈 Data Analysis:")
            with engine.connect() as conn:
                # Count total records
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                total_count = result.scalar()
                print(f"  • Total records: {total_count}")

                if total_count > 0:
                    # Get sample records
                    result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
                    samples = result.fetchall()
                    column_names = result.keys()

                    print(f"\n📝 Sample Records:")
                    for i, row in enumerate(samples, 1):
                        print(f"  {i}. ", end="")
                        for j, value in enumerate(row):
                            print(f"{column_names[j]}={value}", end="")
                            if j < len(row) - 1:
                                print(", ", end="")
                        print()

                    # Check for opportunity_id column specifically
                    if 'opportunity_id' in column_names:
                        result = conn.execute(text(f"SELECT DISTINCT opportunity_id FROM {table_name}"))
                        opportunity_ids = [row[0] for row in result.fetchall()]
                        print(f"  • Opportunity IDs found: {opportunity_ids}")
                else:
                    print(f"  ❌ TABLE IS EMPTY - This explains the issue!")

        # Check for any recent data insertion activity
        print(f"\n🔍 RECENT ACTIVITY ANALYSIS:")
        print("-" * 40)

        with engine.connect() as conn:
            # Check if there are any records in app_opportunities with enrichment data
            result = conn.execute(text("""
                SELECT COUNT(*) FROM app_opportunities
                WHERE final_score IS NOT NULL
                OR app_name IS NOT NULL
                OR willingness_to_pay_score IS NOT NULL
            """))
            enriched_app_opportunities = result.scalar()
            print(f"  • Enriched app_opportunities: {enriched_app_opportunities}")

            # Get the most recent submission_id from app_opportunities
            result = conn.execute(text("""
                SELECT submission_id, app_name, final_score, created_at
                FROM app_opportunities
                WHERE submission_id IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 5
            """))
            recent_submissions = result.fetchall()

            if recent_submissions:
                print(f"\n📝 Recent app_opportunities:")
                for i, row in enumerate(recent_submissions, 1):
                    print(f"  {i}. {row[0]}: app_name={row[1]}, score={row[2]}, created={row[3]}")

                # Check if any of these recent submission_ids exist in enrichment tables
                recent_submission_ids = [row[0] for row in recent_submissions if row[0]]
                if recent_submission_ids:
                    print(f"\n🔍 Checking if recent submissions are in enrichment tables:")
                    for table_name in existing_enrichment_tables:
                        try:
                            # Try different column names that might reference submissions
                            id_columns = ['submission_id', 'opportunity_id', 'app_opportunity_id']
                            found_any = False

                            for id_col in id_columns:
                                result = conn.execute(text(f"""
                                    SELECT COUNT(*) FROM {table_name}
                                    WHERE {id_col} IN :submission_ids
                                """), {'submission_ids': tuple(recent_submission_ids)})
                                count = result.scalar()
                                if count > 0:
                                    print(f"  • {table_name}.{id_col}: {count} matching records")
                                    found_any = True
                                    break

                            if not found_any:
                                print(f"  • {table_name}: No matching records found")
                        except Exception as e:
                            print(f"  • {table_name}: Error checking - {e}")

        # Test the specific opportunity_id from test logs
        test_opportunity_id = "d59d07ea-685d-4d0a-ad70-b8a33f0ebea8"
        print(f"\n🧪 TESTING SPECIFIC OPPORTUNITY_ID FROM TEST LOGS:")
        print(f"  • Test opportunity_id: {test_opportunity_id}")

        with engine.connect() as conn:
            for table_name in existing_enrichment_tables:
                try:
                    # Try different possible ID column names
                    id_columns = ['opportunity_id', 'submission_id', 'id']
                    found_records = False

                    for id_col in id_columns:
                        try:
                            result = conn.execute(text(f"""
                                SELECT COUNT(*) FROM {table_name}
                                WHERE {id_col} = :opportunity_id
                            """), {'opportunity_id': test_opportunity_id})
                            count = result.scalar()
                            if count > 0:
                                print(f"  ✅ {table_name}.{id_col}: {count} records found")
                                found_records = True
                                break
                        except Exception as e:
                            # Column might not exist, continue to next
                            continue

                    if not found_records:
                        print(f"  ❌ {table_name}: No records found for opportunity_id={test_opportunity_id}")

                except Exception as e:
                    print(f"  ❌ {table_name}: Error - {e}")

        print(f"\n🎯 DIAGNOSIS:")
        if missing_enrichment_tables:
            print(f"  ❌ Missing enrichment tables: {missing_enrichment_tables}")
            print(f"  🔧 Need to run migrations to create missing tables")

        for table_name in existing_enrichment_tables:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                if count == 0:
                    print(f"  ❌ {table_name}: Empty despite test logs showing successful storage")
                    print(f"  🔧 Possible causes: Transaction rollback, wrong ID mapping, table schema mismatch")

        return True

    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Starting specialized enrichment tables inspection...")
    success = inspect_enrichment_tables()

    if not success:
        print("\n❌ Enrichment table inspection failed")
        sys.exit(1)
    else:
        print("\n✅ Enrichment table inspection completed")
        sys.exit(0)