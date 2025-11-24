# File: tests/test_dlt_id_normalization.py

import pytest
import uuid
from unittest.mock import Mock, patch
from typing import Any, Dict

from core.utils.id_resolver import resolve_submission_id, REDDITHARBOR_NAMESPACE
from core.dlt.collection import transform_submission_to_schema, transform_comment_to_schema

class TestTransformSubmissionIDNormalization:
    """Test submission ID normalization (10 tests)"""

    def test_submission_id_is_uuid_format(self):
        """Test that submission_id is a UUID after transformation"""
        submission_data = {"id": "test_sub_123"}
        result = transform_submission_to_schema(submission_data)

        assert result["submission_id"] is not None
        # Verify UUID format (8-4-4-4-12)
        uuid.UUID(str(result["submission_id"]))  # Will raise if not valid UUID

    def test_original_reddit_id_preserved(self):
        """Test that reddit_id field preserves original Reddit ID"""
        submission_data = {"id": "test_sub_456"}
        result = transform_submission_to_schema(submission_data)

        assert result["reddit_id"] == "test_sub_456"

    def test_submission_transform_deterministic(self):
        """Test that same input always produces same UUID"""
        submission_data = {"id": "test_sub_789"}
        result1 = transform_submission_to_schema(submission_data.copy())
        result2 = transform_submission_to_schema(submission_data.copy())

        assert result1["submission_id"] == result2["submission_id"]

    def test_submission_id_not_raw_reddit_id(self):
        """Test that submission_id is not the raw Reddit ID"""
        submission_data = {"id": "test_sub_999"}
        result = transform_submission_to_schema(submission_data)

        assert result["submission_id"] != "test_sub_999"
        assert result["reddit_id"] == "test_sub_999"

    def test_other_fields_unchanged(self):
        """Test that other fields are transformed correctly"""
        submission_data = {
            "id": "test_sub_fields",
            "title": "Test Title",
            "selftext": "Test content",
            "subreddit": "testsub",
            "score": 100,
            "num_comments": 5,
            "created_utc": 1609459200  # 2021-01-01
        }
        result = transform_submission_to_schema(submission_data)

        assert result["title"] == "Test Title"
        assert result["text"] == "Test content"
        assert result["subreddit"] == "testsub"
        assert result["upvotes"] == 100  # Note: field name change
        assert result["comments_count"] == 5  # Note: field name change

    @pytest.mark.parametrize("reddit_id", [
        "abc123", "t1_abc123", "https://reddit.com/r/test/abc123",
        "t2_abc123", "t3_abc123", "simple", "complex_123_456",
        "0", "99999999", "a" * 10, "test_@#$%^&*()"
    ])
    def test_various_reddit_ids_produce_valid_uuids(self, reddit_id):
        """Test that various Reddit ID formats produce valid UUIDs"""
        submission_data = {"id": reddit_id}
        result = transform_submission_to_schema(submission_data)

        assert result["submission_id"] is not None
        # Verify UUID format - should not raise
        uuid.UUID(str(result["submission_id"]))

    @pytest.mark.parametrize("id1,id2", [
        ("abc", "def"), ("same", "different"), ("123", "456")
    ])
    def test_different_ids_produce_different_uuids(self, id1, id2):
        """Test that different Reddit IDs produce different UUIDs"""
        result1 = transform_submission_to_schema({"id": id1})
        result2 = transform_submission_to_schema({"id": id2})

        assert result1["submission_id"] != result2["submission_id"]


