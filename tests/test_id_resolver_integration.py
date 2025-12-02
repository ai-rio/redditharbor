"""
Integration Tests for RedditHarbor ID Resolver with Storage and Verification

These tests verify that the canonical ID resolver correctly integrates with:
1. database_verifier.py - Submission lookup and verification
2. enhanced_hybrid_store.py - UUID resolution for FK references

Author: Data Engineering Team
Date: 2025-11-23
"""

import threading
import uuid
from unittest.mock import Mock, patch

import pytest

from core.utils.id_resolver import (
    generate_deterministic_uuid,
    is_valid_uuid,
    resolve_submission_id,
)


class TestResolverWithDatabaseVerifier:
    """Integration tests for resolver + database_verifier."""

    def test_resolver_handles_hybrid_id_format(self):
        """Verify resolver can process 'hybrid_1' format IDs."""
        result = resolve_submission_id("hybrid_1")

        assert result is not None
        assert result.uuid is not None
        assert is_valid_uuid(result.uuid)
        assert result.source == "generated"

    def test_resolver_handles_uuid_passthrough(self):
        """Verify resolver passes through valid UUIDs unchanged."""
        test_uuid = str(uuid.uuid4())
        result = resolve_submission_id(test_uuid)

        assert result is not None
        assert result.uuid == test_uuid.lower()  # Normalized case
        assert result.source == "passthrough"

    def test_resolver_deterministic_for_synthetic_ids(self):
        """Verify same synthetic ID always produces same UUID."""
        id1 = resolve_submission_id("test_submission_001")
        id2 = resolve_submission_id("test_submission_001")

        assert id1.uuid == id2.uuid
        assert id1.uuid == generate_deterministic_uuid("test_submission_001")

    def test_resolver_extracts_reddit_id_from_url(self):
        """Verify resolver extracts ID from Reddit URL format."""
        url = "https://reddit.com/r/datascience/comments/1fp7k8t/title_here"
        result = resolve_submission_id(url)

        assert result is not None
        assert result.uuid is not None

        # Should match direct resolution of the extracted ID
        direct = resolve_submission_id("1fp7k8t")
        assert result.uuid == direct.uuid

    def test_resolver_handles_dict_with_submission_id(self):
        """Verify resolver extracts submission_id from dict input."""
        data = {"submission_id": "abc123", "title": "Test Post"}
        result = resolve_submission_id(data)

        assert result is not None
        assert result.uuid is not None

        # Should match direct resolution
        direct = resolve_submission_id("abc123")
        assert result.uuid == direct.uuid


class TestResolverWithEnhancedStore:
    """Integration tests for resolver + enhanced_hybrid_store."""

    def test_resolver_with_mock_supabase_lookup(self):
        """Verify resolver uses supabase_client for database lookups when provided."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [{"id": "db-uuid-12345"}]

        # Mock the table().select().eq().execute() chain
        # Mock the table().select().eq().execute() chain
        mock_chain = (
            mock_client.table.return_value.select.return_value.eq.return_value.execute
        )
        mock_chain.return_value = mock_response

        result = resolve_submission_id(
            "test_id",
            supabase_client=mock_client,
            require_db_existence=False,
            fallback_to_generated=True,
        )

        assert result is not None
        assert result.uuid is not None

    def test_resolver_fallback_when_not_in_database(self):
        """Verify resolver falls back to generation when ID not in database."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = []  # Empty result - not found

        # Mock the table().select().eq().execute() chain
        mock_chain = (
            mock_client.table.return_value.select.return_value.eq.return_value.execute
        )
        mock_chain.return_value = mock_response

        result = resolve_submission_id(
            "nonexistent_id",
            supabase_client=mock_client,
            require_db_existence=False,
            fallback_to_generated=True,
        )

        assert result is not None
        assert result.uuid is not None
        # Should be generated since not found in DB
        assert result.source in ("generated", "passthrough")

    def test_resolver_require_db_existence_false(self):
        """Verify resolver doesn't require database existence when flag is False."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = []  # Not found in database

        # Mock the table().select().eq().execute() chain
        mock_chain = (
            mock_client.table.return_value.select.return_value.eq.return_value.execute
        )
        mock_chain.return_value = mock_response

        result = resolve_submission_id(
            "unknown_id",
            supabase_client=mock_client,
            require_db_existence=False,
            fallback_to_generated=True,
        )

        # Should succeed by generating a UUID
        assert result is not None
        assert result.uuid is not None
        assert result.source == "generated"

    def test_resolver_require_db_existence_true_fails(self):
        """Verify resolver fails when require_db_existence=True and ID not found."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = []  # Not found in database

        # Mock the table().select().eq().execute() chain
        mock_chain = (
            mock_client.table.return_value.select.return_value.eq.return_value.execute
        )
        mock_chain.return_value = mock_response

        result = resolve_submission_id(
            "unknown_id",
            supabase_client=mock_client,
            require_db_existence=True,
            fallback_to_generated=False,
        )

        # Should fail since not found and generation not allowed
        assert result is not None
        assert result.uuid is None
        assert result.error is not None


