# Live E2E Pipeline Integration Test

## Overview

**test_live_e2e_pipeline.py** is a comprehensive end-to-end integration test that validates the COMPLETE pipeline with REAL APIs and database.

**NO MOCKS. NO FIXTURES. REAL PRODUCTION PIPELINE.**

## What It Tests

### 1. Complete Pipeline Flow
- **Extract**: Real Reddit API calls (PRAW)
- **Transform**: Real LLM analysis (OpenRouter)
- **Load**: Real PostgreSQL database writes

### 2. Test Coverage
- `test_live_pipeline_complete()` - Full E2E test
- `test_live_duplicate_detection()` - Deduplication logic
- `test_live_database_integrity()` - Data validation
- `test_live_reddit_connection()` - Reddit API connectivity

## Prerequisites

### 1. Reddit API Credentials
Create Reddit app at https://www.reddit.com/prefs/apps

```bash
# Required credentials
REDDIT_PUBLIC=your_reddit_client_id
REDDIT_SECRET=your_reddit_client_secret
```

### 2. OpenRouter API Key
Get API key at https://openrouter.ai/

```bash
# Required for LLM analysis
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 3. PostgreSQL Database
Ensure database is running:

```bash
# Default connection
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54331/postgres
```

### 4. Configuration File
Update `.env.local` with real credentials:

```bash
# File: pipeline-v4/.env.local
REDDIT_PUBLIC=your_reddit_client_id_here
REDDIT_SECRET=your_reddit_secret_here
OPENROUTER_API_KEY=your_openrouter_key_here
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54331/postgres
```

## Running the Tests

### All Live Tests
```bash
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v4
pytest tests/test_live_e2e_pipeline.py -v -s
```

### Individual Tests

#### 1. Reddit Connection Test (Quick)
```bash
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_reddit_connection -v -s
```

**Expected Output:**
```
=========== LIVE REDDIT CONNECTION ===========
✓ Reddit API authenticated
✓ Subreddit: r/productivity
  Subscribers: 2,500,000
✓ Fetched 2 submissions
==============================================
Test Duration: ~5s
```

#### 2. Complete Pipeline Test (Comprehensive)
```bash
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_pipeline_complete -v -s
```

**Expected Output:**
```
=========== LIVE E2E PIPELINE TEST ===========
[STAGE 1] Extracting from r/productivity...
✓ Fetched 3 real submissions from Reddit
  Time: 1.2s

[STAGE 2] Analyzing with OpenRouter LLM...
  Analyzing submission 1/3: abc123
    ✓ WTP=75.0, Score=68.5, Confidence=80.0
  Analyzing submission 2/3: def456
    ✓ WTP=82.0, Score=71.2, Confidence=85.0
  Analyzing submission 3/3: ghi789
    ✓ WTP=68.0, Score=65.0, Confidence=75.0
✓ Analyzed 3 submissions with LLM
  Time: 12.5s
  Avg per submission: 4.2s

[STAGE 3] Loading to PostgreSQL database...
  Saving analysis 1/3: abc123
    ✓ Saved to database
  Saving analysis 2/3: def456
    ✓ Saved to database
  Saving analysis 3/3: ghi789
    ✓ Saved to database
✓ Saved 3/3 analyses to database
  Time: 2.1s

[VERIFICATION] Querying database...
  ✓ Verified abc123: ID=1, Score=68.5
  ✓ Verified def456: ID=2, Score=71.2
  ✓ Verified ghi789: ID=3, Score=65.0

=========== RESULTS ===========
✓ Stage 1 (Extract): 3 submissions (1.2s)
✓ Stage 2 (Transform): 3 analyses (12.5s)
✓ Stage 3 (Load): 3 saved (2.1s)
✓ Total Pipeline Time: 15.8s
✓ Database Integrity: VERIFIED
===============================
```

#### 3. Duplicate Detection Test
```bash
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_duplicate_detection -v -s
```

**Expected Output:**
```
=========== DUPLICATE DETECTION ===========
[RUN 1] First pipeline execution...
✓ Run 1: Saved 3 analyses

[RUN 2] Second pipeline execution...
⊘ Skipping duplicate: abc123
⊘ Skipping duplicate: def456
⊘ Skipping duplicate: ghi789
✓ Run 2: Saved 0, Skipped 3

=========== RESULTS ===========
✓ First Run: 3 saved
✓ Second Run: 0 saved, 3 skipped
✓ Duplicate Detection: WORKING
===============================
```

#### 4. Database Integrity Test
```bash
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_database_integrity -v -s
```

**Expected Output:**
```
=========== DATABASE INTEGRITY ===========
✓ Found 15 opportunities in database

  [1] abc123: Score=68.5, WTP=75.0, Trust=MEDIUM
  [2] def456: Score=71.2, WTP=82.0, Trust=HIGH
  [3] ghi789: Score=65.0, WTP=68.0, Trust=MEDIUM
  ...

