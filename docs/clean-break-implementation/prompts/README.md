# Partner AI Workflow Documentation

This directory contains prompts, templates, and reports for the **Pre-DLT ID Normalization** feature implementation using a structured Partner AI workflow.

## Workflow Overview

The Partner AI Workflow enables structured, auditable collaboration between:

- **QA Auditor (Human + Claude)**: Defines requirements, reviews implementation, provides feedback
- **Partner AI (Subagents)**: Executes implementation tasks, reports results using templates

## Directory Structure

```
docs/clean-break-implementation/
├── prompts/                  # Task prompts for Partner AI
│   ├── README.md             # This file
│   ├── 01-transform-submission-prompt.md
│   ├── 02-transform-comment-prompt.md
│   ├── 03-update-schema-columns-prompt.md
│   └── 04-verify-tests-prompt.md
│
├── templates/                # Standardized communication templates
│   ├── implementation-prompt-template.md
│   ├── implementation-report-template.md
│   └── qa-feedback-template.md
│
├── partner-ai-reports/       # Completed reports from Partner AI
│   └── (Partner AI places completed reports here)
│
└── qa-feedback/              # QA Auditor feedback on reports
    └── (QA Auditor places feedback here)
```

## Workflow Process

### Phase 1: Task Assignment

1. QA Auditor creates task prompt using `implementation-prompt-template.md`
2. Prompt is placed in `prompts/` directory with numbered prefix (e.g., `01-`, `02-`)
3. Each prompt specifies:
   - Task ID and assigned subagent
   - Requirements (MUST/SHOULD/MAY)
   - Files to modify with line numbers
   - Acceptance criteria
   - Report template to use

### Phase 2: Implementation

1. Partner AI reads the task prompt
2. Executes implementation following requirements
3. Creates report using `implementation-report-template.md`
4. Places completed report in `partner-ai-reports/` with naming convention:
   - `{TASK_ID}-implementation-report.md` (e.g., `01-implementation-report.md`)

### Phase 3: QA Review

1. QA Auditor reviews the implementation report
2. Creates feedback using `qa-feedback-template.md`
3. Places feedback in `qa-feedback/` with naming convention:
   - `{TASK_ID}-qa-feedback.md` (e.g., `01-qa-feedback.md`)
4. Feedback status determines next action:
   - **APPROVED**: Proceed to next task
   - **NEEDS_REVISION**: Partner AI addresses issues, resubmits
   - **REJECTED**: Task requires complete rework

### Phase 4: Iteration (if needed)

1. If NEEDS_REVISION, Partner AI:
   - Reviews feedback
   - Makes required changes
   - Submits updated report with suffix: `{TASK_ID}-implementation-report-v2.md`
2. QA Auditor reviews again
3. Repeat until APPROVED or REJECTED

## TDD Workflow

This implementation follows **Test-Driven Development (TDD)**, a software development approach where tests are written BEFORE implementation code.

### The RED/GREEN/REFACTOR Cycle

```
+-------+       +--------+       +----------+
|  RED  |  -->  | GREEN  |  -->  | REFACTOR |
+-------+       +--------+       +----------+
   |                |                  |
   v                v                  v
Tests FAIL     Tests PASS      Clean up code
(expected)     (your goal)    (keep tests green)
```

### Phase Status

| Phase | Status | Description |
|-------|--------|-------------|
| **RED** | COMPLETE | Tests written first - currently FAILING (34 of 55 tests fail) |
| **GREEN** | YOUR TASK | Implement minimum code to make all 55 tests PASS |
| **REFACTOR** | LATER | Clean up and optimize while keeping tests green |

### Why TDD?

1. **Tests define behavior** - The tests are the specification. Read them to understand what the code should do.
2. **Confidence in changes** - Passing tests prove the implementation is correct.
3. **Prevents over-engineering** - Write only the code needed to pass tests.
4. **Regression safety** - Tests catch any breaking changes immediately.

### Partner AI's Role

As the Partner AI, your job is to transition from **RED to GREEN**:

1. **Run tests first** to confirm RED state (tests should fail before you start)
2. **Read the failing tests** to understand expected behavior
3. **Implement the minimum code** needed to make tests pass
4. **Run tests after each change** to track progress
5. **Stop when all tests are GREEN** (55/55 passing)

### Pre-Implementation Verification

Before making ANY code changes, run:

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix
pytest tests/test_dlt_id_normalization.py -v --tb=no | grep -E "(PASSED|FAILED|ERROR)"
```

Expected output: Multiple FAILED tests (this confirms RED phase is ready for implementation).

### Post-Implementation Verification

After completing all tasks, run:

```bash
pytest tests/test_dlt_id_normalization.py -v
```

Expected output: `55 passed` (this confirms GREEN phase is complete).

---

## Feature: Pre-DLT ID Normalization

### Purpose

Modify DLT transform functions to normalize Reddit IDs to UUIDs **before** data enters the DLT pipeline, ensuring consistent primary keys and foreign key alignment.

### Implementation Tasks

| Task | File | Function | Description |
|------|------|----------|-------------|
| 01 | `core/dlt/collection.py` | `transform_submission_to_schema()` | Add ID normalization for submissions |
| 02 | `core/dlt/collection.py` | `transform_comment_to_schema()` | Add ID normalization for comments |
| 03 | `core/dlt/collection.py` | DLT resource definitions | Update column schema hints |
| 04 | `tests/test_dlt_id_normalization.py` | All tests | Verify GREEN phase (55 tests pass) |

### Key Components

- **ID Resolver**: `core/utils/id_resolver.py` - Provides `resolve_submission_id()` function
- **Transform Functions**: `core/dlt/collection.py` - Lines 113-152 (submission), 290-334 (comment)
- **Test File**: `tests/test_dlt_id_normalization.py` - 55 tests, 34 currently failing

### Success Criteria

1. All 55 tests in `test_dlt_id_normalization.py` pass
2. Transform functions produce deterministic UUIDs
3. Original Reddit IDs preserved in `reddit_id` / `reddit_comment_id` / `reddit_submission_id` fields
4. Foreign key alignment maintained between comments and submissions

## How to Use This Workflow

### For Partner AI (Subagents)

1. Read your assigned prompt in `prompts/`
2. Implement following MUST/SHOULD/MAY requirements
3. Run tests as specified in acceptance criteria
4. Create report using the template
5. Place report in `partner-ai-reports/`

### For QA Auditor

1. Create prompts using `implementation-prompt-template.md`
2. Wait for Partner AI reports
3. Review reports against acceptance criteria
4. Provide feedback using `qa-feedback-template.md`
5. Track progress through task completion

## Naming Conventions

### Prompts
```
{NN}-{descriptive-name}-prompt.md
Example: 01-transform-submission-prompt.md
```

### Reports
```
{NN}-implementation-report.md        # Initial submission
{NN}-implementation-report-v2.md     # Revision 2
{NN}-implementation-report-v3.md     # Revision 3
```

### Feedback
```
{NN}-qa-feedback.md                  # Initial feedback
{NN}-qa-feedback-v2.md               # Feedback on revision
```

## Requirements Language

- **MUST**: Required for acceptance
- **SHOULD**: Expected unless justified otherwise
- **MAY**: Optional enhancement