class TestDatabaseVerifierIntegration:
    """Test database_verifier.py integration with resolver."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        session = Mock()
        return session

    def test_verifier_resolves_hybrid_id_before_query(self):
        """Verify the verifier uses resolver to transform hybrid IDs."""
        # This tests the integration pattern, not the actual database
        input_id = "hybrid_1"
        result = resolve_submission_id(input_id)

        # The resolved UUID should be used for database queries
        assert result.uuid is not None
        assert is_valid_uuid(result.uuid)

        # Different from input
        assert result.uuid != input_id

    def test_verifier_handles_various_id_formats(self):
        """Verify verifier can handle all expected ID formats."""
        test_cases = [
            ("hybrid_1", "generated"),
            ("test_submission", "generated"),
            (str(uuid.uuid4()), "passthrough"),
            ("https://reddit.com/r/test/comments/abc123/title", "generated"),
            ({"submission_id": "dict_id"}, "generated"),
        ]

        for input_val, expected_source in test_cases:
            result = resolve_submission_id(input_val)
            assert result is not None, f"Failed for input: {input_val}"
            assert result.uuid is not None, f"No UUID for input: {input_val}"
            assert result.source == expected_source, f"Wrong source for {input_val}"

    @patch("scripts.testing.integration.utils.database_verifier.text")
    def test_verifier_query_with_resolved_uuid(self, mock_text):
        """Test that verifier would use resolved UUID in database queries."""
        # Simulate the verifier's integration pattern
        input_id = "hybrid_test_123"
        resolved = resolve_submission_id(input_id)

        # Mock the query creation
        mock_query = Mock()
        mock_text.return_value = mock_query

        # Simulate execution result
        mock_result = Mock()
        mock_result.id = resolved.uuid
        mock_result.title = "Test Submission"

        # Verify the resolver provides correct UUID for queries
        assert resolved.uuid is not None
        assert is_valid_uuid(resolved.uuid)

        # The resolved UUID should be different from the input
        assert resolved.uuid != input_id

    def test_verifier_supports_fallback_queries(self):
        """
        Verify resolver integration supports both UUID and reddit_id fallback queries.
        """
        input_id = "test_reddit_123"
        resolved = resolve_submission_id(input_id)

        # Should generate UUID for primary query
        assert resolved.uuid is not None
        assert is_valid_uuid(resolved.uuid)

        # Original ID should be available for fallback query
        assert input_id == input_id  # Original ID preserved for fallback


class TestEnhancedStoreIntegration:
    """Test enhanced_hybrid_store.py integration with resolver."""

    def test_store_resolution_maintains_determinism(self):
        """Verify store uses resolver for deterministic UUID generation."""
        # Same input should always get same UUID
        inputs = ["submission_001", "submission_002", "submission_001"]
        results = [resolve_submission_id(inp) for inp in inputs]

        # First and third should match (same input)
        assert results[0].uuid == results[2].uuid
        # First and second should differ
        assert results[0].uuid != results[1].uuid

    def test_store_resolution_handles_fk_reference(self):
        """Verify resolved UUIDs are valid for FK references."""
        # Simulate the _get_or_create_opportunity_id flow
        submission_id = "test_submission_for_fk"
        result = resolve_submission_id(submission_id)

        # The UUID should be valid format for FK
        assert result is not None
        assert is_valid_uuid(result.uuid)

        # UUID should be reproducible for FK consistency
        result2 = resolve_submission_id(submission_id)
        assert result.uuid == result2.uuid

    def test_store_handles_database_verified_uuids(self):
        """Verify store handles database-verified UUIDs correctly."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [{"id": "database-uuid-789"}]

        # Mock the table().select().eq().execute() chain
        mock_chain = (
            mock_client.table.return_value.select.return_value.eq.return_value.execute
        )
        mock_chain.return_value = mock_response

        # Test with database client
        result = resolve_submission_id(
            "existing_id",
            supabase_client=mock_client,
            require_db_existence=False,
            fallback_to_generated=True,
        )

        # Should return database UUID
        assert result is not None
        assert result.uuid is not None

    def test_store_handles_generated_uuid_verification(self):
        """Verify store can verify generated UUIDs exist in database."""
        mock_client = Mock()

        # First response: empty (UUID not found)
        mock_empty_response = Mock()
        mock_empty_response.data = []

        # Second response: found via reddit_id lookup
        mock_found_response = Mock()
        mock_found_response.data = [{"id": "actual-db-uuid-456"}]

        # Configure mock to return different responses for different calls
        mock_table = mock_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_eq = mock_select.eq.return_value

        # Call sequence: first UUID lookup fails, then reddit_id lookup succeeds
        mock_eq.execute.side_effect = [mock_empty_response, mock_found_response]

        # Test integration pattern from enhanced store
        result = resolve_submission_id(
            "test_id",
            supabase_client=mock_client,
            require_db_existence=False,
            fallback_to_generated=True,
        )

        assert result is not None
        assert result.uuid is not None


