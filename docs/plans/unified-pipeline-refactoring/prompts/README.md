# Local AI Testing Prompts

This directory contains dedicated testing prompts for each phase of the unified pipeline refactoring.

## Purpose

Each prompt file provides:
- Clear testing instructions for local AI agents
- Step-by-step validation procedures
- Expected outcomes and success criteria
- What to report back to the remote development team

## Prompt Files

| Phase | File | Purpose |
|-------|------|---------|
| **Phase 1** | `phase-1-local-testing-prompt.md` | Test foundation structure, base classes, and config |
| **Phase 2** | `phase-2-local-testing-prompt.md` | Test agent restructuring, imports, and production scripts |
| **Phase 3** | `phase-3-local-testing-prompt.md` | Test utility extraction (future) |
| **Phase 4** | `phase-4-local-testing-prompt.md` | Test data fetching layer (future) |

## Usage

**For Local AI Agents:**

```bash
# 1. Pull latest changes from remote
git pull origin <branch-name>

# 2. Read the phase prompt
cat docs/plans/unified-pipeline-refactoring/prompts/phase-X-local-testing-prompt.md

# 3. Execute the testing instructions
# Follow the step-by-step validation procedures

# 4. Generate a report
# Document results in local-ai-report/phase-X-testing-report.md
```

**For Human Developers:**

You can also use these prompts as testing checklists when validating phase completion manually.

## Report Location

Test reports are saved in:
```
docs/plans/unified-pipeline-refactoring/local-ai-report/
├── README.md
├── phase-1-testing-report.md
├── phase-2-testing-report.md
└── ...
```

## Workflow

1. **Remote AI** completes a phase and commits changes
2. **Remote AI** creates a local testing prompt for that phase
3. **Local AI** pulls changes and reads the prompt
4. **Local AI** executes validation tests
5. **Local AI** generates a testing report
6. **Remote AI** reviews the report and fixes any issues

---

**Created**: 2025-11-19
**Last Updated**: 2025-11-19
