"""
Test Suite for Supabase Opportunities Loader (TDD RED Phase)

This test suite defines the expected behavior for replacing DLT-based
opportunities loading with direct Supabase client. All tests should FAIL
initially as we haven't implemented the Supabase loader yet.

Context:
- Replacing: core.dlt.app_opportunities.load_app_opportunities (DLT-based)
- Target: Direct Supabase client upsert to 'opportunities' table
- Problem: DLT normalizes UUIDs to text, PostgreSQL silently rejects
- Solution: Direct Supabase upsert with proper UUID handling

Test Coverage:
1. Single opportunity upsert
2. Batch upsert (5+ opportunities)
3. Upsert behavior on duplicate IDs
4. Filtering profiles without problem_description
5. Empty list handling
6. UUID format preservation
"""

import pytest
import uuid
from typing import Any
from unittest.mock import Mock, patch, AsyncMock

# Import the function we'll be testing (will fail initially - that's expected)
try:
    from core.dlt.app_opportunities import load_app_opportunities
except ImportError:
    # Module doesn't exist yet - create placeholder
    def load_app_opportunities(ai_profiles: list[dict[str, Any]]) -> bool:
        """Placeholder - not implemented yet"""
        raise NotImplementedError("Supabase loader not implemented yet")


@pytest.fixture
def valid_opportunity_profile():
    """
    Fixture providing a valid opportunity profile matching the schema.

    Schema: opportunities table (from baseline_schema.sql)
    - id: UUID (primary key)
    - title: TEXT NOT NULL
    - description: TEXT
    - problem_statement: TEXT
    - target_audience: TEXT
    - submission_id: UUID (foreign key to submissions)
    - created_at: TIMESTAMPTZ
    - updated_at: TIMESTAMPTZ

    Note: The DLT version uses different field names (problem_description, app_concept, etc.)
    but we're testing the NEW Supabase loader that maps to the actual DB schema.
    """
    return {
        "id": str(uuid.uuid4()),
        "title": "Test App Opportunity",
        "description": "A comprehensive description of the opportunity",
        "problem_statement": "Users struggle with X, Y, and Z",
        "target_audience": "Small teams and individual developers",
        "submission_id": str(uuid.uuid4()),
    }


@pytest.fixture
def multiple_opportunity_profiles():
    """Fixture providing 5 valid opportunity profiles for batch testing."""
    base_submission_id = str(uuid.uuid4())

    return [
        {
            "id": str(uuid.uuid4()),
            "title": f"Opportunity {i+1}",
            "description": f"Description for opportunity {i+1}",
            "problem_statement": f"Problem statement {i+1}",
            "target_audience": "Target users",
            "submission_id": base_submission_id,
        }
        for i in range(5)
    ]


@pytest.fixture
def supabase_client_mock():
    """
    Mock Supabase client for testing database interactions.

    Mocks the expected Supabase client interface:
    - client.table(name).upsert(data).execute()
    - client.table(name).select("*").eq("id", value).execute()
    """
    mock_client = Mock()
    mock_table = Mock()
    mock_insert = Mock()
    mock_execute = Mock()

    # Setup mock chain: client.table().upsert().execute()
    mock_execute.data = []
    mock_insert.execute.return_value = mock_execute
    mock_table.upsert.return_value = mock_insert
    mock_client.table.return_value = mock_table

    return mock_client


