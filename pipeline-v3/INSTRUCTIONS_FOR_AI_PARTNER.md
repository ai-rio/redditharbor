# Instructions for AI Partner: Fix LLM Integration and Run Live Test

**Date:** December 2, 2025
**Status:** Pipeline is 95% functional. One blocker remains.

---

## Current Situation

✅ **Working:**
- Reddit API extraction (PRAW client)
- Database connection (Supabase)
- Staging layer (deduplication)
- Configuration (all credentials valid)
- CLI interface (`main.py`)

❌ **Blocked:**
- LLM analysis step fails due to Instructor/OpenRouter incompatibility

---

## The TWO Issues to Fix

### Issue #1: LLM Integration (May Already Be Fixed)

**Error:** `"Instructor does not support multiple tool calls, use List[Model] instead"`

**Location:** `transform/analyzer.py` or `transform/analyzer_factory.py`

**Root Cause:** The Instructor library configuration is incompatible with OpenRouter's response format for model `meta-llama/llama-3.1-8b-instruct:floor`

**Status Check:** Run the pipeline first. If it completes without LLM errors, this is already fixed.

### Issue #2: Database Storage is a Stub (CRITICAL)

**Problem:** Pipeline runs successfully but database stays at 0 opportunities

**Location:** `load/onlymaps_database.py` line ~177-183

**Root Cause:** The `store_analyses()` method is a stub that returns mock statistics without actually writing to the database

**Evidence:**
```python
def store_analyses(self, analyses: List[AnalysisResult]) -> Dict[str, int]:
    """For now, return mock storage stats"""  # ← STUB!
    return {
        "stored": len(analyses),  # Lies - nothing stored
        "skipped": 0,
        "errors": 0
    }
```

**This MUST be replaced with actual database INSERT operations.**

---

## Fix Options for Issue #1 (LLM Integration)

### Option 1: Switch to OpenAI (Recommended - Fastest)

**If OpenAI API key is available in `.env.local`:**

1. Check if `OPENAI_API_KEY` exists:
   ```bash
   grep OPENAI_API_KEY ../.env.local
   ```

2. If yes, update `config/settings.py` to use OpenAI instead of OpenRouter:
   - Find where model/provider is configured
   - Change from OpenRouter to OpenAI
   - Use model: `gpt-4o-mini` (cheap, fast, compatible)

3. Test immediately (see Step 3 below)

---

### Option 2: Fix Instructor Configuration for OpenRouter

**Modify the Instructor client initialization:**

Location: `transform/analyzer.py` or wherever Instructor is initialized

Change from:
```python
client = instructor.patch(openai.OpenAI(...))
```

To:
```python
client = instructor.from_openai(
    openai.OpenAI(...),
    mode=instructor.Mode.JSON  # or Mode.TOOLS
)
```

**Or** try wrapping the response model in a List:
```python
response = client.chat.completions.create(
    response_model=List[AppIdea],  # Instead of just AppIdea
    ...
)
```

---

### Option 3: Use Different OpenRouter Model

Edit: `config/settings.py` or `.env.local`

Change model from:
```
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:floor
```

To a more compatible model:
```
OPENROUTER_MODEL=openai/gpt-4o-mini
```
or
```
OPENROUTER_MODEL=anthropic/claude-3-haiku
```

---

## Fix for Issue #2: Replace Database Storage Stub

**READ first:**
```bash
Read: load/onlymaps_database.py (line 150-200)
Read: models/database.py (Opportunity model)
```

**IMPLEMENT actual storage:**

The stub needs to be replaced with code that:
1. Converts `AnalysisResult` to `Opportunity` database model
2. Actually inserts into PostgreSQL via SQLAlchemy
3. Commits the transaction
4. Handles errors with rollback

**Check if there's already a data mapper:**
```bash
Grep: "AnalysisToOpportunity" load/
```

If a mapper exists, use it. If not, implement the conversion inline.

**Required fields mapping (from previous schema fixes):**
- `reddit_upvotes` ← analysis.reddit_data.upvotes
- `analyzed_at` ← analysis.analyzed_at
- `trust_level` ← analysis.trust_level
- `submission_id` ← analysis.submission_id
- Plus all other Opportunity model fields

---

## Step-by-Step Instructions

### Step 1: Check What's Already Fixed

**Run the pipeline first to see current state:**
```bash
uv run python main.py --limit 5 --subreddits productivity
```

**If it fails with LLM error:** Implement Issue #1 fix (LLM integration)
**If it completes successfully:** Check database

```bash
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  -c "SELECT COUNT(*) FROM app_opportunities;"
```

**If count = 0:** Issue #2 (storage stub) needs fixing

### Step 2: Implement Required Fixes

**For Issue #1 (LLM Integration):** Choose option below

