#!/usr/bin/env python3
"""
Test Schema Validation for Deduplication Integration Migration
Validates that all schema changes were applied correctly
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import psycopg2

# Database connection parameters
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 54322,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'postgres'
}

def test_business_concepts_columns():
    """Test that business_concepts table has the new deduplication tracking columns"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Check if columns exist
        cur.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'business_concepts'
            AND column_name IN (
                'has_agno_analysis', 'agno_analysis_count', 'last_agno_analysis_at',
                'agno_avg_wtp_score', 'has_ai_profile', 'ai_profile_count', 'last_ai_profile_at'
            )
            ORDER BY column_name;
        """)

        columns = cur.fetchall()
        expected_columns = {
            'agno_analysis_count': ('integer', None, 'YES'),
            'agno_avg_wtp_score': ('numeric', None, 'YES'),
            'ai_profile_count': ('integer', None, 'YES'),
            'has_ai_profile': ('boolean', 'false', 'YES'),
            'has_agno_analysis': ('boolean', 'false', 'YES'),
            'last_ai_profile_at': ('timestamp with time zone', None, 'YES'),
            'last_agno_analysis_at': ('timestamp with time zone', None, 'YES')
        }

        print("✓ Business Concepts Columns Check:")
        success = True

        for column_name, data_type, default, nullable in columns:
            if column_name in expected_columns:
                expected_type, expected_default, expected_nullable = expected_columns[column_name]
                print(f"  - {column_name}: {data_type} (OK)")

                # Validate type
                if data_type != expected_type:
                    print(f"    ✗ Expected type {expected_type}, got {data_type}")
                    success = False

                # Validate nullable
                if nullable != expected_nullable:
                    print(f"    ✗ Expected nullable {expected_nullable}, got {nullable}")
                    success = False
            else:
                print(f"  - {column_name}: {data_type} (Unexpected)")
                success = False

        cur.close()
        conn.close()

        return success

    except Exception as e:
        print(f"✗ Error checking business_concepts columns: {e}")
        return False

def test_llm_monetization_analysis_table():
    """Test that llm_monetization_analysis table exists with proper structure"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'llm_monetization_analysis'
            );
        """)
        table_exists = cur.fetchone()[0]

        if not table_exists:
            print("✗ llm_monetization_analysis table does not exist")
            return False

        print("✓ llm_monetization_analysis table exists")

        # Check for deduplication tracking columns
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'llm_monetization_analysis'
            AND column_name IN ('copied_from_primary', 'primary_opportunity_id', 'business_concept_id')
            ORDER BY column_name;
        """)

        columns = cur.fetchall()
        expected_columns = {
            'business_concept_id': 'bigint',
            'copied_from_primary': 'boolean',
            'primary_opportunity_id': 'uuid'
        }

        print("✓ LLM Monetization Analysis Deduplication Columns:")
        success = True

        for column_name, data_type in columns:
            if column_name in expected_columns:
                expected_type = expected_columns[column_name]
                if data_type == expected_type:
                    print(f"  - {column_name}: {data_type} (OK)")
                else:
                    print(f"  ✗ {column_name}: Expected {expected_type}, got {data_type}")
                    success = False
            else:
                print(f"  - {column_name}: {data_type} (Unexpected)")

        cur.close()
        conn.close()

        return success

    except Exception as e:
        print(f"✗ Error checking llm_monetization_analysis table: {e}")
        return False

