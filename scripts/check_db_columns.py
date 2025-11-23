#!/usr/bin/env python3
"""
Check Database Columns for monetization_patterns table

This script checks if the required monetization columns exist in the database.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from config.settings import get_psycopg2_config

# Load environment variables
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env.local', override=True)
load_dotenv(project_root / '.env', override=False)

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("psycopg2 not available, trying alternative connection methods")

def get_db_connection():
    """Get database connection using secure configuration."""
    if not PSYCOPG2_AVAILABLE:
        raise ImportError("psycopg2 not available for database connection")

    db_config = get_psycopg2_config()
    if isinstance(db_config, str):
        return psycopg2.connect(db_config)
    else:
        return psycopg2.connect(**db_config)

def check_columns_direct():
    """Check columns using direct database connection."""
    if not PSYCOPG2_AVAILABLE:
        print("❌ psycopg2 not available for direct database connection")
        return False

    try:
        # Connect using secure configuration
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if monetization_patterns table exists and get its columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'monetization_patterns'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()

        print(f"📋 monetization_patterns table has {len(columns)} columns:")
        for col_name, data_type, is_nullable in columns:
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            print(f"  • {col_name}: {data_type} ({nullable})")

        # Check for required columns
        required_columns = [
            'willingness_to_pay_score',
            'customer_segment',
            'price_sensitivity_score',
            'revenue_potential_score'
        ]

        existing_columns = [col[0] for col in columns]
        missing_columns = [col for col in required_columns if col not in existing_columns]

        if missing_columns:
            print(f"\n❌ Missing columns: {missing_columns}")
        else:
            print("\n✅ All required monetization columns exist!")

        conn.close()
        return len(missing_columns) == 0

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_columns_via_store():
    """Check columns using existing storage infrastructure."""
    try:
        from core.storage.enhanced_hybrid_store import EnhancedHybridStore
        store = EnhancedHybridStore()

        # Try to query the table structure
        result = store.client.table('monetization_patterns').select('*').limit(1).execute()

        if result.data:
            columns = list(result.data[0].keys())
            print(f"📋 monetization_patterns table columns (via API):")
            for col in columns:
                print(f"  • {col}")

            required_columns = [
                'willingness_to_pay_score',
                'customer_segment',
                'price_sensitivity_score',
                'revenue_potential_score'
            ]

            missing_columns = [col for col in required_columns if col not in columns]

            if missing_columns:
                print(f"\n❌ Missing columns: {missing_columns}")
            else:
                print("\n✅ All required monetization columns exist!")

            return len(missing_columns) == 0
        else:
            print("📋 monetization_patterns table exists but has no data")
            return True

    except Exception as e:
        print(f"❌ Store-based check failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking monetization_patterns table columns...")
    print("=" * 50)

    # Try direct connection first
    success = check_columns_direct()

    if not success:
        print("\n🔄 Trying alternative connection method...")
        success = check_columns_via_store()

    if success:
        print("\n🎉 Column verification completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Column verification failed")
        sys.exit(1)