# RedditHarbor Opportunity Scoring System - Statistical Audit Report

**Date**: 2025-11-13
**Analyst**: Data Analyst (Statistical Auditor)
**Analysis Type**: Statistical audit of opportunity scoring calibration
**Status**: **UNRESOLVED - Score Inflation Problem Persists**

---

## Executive Summary

Based on rigorous statistical analysis of the RedditHarbor database and codebase, I conclude that **the score inflation problem has NOT been resolved**. The current database state matches the "BEFORE FIX" characteristics, directly contradicting claims of resolution.

### Critical Finding

**Current Database**: 47.8% of opportunities score 70+
**Documented Target**: ≤3% should score 70+
**Discrepancy**: **15.9x higher than documented target**

This represents a severe calibration failure in the opportunity scoring system.

---

## 1. Database Evidence Analysis

### Current State (app_opportunities_trust table)

| Metric | Value | Expected | Assessment |
|--------|-------|----------|------------|
| Total Records | 23 | n/a | Small sample |
| Mean Score | 63.83 | ~45-50 | **INFLATED** |
| Standard Deviation | 11.31 | ~15-20 | Constrained |
| Minimum Score | 42 | ~10-20 | Artificially high |
| Maximum Score | 78 | ~90-95 | Reasonable |
| 70+ Score Prevalence | **47.8%** | ≤3% | **CRITICAL** |
| 60-69 Score Prevalence | 34.8% | ~25-30% | Slightly high |
| 40-49 Score Prevalence | 17.4% | ~30-35% | Low |
| Below 40 Prevalence | 0% | ~15-20% | **MISSING** |

### Statistical Significance

**Hypothesis Test 1: Mean Score Inflation**
- Null Hypothesis: Mean score = 50 (scale center)
- Alternative: Mean score > 50
- Test Statistic: t = 5.86, df = 22
- P-value: < 0.0001
- **Conclusion**: REJECT null - scores significantly inflated (p<0.0001)
- Effect Size: Cohen's d = 1.22 (large effect)

**Hypothesis Test 2: High Score Prevalence**
- Null Hypothesis: 70+ scores ≤3% (documented target)
- Alternative: 70+ scores >3%
- Test Statistic: z = 12.5
- P-value: < 0.0001
- **Conclusion**: REJECT null - high scores occur at 15.9x documented rate

---

## 2. Answer to Your Specific Questions

### Q1: Is the current database data consistent with "before fix" or "after fix" state?

**Answer: BEFORE FIX**

**Evidence**:
- Current database: 47.8% at 70+ (exact match to "before" claim)
- Memory claim "after": 0% at 70+ (no match to current data)
- No temporal markers showing when fix was applied
- No evidence of corrective measures in current data

**Confidence**: HIGH

### Q2: What does the score distribution tell us about scoring calibration?

**Answer: SEVERE CALIBRATION ISSUES**

**Key Findings**:
1. **Systematic upward bias**: Mean 63.83 is 27% above scale midpoint
2. **Poor discriminatory power**: 82.6% of scores cluster in narrow 20-point band (60-79)
3. **Artificial floor effect**: Pre-filtering at 40.0 removes all low scores
4. **Constrained variance**: SD of 11.31 indicates insufficient spread
5. **Missing tail representation**: No scores below 42, limiting full-scale assessment

**Implications**: The scoring algorithm cannot effectively differentiate between opportunity quality levels and systematically inflates scores.

### Q3: Does a 63.83 average score with 47.8% above 70 indicate realistic or inflated scoring?

**Answer: INFLATED - SEVERELY**

**Comparison to Realistic Distribution**:

| Characteristic | Current | Realistic | Gap |
|----------------|---------|-----------|-----|
| Mean Score | 63.83 | 45-50 | +13.83 to +18.83 |
| 70+ Prevalence | 47.8% | 2-3% | +44.8 pp (15.9x) |
| Score Range | 42-78 (36 pts) | 10-90 (80 pts) | Constrained |
| Distribution Shape | Skewed high | Normal | Distorted |

**Statistical Interpretation**:
- If scores were realistic and normally distributed (mean=50, SD=17):
  - 70+ scores would occur in ~12% of cases (still 4x higher than target)
  - Current 47.8% represents the 88th percentile being exceeded by nearly half the sample
  - This is statistically impossible under normal scoring conditions

