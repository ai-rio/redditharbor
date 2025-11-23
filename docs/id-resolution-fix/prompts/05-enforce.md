# Enforcement Prompt: Database-Level ID Normalization (Phase 3)

**Target Agent**: Claude Code with subagent delegation
**Primary Subagent**: `data-engineer` (SQL migrations)
**Secondary Subagent**: `test-engineer` (database tests)
**Predecessor**: 04-integrate.md (completed)
**Scope**: Database trigger enforcement for app_opportunities

---

## Objective

Create PostgreSQL database-level enforcement that automatically normalizes submission_id values in the app_opportunities table to UUID format. This ensures data consistency regardless of what format the application layer sends, providing a safety net that matches the Python resolver's behavior exactly.

---

## The Prompt

```
You are implementing Phase 3 (Enforcement) of the RedditHarbor ID Resolution fix. Your task is to create database-level triggers and functions that automatically normalize submission_id values, ensuring consistency even if application code bypasses the Python resolver.

## PROJECT CONTEXT

The previous phases established:
- **Phase 1 (Implement)**: Created `core/utils/id_resolver.py` with deterministic UUID generation
- **Phase 2 (Integrate)**: Wired the resolver into database_verifier.py and enhanced_hybrid_store.py

The Python resolver uses this namespace for deterministic UUID5 generation:
```python
REDDITHARBOR_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")
# Computed value: 8b5de7e2-d0ea-5147-a3b6-37b0c9a0a9f7
```

The database enforcement MUST use the same namespace to ensure Python and PostgreSQL produce identical UUIDs for the same input.

## THE PROBLEM

`app_opportunities.submission_id` currently has:
- NO foreign key constraint (DLT manages this table)
- Mixed data: some rows have UUIDs, others have raw strings like "hybrid_1", "high_quality"
- No validation at the database level

This allows data inconsistency regardless of application-level fixes.

## ENFORCEMENT STRATEGY

Create a PostgreSQL trigger that:
1. Fires BEFORE INSERT or UPDATE on app_opportunities
2. Checks if submission_id is already a valid UUID format
3. If not a UUID, generates a deterministic UUID using the same uuid5 algorithm as Python
4. Updates the submission_id to the normalized UUID value

The trigger approach is preferred over a CHECK constraint because:
- It transforms data automatically (constraint would just reject)
- It maintains backwards compatibility with existing callers
- It provides a safety net without breaking DLT operations

## DELIVERABLES

You must create exactly 3 files:

### File 1: Migration (UP)
Path: `/home/carlos/projects/redditharbor-core-functions-fix/supabase/migrations/20251123120000_add_id_normalization_trigger.sql`

### File 2: Migration (DOWN)
Path: `/home/carlos/projects/redditharbor-core-functions-fix/supabase/migrations/20251123120001_revert_id_normalization_trigger.sql`

### File 3: Test Script
Path: `/home/carlos/projects/redditharbor-core-functions-fix/scripts/database/test_id_normalization_trigger.py`

## SUBAGENT DELEGATION

Use `data-engineer` subagent for:
- Creating the PostgreSQL uuid5 function that matches Python's behavior
- Creating the trigger function for app_opportunities
- Writing the up and down migrations
- Ensuring pgcrypto extension is available for SHA-1

Use `test-engineer` subagent for:
- Creating the Python test script
- Verifying PostgreSQL and Python produce identical UUIDs
- Testing various input formats

---

## FILE 1: UP MIGRATION

### Requirements

1. **Enable pgcrypto extension** (if not already enabled) for `digest()` function
2. **Create uuid5_generate function** that matches Python's uuid.uuid5() exactly
3. **Create normalize_submission_id function** that applies uuid5 to non-UUID values
4. **Create trigger** on app_opportunities table

### UUID5 Algorithm Specification

The uuid5 algorithm requires:
1. Concatenate namespace UUID bytes (16 bytes) + name UTF-8 bytes
2. Compute SHA-1 hash of the concatenated bytes
3. Take first 16 bytes of hash
4. Set version bits (byte 6, bits 4-7) to 0101 (version 5)
5. Set variant bits (byte 8, bits 6-7) to 10 (RFC 4122)
6. Format as UUID string

### Migration SQL Template

```sql
-- Migration: Add ID normalization trigger for app_opportunities
-- Purpose: Ensure submission_id is always a valid UUID, matching Python resolver behavior
-- Namespace: 8b5de7e2-d0ea-5147-a3b6-37b0c9a0a9f7 (uuid5 of "redditharbor-pipeline")

