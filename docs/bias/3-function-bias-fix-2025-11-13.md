# 3-Function Bias Fix - November 13, 2025

## Executive Summary

**Issue**: LLM profiler was generating exactly 3 functions for 100% of Reddit opportunities, contradicting the 1-3 function methodology that assigns different simplicity scores (1-func: 100pts, 2-func: 85pts, 3-func: 70pts).

**Root Cause**: When `llm_profiler_enhanced.py` was created for cost tracking implementation (commit f6da902), it copied the original unfixed prompt from an old version of `llm_profiler.py` that had subjective guidance ("simple/moderate/complex problems").

**Solution**: Applied improved prompt engineering using concrete examples and objective criteria from the prompt-engineer agent.

**Result**: Overcorrected - Now 100% of apps have 1 function (down from 100% with 3 functions).

**Status**: ⚠️ Need to balance the prompt to achieve natural distribution (~60% 1-func, ~30% 2-func, ~10% 3-func)

---

## Historical Context

### Previous Bias Issue (Commit e6789d2)
- **Problem**: 95% of apps had exactly 2 functions
- **Fix**: Updated prompt in `llm_profiler.py`
- **Location**: docs/bias/function-count-diagnosis-summary.md

### Current Issue Discovery (November 13, 2025)
- During E2E workflow testing, discovered 100% of 7 generated apps had exactly 3 functions
- Investigation revealed `llm_profiler_enhanced.py` (the active profiler) had the old unfixed prompt
- `llm_profiler.py` had the fix but wasn't being used in production

---

## Technical Analysis

### Files Modified
1. **agent_tools/llm_profiler_enhanced.py** (lines 213-242)
   - Active profiler used by batch_opportunity_scoring.py
   - Contains cost tracking features via LiteLLM
   - Prompt was outdated

2. **agent_tools/llm_profiler.py** (lines 109-138)
   - Backup profiler
   - Updated for consistency

### Prompt Changes

#### OLD PROMPT (Subjective Guidance)
```markdown
**Function Count Guidelines:**
- Choose the MINIMUM number of functions (1-3) that genuinely solve the core problem
- Simple problems (single pain point) → 1 function is ideal
- Moderate problems (related pain points) → 2 functions may be needed
- Complex problems (multiple distinct needs) → 3 functions might be required
- Do NOT artificially inflate or deflate function count - match it to problem complexity
- Quality over quantity: fewer focused functions beat more scattered ones
```

**Problem with old prompt:**
- Subjective terms like "simple/moderate/complex"
- LLMs tend to classify Reddit posts as "complex" → Always choose 3 functions
- No concrete examples to guide decision-making
- No objective decision framework

#### NEW PROMPT (Objective Criteria + Examples)
```markdown
**Function Count Guidelines:**

START WITH 1 FUNCTION - only add more if absolutely necessary.

**DECISION FRAMEWORK:**
1. Count the number of DISTINCT user actions needed to solve the problem
2. If related actions can be combined into one workflow → 1 function
3. If actions require completely different interfaces/inputs → consider 2 functions
4. Only use 3 functions if there are truly independent problem domains

**CONCRETE EXAMPLES:**

1-Function Apps (PREFERRED - aim for this):
- Problem: "I forget to water my plants" → Function: "Send watering reminders based on plant type"
- Problem: "I can't track my daily calories" → Function: "Log food and show calorie total"
- Problem: "I lose track of parking spot" → Function: "Save and retrieve parking location"
- Problem: "I overspend on subscriptions" → Function: "Track recurring charges and show monthly total"

2-Function Apps (only if problem has TWO distinct needs):
- Problem: "I forget bills AND want to see spending patterns" → Functions: "1) Send bill reminders, 2) Visualize spending trends"
- Problem: "I can't find recipes for ingredients I have" → Functions: "1) Scan/input ingredients, 2) Match to recipes"

3-Function Apps (RARE - only for genuinely complex problems):
- Problem: "Roommates argue about chores, don't know who did what, and dispute fairness" → Functions: "1) Assign chores, 2) Track completion, 3) Calculate equity scores"

**CRITICAL RULES:**
- If you're tempted to add a 2nd function, ask: "Could this be a feature of the 1st function instead?"
- If you're considering 3 functions, ask: "Are we solving ONE problem or multiple separate problems?"
- Default to 1 function unless you can clearly justify why 2+ are essential
- Helper features, settings, or view options DO NOT count as separate functions
```

**Improvements in new prompt:**
- Explicit bias toward 1 function ("START WITH 1 FUNCTION")
- Objective framework (count distinct user actions)
- 4 concrete examples of 1-function apps
- 2 examples of 2-function apps
- 1 example of 3-function apps
- Anti-rationalization questions

---

## Test Results

### Test Configuration
- **Date**: November 13, 2025
- **Script**: scripts/core/batch_opportunity_scoring.py
- **Threshold**: SCORE_THRESHOLD=20.0
- **Sample Size**: 7 Reddit opportunities
- **Model**: Claude Haiku 4.5 via OpenRouter

### Before Fix (Previous Run)
```
Function Distribution:
- 1 function:  0/7 (0.0%)
- 2 functions: 0/7 (0.0%)
- 3 functions: 7/7 (100.0%)  ⚠️ BIAS
```