def test_opportunities_unified_columns():
    """Test that opportunities_unified table has deduplication tracking columns"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Check for deduplication tracking columns
        cur.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'opportunities_unified'
            AND column_name IN ('copied_from_primary', 'primary_opportunity_id')
            ORDER BY column_name;
        """)

        columns = cur.fetchall()
        expected_columns = {
            'copied_from_primary': ('boolean', 'false'),
            'primary_opportunity_id': ('uuid', None)
        }

        print("✓ Opportunities Unified Deduplication Columns:")
        success = True

        for column_name, data_type, default in columns:
            if column_name in expected_columns:
                expected_type, expected_default = expected_columns[column_name]
                if data_type == expected_type:
                    print(f"  - {column_name}: {data_type} (OK)")

                    # Check default if specified
                    if expected_default is not None:
                        actual_default = default.split('::')[0] if default else None
                        if actual_default != expected_default:
                            print(f"    ✗ Expected default {expected_default}, got {actual_default}")
                            success = False
                else:
                    print(f"  ✗ {column_name}: Expected {expected_type}, got {data_type}")
                    success = False
            else:
                print(f"  - {column_name}: {data_type} (Unexpected)")

        cur.close()
        conn.close()

        return success

    except Exception as e:
        print(f"✗ Error checking opportunities_unified columns: {e}")
        return False

def test_indexes():
    """Test that the required indexes were created"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Expected indexes
        expected_indexes = [
            ('idx_business_concepts_agno_analysis', 'business_concepts'),
            ('idx_business_concepts_ai_profile', 'business_concepts'),
            ('idx_business_concepts_wtp_score', 'business_concepts'),
            ('idx_llm_analysis_deduplication', 'llm_monetization_analysis'),
            ('idx_llm_analysis_business_concept', 'llm_monetization_analysis'),
            ('idx_opportunities_unified_deduplication', 'opportunities_unified'),
            ('idx_llm_analysis_opportunity', 'llm_monetization_analysis')
        ]

        print("✓ Indexes Check:")
        success = True

        for index_name, table_name in expected_indexes:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE tablename = %s AND indexname = %s
                );
            """, (table_name, index_name))

            exists = cur.fetchone()[0]
            if exists:
                print(f"  - {index_name}: OK")
            else:
                print(f"  ✗ {index_name}: Missing")
                success = False

        cur.close()
        conn.close()

        return success

    except Exception as e:
        print(f"✗ Error checking indexes: {e}")
        return False

def test_views():
    """Test that the required views were created"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Expected views
        expected_views = [
            'agno_analysis_stats',
            'deduplication_integration_stats'
        ]

        print("✓ Views Check:")
        success = True

        for view_name in expected_views:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views
                    WHERE table_name = %s
                );
            """, (view_name,))

            exists = cur.fetchone()[0]
            if exists:
                print(f"  - {view_name}: OK")
            else:
                print(f"  ✗ {view_name}: Missing")
                success = False

        cur.close()
        conn.close()

        return success

    except Exception as e:
        print(f"✗ Error checking views: {e}")
        return False

def test_foreign_key_constraints():
    """Test that foreign key constraints exist"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Expected foreign key constraints
        expected_constraints = [
            ('fk_llm_analysis_business_concept', 'llm_monetization_analysis'),
            ('fk_llm_analysis_primary_opportunity', 'llm_monetization_analysis'),
            ('fk_opportunities_primary_opportunity', 'opportunities_unified')
        ]

        print("✓ Foreign Key Constraints Check:")
        success = True

        for constraint_name, table_name in expected_constraints:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.table_constraints
                    WHERE constraint_name = %s
                    AND table_name = %s
                    AND constraint_type = 'FOREIGN KEY'
                );
            """, (constraint_name, table_name))

            exists = cur.fetchone()[0]
            if exists:
                print(f"  - {constraint_name}: OK")
            else:
                print(f"  ✗ {constraint_name}: Missing")
                success = False

        cur.close()
        conn.close()

        return success

    except Exception as e:
        print(f"✗ Error checking foreign key constraints: {e}")
        return False