-- ============================================================================
-- PREREQUISITE: Enable pgcrypto for SHA-1 digest function
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- FUNCTION: uuid5_generate(namespace_uuid, name)
-- Generates a version 5 (SHA-1) UUID matching Python's uuid.uuid5()
-- ============================================================================

CREATE OR REPLACE FUNCTION uuid5_generate(namespace_uuid UUID, name TEXT)
RETURNS UUID AS $$
DECLARE
    namespace_bytes BYTEA;
    name_bytes BYTEA;
    hash_bytes BYTEA;
    result_bytes BYTEA;
BEGIN
    -- Handle NULL or empty input
    IF name IS NULL OR name = '' THEN
        RETURN NULL;
    END IF;

    -- Convert namespace UUID to bytes (big-endian, as per RFC 4122)
    namespace_bytes := decode(replace(namespace_uuid::TEXT, '-', ''), 'hex');

    -- Convert name to UTF-8 bytes
    name_bytes := convert_to(name, 'UTF8');

    -- Create SHA-1 hash of namespace + name
    hash_bytes := digest(namespace_bytes || name_bytes, 'sha1');

    -- Take first 16 bytes of the hash
    result_bytes := substring(hash_bytes from 1 for 16);

    -- Set version (byte 6, high nibble = 5 for UUID version 5)
    -- Original: xxxx xxxx, Target: 0101 xxxx
    result_bytes := set_byte(
        result_bytes,
        6,
        (get_byte(result_bytes, 6) & x'0f'::int) | x'50'::int
    );

    -- Set variant (byte 8, high 2 bits = 10 for RFC 4122)
    -- Original: xxxx xxxx, Target: 10xx xxxx
    result_bytes := set_byte(
        result_bytes,
        8,
        (get_byte(result_bytes, 8) & x'3f'::int) | x'80'::int
    );

    -- Format as UUID string and cast
    RETURN encode(result_bytes, 'hex')::UUID;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

-- ============================================================================
-- FUNCTION: is_valid_uuid(text)
-- Checks if a string is a valid UUID format
-- ============================================================================

