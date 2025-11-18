#!/usr/bin/env python3
"""Check all tables to understand current state"""

import asyncio
import asyncpg
from config.settings import get_database_config

async def check_all_tables():
    """Check all tables"""
    db_config = get_database_config()

    try:
        conn = await asyncpg.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database
        )

        print("🔍 Checking all tables...\n")

        # List all tables
        all_tables = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)

        print(f"📋 All tables ({len(all_tables)} total):")
        for table in all_tables:
            # Get row count
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['tablename']}")
                print(f"  - {table['tablename']}: {count} rows")
            except Exception as e:
                print(f"  - {table['tablename']}: ERROR - {e}")

        # List all views
        all_views = await conn.fetch("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        print(f"\n📋 All views ({len(all_views)} total):")
        for view in all_views:
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {view['table_name']}")
                print(f"  - {view['table_name']}: {count} rows")
            except Exception as e:
                print(f"  - {view['table_name']}: ERROR - {e}")

        await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_tables())