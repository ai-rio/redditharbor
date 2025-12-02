# Implementation Prompt: Canonical ID Resolver (Phase 1)

**Target Agent**: Claude Code with subagent delegation
**Primary Subagent**: `python-pro` (implementation)
**Secondary Subagent**: `test-engineer` (test suite)
**Scope**: Phase 1 Foundation ONLY (no database integration)

---

## Objective

Implement the canonical ID resolver module for RedditHarbor that provides a single source of truth for submission ID resolution. This module will transform any input format (UUID, Reddit ID, synthetic ID, URL, or dict) into a consistent UUID suitable for database operations.

---

## The Prompt

```
You are implementing Phase 1 of the RedditHarbor ID Resolution fix. Your task is to create the canonical ID resolver module and comprehensive unit tests.

## PROJECT CONTEXT

RedditHarbor's pipeline has ID resolution inconsistencies causing database verification failures. The core issue: data is stored using UUID transformations, but queries use raw IDs like "hybrid_1". This resolver will be the single source of truth for all ID transformations.

## DELIVERABLES

You must create exactly 3 files:

1. `/home/carlos/projects/redditharbor-core-functions-fix/core/utils/id_resolver.py` - Main resolver module
2. `/home/carlos/projects/redditharbor-core-functions-fix/core/utils/__init__.py` - Updated exports (add to existing)
3. `/home/carlos/projects/redditharbor-core-functions-fix/tests/test_id_resolver.py` - Comprehensive unit tests

## SUBAGENT DELEGATION

Use `python-pro` subagent for:
- Creating the id_resolver.py module with type hints, dataclasses, and clean architecture
- Updating the __init__.py exports

Use `test-engineer` subagent for:
- Creating the comprehensive test_id_resolver.py test suite
- Ensuring 100% code coverage of the resolver logic

## FILE 1: core/utils/id_resolver.py

### Required Structure

```python
"""
RedditHarbor Canonical ID Resolver

Provides the single source of truth for submission ID resolution across the
RedditHarbor pipeline. Handles conversion from any input format (UUID, Reddit ID,
synthetic ID, URL, or dict) to a consistent submissions.id UUID.

Author: Data Engineering Team
Date: 2025-11-23
Version: 1.0.0
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

# Fixed namespace for deterministic UUID generation
# This ensures same input always produces same UUID across runs
REDDITHARBOR_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")

# Regex pattern for extracting Reddit ID from URLs
REDDIT_URL_PATTERN = re.compile(
    r"reddit\.com/r/[^/]+/comments/([a-zA-Z0-9]+)"
)

# Regex pattern for validating UUID format
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE
)


@dataclass
class ResolutionResult:
    """Result of ID resolution operation.

    Attributes:
        uuid: The resolved submissions.id UUID (None if resolution failed)
        source: How the UUID was obtained ("database", "passthrough", "generated")
        original_input: String representation of the original input
        error: Error message if resolution failed (None on success)
        metadata: Additional context about the resolution (optional)
    """
    uuid: str | None
    source: Literal["database", "passthrough", "generated"] | None
    original_input: str
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def resolve_submission_id(
    input_value: str | dict[str, Any] | None,
    *,
    require_db_existence: bool = False,
    fallback_to_generated: bool = True,
    supabase_client: Any = None,
) -> ResolutionResult | None:
    """
    Resolve any submission identifier to a canonical UUID.

    This is the single source of truth for submission ID resolution in RedditHarbor.
    It accepts multiple input formats and returns a consistent UUID suitable for
    database operations.

    Args:
        input_value: The input to resolve. Can be:
            - None: Returns None
            - Empty/whitespace string: Returns None
            - UUID string: Validated and passed through
            - Reddit ID: Looked up in database or generated deterministically
            - Synthetic ID: Looked up in database or generated deterministically
            - Reddit URL: ID extracted and processed
            - Dict with submission_id or reddit_id: Field extracted and processed
        require_db_existence: If True, fail when ID not found in database
        fallback_to_generated: If True, generate UUID when database lookup fails
        supabase_client: Optional Supabase client for database lookups
            (Phase 1: not used, Phase 2+: required for database resolution)

    Returns:
        ResolutionResult with resolved UUID and metadata, or None for null/empty input

    Examples:
        >>> resolve_submission_id("hybrid_1")
        ResolutionResult(uuid="...", source="generated", original_input="hybrid_1", ...)

        >>> resolve_submission_id("e7763e41-d7bf-4bf1-a004-decff9f0f0c5")
        ResolutionResult(uuid="e7763e41-d7bf-4bf1-a004-decff9f0f0c5", source="passthrough", ...)

        >>> resolve_submission_id({"submission_id": "test123"})
        ResolutionResult(uuid="...", source="generated", original_input="{'submission_id': ...}", ...)
    """
    # Implementation follows the flowchart from design document
    ...
```

### Resolution Algorithm (MUST implement exactly)

1. **Null/Empty Check**: If input is None, return None. If input is empty string or whitespace-only, return None.

2. **Dict Extraction**: If input is a dict:
   - Check for `submission_id` key first (priority)
   - Fall back to `reddit_id` key if no submission_id
   - If neither key exists, return ResolutionResult with error: "Invalid dict format: missing submission_id and reddit_id"
   - Continue processing with the extracted string value

3. **UUID Validation**: If input matches UUID format (regex: `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`):
   - If require_db_existence is False: Return ResolutionResult with same UUID, source="passthrough"
   - If require_db_existence is True AND supabase_client is None: Return with source="passthrough" (Phase 1 behavior)
   - Phase 2+ will add database existence check here

4. **URL Extraction**: If input contains "reddit.com":
   - Use regex to extract Reddit ID from URL pattern `/comments/([a-zA-Z0-9]+)`
   - If extraction fails, return ResolutionResult with error: "Could not extract Reddit ID from URL: {input}"
   - Continue processing with extracted ID

5. **Database Lookup** (Phase 2+, skip in Phase 1):
   - If supabase_client is provided, query `submissions WHERE reddit_id = :input`
   - If found, return ResolutionResult with submissions.id UUID, source="database"
   - If not found and require_db_existence=True and fallback_to_generated=False:
     Return ResolutionResult with error: "Submission not found and require_db_existence=True"

6. **UUID Generation**: If fallback_to_generated is True:
   - Generate deterministic UUID: `str(uuid.uuid5(REDDITHARBOR_NAMESPACE, input_string))`
   - Return ResolutionResult with generated UUID, source="generated"

7. **Error Fallback**: If fallback_to_generated is False and no resolution found:
   - Return ResolutionResult with error: "Could not resolve submission ID: {input}"

### Helper Functions to Implement

```python
def is_valid_uuid(value: str) -> bool:
    """Check if string is a valid UUID format."""
    ...

def extract_reddit_id_from_url(url: str) -> str | None:
    """Extract Reddit submission ID from a Reddit URL."""
    ...

def generate_deterministic_uuid(input_string: str) -> str:
    """Generate a deterministic UUID using the RedditHarbor namespace."""
    ...

def extract_id_from_dict(data: dict[str, Any]) -> tuple[str | None, str | None]:
    """
    Extract submission ID from a dict.

    Returns:
        Tuple of (extracted_id, extraction_method) or (None, error_message)
    """
    ...
```

## FILE 2: core/utils/__init__.py (UPDATE EXISTING)

Add these exports to the existing __init__.py:

```python
from .id_resolver import (
    ResolutionResult,
    resolve_submission_id,
    is_valid_uuid,
    extract_reddit_id_from_url,
    generate_deterministic_uuid,
    REDDITHARBOR_NAMESPACE,
)
```

Update `__all__` to include all new exports.

## FILE 3: tests/test_id_resolver.py

### Required Test Cases (from design document)

Implement ALL of these test cases:

| Test ID | Test Function | Input | Expected Behavior |
|---------|---------------|-------|-------------------|
| UT-001 | test_resolve_none_input | None | Returns None |
| UT-002 | test_resolve_empty_string | "" | Returns None |
| UT-003 | test_resolve_whitespace_only | "   " | Returns None |
| UT-004 | test_resolve_valid_uuid_passthrough | Valid UUID | Same UUID, source="passthrough" |
| UT-005 | test_resolve_invalid_uuid_format | "not-a-uuid" | Generated UUID, source="generated" |
| UT-006 | test_resolve_synthetic_id | "hybrid_1" | Deterministic UUID, source="generated" |
| UT-007 | test_resolve_reddit_url | Reddit URL | Extracted ID processed, source="generated" |
| UT-008 | test_resolve_dict_with_submission_id | {"submission_id": "..."} | Process submission_id |
| UT-009 | test_resolve_dict_with_reddit_id_only | {"reddit_id": "..."} | Fallback to reddit_id |
| UT-010 | test_resolve_empty_dict | {} | Error result |
| UT-011 | test_uuid_determinism | Same input twice | Same UUID both times |
| UT-012 | test_different_inputs_different_uuids | Different inputs | Different UUIDs |
| UT-013 | test_url_extraction_various_formats | Multiple URL formats | Correct ID extraction |
| UT-014 | test_invalid_url_extraction | Bad URL | Error result |
| UT-015 | test_dict_with_both_fields | Dict with both fields | submission_id takes priority |

### Test File Structure

```python
"""
Unit Tests for RedditHarbor Canonical ID Resolver

