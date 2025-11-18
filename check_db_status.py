#!/usr/bin/env python3
"""Quick database status check"""

import asyncio
import asyncpg
from config.settings import get_database_config

async def check_db():
    """Check database status and tables"""
    db_config = get_database_config()

    try:
        conn = await asyncpg.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database
        )

        print("✅ Database connection successful")

        # List tables
        tables = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        print(f"\n📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['tablename']}")

        # Check for key tables we expect
        key_tables = ['opportunities', 'app_opportunities', 'workflow_results', 'submissions', 'comments']
        existing_key_tables = [t['tablename'] for t in tables if t['tablename'] in key_tables]

        print(f"\n🔑 Key tables found: {len(existing_key_tables)}/{len(key_tables)}")
        for table in existing_key_tables:
            print(f"  - {table}")

        await conn.close()

    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())