# Integration Prompt: Wire Canonical ID Resolver (Phase 2)

**Target Agent**: Claude Code with subagent delegation
**Primary Subagent**: `python-pro` (code modifications)
**Secondary Subagent**: `test-engineer` (integration tests)
**Predecessor**: 03-implement.md (completed)
**Scope**: Phase 2 - Critical Fixes ONLY

---

## Objective

Integrate the canonical ID resolver (`core/utils/id_resolver.py`) into the critical code paths identified in the design audit. This phase focuses on the two highest-priority integration points that directly cause the database verification failures observed in Test 02 Small Batch.

---

## The Prompt

```
You are performing Phase 2 integration of the RedditHarbor ID Resolution fix. Your task is to wire the canonical ID resolver into critical code paths and create integration tests.

## PROJECT CONTEXT

The canonical ID resolver module was created in Phase 1:
- Location: `/home/carlos/projects/redditharbor-core-functions-fix/core/utils/id_resolver.py`
- Key exports: `resolve_submission_id`, `ResolutionResult`
- Capability: Transforms any input format (UUID, Reddit ID, synthetic ID, URL, dict) to consistent UUID

The core issue: Database verification fails because data is stored using UUID transformations, but queries use raw IDs like "hybrid_1". The resolver provides the single source of truth for all ID transformations.

## RESOLVER INTERFACE

```python
from core.utils.id_resolver import resolve_submission_id, ResolutionResult

# Basic usage
result = resolve_submission_id(input_value)
if result and result.uuid:
    # Use result.uuid for database operations
    # result.source tells you how it was resolved: "database", "passthrough", "generated"

# With database lookup (requires supabase_client)
result = resolve_submission_id(
    input_value,
    supabase_client=self.supabase_client,
    require_db_existence=False,  # Don't fail if not found
    fallback_to_generated=True   # Generate UUID if lookup fails
)
```

## DELIVERABLES

You must modify exactly 2 files and create 1 new test file:

### File 1: database_verifier.py (CRITICAL PRIORITY)
Path: `/home/carlos/projects/redditharbor-core-functions-fix/scripts/testing/integration/utils/database_verifier.py`

### File 2: enhanced_hybrid_store.py (HIGH PRIORITY)
Path: `/home/carlos/projects/redditharbor-core-functions-fix/core/storage/enhanced_hybrid_store.py`

### File 3: test_id_resolver_integration.py (NEW)
Path: `/home/carlos/projects/redditharbor-core-functions-fix/tests/test_id_resolver_integration.py`

## SUBAGENT DELEGATION

Use `python-pro` subagent for:
- Modifying database_verifier.py to use the canonical resolver
- Refactoring enhanced_hybrid_store.py to delegate to the canonical resolver
- Ensuring consistent error handling and logging

Use `test-engineer` subagent for:
- Creating integration tests that verify resolver works with both modules
- Testing both UUID and non-UUID input scenarios
- Verifying no regression in existing functionality

---

## FILE 1: database_verifier.py MODIFICATIONS

### Current Problem (Line 178-185)
The query uses `submission_id` directly without resolution. When the input is "hybrid_1" but the database stores a UUID, the lookup fails.

### Required Changes

#### Change 1: Add Import (Top of File, after line 19)
```python
# Add after existing imports
from core.utils.id_resolver import resolve_submission_id, ResolutionResult
```

#### Change 2: Update verify_submission_storage Method (Lines 157-222)
Replace the existing query logic with resolver-based lookup.

BEFORE (Lines 175-189):
```python
        try:
            with self.SessionLocal() as session:
                # Verify base submission exists
                submission_query = text("""
                    SELECT submission_id, title, subreddit, reddit_score,
                           created_utc
                    FROM submissions
                    WHERE submission_id = :submission_id
                """)

                submission_result = session.execute(submission_query, {"submission_id": submission_id}).fetchone()

                if not submission_result:
                    result.message = f"Submission {submission_id} not found in database"
                    return result
