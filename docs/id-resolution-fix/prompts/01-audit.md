# Submission ID Usage Audit Prompt

## Agent Mission

You are a code auditor tasked with analyzing the RedditHarbor codebase to document all locations where submission identifiers are read, written, or transformed. The codebase has an ID chaos problem with multiple identifier fields that are sometimes confused.

## Context: The ID Chaos Problem

The database schema has multiple ID fields for submissions:

| Field | Table | Type | Description |
|-------|-------|------|-------------|
| `id` | `submissions` | UUID | Auto-generated primary key |
| `submission_id` | `submissions` | VARCHAR | Sometimes UUID, sometimes raw string |
| `reddit_id` | `submissions` | VARCHAR | The actual Reddit identifier (e.g., "1fp7k8t") |
| `submission_id` | `app_opportunities` | VARCHAR | Raw strings like "hybrid_1" or UUIDs |

The problem: Code in different locations expects different formats, leading to FK violations, lookup failures, and data inconsistencies.

## Your Task

Perform a comprehensive audit of the codebase to:

1. **Identify all locations** that read or write submission-related IDs
2. **Document the expected format** at each location (UUID vs raw string vs Reddit ID)
3. **Map transformations** between formats
4. **Identify mismatches** where producers and consumers disagree on format

## Files to Examine

### Priority 1 - Core Storage Layer (Must Audit)

```
core/storage/enhanced_hybrid_store.py
core/storage/hybrid_store.py
core/storage/dlt_loader.py
core/storage/profile_store.py
```

### Priority 2 - DLT Infrastructure

```
core/dlt/__init__.py
core/dlt/constants.py
core/dlt/app_opportunities.py
core/dlt/collection.py
core/dlt/reddit_source.py
```

### Priority 3 - Pipeline Components

```
core/pipeline/__init__.py
core/pipeline/config.py
core/pipeline/factory.py
core/collection.py
```

### Priority 4 - Enrichment Services

```
core/enrichment/base_service.py
core/enrichment/profiler_service.py
core/enrichment/opportunity_service.py
core/enrichment/trust_service.py
core/enrichment/market_validation_service.py
core/enrichment/monetization_service.py
```

### Priority 5 - Testing and Verification

```
scripts/testing/integration/utils/database_verifier.py
tests/test_storage_integration.py
tests/test_dlt_loader.py
```

## Search Patterns to Execute

Run these grep/search commands to find all relevant code locations:

### Pattern 1: Direct submission_id references
```bash
grep -rn "submission_id" core/ --include="*.py" | grep -v "__pycache__"
grep -rn "submission_id" scripts/testing/ --include="*.py" | grep -v "__pycache__"
```

### Pattern 2: Reddit ID references
```bash
grep -rn "reddit_id" core/ --include="*.py" | grep -v "__pycache__"
grep -rn "reddit_id" scripts/ --include="*.py" | grep -v "__pycache__"
```

### Pattern 3: UUID transformations
```bash
grep -rn "uuid.UUID\|uuid.uuid4\|uuid.uuid5" core/ --include="*.py" | grep -v "__pycache__"
```

### Pattern 4: ID format validation/conversion
```bash
grep -rn "_fix_submission_id\|_resolve_submission\|convert.*id\|transform.*id" core/ --include="*.py" | grep -v "__pycache__"
```

### Pattern 5: Primary key definitions
```bash
grep -rn "PK_SUBMISSION_ID\|primary_key.*submission" core/ --include="*.py" | grep -v "__pycache__"
```

### Pattern 6: Database queries involving submission IDs
```bash
grep -rn "\.eq\(.*submission_id\|WHERE.*submission_id" core/ --include="*.py" | grep -v "__pycache__"
```

## Analysis Framework

For each location found, document:

### A. Basic Information
- **File path**: Absolute path to the file
- **Function/Method**: Name of the function or method
- **Line numbers**: Start and end lines of relevant code
- **Context**: Brief description of what this code does

### B. ID Field Analysis
- **Field name used**: Which field is being accessed (id, submission_id, reddit_id)
- **Expected format**: UUID | VARCHAR | Raw Reddit ID | Hybrid
- **Actual format observed**: What format does the data actually contain
- **Source of data**: Where does this ID value come from

### C. Operation Type
- **READ**: Code reads/queries using this ID
- **WRITE**: Code writes/inserts this ID
- **TRANSFORM**: Code converts between ID formats
- **VALIDATE**: Code validates ID format

### D. FK Relationship Impact
- Does this code expect the ID to reference `submissions.id` (UUID)?
- Does this code expect the ID to reference `submissions.submission_id`?
- Could a format mismatch cause FK violations?

## Output Format

Generate a markdown report at: `docs/id-resolution-fix/reports/01-audit-report.md`

The report MUST include these sections:

### Section 1: Executive Summary

Brief overview of findings including:
- Total locations audited
- Number of potential mismatches found
- Critical risk areas identified

### Section 2: ID Field Usage Matrix

Create a table showing which files use which ID fields:

```markdown
| File | submission_id | reddit_id | id (UUID) | Transforms |
|------|---------------|-----------|-----------|------------|
| core/storage/enhanced_hybrid_store.py | READ/WRITE | READ | WRITE | YES |
| ... | ... | ... | ... | ... |
```