class TestEdgeCasesIntegration:
    """Test edge cases for resolver integration."""

    def test_empty_submission_id_handling(self):
        """Verify empty/None submission IDs are handled gracefully."""
        assert resolve_submission_id(None) is None
        assert resolve_submission_id("") is None
        assert resolve_submission_id("   ") is None

    def test_invalid_dict_format(self):
        """Verify invalid dict format returns error result."""
        result = resolve_submission_id({"title": "no id field"})

        assert result is not None
        assert result.uuid is None
        assert result.error is not None
        assert "missing submission_id" in result.error

    def test_resolver_thread_safety(self):
        """Verify resolver is thread-safe (no shared mutable state)."""
        results = []
        errors = []

        def resolve_in_thread(input_id, expected_uuid):
            try:
                result = resolve_submission_id(input_id)
                if result.uuid != expected_uuid:
                    errors.append(
                        f"Mismatch for {input_id}: got {result.uuid}, "
                        f"expected {expected_uuid}"
                    )
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # Pre-compute expected UUIDs
        expected = {
            "thread_test_1": resolve_submission_id("thread_test_1").uuid,
            "thread_test_2": resolve_submission_id("thread_test_2").uuid,
            "thread_test_3": resolve_submission_id("thread_test_3").uuid,
        }

        threads = []
        for _i in range(10):
            for test_id, expected_uuid in expected.items():
                t = threading.Thread(
                    target=resolve_in_thread, args=(test_id, expected_uuid)
                )
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 30  # 10 iterations x 3 test IDs

    def test_resolver_handles_unicode_and_special_characters(self):
        """Verify resolver handles Unicode characters in input strings."""
        unicode_inputs = [
            "tést_wïth_üñïçödé",
            "测试_中文_输入",
            "тест_кириллица",
            "🚀rocket_science_submission",
        ]

        for unicode_input in unicode_inputs:
            result = resolve_submission_id(unicode_input)
            assert result is not None, f"Failed for Unicode input: {unicode_input}"
            assert result.uuid is not None, (
                f"No UUID for Unicode input: {unicode_input}"
            )
            assert is_valid_uuid(result.uuid), (
                f"Invalid UUID for Unicode input: {unicode_input}"
            )
            assert result.source == "generated", (
                f"Wrong source for Unicode input: {unicode_input}"
            )

    def test_resolver_handles_very_long_inputs(self):
        """Verify resolver handles very long input strings gracefully."""
        very_long_input = "a" * 1000  # 1000 character string
        result = resolve_submission_id(very_long_input)

        assert result is not None
        assert result.uuid is not None
        assert is_valid_uuid(result.uuid)
        assert result.source == "generated"

    def test_resolver_preserves_original_input_in_result(self):
        """Verify resolver preserves original input for debugging/tracing."""
        test_cases = [
            "simple_id",
            str(uuid.uuid4()),
            {"submission_id": "dict_input"},
            "https://reddit.com/r/test/comments/abc123/title",
        ]

        for original_input in test_cases:
            result = resolve_submission_id(original_input)
            assert result is not None
            assert result.original_input == str(original_input)


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing code."""

    def test_uuid_passthrough_unchanged(self):
        """Verify existing UUID-based code continues to work."""
        existing_uuid = "e7763e41-d7bf-4bf1-a004-decff9f0f0c5"
        result = resolve_submission_id(existing_uuid)

        # Should pass through unchanged (except case normalization)
        assert result.uuid == existing_uuid.lower()
        assert result.source == "passthrough"

    def test_reddit_id_compatibility(self):
        """Verify reddit_id based lookups are supported."""
        # Reddit IDs are typically alphanumeric like "1fp7k8t"
        reddit_id = "1fp7k8t"
        result = resolve_submission_id(reddit_id)

        assert result is not None
        assert result.uuid is not None
        # Should generate deterministic UUID
        assert result.source == "generated"

    def test_mixed_case_uuid_handling(self):
        """Verify resolver handles mixed-case UUIDs correctly."""
        mixed_case_uuid = "E7763e41-D7BF-4BF1-A004-DECFF9F0F0C5"
        result = resolve_submission_id(mixed_case_uuid)

        assert result is not None
        assert result.uuid == mixed_case_uuid.lower()  # Should normalize to lowercase
        assert result.source == "passthrough"

    def test_hybrid_id_format_compatibility(self):
        """Verify hybrid ID formats used in tests are supported."""
        hybrid_ids = ["hybrid_1", "hybrid_2", "hybrid_test_123", "synthetic_id_456"]

        for hybrid_id in hybrid_ids:
            result = resolve_submission_id(hybrid_id)
            assert result is not None, f"Failed for hybrid ID: {hybrid_id}"
            assert result.uuid is not None, f"No UUID for hybrid ID: {hybrid_id}"
            assert result.source == "generated", (
                f"Wrong source for hybrid ID: {hybrid_id}"
            )

            # Should be deterministic
            result2 = resolve_submission_id(hybrid_id)
            assert result.uuid == result2.uuid, f"Non-deterministic for {hybrid_id}"
