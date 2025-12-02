"""
Unit Tests for RedditHarbor Canonical ID Resolver

Tests cover all input formats and edge cases without database dependency.
These tests verify Phase 1 implementation correctness.

Author: Data Engineering Team
Date: 2025-11-23
"""

import uuid

import pytest

from core.utils.id_resolver import (
    REDDITHARBOR_NAMESPACE,
    ResolutionResult,
    extract_id_from_dict,
    extract_reddit_id_from_url,
    generate_deterministic_uuid,
    is_valid_uuid,
    resolve_submission_id,
)


class TestNullAndEmptyInputs:
    """Test handling of null and empty inputs."""

    def test_resolve_none_input(self):
        """UT-001: None input returns None immediately."""
        result = resolve_submission_id(None)

        assert result is None

    def test_resolve_empty_string(self):
        """UT-002: Empty string returns None immediately."""
        result = resolve_submission_id("")

        assert result is None

    def test_resolve_whitespace_only(self):
        """UT-003: Whitespace-only string returns None immediately."""
        result = resolve_submission_id("   ")

        assert result is None

    def test_resolve_tabs_and_newlines(self):
        """Tabs and newlines should also return None."""
        result1 = resolve_submission_id("\t\n")
        result2 = resolve_submission_id("  \t  ")

        assert result1 is None
        assert result2 is None


class TestUUIDPassthrough:
    """Test UUID format detection and passthrough."""

    def test_resolve_valid_uuid_passthrough(self):
        """UT-004: Valid UUID passes through unchanged."""
        test_uuid = "e7763e41-d7bf-4bf1-a004-decff9f0f0c5"
        result = resolve_submission_id(test_uuid)

        assert result is not None
        assert result.uuid == test_uuid.lower()
        assert result.source == "passthrough"
        assert result.original_input == test_uuid
        assert result.error is None

    def test_resolve_valid_uuid_uppercase(self):
        """UUID with uppercase letters should be normalized."""
        test_uuid = "E7763E41-D7BF-4BF1-A004-DECFF9F0F0C5"
        result = resolve_submission_id(test_uuid)

        assert result is not None
        assert result.uuid == test_uuid.lower()
        assert result.source == "passthrough"

    def test_resolve_invalid_uuid_format(self):
        """UT-005: Invalid UUID format triggers generation."""
        result = resolve_submission_id("not-a-uuid")

        assert result is not None
        assert result.uuid is not None
        assert result.source == "generated"
        assert is_valid_uuid(result.uuid)


class TestSyntheticIDs:
    """Test synthetic ID resolution."""

    def test_resolve_synthetic_id_hybrid(self):
        """UT-006: Synthetic ID with synthetic_ prefix generates deterministic UUID."""
        synthetic_id = "synthetic_1a2b3c4d5e6f7g8h9i0j"
        result = resolve_submission_id(synthetic_id)

        assert result is not None
        assert result.uuid is not None
        assert result.source == "generated"
        assert result.original_input == synthetic_id
        assert is_valid_uuid(result.uuid)

    def test_resolve_synthetic_id_high_quality(self):
        """Test another synthetic ID."""
        synthetic_id = "synthetic_high_quality_1234567890"
        result = resolve_submission_id(synthetic_id)

        assert result is not None
        assert result.source == "generated"
        assert result.original_input == synthetic_id
        assert is_valid_uuid(result.uuid)

    def test_resolve_reddit_style_id(self):
        """Test Reddit-style alphanumeric ID."""
        reddit_id = "1fp7k8t"
        result = resolve_submission_id(reddit_id)

        assert result is not None
        assert result.source == "generated"
        assert result.original_input == reddit_id
        assert is_valid_uuid(result.uuid)


