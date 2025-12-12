# Priority 1: Opportunity Validator - Data Architecture Plan

**Status**: Planning Phase
**Target Metric**: Process 70+ opportunities at <100ms per opportunity
**Business Goal**: Identify & track 50+ high-scoring (70+) opportunities quarterly with 1-3 function compliance

---

## 1. Current State Analysis

### Existing Infrastructure ✅
- **Pipeline-v4**: Extract → Transform → Load architecture operational
- **Scoring**: 5-dimensional LLM-based analysis (0-100 scale)
- **Constraints**: 1-3 core functions validation via Pydantic
- **Storage**: `app_opportunities` table with JSONB fields
- **Filtering**: Pre-AI quality checks (engagement, keywords) + post-AI constraint validation

### Gap: No Pipeline-Level 70+ Threshold
**Current behavior**: All analyzed opportunities stored regardless of score
**Query-time filtering**: Dashboard applies 70+ threshold visually only
**Business impact**: Cannot distinguish high-value opportunities during collection

---

## 2. Priority 1 Solution: Opportunity Validator

### What It Does (Simple)
1. **Validates opportunity meets criteria**:
   - `final_score >= 70`
   - `core_functions` count is 1-3
   - `confidence_score >= 75` (default validation)

2. **Gates storage decision**:
   - Score >= 70 → Store to DB
   - Score < 70 → Log & skip (optional archive table)

3. **Tracks quarterly progress**:
   - Count of 70+ opportunities stored
   - Progress toward 50+ quarterly target

---

## 3. Minimal Data Schema Changes

### Option A: Add Columns to `app_opportunities` (Recommended)

```sql
-- New columns for validator tracking
ALTER TABLE app_opportunities ADD COLUMN (
    passes_validator boolean DEFAULT false,          -- Did it pass 70+ threshold?
    validator_version varchar(20) DEFAULT '1.0',     -- Validator algorithm version
    validation_timestamp timestamp DEFAULT now()     -- When validator ran
);

-- New index for efficient high-value filtering
CREATE INDEX idx_app_opportunities_validator
ON app_opportunities(passes_validator, final_score DESC);
```

### Option B: Separate `opportunities_archive` (If Needed Later)

For now: **Skip this**. We can archive sub-70 scores later if needed.

### Pipeline-v4 Impact

**Current pipeline-v4 flow**:
```
LLM Analysis (transform/analyzer.py)
  → AnalysisResult (with final_score)
  → Opportunity model (auto-calculates final_score from metrics)
  → Loader.save_analysis() → PostgreSQL
```

**Modified flow with validator**:
```
LLM Analysis (transform/analyzer.py)
  → AnalysisResult (with final_score)
  → OpportunityValidator.validate()
    ├─ Check: final_score >= 70
    ├─ Check: len(core_functions) in [1, 2, 3]
    ├─ Check: confidence_score >= 75
    └─ Return: ValidationResult {is_valid, reason, scores}
  → IF valid: Opportunity model → Loader.save_analysis()
  → IF invalid: Log to validation_skipped.json, skip save
```

---

## 4. Minimal Code Changes Required

### New File: `core/validation/opportunity_validator.py`

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationResult:
    is_valid: bool
    score: float
    reason: Optional[str] = None
    core_functions_count: Optional[int] = None

class OpportunityValidator:
    """Validates opportunities meet Priority 1 criteria."""

    MIN_SCORE = 70.0
    MIN_CONFIDENCE = 75.0
    VALID_FUNCTION_COUNTS = {1, 2, 3}

    @staticmethod
    def validate(analysis_result) -> ValidationResult:
        """
        Returns ValidationResult indicating if opportunity meets 70+ threshold.
        """
        # Check score
        if analysis_result.final_score < OpportunityValidator.MIN_SCORE:
            return ValidationResult(
                is_valid=False,
                score=analysis_result.final_score,
                reason=f"Score {analysis_result.final_score} < {OpportunityValidator.MIN_SCORE}"
            )

        # Check confidence
        if analysis_result.confidence_score < OpportunityValidator.MIN_CONFIDENCE:
            return ValidationResult(
                is_valid=False,
                score=analysis_result.final_score,
                reason=f"Confidence {analysis_result.confidence_score} < {OpportunityValidator.MIN_CONFIDENCE}"
            )

        # Check core functions (extract from app_idea)
        core_functions = analysis_result.app_idea.core_functions
        func_count = len(core_functions)

        if func_count not in OpportunityValidator.VALID_FUNCTION_COUNTS:
            return ValidationResult(
                is_valid=False,
                score=analysis_result.final_score,
                reason=f"Invalid function count: {func_count}. Must be 1-3.",
                core_functions_count=func_count
            )

        # All checks passed
        return ValidationResult(
            is_valid=True,
            score=analysis_result.final_score,
            core_functions_count=func_count
        )
```

### Modify: `pipeline-v4/core/pipeline.py`

```python
from core.validation.opportunity_validator import OpportunityValidator

class Pipeline:
    def run(self, subreddit: str, limit: int = 10) -> dict:
        """Process submissions with validation."""

        analyzed_count = 0
        validated_count = 0  # NEW: Track passes
        skipped_count = 0    # NEW: Track failures

        for analysis in analyses:
            try:
                # NEW: Validate before saving
                validation = OpportunityValidator.validate(analysis)

                if not validation.is_valid:
                    logger.info(f"Validation failed: {validation.reason}")
                    skipped_count += 1
                    continue  # Skip saving

                if self.loader.save_analysis(analysis):
                    validated_count += 1

            except Exception as e:
                logger.error(f"Error: {e}")
                skipped_count += 1

        return {
            "analyzed": analyzed_count,
            "validated": validated_count,  # NEW
            "skipped": skipped_count,      # NEW
            "saved": validated_count
        }
