# Clean Break Implementation

This documentation folder describes RedditHarbor's "Clean Break" refactoring approach to solve persistent ID format issues in the data pipeline.

## Purpose

The Clean Break Implementation addresses a fundamental architectural issue: **ID format mismatches** between how data is stored versus how it is queried. Rather than adding more patches to existing workarounds, this approach establishes a single source of truth for ID normalization.

## The Problem (Summary)

```
+------------------+     +------------------+     +------------------+
|   Reddit API     | --> |   DLT Pipeline   | --> |   PostgreSQL     |
|   id: "abc123"   |     |   ???            |     |   id: ???        |
+------------------+     +------------------+     +------------------+
                                  |
                                  v
                         Multiple code paths
                         No single source of truth
                         Result: ID format chaos
```

Data enters the system with Reddit IDs (`abc123`), but is sometimes stored as:
- Raw Reddit ID: `abc123`
- UUID format: `550e8400-e29b-41d4-a716-446655440000`
- Mixed formats in the same column

Queries then fail to find records because they use the wrong format.

## The Solution (Summary)

```
+------------------+     +------------------+     +------------------+
|   Reddit API     | --> |   ID Resolver    | --> |   DLT Pipeline   |
|   id: "abc123"   |     |   (normalize)    |     |   (UUID only)    |
+------------------+     +------------------+     +------------------+
                                  |
                                  v
                         Single code path
                         UUID v5 (deterministic)
                         Consistent storage & queries
```

**Normalize all IDs to UUIDs BEFORE they enter DLT.**

## Document Index

| Document | Description |
|----------|-------------|
| [00-problem-statement.md](./00-problem-statement.md) | Detailed analysis of the ID format problem and why previous fixes failed |
| [01-architecture-decision.md](./01-architecture-decision.md) | ADR for the clean break approach (future) |
| [02-implementation-guide.md](./02-implementation-guide.md) | Step-by-step implementation instructions |
| [03-migration-guide.md](./03-migration-guide.md) | Migrating existing data to new format (future) |
| [04-testing-strategy.md](./04-testing-strategy.md) | Test coverage requirements (future) |

## Quick Start for Developers

### Understanding the ID Resolver

The canonical ID resolver lives at `core/utils/id_resolver.py`. It provides:

```python
from core.utils.id_resolver import resolve_submission_id, REDDITHARBOR_NAMESPACE

# Any input format -> Consistent UUID output
result = resolve_submission_id("abc123")
print(result.uuid)  # "550e8400-e29b-41d4-a716-446655440000"

result = resolve_submission_id("https://reddit.com/r/python/comments/abc123")
print(result.uuid)  # Same UUID as above (deterministic)
```

### Key Principles

1. **Single Entry Point**: All IDs go through `resolve_submission_id()` before storage
2. **Deterministic UUIDs**: Same input always produces same UUID (UUID v5)
3. **Format Agnostic**: Accepts Reddit IDs, URLs, or existing UUIDs
4. **Fail-Safe**: Returns `ResolutionResult` with error details, never raises

### Critical Files

| File | Purpose |
|------|---------|
| `core/utils/id_resolver.py` | Canonical ID resolver implementation |
| `core/dlt/collection.py` | DLT transform functions that use the resolver |
| `config/dlt.toml` | DLT configuration (`max_nesting_levels = 1`) |
| `core/dlt/constants.py` | Primary key constants for DLT resources |

### Before Making Changes

1. Read [00-problem-statement.md](./00-problem-statement.md) to understand the history
2. Review [02-implementation-guide.md](./02-implementation-guide.md) for the implementation pattern
3. Run existing tests: `pytest tests/test_id_resolver.py -v`

## Related Documentation

- [ID Resolution Fix Reports](../id-resolution-fix/reports/) - Historical context and QA validation
- [REMEDIATION_WORKFLOW_SUMMARY.md](../../REMEDIATION_WORKFLOW_SUMMARY.md) - Overall project remediation status

## Status

| Phase | Status | Description |
|-------|--------|-------------|
| Problem Analysis | Complete | Root cause identified |
| ID Resolver | Complete | `core/utils/id_resolver.py` implemented |
| DLT Integration | In Progress | Transform functions being updated |
| Data Migration | Pending | Existing data normalization |
| Validation | Pending | E2E testing and verification |
