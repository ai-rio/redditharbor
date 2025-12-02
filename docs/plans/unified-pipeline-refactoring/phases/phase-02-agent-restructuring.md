# Phase 2: Agent Tools Restructuring

**Timeline**: Week 1-2, Days 3-5  
**Duration**: 3 days  
**Risk Level**: 🟡 MEDIUM  
**Dependencies**: Phase 1 completed, module structure created

---

## Context

### What Was Completed (Phase 1)
- [x] Created complete modular directory structure
- [x] Added `__init__.py` files with proper exports
- [x] Set up testing infrastructure and CI/CD
- [x] Established baseline performance metrics

### Current State
```
agent_tools/                    # 🔴 Flat structure, large files
├── llm_profiler_enhanced.py    # 37KB
├── market_data_validator.py    # 70KB (VERY LARGE!)
├── monetization_agno_analyzer.py # 63KB
├── jina_*.py                   # Multiple Jina clients
└── ... (15+ files total)
```

### Why This Phase Is Critical
- These are the AI services that `core/enrichment/` will wrap
- 70KB+ files are technical debt that will complicate debugging
- Clean structure establishes import patterns for the entire project
- Doing this now prevents future refactoring during enrichment phase

---

## Objectives

### Primary Goals
1. **Restructure** `agent_tools/` into logical `core/agents/` modules
2. **Break up** monolithic files (70KB → multiple focused files)
3. **Establish** clean import patterns for AI services
4. **Validate** all existing functionality still works

### Success Criteria
- [x] All files moved to new `core/agents/` structure
- [x] Files over 30KB broken into logical modules
- [x] All imports updated across codebase
- [x] All existing tests passing
- [x] New structure documented in CLAUDE.md

### Risk Mitigation
- Keep `agent_tools/` as backup until validation complete
- Update imports incrementally and test after each change
- Use IDE refactoring tools to catch all import references

---

## Tasks

### Task 1: Create core/agents/ Structure (30 minutes)

```bash
# Create directory structure
mkdir -p core/agents/{profiler,monetization,market_validation,search,interactive}

# Create __init__.py files
touch core/agents/__init__.py
touch core/agents/profiler/__init__.py
touch core/agents/monetization/__init__.py
touch core/agents/market_validation/__init__.py
touch core/agents/search/__init__.py
touch core/agents/interactive/__init__.py
```

**Validation:**
- [ ] All directories created
- [ ] All `__init__.py` files present
- [ ] Structure matches design doc

---

### Task 2: Restructure Profiler Module (2 hours)

**Priority: HIGH** - Critical dependency for enrichment services

```bash
# Move and rename
mv agent_tools/llm_profiler_enhanced.py core/agents/profiler/enhanced_profiler.py
mv agent_tools/llm_profiler.py core/agents/profiler/base_profiler.py
```

**Then break up enhanced_profiler.py (37KB) into:**
```python
core/agents/profiler/
├── __init__.py                 # Public exports
├── enhanced_profiler.py        # Main class (keep <20KB)
├── prompt_templates.py         # Extracted prompts
└── response_parser.py          # Extracted parsing logic
```

**Update imports:**
```python
# In core/agents/profiler/__init__.py
from .enhanced_profiler import EnhancedLLMProfiler
from .base_profiler import BaseLLMProfiler

__all__ = ['EnhancedLLMProfiler', 'BaseLLMProfiler']
```

**Validation:**
- [ ] Files moved and organized
- [ ] enhanced_profiler.py <20KB
- [ ] Imports work: `from core.agents.profiler import EnhancedLLMProfiler`
- [ ] Existing tests pass: `pytest tests/test_profiler* -v`

---

### Task 3: Restructure Market Validation Module (3 hours)

**Priority: HIGH** - 70KB file needs immediate attention

```bash
# Move file
mv agent_tools/market_data_validator.py core/agents/market_validation/validator.py
mv agent_tools/market_validation_integration.py core/agents/market_validation/integration.py
mv agent_tools/market_validation_persistence.py core/agents/market_validation/persistence.py
```

**Break up validator.py (70KB → 3 files):**
```python
core/agents/market_validation/
├── __init__.py
├── validator.py               # Main MarketDataValidator class (25KB)
├── search_client.py           # Jina/web search logic (20KB)
├── analysis_engine.py         # Data analysis logic (20KB)
├── integration.py             # Existing file
└── persistence.py             # Existing file
```

**Refactoring validator.py:**
```python
# Extract search logic
class SearchClient:
    def search_competitors(self, query: str) -> List[str]:
        # Move Jina search logic here
        pass

# Extract analysis logic  
class AnalysisEngine:
    def analyze_market_data(self, data: Dict) -> Dict:
        # Move analysis logic here
        pass

# Updated validator uses composition
class MarketDataValidator:
    def __init__(self):
        self.search_client = SearchClient()
        self.analysis_engine = AnalysisEngine()
    
    def validate(self, submission: dict) -> dict:
        # Orchestrate using search_client and analysis_engine
        pass
```

