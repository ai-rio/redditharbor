#!/usr/bin/env python3
"""
Test SQLAlchemy direct database access to verify it can access opportunities_unified
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.local
project_root = Path(__file__).parent.resolve()
load_dotenv(project_root / '.env.local', override=True)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import SQLAlchemy components directly
try:
    from sqlalchemy import create_engine, text, MetaData, Table
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
    print("✅ SQLAlchemy available")
except ImportError as e:
    SQLALCHEMY_AVAILABLE = False
    print(f"❌ SQLAlchemy not available: {e}")

def test_sqlalchemy_access():
    """Test direct SQLAlchemy database access"""

    if not SQLALCHEMY_AVAILABLE:
        return False

    # Connection string from environment or default
    connection_string = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres")

    print(f"🔗 Testing connection to: {connection_string}")

    try:
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        print("✅ SQLAlchemy engine created")

        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection established")

            # Test direct SQL query
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE '%opportunity%'
                ORDER BY table_name
            """))

            tables = result.fetchall()
            print(f"📋 Found {len(tables)} opportunity-related tables:")
            for table in tables:
                print(f"  - {table[0]}")

            # Test direct access to opportunities_unified
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM opportunities_unified
                """))
                count = result.fetchone()[0]
                print(f"✅ opportunities_unified accessible: {count} records")
            except Exception as e:
                print(f"❌ opportunities_unified access failed: {e}")
                return False

            # Test business_concepts access
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM business_concepts
                """))
                count = result.fetchone()[0]
                print(f"✅ business_concepts accessible: {count} records")
            except Exception as e:
                print(f"❌ business_concepts access failed: {e}")
                return False

            # Test the specific deduplication query that was failing
            test_reddit_ids = ["1p7drk6", "1p7hni7", "1p6rx44"]

            print(f"\n🔍 Testing deduplication queries:")
            for reddit_id in test_reddit_ids:
                try:
                    # Two-step lookup approach
                    result = conn.execute(text("""
                        SELECT s.id as submission_uuid, ou.business_concept_id
                        FROM submissions s
                        LEFT JOIN opportunities_unified ou ON s.id = ou.submission_id
                        WHERE s.reddit_id = :reddit_id
                    """), {"reddit_id": reddit_id})

                    row = result.fetchone()
                    if row:
                        print(f"  ✅ {reddit_id}: found submission_uuid={row[0]}, business_concept_id={row[1]}")
                    else:
                        print(f"  ✅ {reddit_id}: new submission (no existing record)")

                except Exception as e:
                    print(f"  ❌ {reddit_id}: query failed - {e}")
                    return False

        return True

    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing SQLAlchemy Direct Database Access ===\n")

    success = test_sqlalchemy_access()

    if success:
        print(f"\n✅ CONCLUSION: SQLAlchemy can access opportunities_unified table!")
        print("This means SQLAlchemy should solve the Supabase REST API limitation.")
    else:
        print(f"\n❌ CONCLUSION: SQLAlchemy has issues accessing the database")

    print(f"\n📋 RECOMMENDATION:")
    if success:
        print("1. Use SQLAlchemy for deduplication queries instead of Supabase client")
        print("2. This bypasses the PostgREST table access limitations")
        print("3. Provides direct PostgreSQL access to all tables")
    else:
        print("1. Check DATABASE_URL configuration")
        print("2. Verify database connection credentials")
        print("3. Ensure PostgreSQL is running on port 54322")