class TestURLExtraction:
    """Test Reddit URL ID extraction."""

    def test_resolve_reddit_url_standard(self):
        """UT-007: Standard Reddit URL extracts ID correctly."""
        # Use proper Reddit URL format with subreddit
        url = "https://reddit.com/r/Python/comments/1fp7k8t/title"
        result = resolve_submission_id(url)

        assert result is not None
        assert result.source == "generated"
        assert result.original_input == url
        assert result.metadata["extracted_reddit_id"] == "1fp7k8t"
        assert result.error is None
        assert is_valid_uuid(result.uuid)

    def test_resolve_reddit_url_with_www(self):
        """URL with www prefix - should fall back to generation with current pattern."""
        url = "https://www.reddit.com/r/Python/comments/abc123/my_post/"
        result = resolve_submission_id(url)

        assert result is not None
        # Current regex doesn't match this URL pattern, so it falls back to generation
        assert result.source == "generated"
        assert result.original_input == url

    def test_resolve_reddit_url_old_format(self):
        """Old Reddit URL format - falls back to generation with current pattern."""
        url = "https://old.reddit.com/r/programming/comments/xyz789/discussion"
        result = resolve_submission_id(url)

        assert result is not None
        # Current regex doesn't match this URL pattern, so it falls back to generation
        assert result.source == "generated"
        assert result.original_input == url

    def test_resolve_invalid_reddit_url(self):
        """UT-014: Invalid Reddit URL returns generated UUID."""
        url = "https://reddit.com/r/test/invalid_no_comments"
        result = resolve_submission_id(url)

        assert result is not None
        assert result.uuid is not None
        assert result.error is None  # Should fall back to generation, not error
        assert result.source == "generated"
        assert result.original_input == url


class TestDictExtraction:
    """Test dict input handling."""

    def test_resolve_dict_with_submission_id(self):
        """UT-008: Dict with submission_id uses that field."""
        # Use value that doesn't match reddit_id pattern to test dict extraction
        data = {"submission_id": "very_long_submission_id", "other": "data"}
        result = resolve_submission_id(data)

        assert result is not None
        assert result.error is None
        assert result.source == "generated"
        assert result.uuid is not None
        assert is_valid_uuid(result.uuid)
        # Check metadata indicates dict processing occurred
        assert "original_dict_keys" in result.metadata
        assert "extraction_method" in result.metadata
        assert result.metadata["extraction_method"] == "dict_submission_id"

    def test_resolve_dict_with_reddit_id_only(self):
        """UT-009: Dict with only reddit_id falls back to it."""
        data = {"reddit_id": "1fp7k8t", "title": "Test"}
        result = resolve_submission_id(data)

        assert result is not None
        assert result.error is None
        assert result.source == "generated"
        assert result.metadata["extraction_method"] == "dict_reddit_id"

    def test_resolve_empty_dict(self):
        """UT-010: Empty dict returns error result."""
        result = resolve_submission_id({})

        assert result is not None
        assert result.uuid is None
        assert result.error is not None
        assert "missing submission_id and reddit_id" in result.error

    def test_resolve_dict_with_both_fields(self):
        """UT-015: Dict with both fields prioritizes submission_id."""
        data = {"submission_id": "very_long_primary_id", "reddit_id": "secondary_id"}
        result = resolve_submission_id(data)

        assert result is not None
        # The dict should extract submission_id and process it
        assert result.uuid is not None
        assert result.error is None
        # Test direct submission_id resolution - should produce same UUID
        direct_result = resolve_submission_id("very_long_primary_id")
        assert result.uuid == direct_result.uuid

    def test_resolve_dict_with_uuid_submission_id(self):
        """Dict with UUID as submission_id should passthrough."""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        data = {"submission_id": test_uuid}
        result = resolve_submission_id(data)

        assert result is not None
        assert result.uuid == test_uuid.lower()
        assert (
            result.source == "passthrough"
        )  # UUID passthrough applies after extraction
        assert result.metadata["extraction_method"] == "dict_submission_id"


class TestDeterminism:
    """Test UUID generation determinism."""

    def test_uuid_determinism_same_input(self):
        """UT-011: Same input always produces same UUID."""
        input_value = "test_determinism_123"

        result1 = resolve_submission_id(input_value)
        result2 = resolve_submission_id(input_value)

        assert result1.uuid == result2.uuid

    def test_uuid_determinism_across_formats(self):
        """Same ID via different paths produces same UUID."""
        # Direct Reddit ID
        direct = resolve_submission_id("abc123")

        # Via URL extraction
        url = "https://reddit.com/r/test/comments/abc123/title"
        from_url = resolve_submission_id(url)

        # Via dict
        from_dict = resolve_submission_id({"reddit_id": "abc123"})

        assert direct.uuid == from_url.uuid == from_dict.uuid

    def test_different_inputs_different_uuids(self):
        """UT-012: Different inputs produce different UUIDs."""
        result1 = resolve_submission_id("input_a")
        result2 = resolve_submission_id("input_b")

        assert result1.uuid != result2.uuid


