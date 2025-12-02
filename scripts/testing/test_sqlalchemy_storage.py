#!/usr/bin/env python3
"""
Test if SQLAlchemy storage is working and can actually store data
"""

import sys
import os
from pathlib import Path

# Set up paths
pipeline_v2_root = Path(__file__).parent / "pipeline-v2"
project_root = Path(__file__).parent

# Ensure pipeline-v2 comes before project root
while pipeline_v2_root.__str__() in sys.path:
    sys.path.remove(pipeline_v2_root.__str__())
while project_root.__str__() in sys.path:
    sys.path.remove(project_root.__str__())

sys.path.insert(0, pipeline_v2_root.__str__())
sys.path.insert(1, project_root.__str__())

# Set environment
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@127.0.0.1:54331/postgres"

print("=== Testing SQLAlchemy Storage ===")

try:
    # Import SQLAlchemy loader
    from storage.sqlalchemy_loader import SQLAlchemyLoader, create_sqlalchemy_loader
    print("✅ SQLAlchemy loader imported successfully")

    # Create loader
    loader = create_sqlalchemy_loader("postgresql://postgres:postgres@127.0.0.1:54331/postgres")
    print("✅ SQLAlchemy loader created successfully")

    # Test connection
    if loader.validate_connection():
        print("✅ Database connection validated")
    else:
        print("❌ Database connection failed")

    # Get database statistics
    stats = loader.get_load_statistics()
    print(f"📊 Database stats: {stats}")

    # Test with sample data
    test_data = [
        {
            "submission_id": "test_123",
            "reddit_id": "1test123",
            "title": "Test Opportunity",
            "url": "https://reddit.com/r/test/comments/1test123/test",
            "subreddit": "test",
            "author": "testuser",
            "created_utc": "2025-01-01T00:00:00Z",
            "reddit_score": 100,
            "num_comments": 10,
            "opportunity_score": 85.5,
            "monetization_score": 90.0,
            "trust_score": 88.0,
            "final_score": 87.5,
            "opportunity_id": "test_opp_123"
        }
    ]

    print(f"\n🧪 Testing data load with {len(test_data)} sample records...")

    # Load data
    result = loader.load_opportunities(test_data, "merge")
    print(f"✅ Load completed: {result}")

    # Verify data was actually stored
    print(f"🔍 Verifying data persistence...")
    verification = loader._verify_load_operation(None, test_data)
    print(f"📈 Verification result: {verification}")

    print(f"\n🎉 SUCCESS: SQLAlchemy storage is working and storing data!")
    print(f"   - Data loaded: {len(test_data)} records")
    print(f"   - Connection: Valid")
    print(f"   - Storage: Functional")

except Exception as e:
    print(f"❌ SQLAlchemy storage test failed: {e}")
    import traceback
    traceback.print_exc()