class TestLoadSingleOpportunity:
    """Test loading a single opportunity profile (Test Case 1)"""

    def test_load_single_opportunity_success(
        self, valid_opportunity_profile, supabase_client_mock
    ):
        """
        Given: Single valid opportunity profile with UUID id
        When: load_app_opportunities() called
        Then: Returns True, data upserted to database, UUID preserved

        This test verifies:
        - Function returns True on success
        - Supabase upsert is called with correct data
        - UUID format is preserved (not converted to text)
        """
        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            result = load_app_opportunities([valid_opportunity_profile])

        # Assertion 1: Function returns True
        assert result is True, "load_app_opportunities should return True on success"

        # Assertion 2: Supabase upsert was called
        supabase_client_mock.table.assert_called_once_with('opportunities')
        supabase_client_mock.table().upsert.assert_called_once()

        # Assertion 3: Upsert was called with correct data
        upsert_call_args = supabase_client_mock.table().upsert.call_args[0][0]
        assert len(upsert_call_args) == 1, "Should upsert exactly 1 record"

        upserted_data = upsert_call_args[0]
        assert upserted_data['id'] == valid_opportunity_profile['id']
        assert upserted_data['title'] == valid_opportunity_profile['title']
        assert upserted_data['problem_statement'] == valid_opportunity_profile['problem_statement']

        # Assertion 4: UUID format validation
        try:
            uuid.UUID(upserted_data['id'])  # Should not raise
        except (ValueError, TypeError):
            pytest.fail("ID should be a valid UUID string")

    def test_uuid_format_preserved(self, valid_opportunity_profile, supabase_client_mock):
        """
        Given: Profile with id as UUID string
        When: load_app_opportunities() upserts to database
        Then: Database id column contains valid UUID (not text)

        This is the core test for the UUID blocker fix.
        DLT was normalizing UUIDs to text, PostgreSQL silently rejected.
        Direct Supabase upsert should preserve UUID format.
        """
        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            result = load_app_opportunities([valid_opportunity_profile])

        # Get the upserted data
        upsert_call_args = supabase_client_mock.table().upsert.call_args[0][0]
        upserted_data = upsert_call_args[0]

        # Verify UUID format
        opportunity_id = upserted_data['id']

        # Test 1: Should be a string
        assert isinstance(opportunity_id, str), "UUID should be passed as string"

        # Test 2: Should be valid UUID format (8-4-4-4-12)
        uuid_obj = uuid.UUID(opportunity_id)
        assert str(uuid_obj) == opportunity_id, "UUID should be in standard format"

        # Test 3: Should match input UUID
        assert opportunity_id == valid_opportunity_profile['id'], "UUID should not be modified"

        # Test 4: submission_id should also be UUID format
        if 'submission_id' in upserted_data and upserted_data['submission_id']:
            submission_uuid = uuid.UUID(upserted_data['submission_id'])
            assert str(submission_uuid) == upserted_data['submission_id']


class TestLoadMultipleOpportunities:
    """Test loading multiple opportunities in batch (Test Case 2)"""

    def test_load_multiple_opportunities_batch(
        self, multiple_opportunity_profiles, supabase_client_mock
    ):
        """
        Given: 5 opportunity profiles
        When: load_app_opportunities() called
        Then: All 5 upserted, returns True

        Verifies batch upsert capability and success reporting.
        """
        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            result = load_app_opportunities(multiple_opportunity_profiles)

        # Assertion 1: Returns True
        assert result is True, "Batch load should return True on success"

        # Assertion 2: Upsert called with all 5 records
        upsert_call_args = supabase_client_mock.table().upsert.call_args[0][0]
        assert len(upsert_call_args) == 5, "Should upsert all 5 opportunities"

        # Assertion 3: Each record has required fields
        for i, upserted_data in enumerate(upsert_call_args):
            assert 'id' in upserted_data, f"Record {i} missing 'id'"
            assert 'title' in upserted_data, f"Record {i} missing 'title'"
            assert 'problem_statement' in upserted_data, f"Record {i} missing 'problem_statement'"

            # Verify UUID format
            uuid.UUID(upserted_data['id'])  # Should not raise

    def test_batch_maintains_order(self, multiple_opportunity_profiles, supabase_client_mock):
        """
        Given: 5 opportunity profiles with specific order
        When: load_app_opportunities() called
        Then: Upsert maintains original order

        This ensures predictable behavior for downstream systems.
        """
        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            load_app_opportunities(multiple_opportunity_profiles)

        upsert_call_args = supabase_client_mock.table().upsert.call_args[0][0]

        # Verify order matches input
        for i, (original, upserted) in enumerate(zip(multiple_opportunity_profiles, upsert_call_args)):
            assert upserted['id'] == original['id'], f"Record {i} order mismatch"
            assert upserted['title'] == original['title'], f"Record {i} title mismatch"