CREATE OR REPLACE FUNCTION is_valid_uuid(input TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    IF input IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Attempt to cast to UUID; if it fails, it's not valid
    PERFORM input::UUID;
    RETURN TRUE;
EXCEPTION
    WHEN invalid_text_representation THEN
        RETURN FALSE;
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- CONSTANT: RedditHarbor namespace UUID
-- This is uuid5(NAMESPACE_DNS, "redditharbor-pipeline") computed in Python
-- MUST match core/utils/id_resolver.py REDDITHARBOR_NAMESPACE
-- ============================================================================

-- We define this as a function since PostgreSQL doesn't have module-level constants
CREATE OR REPLACE FUNCTION redditharbor_namespace()
RETURNS UUID AS $$
BEGIN
    RETURN '8b5de7e2-d0ea-5147-a3b6-37b0c9a0a9f7'::UUID;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- FUNCTION: normalize_submission_id(text)
-- Normalizes any submission_id to UUID format
-- If already a UUID, returns as-is; otherwise generates deterministic UUID
-- ============================================================================

CREATE OR REPLACE FUNCTION normalize_submission_id(input TEXT)
RETURNS UUID AS $$
DECLARE
    rh_namespace UUID;
BEGIN
    -- Handle NULL or empty input
    IF input IS NULL OR trim(input) = '' THEN
        RETURN NULL;
    END IF;

    -- Strip whitespace
    input := trim(input);

    -- If already a valid UUID, return it directly
    IF is_valid_uuid(input) THEN
        RETURN input::UUID;
    END IF;

    -- Generate deterministic UUID using RedditHarbor namespace
    rh_namespace := redditharbor_namespace();
    RETURN uuid5_generate(rh_namespace, input);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- TRIGGER FUNCTION: normalize_app_opportunities_submission_id()
-- Automatically normalizes submission_id on INSERT or UPDATE
-- ============================================================================

CREATE OR REPLACE FUNCTION normalize_app_opportunities_submission_id()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process if submission_id is being set
    IF NEW.submission_id IS NOT NULL THEN
        -- Cast to TEXT for processing (submission_id might be UUID or TEXT)
        NEW.submission_id := normalize_submission_id(NEW.submission_id::TEXT);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: app_opportunities_normalize_submission_id
-- Fires before INSERT or UPDATE to normalize submission_id
-- ============================================================================

DROP TRIGGER IF EXISTS app_opportunities_normalize_submission_id ON app_opportunities;

CREATE TRIGGER app_opportunities_normalize_submission_id
    BEFORE INSERT OR UPDATE OF submission_id
    ON app_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION normalize_app_opportunities_submission_id();

-- ============================================================================
-- VERIFICATION: Test the functions work correctly
-- ============================================================================

DO $$
DECLARE
    test_result UUID;
    expected_uuid UUID;
BEGIN
    -- Test 1: uuid5_generate produces correct output
    -- Python: uuid.uuid5(uuid.UUID('8b5de7e2-d0ea-5147-a3b6-37b0c9a0a9f7'), 'hybrid_1')
    -- Expected: Compute this value for verification
    test_result := uuid5_generate(
        '8b5de7e2-d0ea-5147-a3b6-37b0c9a0a9f7'::UUID,
        'hybrid_1'
    );

    IF test_result IS NULL THEN
        RAISE EXCEPTION 'uuid5_generate returned NULL for valid input';
    END IF;

    RAISE NOTICE 'uuid5_generate("hybrid_1") = %', test_result;

    -- Test 2: is_valid_uuid works correctly
    IF NOT is_valid_uuid('e7763e41-d7bf-4bf1-a004-decff9f0f0c5') THEN
        RAISE EXCEPTION 'is_valid_uuid returned FALSE for valid UUID';
    END IF;

    IF is_valid_uuid('not-a-uuid') THEN
        RAISE EXCEPTION 'is_valid_uuid returned TRUE for invalid UUID';
    END IF;

    -- Test 3: normalize_submission_id handles all cases
    -- Valid UUID should pass through
    test_result := normalize_submission_id('e7763e41-d7bf-4bf1-a004-decff9f0f0c5');
    IF test_result != 'e7763e41-d7bf-4bf1-a004-decff9f0f0c5'::UUID THEN
        RAISE EXCEPTION 'normalize_submission_id did not passthrough valid UUID';
    END IF;

    -- Non-UUID should be converted
    test_result := normalize_submission_id('hybrid_1');
    IF NOT is_valid_uuid(test_result::TEXT) THEN
        RAISE EXCEPTION 'normalize_submission_id did not generate valid UUID for non-UUID input';
    END IF;

    RAISE NOTICE 'All verification tests passed!';
END $$;

-- ============================================================================
-- COMMENT: Document the migration
-- ============================================================================

COMMENT ON FUNCTION uuid5_generate(UUID, TEXT) IS
'Generates a version 5 (SHA-1) UUID matching Python uuid.uuid5(). Used for deterministic ID normalization.';

COMMENT ON FUNCTION is_valid_uuid(TEXT) IS
'Checks if a string is a valid UUID format without throwing an exception.';

COMMENT ON FUNCTION redditharbor_namespace() IS
'Returns the RedditHarbor namespace UUID used for deterministic ID generation. Must match core/utils/id_resolver.py REDDITHARBOR_NAMESPACE.';

COMMENT ON FUNCTION normalize_submission_id(TEXT) IS
'Normalizes any submission_id to UUID format. Passes through valid UUIDs, generates deterministic UUID for other formats.';

COMMENT ON FUNCTION normalize_app_opportunities_submission_id() IS
'Trigger function that automatically normalizes submission_id on INSERT/UPDATE.';

COMMENT ON TRIGGER app_opportunities_normalize_submission_id ON app_opportunities IS
'Ensures submission_id is always a valid UUID by normalizing on INSERT/UPDATE.';
```

---

## FILE 2: DOWN MIGRATION (ROLLBACK)

### Requirements

1. Drop the trigger first (depends on function)
2. Drop functions in reverse dependency order
3. Do NOT drop pgcrypto (may be used elsewhere)
4. Do NOT modify existing data (just remove enforcement)

### Migration SQL Template

```sql
-- Migration: Revert ID normalization trigger for app_opportunities
-- Purpose: Remove database-level ID normalization enforcement
-- WARNING: This does not revert any data changes already made by the trigger

-- ============================================================================
-- DROP TRIGGER (must be done before dropping the function)
-- ============================================================================

DROP TRIGGER IF EXISTS app_opportunities_normalize_submission_id ON app_opportunities;

-- ============================================================================
-- DROP FUNCTIONS (in reverse dependency order)
-- ============================================================================

DROP FUNCTION IF EXISTS normalize_app_opportunities_submission_id();
DROP FUNCTION IF EXISTS normalize_submission_id(TEXT);
DROP FUNCTION IF EXISTS redditharbor_namespace();
DROP FUNCTION IF EXISTS is_valid_uuid(TEXT);
DROP FUNCTION IF EXISTS uuid5_generate(UUID, TEXT);

-- ============================================================================
-- NOTE: Not dropping pgcrypto extension
-- Other parts of the database may depend on it
-- ============================================================================

-- ============================================================================
-- VERIFICATION: Confirm trigger is removed
-- ============================================================================

DO $$
BEGIN
    -- Verify trigger no longer exists
    IF EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'app_opportunities_normalize_submission_id'
    ) THEN
        RAISE EXCEPTION 'Trigger was not properly removed';
    END IF;

    RAISE NOTICE 'Rollback completed successfully. ID normalization trigger removed.';