Tests cover all input formats and edge cases without database dependency.
These tests verify Phase 1 implementation correctness.

Author: Data Engineering Team
Date: 2025-11-23
"""

import pytest
import uuid

from core.utils.id_resolver import (
    ResolutionResult,
    resolve_submission_id,
    is_valid_uuid,
    extract_reddit_id_from_url,
    generate_deterministic_uuid,
    REDDITHARBOR_NAMESPACE,
)


class TestNullAndEmptyInputs:
    """Test handling of null and empty inputs."""

    def test_resolve_none_input(self):
        """UT-001: None input returns None."""
        result = resolve_submission_id(None)
        assert result is None

    def test_resolve_empty_string(self):
        """UT-002: Empty string returns None."""
        result = resolve_submission_id("")
        assert result is None

    def test_resolve_whitespace_only(self):
        """UT-003: Whitespace-only string returns None."""
        result = resolve_submission_id("   ")
        assert result is None

    def test_resolve_tabs_and_newlines(self):
        """Tabs and newlines should also return None."""
        assert resolve_submission_id("\t\n") is None
        assert resolve_submission_id("  \t  ") is None


class TestUUIDPassthrough:
    """Test UUID format detection and passthrough."""

    def test_resolve_valid_uuid_passthrough(self):
        """UT-004: Valid UUID passes through unchanged."""
        test_uuid = "e7763e41-d7bf-4bf1-a004-decff9f0f0c5"
        result = resolve_submission_id(test_uuid)

        assert result is not None
        assert result.uuid == test_uuid
        assert result.source == "passthrough"
        assert result.error is None

    def test_resolve_valid_uuid_uppercase(self):
        """UUID with uppercase letters should be normalized."""
        test_uuid = "E7763E41-D7BF-4BF1-A004-DECFF9F0F0C5"
        result = resolve_submission_id(test_uuid)

        assert result is not None
        assert result.uuid.lower() == test_uuid.lower()
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
        """UT-006: Synthetic ID 'hybrid_1' generates deterministic UUID."""
        result = resolve_submission_id("hybrid_1")

        assert result is not None
        assert result.uuid is not None
        assert result.source == "generated"
        assert result.original_input == "hybrid_1"
        assert is_valid_uuid(result.uuid)

    def test_resolve_synthetic_id_high_quality(self):
        """Test 'high_quality' synthetic ID."""
        result = resolve_submission_id("high_quality")

        assert result is not None
        assert result.source == "generated"
        assert is_valid_uuid(result.uuid)

    def test_resolve_reddit_style_id(self):
        """Test Reddit-style alphanumeric ID."""
        result = resolve_submission_id("1fp7k8t")

        assert result is not None
        assert result.source == "generated"
        assert is_valid_uuid(result.uuid)


class TestURLExtraction:
    """Test Reddit URL ID extraction."""

    def test_resolve_reddit_url_standard(self):
        """UT-007: Standard Reddit URL extracts ID correctly."""
        url = "https://reddit.com/r/datascience/comments/1fp7k8t/title"
        result = resolve_submission_id(url)

        assert result is not None
        assert result.source == "generated"
        assert result.error is None
        # The extracted ID should produce consistent UUID
        direct_result = resolve_submission_id("1fp7k8t")
        assert result.uuid == direct_result.uuid

    def test_resolve_reddit_url_with_www(self):
        """URL with www prefix."""
        url = "https://www.reddit.com/r/Python/comments/abc123/my_post/"
        result = resolve_submission_id(url)

        assert result is not None
        assert result.source == "generated"

    def test_resolve_reddit_url_old_format(self):
        """Old Reddit URL format."""
        url = "https://old.reddit.com/r/programming/comments/xyz789/discussion"
        result = resolve_submission_id(url)

        assert result is not None
        assert result.source == "generated"

    def test_resolve_invalid_reddit_url(self):
        """UT-014: Invalid Reddit URL returns error."""
        url = "https://reddit.com/r/test/invalid_no_comments"
        result = resolve_submission_id(url)

        assert result is not None
        assert result.error is not None
        assert "Could not extract Reddit ID from URL" in result.error


class TestDictExtraction:
    """Test dict input handling."""

    def test_resolve_dict_with_submission_id(self):
        """UT-008: Dict with submission_id uses that field."""
        data = {"submission_id": "test123", "other": "data"}
        result = resolve_submission_id(data)

        assert result is not None
        assert result.source == "generated"
        assert result.error is None

    def test_resolve_dict_with_reddit_id_only(self):
        """UT-009: Dict with only reddit_id falls back to it."""
        data = {"reddit_id": "1fp7k8t", "title": "Test"}
        result = resolve_submission_id(data)

        assert result is not None
        assert result.source == "generated"
        # Should match direct resolution
        direct = resolve_submission_id("1fp7k8t")
        assert result.uuid == direct.uuid

    def test_resolve_empty_dict(self):
        """UT-010: Empty dict returns error result."""
        result = resolve_submission_id({})

        assert result is not None
        assert result.uuid is None
        assert result.error is not None
        assert "missing submission_id and reddit_id" in result.error

    def test_resolve_dict_with_both_fields(self):
        """UT-015: Dict with both fields prioritizes submission_id."""
        data = {
            "submission_id": "primary_id",
            "reddit_id": "secondary_id"
        }
        result = resolve_submission_id(data)

        # Should use submission_id, not reddit_id
        primary_result = resolve_submission_id("primary_id")
        assert result.uuid == primary_result.uuid

    def test_resolve_dict_with_uuid_submission_id(self):
        """Dict with UUID as submission_id should passthrough."""
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"
        data = {"submission_id": test_uuid}
        result = resolve_submission_id(data)

        assert result is not None
        assert result.uuid == test_uuid
        assert result.source == "passthrough"


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
        # Direct ID
        direct = resolve_submission_id("abc123")

        # Via URL extraction
        url = "https://reddit.com/r/test/comments/abc123/title"
        from_url = resolve_submission_id(url)

        # Via dict
        from_dict = resolve_submission_id({"submission_id": "abc123"})

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

    def test_extract_reddit_id_from_url_valid(self):
        """UT-013: Various URL formats extract correctly."""
        cases = [
            ("https://reddit.com/r/test/comments/abc123/title", "abc123"),
            ("https://www.reddit.com/r/Python/comments/xyz789/post/", "xyz789"),
            ("https://old.reddit.com/r/programming/comments/def456/", "def456"),
        ]
        for url, expected_id in cases:
            result = extract_reddit_id_from_url(url)
            assert result == expected_id, f"Failed for URL: {url}"

    def test_extract_reddit_id_from_url_invalid(self):
        """Invalid URLs return None."""
        assert extract_reddit_id_from_url("https://google.com") is None
        assert extract_reddit_id_from_url("not a url") is None
        assert extract_reddit_id_from_url("https://reddit.com/r/test") is None

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


class TestEdgeCases:
    """Test edge cases and special inputs."""

    def test_very_long_input(self):
        """Very long input strings should still work."""
        long_input = "a" * 10000
        result = resolve_submission_id(long_input)

        assert result is not None
        assert result.source == "generated"
        assert is_valid_uuid(result.uuid)

    def test_special_characters_in_id(self):
        """IDs with special characters should be handled."""
        result = resolve_submission_id("test_id_with_underscores_123")
        assert result is not None
        assert is_valid_uuid(result.uuid)

    def test_unicode_in_input(self):
        """Unicode characters in input should be handled."""
        result = resolve_submission_id("test_unicode_cafe")
        assert result is not None
        assert is_valid_uuid(result.uuid)

    def test_numeric_string(self):
        """Pure numeric strings should be handled."""
        result = resolve_submission_id("1234567890")
        assert result is not None
        assert result.source == "generated"


class TestFallbackBehavior:
    """Test fallback_to_generated parameter behavior."""

    def test_fallback_enabled_default(self):
        """Default behavior generates UUID for unknown IDs."""
        result = resolve_submission_id("unknown_id_12345")

        assert result is not None
        assert result.uuid is not None
        assert result.source == "generated"

    def test_fallback_disabled_no_db(self):
        """With fallback disabled and no DB, should error."""
        result = resolve_submission_id(
            "unknown_id",
            fallback_to_generated=False,
            supabase_client=None
        )

        assert result is not None
        assert result.uuid is None
        assert result.error is not None


class TestResolutionResultDataclass:
    """Test ResolutionResult dataclass behavior."""

    def test_result_has_all_fields(self):
        """Result has all expected fields."""
        result = resolve_submission_id("test")

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
        result = resolve_submission_id("my_test_input")

        assert "my_test_input" in result.original_input
```

## VERIFICATION STEPS

After implementation, run these commands to verify:

```bash
# Navigate to project root
cd /home/carlos/projects/redditharbor-core-functions-fix

# Run ruff formatting
ruff format core/utils/id_resolver.py tests/test_id_resolver.py

# Run ruff linting
ruff check core/utils/id_resolver.py tests/test_id_resolver.py

# Run tests with coverage
pytest tests/test_id_resolver.py -v --tb=short

# Verify all tests pass
pytest tests/test_id_resolver.py -v --tb=short | grep -E "(PASSED|FAILED|ERROR)"
```

## SUCCESS CRITERIA

Phase 1 is complete when:

1. [ ] `core/utils/id_resolver.py` exists with all required functions
2. [ ] `core/utils/__init__.py` exports all new symbols
3. [ ] `tests/test_id_resolver.py` has all required test cases
4. [ ] All tests pass: `pytest tests/test_id_resolver.py -v`
5. [ ] Code passes ruff formatting: `ruff format --check core/utils/id_resolver.py`
6. [ ] Code passes ruff linting: `ruff check core/utils/id_resolver.py`
7. [ ] Same input always produces same UUID (determinism verified)
8. [ ] No database connection required for tests

## CONSTRAINTS

1. **Python 3.11+**: Use modern type hints (str | None, not Optional[str])
2. **No external dependencies**: Only standard library (uuid, re, dataclasses, typing)
3. **Thread-safe**: No global mutable state
4. **Follow existing patterns**: Match style in core/utils/logging.py
5. **Docstrings**: Use Google style with Args, Returns, Raises sections
6. **No database calls in Phase 1**: supabase_client parameter should be ignored

## REPORT

After successful implementation, create a brief report at:
`/home/carlos/projects/redditharbor-core-functions-fix/docs/id-resolution-fix/reports/03-implement-report.md`

Include:
- Files created/modified
- Test results summary
- Any deviations from design
- Ready for Phase 2 confirmation
```

---

## Implementation Notes

### Key Techniques Used

1. **Explicit Scope Limitation**: The prompt clearly states "Phase 1 ONLY" multiple times to prevent scope creep into database integration

2. **Subagent Delegation Pattern**: Explicitly specifies which subagent to use for each component (python-pro for implementation, test-engineer for tests)

3. **Complete Code Templates**: Provides skeleton code with docstrings and type hints to ensure consistent style

4. **Test-First Specification**: All test cases are pre-defined from the design document, ensuring coverage requirements are met

5. **Verification Commands**: Concrete bash commands for validation prevent ambiguity about "done"

6. **Success Criteria Checklist**: Binary checkboxes make completion unambiguous

7. **Pattern References**: Points to existing code (core/utils/logging.py) for style consistency

### Design Choices

1. **Dataclass over TypedDict**: ResolutionResult uses dataclass for better IDE support and validation

2. **Literal types for source**: Ensures only valid source values are used

3. **Factory default for metadata**: `field(default_factory=dict)` prevents mutable default issues

4. **Regex constants at module level**: Compiled once, reused for performance

5. **Keyword-only arguments**: Forces explicit parameter naming for clarity

### Expected Outcomes

The implementation should:
- Handle all input formats specified in the design document
- Generate deterministic UUIDs using uuid5 with fixed namespace
- Be thread-safe with no global mutable state
- Pass all unit tests without database connection
- Be ready for Phase 2 database integration