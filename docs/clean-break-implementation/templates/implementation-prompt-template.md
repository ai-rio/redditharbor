# Implementation Prompt Template

Use this template to create task prompts for Partner AI subagents.

---

## Task: {TASK_ID} - {TASK_TITLE}

### Assigned Subagent

**Agent**: `{AGENT_NAME}` (e.g., `python-pro`, `test-runner`, `database-expert`)

### Context/Background

{Provide context about why this task is needed. Include:
- What problem does this solve?
- How does it fit into the larger feature?
- What dependencies exist on previous tasks?
- Any relevant architecture decisions}

### Requirements

#### MUST (Required)

- [ ] {Requirement 1 - Mandatory for acceptance}
- [ ] {Requirement 2 - Mandatory for acceptance}
- [ ] {Requirement 3 - Mandatory for acceptance}

#### SHOULD (Expected)

- [ ] {Requirement 4 - Expected unless justified}
- [ ] {Requirement 5 - Expected unless justified}

#### MAY (Optional)

- [ ] {Requirement 6 - Nice to have}
- [ ] {Requirement 7 - Future enhancement consideration}

### Files to Modify

| File | Lines | Description |
|------|-------|-------------|
| `{path/to/file1.py}` | {line range} | {What to modify} |
| `{path/to/file2.py}` | {line range} | {What to modify} |

### Detailed Instructions

{Provide step-by-step instructions:

1. **Step 1 Title**
   - Detail about step 1
   - Code example if helpful:
   ```python
   # Example code
   def example():
       pass
   ```

2. **Step 2 Title**
   - Detail about step 2

3. **Step 3 Title**
   - Detail about step 3
}

### Code Examples

#### Before (Current Implementation)
```python
{Show current code that needs modification}
```

#### After (Expected Implementation)
```python
{Show expected code after modification}
```

### Acceptance Criteria

All of the following MUST be true for this task to be accepted:

1. [ ] {Criterion 1 - Specific, measurable, testable}
2. [ ] {Criterion 2 - Specific, measurable, testable}
3. [ ] {Criterion 3 - Specific, measurable, testable}

### Verification Commands

Run these commands to verify your implementation:

```bash
# Command 1 - Description
{command}

# Command 2 - Description
{command}
```

### Report Template

Use the following template for your implementation report:

**Template**: `templates/implementation-report-template.md`

**Report Location**: Place completed report at:
```
docs/clean-break-implementation/partner-ai-reports/{TASK_ID}-implementation-report.md
```

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| {Previous Task ID} | {Complete/Pending} | {Dependency details} |
| {External Resource} | {Available/Unavailable} | {Resource details} |

### Reference Materials

- {Link or path to relevant documentation}
- {Link or path to related code}
- {Link or path to test file}

---

## Template Usage Notes

1. Replace all `{placeholder}` values with actual content
2. Remove any sections not applicable to this task
3. Add sections as needed for task-specific requirements
4. Be specific about line numbers and file paths
5. Include code examples for complex changes
6. Define acceptance criteria that can be objectively verified