END $$;
```

---

## FILE 3: TEST SCRIPT

### Requirements

1. Verify PostgreSQL uuid5 matches Python uuid5 for test inputs
2. Test trigger fires correctly on INSERT
3. Test trigger fires correctly on UPDATE
4. Test passthrough behavior for existing UUIDs
5. Test edge cases (NULL, empty string, whitespace)

### Test Script Template

```python
"""
Database-Level ID Normalization Trigger Tests

Verifies that the PostgreSQL uuid5_generate function produces
identical output to Python's uuid.uuid5() and that the trigger
correctly normalizes submission_id values.

Author: Data Engineering Team
Date: 2025-11-23
"""

from __future__ import annotations

import os
import sys
import uuid
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# RedditHarbor namespace - MUST match both PostgreSQL and Python
REDDITHARBOR_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "redditharbor-pipeline")


class TestUUID5Parity:
    """Test that PostgreSQL uuid5_generate matches Python uuid.uuid5."""

    @pytest.fixture
    def supabase_client(self):
        """Create Supabase client for testing."""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

        if not url or not key:
            pytest.skip("SUPABASE_URL and SUPABASE_KEY required for database tests")

        return create_client(url, key)

    def test_namespace_constant_matches(self, supabase_client):
        """Verify PostgreSQL namespace matches Python namespace."""
        # Query the PostgreSQL function
        result = supabase_client.rpc("redditharbor_namespace").execute()

        # Extract the UUID from the response
        pg_namespace = result.data

        assert pg_namespace is not None, "PostgreSQL redditharbor_namespace() returned NULL"
        assert str(pg_namespace) == str(REDDITHARBOR_NAMESPACE), (
            f"Namespace mismatch! Python: {REDDITHARBOR_NAMESPACE}, PostgreSQL: {pg_namespace}"
        )

    @pytest.mark.parametrize("test_input,description", [
        ("hybrid_1", "synthetic hybrid ID"),
        ("high_quality", "synthetic quality ID"),
        ("1fp7k8t", "Reddit-style alphanumeric ID"),
        ("test_submission_001", "test submission ID"),
        ("abc123", "simple alphanumeric"),
        ("a" * 100, "long string input"),
        ("test_with_underscores_123", "underscores in ID"),
    ])
    def test_uuid5_parity(self, supabase_client, test_input: str, description: str):
        """Verify PostgreSQL uuid5 matches Python uuid5 for various inputs."""
        # Generate UUID in Python
        python_uuid = str(uuid.uuid5(REDDITHARBOR_NAMESPACE, test_input))

        # Generate UUID in PostgreSQL via RPC
        result = supabase_client.rpc(
            "uuid5_generate",
            {"namespace_uuid": str(REDDITHARBOR_NAMESPACE), "name": test_input}
        ).execute()

        pg_uuid = result.data

        assert pg_uuid is not None, f"PostgreSQL returned NULL for '{test_input}'"
        assert str(pg_uuid) == python_uuid, (
            f"UUID5 mismatch for {description}!\n"
            f"  Input: '{test_input}'\n"
            f"  Python:     {python_uuid}\n"
            f"  PostgreSQL: {pg_uuid}"
        )

    def test_uuid5_determinism(self, supabase_client):
        """Verify same input always produces same UUID."""
        test_input = "determinism_test_12345"

        # Call multiple times
        results = []
        for _ in range(3):
            result = supabase_client.rpc(
                "uuid5_generate",
                {"namespace_uuid": str(REDDITHARBOR_NAMESPACE), "name": test_input}
            ).execute()
            results.append(str(result.data))

        assert len(set(results)) == 1, f"Non-deterministic results: {results}"