**Validation:**
- [ ] 70KB file split into logical components
- [ ] Each file <30KB
- [ ] All existing functionality preserved
- [ ] Tests pass: `pytest tests/test_market* -v`
- [ ] Import works: `from core.agents.market_validation import MarketDataValidator`

---

### Task 4: Restructure Monetization Module (2 hours)

```bash
# Move files
mv agent_tools/monetization_agno_analyzer.py core/agents/monetization/agno_analyzer.py
mv agent_tools/monetization_llm_analyzer.py core/agents/monetization/llm_analyzer.py
mv agent_tools/monetization_analyzer_factory.py core/agents/monetization/factory.py
```

**Break up agno_analyzer.py (63KB → 3 files):**
```python
core/agents/monetization/
├── __init__.py
├── agno_analyzer.py           # Main class (25KB)
├── multi_agent_pipeline.py    # Agent orchestration (20KB)
├── pricing_calculator.py      # Pricing logic (15KB)
├── llm_analyzer.py            # Existing
└── factory.py                 # Existing
```

**Validation:**
- [ ] Files reorganized
- [ ] agno_analyzer.py <30KB
- [ ] All monetization tests pass
- [ ] Import works: `from core.agents.monetization import MonetizationAgnoAnalyzer`

---

### Task 5: Consolidate Search Clients (1 hour)

**Goal:** Unify multiple Jina client implementations

```bash
# Move files
mv agent_tools/jina_hybrid_client.py core/agents/search/hybrid_client.py
mv agent_tools/jina_mcp_client.py core/agents/search/mcp_client.py
mv agent_tools/jina_mcp_client_simple.py core/agents/search/mcp_client_simple.py
mv agent_tools/jina_reader_client.py core/agents/search/reader_client.py
```

**Create unified interface:**
```python
# core/agents/search/__init__.py
from .hybrid_client import JinaHybridClient
from .reader_client import JinaReaderClient

# Provide factory for easy selection
def get_jina_client(client_type: str = 'hybrid'):
    if client_type == 'hybrid':
        return JinaHybridClient()
    elif client_type == 'reader':
        return JinaReaderClient()
    else:
        raise ValueError(f"Unknown client type: {client_type}")
```

**Validation:**
- [ ] All Jina clients moved
- [ ] Factory pattern works
- [ ] Existing search tests pass

---

### Task 6: Move Remaining Modules (30 minutes)

```bash
# Interactive analyzer
mv agent_tools/interactive_analyzer.py core/agents/interactive/analyzer.py

# Agno validation converter
mv agent_tools/agno_validation_converter.py core/agents/monetization/validation_converter.py
```

**Validation:**
- [ ] All files accounted for
- [ ] No files remain in agent_tools/
- [ ] All modules have proper `__init__.py`

---

### Task 7: Update All Imports Across Codebase (2 hours)

**Critical Step:** Update all references to agent_tools

**Strategy:**
```bash
# Find all imports
grep -r "from agent_tools" . --include="*.py" > /tmp/imports_to_update.txt
grep -r "import agent_tools" . --include="*.py" >> /tmp/imports_to_update.txt

# Example replacements:
# OLD: from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler
# NEW: from core.agents.profiler import EnhancedLLMProfiler

# OLD: from agent_tools.market_data_validator import MarketDataValidator  
# NEW: from core.agents.market_validation import MarketDataValidator

# OLD: from agent_tools.monetization_agno_analyzer import MonetizationAgnoAnalyzer
# NEW: from core.agents.monetization import MonetizationAgnoAnalyzer
```

**Files to update (likely candidates):**
```bash
# Find files that import from agent_tools
find . -name "*.py" -exec grep -l "agent_tools" {} \; | grep -v __pycache__
```

Common locations:
- `scripts/core/batch_opportunity_scoring.py`
- `scripts/dlt/dlt_trust_pipeline.py`
- `tests/test_*.py`
- Any other scripts that use AI agents

**Validation:**
- [ ] Run: `grep -r "agent_tools" . --include="*.py" | grep -v __pycache__ | wc -l` → should be 0
- [ ] All Python files parse: `python -m py_compile <file>`
- [ ] All imports resolve: `python -c "from core.agents.profiler import EnhancedLLMProfiler"`

---

### Task 8: Update Documentation (30 minutes)

**Update CLAUDE.md:**
```markdown
### Module Architecture Boundaries

Core modules:
- `core/agents/` - AI service implementations
  - `profiler/` - EnhancedLLMProfiler and variants
  - `monetization/` - MonetizationAgnoAnalyzer and pricing
  - `market_validation/` - MarketDataValidator and search
  - `search/` - Jina client implementations
  - `interactive/` - Interactive analysis tools
- `core/enrichment/` - Service wrappers for pipeline integration
- `core/fetchers/` - Data acquisition layer
...
```

