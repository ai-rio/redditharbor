# QA Feedback Template

Use this template to provide feedback on Partner AI implementation reports.

---

## QA Feedback: {TASK_ID}

**Report Reviewed**: `partner-ai-reports/{TASK_ID}-implementation-report.md`

**Report Version**: {version number reviewed}

**Reviewed By**: QA Auditor

**Review Date**: {YYYY-MM-DD}

---

## Review Status

**Status**: APPROVED / NEEDS_REVISION / REJECTED

| Status | Meaning |
|--------|---------|
| APPROVED | Implementation meets all requirements, proceed to next task |
| NEEDS_REVISION | Implementation has issues that must be addressed |
| REJECTED | Implementation requires complete rework |

---

## Checklist Verification

### MUST Requirements

| # | Requirement | Partner Claimed | QA Verified | Notes |
|---|-------------|-----------------|-------------|-------|
| 1 | {Requirement text} | Complete/Incomplete | PASS/FAIL | {notes} |
| 2 | {Requirement text} | Complete/Incomplete | PASS/FAIL | {notes} |
| 3 | {Requirement text} | Complete/Incomplete | PASS/FAIL | {notes} |

### SHOULD Requirements

| # | Requirement | Partner Claimed | QA Verified | Notes |
|---|-------------|-----------------|-------------|-------|
| 4 | {Requirement text} | Complete/Skipped | PASS/FAIL/N/A | {notes} |
| 5 | {Requirement text} | Complete/Skipped | PASS/FAIL/N/A | {notes} |

### Acceptance Criteria

| Criterion | Partner Claimed | QA Verified | Evidence Reviewed |
|-----------|-----------------|-------------|-------------------|
| {Criterion 1} | Met/Not Met | PASS/FAIL | {what was checked} |
| {Criterion 2} | Met/Not Met | PASS/FAIL | {what was checked} |
| {Criterion 3} | Met/Not Met | PASS/FAIL | {what was checked} |

---

## Issues Found

### Issue 1: {Issue Title}

**Severity**: Critical / High / Medium / Low

**Category**: Bug / Missing Feature / Code Quality / Documentation / Testing

**Description**:
{Describe the issue in detail}

**Location**:
- File: `{path/to/file.py}`
- Lines: {line numbers}

**Expected Behavior**:
{What should happen}

**Actual Behavior**:
{What actually happens or is missing}

**Evidence**:
```
{Test output, code snippet, or other evidence}
```

---

### Issue 2: {Issue Title} (if applicable)

**Severity**: Critical / High / Medium / Low

**Category**: Bug / Missing Feature / Code Quality / Documentation / Testing

**Description**:
{Describe the issue}

**Location**:
- File: `{path/to/file.py}`
- Lines: {line numbers}

**Expected Behavior**:
{What should happen}

**Actual Behavior**:
{What actually happens}

---

## Required Changes

{List specific changes that must be made for APPROVED status}

### For NEEDS_REVISION

1. **{Change 1 Title}**
   - What: {Specific change required}
   - Where: `{file:lines}`
   - Why: {Addresses Issue #X}

2. **{Change 2 Title}**
   - What: {Specific change required}
   - Where: `{file:lines}`
   - Why: {Addresses Issue #X}

### For REJECTED

{Explain why complete rework is needed and provide guidance for restarting}

---

## Positive Feedback

{Acknowledge what was done well:
- Clean code structure
- Good test coverage
- Clear documentation
- Creative solutions}

---

## Verification Commands Used

```bash
# Commands run during QA review
{command 1}
{command 2}
```

---

## Approved for Next Task

**Approved**: Yes / No

**Next Task**: {TASK_ID if approved, or "Address feedback first" if not}

**Blocking Issues**: {List any issues that block proceeding}

---

## QA Notes

{Additional observations, recommendations, or context:
- Patterns noticed
- Potential future issues
- Suggestions beyond requirements
- Dependencies affected}

---

## Revision Tracking

| Revision | Date | Status | Key Changes |
|----------|------|--------|-------------|
| v1 | {date} | {status} | Initial review |
| v2 | {date} | {status} | {what changed} |

---

## Template Usage Notes

1. Be specific about issues - vague feedback wastes cycles
2. Include evidence (test output, code snippets)
3. Distinguish between blocking issues and suggestions
4. Acknowledge good work alongside improvements needed
5. Provide actionable guidance for NEEDS_REVISION status
6. Use REJECTED sparingly - only for fundamental problems