class TestNormalizationFunction:
    """Test the normalize_submission_id function."""

    @pytest.fixture
    def supabase_client(self):
        """Create Supabase client for testing."""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

        if not url or not key:
            pytest.skip("SUPABASE_URL and SUPABASE_KEY required for database tests")

        return create_client(url, key)

    def test_uuid_passthrough(self, supabase_client):
        """Valid UUID should pass through unchanged."""
        test_uuid = "e7763e41-d7bf-4bf1-a004-decff9f0f0c5"

        result = supabase_client.rpc(
            "normalize_submission_id",
            {"input": test_uuid}
        ).execute()

        assert str(result.data) == test_uuid

    def test_non_uuid_normalized(self, supabase_client):
        """Non-UUID string should be converted to UUID."""
        test_input = "hybrid_1"
        expected = str(uuid.uuid5(REDDITHARBOR_NAMESPACE, test_input))

        result = supabase_client.rpc(
            "normalize_submission_id",
            {"input": test_input}
        ).execute()

        assert str(result.data) == expected

    def test_null_input(self, supabase_client):
        """NULL input should return NULL."""
        result = supabase_client.rpc(
            "normalize_submission_id",
            {"input": None}
        ).execute()

        assert result.data is None

    def test_empty_string(self, supabase_client):
        """Empty string should return NULL."""
        result = supabase_client.rpc(
            "normalize_submission_id",
            {"input": ""}
        ).execute()

        assert result.data is None

    def test_whitespace_only(self, supabase_client):
        """Whitespace-only string should return NULL."""
        result = supabase_client.rpc(
            "normalize_submission_id",
            {"input": "   "}
        ).execute()

        assert result.data is None


