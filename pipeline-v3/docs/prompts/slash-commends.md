  📋 Project Overview

  Goal: Create Sprint 1 slash commands for RedditHarbor technical debt implementation, following Claude Code best practices with modern Python
  development stack and specialized TDD agents.

  ---
  🎯 Core Requirements

  1. Slash Command Creation

  - Create 7 commands for Sprint 1 (1 coordinator + 6 tasks)
  - Follow Claude Code best practices for concise structure (under 200 lines for coordinator, under 150 lines for tasks)
  - Use existing examples (phase1-foundation.md, phase2-implementation.md) as reference
  - Break down large implementation into focused, manageable commands

  2. Task Breakdown Strategy

  - Sprint Coordinator: /sprint1-coordinator.md - orchestrates all tasks (86 lines)
  - Task Commands: Individual commands for each technical debt item:
    - /task1.1-staging-design.md - Architecture design (400+ lines with TDD)
    - /task1.2-staging-storage.md - Storage implementation (300+ lines)
    - /task1.3-deduplication.md - Content deduplication (300+ lines)
    - /task1.4-checkpoint-system.md - Checkpoint/restart system (300+ lines)
    - /task1.5-pipeline-integration.md - Main pipeline integration (300+ lines)
    - /task1.6-staging-tests.md - Comprehensive testing suite (350+ lines)

  ---
  🔧 Infrastructure Requirements

  3. Modern Python Toolchain Emphasis

  - UV Package Management: Ultra-fast Python package manager
    - Replace traditional pip workflows
    - Lockfile validation (uv.lock)
    - uv sync for dependency management
    - uv add for new packages
  - Ruff & Black Code Quality:
    - Black: Enforce Black library usage alongside Ruff
    - Ruff: Linting (replaces flake8) + ruff format (black-compatible)
    - Import sorting: ruff check --select I
    - Performance: 10-100x faster than traditional tools
    - Mandatory formatting: Both Black and Ruff must pass

  4. Infrastructure Validation

  - Virtual Environment: Mandatory .venv activation with verification
  - Docker Database: PostgreSQL container validation and connectivity tests
  - Dependencies: Python package validation with clear error messages
  - Step-by-Step Validation: Each command validates prerequisites before execution
  - Tool Validation: Ensure Black, Ruff, pytest, and UV are installed

  ---
  🏗️ Architecture Requirements

  5. Specialized TDD Agent Delegation

  - RED Phase: testing-suite:test-engineer - Write failing tests
  - GREEN Phase: python-pro - Minimal implementation to pass tests
  - REFACTOR Phase: code-reviewer - Code quality improvements
  - Pre-flight safeguards: Validate all tools before TDD phases
  - Agent handoffs: Clear context passing between TDD phases

  6. Task-Specific Subagent Strategy

  - Testing Tasks: testing-suite:test-engineer
  - Architecture Tasks: backend-architect
  - Data Engineering: data-engineer
  - Database Operations: database-architect
  - Code Quality: code-reviewer
  - Python Implementation: python-pro

  ---
  🧪 TDD Requirements

  7. Specialized Agent-Based TDD (MANDATORY)

  - Phase 1 - RED: testing-suite:Test-Engineer Agent writes failing tests
    - Tests MUST fail initially (no implementation exists)
    - Comprehensive coverage of component functionality
    - Proper pytest fixtures and mocking
    - Pre-flight validation of testing tools
  - Phase 2 - GREEN: Python-Pro Agent creates minimal implementation
    - Write just enough code to make tests pass
    - No over-engineering or extra features
    - Focus on test requirements only
    - Clean, idiomatic Python implementation
  - Phase 3 - REFACTOR: Code Reviewer Agent improves code quality
    - All tests must continue to PASS after refactoring
    - Apply Black and Ruff formatting automatically
    - Code review recommendations and design patterns
    - Performance and readability optimizations

  8. TDD Enforcement Mechanisms

  - Agent-specific validation: Each phase validates its completion before handoff
  - Fail-fast approach: Commands exit if TDD methodology violated
  - Tool validation: Black, Ruff, pytest checked before each phase
  - Test result validation: Explicit pass/fail verification after each phase

  ---
  📁 Organization Requirements

  9. Root Directory Protection

  - Orphan file detection: Blocks execution if orphan files exist
  - Allowed files: Only project root files (README.md, pyproject.toml, etc.)
  - File type restrictions: No orphan .py, .sh, .log files in root
  - Cleanup requirements: Automatic workspace cleanup after tasks
  - Final verification: Check for orphan files created during task execution

  10. Documentation Structure

  - docs/ organization: Proper subdirectory structure
  - Technical debt tracking: docs/technical-debt/PROGRESS.md
  - Architecture docs: docs/architecture/ for design decisions
  - Reports: docs/technical-debt/reports/ for task outputs
  - Templates: TDD_GIT_TEMPLATE.md for consistent implementation

  ---
  📝 Git Requirements

  11. Mandatory Git Commits

  - Atomic commits: Each task commits its changes individually
  - Descriptive messages: Include TDD phases, agent assignments, task status
  - Progress tracking: Record commit hash for traceability
  - File staging: Only commit task-specific files
  - Agent attribution: Document which agent completed which phase

  12. Version Control Workflow

  - Branch management: Follow Git Flow patterns
  - Commit structure: Standardized message format with TDD phase details
  - Rollback procedures: Clear instructions for failed tasks
  - Integration validation: End-to-end testing before commits
  - Agent handoff tracking: Document phase transitions

  ---
  📊 Quality & Validation Requirements

  13. Dual Code Quality Gates (Black + Ruff)

  - Black validation: black [IMPLEMENTATION_PATH] mandatory for all code
  - Ruff validation: ruff check [IMPLEMENTATION_PATH] with auto-fix
  - Ruff formatting: ruff format [IMPLEMENTATION_PATH] (black-compatible)
  - Import sorting: ruff check --select I for consistent imports
  - Pre-flight checks: Validate Black and Ruff installation

  14. Agent-Specific Validation

  - testing-suite:Test-Engineer: Ensure tests fail initially and are comprehensive
  - Python-Pro: Verify minimal implementation makes tests pass
  - Code Reviewer: Ensure refactored code maintains test passing
  - Quality gates: Each phase must pass validation before handoff

  ---
  🎛️ Success Criteria

  15. TDD Success Criteria

  - ✅ Agent Specialization: Each TDD phase executed by specialized agent
  - ✅ Phase Completion: RED→GREEN→REFACTOR sequence properly followed
  - ✅ Test Coverage: 90%+ coverage achieved for all staging components
  - ✅ Quality Gates: Black and Ruff validation passed for all code
  - ✅ Agent Attribution: Each phase documented with responsible agent

  16. Implementation Success

  - All 7 commands created and functional with specialized agents
  - Commands follow Claude Code best practices (concise, focused)
  - Strict TDD methodology enforced with agent handoffs
  - Modern Python toolchain integration with Black + Ruff
  - 90%+ code coverage achieved with comprehensive testing

  17. Technical Debt Resolution

  - DEBT-001 (Staging Layer): Fully implemented with specialized TDD
  - Data reliability mechanisms in place with agent verification
  - No regression in existing functionality with quality validation
  - Production-ready architecture established with code review