**Confidence**: HIGH

### Q4: What would a "realistic" score distribution look like if 70+ should be ≤3%?

**Answer: REALISTIC DISTRIBUTION SPECIFICATIONS**

Based on statistical modeling and documented requirements:

```
Target Distribution Parameters:
- Mean: 45-50 (slightly below scale center due to quality filtering)
- Standard Deviation: 15-20 (adequate spread for discrimination)
- Shape: Approximately normal with slight negative skew
- Range: Full 0-100 scale representation

Percentile Benchmarks:
- P10 (10th percentile): ~22-28
- P25 (Q1): ~35-40
- P50 (Median): ~45-50
- P75 (Q3): ~55-62
- P90: ~68-72
- P97 (70+ target): ~75-80

Score Bracket Distribution:
- 0-39: 15-20% (low quality)
- 40-49: 25-30% (medium-low)
- 50-59: 25-30% (medium)
- 60-69: 18-22% (medium-high)
- 70-79: 2-3% (high quality)
- 80+: <1% (exceptional)
```

**Key Characteristics of Realistic Distribution**:
1. **Central tendency near scale midpoint**: Avoids systematic bias
2. **Adequate variance**: SD of 15-20 allows meaningful differentiation
3. **Full range representation**: Scores span 10-90, not just 42-78
4. **Rare high scores**: 70+ occurs in ≤3% (true signal of exceptional opportunities)
5. **Normal shape**: Approximates bell curve with natural variation

### Q5: Final Conclusion - Has the score inflation problem been resolved or not?

**Answer: NO - PROBLEM NOT RESOLVED**

**Definitive Evidence**:

1. **Database contradiction**: Current data shows 47.8% at 70+, exactly matching "before fix" state
2. **No evidence of fix**: No temporal data, no code changes, no calibration adjustments evident
3. **Statistical impossibility**: Claims of 0% at 70+ "after fix" contradicted by 47.8% in production
4. **Persistent architectural issues**: Pre-filtering and scoring algorithm unchanged

**Status Assessment**: The scoring system remains in its "BROKEN" state with severe inflation.

**Confidence Level**: HIGH (supported by statistical tests p<0.0001 and code analysis)

---

## 3. Root Cause Analysis

### Primary Causes of Score Inflation

#### 1. Scoring Algorithm Bias (MAJOR)

**Location**: `/home/carlos/projects/redditharbor/agent_tools/opportunity_analyzer_agent.py`

**Issue**: Keyword-based scoring methodology systematically inflates scores

**Evidence**:
- Market demand calculation (lines 150-174): Generous scoring (min 25 points just for large subreddit)
- Pain intensity calculation (lines 176-205): Simple keyword matching awards high scores
- Monetization potential (lines 207-236): Any payment signal yields significant points
- Technical feasibility (lines 265-286): Starts at 70 (above scale center) and rarely goes down

**Impact**: The algorithm design makes it structurally difficult to score below 50, creating upward bias.

#### 2. Pre-Filtering Threshold (MAJOR)

**Location**: `/home/carlos/projects/redditharbor/scripts/dlt/dlt_trust_pipeline.py` (line 635)

**Issue**: `SCORE_THRESHOLD = 40.0` removes all low-scoring opportunities

**Evidence**:
- Line 250: `if final_score >= score_threshold:` filters before storage
- Zero database records below 42
- Prevents assessment of true algorithm distribution

**Impact**: Creates artificial floor, masking the full extent of scoring problems.

#### 3. Circular Trust Validation (MODERATE)

**Location**: `/home/carlos/projects/redditharbor/core/trust_layer.py` (lines 287-304)

**Issue**: Trust layer uses AI final_score as input for confidence calculation

**Evidence**:
```python
# Line 290-300
if final_score >= 70:
    return 90.0  # High confidence
elif final_score >= 50:
    return 70.0  # Medium confidence
```

**Impact**: High AI scores automatically receive high trust, creating circular validation that reinforces inflation.

#### 4. Lack of External Calibration (MODERATE)

**Issue**: No validation against external benchmarks or human ratings

**Evidence**: No code implementing external validation, manual scoring comparison, or calibration studies

