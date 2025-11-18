#!/usr/bin/env python3
"""
Comprehensive test suite for core_functions serialization standardization.

This test validates that:
1. All three formats (list, comma-separated string, JSON string) are handled
2. Serialization produces consistent JSON strings for JSONB storage
3. Deserialization properly converts back to Python lists
4. Integration with DLT pipelines works correctly
5. Backward compatibility is maintained

Author: Claude Code
Purpose: Test the core_functions format fix
"""

import json
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.utils.core_functions_serialization import (
    serialize_core_functions,
    deserialize_core_functions,
    validate_core_functions,
    standardize_core_functions,
    dlt_standardize_core_functions,
    CoreFunctionsType,
    SerializedCoreFunctions
)


class TestCoreFunctionsSerialization:
    """Test core functions serialization utilities."""

    def test_serialize_list_input(self):
        """Test serialization with Python list input."""
        functions = ["Task management", "automation", "analytics"]
        result = serialize_core_functions(functions)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == functions
        assert len(parsed) == 3

    def test_serialize_comma_separated_string(self):
        """Test serialization with comma-separated string input."""
        functions_str = "Task management, automation, analytics"
        result = serialize_core_functions(functions_str)

        assert isinstance(result, str)
        parsed = json.loads(result)
        expected = ["Task management", "automation", "analytics"]
        assert parsed == expected

    def test_serialize_json_string_input(self):
        """Test serialization with JSON string input."""
        json_str = '["Task management", "automation", "analytics"]'
        result = serialize_core_functions(json_str)

        assert isinstance(result, str)
        parsed = json.loads(result)
        expected = ["Task management", "automation", "analytics"]
        assert parsed == expected

    def test_serialize_single_string(self):
        """Test serialization with single string input."""
        single_func = "Task management"
        result = serialize_core_functions(single_func)

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == ["Task management"]

    def test_serialize_empty_input(self):
        """Test serialization with None/empty input."""
        result_none = serialize_core_functions(None)
        result_empty = serialize_core_functions("")

        assert result_none == result_empty == '[]'
        parsed = json.loads(result_none)
        assert parsed == []

    def test_deserialize_valid_json(self):
        """Test deserialization with valid JSON string."""
        json_str = '["Task management", "automation", "analytics"]'
        result = deserialize_core_functions(json_str)

        assert isinstance(result, list)
        assert result == ["Task management", "automation", "analytics"]

    def test_deserialize_empty_string(self):
        """Test deserialization with empty string."""
        result_empty = deserialize_core_functions("")
        result_null = deserialize_core_functions("null")

        assert result_empty == result_null == []

    def test_deserialize_invalid_json(self):
        """Test deserialization with invalid JSON falls back to string."""
        invalid_str = "not a json"
        result = deserialize_core_functions(invalid_str)

        # Should fall back to treating the input as a single function
        assert result == [invalid_str]

    def test_validate_core_functions(self):
        """Test core functions validation."""
        valid_functions = ["Task management", "automation", "analytics"]
        too_many_functions = ["func1", "func2", "func3", "func4", "func5"]
        empty_functions = ["", "   ", "", "valid"]

        result_valid = validate_core_functions(valid_functions)
        result_too_many = validate_core_functions(too_many_functions)
        result_empty = validate_core_functions(empty_functions)

        assert result_valid == valid_functions
        assert len(result_too_many) == 3  # Truncated to 3
        assert result_empty == ["valid"]  # Empty strings filtered out

    def test_validate_empty_input_raises_error(self):
        """Test that validation raises error for no valid functions."""
        with pytest.raises(ValueError, match="At least one valid core function"):
            validate_core_functions([])

    def test_standardize_core_functions_main_entry_point(self):
        """Test the main standardize_core_functions function."""
        # Test all input types
        list_input = ["func1", "func2"]
        string_input = "func1, func2"
        json_input = '["func1", "func2"]'

        result_list = standardize_core_functions(list_input)
        result_string = standardize_core_functions(string_input)
        result_json = standardize_core_functions(json_input)

        # All should produce the same JSON string
        assert result_list == result_string == result_json

        # Verify it's valid JSON
        parsed = json.loads(result_list)
        assert parsed == ["func1", "func2"]

    def test_dlt_standardize_core_functions_profile(self):
        """Test DLT-specific profile standardization."""
        profile = {
            "submission_id": "test123",
            "app_concept": "Test app",
            "core_functions": ["func1", "func2", "func3"],
            "other_field": "unchanged"
        }

        result = dlt_standardize_core_functions(profile)

        # Should modify the profile in place and return it
        assert result is profile
        assert profile["core_functions"] == json.dumps(["func1", "func2", "func3"])
        assert profile["other_field"] == "unchanged"

    def test_dlt_standardize_core_functions_no_field(self):
        """Test DLT profile standardization when field is missing."""
        profile = {
            "submission_id": "test123",
            "app_concept": "Test app"
        }

        result = dlt_standardize_core_functions(profile)

        # Should not add the field if missing
        assert "core_functions" not in profile
        assert result is profile