def test_functions():
    """Test that helper functions were created"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Expected functions
        expected_functions = [
            'update_agno_analysis_tracking',
            'update_ai_profile_tracking'
        ]

        print("✓ Functions Check:")
        success = True

        for function_name in expected_functions:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_proc
                    WHERE proname = %s
                );
            """, (function_name,))

            exists = cur.fetchone()[0]
            if exists:
                print(f"  - {function_name}: OK")
            else:
                print(f"  ✗ {function_name}: Missing")
                success = False

        cur.close()
        conn.close()

        return success

    except Exception as e:
        print(f"✗ Error checking functions: {e}")
        return False

def test_data_integrity():
    """Test basic data integrity with sample data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("✓ Data Integrity Tests:")

        # Test 1: Create a test business concept
        cur.execute("""
            INSERT INTO business_concepts (concept_name, concept_fingerprint)
            VALUES ('Test Concept', SHA256('test concept'))
            RETURNING id;
        """)
        concept_id = cur.fetchone()[0]
        print(f"  - Created test business concept: ID {concept_id}")

        # Test 2: Create a test opportunity
        cur.execute("""
            INSERT INTO opportunities_unified (title, description)
            VALUES ('Test Opportunity', 'Test description')
            RETURNING id;
        """)
        opportunity_id = cur.fetchone()[0]
        print(f"  - Created test opportunity: ID {opportunity_id}")

        # Test 3: Link opportunity to concept
        cur.execute("""
            UPDATE opportunities_unified
            SET business_concept_id = %s
            WHERE id = %s;
        """, (concept_id, opportunity_id))
        print(f"  - Linked opportunity to concept")

        # Test 4: Create llm_monetization_analysis record
        cur.execute("""
            INSERT INTO llm_monetization_analysis (
                opportunity_id, llm_monetization_score, keyword_monetization_score
            ) VALUES (%s, 75.5, 68.2);
        """, (opportunity_id,))
        print(f"  - Created LLM monetization analysis")

        # Test 5: Update Agno analysis tracking
        cur.execute("SELECT update_agno_analysis_tracking(%s, true, 85.5);", (concept_id,))
        result = cur.fetchone()[0]
        if result:
            print(f"  - Updated Agno analysis tracking successfully")
        else:
            print(f"  ✗ Failed to update Agno analysis tracking")

        # Test 6: Update AI profile tracking
        cur.execute("SELECT update_ai_profile_tracking(%s, true);", (concept_id,))
        result = cur.fetchone()[0]
        if result:
            print(f"  - Updated AI profile tracking successfully")
        else:
            print(f"  ✗ Failed to update AI profile tracking")

        # Test 7: Verify view queries work
        cur.execute("SELECT * FROM agno_analysis_stats LIMIT 1;")
        cur.fetchone()
        print(f"  - agno_analysis_stats view works")

        cur.execute("SELECT * FROM deduplication_integration_stats WHERE table_name = 'business_concepts';")
        cur.fetchone()
        print(f"  - deduplication_integration_stats view works")

        # Clean up test data
        cur.execute("DELETE FROM llm_monetization_analysis WHERE opportunity_id = %s;", (opportunity_id,))
        cur.execute("DELETE FROM opportunities_unified WHERE id = %s;", (opportunity_id,))
        cur.execute("DELETE FROM business_concepts WHERE id = %s;", (concept_id,))
        print(f"  - Cleaned up test data")

        conn.commit()
        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"✗ Error in data integrity test: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

def main():
    """Run all schema validation tests"""
    print("Deduplication Integration Schema Validation")
    print("=" * 50)

    tests = [
        ("Business Concepts Columns", test_business_concepts_columns),
        ("LLM Monetization Analysis Table", test_llm_monetization_analysis_table),
        ("Opportunities Unified Columns", test_opportunities_unified_columns),
        ("Indexes", test_indexes),
        ("Views", test_views),
        ("Foreign Key Constraints", test_foreign_key_constraints),
        ("Functions", test_functions),
        ("Data Integrity", test_data_integrity)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name))
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<40} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All schema validation tests passed!")
        print("The deduplication integration migration was applied successfully.")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed.")
        print("Please check the migration errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())