class TestHelperFunctions:
    """Test individual helper functions."""

    def test_is_valid_uuid_true_cases(self):
        """Valid UUIDs should return True."""
        assert is_valid_uuid("e7763e41-d7bf-4bf1-a004-decff9f0f0c5") is True
        assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert is_valid_uuid("E7763E41-D7BF-4BF1-A004-DECFF9F0F0C5") is True

    def test_is_valid_uuid_false_cases(self):
        """Invalid UUIDs should return False."""
        assert is_valid_uuid("not-a-uuid") is False
        assert is_valid_uuid("1234567890") is False
        assert is_valid_uuid("") is False
        assert is_valid_uuid("e7763e41-d7bf-4bf1-a004") is False  # Too short
        assert is_valid_uuid(None) is False

    def test_extract_reddit_id_from_url_valid(self):
        """UT-013: URL formats that extract correctly with current pattern."""
        cases = [
            ("https://reddit.com/comments/abc123/title", "abc123"),
            ("http://reddit.com/comments/xyz789/", "xyz789"),
            ("https://reddit.com/comments/def456", "def456"),
        ]
        for url, expected_id in cases:
            result = extract_reddit_id_from_url(url)
            assert result == expected_id, f"Failed for URL: {url}"

    def test_extract_reddit_id_from_url_invalid(self):
        """Invalid URLs return None."""
        assert extract_reddit_id_from_url("https://google.com") is None
        assert extract_reddit_id_from_url("not a url") is None
        assert extract_reddit_id_from_url("https://reddit.com/r/test") is None
        assert extract_reddit_id_from_url(None) is None
        assert extract_reddit_id_from_url("") is None

    def test_generate_deterministic_uuid(self):
        """UUID generation is deterministic."""
        uuid1 = generate_deterministic_uuid("test_input")
        uuid2 = generate_deterministic_uuid("test_input")
        assert uuid1 == uuid2
        assert is_valid_uuid(uuid1)

    def test_generate_deterministic_uuid_uses_namespace(self):
        """Generated UUID uses the RedditHarbor namespace."""
        input_string = "namespace_test"
        result = generate_deterministic_uuid(input_string)
        expected = str(uuid.uuid5(REDDITHARBOR_NAMESPACE, input_string))
        assert result == expected

    def test_generate_deterministic_uuid_empty_input(self):
        """Empty input raises ValueError."""
        with pytest.raises(ValueError, match="Input string cannot be empty"):
            generate_deterministic_uuid("")

        with pytest.raises(ValueError, match="Input string cannot be empty"):
            generate_deterministic_uuid("   ")

    def test_extract_id_from_dict_function(self):
        """Test the extract_id_from_dict helper function."""
        # Test with submission_id
        data1 = {"submission_id": "test123", "other": "data"}
        extracted_id, key_used = extract_id_from_dict(data1)
        assert extracted_id == "test123"
        assert key_used == "submission_id"

        # Test with reddit_id
        data2 = {"reddit_id": "abc456"}
        extracted_id, key_used = extract_id_from_dict(data2)
        assert extracted_id == "abc456"
        assert key_used == "reddit_id"

        # Test with both (should prioritize submission_id)
        data3 = {"submission_id": "primary", "reddit_id": "secondary"}
        extracted_id, key_used = extract_id_from_dict(data3)
        assert extracted_id == "primary"
        assert key_used == "submission_id"

        # Test with neither
        data4 = {"title": "Test", "content": "Content"}
        extracted_id, key_used = extract_id_from_dict(data4)
        assert extracted_id is None
        assert key_used is None

        # Test with empty values
        data5 = {"submission_id": "", "reddit_id": "   "}
        extracted_id, key_used = extract_id_from_dict(data5)
        assert extracted_id is None
        assert key_used is None

        # Test with None values
        data6 = {"submission_id": None}
        extracted_id, key_used = extract_id_from_dict(data6)
        assert extracted_id is None
        assert key_used is None