=========== RESULTS ===========
✓ Opportunities Checked: 15
✓ Unique submission_ids: 15
✓ All scores valid: 0.0-100.0 range
✓ All timestamps valid
✓ All JSON fields valid
✓ Database Integrity: VERIFIED
===============================
```

## Test Behavior

### Data Persistence
- Tests intentionally **keep data in database** for verification
- Data is NOT automatically cleaned up
- Run cleanup utility if needed (see below)

### Staging State
- Staging state is **cleared before each test**
- Located in `pipeline_staging/processed.json`
- Ensures clean test runs

### Performance Expectations
- Reddit API: ~1-2s per 3 submissions
- LLM Analysis: ~3-5s per submission (OpenRouter)
- Database Write: <1s per 3 records
- **Total E2E Time: ~15-30s for 3 submissions**

## Troubleshooting

### Test Skipped: "Credentials contain placeholder values"
**Problem:** `.env.local` contains placeholder credentials

**Solution:**
```bash
# Edit .env.local with real credentials
nano .env.local

# Replace placeholders:
REDDIT_PUBLIC=actual_reddit_client_id
REDDIT_SECRET=actual_reddit_secret
OPENROUTER_API_KEY=actual_openrouter_key
```

### AuthenticationError: "No cookie auth credentials found"
**Problem:** OpenRouter API key is invalid or placeholder

**Solution:**
1. Get valid API key from https://openrouter.ai/
2. Update `.env.local`
3. Verify: `grep OPENROUTER_API_KEY .env.local`

### Database Connection Error
**Problem:** PostgreSQL not running or wrong URL

**Solution:**
```bash
# Check if PostgreSQL is running
psql postgresql://postgres:postgres@127.0.0.1:54331/postgres -c "SELECT version()"

# Update DATABASE_URL in .env.local if needed
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:YOUR_PORT/postgres
```

### Reddit API Rate Limiting
**Problem:** Too many requests to Reddit API

**Solution:**
- Reddit allows 60 requests/minute
- Tests use `limit=3` to minimize requests
- Wait 1 minute between test runs if rate limited

## Cleanup

### Clear Staging State
```bash
rm -rf pipeline_staging/processed.json
```

### Clear Test Data (Optional)
```python
# In test file, uncomment cleanup method
def test_cleanup_old_opportunities(self):
    loader = Loader(settings=self.settings)
    opportunities = loader.get_opportunities_by_subreddit("productivity")
    for opp in opportunities:
        loader.delete_opportunity(opp.submission_id)
    loader.close()
```

Then run:
```bash
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_cleanup_old_opportunities -v -s
```

### Manual Database Cleanup
```sql
-- Connect to database
psql postgresql://postgres:postgres@127.0.0.1:54331/postgres

-- Delete test opportunities
DELETE FROM opportunities WHERE subreddit = 'productivity';

-- Verify
SELECT COUNT(*) FROM opportunities;
```

## Performance Metrics

### Expected Timings
| Stage | Operation | Time per Item | Time for 3 Items |
|-------|-----------|---------------|------------------|
| Extract | Reddit API | 0.3-0.5s | 1-2s |
| Transform | LLM Analysis | 3-5s | 9-15s |
| Load | Database Write | 0.2-0.3s | 0.6-1s |
| **Total** | **Complete Pipeline** | **3.5-5.8s** | **10.6-18s** |

### Optimization Notes
- LLM analysis is the bottleneck (~75% of total time)
- Redis caching can reduce duplicate LLM calls
- Batch processing can improve throughput
- Connection pooling reduces database overhead

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Live E2E Tests

on:
  push:
    branches: [ main, develop ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  live-e2e:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 54331:5432

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run Live E2E Tests
        env:
          REDDIT_PUBLIC: ${{ secrets.REDDIT_PUBLIC }}
          REDDIT_SECRET: ${{ secrets.REDDIT_SECRET }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          DATABASE_URL: postgresql://postgres:postgres@localhost:54331/postgres
        run: |
          pytest tests/test_live_e2e_pipeline.py -v -s
```

## Security Notes

### Credentials
- **NEVER commit credentials to git**
- Use `.env.local` (gitignored)
- Store secrets in environment variables
- Use GitHub Secrets for CI/CD

### Data Privacy
- Test data contains real Reddit content
- PII should be anonymized (future enhancement)
- Delete test data regularly
- Follow Reddit API ToS

## Test Development

### Adding New Tests
```python
def test_live_new_feature(self):
    """Test description"""
    # Skip if missing credentials
    if self.settings.llm_api_key == "your_openrouter_api_key_here":
        pytest.skip("Missing credentials")

    # Test implementation
    pipeline = Pipeline(settings=self.settings)
    # ... test logic ...

    pipeline.loader.close()
```

### Best Practices
1. **Always check credentials** before expensive operations
2. **Use small limits** (3 items) for faster tests
3. **Log intermediate results** for debugging
4. **Clean up resources** in finally blocks
5. **Verify data integrity** after writes
6. **Use descriptive assertions** with clear messages

## Related Documentation
- [Pipeline Architecture](../docs/architecture/pipeline-v4.md)
- [Configuration Guide](../docs/guides/configuration.md)
- [Database Schema](../docs/database/schema.md)
- [Testing Strategy](../docs/testing/strategy.md)

## Support
- GitHub Issues: https://github.com/yourusername/redditharbor/issues
- Documentation: https://docs.redditharbor.dev
- Discord: https://discord.gg/redditharbor

---

**Last Updated:** 2025-12-11
**Test Version:** 1.0.0
**Pipeline Version:** v4
