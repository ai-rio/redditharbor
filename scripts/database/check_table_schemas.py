#!/usr/bin/env python3
"""Check table schemas to understand the structure"""

import asyncio
import asyncpg
from config.settings import get_database_config

async def check_schemas():
    """Check schemas of key tables"""
    db_config = get_database_config()

    try:
        conn = await asyncpg.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database
        )

        print("🔍 Checking table schemas...\n")

        # Check opportunities table
        print("📋 opportunities table:")
        opp_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'opportunities'
            ORDER BY ordinal_position
        """)
        for col in opp_columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")

        print("\n📋 app_opportunities table:")
        app_opp_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'app_opportunities'
            ORDER BY ordinal_position
        """)
        for col in app_opp_columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")

        print("\n📋 workflow_results table:")
        wr_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'workflow_results'
            ORDER BY ordinal_position
        """)
        for col in wr_columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")

        print("\n📋 submissions table:")
        sub_columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'submissions'
            ORDER BY ordinal_position
        """)
        for col in sub_columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")

        await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_schemas())