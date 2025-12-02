# Live Testing Quick Start

## ⚡ One-Line Summary
Run 4 slash commands sequentially to validate RedditHarbor with real Reddit data (~5 hours total).

## 🚀 Execute Testing

```bash
# Phase 1: Smoke Test (30 min)
/live-test-phase1-smoke

# ✅ Review: docs/live-test/reports/phase1/smoke-test-report.md

# Phase 2: Business Value (1 hour)
/live-test-phase2-business

# ✅ Review: docs/live-test/reports/phase2/business-validation-report.md

# Phase 3: Volume Test (45 min)
/live-test-phase3-volume

# ✅ Review: docs/live-test/reports/phase3/performance-report.md

# Phase 4: Deep Validation (2-3 hours)
/live-test-phase4-validation

# ✅ Review: docs/live-test/reports/phase4/production-readiness-report.md
```

## 📊 Success Criteria

| Metric | Target | Where to Check |
|--------|--------|----------------|
| Pipeline success | >95% | Phase 3 performance report |
| Error rate | <5% | Phase 3 performance report |
| High-quality opps | ≥5 (>70 score) | Phase 2 business report |
| Correlation | >0.7 | Phase 4 validation report |
| Processing speed | <10 min/100 posts | Phase 3 performance report |

## 🎯 What Each Phase Does

- **Phase 1**: Basic smoke test (10 posts) - "Does it work?"
- **Phase 2**: Business validation (25 posts) - "Are opportunities real?"
- **Phase 3**: Performance test (100 posts) - "Can it scale?"
- **Phase 4**: Deep validation (50 posts) - "Ready for production?"

## 📁 Where Reports Go

```
docs/live-test/
├── PROGRESS.md                    ← Track overall progress here
├── reports/
│   ├── phase1/                   ← Phase 1 results
│   ├── phase2/                   ← Phase 2 results
│   ├── phase3/                   ← Phase 3 results
│   └── phase4/                   ← Final production readiness
└── workspaces/                    ← Temporary files (auto-created)
```

## ✅ After Testing

**If all phases pass**:
1. Review `docs/live-test/reports/phase4/production-readiness-report.md`
2. Check top 3 opportunities for development
3. Proceed to production deployment

**If any phase fails**:
1. Check `docs/live-test/PROGRESS.md` for details
2. Fix identified issues
3. Re-run failed phase

## 🔗 Full Documentation

- Detailed guide: `docs/live-test/README.md`
- Framework: `docs/live-test/live-testing-framework.md`
- Progress tracking: `docs/live-test/PROGRESS.md`
