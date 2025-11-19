# Local AI Testing Guide

This document helps you quickly find the right testing prompt for your local AI agent.

## Quick Start

### For Local AI Agents

**Current Phase**: Phase 3 - Extract Utilities (Task 2)

**Read this prompt**:
```bash
cat docs/plans/unified-pipeline-refactoring/prompts/phase-3-task-2-local-testing-prompt.md
```

**Then execute the testing instructions step-by-step.**

---

## All Available Testing Prompts

| Phase | Status | Prompt File |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete & Validated | [phase-1-local-testing-prompt.md](prompts/phase-1-local-testing-prompt.md) |
| **Phase 2** | ✅ Complete & Validated | [phase-2-local-testing-prompt.md](prompts/phase-2-local-testing-prompt.md) |
| **Phase 3 Task 1** | ✅ Complete & Validated | [phase-3-task-1-local-testing-prompt.md](prompts/phase-3-task-1-local-testing-prompt.md) |
| **Phase 3 Task 2** | 🟡 Awaiting Local Testing | [phase-3-task-2-local-testing-prompt.md](prompts/phase-3-task-2-local-testing-prompt.md) |
| **Phase 4** | ⏸️ Not Started | (Coming soon) |

---

## Testing Workflow

### 1. Pull Latest Changes

```bash
git fetch origin
git checkout claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
git pull
```

### 2. Read the Testing Prompt

For Phase 3 Task 2:
```bash
cat docs/plans/unified-pipeline-refactoring/prompts/phase-3-task-2-local-testing-prompt.md
```

### 3. Execute Tests

Follow the step-by-step instructions in the prompt.

### 4. Generate Report

Save your test results to:
```
docs/plans/unified-pipeline-refactoring/local-ai-report/phase-3-task-2-testing-report.md
```

### 5. Commit and Push

```bash
git add docs/plans/unified-pipeline-refactoring/local-ai-report/phase-3-task-2-testing-report.md
git commit -m "test: Add Phase 3 Task 2 local testing report"
git push
```

---

## Testing Reports

All testing reports are saved in:
```
docs/plans/unified-pipeline-refactoring/local-ai-report/
```

**Phase 1**: [phase-1-testing-report.md](local-ai-report/phase-1-testing-report.md) - ✅ Complete
**Phase 2**: [phase-2-testing-report.md](local-ai-report/phase-2-testing-report.md) - ✅ Complete
**Phase 3 Task 1**: [phase-3-task-1-testing-report.md](local-ai-report/phase-3-task-1-testing-report.md) - ✅ Complete
**Phase 3 Task 2**: Awaiting local testing

---

## Need Help?

- **Prompt Structure**: See [prompts/README.md](prompts/README.md)
- **Phase Plans**: See [phases/](phases/)
- **Execution Logs**: See [execution-logs/](execution-logs/)

---

**Last Updated**: 2025-11-19
**Current Testing Phase**: Phase 3 Task 2
