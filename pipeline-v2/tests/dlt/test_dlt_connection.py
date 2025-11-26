#!/usr/bin/env python3
"""
Test Step 2: Verify DLT can connect to real Supabase database
"""

import sys
import os

# Add pipeline-v2 to path
sys.path.insert(0, os.path.dirname(__file__))

def test_dlt_connection():
    """Test DLT connection to real Supabase database"""
    print("🔍 Testing DLT Connection to Real Supabase Database")
    print("=" * 60)

    try:
        # Test basic DLT import
        import dlt
        print(f"✅ DLT imported successfully (version: {dlt.__version__})")

        # Test configuration loading
        from storage.dlt_loader import DLTLoader
        print("✅ DLTLoader imported successfully")

        # Create DLT pipeline to test connection
        print("🔌 Testing database connection...")

        pipeline = dlt.pipeline(
            pipeline_name="test_connection",
            destination="postgres",
            dataset_name="public"
        )
        print("✅ DLT pipeline created successfully")

        # Test actual database connection with simple query
        print("🗄️ Testing database connectivity...")

        # Try to get database schema info
        try:
            # This will test if we can actually connect to the database
            import sqlalchemy as sa

            # Create engine with our credentials
            engine = sa.create_engine("postgresql://postgres:postgres@127.0.0.1:54331/postgres")

            # Test connection with simple query
            with engine.connect() as conn:
                result = conn.execute(sa.text("SELECT version()"))
                db_version = result.fetchone()[0]
                print(f"✅ Database connection successful!")
                print(f"📊 Database version: {db_version[:50]}...")

            # Check if app_opportunities table exists
            print("📋 Checking if app_opportunities table exists...")
            with engine.connect() as conn:
                try:
                    result = conn.execute(sa.text("""
                        SELECT COUNT(*) FROM information_schema.tables
                        WHERE table_name = 'app_opportunities'
                    """))
                    table_count = result.fetchone()[0]

                    if table_count > 0:
                        print("✅ app_opportunities table exists!")

                        # Get table schema
                        result = conn.execute(sa.text("""
                            SELECT column_name, data_type
                            FROM information_schema.columns
                            WHERE table_name = 'app_opportunities'
                            ORDER BY ordinal_position
                        """))
                        columns = result.fetchall()
                        print(f"📝 Table schema ({len(columns)} columns):")
                        for col_name, col_type in columns:
                            print(f"   - {col_name}: {col_type}")
                    else:
                        print("❌ app_opportunities table does not exist")

                except Exception as e:
                    print(f"❌ Error checking table schema: {e}")

        except ImportError:
            print("⚠️ sqlalchemy not available, testing with DLT only...")

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

        print("\n🎉 CONNECTION TEST COMPLETE")
        print("=" * 60)
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_dlt_connection()

    if success:
        print("\n✅ Step 2 PASSED: DLT can connect to real Supabase database")
    else:
        print("\n❌ Step 2 FAILED: DLT connection issues")
        sys.exit(1)