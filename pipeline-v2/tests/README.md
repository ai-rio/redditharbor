# Pipeline-v2 Tests

Comprehensive TDD test suite for quality filter migration validation.

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures and configuration
├── test_old_system_baseline.py         # OLD system behavior baseline
├── test_quality_filter_migration.py    # NEW vs OLD migration validation
└── test_cost_savings_validation.py     # Cost savings proof
```

## Test Suites

### 1. test_old_system_baseline.py

**Purpose**: Capture and document OLD system behavior (dlt_trust_pipeline.py lines 92-176)

**Coverage**:
- Quality score calculation logic
- Filter decision logic (currently disabled)
- Threshold constants and rationale
- Field mapping (upvotes/score, text/content, etc.)
- Edge case handling

**Key Tests**:
- `test_high_quality_score()` - High-quality posts score well
- `test_score_components_*()` - Engagement, keywords, recency components
- `test_rejects_low_*()` - Filter conditions (when enabled)
- `test_edge_case_*()` - Boundary conditions
- `test_*_field_names()` - Field name variations

**Status**: Documents OLD system with filtering DISABLED (returns True always)

### 2. test_quality_filter_migration.py

**Purpose**: Prove NEW filter (pipeline-v2/filters/quality.py) matches OLD filter exactly

**Critical Validations**:
- ✅ Quality scores match (±0.1 tolerance)
- ✅ Filter decisions match
- ✅ Filter rate matches
- ✅ Edge cases handled identically
- ✅ No regressions introduced

**Key Tests**:
- `test_scores_match_for_100_posts()` - Score identity on 100 varied posts
- `test_same_decisions_for_100_posts()` - Decision identity
- `test_filter_rate_55_to_65_percent()` - Target filter rate
- `test_no_false_positives_high_quality()` - No high-quality posts filtered
- `test_no_false_negatives_spam()` - Spam properly filtered

**New Features Validated**:
- Human-readable filter reasons
- Quality score breakdowns
- Filter statistics
- enable_filtering flag for testing
- Batch filtering with metadata

### 3. test_cost_savings_validation.py

**Purpose**: Validate cost-saving behavior and prove ROI

**Cost Model**:
- Posts/month: 10,000 (production volume)
- Cost/AI call: $0.02943
- Target filter rate: 60% (range: 55-65%)
- Expected annual savings: $2,116

**Key Tests**:
- `test_filter_rate_on_*()` - Filter rate at various volumes
- `test_annual_savings_calculation()` - Prove $2,116/year savings
- `test_high_quality_posts_always_pass()` - Zero false negatives
- `test_filter_stats_breakdown()` - Filter reason distribution
- `test_threshold_sensitivity()` - Threshold optimization analysis

**Performance Requirements**:
- Process 10K posts in <5 seconds (2000+ posts/sec)
- Filter rate consistency <3% std dev
- Zero false negatives on high-quality posts

## Running Tests

### Run All Tests
```bash
cd /home/carlos/projects/redditharbor-core-functions-fix
pytest pipeline-v2/tests/ -v
```

### Run Specific Test Suite
```bash
# Baseline tests only
pytest pipeline-v2/tests/test_old_system_baseline.py -v

# Migration validation only
pytest pipeline-v2/tests/test_quality_filter_migration.py -v

# Cost savings validation only
pytest pipeline-v2/tests/test_cost_savings_validation.py -v
```

### Run by Marker
```bash
# Baseline tests
pytest -m baseline -v

# Migration tests
pytest -m migration -v

# Cost savings tests
pytest -m cost_savings -v

# Skip slow tests
pytest -m "not slow" -v
```

### Run with Coverage
```bash
pytest pipeline-v2/tests/ --cov=pipeline_v2.filters --cov-report=html
```

### Run with Detailed Output
```bash
# Show print statements and detailed output
pytest pipeline-v2/tests/ -v -s

