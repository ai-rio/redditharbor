# Phase 2 Local AI Testing Prompt

**Phase**: 2 - Agent Tools Restructuring
**Date**: 2025-11-19
**Branch**: `claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq`
**Commit**: `e1a63e6`
**Status**: Ready for local validation

---

## Context

Phase 2 restructured the flat `agent_tools/` directory into a modular `core/agents/` architecture with 5 logical groups:

- `core/agents/profiler/` - AI profiling agents
- `core/agents/monetization/` - Monetization analysis
- `core/agents/market_validation/` - Market validation
- `core/agents/search/` - Jina search clients
- `core/agents/interactive/` - Interactive analysis

**What Changed**:
- ✅ 23 files created in new core/agents/ structure
- ✅ 10,166 lines of code added
- ✅ Production scripts updated with new import paths
- ✅ Original agent_tools/ preserved as backup

---

## Your Task

Validate that Phase 2 restructuring works correctly in the local environment by:

1. Testing that new imports work
2. Verifying module structure is correct
3. Checking that production scripts can be imported (not executed)
4. Validating __init__.py exports
5. Reporting any issues found

---

## Step-by-Step Testing Instructions

### Step 1: Pull Latest Changes

```bash
git fetch origin
git checkout claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
git pull
```

**Expected**: Successfully pulled commit `e1a63e6` or later

---

### Step 2: Verify Module Structure

```bash
# Check that all directories were created
find core/agents -type d | sort
```

**Expected Output**:
```
core/agents
core/agents/interactive
core/agents/market_validation
core/agents/monetization
core/agents/profiler
core/agents/search
```

**Expected**: 6 directories total

---

### Step 3: Verify __init__.py Files

```bash
# Count __init__.py files
find core/agents -name "__init__.py" | wc -l
```

**Expected**: 6 __init__.py files (one per directory)

```bash
# List all __init__.py files
find core/agents -name "__init__.py" | sort
```

**Expected Output**:
```
core/agents/__init__.py
core/agents/interactive/__init__.py
core/agents/market_validation/__init__.py
core/agents/monetization/__init__.py
core/agents/profiler/__init__.py
core/agents/search/__init__.py
```

---

### Step 4: Test Module Imports

**Test 1: Profiler Module**

```bash
python -c "from core.agents.profiler import EnhancedLLMProfiler, BaseLLMProfiler; print('✅ Profiler imports work')"
```

**Expected**: `✅ Profiler imports work` (no ImportError)

**Test 2: Monetization Module**

```bash
python -c "from core.agents.monetization import MonetizationAnalysis, MonetizationAnalyzerFactory; print('✅ Monetization imports work')"
```

**Expected**: `✅ Monetization imports work`

**Test 3: Market Validation Module**

```bash
python -c "from core.agents.market_validation import MarketDataValidator; print('✅ Market validation imports work')"
```

**Expected**: `✅ Market validation imports work`

**Test 4: Search Module**

```bash
python -c "from core.agents.search import JinaHybridClient, JinaReaderClient; print('✅ Search clients import work')"
```

**Expected**: `✅ Search clients import work`

**Test 5: Interactive Module**

```bash
python -c "from core.agents.interactive import OpportunityAnalyzerAgent, InteractiveAnalyzer; print('✅ Interactive imports work')"
```

**Expected**: `✅ Interactive imports work`

**Test 6: Central Exports**

```bash
python -c "from core.agents import EnhancedLLMProfiler, MonetizationAnalysis, MarketDataValidator; print('✅ Central exports work')"
```

**Expected**: `✅ Central exports work`

---

### Step 5: Verify Production Scripts Can Be Imported

**IMPORTANT**: Do NOT execute these scripts (they may require credentials). Only test that imports work.

**Test 1: Batch Opportunity Scoring Script**

```bash
python -c "
import sys
from pathlib import Path
project_root = Path('.').resolve()
sys.path.insert(0, str(project_root))

# Test imports only (don't execute)
try:
    import scripts.core.batch_opportunity_scoring as batch_script
    print('✅ batch_opportunity_scoring.py imports successfully')
except Exception as e:
    print(f'❌ Import failed: {e}')
" 2>&1 | grep -E "(✅|❌)"
```

**Expected**: `✅ batch_opportunity_scoring.py imports successfully`

**Test 2: DLT Trust Pipeline Script**

```bash
python -c "
import sys
from pathlib import Path
project_root = Path('.').resolve()
sys.path.insert(0, str(project_root))

# Test imports only (don't execute)
try:
    import scripts.dlt.dlt_trust_pipeline as dlt_script
    print('✅ dlt_trust_pipeline.py imports successfully')
except Exception as e:
    print(f'❌ Import failed: {e}')
" 2>&1 | grep -E "(✅|❌)"
```