class TestFormatStandardization:
    """Test that the three identified formats are properly handled."""

    def test_format_a_json_string_to_jsonb(self):
        """Test Format A: JSON string → JSONB (correct format)."""
        # This is the target format
        json_string = json.dumps(["func1", "func2", "func3"])

        # Should pass through unchanged
        result = standardize_core_functions(json_string)
        assert result == json_string

        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed == ["func1", "func2", "func3"]

    def test_format_b_python_list_to_text(self):
        """Test Format B: Python list → TEXT (needs fix)."""
        python_list = ["func1", "func2", "func3"]

        # Should be converted to JSON string
        result = standardize_core_functions(python_list)
        assert isinstance(result, str)

        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed == python_list

    def test_format_c_jsonb_native(self):
        """Test Format C: JSONB native (target database format)."""
        # This is what the database expects to receive
        python_list = ["func1", "func2", "func3"]
        json_string = json.dumps(python_list)

        # Our utility should produce this format
        result = standardize_core_functions(python_list)
        assert result == json_string


class TestBackwardCompatibility:
    """Test backward compatibility with existing data."""

    def test_handle_legacy_comma_separated_data(self):
        """Test handling of legacy comma-separated data."""
        legacy_comma = "Task management, automation, analytics"

        result = standardize_core_functions(legacy_comma)

        # Should convert to proper JSON array
        parsed = json.loads(result)
        expected = ["Task management", "automation", "analytics"]
        assert parsed == expected

    def test_handle_legacy_mixed_formats(self):
        """Test handling of mixed legacy formats."""
        test_cases = [
            ["func1", "func2"],  # Python list
            "func1, func2",      # Comma-separated
            '["func1", "func2"]',  # JSON string
            "func1",              # Single function
            None,                 # Empty/null
        ]

        expected_json = '["func1", "func2"]'

        # All should serialize to the same format (except single function and None)
        assert standardize_core_functions(["func1", "func2"]) == expected_json
        assert json.loads(standardize_core_functions("func1, func2")) == ["func1", "func2"]
        assert standardize_core_functions('["func1", "func2"]') == expected_json
        assert json.loads(standardize_core_functions("func1")) == ["func1"]
        assert standardize_core_functions(None) == '[]'


class TestDLTIntegration:
    """Test integration with DLT pipelines."""

    def test_dlt_resource_compatibility(self):
        """Test that standardized data works with DLT resources."""
        # Simulate what happens in DLT resources
        profile_data = {
            "submission_id": "test123",
            "core_functions": ["Task management", "automation", "analytics"]
        }

        # Standardize for DLT
        standardized = dlt_standardize_core_functions(profile_data)

        # Verify it's a JSON string that DLT can handle
        core_functions = standardized["core_functions"]
        assert isinstance(core_functions, str)

        # DLT will handle the JSON string to JSONB conversion
        parsed = json.loads(core_functions)
        assert len(parsed) == 3
        assert "Task management" in parsed

    def test_round_trip_serialization(self):
        """Test that serialization/deserialization round trip works."""
        original = ["Task management", "automation", "analytics"]

        # Serialize (what gets stored in database)
        serialized = standardize_core_functions(original)

        # Deserialize (what gets read back)
        deserialized = deserialize_core_functions(serialized)

        # Should be identical
        assert deserialized == original


class TestTypeHints:
    """Test type hints and IDE support."""

    def test_core_functions_type_union(self):
        """Test that CoreFunctionsType accepts all supported formats."""
        test_values: CoreFunctionsType = [
            ["func1", "func2"],  # List
            "func1, func2",      # Comma-separated string
            '["func1", "func2"]',  # JSON string
            "func1",              # Single string
            None                  # None
        ]

        for value in test_values:
            result = standardize_core_functions(value)
            assert isinstance(result, str)
            assert isinstance(result, SerializedCoreFunctions)

    def test_serialized_type_validation(self):
        """Test that SerializedCoreFunctions is always a JSON string."""
        result: SerializedCoreFunctions = standardize_core_functions(["test"])

        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)  # Should not raise


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])