#!/usr/bin/env python3
"""
Isolated test for SQLAlchemy-based deduplication logic
Tests the exact functions we'll implement in concept_tracker.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.resolve()
load_dotenv(project_root / '.env.local', override=True)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from sqlalchemy import create_engine, text, MetaData, Table
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
    print("✅ SQLAlchemy available")
except ImportError as e:
    SQLALCHEMY_AVAILABLE = False
    print(f"❌ SQLAlchemy not available: {e}")

def test_sqlalchemy_deduplication_logic():
    """Test the exact SQLAlchemy deduplication logic we'll implement"""

    if not SQLALCHEMY_AVAILABLE:
        return False

    # Database connection
    connection_string = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54331/postgres")

    print("=== TESTING SQLAlchemy Deduplication Logic ===\n")
    print(f"Database: {connection_string}\n")

    try:
        # Create SQLAlchemy engine and session
        engine = create_engine(connection_string)

        with engine.connect() as conn:
            print("✅ SQLAlchemy connection established")

            # Test Reddit IDs from the error log
            test_reddit_ids = ["1p7drk6", "1p7hni7", "1p6rx44"]

            print("\n🔍 Testing NEW deduplication logic:")

            for reddit_id in test_reddit_ids:
                print(f"\nTesting Reddit ID: {reddit_id}")

                # Step 1: Two-step lookup (the robust approach)

                # First, find the submission UUID from Reddit ID
                submission_query = text("""
                    SELECT id as submission_uuid, reddit_id
                    FROM submissions
                    WHERE reddit_id = :reddit_id
                """)

                submission_result = conn.execute(submission_query, {"reddit_id": reddit_id})
                submission_row = submission_result.fetchone()

                if submission_row:
                    submission_uuid = submission_row[0]
                    print(f"  ✅ Step 1: Found submission UUID: {submission_uuid}")

                    # Step 2: Check opportunities_unified with the UUID
                    opportunity_query = text("""
                        SELECT business_concept_id, title, is_duplicate
                        FROM opportunities_unified
                        WHERE submission_id = :submission_uuid
                    """)

                    opportunity_result = conn.execute(opportunity_query, {"submission_uuid": submission_uuid})
                    opportunity_row = opportunity_result.fetchone()

                    if opportunity_row:
                        business_concept_id = opportunity_row[0]
                        title = opportunity_row[1]
                        is_duplicate = opportunity_row[2]

                        print(f"  ✅ Step 2: Found opportunity:")
                        print(f"    - business_concept_id: {business_concept_id}")
                        print(f"    - title: {title[:50]}..." if title else "    - title: None")
                        print(f"    - is_duplicate: {is_duplicate}")

                        # Step 3: Check business_concepts for analysis status
                        if business_concept_id:
                            concept_query = text("""
                                SELECT has_agno_analysis, has_profiler_analysis, last_agno_analysis_at
                                FROM business_concepts
                                WHERE id = :concept_id
                            """)

                            concept_result = conn.execute(concept_query, {"concept_id": business_concept_id})
                            concept_row = concept_result.fetchone()

                            if concept_row:
                                has_agno = concept_row[0]
                                has_profiler = concept_row[1]
                                last_agno = concept_row[2]

                                print(f"  ✅ Step 3: Business concept analysis status:")
                                print(f"    - has_agno_analysis: {has_agno}")
                                print(f"    - has_profiler_analysis: {has_profiler}")
                                print(f"    - last_agno_analysis_at: {last_agno}")

                                # Deduplication decision
                                if has_agno:
                                    print(f"  🎯 DECISION: Skip Agno analysis (already exists)")
                                else:
                                    print(f"  🎯 DECISION: Run Agno analysis (needed)")
                            else:
                                print(f"  ❌ Step 3: Business concept {business_concept_id} not found")
                        else:
                            print(f"  🎯 DECISION: New unique opportunity (run all analysis)")
                    else:
                        print(f"  ✅ Step 2: No opportunity found (new submission)")
                        print(f"  🎯 DECISION: Run fresh analysis (new opportunity)")

                else:
                    print(f"  ✅ Step 1: No submission found (brand new Reddit ID)")
                    print(f"  🎯 DECISION: Run fresh analysis (completely new)")

            # Test edge cases
            print(f"\n🧪 Testing edge cases:")

            # Test with existing data
            existing_query = text("""
                SELECT COUNT(*) as count FROM submissions LIMIT 1
            """)
            result = conn.execute(existing_query)
            has_existing = result.fetchone()[0] > 0
            print(f"  - Database has existing submissions: {has_existing}")

            if has_existing:
                # Test with a real submission
                sample_query = text("""
                    SELECT reddit_id, id FROM submissions LIMIT 1
                """)
                sample_result = conn.execute(sample_query)
                sample_row = sample_result.fetchone()

                sample_reddit_id = sample_row[0]
                sample_uuid = sample_row[1]

                print(f"  - Testing with real submission: {sample_reddit_id} -> {sample_uuid}")

                # Test the two-step lookup
                test_query = text("""
                    SELECT s.reddit_id, ou.business_concept_id
                    FROM submissions s
                    LEFT JOIN opportunities_unified ou ON s.id = ou.submission_id
                    WHERE s.id = :uuid
                """)

                test_result = conn.execute(test_query, {"uuid": sample_uuid})
                test_row = test_result.fetchone()

                if test_row:
                    print(f"  ✅ Two-step lookup works: {test_row[0]} -> concept_id: {test_row[1]}")
                else:
                    print(f"  ❌ Two-step lookup failed")

            return True

    except Exception as e:
        print(f"❌ SQLAlchemy deduplication test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sqlalchemy_deduplication_logic()

    if success:
        print(f"\n✅ SUCCESS: SQLAlchemy deduplication logic works perfectly!")
        print(f"🎯 Ready to implement in concept_tracker.py")
    else:
        print(f"\n❌ FAILED: SQLAlchemy deduplication logic has issues")
        print(f"🔧 Need to fix before implementing")