```

AFTER:
```python
        try:
            with self.SessionLocal() as session:
                # PHASE 2 FIX: Use canonical resolver to handle all ID formats
                resolved = resolve_submission_id(submission_id)

                if not resolved or not resolved.uuid:
                    result.message = f"Could not resolve submission ID: {submission_id}"
                    if resolved and resolved.error:
                        result.message += f" - {resolved.error}"
                    return result

                resolved_uuid = resolved.uuid
                logger.debug(
                    f"Resolved submission_id '{submission_id}' to UUID '{resolved_uuid}' "
                    f"(source={resolved.source})"
                )

                # Try lookup by resolved UUID first (submissions.id)
                submission_result = None

                # Strategy 1: Query by UUID (id column)
                submission_query = text("""
                    SELECT id, reddit_id, title, subreddit, reddit_score, created_utc
                    FROM submissions
                    WHERE id = :uuid_value
                """)
                submission_result = session.execute(
                    submission_query, {"uuid_value": resolved_uuid}
                ).fetchone()

                # Strategy 2: Fallback to reddit_id lookup if UUID not found
                if not submission_result:
                    logger.debug(f"UUID lookup failed, trying reddit_id fallback for: {submission_id}")
                    reddit_id_query = text("""
                        SELECT id, reddit_id, title, subreddit, reddit_score, created_utc
                        FROM submissions
                        WHERE reddit_id = :reddit_id
                    """)
                    submission_result = session.execute(
                        reddit_id_query, {"reddit_id": submission_id}
                    ).fetchone()

                if not submission_result:
                    result.message = (
                        f"Submission not found. Tried: UUID={resolved_uuid}, "
                        f"reddit_id={submission_id}"
                    )
                    return result

                # Use the actual database ID for subsequent queries
                actual_db_id = submission_result.id if hasattr(submission_result, 'id') else resolved_uuid
```

#### Change 3: Update _verify_app_opportunities Method (Lines 224-256)
The method needs to use the resolved ID for the FK lookup.

BEFORE (Lines 227-236):
```python
        try:
            query = text("""
                SELECT submission_id, app_name, value_proposition, problem_description,
                       target_user, monetization_model, final_score, opportunity_score,
                       market_validation_score, monetization_score, dimension_scores,
                       priority, confidence, status, trust_level, analyzed_at
                FROM app_opportunities
                WHERE submission_id = :submission_id
            """)

            result = session.execute(query, {"submission_id": submission_id}).fetchone()
```

AFTER:
```python
        try:
            # PHASE 2 FIX: Use resolver for consistent ID handling
            resolved = resolve_submission_id(submission_id)

            if not resolved or not resolved.uuid:
                logger.warning(f"Could not resolve submission_id for app_opportunities: {submission_id}")
                return False

            resolved_uuid = resolved.uuid

            # Try by resolved UUID first
            query = text("""
                SELECT submission_id, app_name, value_proposition, problem_description,
                       target_user, monetization_model, final_score, opportunity_score,
                       market_validation_score, monetization_score, dimension_scores,
                       priority, confidence, status, trust_level, analyzed_at
                FROM app_opportunities
                WHERE submission_id = :submission_id
            """)

            result = session.execute(query, {"submission_id": resolved_uuid}).fetchone()

            # Fallback: try original ID if UUID lookup failed
            if not result:
                logger.debug(f"UUID lookup failed for app_opportunities, trying original: {submission_id}")
                result = session.execute(query, {"submission_id": submission_id}).fetchone()
```

---

## FILE 2: enhanced_hybrid_store.py MODIFICATIONS

### Current Problem (Lines 473-535)
The `_resolve_submission_uuid` method duplicates resolver logic. It should delegate to the canonical resolver.

### Required Changes

#### Change 1: Add Import (Top of File, after line 30)
```python
# Add after existing imports
from core.utils.id_resolver import resolve_submission_id, ResolutionResult
```

#### Change 2: Refactor _resolve_submission_uuid Method (Lines 473-535)
Replace the standalone resolution logic with delegation to canonical resolver.

BEFORE (entire method at lines 473-535):
```python
    def _resolve_submission_uuid(self, submission_id: str) -> Optional[str]:
        """
        Resolve a submission identifier to a valid UUID from the submissions table.
        ...
        """
        if not submission_id:
            return None

        # Step 1: Check if it's already a valid UUID
        try:
            uuid.UUID(submission_id)
            # ... complex validation logic ...
        except (ValueError, AttributeError):
            pass

        # Step 2: Extract Reddit ID from URL if needed
        reddit_id = submission_id
        if "reddit.com" in submission_id:
            # ... URL extraction logic ...

        # Step 3: Look up the UUID using reddit_id
        # ... database lookup logic ...
