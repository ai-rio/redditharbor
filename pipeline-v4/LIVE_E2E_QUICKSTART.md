# Live E2E Pipeline Test - Quick Start Guide

## What This Is

A **REAL end-to-end integration test** that validates the complete pipeline:
- Real Reddit API → Real LLM → Real Database
- NO mocks, NO fixtures, NO stubs
- Production pipeline verification

## Quick Setup (5 minutes)

### 1. Get Credentials

#### Reddit API (Free)
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" type
4. Name: `RedditHarbor-Test`
5. Redirect URI: `http://localhost:8080`
6. Copy **client_id** (under app name) and **secret**

#### OpenRouter API (Free tier available)
1. Go to https://openrouter.ai/
2. Sign up with GitHub/Google
3. Go to https://openrouter.ai/keys
4. Create new API key
5. Copy the key (starts with `sk-or-v1-...`)

### 2. Configure Environment

```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v4

# Edit .env.local
nano .env.local

# Update these values:
REDDIT_PUBLIC=your_actual_reddit_client_id
REDDIT_SECRET=your_actual_reddit_secret
OPENROUTER_API_KEY=sk-or-v1-your_actual_key_here
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54331/postgres
```

### 3. Start Database

```bash
# If using Docker/Supabase locally
# (Database should already be running for other tests)

# Verify connection
psql postgresql://postgres:postgres@127.0.0.1:54331/postgres -c "SELECT 1"
```

### 4. Run Tests

```bash
# Quick test (Reddit connection only - no LLM calls)
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_reddit_connection -v -s

# Full E2E test (includes LLM calls - costs ~$0.01)
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_pipeline_complete -v -s

# All tests
pytest tests/test_live_e2e_pipeline.py -v -s
```

## Expected Results

### Quick Test (Reddit Connection)
```
============================= test session starts ==============================
tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_reddit_connection

============================================================
TEST: LIVE REDDIT CONNECTION
============================================================

[TEST] Reddit API authentication...
✓ Reddit API authenticated

[TEST] Accessing r/productivity...
✓ Subreddit: r/productivity
  Title: Productivity
  Subscribers: 2,500,000

[TEST] Fetching submissions...
✓ Fetched 2 submissions
  [1] abc123: New productivity app for time tracking...
  [2] def456: How I organize my day using markdown...

============================================================
REDDIT CONNECTION RESULTS
============================================================
✓ Authentication: VERIFIED
✓ Subreddit Access: VERIFIED
✓ Data Fetch: VERIFIED
============================================================

PASSED                                                                [100%]

============================== 1 passed in 6.55s ===============================
```

### Full E2E Test
```
============================= test session starts ==============================
tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_pipeline_complete

============================================================
TEST: LIVE PIPELINE COMPLETE
============================================================

[STAGE 1] Extracting from r/productivity...
✓ Fetched 3 real submissions from Reddit
  [1] abc123: New productivity app for time tracking...
  [2] def456: How I organize my day using markdown...
  [3] ghi789: The best Pomodoro technique explained...
  Time: 1.15s

[STAGE 2] Analyzing with OpenRouter LLM...
  Analyzing submission 1/3: abc123
    ✓ WTP=75.0, Score=68.5, Confidence=80.0
  Analyzing submission 2/3: def456
    ✓ WTP=82.0, Score=71.2, Confidence=85.0
  Analyzing submission 3/3: ghi789
    ✓ WTP=68.0, Score=65.0, Confidence=75.0
✓ Analyzed 3 submissions with LLM
  Time: 12.48s
  Avg per submission: 4.16s

[STAGE 3] Loading to PostgreSQL database...
  Saving analysis 1/3: abc123
    ✓ Saved to database
  Saving analysis 2/3: def456
    ✓ Saved to database
  Saving analysis 3/3: ghi789
    ✓ Saved to database
✓ Saved 3/3 analyses to database
  Time: 2.13s

[VERIFICATION] Querying database...
  ✓ Verified abc123: ID=1, Score=68.5
  ✓ Verified def456: ID=2, Score=71.2
  ✓ Verified ghi789: ID=3, Score=65.0

============================================================
LIVE E2E PIPELINE TEST RESULTS
============================================================
✓ Stage 1 (Extract): 3 submissions (1.15s)
✓ Stage 2 (Transform): 3 analyses (12.48s)
✓ Stage 3 (Load): 3 saved (2.13s)
✓ Total Pipeline Time: 15.76s
✓ Database Integrity: VERIFIED
============================================================

PASSED                                                                [100%]

============================== 1 passed in 18.21s ===============================
```

## Cost Estimate

### OpenRouter Pricing (GPT-4o-mini)
- Model: `openai/gpt-4o-mini`
- Cost: ~$0.003 per submission
- **3 submissions = ~$0.01 total**

### Reddit API
- **FREE** (rate limited to 60 requests/min)

### Database
- **FREE** (local PostgreSQL)

## What Gets Tested

### ✅ Complete Pipeline Flow
1. **Extract**: Fetch real Reddit submissions via PRAW
2. **Transform**: Analyze with OpenRouter LLM (GPT-4o-mini)
3. **Load**: Save to PostgreSQL database
4. **Verify**: Query database to confirm integrity

### ✅ Data Validation
- Score ranges (0-100)
- Required fields present
- JSON structure valid
- Timestamps correct
- Unique constraint enforcement

### ✅ Error Handling
- API authentication
- Rate limiting
- Database constraints
- Duplicate detection

### ✅ Performance
- Pipeline completes in <30s
- LLM analysis time reasonable
- Database writes efficient

## Troubleshooting

### "Credentials contain placeholder values"
**Fix:** Update `.env.local` with real credentials (see Step 2)

### "AuthenticationError: No cookie auth credentials found"
**Fix:** OpenRouter API key is invalid
```bash
# Verify your key
grep OPENROUTER_API_KEY .env.local

# Should start with: sk-or-v1-
```

### "Connection refused" (Database)
**Fix:** Start PostgreSQL
```bash
# Check if running
psql postgresql://postgres:postgres@127.0.0.1:54331/postgres -c "SELECT 1"
```

### "Rate limit exceeded" (Reddit)
**Fix:** Wait 60 seconds, then retry

## Next Steps

After successful test:

1. **View Results in Database**
   ```sql
   psql postgresql://postgres:postgres@127.0.0.1:54331/postgres
   SELECT * FROM opportunities ORDER BY created_at DESC LIMIT 5;
   ```

2. **Run Duplicate Detection Test**
   ```bash
   pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_duplicate_detection -v -s
   ```

3. **Check Database Integrity**
   ```bash
   pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_database_integrity -v -s
   ```

4. **Read Full Documentation**
   ```bash
   cat tests/LIVE_E2E_TEST_README.md
   ```

## Tips

- **Start with Reddit connection test** (no LLM cost)
- **Limit=3 keeps costs low** (~$0.01 per test)
- **Tests keep data in DB** for verification
- **Staging state is cleared** before each test
- **Run cleanup** periodically to remove test data

## Support

- Issues: https://github.com/yourusername/redditharbor/issues
- Documentation: `tests/LIVE_E2E_TEST_README.md`
- Examples: See test output above

---

**Ready to test? Run this now:**
```bash
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_reddit_connection -v -s
```

**Cost: $0.00** (Reddit API is free)
**Time: ~6 seconds**