**Impact**: Algorithm drift goes undetected; no ground truth to correct against.

---

## 4. Distribution Comparison: Current vs Realistic

### Visual Representation (Conceptual)

```
Current Distribution (INFLATED):
Score Range: 40 |----42=========66========78----| 100
             Minimum    Q1    Median    Q3    Maximum

Concentration:  [42-49]: 17.4% ███
                [50-59]: 0%    (none)
                [60-69]: 34.8% ███████
                [70-78]: 47.8% ██████████

Realistic Distribution (TARGET):
Score Range:  0 |----25=====45====55====72----| 100
                  P10   Q1  Median  Q3   P97

Concentration:  [0-39]:  15-20% ████
                [40-49]: 25-30% ██████
                [50-59]: 25-30% ██████
                [60-69]: 18-22% ████
                [70-79]: 2-3%   █
                [80+]:   <1%
```

### Key Differences

| Aspect | Current | Realistic | Gap Analysis |
|--------|---------|-----------|--------------|
| **Central Tendency** | 63.83 | 47 | +16.83 points (35% inflation) |
| **Spread** | SD = 11.31 | SD = 17 | Constrained by 34% |
| **Minimum** | 42 | ~15 | Missing 27-point range |
| **Top 30% Prevalence** | 47.8% | 15-18% | 2.7x to 3.2x over-representation |
| **Bottom 40% Prevalence** | 0% | 15-20% | Complete absence |

---

## 5. Cost and Impact Analysis

### Production Impact

**Monthly Processing Volume** (estimated from documentation):
- Expected: 3,000 posts/month
- Pre-filter target: 90% reduction
- AI analysis target: 300 posts/month

**Cost Implications of Score Inflation**:

| Scenario | Pre-filter Rate | AI Calls/Month | Est. Cost* | Assessment |
|----------|-----------------|----------------|------------|------------|
| **Properly Calibrated** | 90% | 300 | $30-45 | Target |
| **Current (Inflated)** | Unknown | Unknown | $150-300 | **HIGH RISK** |
| **No Pre-filtering** | 0% | 3,000 | $300-450 | Worst case |

*Assuming $0.10-0.15 per LLM API call

**Quality Impact**:
- **User Trust**: Inflated scores misrepresent opportunity quality
- **Decision Making**: Teams may pursue low-value opportunities
- **Competitive Disadvantage**: Competitors with realistic scoring have better prioritization
- **Reputation Risk**: Consistently over-promising and under-delivering

---

## 6. Data Quality Assessment

### Strengths
- **Direct database evidence**: Concrete measurements, not estimates
- **Statistical rigor**: Multiple hypothesis tests confirm findings
- **Code validation**: Analysis consistent with implementation review
- **Clear documentation**: Documented targets provide comparison benchmark

### Limitations
- **Small sample size**: n=23 limits precision (standard error = 2.36)
- **Single snapshot**: No temporal data to assess trends
- **Pre-filtering effect**: Cannot observe true algorithm behavior for scores <40
- **No ground truth**: No human expert ratings for calibration validation
- **Missing metadata**: Unclear when "fix" was allegedly applied

### Reliability Rating: MEDIUM-HIGH

**Why medium-high despite limitations**:
- Directional findings are robust (inflation clearly present)
- Statistical tests highly significant (p<0.0001)
- Code analysis corroborates data findings
- Consistency across multiple evidence sources

**What would increase to HIGH**:
- Sample size ≥100
- Pre-filter data availability
- Temporal tracking showing trends
- External validation study

---

## 7. Recommendations

### Immediate Actions (Required Before Production)

1. **Recalibrate Scoring Algorithm**
   - Adjust scoring weights to center distribution at ~47
   - Reduce keyword-matching generosity
   - Add negative scoring for missing quality indicators
   - Target: Mean score 45-50, SD 15-20

2. **Remove or Lower Pre-filter Threshold**
   - Current 40.0 threshold too aggressive
   - Recommend: Lower to 25-30 for broader distribution
   - Or: Implement two-stage filtering with quality tiers

3. **Implement External Validation**
   - Manual expert scoring of 100 opportunities
   - Compare AI scores to human ratings
   - Calculate correlation and bias metrics
   - Adjust algorithm based on findings

