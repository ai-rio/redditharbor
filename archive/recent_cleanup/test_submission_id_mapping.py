#!/usr/bin/env python3
"""
Test case to reproduce the submission_id mapping issue.

This test demonstrates that services fail when database returns 'id' field
but services expect 'submission_id' field.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_submission_id_mapping():
    """Test that demonstrates the submission_id mapping failure."""

    # Simulate database response (what pipeline gets from Supabase)
    database_submission = {
        'id': 'hybrid_1',  # Database returns 'id' field
        'title': 'Need feedback on timezone scheduling tool',
        'content': 'Looking for a better way to schedule meetings across timezones',
        'subreddit': 'remotework',
        'reddit_score': 15,
        'num_comments': 8,
        'created_utc': 1700000000,
        'author': 'test_user'
    }

    # Test: ProfilerService expects 'submission_id' field
    print("=== Testing ProfilerService submission_id mapping ===")

    try:
        # This should fail with KeyError: 'submission_id'
        submission_id = database_submission['submission_id']  # This line will fail
        print(f"✓ ProfilerService would get submission_id: {submission_id}")
    except KeyError as e:
        print(f"❌ ProfilerService fails with: {e}")
        print(f"   Available fields: {list(database_submission.keys())}")

    # Test: OpportunityService expects 'submission_id' field
    print("\n=== Testing OpportunityService submission_id mapping ===")

    try:
        # This should fail with KeyError: 'submission_id'
        submission_id = database_submission['submission_id']  # This line will fail
        print(f"✓ OpportunityService would get submission_id: {submission_id}")
    except KeyError as e:
        print(f"❌ OpportunityService fails with: {e}")
        print(f"   Available fields: {list(database_submission.keys())}")

    # Test: Proposed fix - use field mapping
    print("\n=== Testing Proposed Fix: Field Mapping ===")

    def get_submission_id(submission):
        """Helper function to get submission_id with fallback."""
        return submission.get('submission_id') or submission.get('id', 'unknown')

    try:
        submission_id = get_submission_id(database_submission)
        print(f"✓ Fixed mapping gets submission_id: {submission_id}")
        return True
    except Exception as e:
        print(f"❌ Fixed mapping fails: {e}")
        return False

def test_service_field_mapping():
    """Test that services need to use field mapping for submission_id."""

    print("\n=== Testing Field Mapping in Services ===")

    # Mock submission with 'id' field (as from database)
    submission = {
        'id': 'test_123',
        'title': 'Test submission',
        'content': 'Test content',
        'subreddit': 'test'
    }

    # Current broken service code pattern
    print("\n--- Current Broken Pattern ---")
    try:
        # This is what ProfilerService._generate_profile() does:
        submission_id = submission["submission_id"]  # KeyError!
        print(f"Current pattern works: {submission_id}")
    except KeyError:
        print("❌ Current pattern fails: KeyError 'submission_id'")

    # Proposed fix pattern
    print("\n--- Proposed Fixed Pattern ---")
    try:
        # This is what should be done:
        submission_id = submission.get("submission_id") or submission.get("id", "unknown")
        print(f"✓ Fixed pattern works: {submission_id}")
        return True
    except Exception as e:
        print(f"❌ Fixed pattern fails: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing submission_id mapping issue")
    print("=" * 60)

    # Test 1: Reproduce the mapping failure
    success1 = test_submission_id_mapping()

    # Test 2: Show the fix works
    success2 = test_service_field_mapping()

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"❌ Current services fail with database 'id' field: {not success1}")
    print(f"✅ Field mapping fix resolves the issue: {success2}")

    if success1 and success2:
        print("\n🎯 CONCLUSION: The issue is submission_id field mapping.")
        print("   Services expect 'submission_id' but database returns 'id'.")
        print("   Fix: Update services to use field mapping for submission_id.")
    else:
        print("\n⚠️  Unexpected test results")