**READ these files to understand current implementation:**
```bash
Read: config/settings.py
Read: transform/analyzer.py
Read: transform/analyzer_factory.py
```

**EDIT only what's needed** to implement your chosen fix option.

**DO NOT:**
- Create new files
- Write test scripts
- Add documentation
- Refactor unrelated code

---

**For Issue #2 (Storage Stub):** Implement actual database writes in `load/onlymaps_database.py`

### Step 3: Clean Up Clutter (Optional but Recommended)

Remove the 13 unnecessary files from previous testing theater:

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3

rm -f BUSINESS_READINESS_CERTIFICATE.md \
      FINAL_SOLUTION_SUMMARY.md \
      PIPELINE_READINESS_REPORT.md \
      SCHEMA_FIX_SUMMARY.md \
      schema_fix_verification_report.md \
      apply_direct_schema_fix.py \
      fix_schema_mismatch.py \
      test_pipeline_readiness.py \
      test_real_pipeline.py \
      test_schema_fix.py \
      verify_business_readiness.py \
      verify_db_schema.py \
      run_pipeline_now.py
```

---

### Step 4: Live Test (CRITICAL - Must Complete)

**Run the pipeline with 5 real Reddit posts:**

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3

uv run python main.py \
  --limit 5 \
  --subreddits productivity \
  --log-level INFO
```

**Expected output if successful:**
```
✓ Analyzed 5 submissions
✓ Quality filtering complete
✓ Store: 5 stored (or similar number)
Database Statistics:
  - Total opportunities: 5 (or similar number)
```

---

### Step 5: Verify Success

**Check database for actual opportunities:**

```bash
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres \
  -c "SELECT COUNT(*) as opportunities FROM app_opportunities;"
```

**Expected result:** `opportunities > 0` (at least 1, ideally 3-5)

---

### Step 6: Report Results

**If successful (opportunities > 0):**

Create a simple success report:
```
PIPELINE LIVE TEST - SUCCESS

Date: [current date]
Opportunities generated: [number]
Command: uv run python main.py --limit 5 --subreddits productivity
Fix applied: [which option you used]

Pipeline is NOW achieving its core business goal.
```

**If still failing:**

Report the NEW error:
```
PIPELINE LIVE TEST - FAILED

Date: [current date]
Fix attempted: [which option]
New error: [exact error message]
Location: [where it failed]

Next steps: [your recommendation]
```

---

## Success Criteria

**The pipeline achieves its core goal when:**
- ✅ `uv run python main.py --limit 5 --subreddits productivity` completes without errors
- ✅ Database query shows `opportunities > 0` **← THIS IS CRITICAL**
- ✅ Log shows "✓ Store: X stored" where X > 0

**IMPORTANT:** The database count MUST be > 0. If the pipeline runs without errors but database stays at 0, the storage layer is likely a stub/mock that needs real implementation.

**Check for stub code in `load/onlymaps_database.py` around line 177:**
```python
# BAD - This is a stub:
def store_analyses(...):
    return {"stored": len(analyses), ...}  # No actual DB write!

# GOOD - This actually writes:
def store_analyses(...):
    for analysis in analyses:
        self.session.add(...)
        self.session.commit()
```

**That's it. Nothing else matters.**

---

## What NOT to Do

❌ Don't write new test scripts
❌ Don't create comprehensive test suites
❌ Don't refactor unrelated code
❌ Don't write documentation
❌ Don't create readiness reports
❌ Don't run the full test suite (150 failing tests are irrelevant)
❌ Don't create new abstractions
❌ Don't implement error handling improvements

**ONLY:** Fix the LLM integration, run live test, verify database has opportunities.

---

## Context You Need

**Working directory:**
```
/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3
```

**Main entry point:**
```
main.py (has CLI with --help)
```

**Environment file:**
```
../.env.local (in parent directory)
```

**Database:**
```
postgresql://postgres:postgres@127.0.0.1:54322/postgres
Table: app_opportunities
```

**Credentials (all verified working):**
- Reddit: `REDDIT_PUBLIC`, `REDDIT_SECRET` (in .env.local)
- OpenRouter: `OPENROUTER_API_KEY` (in .env.local)
- OpenAI: Check if `OPENAI_API_KEY` exists in .env.local

---

## Final Notes

This is **NOT** a research project. This is **NOT** a refactoring exercise.

This is: **Change 1 configuration → Run 1 command → Verify 1 number > 0**

That's the entire scope. Good luck.

---

## Questions to Answer Before Starting

1. Does `.env.local` have `OPENAI_API_KEY`? (If yes, use Option 1)
2. If no, which fix option will you use? (2 or 3)
3. What file(s) will you edit? (Read them first)

**Then:** Make the change, run the test, check the database, report back.

End of instructions.