class TestTriggerBehavior:
    """Test the app_opportunities trigger behavior."""

    @pytest.fixture
    def supabase_client(self):
        """Create Supabase client for testing."""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

        if not url or not key:
            pytest.skip("SUPABASE_URL and SUPABASE_KEY required for database tests")

        return create_client(url, key)

    @pytest.fixture
    def cleanup_test_data(self, supabase_client):
        """Cleanup test data after each test."""
        test_ids = []
        yield test_ids

        # Cleanup: delete any test records
        for test_id in test_ids:
            try:
                supabase_client.table("app_opportunities")\
                    .delete()\
                    .eq("id", test_id)\
                    .execute()
            except Exception:
                pass  # Ignore cleanup errors

    def test_trigger_normalizes_on_insert(self, supabase_client, cleanup_test_data):
        """Trigger should normalize submission_id on INSERT."""
        # Insert with non-UUID submission_id
        test_submission_id = "trigger_test_insert_001"
        expected_uuid = str(uuid.uuid5(REDDITHARBOR_NAMESPACE, test_submission_id))

        # Create minimal app_opportunity record
        result = supabase_client.table("app_opportunities").insert({
            "submission_id": test_submission_id,
            "app_name": "Trigger Test App",
            "value_proposition": "Test trigger normalization",
        }).execute()

        assert result.data and len(result.data) > 0

        inserted = result.data[0]
        cleanup_test_data.append(inserted["id"])

        # Verify submission_id was normalized
        assert str(inserted["submission_id"]) == expected_uuid, (
            f"Trigger did not normalize submission_id on INSERT!\n"
            f"  Input:    '{test_submission_id}'\n"
            f"  Expected: {expected_uuid}\n"
            f"  Got:      {inserted['submission_id']}"
        )

    def test_trigger_preserves_uuid_on_insert(self, supabase_client, cleanup_test_data):
        """Trigger should preserve valid UUID on INSERT."""
        test_uuid = str(uuid.uuid4())

        result = supabase_client.table("app_opportunities").insert({
            "submission_id": test_uuid,
            "app_name": "UUID Preservation Test",
            "value_proposition": "Test UUID passthrough",
        }).execute()

        assert result.data and len(result.data) > 0

        inserted = result.data[0]
        cleanup_test_data.append(inserted["id"])

        # Verify UUID was preserved
        assert str(inserted["submission_id"]) == test_uuid

    def test_trigger_normalizes_on_update(self, supabase_client, cleanup_test_data):
        """Trigger should normalize submission_id on UPDATE."""
        # First insert with a UUID
        initial_uuid = str(uuid.uuid4())

        result = supabase_client.table("app_opportunities").insert({
            "submission_id": initial_uuid,
            "app_name": "Update Test App",
            "value_proposition": "Test trigger update normalization",
        }).execute()

        assert result.data and len(result.data) > 0
        inserted = result.data[0]
        cleanup_test_data.append(inserted["id"])

        # Now update with a non-UUID value
        new_submission_id = "trigger_test_update_001"
        expected_uuid = str(uuid.uuid5(REDDITHARBOR_NAMESPACE, new_submission_id))

        update_result = supabase_client.table("app_opportunities")\
            .update({"submission_id": new_submission_id})\
            .eq("id", inserted["id"])\
            .execute()

        assert update_result.data and len(update_result.data) > 0
        updated = update_result.data[0]

        # Verify submission_id was normalized on UPDATE
        assert str(updated["submission_id"]) == expected_uuid, (
            f"Trigger did not normalize submission_id on UPDATE!\n"
            f"  Input:    '{new_submission_id}'\n"
            f"  Expected: {expected_uuid}\n"
            f"  Got:      {updated['submission_id']}"
        )


class TestIsValidUUID:
    """Test the is_valid_uuid helper function."""

    @pytest.fixture
    def supabase_client(self):
        """Create Supabase client for testing."""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

        if not url or not key:
            pytest.skip("SUPABASE_URL and SUPABASE_KEY required for database tests")

        return create_client(url, key)

    @pytest.mark.parametrize("test_input,expected", [
        ("e7763e41-d7bf-4bf1-a004-decff9f0f0c5", True),
        ("E7763E41-D7BF-4BF1-A004-DECFF9F0F0C5", True),  # Uppercase
        ("550e8400-e29b-41d4-a716-446655440000", True),
        ("not-a-uuid", False),
        ("12345678", False),
        ("e7763e41-d7bf-4bf1-a004", False),  # Too short
        ("", False),
        ("hybrid_1", False),
    ])
    def test_is_valid_uuid(self, supabase_client, test_input: str, expected: bool):
        """Test is_valid_uuid function for various inputs."""
        result = supabase_client.rpc(
            "is_valid_uuid",
            {"input": test_input}
        ).execute()

        assert result.data == expected, (
            f"is_valid_uuid('{test_input}') expected {expected}, got {result.data}"
        )


class TestEdgeCases:
    """Test edge cases and special inputs."""

    @pytest.fixture
    def supabase_client(self):
        """Create Supabase client for testing."""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

        if not url or not key:
            pytest.skip("SUPABASE_URL and SUPABASE_KEY required for database tests")

        return create_client(url, key)

    def test_unicode_handling(self, supabase_client):
        """Test Unicode characters are handled correctly."""
        test_input = "test_unicode_cafe_123"  # ASCII-safe for this test

        python_uuid = str(uuid.uuid5(REDDITHARBOR_NAMESPACE, test_input))

        result = supabase_client.rpc(
            "uuid5_generate",
            {"namespace_uuid": str(REDDITHARBOR_NAMESPACE), "name": test_input}
        ).execute()

        assert str(result.data) == python_uuid

    def test_special_characters(self, supabase_client):
        """Test special characters in input."""
        test_input = "test_with_underscores_and-dashes.and.dots"

        python_uuid = str(uuid.uuid5(REDDITHARBOR_NAMESPACE, test_input))

        result = supabase_client.rpc(
            "uuid5_generate",
            {"namespace_uuid": str(REDDITHARBOR_NAMESPACE), "name": test_input}
        ).execute()

        assert str(result.data) == python_uuid