**Expected**: `✅ dlt_trust_pipeline.py imports successfully`

---

### Step 6: Check File Sizes

```bash
# List largest files in core/agents
find core/agents -name "*.py" -type f -exec ls -lh {} \; | awk '{print $5, $9}' | sort -hr | head -10
```

**Expected**: Files similar to these sizes:
- `validator.py` - ~69KB
- `agno_analyzer.py` - ~62KB
- `enhanced_profiler.py` - ~37KB
- `hybrid_client.py` - ~30KB

---

### Step 7: Verify Backup Exists

```bash
# Check that original agent_tools/ still exists
ls -la agent_tools/ | head -10
```

**Expected**: Original `agent_tools/` directory should still exist with all original files intact.

---

## Expected Test Summary

After completing all steps, you should have:

✅ **Module Structure**: 6 directories created
✅ **Init Files**: 6 __init__.py files present
✅ **Profiler Imports**: Working
✅ **Monetization Imports**: Working
✅ **Market Validation Imports**: Working
✅ **Search Imports**: Working
✅ **Interactive Imports**: Working
✅ **Central Exports**: Working
✅ **Production Scripts**: Can be imported (not executed)
✅ **Backup**: Original agent_tools/ preserved

**Total Tests**: 9 test categories

---

## What to Report Back

Please create a report at:
```
docs/plans/unified-pipeline-refactoring/local-ai-report/phase-2-testing-report.md
```

### Report Structure

```markdown
# Phase 2 Testing Report - Local AI Validation

**Date**: [current date]
**Branch**: claude/pull-the-chan-01VHHaDftgWXe82ENhr3nauq
**Commit**: [actual commit hash]
**Tester**: Local AI Agent

## Executive Summary

[PASS/FAIL status with brief explanation]

## Test Results

### Module Structure
- [ ] 6 directories created: [PASS/FAIL]
- [ ] 6 __init__.py files present: [PASS/FAIL]

### Import Tests
- [ ] Profiler imports: [PASS/FAIL]
- [ ] Monetization imports: [PASS/FAIL]
- [ ] Market validation imports: [PASS/FAIL]
- [ ] Search imports: [PASS/FAIL]
- [ ] Interactive imports: [PASS/FAIL]
- [ ] Central exports: [PASS/FAIL]

### Production Scripts
- [ ] batch_opportunity_scoring.py: [PASS/FAIL]
- [ ] dlt_trust_pipeline.py: [PASS/FAIL]

### Backup Verification
- [ ] agent_tools/ preserved: [PASS/FAIL]

## Issues Found

[List any issues encountered, or write "None" if all tests passed]

## Recommendations

[Your recommendation: PASS (proceed to Phase 3) or FAIL (needs fixes)]
```

---

## Common Issues and Solutions

### Issue 1: ImportError - Module not found

**Symptom**: `ModuleNotFoundError: No module named 'core.agents.X'`

**Cause**: Project root not in Python path

**Solution**:
```bash
# Add project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Issue 2: Circular import errors

**Symptom**: `ImportError: cannot import name 'X' from partially initialized module`

**Cause**: Circular dependencies in module imports

**Solution**: Report this issue - it's a code problem that needs fixing.

### Issue 3: Missing dependencies

**Symptom**: `ModuleNotFoundError: No module named 'litellm'` or similar

**Cause**: Project dependencies not installed

**Solution**: This is expected - just report that imports structurally work but dependencies are missing.

---

## Notes

- **DO NOT** execute production scripts (they require credentials and database access)
- **DO** test that imports work structurally
- **DO** report any ImportError or ModuleNotFoundError
- **DO** verify the file structure is correct
- **DO NOT** modify any code during testing

---

## Success Criteria

Phase 2 is considered **PASSED** if:

1. ✅ All 6 directories exist
2. ✅ All 6 __init__.py files present
3. ✅ All import tests pass (or fail only due to missing dependencies, not structure issues)
4. ✅ Production scripts can be imported
5. ✅ Original agent_tools/ backup exists

---

## After Testing

Once you've completed testing and generated your report:

1. Commit your report to the repo
2. Notify the team of results
3. If all tests pass, Phase 2 is validated and Phase 3 can begin
4. If tests fail, work with remote team to fix issues

---

**Testing Priority**: 🔴 HIGH - Phase 2 restructures core agent imports used by production scripts

**Estimated Testing Time**: 10-15 minutes

**Last Updated**: 2025-11-19