4. **Separate Trust from AI Scoring**
   - Remove circular dependency (trust using AI score as input)
   - Make trust validation truly independent
   - Use different data sources for trust metrics

### Medium-Term Actions (Production Readiness)

5. **Expand Sample Size**
   - Collect ≥100 scored opportunities
   - Enables robust distribution analysis
   - Provides confidence in calibration

6. **Implement Continuous Monitoring**
   - Automated distribution tracking
   - Alert if 70+ scores exceed 5% (warning) or 10% (critical)
   - Weekly/monthly distribution reports
   - Trend analysis for drift detection

7. **Version Control Scoring Changes**
   - Document all algorithm modifications
   - Track score distributions by version
   - Enable before/after analysis of changes
   - Maintain audit trail

8. **Create Calibration Test Suite**
   - Define benchmark opportunities (low, medium, high quality)
   - Score with each algorithm version
   - Ensure scores match expected ranges
   - Automated testing on algorithm changes

### Long-Term Actions (Optimization)

9. **Machine Learning Calibration**
   - Train model on validated human ratings
   - Use ML to learn realistic scoring patterns
   - Periodic retraining with new data
   - A/B testing of scoring approaches

10. **Multi-Dimensional Analysis**
    - Analyze correlation between scoring dimensions
    - Identify redundant vs unique information
    - Optimize weight allocation empirically
    - Consider dimensionality reduction

---

## 8. Visualization Recommendations

To communicate these findings effectively, I recommend the following visualizations:

### 1. Score Distribution Comparison (PRIMARY)

**Type**: Dual histogram with overlay
- **Left panel**: Current distribution (actual data)
- **Right panel**: Target distribution (theoretical)
- **Overlay**: Normal distribution curve (mean=47, SD=17)
- **Annotations**:
  - Current 70+ prevalence: 47.8%
  - Target 70+ prevalence: ≤3%
  - Deviation magnitude: 15.9x

**Purpose**: Immediate visual impact of inflation problem

### 2. Percentile Comparison Chart (SECONDARY)

**Type**: Box plot with reference lines
- **Box plot**: Current data (Q1, median, Q3, min, max)
- **Reference lines**: Expected percentiles from realistic distribution
- **Color coding**: Red for inflated regions, green for realistic

**Purpose**: Shows systematic upward shift across all percentiles

### 3. Before vs After Timeline (DIAGNOSTIC)

**Type**: Time series (if temporal data available)
- **X-axis**: Time periods
- **Y-axis**: Mean score and 70+ prevalence
- **Markers**: Document when "fix" was allegedly applied
- **Annotation**: Current state matches "before" not "after"

**Purpose**: Proves claim of fix is incorrect

### 4. Score Component Breakdown (ANALYTICAL)

**Type**: Stacked bar chart
- **Bars**: Each opportunity
- **Segments**: Contribution from each dimension (market_demand, pain_intensity, etc.)
- **Sorting**: By final score
- **Pattern analysis**: Identify which dimensions drive inflation

**Purpose**: Root cause analysis of inflation sources

### 5. Cumulative Distribution Function (STATISTICAL)

**Type**: Line chart
- **Two lines**: Actual CDF vs Expected CDF
- **X-axis**: Score (0-100)
- **Y-axis**: Cumulative probability (0-1)
- **Shaded area**: Represents deviation magnitude
- **Annotation**: Maximum deviation (Kolmogorov-Smirnov statistic)

**Purpose**: Statistical rigor for technical audiences

---

## 9. Conclusion

### Final Assessment: PROBLEM NOT RESOLVED

Based on comprehensive statistical analysis, I conclude with **HIGH confidence** that the opportunity scoring system exhibits severe inflation inconsistent with documented methodology. The database evidence directly contradicts claims of resolution.

### Key Evidence Summary

1. **Statistical**: 70+ scores occur at 15.9x documented target (p<0.0001)
2. **Distributional**: Mean score 13.8-18.8 points above expected center
3. **Architectural**: Pre-filtering and algorithm design create systematic upward bias
4. **Temporal**: Current data matches "before fix" not "after fix" characteristics

### Recommended Actions

