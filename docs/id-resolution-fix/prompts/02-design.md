# ID Resolution Design Prompt

**Phase**: 02-Design (No Implementation)
**Output**: `/home/carlos/projects/redditharbor-core-functions-fix/docs/id-resolution-fix/reports/02-design-report.md`
**Predecessor**: `01-audit-report.md` (completed)

---

## The Prompt

```
You are a senior software architect designing a solution for a critical ID resolution problem in the RedditHarbor data pipeline. Your task is to produce a DESIGN DOCUMENT ONLY - no code implementation.

## Problem Statement

The RedditHarbor pipeline has inconsistent ID handling that causes database verification failures:

1. **Pipeline stores data successfully** using transformed UUIDs
2. **Verifier queries fail** because it queries the wrong field with the original ID format
3. **Mixed ID formats** exist in the same database columns

### Root Cause Analysis (from Audit)

The transformation chain is broken:

```
Pipeline Input ("hybrid_1", "1fp7k8t", or UUID)
    |
    v
EnhancedHybridStore._fix_submission_id_formats()
    |
    v  (converts to UUID via uuid5)
app_opportunities.submission_id (stores UUID)
    |
BUT:
    |
DatabaseVerifier.verify_submission_storage("hybrid_1")
    |
    v
submissions WHERE submission_id = "hybrid_1"
    |
    v
FAILS (submissions.submission_id contains UUIDs, not "hybrid_1")
```

### Database Schema Reality

| Table | Field | Contains | Notes |
|-------|-------|----------|-------|
| submissions | id | UUID | Primary key, auto-generated |
| submissions | submission_id | UUID | Copy of id field |
| submissions | reddit_id | VARCHAR | "hybrid_1", "1fp7k8t", etc. |
| app_opportunities | submission_id | Mixed | UUID OR raw string (no FK) |
| opportunities | submission_id | UUID | FK to submissions.id |

### Foreign Key Constraints

- `opportunities.submission_id` -> `submissions.id` (UUID, enforced)
- `app_opportunities.submission_id` -> NO FK (DLT-managed, not enforced)

### Current ID Resolution Code (Reference Only)

Location: `core/storage/enhanced_hybrid_store.py:473-535`

The existing `_resolve_submission_uuid()` method handles:
- Valid UUIDs (verify in submissions.id)
- Reddit URLs (extract ID via regex)
- Reddit IDs (lookup via submissions.reddit_id)

BUT: This resolver is NOT used by database_verifier.py or other consumers.

---

## Design Requirements

### Requirement 1: Single Source of Truth

Design ONE canonical ID resolver that:
- Lives in a single location (suggest: `core/utils/id_resolver.py`)
- Is imported and used by ALL code that needs ID resolution
- Has a clear, simple interface

### Requirement 2: Universal Input Handling

The resolver must accept ANY of these input formats:
- UUID string: `"e7763e41-d7bf-4bf1-a004-decff9f0f0c5"`
- Reddit ID: `"1fp7k8t"`, `"abc123"`
- Synthetic ID: `"hybrid_1"`, `"high_quality"`, `"test_int_unique_12345678_1"`
- Reddit URL: `"https://reddit.com/r/datascience/comments/1fp7k8t/title"`
- Raw submission dict: `{"submission_id": "...", "reddit_id": "..."}`

### Requirement 3: Deterministic Output

The resolver must return:
- `submissions.id` UUID when the submission exists in the database
- A deterministically-generated UUID (via uuid5) when the submission does NOT exist
- `None` only when input is invalid/empty

### Requirement 4: Backwards Compatibility

The design must:
- NOT require database migrations
- NOT break existing data in any table
- Work with both old (mixed format) and new (UUID-only) data
- Allow gradual adoption across codebase

### Requirement 5: Testability

Each component must be independently testable:
- ID format detection (pure function, no DB)
- UUID generation (pure function, no DB)
- Database lookup (requires DB, mockable)
- Full resolution chain (integration test)

---

## Required Design Deliverables

### Deliverable 1: Architecture Diagram

Create an ASCII diagram showing:
- Where the resolver fits in the existing architecture
- Which components call the resolver
- Data flow for ID resolution
- Integration with existing `_resolve_submission_uuid()` code

Example format:
```
+------------------+     +------------------+     +------------------+
| Component A      | --> | ID Resolver      | --> | Database         |
+------------------+     +------------------+     +------------------+
```

### Deliverable 2: Interface Definition

Define the public interface:

```
Function: resolve_submission_id(input, options) -> Result

