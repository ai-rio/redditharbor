# RedditHarbor Live Testing

Comprehensive live testing framework to validate that the RedditHarbor pipeline can discover actual monetizable app opportunities from real Reddit discussions.

## Quick Start

```bash
# Run phases sequentially
/live-test-phase1-smoke      # 30 min - Basic functionality
/live-test-phase2-business   # 1 hour - Business value
/live-test-phase3-volume     # 45 min - Scalability
/live-test-phase4-validation # 2-3 hours - Deep validation
```

## Directory Structure

```
docs/live-test/
├── README.md                          # This file
├── PROGRESS.md                        # Live testing progress tracker
├── live-testing-framework.md         # Original framework document
├── reports/                           # Test results by phase
│   ├── phase1/                       # Smoke test reports
│   ├── phase2/                       # Business validation reports
│   ├── phase3/                       # Performance reports
│   └── phase4/                       # Deep validation & production readiness
├── templates/                         # Report templates (future)
└── workspaces/                        # Temporary phase workspaces
    ├── phase1-workspace/             # Phase 1 working files
    ├── phase2-workspace/             # Phase 2 working files
    ├── phase3-workspace/             # Phase 3 working files
    └── phase4-workspace/             # Phase 4 working files
```

## Testing Phases

### Phase 1: Smoke Test (30 minutes)
**Command**: `/live-test-phase1-smoke`

**Objective**: Validate basic pipeline functionality with real Reddit data

**Configuration**:
- Posts: 10
- Subreddit: productivity
- Focus: All 6 pipeline steps working

**Success Criteria**:
- Pipeline completes without errors
- All 6 steps execute successfully
- Database stores ~10 records
- 2-3 records have meaningful content

**Agent**: `testing-suite:test-engineer`

---

### Phase 2: Business Value Validation (1 hour)
**Command**: `/live-test-phase2-business`

**Objective**: Verify AI can identify real monetizable opportunities

**Configuration**:
- Posts: 25
- Subreddits: personalfinance, productivity, fitness
- Focus: Problem detection, scoring accuracy

**Success Criteria**:
- At least 3 opportunities with scores >70
- Problems are identifiable
- "I wish"/"if only" language detected
- Clear pain points mentioned
- 1-3 function constraint enforced

**Agent**: `project-management-suite:business-analyst`

---

### Phase 3: Volume Test (45 minutes)
**Command**: `/live-test-phase3-volume`

**Objective**: Validate pipeline scalability and performance

**Configuration**:
- Posts: 100
- Subreddits: productivity, personalfinance, startups, fitness
- Focus: Performance, memory, throughput

**Success Criteria**:
- Pipeline completes in <10 minutes
- Memory usage <2GB
- No API rate limiting
- Quality filtering ~60%
- Error rate <5%

**Agent**: `supabase-toolkit:data-engineer`

---

### Phase 4: Deep Validation (2-3 hours)
**Command**: `/live-test-phase4-validation`

**Objective**: Comprehensive quality assurance and production readiness

**Configuration**:
- Posts: 50
- Subreddits: freelancer, HomeImprovement, smallbusiness
- Focus: Quality, correlation analysis, viability

**Success Criteria**:
- Top 20 opportunities deeply reviewed
- Correlation >0.7 (AI scores vs manual ratings)
- Database integrity confirmed
- Production readiness assessed
- Top 3 opportunities ready for development

**Agents**: `business-analyst` + `ai-engineer` (parallel)

---

## Overall Success Criteria

### Minimum Viable Success
- ✅ Pipeline processes real Reddit data without errors
- ✅ Database stores opportunities correctly
- ✅ At least 5 opportunities with scores >70
- ✅ Manual validation confirms 2-3 real business opportunities

### Technical Indicators
- Pipeline completion rate: >95%
- Error rate: <5%
- Processing time: <30 sec per opportunity
- Memory usage: <1GB per 50 opportunities

### Business Indicators
- High-score opportunities (>70): ≥5 per 100 posts
- Real pain points identified: ≥3 clear examples
- Monetization potential: ≥2 with clear revenue model
- Simplicity compliance: 100% (all 1-3 functions)

---

## How to Use

### 1. Review Framework
```bash
cat docs/live-test/live-testing-framework.md
cat docs/live-test/PROGRESS.md
```

### 2. Execute Phases Sequentially
Each phase must complete successfully before the next:

