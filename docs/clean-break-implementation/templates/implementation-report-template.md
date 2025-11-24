# Implementation Report Template

Use this template to report implementation results to the QA Auditor.

---

## Implementation Report: {TASK_ID}

**Task Title**: {TASK_TITLE}

**Submitted By**: {AGENT_NAME}

**Date**: {YYYY-MM-DD}

**Report Version**: 1 (increment for revisions: v2, v3, etc.)

---

## Implementation Summary

{Provide a brief summary of what was implemented:
- What changes were made?
- How do they address the requirements?
- Any notable decisions or approaches taken?}

---

## Files Modified

| File | Lines Changed | Type of Change |
|------|---------------|----------------|
| `{path/to/file.py}` | {line range} | {Added/Modified/Deleted} |
| `{path/to/file2.py}` | {line range} | {Added/Modified/Deleted} |

---

## Code Changes

### File: `{path/to/file.py}`

#### Before (Lines {start}-{end})
```python
{Original code before modification}
```

#### After (Lines {start}-{end})
```python
{Modified code after implementation}
```

#### Explanation
{Explain why these changes were made and how they meet requirements}

---

### File: `{path/to/file2.py}` (if applicable)

#### Before
```python
{Original code}
```

#### After
```python
{Modified code}
```

#### Explanation
{Explanation of changes}

---

## Tests Run and Results

### Test Command
```bash
{Exact command used to run tests}
```

### Test Output
```
{Paste relevant test output here}
```

### Test Summary

| Metric | Value |
|--------|-------|
| Total Tests | {number} |
| Passed | {number} |
| Failed | {number} |
| Skipped | {number} |
| Duration | {time} |

### Failed Tests (if any)

| Test Name | Failure Reason | Notes |
|-----------|----------------|-------|
| `{test_name}` | {reason} | {notes} |

---

## Issues Encountered

### Issue 1: {Issue Title}

**Description**: {What was the issue?}

**Resolution**: {How was it resolved?}

**Impact**: {Any impact on the implementation or timeline?}

---

### Issue 2: {Issue Title} (if applicable)

**Description**: {What was the issue?}

**Resolution**: {How was it resolved?}

**Impact**: {Any impact on the implementation or timeline?}

---

## Self-Assessment Checklist

### MUST Requirements

- [ ] {Requirement 1 from prompt} - **Status**: {Complete/Incomplete} - {Notes}
- [ ] {Requirement 2 from prompt} - **Status**: {Complete/Incomplete} - {Notes}
- [ ] {Requirement 3 from prompt} - **Status**: {Complete/Incomplete} - {Notes}

### SHOULD Requirements

- [ ] {Requirement 4 from prompt} - **Status**: {Complete/Incomplete/Skipped} - {Justification if skipped}
- [ ] {Requirement 5 from prompt} - **Status**: {Complete/Incomplete/Skipped} - {Justification if skipped}

### MAY Requirements

- [ ] {Requirement 6 from prompt} - **Status**: {Implemented/Deferred} - {Notes}

### Acceptance Criteria Verification

| Criterion | Met? | Evidence |
|-----------|------|----------|
| {Criterion 1 from prompt} | Yes/No | {Test name or verification method} |
| {Criterion 2 from prompt} | Yes/No | {Test name or verification method} |
| {Criterion 3 from prompt} | Yes/No | {Test name or verification method} |

---

## Additional Notes

{Any additional context, observations, or recommendations:
- Edge cases discovered
- Performance considerations
- Suggestions for future improvements
- Dependencies on other tasks}

---

## Ready for QA Review

**Ready**: Yes / No

**If No, explain**: {What needs to be completed before QA review?}

---

## Revision History (for subsequent versions)

| Version | Date | Changes Made | Addressing Feedback |
|---------|------|--------------|---------------------|
| v1 | {date} | Initial submission | N/A |
| v2 | {date} | {changes} | {feedback reference} |

---

## Template Usage Notes

1. Fill in all `{placeholder}` values
2. Remove sections marked "(if applicable)" if not relevant
3. Include actual code snippets, not descriptions
4. Paste real test output, not summaries
5. Be honest in self-assessment - it saves review cycles
6. Mark "Ready for QA Review" as "No" if any MUST requirements are incomplete