Input Types:
- str (any ID format)
- dict (submission with id fields)
- None

Options:
- require_db_existence: bool (default: False)
- fallback_to_generated: bool (default: True)

Result:
- uuid: str | None
- source: Literal["database", "generated", "passthrough"]
- original_input: str
- error: str | None
```

Specify:
- All parameter types and defaults
- Return type structure
- Error conditions and messages
- Thread safety considerations

### Deliverable 3: Resolution Logic Flowchart

Create a decision tree diagram showing the resolution algorithm:

```
Input received
    |
    v
Is input None or empty? --YES--> Return None
    |
    NO
    v
Is input a dict? --YES--> Extract submission_id or reddit_id
    |
    NO
    v
Is input a valid UUID? --YES--> [UUID Path]
    |                               |
    NO                              v
    v                          Verify in submissions.id?
[Non-UUID Path]                     |
    |                          YES: Return UUID (source: database)
    v                          NO: Return UUID (source: passthrough)
Contains "reddit.com"? --YES--> Extract ID from URL
    |
    NO
    v
[Lookup Path]
    |
    v
Query submissions WHERE reddit_id = input
    |
    v
Found? --YES--> Return submissions.id (source: database)
    |
    NO
    v
Generate UUID via uuid5(namespace, input)
    |
    v
Return generated UUID (source: generated)
```

### Deliverable 4: Integration Points Matrix

Create a table listing EVERY location that needs to use the resolver:

| File | Function/Method | Current Behavior | Required Change | Priority |
|------|-----------------|------------------|-----------------|----------|
| database_verifier.py:182 | verify_submission_storage | Queries submission_id directly | Use resolver first | CRITICAL |
| enhanced_hybrid_store.py:578 | _get_or_create_opportunity_id | Uses _resolve_submission_uuid | Migrate to shared resolver | HIGH |
| ... | ... | ... | ... | ... |

Include at minimum:
- All files from audit report with CRITICAL/HIGH risk
- Any additional files that query by submission_id
- Estimated effort (lines changed) for each

### Deliverable 5: Migration Strategy

Design a phased rollout plan:

**Phase 1: Foundation**
- Create the resolver module
- Add comprehensive unit tests
- Verify with existing test data

**Phase 2: Critical Fixes**
- Integrate into database_verifier.py
- Verify pipeline tests pass

**Phase 3: Consolidation**
- Migrate enhanced_hybrid_store.py to use shared resolver
- Remove duplicate resolution logic

**Phase 4: Full Adoption**
- Update all remaining consumers
- Add deprecation warnings to old methods
- Document the canonical approach

For each phase, specify:
- Success criteria
- Rollback plan
- Dependencies on previous phases

### Deliverable 6: Test Case Specifications

Define test cases for validation:

**Unit Tests (No Database)**

| Test ID | Input | Expected Output | Tests |
|---------|-------|-----------------|-------|
| UT-001 | `None` | `None` | Null handling |
| UT-002 | `""` | `None` | Empty string |
| UT-003 | `"e7763e41-d7bf-4bf1-a004-decff9f0f0c5"` | Same UUID, source="passthrough" | Valid UUID passthrough |
| UT-004 | `"hybrid_1"` | Deterministic UUID, source="generated" | Synthetic ID conversion |
| UT-005 | `"https://reddit.com/r/test/comments/abc123/"` | Extracted ID processed | URL extraction |
| UT-006 | `{"submission_id": "xyz", "reddit_id": "abc"}` | Process submission_id first | Dict handling |

**Integration Tests (With Database)**

| Test ID | Setup | Input | Expected | Tests |
|---------|-------|-------|----------|-------|
| IT-001 | Insert submission with reddit_id="test1" | "test1" | submissions.id UUID, source="database" | Database lookup |
| IT-002 | No matching submission | "nonexistent" | Generated UUID, source="generated" | Graceful fallback |
| IT-003 | Insert then resolve twice | "test2" | Same UUID both times | Idempotency |

**End-to-End Tests**

| Test ID | Scenario | Expected Outcome |
|---------|----------|------------------|
| E2E-001 | Pipeline stores "hybrid_1", verifier queries "hybrid_1" | Verification succeeds |
| E2E-002 | Pipeline stores real Reddit ID, verifier queries same | Verification succeeds |
| E2E-003 | Mixed batch with UUIDs and synthetic IDs | All verifications succeed |

---

## Constraints

1. **NO CODE** - This is a design document only
2. **NO DATABASE MIGRATIONS** - Work with existing schema
3. **BACKWARDS COMPATIBLE** - Don't break existing data
4. **DLT COMPATIBLE** - Must work with DLT pipeline's merge operations
5. **DETERMINISTIC** - Same input must always produce same output

---

## Reference: Audit Findings Summary

From `01-audit-report.md`:

### Critical Issues (3)
1. database_verifier.py:182 - Wrong query field for non-UUID values
2. enhanced_hybrid_store.py:613 - FK constraint using potentially wrong format
3. test_02_small_batch.py:213 - Test uses string ID expecting UUID

### High Risk Issues (8)
- hybrid_store.py:215-218 - reddit_id/submission_id confusion
- profile_store.py:92-93 - Field mapping inconsistency
- collection.py:295-296 - Comment linking with wrong ID format
- enhanced_hybrid_store.py:494-502 - Complex UUID resolution with fallbacks
- (4 more in audit report)

### Key Code Locations

1. **Existing resolver** (to consolidate):
   - `core/storage/enhanced_hybrid_store.py:_resolve_submission_uuid` (lines 473-535)

2. **Primary consumer to fix**:
   - `scripts/testing/integration/utils/database_verifier.py:verify_submission_storage` (line 182)

3. **ID transformation entry point**:
   - `core/storage/enhanced_hybrid_store.py:_fix_submission_id_formats` (lines 213-269)

---

## Output Format

Produce a markdown document with the following structure:

```markdown
# ID Resolution Design Document