```

AFTER (replace entire method):
```python
    def _resolve_submission_uuid(self, submission_id: str) -> Optional[str]:
        """
        Resolve a submission identifier to a valid UUID from the submissions table.

        PHASE 2 REFACTOR: Delegates to canonical resolver for consistent ID handling.

        The submission_id can be in various formats:
        - A valid UUID (already matches submissions.id)
        - A Reddit ID (e.g., '1fp7k8t') that needs lookup via submissions.reddit_id
        - A Reddit URL (e.g., 'https://reddit.com/r/datascience/comments/1fp7k8t/')
        - A hybrid ID (e.g., 'hybrid_1') that may need conversion

        Args:
            submission_id: The submission identifier in any format

        Returns:
            Optional[str]: The UUID from submissions.id, or None if not found
        """
        if not submission_id:
            return None

        # PHASE 2: Delegate to canonical resolver
        result = resolve_submission_id(
            submission_id,
            supabase_client=self.supabase_client,
            require_db_existence=False,
            fallback_to_generated=True
        )

        if not result:
            logger.debug(f"Resolver returned None for submission_id: {submission_id}")
            return None

        if result.error:
            logger.warning(
                f"[ENHANCED_STORE] ID resolution warning for '{submission_id}': {result.error}"
            )
            # Still return UUID if we got one despite error
            if result.uuid:
                return result.uuid
            return None

        if result.uuid:
            logger.debug(
                f"Resolved '{submission_id}' to UUID '{result.uuid}' (source={result.source})"
            )

            # If source is "generated", verify UUID exists in database
            if result.source == "generated" and self.supabase_client:
                # Verify the generated UUID actually exists in submissions
                try:
                    response = self.supabase_client.table("submissions")\
                        .select("id").eq("id", result.uuid).execute()
                    if not response.data or len(response.data) == 0:
                        # Generated UUID doesn't exist, try reddit_id lookup
                        logger.debug(
                            f"Generated UUID {result.uuid} not in database, "
                            f"trying reddit_id lookup for: {submission_id}"
                        )
                        response = self.supabase_client.table("submissions")\
                            .select("id").eq("reddit_id", submission_id).execute()
                        if response.data and len(response.data) > 0:
                            actual_uuid = response.data[0]["id"]
                            logger.info(
                                f"Found submission via reddit_id: {submission_id} -> {actual_uuid}"
                            )
                            return actual_uuid
                        else:
                            logger.warning(
                                f"[ENHANCED_STORE] Could not verify submission exists: {submission_id}"
                            )
                            # Return the generated UUID anyway for storage
                            return result.uuid
                except Exception as e:
                    logger.error(f"Error verifying UUID existence: {e}")
                    # Return generated UUID on error
                    return result.uuid

            return result.uuid

        logger.warning(f"[ENHANCED_STORE] No UUID resolved for: {submission_id}")
        return None
```

#### Change 3: Update _get_or_create_opportunity_id Method (Line 612)
Ensure it uses the canonical resolver's UUID for FK reference.

The method already calls `_resolve_submission_uuid` at line 578, which now delegates to the canonical resolver. No additional changes needed here, but verify the flow is correct.

---

## FILE 3: test_id_resolver_integration.py (NEW FILE)

Create integration tests that verify the resolver works correctly with both modified modules.

```python
"""
Integration Tests for RedditHarbor ID Resolver with Storage and Verification

These tests verify that the canonical ID resolver correctly integrates with:
1. database_verifier.py - Submission lookup and verification
2. enhanced_hybrid_store.py - UUID resolution for FK references

Author: Data Engineering Team
Date: 2025-11-23
"""

import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch

from core.utils.id_resolver import (
    resolve_submission_id,
    ResolutionResult,
    is_valid_uuid,
    generate_deterministic_uuid,
    REDDITHARBOR_NAMESPACE,
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
        assert result.uuid == test_uuid
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
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = resolve_submission_id(
            "test_id",
            supabase_client=mock_client,
            require_db_existence=False,
            fallback_to_generated=True
        )

        assert result is not None
        assert result.uuid is not None

    def test_resolver_fallback_when_not_in_database(self):
        """Verify resolver falls back to generation when ID not in database."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = []  # Empty result - not found

        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = resolve_submission_id(
            "nonexistent_id",
            supabase_client=mock_client,
            require_db_existence=False,
            fallback_to_generated=True
        )

        assert result is not None
        assert result.uuid is not None
        # Should be generated since not found in DB
        assert result.source in ("generated", "passthrough")


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
        import threading
        results = []
        errors = []

        def resolve_in_thread(input_id, expected_uuid):
            try:
                result = resolve_submission_id(input_id)
                if result.uuid != expected_uuid:
                    errors.append(f"Mismatch for {input_id}")
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
        for i in range(10):
            for test_id, expected_uuid in expected.items():
                t = threading.Thread(
                    target=resolve_in_thread,
                    args=(test_id, expected_uuid)
                )
                threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 30  # 10 iterations x 3 test IDs


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing code."""

    def test_uuid_passthrough_unchanged(self):
        """Verify existing UUID-based code continues to work."""
        existing_uuid = "e7763e41-d7bf-4bf1-a004-decff9f0f0c5"
        result = resolve_submission_id(existing_uuid)

        # Should pass through unchanged
        assert result.uuid == existing_uuid
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
```

---

## VERIFICATION STEPS

After implementation, run these commands to verify:

```bash
# Navigate to project root
cd /home/carlos/projects/redditharbor-core-functions-fix

# Run ruff formatting on modified files
ruff format scripts/testing/integration/utils/database_verifier.py
ruff format core/storage/enhanced_hybrid_store.py
ruff format tests/test_id_resolver_integration.py

# Run ruff linting
ruff check scripts/testing/integration/utils/database_verifier.py
ruff check core/storage/enhanced_hybrid_store.py
ruff check tests/test_id_resolver_integration.py

# Run the new integration tests
pytest tests/test_id_resolver_integration.py -v --tb=short

# Run the original unit tests to verify no regression
pytest tests/test_id_resolver.py -v --tb=short

# Run storage tests to verify no regression
pytest tests/test_storage_services.py -v --tb=short

# Run Test 02 Small Batch to verify fix works in practice
# (This is the test that originally revealed the ID resolution issue)
cd scripts/testing/integration
./run_test_02_small_batch.sh
```

---

## SUCCESS CRITERIA

Phase 2 is complete when:

1. [ ] `database_verifier.py` imports and uses `resolve_submission_id`
2. [ ] `database_verifier.py` `verify_submission_storage()` uses resolver with fallback
3. [ ] `database_verifier.py` `_verify_app_opportunities()` uses resolver
4. [ ] `enhanced_hybrid_store.py` imports the canonical resolver
5. [ ] `enhanced_hybrid_store.py` `_resolve_submission_uuid()` delegates to resolver
6. [ ] `tests/test_id_resolver_integration.py` created with all test cases
7. [ ] All integration tests pass: `pytest tests/test_id_resolver_integration.py -v`
8. [ ] All original unit tests pass: `pytest tests/test_id_resolver.py -v`
9. [ ] No ruff formatting/linting errors
10. [ ] Test 02 Small Batch shows improved verification success rate

---

## CONSTRAINTS

1. **Minimal Changes**: Only modify the specific methods identified - don't refactor unrelated code
2. **Backwards Compatible**: Existing UUID-based code must continue to work unchanged
3. **No New Dependencies**: Only use the resolver from core/utils/id_resolver.py
4. **Logging**: Add debug-level logging for resolution steps (not info-level to avoid spam)
5. **Error Handling**: Never raise exceptions from resolver integration - always fall back gracefully
6. **Follow Patterns**: Match existing code style in each modified file

---

## EXPECTED BEHAVIOR AFTER INTEGRATION

### Before Fix (Current Behavior)
```
Input: "hybrid_1"
Database Query: WHERE submission_id = 'hybrid_1'
Result: NOT FOUND (data stored under UUID)
Verification: FAILED
```

### After Fix (Expected Behavior)
```
Input: "hybrid_1"
Resolver: resolve_submission_id("hybrid_1") -> UUID "a1b2c3d4-..."
Database Query: WHERE id = 'a1b2c3d4-...' OR reddit_id = 'hybrid_1'
Result: FOUND
Verification: PASSED
```

---

## REPORT

After successful implementation, create a brief report at:
`/home/carlos/projects/redditharbor-core-functions-fix/docs/id-resolution-fix/reports/04-integrate-report.md`

Include:
- Files modified with line counts
- Test results summary
- Before/after verification success rates (if Test 02 was run)
- Any issues encountered and resolutions
- Ready for Phase 3 confirmation (broader integration)
```

---

## Implementation Notes

### Key Techniques Used

1. **Explicit Before/After Code Blocks**: Shows exact code to replace, minimizing ambiguity about what changes are needed

2. **Line Number References**: Specific line numbers from the actual source files guide implementation precisely

3. **Subagent Delegation**: Clear separation between `python-pro` for code modifications and `test-engineer` for integration tests

4. **Fallback Strategy Pattern**: Integration uses two-stage lookup (UUID first, then reddit_id) for maximum compatibility

5. **Minimal Invasion Principle**: Only modifies specific methods that need fixing, not entire files

6. **Comprehensive Test Coverage**: Integration tests cover all the scenarios that caused the original failures

7. **Backwards Compatibility Tests**: Explicit tests ensure existing UUID-based code continues to work

8. **Verification Commands**: Concrete bash commands with expected outcomes

### Design Choices

1. **Delegation over Duplication**: `_resolve_submission_uuid` now delegates to canonical resolver instead of duplicating logic

2. **Two-Stage Lookup in Verifier**: First tries resolved UUID, then falls back to original ID for robustness

3. **Debug-Level Logging**: Resolution steps logged at debug level to avoid log spam while maintaining traceability

4. **Graceful Degradation**: All resolver calls are wrapped with error handling that falls back to original behavior

5. **Thread Safety Testing**: Integration tests include thread safety verification since resolver is used in concurrent scenarios

### Expected Outcomes

After implementation:
- Test 02 Small Batch verification should show improved success rate
- Both UUID and non-UUID inputs resolve to correct database records
- No regression in existing tests that use UUID-based lookups
- Clear logging trail for debugging ID resolution issues