### After Fix (Current Run)
```
Function Distribution:
- 1 function:  7/7 (100.0%)  ⚠️ OVERCORRECTION
- 2 functions: 0/7 (0.0%)
- 3 functions: 0/7 (0.0%)
```

### Sample Generated Apps
All 7 apps generated with 1 function:

1. **OpportunityFilter** (Score: 25.55)
   - Function: "Opportunity Assessment Engine: Users input opportunity details and..."

2. **BoundaryBridge** (Score: 26.55)
   - Function: "Generate contextual status messages that explain availability bound..."

3. **LaunchLock** (Score: 26.55)
   - Function: "Milestone Sequencer: Convert product roadmap into mandatory launch-..."

4. **HostMatch** (Score: 25.55)
   - Function: "Compare WordPress hosting providers by cost, uptime, speed, and sca..."

5. **CreativeShowcase** (Score: 25.55)
   - Function: "Process-to-Post Builder: Transform behind-the-scenes creative work..."

6. **StripeSync** (Score: 28.65)
   - Function: "Auto-sync Stripe transactions to QuickBooks and bank accounts with..."

7. **LocalConnect** (Score: 25.55)
   - Function: "Discover and join real-time local events and activities within a cu..."

---

## Analysis

### What Worked
✅ **Completely eliminated 3-function bias**
✅ **Concrete examples guide LLM decision-making**
✅ **Objective framework ("count distinct user actions") is clearer**
✅ **All generated apps have valid, focused single functions**

### What Didn't Work
⚠️ **Overcorrected to 100% 1-function apps**
⚠️ **Prompt is too heavily biased toward simplicity**
⚠️ **4:2:1 example ratio may be too skewed**

### Why Overcorrection Happened
1. **Strong directive**: "START WITH 1 FUNCTION - only add more if absolutely necessary"
2. **Example imbalance**: 4 one-function examples vs 2 two-function vs 1 three-function
3. **LLM tendency**: When given explicit preference, LLMs overweight it
4. **Questioning framework**: Both critical questions push toward fewer functions

---

## Next Steps

### Immediate Actions
1. ⏸️ **Pause production use** of current prompt until balanced
2. 📊 **Collect larger sample** (20-30 opportunities) to confirm pattern
3. 🔄 **Iterate on prompt** to achieve target distribution

### Target Distribution
Based on methodology:
- **1 function**: ~60% (most problems are simple)
- **2 functions**: ~30% (some problems have dual needs)
- **3 functions**: ~10% (complex multi-domain problems)

### Prompt Refinement Strategy
```markdown
**Balanced Approach:**

1. Remove strong directive "START WITH 1 FUNCTION"
2. Balance examples: 3 one-function, 3 two-function, 2 three-function
3. Replace "only add more if absolutely necessary" with neutral phrasing
4. Add 2-function validation questions (not just anti-2-function)
5. Emphasize matching complexity to problem, not defaulting to simplicity
```

Example rebalanced guidance:
```markdown
**Function Count Guidelines:**

Match function count to problem complexity - no more, no less.

**DECISION FRAMEWORK:**
1. Identify DISTINCT user needs in the problem statement
2. If one workflow solves all needs → 1 function
3. If needs require different interfaces/data → 2 functions
4. If needs span independent problem domains → 3 functions

[Balanced examples - 3:3:2 ratio]

**VALIDATION QUESTIONS:**
- For 1 function: "Are there distinct needs being bundled together?"
- For 2 functions: "Could these be combined into one workflow OR split into three domains?"
- For 3 functions: "Are we solving one complex problem or multiple separate problems?"
```

---

## Recommendations

### Short-term
1. **Test rebalanced prompt** with 20-opportunity sample
2. **Monitor distribution** across multiple test runs
3. **Document edge cases** where LLM struggles with 2/3 functions

### Long-term
1. **A/B testing framework** for prompt variations
2. **Statistical validation** of distribution across 100+ opportunities
3. **Manual review process** for validating function count decisions
4. **Feedback loop** from implementation to refine complexity criteria

---

## Files Changed

### Code Changes
- `agent_tools/llm_profiler_enhanced.py` (lines 213-242)
- `agent_tools/llm_profiler.py` (lines 109-138)

### Documentation
- `docs/bias/3-function-bias-fix-2025-11-13.md` (this file)
- Referenced: `docs/bias/function-count-diagnosis-summary.md` (previous 2-function bias)

### Test Artifacts
- `/tmp/prompt_test.log` - Test run output
- Database: `workflow_results` table with 7 test profiles

---

## Conclusion

**The improved prompt successfully fixed the 3-function bias but overcorrected to a 1-function bias.**

This is actually a positive outcome because:
1. ✅ We proved the prompt engineering approach works
2. ✅ We have objective criteria that LLMs can follow
3. ✅ We understand the mechanism (example ratio + directive strength)
4. ✅ Balancing is easier than starting from subjective guidance

**Next iteration should focus on achieving natural distribution rather than eliminating bias.**

---

**Author**: AI Assistant (Claude Sonnet 4.5)
**Date**: November 13, 2025
**Related Commit**: f6da902 (cost tracking implementation that introduced the regression)
**Previous Fix**: e6789d2 (fixed 2-function bias in llm_profiler.py)