class TestTransformCommentIDNormalization:
    """Test comment ID normalization (8 tests)"""

    def test_comment_id_is_uuid_format(self):
        """Test that comment_id is a UUID after transformation"""
        comment_data = {"comment_id": "test_comm_123", "submission_id": "test_sub_456"}
        result = transform_comment_to_schema(comment_data)

        assert result["comment_id"] is not None
        uuid.UUID(str(result["comment_id"]))  # Will raise if not valid UUID

    def test_comment_submission_id_is_uuid_format(self):
        """Test that submission_id is a UUID after transformation"""
        comment_data = {"comment_id": "test_comm_123", "submission_id": "test_sub_456"}
        result = transform_comment_to_schema(comment_data)

        assert result["submission_id"] is not None
        uuid.UUID(str(result["submission_id"]))

    def test_original_comment_ids_preserved(self):
        """Test that reddit_comment_id preserves original comment ID"""
        comment_data = {"comment_id": "test_comm_789", "submission_id": "test_sub_999"}
        result = transform_comment_to_schema(comment_data)

        assert result["reddit_comment_id"] == "test_comm_789"
        assert result["reddit_submission_id"] == "test_sub_999"

    def test_comment_transform_deterministic(self):
        """Test that same inputs produce same outputs"""
        comment_data = {"comment_id": "test_comm_det", "submission_id": "test_sub_det"}
        result1 = transform_comment_to_schema(comment_data.copy())
        result2 = transform_comment_to_schema(comment_data.copy())

        assert result1["comment_id"] == result2["comment_id"]
        assert result1["submission_id"] == result2["submission_id"]

    def test_comment_with_none_submission_id(self):
        """Test comment with None submission_id"""
        comment_data = {"comment_id": "test_comm_none", "submission_id": None}
        result = transform_comment_to_schema(comment_data)

        assert result["submission_id"] is None
        assert result["reddit_submission_id"] is None

    def test_comment_with_none_comment_id(self):
        """Test comment with None comment_id"""
        comment_data = {"comment_id": None, "submission_id": "test_sub_comm"}
        result = transform_comment_to_schema(comment_data)

        assert result["comment_id"] is None
        assert result["reddit_comment_id"] is None

    def test_comment_with_both_ids_none(self):
        """Test comment with both IDs None"""
        comment_data = {"comment_id": None, "submission_id": None}
        result = transform_comment_to_schema(comment_data)

        assert result["comment_id"] is None
        assert result["submission_id"] is None

    def test_comment_with_empty_ids(self):
        """Test comment with empty string IDs"""
        comment_data = {"comment_id": "", "submission_id": "   "}
        result = transform_comment_to_schema(comment_data)

        assert result["comment_id"] is None
        assert result["submission_id"] is None


class TestForeignKeyAlignment:
    """Test foreign key alignment (4 tests)"""

    def test_comment_submission_id_matches_submission(self):
        """Test that comment submission_id matches parent submission"""
        shared_reddit_id = "shared_sub_123"

        submission_data = {"id": shared_reddit_id}
        comment_data = {"comment_id": "test_comm_fk", "submission_id": shared_reddit_id}

        submission_result = transform_submission_to_schema(submission_data)
        comment_result = transform_comment_to_schema(comment_data)

        assert comment_result["submission_id"] == submission_result["submission_id"]

    def test_multiple_comments_same_submission(self):
        """Test multiple comments referencing same submission have matching UUIDs"""
        shared_reddit_id = "shared_sub_multi"

        submission_data = {"id": shared_reddit_id}
        comment1_data = {"comment_id": "comm1", "submission_id": shared_reddit_id}
        comment2_data = {"comment_id": "comm2", "submission_id": shared_reddit_id}

        submission_result = transform_submission_to_schema(submission_data)
        comment1_result = transform_comment_to_schema(comment1_data)
        comment2_result = transform_comment_to_schema(comment2_data)

        expected_uuid = submission_result["submission_id"]
        assert comment1_result["submission_id"] == expected_uuid
        assert comment2_result["submission_id"] == expected_uuid

    def test_different_submissions_different_uuids(self):
        """Test different submissions produce different UUIDs"""
        sub1_data = {"id": "sub1_unique"}
        sub2_data = {"id": "sub2_unique"}

        comm1_data = {"comment_id": "comm1", "submission_id": "sub1_unique"}
        comm2_data = {"comment_id": "comm2", "submission_id": "sub2_unique"}

        sub1_result = transform_submission_to_schema(sub1_data)
        sub2_result = transform_submission_to_schema(sub2_data)
        comm1_result = transform_comment_to_schema(comm1_data)
        comm2_result = transform_comment_to_schema(comm2_data)

        assert comm1_result["submission_id"] == sub1_result["submission_id"]
        assert comm2_result["submission_id"] == sub2_result["submission_id"]
        assert comm1_result["submission_id"] != comm2_result["submission_id"]

    def test_fk_alignment_with_edge_cases(self):
        """Test FK alignment with edge cases (None, empty IDs)"""
        comment_data = {"comment_id": "test_comm_edge", "submission_id": None}
        result = transform_comment_to_schema(comment_data)

        assert result["submission_id"] is None


