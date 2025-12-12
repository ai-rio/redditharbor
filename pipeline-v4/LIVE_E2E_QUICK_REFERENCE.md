# Live E2E Test - Quick Reference Card

## 🚀 Quick Start (30 seconds)

```bash
# 1. Navigate to pipeline-v4
cd /home/carlos/projects/redditharbor-core-functions-fix/pipeline-v4

# 2. Run quick test (FREE - no LLM)
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_reddit_connection -v -s

# 3. Run full E2E test (~$0.01)
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_pipeline_complete -v -s
```

## 📋 Prerequisites

### Required Credentials
```bash
# Edit .env.local
REDDIT_PUBLIC=your_reddit_client_id
REDDIT_SECRET=your_reddit_client_secret
OPENROUTER_API_KEY=sk-or-v1-your_key_here
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54331/postgres
```

### Get Credentials
- **Reddit**: https://www.reddit.com/prefs/apps (FREE)
- **OpenRouter**: https://openrouter.ai/keys (FREE tier)
- **Database**: Local PostgreSQL (FREE)

## 🧪 Test Commands

### Individual Tests
```bash
# Reddit API test (6s, $0.00)
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_reddit_connection -v -s

# Full E2E pipeline (15-20s, ~$0.01)
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_pipeline_complete -v -s

# Duplicate detection (20-25s, ~$0.01)
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_duplicate_detection -v -s

# Database integrity (2s, $0.00)
pytest tests/test_live_e2e_pipeline.py::TestLiveE2EPipeline::test_live_database_integrity -v -s
```

### All Tests
```bash
# Run all tests (45s, ~$0.02)
pytest tests/test_live_e2e_pipeline.py -v -s

# Run without verbose output
pytest tests/test_live_e2e_pipeline.py -v
```

## ✅ Expected Results

### Quick Test (Reddit Connection)
```
============================================================
TEST: LIVE REDDIT CONNECTION
✓ Reddit API authenticated
✓ Subreddit: r/productivity (2,500,000 subscribers)
✓ Fetched 2 submissions
============================================================
PASSED in 6.55s
```

### Full E2E Test
```
============================================================
TEST: LIVE PIPELINE COMPLETE
✓ Stage 1 (Extract): 3 submissions (1.15s)
✓ Stage 2 (Transform): 3 analyses (12.48s)
✓ Stage 3 (Load): 3 saved (2.13s)
✓ Total Pipeline Time: 15.76s
✓ Database Integrity: VERIFIED
============================================================
PASSED in 18.21s
```

## 🔧 Troubleshooting

| Error | Fix |
|-------|-----|
| "Credentials contain placeholder values" | Update `.env.local` with real credentials |
| "AuthenticationError" | Check OpenRouter API key (starts with `sk-or-v1-`) |
| "Connection refused" | Start PostgreSQL: `psql $DATABASE_URL -c "SELECT 1"` |
| "Rate limit exceeded" | Wait 60 seconds (Reddit: 60 req/min) |

## 📊 Performance

| Test | Duration | Cost |
|------|----------|------|
| Reddit Connection | 6s | $0.00 |
| Database Integrity | 2s | $0.00 |
| Full E2E Pipeline | 15-20s | $0.01 |
| Duplicate Detection | 20-25s | $0.01 |
| **All Tests** | **45s** | **$0.02** |

## 📚 Documentation

| File | Purpose |
|------|---------|
| `tests/test_live_e2e_pipeline.py` | Test suite (450+ lines) |
| `tests/LIVE_E2E_TEST_README.md` | Comprehensive docs (400+ lines) |
| `LIVE_E2E_QUICKSTART.md` | 5-minute setup guide (250+ lines) |
| `LIVE_E2E_TEST_EXECUTION_SUMMARY.md` | Execution results (450+ lines) |
| `LIVE_E2E_DELIVERABLES.md` | Complete summary |
| `LIVE_E2E_QUICK_REFERENCE.md` | This quick reference |

## 🎯 What Gets Tested

- ✅ Real Reddit API (PRAW authentication, data fetch)
- ✅ Real LLM Analysis (OpenRouter GPT-4o-mini)
- ✅ Real PostgreSQL Database (write, read, constraints)
- ✅ Duplicate Detection (staging layer, deduplication)
- ✅ Data Integrity (scores, timestamps, JSON structure)
- ✅ Error Handling (API errors, database errors)
- ✅ Performance (timing, bottlenecks)

## 💾 Database Verification

```bash
# Connect to database
psql postgresql://postgres:postgres@127.0.0.1:54331/postgres

# View test results
SELECT
    submission_id,
    subreddit,
    title,
    wtp_score,
    final_score,
    trust_level,
    created_at
FROM opportunities
WHERE subreddit = 'productivity'
ORDER BY created_at DESC
LIMIT 10;
```

## 🧹 Cleanup

```bash
# Clear staging state
rm -rf pipeline_staging/processed.json

# Clear test data (SQL)
psql $DATABASE_URL -c "DELETE FROM opportunities WHERE subreddit = 'productivity';"
```

## 📈 Cost Breakdown

### Per Test Run
- Reddit API: $0.00 (FREE)
- OpenRouter (3 items): ~$0.01
- Database: $0.00 (local)
- **Total: ~$0.01**

### Monthly (Daily CI/CD)
- Daily runs: 30
- Cost per run: $0.01
- **Monthly total: ~$0.30**

## 🔗 Quick Links

- Reddit Apps: https://www.reddit.com/prefs/apps
- OpenRouter Keys: https://openrouter.ai/keys
- Full Docs: `tests/LIVE_E2E_TEST_README.md`
- Quick Start: `LIVE_E2E_QUICKSTART.md`

---

**Last Updated:** 2025-12-11
**Version:** 1.0.0
**Status:** ✅ READY
