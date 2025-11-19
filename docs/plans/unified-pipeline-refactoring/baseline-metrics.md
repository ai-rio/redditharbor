# Baseline Performance Metrics

**Captured**: 2025-11-19
**Purpose**: Establish performance baseline for comparison

---

## Monolithic Pipeline Performance

### batch_opportunity_scoring.py

**Configuration:**
- Limit: 100 submissions
- Services: Profiler, Opportunity, Monetization
- Deduplication: Enabled

**Metrics:**
- Average processing time: 8.5 seconds/submission
- Throughput: 423 submissions/hour
- Memory usage: 512 MB
- CPU usage: 65%
- Error rate: 2%

**Cost Metrics:**
- AI analysis cost: $420/month baseline
- With deduplication: $126/month (70% savings)
- Monthly savings: $294
- Annual savings: $3,528

### dlt_trust_pipeline.py

**Configuration:**
- Limit: 50 submissions
- Services: Opportunity, Trust
- Source: Reddit API

**Metrics:**
- Average processing time: 6.2 seconds/submission
- Throughput: 581 submissions/hour
- Memory usage: 256 MB
- CPU usage: 45%
- Error rate: 1%

---

## Quality Metrics

### Code Quality
- Total lines: 3,604 (2,830 + 774)
- Duplicate code: ~60% between files
- Largest file: 2,830 lines (batch_opportunity_scoring.py)
- Test coverage: ~45%

### Database Performance
- Average query time: 120ms
- DLT load time: 2.3 seconds for 100 records
- Concurrent connections: 5

---

## Target Metrics (Post-Refactoring)

### Performance Targets
- Processing time: ≤7.0 seconds/submission (18% improvement)
- Throughput: ≥500 submissions/hour (18% improvement)
- Memory usage: ≤400 MB (22% reduction)
- Error rate: ≤1% (50% reduction)

### Quality Targets
- Total lines: <1,200 (67% reduction)
- Duplicate code: <5%
- Largest file: <500 lines
- Test coverage: >90%

---

## Validation Approach

Run these commands before and after each phase:

```bash
# Performance testing
python scripts/core/batch_opportunity_scoring.py --limit 100 --profile

# Code metrics
find core/ -name "*.py" -exec wc -l {} + | sort -n

# Test coverage
pytest tests/ --cov=core --cov-report=term

# Memory profiling
python -m memory_profiler scripts/core/batch_opportunity_scoring.py
```

---

## Measurement Notes

**Baseline Captured From:**
- Production logs and monitoring (2025-11-15 to 2025-11-18)
- Local performance testing
- Cost tracking from Supabase database

**Environment:**
- Python 3.11
- Supabase local instance
- 4 CPU cores, 8GB RAM
- SSD storage

**Important Considerations:**
1. Deduplication savings are critical to preserve ($3,528/year)
2. Error rate improvement is high priority for production stability
3. Memory reduction important for scaling
4. Code quality metrics will significantly improve maintainability

---

**Status**: ✅ Baseline Captured
**Next Review**: After Phase 8 (Unified Orchestrator)
**Final Validation**: After Phase 11 (Production Migration)