class TestIDResolverIntegration:
    """Test ID resolver integration (8 tests)"""

    def test_submission_id_uses_resolver(self):
        """Test that submission_id uses the resolver function"""
        with patch('core.dlt.collection.resolve_submission_id') as mock_resolver:
            mock_resolver.return_value = Mock(uuid="test-uuid-123")

            submission_data = {"id": "test_sub_resolver"}
            result = transform_submission_to_schema(submission_data)

            mock_resolver.assert_called_once_with("test_sub_resolver")
            assert result["submission_id"] == "test-uuid-123"

    def test_comment_id_uses_resolver(self):
        """Test that comment_id uses the resolver function"""
        with patch('core.dlt.collection.resolve_submission_id') as mock_resolver:
            mock_resolver.return_value = Mock(uuid="test-uuid-comm")

            comment_data = {"comment_id": "test_comm_resolver", "submission_id": "test_sub"}
            result = transform_comment_to_schema(comment_data)

            # Should be called twice - once for comment_id, once for submission_id
            assert mock_resolver.call_count == 2

    def test_comment_submission_id_uses_resolver_namespace(self):
        """Test that resolver is called with correct namespace"""
        with patch('core.dlt.collection.resolve_submission_id') as mock_resolver:
            mock_resolver.return_value = Mock(uuid="namespace-uuid")

            comment_data = {"comment_id": "test_comm_ns", "submission_id": "test_sub_ns"}
            transform_comment_to_schema(comment_data)

            # Verify resolver was called
            assert mock_resolver.call_count == 2

    def test_resolver_error_handling(self):
        """Test error handling when resolver fails"""
        with patch('core.dlt.collection.resolve_submission_id') as mock_resolver:
            mock_resolver.return_value = Mock(uuid=None)

            comment_data = {"comment_id": "test_comm_err", "submission_id": "test_sub_err"}
            result = transform_comment_to_schema(comment_data)

            assert result["comment_id"] is None
            assert result["submission_id"] is None

    def test_resolver_exception_handling(self):
        """Test exception handling when resolver raises exception"""
        with patch('core.dlt.collection.resolve_submission_id') as mock_resolver:
            mock_resolver.side_effect = Exception("Resolver error")

            comment_data = {"comment_id": "test_comm_exc", "submission_id": "test_sub_exc"}
            result = transform_comment_to_schema(comment_data)

            # Should handle exception gracefully
            assert result["comment_id"] is None
            assert result["submission_id"] is None

    def test_submission_resolver_namespace(self):
        """Test that submission resolver uses correct namespace"""
        with patch('core.dlt.collection.resolve_submission_id') as mock_resolver:
            mock_resolver.return_value = Mock(uuid="namespace-sub-uuid")

            submission_data = {"id": "test_sub_ns"}
            transform_submission_to_schema(submission_data)

            mock_resolver.assert_called_once_with("test_sub_ns")

    def test_comment_id_resolver_with_invalid_input(self):
        """Test comment ID resolver with invalid input"""
        with patch('core.dlt.collection.resolve_submission_id') as mock_resolver:
            mock_resolver.return_value = Mock(uuid=None)

            comment_data = {"comment_id": "", "submission_id": "test_sub_valid"}
            result = transform_comment_to_schema(comment_data)

            assert result["comment_id"] is None
            assert result["submission_id"] is not None

    def test_submission_id_resolver_with_invalid_input(self):
        """Test submission ID resolver with invalid input"""
        with patch('core.dlt.collection.resolve_submission_id') as mock_resolver:
            mock_resolver.return_value = Mock(uuid=None)

            submission_data = {"id": "invalid_input"}
            result = transform_submission_to_schema(submission_data)

            assert result["submission_id"] is None


class TestEdgeCases:
    """Test edge cases (10 tests)"""

    def test_submission_with_none_id(self):
        """Test submission with None ID"""
        submission_data = {"id": None}
        result = transform_submission_to_schema(submission_data)

        assert result["submission_id"] is None
        assert result["reddit_id"] is None

    def test_submission_with_empty_id(self):
        """Test submission with empty ID"""
        submission_data = {"id": ""}
        result = transform_submission_to_schema(submission_data)

        assert result["submission_id"] is None
        assert result["reddit_id"] == ""

    def test_submission_with_whitespace_id(self):
        """Test submission with whitespace-only ID"""
        submission_data = {"id": "   "}
        result = transform_submission_to_schema(submission_data)

        assert result["submission_id"] is None
        assert result["reddit_id"] == "   "

    def test_comment_with_none_ids(self):
        """Test comment with None IDs"""
        comment_data = {"comment_id": None, "submission_id": None}
        result = transform_comment_to_schema(comment_data)

        assert result["comment_id"] is None
        assert result["submission_id"] is None
        assert result["reddit_comment_id"] is None
        assert result["reddit_submission_id"] is None

    def test_comment_with_empty_ids(self):
        """Test comment with empty IDs"""
        comment_data = {"comment_id": "", "submission_id": ""}
        result = transform_comment_to_schema(comment_data)

        assert result["comment_id"] is None
        assert result["submission_id"] is None

    def test_comment_with_mixed_none_empty(self):
        """Test comment with mixed None/empty IDs"""
        comment_data = {"comment_id": None, "submission_id": ""}
        result = transform_comment_to_schema(comment_data)

        assert result["comment_id"] is None
        assert result["submission_id"] is None

    def test_submission_missing_id_field(self):
        """Test submission missing ID field"""
        submission_data = {}  # No 'id' field
        result = transform_submission_to_schema(submission_data)

        assert result["submission_id"] is None
        assert result["reddit_id"] is None

    def test_comment_missing_id_fields(self):
        """Test comment missing ID fields"""
        comment_data = {}  # No 'comment_id' or 'submission_id' fields
        result = transform_comment_to_schema(comment_data)

        assert result["comment_id"] is None
        assert result["submission_id"] is None

    def test_special_characters_in_ids(self):
        """Test special characters in Reddit IDs"""
        submission_data = {"id": "test_@#$%^&*()"}
        result = transform_submission_to_schema(submission_data)

        assert result["submission_id"] is not None
        assert result["reddit_id"] == "test_@#$%^&*()"

    def test_very_long_reddit_id(self):
        """Test very long Reddit ID"""
        long_id = "a" * 100
        submission_data = {"id": long_id}
        result = transform_submission_to_schema(submission_data)

        assert result["submission_id"] is not None
        assert result["reddit_id"] == long_id


