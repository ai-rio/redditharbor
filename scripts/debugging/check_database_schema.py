#!/usr/bin/env python3
"""Check the actual database schema for app_opportunities table"""

import sys
import os
from pathlib import Path

# Add pipeline-v2 to path
pipeline_v2_root = Path(__file__).parent / "pipeline-v2"
sys.path.insert(0, str(pipeline_v2_root))

os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"

try:
    from sqlalchemy import create_engine, text
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    print("=== Checking Database Schema ===")

    # Create engine
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as conn:
        print("\n📋 Table structure for app_opportunities:")

        # Get table columns
        result = conn.execute(text("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'app_opportunities'
            ORDER BY ordinal_position
        """))

        columns = result.fetchall()
        if columns:
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        else:
            print("  ❌ No columns found - table might not exist")

        print(f"\n📊 Total columns: {len(columns)}")

        # Check if table exists and has data
        count_result = conn.execute(text("SELECT COUNT(*) FROM app_opportunities"))
        record_count = count_result.fetchone()[0]
        print(f"📈 Records in app_opportunities: {record_count}")

        # Show a sample of existing data if any
        if record_count > 0:
            sample_result = conn.execute(text("SELECT * FROM app_opportunities LIMIT 1"))
            sample = sample_result.fetchone()
            if sample:
                print(f"\n🔍 Sample data columns available: {len(sample)} fields")
                # Get column names
                col_names = [desc[0] for desc in result.cursor.description]
                print(f"   Available columns: {col_names}")

except Exception as e:
    print(f"❌ Database schema check failed: {e}")
    import traceback
    traceback.print_exc()