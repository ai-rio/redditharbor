#!/usr/bin/env python3
"""
Database Schema Investigation Tool

This script investigates the actual app_opportunities table structure to fix
the SQLAlchemy schema alignment issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import sqlalchemy
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    print("SQLAlchemy not available - cannot investigate schema")
    sys.exit(1)

def investigate_database_schema():
    """Investigate the actual database schema for app_opportunities table"""

    # Connection string
    connection_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    try:
        # Create engine
        engine = create_engine(connection_string)

        with engine.connect() as conn:
            print("🔍 INVESTIGATING DATABASE SCHEMA")
            print("=" * 60)

            # 1. Check if table exists
            table_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'app_opportunities'
                )
            """)).scalar()

            print(f"\n1. Table exists: {table_exists}")

            if not table_exists:
                print("❌ app_opportunities table does not exist!")
                return

            # 2. Get actual column information
            print("\n2. ACTUAL TABLE COLUMNS:")
            columns_result = conn.execute(text("""
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default,
                    ordinal_position
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'app_opportunities'
                ORDER BY ordinal_position
            """)).fetchall()

            actual_columns = []
            for col in columns_result:
                col_info = {
                    "name": col[0],
                    "type": col[1],
                    "max_length": col[2],
                    "nullable": col[3] == "YES",
                    "default": col[4],
                    "position": col[5]
                }
                actual_columns.append(col_info)
                nullable_str = "NULL" if col_info["nullable"] else "NOT NULL"
                default_str = f" DEFAULT {col_info['default']}" if col_info['default'] else ""
                print(f"   {col_info['position']:2d}. {col_info['name']:25s} {col_info['type']:15s} {nullable_str:8s}{default_str}")

            # 3. Get constraints information
            print("\n3. TABLE CONSTRAINTS:")
            try:
                constraints_result = conn.execute(text("""
                    SELECT
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name
                    FROM information_schema.table_constraints tc
                    LEFT JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = 'app_opportunities'
                    ORDER BY tc.constraint_type, tc.constraint_name
                """)).fetchall()

                constraints = {}
                for constraint in constraints_result:
                    constraint_name = constraint[0]
                    constraint_type = constraint[1]
                    column_name = constraint[2]

                    if constraint_type not in constraints:
                        constraints[constraint_type] = []

                    constraints[constraint_type].append({
                        "name": constraint_name,
                        "column": column_name
                    })

                for constraint_type, constraint_list in constraints.items():
                    print(f"   {constraint_type}:")
                    for constraint in constraint_list:
                        print(f"     - {constraint['name']} on {constraint['column']}")

            except Exception as e:
                print(f"   Could not retrieve constraints: {e}")

            # 4. Check for indexes
            print("\n4. TABLE INDEXES:")
            try:
                indexes_result = conn.execute(text("""
                    SELECT
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    AND tablename = 'app_opportunities'
                    ORDER BY indexname
                """)).fetchall()

                for index in indexes_result:
                    print(f"   {index[0]}:")
                    print(f"     {index[1]}")

            except Exception as e:
                print(f"   Could not retrieve indexes: {e}")

            # 5. Sample data investigation
            print("\n5. SAMPLE DATA INVESTIGATION:")
            try:
                sample_result = conn.execute(text("""
                    SELECT * FROM app_opportunities LIMIT 1
                """)).fetchone()

                if sample_result:
                    print("   Sample record found:")
                    for i, (column_name, column_value) in enumerate(zip([col['name'] for col in actual_columns], sample_result)):
                        value_str = str(column_value) if column_value is not None else "NULL"
                        if len(value_str) > 50:
                            value_str = value_str[:47] + "..."
                        print(f"     {column_name}: {value_str}")
                else:
                    print("   No data in table")

            except Exception as e:
                print(f"   Could not retrieve sample data: {e}")

            # 6. Identify DLT-specific columns
            print("\n6. DLT-SPECIFIC COLUMNS ANALYSIS:")
            dlt_columns = [col for col in actual_columns if col['name'].startswith('_dlt_')]
            if dlt_columns:
                print("   DLT-specific columns found:")
                for col in dlt_columns:
                    nullable_str = "NULL" if col["nullable"] else "NOT NULL"
                    default_str = f" DEFAULT {col['default']}" if col['default'] else ""
                    print(f"     - {col['name']}: {col['type']} {nullable_str}{default_str}")
            else:
                print("   No DLT-specific columns found")

            # 7. Column compatibility analysis
            print("\n7. SCHEMA COMPATIBILITY ANALYSIS:")

            # Expected columns from SQLAlchemy loader
            expected_columns = [
                '_dlt_load_id', '_dlt_id', 'submission_id', 'title', 'subreddit',
                'upvotes', 'comments_count', 'score', 'created_utc', 'quality_score',
                'trust_score', 'opportunity_score', 'monetization_score', 'core_functions',
                'app_concept', 'problem_description', 'trust_level', 'trust_badges',
                'processed_at', 'pipeline_version'
            ]

            actual_column_names = [col['name'] for col in actual_columns]

            print("   Expected vs Actual:")
            missing_columns = [col for col in expected_columns if col not in actual_column_names]
            extra_columns = [col for col in actual_column_names if col not in expected_columns and not col.startswith('_dlt_')]

            if missing_columns:
                print(f"     ❌ Missing columns: {missing_columns}")

            if extra_columns:
                print(f"     ⚠️  Extra columns: {extra_columns}")

            if not missing_columns and not extra_columns:
                print("     ✅ Perfect schema match!")
            elif missing_columns:
                print("     ❌ Schema mismatch - SQLAlchemy loader will fail!")
            else:
                print("     ⚠️  Schema compatible but with extra columns")

            return {
                "table_exists": table_exists,
                "columns": actual_columns,
                "missing_columns": missing_columns,
                "extra_columns": extra_columns
            }

    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    result = investigate_database_schema()

    if result:
        print("\n" + "=" * 60)
        print("🎯 SCHEMA INVESTIGATION COMPLETE")
        print("=" * 60)

        if result["missing_columns"]:
            print("🚨 CRITICAL ISSUES FOUND:")
            print(f"   Missing columns: {result['missing_columns']}")
            print("   SQLAlchemy loader needs to be updated!")
        else:
            print("✅ Schema appears compatible")
    else:
        print("❌ Schema investigation failed")