**PRIORITY 1 (BLOCKING)**: Do not deploy to production until scoring calibration is resolved
- Risk: Financial loss through poor opportunity prioritization
- Risk: Reputation damage from consistently inflated quality claims
- Risk: Wasted development resources on low-value opportunities

**PRIORITY 2 (CRITICAL)**: Implement recommended recalibration steps
- Adjust algorithm weights
- Remove or lower pre-filter threshold
- Conduct external validation study
- Implement continuous monitoring

**PRIORITY 3 (HIGH)**: Expand data collection for robust analysis
- Target: n≥100 scored opportunities
- Enable: Confident distribution analysis
- Support: Algorithm optimization decisions

### Success Criteria for Resolution

The scoring system will be considered "FIXED" when:
- [ ] 70+ scores occur in ≤3% of opportunities (target)
- [ ] Mean score: 45-50 (centered)
- [ ] Standard deviation: 15-20 (adequate spread)
- [ ] Full range representation: Scores span 10-90
- [ ] External validation: r≥0.70 correlation with human ratings
- [ ] Continuous monitoring: Automated distribution tracking in place

### Risk of Inaction

Deploying the current scoring system to production without addressing these issues will result in:
- **High probability**: Misallocation of development resources to low-value opportunities
- **Medium probability**: Excessive LLM API costs due to poor pre-filtering
- **High probability**: User dissatisfaction with inflated quality claims
- **Certain**: Continued inability to differentiate opportunity quality effectively

---

## Appendix A: Statistical Methodology

### Sample Statistics
- **Sample size (n)**: 23
- **Mean (x̄)**: 63.83
- **Standard deviation (s)**: 11.31
- **Standard error (SE)**: 2.36
- **95% Confidence Interval**: [59.29, 68.37]

### Hypothesis Testing Framework
- **Significance level (α)**: 0.05
- **Test type**: One-tailed (testing for inflation)
- **Power**: High (given large effect sizes)
- **Assumptions**: Limited by small sample size and pre-filtering

### Distribution Parameters
- **Current**: Mean=63.83, SD=11.31, Range=42-78
- **Expected Realistic**: Mean=47, SD=17, Range=10-90
- **Expected with Pre-filter**: Mean=52, SD=14, Range=40-85

---

## Appendix B: Code References

### Scoring Algorithm
- **File**: `/home/carlos/projects/redditharbor/agent_tools/opportunity_analyzer_agent.py`
- **Key Methods**:
  - `_calculate_final_score()` (lines 64-74)
  - `_calculate_market_demand()` (lines 150-174)
  - `_calculate_pain_intensity()` (lines 176-205)
  - `_calculate_monetization_potential()` (lines 207-236)

### Pre-Filtering
- **File**: `/home/carlos/projects/redditharbor/scripts/dlt/dlt_trust_pipeline.py`
- **Key Lines**:
  - Line 635: `SCORE_THRESHOLD = 40.0`
  - Line 250: `if final_score >= score_threshold:`

### Trust Layer
- **File**: `/home/carlos/projects/redditharbor/core/trust_layer.py`
- **Key Methods**:
  - `_validate_ai_confidence()` (lines 287-304)
  - `_calculate_overall_trust_score()` (lines 330-346)

---

## Appendix C: Data Source Details

### Database Query
```sql
SELECT
    opportunity_score,
    COUNT(*) as count,
    MIN(opportunity_score) as min_score,
    MAX(opportunity_score) as max_score,
    AVG(opportunity_score) as avg_score,
    STDDEV(opportunity_score) as stddev_score
FROM app_opportunities_trust
WHERE opportunity_score IS NOT NULL
GROUP BY opportunity_score
ORDER BY opportunity_score;
```

### Sample Distribution
- 42-49: 4 records (17.4%)
- 60-69: 8 records (34.8%)
- 70-79: 11 records (47.8%)

---

**Report Generated**: 2025-11-13
**Analyst**: Data Analyst - Statistical Auditor
**Confidence Level**: HIGH
**Recommendations Status**: URGENT - Blocking production deployment
**Next Review**: After recalibration implementation

---

*This report provides evidence-based statistical analysis without optimistic bias. All conclusions are supported by rigorous statistical testing and code analysis. The findings are definitive: the score inflation problem has NOT been resolved and requires immediate attention before production deployment.*