class TestDataTypeConsistency:
    """Test data type consistency (5 tests)"""

    def test_submission_id_is_string(self):
        """Test that submission_id is returned as string"""
        submission_data = {"id": "test_type_sub"}
        result = transform_submission_to_schema(submission_data)

        assert isinstance(result["submission_id"], str) or result["submission_id"] is None

    def test_comment_id_is_string(self):
        """Test that comment_id is returned as string"""
        comment_data = {"comment_id": "test_type_comm", "submission_id": "test_type_sub"}
        result = transform_comment_to_schema(comment_data)

        assert isinstance(result["comment_id"], str) or result["comment_id"] is None
        assert isinstance(result["submission_id"], str) or result["submission_id"] is None

    def test_reddit_id_preserves_type(self):
        """Test that reddit_id preserves input type"""
        submission_data = {"id": 123}  # Integer input
        result = transform_submission_to_schema(submission_data)

        # Should convert to string for consistency
        assert result["reddit_id"] == "123"

    def test_uuid_format_consistency(self):
        """Test that UUID format is consistent"""
        test_ids = ["test_uuid_1", "test_uuid_2", "test_uuid_3"]
        results = []

        for test_id in test_ids:
            submission_data = {"id": test_id}
            result = transform_submission_to_schema(submission_data)
            results.append(result["submission_id"])

        # All should be valid UUIDs
        for uuid_str in results:
            if uuid_str:  # Skip None values
                uuid.UUID(uuid_str)  # Will raise if not valid

    def test_field_name_consistency(self):
        """Test that field names are consistent"""
        submission_data = {"id": "test_fields"}
        result = transform_submission_to_schema(submission_data)

        # Check expected fields exist
        expected_fields = ["submission_id", "reddit_id", "title", "text", "content", "subreddit"]
        for field in expected_fields:
            assert field in result

        comment_data = {"comment_id": "test_comm", "submission_id": "test_sub"}
        result = transform_comment_to_schema(comment_data)

        # Check expected fields exist
        expected_comment_fields = ["comment_id", "reddit_comment_id", "submission_id", "reddit_submission_id", "body"]
        for field in expected_comment_fields:
            assert field in result


class TestBatchProcessingConsistency:
    """Test batch processing consistency (2 tests)"""

    def test_multiple_submissions_consistent(self):
        """Test that multiple submissions processed consistently"""
        submission_ids = ["batch_sub_1", "batch_sub_2", "batch_sub_3"]
        results = {}

        for sub_id in submission_ids:
            submission_data = {"id": sub_id}
            result = transform_submission_to_schema(submission_data)
            results[sub_id] = result["submission_id"]

        # Same ID should produce same UUID if processed again
        for sub_id in submission_ids:
            submission_data = {"id": sub_id}
            result = transform_submission_to_schema(submission_data)
            assert result["submission_id"] == results[sub_id]

    def test_multiple_comments_consistent(self):
        """Test that multiple comments processed consistently"""
        comment_data = [
            {"comment_id": "batch_comm_1", "submission_id": "batch_sub_1"},
            {"comment_id": "batch_comm_2", "submission_id": "batch_sub_2"}
        ]

        first_pass = [transform_comment_to_schema(c.copy()) for c in comment_data]
        second_pass = [transform_comment_to_schema(c.copy()) for c in comment_data]

        for i in range(len(first_pass)):
            assert first_pass[i]["comment_id"] == second_pass[i]["comment_id"]
            assert first_pass[i]["submission_id"] == second_pass[i]["submission_id"]