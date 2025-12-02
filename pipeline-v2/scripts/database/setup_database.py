#!/usr/bin/env python3
"""
Step 3: Create app_opportunities table in Supabase database
"""

import sys
import os
import sqlalchemy as sa

# Add pipeline-v2 to path
sys.path.insert(0, os.path.dirname(__file__))

def create_app_opportunities_table():
    """Create the app_opportunities table if it doesn't exist"""
    print("🏗️ Creating app_opportunities table in Supabase")
    print("=" * 50)

    try:
        # Connect to database
        engine = sa.create_engine("postgresql://postgres:postgres@127.0.0.1:54331/postgres")
        print("✅ Database connection established")

        with engine.connect() as conn:
            # Create table schema
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS app_opportunities (
                submission_id VARCHAR(20) PRIMARY KEY,
                title VARCHAR(1000),
                url VARCHAR(2000),
                subreddit VARCHAR(100),
                author VARCHAR(100),
                score INTEGER,
                created_utc TIMESTAMP,
                num_comments INTEGER,

                -- AI Analysis Fields
                opportunity_score FLOAT,
                opportunity_category VARCHAR(50),
                opportunity_reasoning TEXT,

                -- Monetization Analysis Fields
                monetization_score FLOAT,
                monetization_keywords TEXT[],
                monetization_confidence FLOAT,

                -- Profiling Analysis Fields
                user_intent VARCHAR(100),
                user_persona VARCHAR(100),
                expertise_level VARCHAR(50),

                -- Trust Validation Fields
                trust_score FLOAT,
                trust_badge VARCHAR(20),
                activity_score FLOAT,
                engagement_score FLOAT,
                trend_score FLOAT,
                validity_score FLOAT,
                quality_score FLOAT,
                ai_confidence_score FLOAT,

                -- Metadata
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            conn.execute(sa.text(create_table_sql))
            print("✅ app_opportunities table created successfully")

            # Create index for better query performance
            create_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_app_opportunities_trust_score ON app_opportunities(trust_score DESC);",
                "CREATE INDEX IF NOT EXISTS idx_app_opportunities_subreddit ON app_opportunities(subreddit);",
                "CREATE INDEX IF NOT EXISTS idx_app_opportunities_processed_at ON app_opportunities(processed_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_app_opportunities_opportunity_score ON app_opportunities(opportunity_score DESC);"
            ]

            for index_sql in create_indexes_sql:
                conn.execute(sa.text(index_sql))
                print(f"✅ Index created successfully")

            # Verify table exists and show schema
            print("📋 Verifying table creation...")
            result = conn.execute(sa.text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'app_opportunities'
                ORDER BY ordinal_position
            """))

            columns = result.fetchall()
            print(f"📝 Table schema ({len(columns)} columns):")
            for col_name, col_type, nullable in columns:
                null_indicator = "NULL" if nullable == "YES" else "NOT NULL"
                print(f"   - {col_name}: {col_type} ({null_indicator})")

            # Test inserting a sample record
            print("\n🧪 Testing sample record insertion...")
            from datetime import datetime

            test_record = {
                'submission_id': 'test_1234567890',
                'title': 'Test Opportunity',
                'url': 'https://reddit.com/test',
                'subreddit': 'test',
                'author': 'test_user',
                'score': 100,
                'created_utc': datetime.now(),
                'num_comments': 10,
                'opportunity_score': 75.5,
                'trust_score': 80.0,
                'trust_badge': 'SILVER'
            }

            # Build INSERT statement
            columns_str = ', '.join(test_record.keys())
            values_str = ', '.join([f":{k}" for k in test_record.keys()])

            insert_sql = f"""
            INSERT INTO app_opportunities ({columns_str})
            VALUES ({values_str})
            ON CONFLICT (submission_id) DO NOTHING;
            """

            conn.execute(sa.text(insert_sql), test_record)
            print("✅ Sample record inserted successfully")

            # Clean up test record
            conn.execute(sa.text("DELETE FROM app_opportunities WHERE submission_id = 'test_1234567890'"))
            print("🧹 Test record cleaned up")

        print("\n🎉 TABLE SETUP COMPLETE")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

if __name__ == "__main__":
    success = create_app_opportunities_table()

    if success:
        print("\n✅ Step 3 PASSED: app_opportunities table created successfully")
    else:
        print("\n❌ Step 3 FAILED: Could not create table")
        sys.exit(1)