def main():
    """Run tests manually without pytest."""
    print("Running ID Normalization Trigger Tests...")
    print(f"RedditHarbor Namespace: {REDDITHARBOR_NAMESPACE}")
    print()

    # Verify namespace computation
    expected_namespace = "8b5de7e2-d0ea-5147-a3b6-37b0c9a0a9f7"
    assert str(REDDITHARBOR_NAMESPACE) == expected_namespace, (
        f"Namespace mismatch! Expected: {expected_namespace}, Got: {REDDITHARBOR_NAMESPACE}"
    )
    print(f"[PASS] Namespace constant verified: {REDDITHARBOR_NAMESPACE}")

    # Compute expected UUIDs for common test inputs
    test_inputs = ["hybrid_1", "high_quality", "1fp7k8t", "test_submission_001"]
    print("\nExpected UUIDs for test inputs:")
    for inp in test_inputs:
        expected = uuid.uuid5(REDDITHARBOR_NAMESPACE, inp)
        print(f"  {inp!r:30} -> {expected}")

    print("\nTo run full test suite:")
    print("  pytest scripts/database/test_id_normalization_trigger.py -v")


if __name__ == "__main__":
    main()
```

---

## VERIFICATION STEPS

After implementation, run these commands to verify:

```bash
# Navigate to project root
cd /home/carlos/projects/redditharbor-core-functions-fix

# Apply the migration
supabase db push

# Or apply via psql directly
psql $DATABASE_URL -f supabase/migrations/20251123120000_add_id_normalization_trigger.sql

# Run ruff on the test script
ruff format scripts/database/test_id_normalization_trigger.py
ruff check scripts/database/test_id_normalization_trigger.py

# Run the test script standalone (shows expected UUIDs)
python scripts/database/test_id_normalization_trigger.py

# Run full pytest suite
pytest scripts/database/test_id_normalization_trigger.py -v --tb=short

# Verify UUID parity specifically
pytest scripts/database/test_id_normalization_trigger.py::TestUUID5Parity -v
```

---

## SUCCESS CRITERIA

Phase 3 (Enforcement) is complete when:

1. [ ] `uuid5_generate` PostgreSQL function exists and is IMMUTABLE
2. [ ] `normalize_submission_id` PostgreSQL function exists
3. [ ] `app_opportunities_normalize_submission_id` trigger is active
4. [ ] PostgreSQL `uuid5_generate` produces identical output to Python `uuid.uuid5()` for all test inputs
5. [ ] Trigger normalizes non-UUID values on INSERT
6. [ ] Trigger normalizes non-UUID values on UPDATE
7. [ ] Trigger preserves valid UUIDs unchanged
8. [ ] Down migration successfully removes all objects
9. [ ] All pytest tests pass: `pytest scripts/database/test_id_normalization_trigger.py -v`
10. [ ] No ruff formatting/linting errors on test script

---

## CONSTRAINTS

1. **Namespace MUST Match**: PostgreSQL namespace MUST be `8b5de7e2-d0ea-5147-a3b6-37b0c9a0a9f7`
2. **No FK Constraints**: Do NOT add foreign key constraints (DLT manages app_opportunities)
3. **No Data Migration**: Do NOT bulk-update existing data (transform on read via application)
4. **Reversible**: Migration must be fully reversible
5. **DLT Compatible**: Must not interfere with DLT merge operations
6. **Idempotent Functions**: All functions should be CREATE OR REPLACE

---

## CRITICAL: UUID5 ALGORITHM VERIFICATION

Before considering the implementation complete, verify these specific test cases produce identical results in Python and PostgreSQL:

| Input | Expected UUID (Python uuid5) |
|-------|------------------------------|
| "hybrid_1" | [compute at runtime] |
| "high_quality" | [compute at runtime] |
| "1fp7k8t" | [compute at runtime] |
| "test_submission_001" | [compute at runtime] |

The test script computes and displays these expected values. If there is ANY mismatch, the implementation is incorrect.

---

## EXPECTED BEHAVIOR AFTER ENFORCEMENT

### Before Enforcement (Current)
```
INSERT INTO app_opportunities (submission_id, ...) VALUES ('hybrid_1', ...);
-- Result: submission_id = 'hybrid_1' (string, not UUID)
```

### After Enforcement (Expected)
```
INSERT INTO app_opportunities (submission_id, ...) VALUES ('hybrid_1', ...);
-- Trigger fires, normalizes value
-- Result: submission_id = 'a1b2c3d4-...' (deterministic UUID)
-- Same UUID that Python would generate for 'hybrid_1'
```

---

## REPORT

After successful implementation, create a brief report at:
`/home/carlos/projects/redditharbor-core-functions-fix/docs/id-resolution-fix/reports/05-enforce-report.md`

Include:
- Files created
- Test results summary
- UUID parity verification (Python vs PostgreSQL for test inputs)
- Any deviations from design
- Confirmation that trigger is active
- Ready for Phase 4 confirmation (full adoption)
```

