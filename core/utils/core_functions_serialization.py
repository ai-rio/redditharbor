#!/usr/bin/env python3
"""
Core Functions Serialization Utilities

Standardizes core_functions serialization across the RedditHarbor codebase.
Ensures consistent JSON string → JSONB conversion for database storage.

Author: Claude Code
Purpose: Fix core_functions format inconsistency identified in schema consolidation
"""

import json
from typing import Any, Union


def serialize_core_functions(functions: list[str] | str | None) -> str:
    """
    Serialize core_functions to JSON string for JSONB storage.

    This function ensures consistent serialization across all pipelines:
    - Converts Python lists to JSON strings (Format A)
    - Converts comma-separated strings to JSON arrays
    - Handles None and empty values

    Args:
        functions: Core functions as list, string, or None

    Returns:
        JSON string suitable for JSONB column

    Examples:
        >>> serialize_core_functions(["func1", "func2"])
        '[\"func1\", \"func2\"]'

        >>> serialize_core_functions("func1, func2")
        '[\"func1\", \"func2\"]'

        >>> serialize_core_functions(None)
        '[]'
    """
    if functions is None:
        return json.dumps([])

    if isinstance(functions, list):
        # Filter out empty strings and validate
        clean_functions = [f.strip() for f in functions if f and f.strip()]
        return json.dumps(clean_functions)

    if isinstance(functions, str):
        # Handle comma-separated strings
        if functions.strip().startswith('['):
            # Already JSON format
            try:
                parsed = json.loads(functions)
                if isinstance(parsed, list):
                    return json.dumps(parsed)
            except json.JSONDecodeError:
                pass

        # Split comma-separated values
        if ',' in functions:
            split_functions = [f.strip() for f in functions.split(',') if f.strip()]
            return json.dumps(split_functions)

        # Single function as string
        clean_func = functions.strip()
        if clean_func:
            return json.dumps([clean_func])

    # Fallback: try to convert to string and handle as single function
    try:
        str_func = str(functions).strip()
        if str_func:
            return json.dumps([str_func])
    except Exception:
        pass

    # Ultimate fallback
    return json.dumps([])


def deserialize_core_functions(json_str: str) -> list[str]:
    """
    Deserialize core_functions from JSON string.

    Args:
        json_str: JSON string from database

    Returns:
        List of function names

    Examples:
        >>> deserialize_core_functions('["func1", "func2"]')
        ['func1', 'func2']

        >>> deserialize_core_functions('[]')
        []
    """
    if not json_str or json_str.strip() == '':
        return []

    try:
        result = json.loads(json_str)
        if isinstance(result, list):
            return [str(item) for item in result if item]
    except (json.JSONDecodeError, TypeError):
        # Handle cases where data might be stored as plain string
        if json_str != 'null':
            return [json_str]

    return []


def validate_core_functions(functions: list[str]) -> list[str]:
    """
    Validate and clean core_functions list.

    Ensures:
    - 1-3 functions maximum
    - No empty strings
    - Proper string formatting

    Args:
        functions: List of function names

    Returns:
        Validated list of function names

    Raises:
        ValueError: If no valid functions provided
    """
    clean_functions = [f.strip() for f in functions if f and f.strip()]

    if not clean_functions:
        raise ValueError("At least one valid core function must be provided")

    if len(clean_functions) > 3:
        clean_functions = clean_functions[:3]

    return clean_functions


# Type hints for better IDE support
CoreFunctionsType = Union[list[str], str, None]
SerializedCoreFunctions = str


def standardize_core_functions(functions: CoreFunctionsType) -> SerializedCoreFunctions:
    """
    Main entry point for standardizing core_functions.

    This is the recommended function to use throughout the codebase
    for consistent core_functions handling.

    Args:
        functions: Core functions in any supported format

    Returns:
        Serialized JSON string for database storage

    Example usage in data pipelines:
        >>> profile["core_functions"] = standardize_core_functions(["func1", "func2"])
        >>> profile["core_functions"] = standardize_core_functions("func1, func2")
        >>> profile["core_functions"] = standardize_core_functions(None)
    """
    return serialize_core_functions(functions)


# DLT-specific helper for resource functions
def dlt_standardize_core_functions(profile: dict[str, Any]) -> dict[str, Any]:
    """
    Standardize core_functions in a profile dictionary for DLT pipelines.

    This function is designed to be used in DLT resource functions
    to ensure consistent core_functions serialization.

    Args:
        profile: Dictionary containing core_functions field

    Returns:
        Modified profile with standardized core_functions

    Example:
        >>> profile = {"core_functions": ["func1", "func2"]}
        >>> profile = dlt_standardize_core_functions(profile)
        >>> profile["core_functions"]  # '[\"func1\", \"func2\"]'
    """
    if "core_functions" in profile:
        profile["core_functions"] = standardize_core_functions(profile["core_functions"])

    return profile
