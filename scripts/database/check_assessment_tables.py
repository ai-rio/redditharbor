#!/usr/bin/env python3
"""Check assessment tables schema"""

import asyncio
import asyncpg
from config.settings import get_database_config

async def check_assessment_schemas():
    """Check schemas of assessment tables"""
    db_config = get_database_config()

    try:
        conn = await asyncpg.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database
        )

        print("🔍 Checking assessment table schemas...\n")

        # Check opportunity_scores table
        print("📋 opportunity_scores table:")
        try:
            opp_scores_columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'opportunity_scores'
                ORDER BY ordinal_position
            """)
            if opp_scores_columns:
                for col in opp_scores_columns:
                    print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            else:
                print("  - Table does not exist or has no columns")
        except Exception as e:
            print(f"  - ERROR: {e}")

        print("\n📋 market_validations table:")
        try:
            market_val_columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'market_validations'
                ORDER BY ordinal_position
            """)
            if market_val_columns:
                for col in market_val_columns:
                    print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            else:
                print("  - Table does not exist or has no columns")
        except Exception as e:
            print(f"  - ERROR: {e}")

        print("\n📋 score_components table:")
        try:
            score_comp_columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'score_components'
                ORDER BY ordinal_position
            """)
            if score_comp_columns:
                for col in score_comp_columns:
                    print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            else:
                print("  - Table does not exist or has no columns")
        except Exception as e:
            print(f"  - ERROR: {e}")

        await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_assessment_schemas())