# Show cost savings calculations
pytest pipeline-v2/tests/test_cost_savings_validation.py::TestCostSavingsCalculation -v -s
```

## Test Data

### Test Post Distributions

**High-Quality (should PASS)**:
- Upvotes: 20-70
- Comments: 10-30
- Keywords: 2-5 problem indicators
- Age: 0-24 hours

**Medium-Quality (borderline)**:
- Upvotes: 5-20
- Comments: 1-5
- Keywords: 1-2 problem indicators
- Age: 0-48 hours

**Low-Quality (should FAIL)**:
- Upvotes: 0-5
- Comments: 0-1
- Keywords: 0-1 problem indicators
- Age: any

### Realistic Distribution
Based on production Reddit data:
- 10% high-quality opportunities
- 15% medium-quality
- 25% low-engagement
- 30% no problem keywords
- 20% spam/noise

Expected filter rate: ~60%

## Success Criteria

### Phase 1: Baseline ✅
- ✅ All OLD system tests pass
- ✅ Behavior documented
- ✅ Thresholds validated
- ✅ Edge cases identified

### Phase 2: Migration ✅
- ✅ NEW scores match OLD scores (±0.1)
- ✅ NEW decisions match OLD decisions
- ✅ Filter rate in range (55-65%)
- ✅ No false negatives on high-quality posts
- ✅ Performance acceptable

### Phase 3: Production Ready ✅
- ✅ Cost savings validated ($2,116/year)
- ✅ Filter rate stable across runs
- ✅ Zero false negatives
- ✅ Performance at scale (10K posts <5s)
- ✅ Deterministic results

## Known Issues

### OLD System
- **Filtering DISABLED**: Line 152 returns True for all posts
- **When Re-enabled**: Will filter ~60% of posts as designed
- **Migration Impact**: NEW system has filtering ENABLED by default

### NEW System Improvements
- ✅ Provides human-readable filter reasons
- ✅ Detailed quality score breakdowns
- ✅ Filter statistics and analytics
- ✅ enable_filtering flag for gradual rollout
- ✅ Batch processing with metadata

## Test Fixtures

### Provided by conftest.py
- `sample_post` - Basic post for simple tests
- `high_quality_posts(count)` - Generate high-quality posts
- `low_quality_posts(count)` - Generate low-quality posts
- `mixed_quality_posts(count)` - Realistic distribution
- `edge_case_posts` - Boundary condition posts
- `field_name_variations` - Different field naming conventions
- `large_dataset(count)` - Performance testing data
- `test_data_generator` - TestDataGenerator instance

### Helper Functions
- `assert_score_in_range()` - Validate score range
- `assert_filter_rate_in_range()` - Validate filter rate

## Continuous Integration

### Pre-commit Checks
```bash
# Run before committing
pytest pipeline-v2/tests/ -m "not slow" -v
```

### Full Test Suite (CI)
```bash
# Run in CI pipeline
pytest pipeline-v2/tests/ -v --cov=pipeline_v2.filters
```

## Troubleshooting

### Import Errors
```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH=/home/carlos/projects/redditharbor-core-functions-fix:$PYTHONPATH
pytest pipeline-v2/tests/ -v
```

### Slow Tests
```bash
# Skip slow tests (>10K posts)
pytest -m "not slow" -v
```

### Failed Migration Tests
If migration tests fail:
1. Check OLD system constants unchanged
2. Verify NEW system imports correctly
3. Compare score calculations step-by-step
4. Check field name mappings

## Documentation

### Generated Reports
- HTML Coverage: `htmlcov/index.html`
- Cost Analysis: Printed during `test_annual_savings_calculation()`
- Filter Stats: Printed during `test_filter_stats_breakdown()`
- Threshold Sensitivity: Printed during `test_threshold_sensitivity()`

### Key Metrics
- **Test Count**: 50+ comprehensive tests
- **Code Coverage**: Target 95%+ on filters/
- **Performance**: 2000+ posts/second
- **False Negative Rate**: 0%
- **Filter Rate Accuracy**: ±3% std dev

## Next Steps

### After Tests Pass
1. ✅ Document OLD system behavior
2. ✅ Validate NEW system matches OLD
3. ✅ Prove cost savings
4. ⏭️ Integration testing with full pipeline
5. ⏭️ Gradual rollout with enable_filtering flag
6. ⏭️ Monitor production filter rates
7. ⏭️ A/B testing if needed

### Future Enhancements
- Add regression tests for specific edge cases
- Benchmarking suite for performance tracking
- Integration tests with AI analysis stage
- Load testing for pipeline throughput