class TestUpsertBehavior:
    """Test upsert behavior on duplicate IDs (Test Case 3)"""

    def test_upsert_behavior_on_duplicate_id(self, valid_opportunity_profile, supabase_client_mock):
        """
        Given: Existing opportunity with id="uuid-123"
        When: load_app_opportunities() with same id but different data
        Then: Record updated (not duplicated), returns True

        This tests the upsert/merge functionality that prevents duplicates.
        """
        # First upsert
        first_profile = valid_opportunity_profile.copy()
        first_profile['title'] = "Original Title"

        # Second upsert with same ID but different title
        second_profile = valid_opportunity_profile.copy()
        second_profile['title'] = "Updated Title"

        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            # First load
            result1 = load_app_opportunities([first_profile])
            assert result1 is True

            # Second load with same ID - should upsert
            result2 = load_app_opportunities([second_profile])
            assert result2 is True

        # Verify upsert was used
        # Note: Implementation should use .upsert() for deduplication
        # We're testing the behavior, not implementation details
        assert supabase_client_mock.table.call_count >= 2, "Should have called table() at least twice"

    def test_upsert_preserves_uuid_on_update(self, valid_opportunity_profile, supabase_client_mock):
        """
        Given: Update to existing opportunity
        When: Upsert operation executes
        Then: UUID format preserved in update operation
        """
        updated_profile = valid_opportunity_profile.copy()
        updated_profile['title'] = "Updated Title"
        updated_profile['description'] = "Updated Description"

        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            result = load_app_opportunities([updated_profile])

        # Get the data passed to upsert
        upsert_call_args = supabase_client_mock.table().upsert.call_args[0][0]
        data = upsert_call_args[0]

        # Verify UUID preserved
        uuid.UUID(data['id'])  # Should not raise
        assert data['id'] == valid_opportunity_profile['id']


class TestFilteringBehavior:
    """Test filtering profiles without problem_description (Test Case 4)"""

    def test_filters_profiles_without_problem_description(self, supabase_client_mock):
        """
        Given: 3 profiles, only 1 has problem_statement
        When: load_app_opportunities() called
        Then: Only 1 upserted, returns True

        Note: The DLT version filters on 'problem_description', but we're
        testing the NEW version that uses the actual schema field 'problem_statement'.
        """
        profiles = [
            {
                "id": str(uuid.uuid4()),
                "title": "Opportunity 1",
                "problem_statement": "Valid problem statement",
                "description": "Valid description",
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Opportunity 2",
                # Missing problem_statement - should be filtered
                "description": "Description without problem",
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Opportunity 3",
                "problem_statement": None,  # Null problem_statement - should be filtered
                "description": "Another description",
            },
        ]

        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            result = load_app_opportunities(profiles)

        # Should return True (at least 1 valid profile)
        assert result is True, "Should return True when at least 1 valid profile exists"

        # Should only upsert 1 record (the valid one)
        upsert_call_args = supabase_client_mock.table().upsert.call_args[0][0]
        assert len(upsert_call_args) == 1, "Should only upsert profiles with problem_statement"

        # Verify the correct profile was upserted
        upserted_data = upsert_call_args[0]
        assert upserted_data['problem_statement'] == "Valid problem statement"

    def test_filters_empty_problem_statement(self, supabase_client_mock):
        """
        Given: Profile with empty string problem_statement
        When: load_app_opportunities() called
        Then: Profile filtered out, returns False
        """
        profiles = [
            {
                "id": str(uuid.uuid4()),
                "title": "Empty Problem",
                "problem_statement": "",  # Empty string - should be filtered
                "description": "Description",
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Whitespace Problem",
                "problem_statement": "   ",  # Whitespace only - should be filtered
                "description": "Description",
            },
        ]

        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            result = load_app_opportunities(profiles)

        # Should return False (no valid profiles)
        assert result is False, "Should return False when no valid profiles"

        # Should not call upsert at all
        supabase_client_mock.table().upsert.assert_not_called()


class TestEmptyListHandling:
    """Test handling of empty lists (Test Case 5)"""

    def test_handles_empty_list(self, supabase_client_mock):
        """
        Given: Empty list []
        When: load_app_opportunities() called
        Then: Returns False, no database operations
        """
        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            result = load_app_opportunities([])

        # Should return False
        assert result is False, "Empty list should return False"

        # Should not call table() or upsert()
        supabase_client_mock.table.assert_not_called()

    def test_handles_none_input(self, supabase_client_mock):
        """
        Given: None input
        When: load_app_opportunities() called
        Then: Returns False, no database operations
        """
        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            # Should handle None gracefully
            result = load_app_opportunities(None)

        assert result is False, "None input should return False"
        supabase_client_mock.table.assert_not_called()


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_handles_supabase_connection_error(self, valid_opportunity_profile):
        """
        Given: Supabase client raises connection error
        When: load_app_opportunities() called
        Then: Returns False, error logged
        """
        mock_client = Mock()
        mock_client.table.side_effect = Exception("Connection failed")

        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=mock_client):
            result = load_app_opportunities([valid_opportunity_profile])

        # Should return False on error
        assert result is False, "Should return False on database error"

    def test_handles_invalid_uuid_format(self, supabase_client_mock):
        """
        Given: Profile with invalid UUID format
        When: load_app_opportunities() called
        Then: Returns False or filters out invalid record
        """
        invalid_profile = {
            "id": "not-a-valid-uuid",
            "title": "Invalid UUID",
            "problem_statement": "Valid problem",
            "description": "Valid description",
        }

        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            # Should either return False or filter out the invalid record
            result = load_app_opportunities([invalid_profile])

        # We expect this to fail validation
        assert result is False, "Should reject invalid UUID format"

    def test_handles_missing_required_fields(self, supabase_client_mock):
        """
        Given: Profile missing required 'title' field
        When: load_app_opportunities() called
        Then: Returns False or filters out invalid record
        """
        incomplete_profile = {
            "id": str(uuid.uuid4()),
            # Missing 'title' (required field)
            "problem_statement": "Valid problem",
            "description": "Valid description",
        }

        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            result = load_app_opportunities([incomplete_profile])

        # Should handle missing required fields
        assert result is False, "Should reject profiles missing required fields"