```

---

## 5. Data Flow: Validator Integration

```
┌────────────────────────────────────────────────────────────────┐
│               OPPORTUNITY VALIDATOR DATA FLOW                  │
└────────────────────────────────────────────────────────────────┘

1. EXTRACT (Reddit API)
   └─ fetch_submissions() → list[RedditSubmission]

2. TRANSFORM (LLM Analysis)
   └─ analyzer.analyze() → AnalysisResult {final_score, app_idea}

3. VALIDATE ← NEW STEP (Validator)
   ├─ Check: final_score >= 70.0
   ├─ Check: len(core_functions) in {1,2,3}
   ├─ Check: confidence_score >= 75.0
   └─ Result: ValidationResult {is_valid, score, reason}

4. CONDITIONAL LOAD
   ├─ IF is_valid=True:
   │  └─ loader.save_analysis() → Opportunity → PostgreSQL
   │     └─ Set: passes_validator=True
   │
   └─ IF is_valid=False:
      └─ Log to metrics
      └─ Skip database save

5. TRACK (Quarterly Progress)
   └─ Query: SELECT COUNT(*) FROM app_opportunities
              WHERE passes_validator=True
   └─ Target: >= 50 quarterly
```

---

## 6. Database Query Patterns (Post-Migration)

### Query 1: All Valid 70+ Opportunities
```sql
SELECT
    submission_id,
    subreddit,
    final_score,
    core_functions,
    created_at
FROM app_opportunities
WHERE passes_validator = true
ORDER BY final_score DESC;
```

### Query 2: Quarterly Progress Tracking
```sql
SELECT
    DATE_TRUNC('quarter', created_at) as quarter,
    COUNT(*) as count_70_plus,
    AVG(final_score) as avg_score,
    MIN(final_score) as min_score
FROM app_opportunities
WHERE passes_validator = true
GROUP BY DATE_TRUNC('quarter', created_at)
ORDER BY quarter DESC;
```

### Query 3: Validation Audit
```sql
SELECT
    subreddit,
    COUNT(*) as total_analyzed,
    SUM(CASE WHEN passes_validator THEN 1 ELSE 0 END) as valid_70_plus,
    ROUND(100.0 * SUM(CASE WHEN passes_validator THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate
FROM app_opportunities
GROUP BY subreddit
ORDER BY pass_rate DESC;
```

---

## 7. Implementation Checklist (Phase 1)

### Database Migration
- [ ] Add `passes_validator` column to `app_opportunities`
- [ ] Add `validator_version` column
- [ ] Add `validation_timestamp` column
- [ ] Create index on `(passes_validator, final_score DESC)`
- [ ] Backfill existing records: `passes_validator = (final_score >= 70.0)`

### Code Changes
- [ ] Create `core/validation/opportunity_validator.py`
- [ ] Update `pipeline-v4/core/pipeline.py` to call validator
- [ ] Update `pipeline-v4/load/loader.py` to set `passes_validator` flag
- [ ] Add logging: Track validation pass/fail rates

### Testing
- [ ] Unit test: OpportunityValidator with score 69.9 (fails), 70.0 (passes)
- [ ] Unit test: Core functions count 0, 1, 2, 3, 4 (only 1-3 valid)
- [ ] Integration test: Full pipeline with mixed scoring
- [ ] Verify: Quarterly count query returns 50+ during test

### Metrics/Tracking
- [ ] Add to dashboard: Total 70+ opportunities count
- [ ] Add quarterly progress widget
- [ ] Track validation pass rate by subreddit

---

## 8. Success Metrics (Phase 1)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Processing Time** | <100ms per opportunity | Measure `validator.validate()` latency |
| **Accuracy** | >95% high-score identification | Manual spot-check of top 20 scores |
| **Quarterly Target** | ≥50 opportunities | Run collection for full quarter, count `passes_validator=True` |
| **Function Compliance** | >90% have 1-3 functions | Query: `SELECT COUNT(*) WHERE core_functions NOT IN (1,2,3)` |

---

## 9. What We're NOT Doing (Keep it Simple)

❌ Complex caching layer
❌ Real-time dashboards
❌ Advanced ML models
❌ Separate microservices
❌ Kubernetes orchestration
❌ Message queues
❌ Event streaming

✅ **Just**: Add validator, filter at pipeline level, track metrics

---

## 10. Dependency Tree (Required for Implementation)

```
Priority 1 Opportunity Validator
├─ DATABASE MIGRATION (baseline)
│  └─ Modify app_opportunities schema
├─ VALIDATOR MODULE (core business logic)
│  └─ core/validation/opportunity_validator.py
├─ PIPELINE INTEGRATION (gating logic)
│  └─ pipeline-v4/core/pipeline.py
│  └─ pipeline-v4/load/loader.py
└─ METRICS TRACKING (monitoring)
   └─ Query patterns for quarterly reporting

Ready to implement after this architecture review ✓
```

---

## 11. Next Steps

**Phase 1 Duration**: 1-2 weeks
**Effort**: ~20-30 hours

1. Database migration (1-2 hours)
2. Validator module + pipeline integration (4-6 hours)
3. Testing & validation (4-6 hours)
4. Metrics & dashboard integration (4-6 hours)
5. Documentation & deployment (2-3 hours)

**Success Criteria**:
- ✅ Pipeline filters to 70+ opportunities
- ✅ 1-3 function compliance enforced
- ✅ Quarterly tracking shows ≥50 opportunities
- ✅ <100ms processing per opportunity