```bash
# Phase 1: Smoke Test
/live-test-phase1-smoke
# Review: docs/live-test/reports/phase1/smoke-test-report.md

# Phase 2: Business Value
/live-test-phase2-business
# Review: docs/live-test/reports/phase2/business-validation-report.md

# Phase 3: Volume Test
/live-test-phase3-volume
# Review: docs/live-test/reports/phase3/performance-report.md

# Phase 4: Deep Validation
/live-test-phase4-validation
# Review: docs/live-test/reports/phase4/production-readiness-report.md
```

### 3. Review Results
After each phase:
1. Check PROGRESS.md for status updates
2. Review phase report in reports/phaseN/
3. Verify success criteria met
4. Fix any issues before proceeding

### 4. Production Decision
After Phase 4, review the production readiness report:
```bash
cat docs/live-test/reports/phase4/production-readiness-report.md
```

Decision matrix:
- **All criteria met**: Proceed to production deployment
- **Most criteria met**: Address specific issues, may skip re-testing
- **Many criteria not met**: Fix issues, re-run affected phases

---

## Key Features

### 1. Fail-Fast Pre-flight Checks
Each phase validates prerequisites before execution to prevent wasted time.

### 2. Workspace Isolation
Each phase has its own workspace directory to prevent contamination:
- Logs: `workspaces/phaseN-workspace/logs/`
- Analysis: `workspaces/phaseN-workspace/analysis/`
- Samples: `workspaces/phaseN-workspace/samples/`

### 3. Structured Reporting
All reports follow consistent templates and go to `reports/phaseN/`

### 4. Agent Specialization
Each phase uses the optimal agent type:
- Phase 1: test-engineer (pipeline validation)
- Phase 2: business-analyst (business assessment)
- Phase 3: data-engineer (performance testing)
- Phase 4: business-analyst + ai-engineer (comprehensive validation)

### 5. Progress Tracking
`PROGRESS.md` maintains real-time status of all phases

---

## Expected Outcomes

### Best Case Scenario
- 15-20 high-quality opportunities identified
- Correlation >0.8 (AI scores vs manual ratings)
- Pipeline proven reliable for production
- Clear development roadmap for next 3 months

### Acceptable Outcome
- 5-10 reasonable opportunities found
- Correlation >0.6
- Pipeline works but needs refinement
- Good foundation for iterative improvement

### Red Flags (Re-test Required)
- <5 opportunities with scores >50
- Poor correlation (<0.6) between AI and manual assessment
- Pipeline errors >10%
- No clear business value in identified opportunities

---

## After Testing

### If Successful → Production Deployment
1. **Scale Up**: Increase Reddit data processing (500-1000 posts/week)
2. **Automate**: Build monitoring and alerting
3. **Validate**: Cross-reference with market research
4. **Develop**: Start building first app opportunity

### If Needs Work → Improvement Cycle
1. **Debug**: Fix pipeline reliability issues
2. **Refine**: Adjust scoring algorithms based on findings
3. **Expand**: Test additional subreddit categories
4. **Repeat**: Run new validation cycle

---

## Troubleshooting

### Phase 1 Fails
- Check Reddit API credentials
- Verify database connectivity
- Review pipeline logs for errors
- Ensure virtual environment activated

### Phase 2 Low Scores
- Try different subreddits (more problem-focused)
- Review AI prompts for problem detection
- Check if scoring algorithm needs tuning

### Phase 3 Performance Issues
- Profile memory usage
- Check for database bottlenecks
- Review API rate limiting
- Consider batch size adjustments

### Phase 4 Poor Correlation
- Review top opportunities manually
- Check if scoring dimensions need adjustment
- Verify business model assumptions
- May need larger sample size

---

## Related Documentation

- **Framework**: `live-testing-framework.md` - Original solo developer testing approach
- **Progress**: `PROGRESS.md` - Real-time phase tracking
- **Migration Phases**: `.claude/commands/phase*-*.md` - Pattern reference
- **Project Memory**: Check memory for RedditHarbor business goals and scoring system

---

## Notes

- All phases use test mode to avoid production data mixing
- Database is NOT cleaned between phases (cumulative testing)
- Workspaces are temporary; reports are permanent
- Each phase builds on previous phase results
- Total testing time: ~5 hours across all phases

---

**Last Updated**: 2025-11-27
**Status**: Ready for execution
**Next Action**: Run `/live-test-phase1-smoke` to begin