### Section 3: Detailed Findings by File

For each file, create a subsection with:

```markdown
#### File: `core/storage/enhanced_hybrid_store.py`

**Purpose**: Enhanced storage service for enrichment data persistence

| Function | Line | ID Field | Format Expected | Operation | Risk |
|----------|------|----------|-----------------|-----------|------|
| `_fix_submission_id_formats` | 213-269 | submission_id | UUID | TRANSFORM | LOW |
| `_resolve_submission_uuid` | 473-535 | submission_id -> id | VARCHAR -> UUID | TRANSFORM | HIGH |
| `_get_or_create_opportunity_id` | 537-666 | submission_id | UUID | READ/WRITE | HIGH |

**Notes**:
- Line 578 calls `_resolve_submission_uuid` to convert raw IDs to UUIDs
- Line 613 uses resolved UUID for FK reference to submissions.id
- Potential issue: If source provides already-UUID submission_id, double resolution occurs
```

### Section 4: Transformation Chain Map

Document the complete transformation flow:

```markdown
## ID Transformation Chain

1. **Reddit API** produces: `reddit_id` (e.g., "1fp7k8t")
2. **Collection Pipeline** stores as: `submission_id` in submissions table
3. **Hybrid Crawler** may produce: synthetic IDs like "hybrid_1"
4. **EnhancedHybridStore._fix_submission_id_formats** converts non-UUID to UUID
5. **EnhancedHybridStore._resolve_submission_uuid** looks up UUID from submissions.id
6. **Enrichment tables** expect: UUID referencing submissions.id

### Known Breaking Points
- [List any locations where the chain breaks]
```

### Section 5: Mismatch Summary Table

```markdown
## Identified Mismatches

| Producer | Consumer | Expected Format | Actual Format | Severity |
|----------|----------|-----------------|---------------|----------|
| hybrid_crawler | enhanced_hybrid_store | UUID | "hybrid_N" | CRITICAL |
| database_verifier | submissions table | submission_id | id (UUID) | HIGH |
| ... | ... | ... | ... | ... |
```

### Section 6: Risk Assessment

Rate each finding:
- **CRITICAL**: Will cause FK violations or data loss
- **HIGH**: May cause lookup failures
- **MEDIUM**: Could cause data inconsistency
- **LOW**: Minor issues, unlikely to cause problems

### Section 7: Recommendations (Brief)

List specific areas that need fixing, prioritized by risk. DO NOT implement fixes - audit only.

## Validation Checklist

Before completing the audit, verify:

- [ ] All Priority 1 files have been examined
- [ ] At least 80% of Priority 2-5 files examined
- [ ] All grep patterns executed and results incorporated
- [ ] Each finding includes file path, function name, and line numbers
- [ ] Mismatch table is complete
- [ ] Risk assessment applied to all findings
- [ ] Report saved to correct location

## Special Attention Areas

Based on initial analysis, pay special attention to:

1. **`EnhancedHybridStore._fix_submission_id_formats`** (lines 213-269)
   - Converts "hybrid_N" style IDs to deterministic UUIDs using uuid5
   - May conflict with actual Reddit IDs

2. **`EnhancedHybridStore._resolve_submission_uuid`** (lines 473-535)
   - Attempts to resolve various ID formats to submissions.id UUID
   - Complex logic with multiple fallback paths

3. **`EnhancedHybridStore._get_or_create_opportunity_id`** (lines 537-666)
   - Creates entries in opportunities table
   - FK constraint: opportunities.submission_id -> submissions.id
   - CRITICAL: Must use resolved UUID, not raw string

4. **`DatabaseVerifier._verify_app_opportunities`** (lines 224-256)
   - Queries by submission_id
   - May be using wrong field for lookups

5. **DLT Constants `PK_SUBMISSION_ID`** (core/dlt/constants.py)
   - Defines "submission_id" as primary key
   - All DLT merge operations depend on this

## Output File Location

Save the completed audit report to:
```
/home/carlos/projects/redditharbor-core-functions-fix/docs/id-resolution-fix/reports/01-audit-report.md
```

Create the directory structure if it does not exist.

## Constraints

- **AUDIT ONLY**: Do not modify any code
- **Be thorough**: Document every location, even if it appears correct
- **Include line numbers**: Every finding must reference specific lines
- **Use absolute paths**: All file paths must be absolute
- **Focus on facts**: Document what IS, not what should be

---

## Example Output Structure

```markdown
# Submission ID Audit Report

**Generated**: [timestamp]
**Auditor**: Claude Code
**Scope**: RedditHarbor core submission ID handling

## Executive Summary

Audited X files across Y directories. Found Z potential ID format mismatches.

**Critical Findings**: N
**High Risk**: M
**Medium Risk**: P
**Low Risk**: Q

## ID Field Usage Matrix

[table here]

## Detailed Findings

### core/storage/enhanced_hybrid_store.py

[detailed analysis]

### core/storage/hybrid_store.py

[detailed analysis]

[... continue for all files ...]

## Transformation Chain Map

[diagram/description]

## Mismatch Summary

[table]

## Risk Assessment

[prioritized list]

## Recommendations

1. [area to fix]
2. [area to fix]
...
```