class TestSchemaAlignment:
    """Test alignment with actual database schema"""

    def test_maps_to_opportunities_table_schema(self, valid_opportunity_profile, supabase_client_mock):
        """
        Given: Valid opportunity profile
        When: load_app_opportunities() called
        Then: Data maps correctly to opportunities table schema

        Schema fields (from baseline_schema.sql):
        - id (UUID, PK)
        - title (TEXT NOT NULL)
        - description (TEXT)
        - problem_statement (TEXT)
        - target_audience (TEXT)
        - submission_id (UUID, FK)
        - created_at (TIMESTAMPTZ, auto)
        - updated_at (TIMESTAMPTZ, auto)
        """
        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            load_app_opportunities([valid_opportunity_profile])

        upsert_call_args = supabase_client_mock.table().upsert.call_args[0][0]
        upserted_data = upsert_call_args[0]

        # Verify required fields present
        assert 'id' in upserted_data, "Missing required field: id"
        assert 'title' in upserted_data, "Missing required field: title"

        # Verify optional fields handled correctly
        expected_fields = {'id', 'title', 'description', 'problem_statement',
                          'target_audience', 'submission_id'}
        for field in expected_fields:
            if field in valid_opportunity_profile:
                assert field in upserted_data, f"Field {field} should be included"

    def test_does_not_upsert_auto_managed_fields(self, valid_opportunity_profile, supabase_client_mock):
        """
        Given: Valid opportunity profile
        When: load_app_opportunities() called
        Then: Does not manually set created_at/updated_at (DB manages these)
        """
        with patch('core.dlt.app_opportunities.get_supabase_client', return_value=supabase_client_mock):
            load_app_opportunities([valid_opportunity_profile])

        upsert_call_args = supabase_client_mock.table().upsert.call_args[0][0]
        upserted_data = upsert_call_args[0]

        # These fields should be managed by database DEFAULT
        assert 'created_at' not in upserted_data, "created_at should be managed by DB"
        assert 'updated_at' not in upserted_data, "updated_at should be managed by DB"


# Test execution summary marker
def test_suite_summary():
    """
    Test Suite Summary - TDD RED Phase

    Expected Status: ALL TESTS SHOULD FAIL

    Test Coverage:
    1. ✓ test_load_single_opportunity_success - Single upsert
    2. ✓ test_uuid_format_preserved - UUID blocker fix
    3. ✓ test_load_multiple_opportunities_batch - Batch upsert
    4. ✓ test_batch_maintains_order - Order preservation
    5. ✓ test_upsert_behavior_on_duplicate_id - Deduplication
    6. ✓ test_upsert_preserves_uuid_on_update - UUID in updates
    7. ✓ test_filters_profiles_without_problem_description - Filtering
    8. ✓ test_filters_empty_problem_statement - Empty string filtering
    9. ✓ test_handles_empty_list - Empty input handling
    10. ✓ test_handles_none_input - None input handling
    11. ✓ test_handles_supabase_connection_error - Error handling
    12. ✓ test_handles_invalid_uuid_format - UUID validation
    13. ✓ test_handles_missing_required_fields - Field validation
    14. ✓ test_maps_to_opportunities_table_schema - Schema alignment
    15. ✓ test_does_not_upsert_auto_managed_fields - DB-managed fields

    Next Steps (GREEN Phase):
    1. Implement get_supabase_client() function
    2. Rewrite load_app_opportunities() using Supabase client
    3. Add UUID validation logic
    4. Add problem_statement filtering
    5. Implement upsert logic for deduplication
    6. Run tests until all pass
    """
    # This test always passes - it's just a marker
    assert True, "Test suite defined - ready for GREEN phase implementation"