## 1. Executive Summary
[2-3 paragraph overview of the design]

## 2. Architecture Diagram
[ASCII diagram with explanation]

## 3. Interface Definition
[Complete interface specification]

## 4. Resolution Logic Flowchart
[Decision tree diagram]

## 5. Integration Points
[Complete matrix of all integration points]

## 6. Migration Strategy
[Phased rollout plan with success criteria]

## 7. Test Specifications
[All test cases organized by type]

## 8. Risk Assessment
[Risks and mitigations for the design]

## 9. Open Questions
[Any decisions that need stakeholder input]

## 10. Appendix: Data Examples
[Concrete examples of ID resolution for common scenarios]
```

Save the output to:
`/home/carlos/projects/redditharbor-core-functions-fix/docs/id-resolution-fix/reports/02-design-report.md`
```

---

## Implementation Notes

### Key Techniques Used

1. **Structured Problem Decomposition**: The prompt breaks down the ID resolution problem into discrete, addressable components (detection, generation, lookup, integration).

2. **Concrete Examples**: Every requirement includes specific examples from the actual codebase with file paths and line numbers.

3. **Explicit Deliverables**: Each output artifact has a defined format and specific content requirements.

4. **Constraint Emphasis**: Critical constraints (no code, no migrations, backwards compatible) are repeated to ensure the agent stays in design mode.

5. **Reference Material Integration**: The prompt incorporates audit findings directly, eliminating the need for the agent to re-discover issues.

### Why These Choices

- **Single resolver design**: Prevents future fragmentation by establishing one canonical approach
- **Phased migration**: Allows incremental validation and rollback at each stage
- **Comprehensive test specs**: Ensures the design is testable before any implementation begins
- **Integration matrix**: Forces enumeration of all affected code, preventing missed integration points

### Expected Outcomes

1. A complete design document that can be handed to any developer for implementation
2. Clear success criteria for each migration phase
3. Test cases that can be implemented before the resolver itself
4. Risk assessment that identifies potential issues early

### Potential Issues to Watch

- The agent may want to include code snippets - redirect to pseudocode or interface definitions only
- The migration strategy must account for the DLT pipeline's merge behavior
- Test specifications should include edge cases like concurrent access and cache invalidation