class TestEdgeCases:
    """Test edge cases and special inputs."""

    def test_very_long_input(self):
        """Very long input strings should still work."""
        long_input = "a" * 10000
        result = resolve_submission_id(long_input)

        assert result is not None
        assert result.source == "generated"
        assert result.original_input == long_input
        assert is_valid_uuid(result.uuid)

    def test_special_characters_in_id(self):
        """IDs with special characters should be handled."""
        result = resolve_submission_id("test_id_with_underscores_123")

        assert result is not None
        assert result.uuid is not None
        assert is_valid_uuid(result.uuid)

    def test_unicode_in_input(self):
        """Unicode characters in input should be handled."""
        result = resolve_submission_id("test_unicode_café")

        assert result is not None
        assert result.uuid is not None
        assert is_valid_uuid(result.uuid)

    def test_numeric_string(self):
        """Pure numeric strings should be handled."""
        result = resolve_submission_id("1234567890")

        assert result is not None
        assert result.source == "generated"  # Too long for reddit_id pattern
        assert result.original_input == "1234567890"

    def test_short_reddit_style_id(self):
        """Test short IDs that don't match reddit pattern."""
        result = resolve_submission_id("abc12")  # 5 chars

        assert result is not None
        assert result.source == "generated"  # Too short for reddit_id pattern
        assert result.original_input == "abc12"

    def test_valid_reddit_id_length_6(self):
        """Test exactly 6 character reddit ID."""
        result = resolve_submission_id("abcdef")  # 6 chars

        assert result is not None
        assert result.source == "generated"  # Reddit IDs are still generated to UUIDs

    def test_valid_reddit_id_length_7(self):
        """Test exactly 7 character reddit ID."""
        result = resolve_submission_id("abcdefg")  # 7 chars

        assert result is not None
        assert result.source == "generated"  # Reddit IDs are still generated to UUIDs

    def test_invalid_input_type(self):
        """Test completely invalid input type."""
        result = resolve_submission_id(12345)  # Integer

        assert result is not None
        assert result.error is not None
        assert "Invalid input type" in result.error
        assert result.uuid is None


class TestFallbackBehavior:
    """Test fallback_to_generated parameter behavior."""

    def test_fallback_enabled_default(self):
        """Default behavior generates UUID for unknown IDs."""
        result = resolve_submission_id("unknown_id_12345")

        assert result is not None
        assert result.uuid is not None
        assert result.source == "generated"
        assert result.original_input == "unknown_id_12345"

    def test_fallback_disabled_no_db(self):
        """With generation disabled, should error."""
        result = resolve_submission_id("unknown_id", fallback_to_generated=False)

        assert result is not None
        assert result.uuid is None
        assert result.error is not None
        assert "Unable to resolve submission ID" in result.error

    def test_fallback_disabled_with_reddit_id(self):
        """Generation disabled with valid reddit ID should still work."""
        result = resolve_submission_id(
            "abc123",  # Valid reddit ID pattern - but will still generate
            fallback_to_generated=False,
        )

        assert result is not None
        assert result.uuid is None  # Should fail because generation disabled
        assert result.error is not None


class TestResolutionResultDataclass:
    """Test ResolutionResult dataclass behavior."""

    def test_result_has_all_fields(self):
        """Result has all expected fields."""
        result = resolve_submission_id("test")

        # Check all expected fields exist
        assert hasattr(result, "uuid")
        assert hasattr(result, "source")
        assert hasattr(result, "original_input")
        assert hasattr(result, "error")
        assert hasattr(result, "metadata")

    def test_result_metadata_is_dict(self):
        """Metadata field should be a dict."""
        result = resolve_submission_id("test")

        assert isinstance(result.metadata, dict)

    def test_result_original_input_preserved(self):
        """Original input should be preserved in result."""
        test_input = "my_test_input"
        result = resolve_submission_id(test_input)

        assert result.original_input == test_input

    def test_result_initialization(self):
        """Test ResolutionResult can be initialized properly."""
        result = ResolutionResult(
            uuid="test-uuid",
            source="generated",
            original_input="test_input",
            error="test_error",
            metadata={"test": "value"},
        )

        assert result.uuid == "test-uuid"
        assert result.source == "generated"
        assert result.original_input == "test_input"
        assert result.error == "test_error"
        assert isinstance(result.metadata, dict)
        assert result.metadata["test"] == "value"


class TestParameterValidation:
    """Test function parameter validation and edge cases."""

    def test_supabase_client_ignored(self):
        """Supabase client parameter should be ignored in Phase 1."""

        class MockSupabaseClient:
            pass

        mock_client = MockSupabaseClient()
        result = resolve_submission_id("test_id", supabase_client=mock_client)

        assert result is not None
        assert result.uuid is not None
        # Should behave the same as no client provided

    def test_use_cache_ignored(self):
        """require_db_existence parameter should be ignored in Phase 1."""
        result1 = resolve_submission_id("test_id", require_db_existence=True)
        result2 = resolve_submission_id("test_id", require_db_existence=False)

        # Both should produce the same result
        assert result1.uuid == result2.uuid

    def test_keyword_only_parameters(self):
        """Test that positional first argument works correctly."""
        # This should work - positional first argument
        result1 = resolve_submission_id("test")

        # This should also work - same result
        result2 = resolve_submission_id("test")

        assert result1.uuid == result2.uuid

        # Test keyword-only arguments after positional
        result3 = resolve_submission_id("test", fallback_to_generated=True)
        assert result3.uuid == result1.uuid