**Create agent_tools/README.md (deprecation notice):**
```markdown
# DEPRECATED: agent_tools/

This directory has been restructured and moved to `core/agents/`.

## Migration Guide

Old imports → New imports:

- `from agent_tools.llm_profiler_enhanced import EnhancedLLMProfiler`  
  → `from core.agents.profiler import EnhancedLLMProfiler`

- `from agent_tools.market_data_validator import MarketDataValidator`  
  → `from core.agents.market_validation import MarketDataValidator`

- `from agent_tools.monetization_agno_analyzer import MonetizationAgnoAnalyzer`  
  → `from core.agents.monetization import MonetizationAgnoAnalyzer`

See `core/agents/README.md` for complete documentation.
```

**Create core/agents/README.md:**
```markdown
# RedditHarbor AI Agents

This directory contains all AI service implementations used by the pipeline.

## Module Structure

- `profiler/` - AI profiling services (app name, core functions extraction)
- `monetization/` - Monetization analysis (WTP, pricing, segments)
- `market_validation/` - Market research and competitor analysis
- `search/` - Search client implementations (Jina, web search)
- `interactive/` - Interactive analysis tools

## Usage

```python
from core.agents.profiler import EnhancedLLMProfiler
from core.agents.monetization import MonetizationAgnoAnalyzer
from core.agents.market_validation import MarketDataValidator

# Use in pipeline
profiler = EnhancedLLMProfiler()
result = profiler.generate_profile(submission)
```

See individual module READMEs for detailed documentation.
```

**Validation:**
- [ ] CLAUDE.md updated
- [ ] Deprecation notice created
- [ ] New README created
- [ ] All documentation references updated

---

## Full Validation Checklist

### Structural Validation
- [ ] All files moved from `agent_tools/` to `core/agents/`
- [ ] No files >30KB (check: `find core/agents -name "*.py" -size +30k`)
- [ ] All modules have `__init__.py` with exports
- [ ] Logical grouping makes sense (profiler, monetization, etc.)

### Functional Validation
- [ ] All Python files parse correctly
- [ ] All imports resolve
- [ ] All existing unit tests pass: `pytest tests/ -v`
- [ ] All integration tests pass

### Import Validation
- [ ] No references to `agent_tools` remain: `grep -r "agent_tools" . --include="*.py" | grep -v __pycache__`
- [ ] New imports work across codebase
- [ ] PYTHONPATH doesn't need adjustment

### Performance Validation
- [ ] Import time not significantly increased
- [ ] No circular import issues
- [ ] Module loading works correctly

### Documentation Validation
- [ ] CLAUDE.md reflects new structure
- [ ] Deprecation notice in old location
- [ ] README in core/agents/
- [ ] Module-level docstrings updated

---

## Rollback Procedure

If this phase fails or causes issues:

### Step 1: Restore Original Structure
```bash
# If you kept agent_tools/ as backup
rm -rf core/agents/
git restore agent_tools/

# Revert all import changes
git diff HEAD -- '*.py' | grep -E '(from core\.agents|import core\.agents)' > /tmp/revert.patch
git checkout HEAD -- '*.py'
```

### Step 2: Validate Rollback
```bash
# Verify original structure works
pytest tests/ -v
python scripts/core/batch_opportunity_scoring.py --help
```

### Step 3: Document Issues
Create rollback report:
```markdown
# Phase 2 Rollback Report

## Issues Encountered
- [List specific failures]

## Files Affected
- [List problematic files]

## Recommended Approach
- [Alternative strategy]
```

### Step 4: Next Steps
- Review issues with team
- Adjust approach if needed
- Consider partial migration (move files without splitting large ones)

---

## Estimated Time Breakdown

| Task | Estimated Time | Notes |
|------|---------------|-------|
| Task 1: Create structure | 30 min | Straightforward |
| Task 2: Profiler module | 2 hours | Medium complexity |
| Task 3: Market validation | 3 hours | 70KB file requires careful splitting |
| Task 4: Monetization | 2 hours | 63KB file |
| Task 5: Search clients | 1 hour | Consolidation |
| Task 6: Remaining modules | 30 min | Simple moves |
| Task 7: Update imports | 2 hours | Tedious but critical |
| Task 8: Documentation | 30 min | Important |
| **Validation & Buffer** | 2 hours | Testing, fixes |
| **Total** | **13.5 hours** | ~2 work days |

**Recommendation**: Allocate 3 days to account for unexpected issues.

---

## Next Phase

Once this phase is complete and validated:

→ **[Phase 3: Extract Utilities](phase-03-extract-utilities.md)**

Phase 3 will extract standalone utility functions and formatters, building on the clean agent structure we've established.

---

## Notes

- **IDE Support**: Use PyCharm or VSCode refactoring tools to help update imports
- **Git Strategy**: Commit after each task for easy rollback
- **Testing**: Run tests after each major change, not just at the end
- **Backup**: Keep `agent_tools/` directory until Phase 3 completes successfully

**Status**: ⏸️ NOT STARTED  
**Last Updated**: 2025-11-19