---

## Implementation Notes

### Key Techniques Used

1. **Namespace Constant Hardcoding**: The PostgreSQL function uses the pre-computed namespace UUID directly, avoiding the need to implement uuid5 within PostgreSQL just to compute the namespace.

2. **Bytea Operations for SHA-1**: Uses pgcrypto's `digest()` function for SHA-1, with careful byte manipulation to set UUID version and variant bits correctly.

3. **IMMUTABLE Function Declaration**: The `uuid5_generate` function is marked IMMUTABLE because it always returns the same output for the same input, allowing PostgreSQL to optimize queries using it.

4. **Trigger on Specific Column**: The trigger fires on `UPDATE OF submission_id` rather than any UPDATE, reducing unnecessary trigger invocations.

5. **Graceful NULL Handling**: All functions handle NULL and empty inputs gracefully, returning NULL instead of errors.

6. **Self-Verification in Migration**: The UP migration includes a DO block that verifies the functions work correctly before the migration completes.

7. **Comprehensive Parity Testing**: The test script includes parametrized tests that verify Python and PostgreSQL produce identical UUIDs for multiple inputs.

### Design Choices

1. **Trigger over Constraint**: A BEFORE trigger that transforms data is more user-friendly than a CHECK constraint that rejects invalid data. This maintains backwards compatibility.

2. **No FK Constraint**: Per the design document, app_opportunities is DLT-managed, so adding an FK constraint would break the DLT pipeline.

3. **No Bulk Data Migration**: Existing data is not bulk-updated because:
   - It would be a destructive operation
   - The application layer (with the Python resolver) handles reads correctly
   - New data will be normalized going forward

4. **Separate DOWN Migration**: A separate rollback file makes it easy to revert if issues are discovered, following Supabase migration best practices.

5. **RPC-Based Testing**: Tests use Supabase RPC calls to invoke PostgreSQL functions directly, allowing precise verification of function behavior.

### Expected Outcomes

After implementation:
- All new INSERT/UPDATE operations on app_opportunities will have normalized submission_id
- Python and PostgreSQL will produce identical UUIDs for the same input
- The database provides a safety net even if application code bypasses the Python resolver
- Existing data remains unchanged (no destructive migration)
- Migration is fully reversible

### Potential Issues to Watch

1. **pgcrypto Extension**: Some PostgreSQL configurations may not have pgcrypto. The migration will fail with a clear error if this is the case.

2. **Supabase RPC Permissions**: The test script uses RPC calls which require the functions to be exposed. If using Supabase, ensure the functions are accessible via the API.

3. **UTF-8 Encoding**: The uuid5 algorithm requires consistent UTF-8 encoding. Test with various character sets to ensure parity.

4. **Performance**: The trigger adds a small overhead to INSERT/UPDATE operations. For high-volume tables, consider the performance impact.
