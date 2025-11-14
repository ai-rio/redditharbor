# Subagent-Based Opportunity Scoring Implementation Guide

**Last Updated:** 2025-11-05
**Status:** Ready for Implementation

## Overview

This guide provides step-by-step instructions for implementing the subagent-based opportunity scoring pipeline that processes 6,127 Reddit submissions to identify monetizable app opportunities.

## Prerequisites

- ✅ RedditHarbor database with 6,127 enhanced submissions
- ✅ Supabase running locally (port 54321-54323)
- ✅ Python environment with UV package manager
- ✅ Marimo installed and working
- ✅ OpportunityAnalyzerAgent implemented (`agent_tools/opportunity_analyzer_agent.py`)

## Architecture Summary

The implementation uses **4 specialized subagents** working in phases:

1. **data-engineer** → Creates database schema
2. **python-pro** → Builds batch scoring script
3. **marimo-specialist** → Creates interactive dashboard
4. **data-scientist** → Generates insights and reports

Full architecture: [subagent-based-opportunity-scoring.md](../architecture/subagent-based-opportunity-scoring.md)

## Implementation Workflow

### Phase 1: Database Infrastructure (10-15 min)

**Subagent:** `supabase-toolkit:data-engineer` or `data-engineer`

**Task Description:**
```
Create a Supabase migration for the opportunity_analysis table with the following schema:

Fields needed:
- id (BIGSERIAL PRIMARY KEY)
- submission_id (TEXT, foreign key to submission table)
- opportunity_id (TEXT UNIQUE)
- title (TEXT)
- subreddit (TEXT)
- sector (TEXT) - one of: Health & Fitness, Finance & Investing, Education & Career, Travel & Experiences, Real Estate, Technology & SaaS
- market_demand (NUMERIC(5,2)) - score 0-100
- pain_intensity (NUMERIC(5,2)) - score 0-100
- monetization_potential (NUMERIC(5,2)) - score 0-100
- market_gap (NUMERIC(5,2)) - score 0-100
- technical_feasibility (NUMERIC(5,2)) - score 0-100
- simplicity_score (NUMERIC(5,2)) - score 0-100
- final_score (NUMERIC(5,2)) - weighted average of dimensions
- priority (TEXT) - 🔥 High Priority, ⚡ Med-High Priority, etc.
- scored_at (TIMESTAMPTZ DEFAULT NOW())

Add indexes on: sector, final_score, priority, scored_at

Create the migration file in supabase/migrations/ and apply it.
```

**Expected Output:**
- `supabase/migrations/[timestamp]_opportunity_scoring_tables.sql`
- Migration applied successfully
- Table visible in Supabase Studio

---

### Phase 2: Batch Scoring Script (15-20 min)

**Subagent:** `python-pro`

**Task Description:**
```
Create scripts/batch_opportunity_scoring.py that:

1. Imports the OpportunityAnalyzerAgent from agent_tools/opportunity_analyzer_agent.py
2. Connects to Supabase using config (SUPABASE_URL, SUPABASE_KEY)
3. Fetches all submissions from the submission table with:
   - submission_id, title, selftext, subreddit, score, num_comments
   - sentiment_score, problem_keywords, solution_mentions
4. Maps subreddits to sectors:
   - Health & Fitness: fitness, loseit, bodyweightfitness, nutrition, etc.
   - Finance & Investing: personalfinance, financialindependence, investing, etc.
   - Education & Career: learnprogramming, cscareerquestions, etc.
   - Travel & Experiences: travel, solotravel, digitalnomad, etc.
   - Real Estate: realestate, firsttimehomebuyer, etc.
   - Technology & SaaS: saas, startups, entrepreneur, etc.
5. Processes submissions in batches of 100
6. Uses OpportunityAnalyzerAgent.analyze_opportunity() for each submission
7. Stores results in opportunity_analysis table
8. Adds progress logging (every 100 submissions)
9. Handles errors gracefully with try/except
10. Reports final statistics (total processed, errors, time taken)

Follow Python best practices:
- Type hints for all functions
- Comprehensive docstrings
- Error handling with logging
- Progress bar using tqdm
- Clean code structure

Use the existing OpportunityAnalyzerAgent scoring logic - do not reimplement it.
```

**Expected Output:**
- `scripts/batch_opportunity_scoring.py`
- Script runs successfully: `python scripts/batch_opportunity_scoring.py`
- 6,127 opportunities scored and stored
- Processing time: ~15-20 minutes

**Test Command:**
```bash
cd /home/carlos/projects/redditharbor
source .venv/bin/activate
python scripts/batch_opportunity_scoring.py
```

---

### Phase 3: Interactive Dashboard (20-25 min)

**Subagent:** `marimo-specialist`

**Task Description:**
```
Create marimo_notebooks/top_contenders_dashboard.py with the following features:

1. **Database Connection**
   - Use marimo_notebooks/config.py for Supabase credentials
   - Use marimo_notebooks/utils.py DatabaseConnector

2. **UI Controls (Interactive)**
   - Sector dropdown: All sectors + "All Sectors" option
   - Score range slider: 0-100 (default: 70-100)
   - Top N selector: 10, 20, 50, 100 (default: 20)
   - Simplicity filter checkbox: "Only show 1-3 function apps"

3. **Data Loading**
   - Query opportunity_analysis table based on filters
   - Sort by final_score DESC
   - Limit to Top N

4. **Visualizations**
   - Score distribution histogram (by sector if filtered)
   - Top opportunities table (interactive with marimo.ui.table)
   - Dimension breakdown radar/bar chart for top 5
   - Priority distribution pie chart
   - Sector comparison bar chart (average scores)

5. **Summary Stats**
   - Total opportunities meeting criteria
   - Average score
   - Top sector by average score
   - Highest scoring opportunity details

6. **Export Functionality**
   - Export button to download results as JSON
   - Export button to download results as CSV

Follow marimo best practices:
- Use anonymous functions: def _(mo):
- UI elements as last expression in cells
- Reactive updates when filters change
- Clean cell structure (9-12 cells total)
- Proper imports in first cell

Reference existing dashboards for patterns:
- simple_opportunity_dashboard.py
- opportunity_insights_dashboard.py
```

**Expected Output:**
- `marimo_notebooks/top_contenders_dashboard.py`
- Dashboard launches: `marimo run marimo_notebooks/top_contenders_dashboard.py --port 8895`
- All filters work reactively
- Charts render correctly
- Export functions work

**Test Command:**
```bash
cd /home/carlos/projects/redditharbor
uv run marimo run marimo_notebooks/top_contenders_dashboard.py --host 0.0.0.0 --port 8895
```

---

### Phase 4: Analytics & Insights (15-20 min)

**Subagent:** `data-scientist` or `data-analyst`

**Task Description:**
```
Create scripts/generate_opportunity_insights.py that:

1. **Statistical Validation**
   - Calculate correlation between dimension scores
   - Validate scoring distribution (normal, skewed, etc.)
   - Identify outliers (scores > 2 std dev from mean)
   - Test correlation: sentiment_score vs pain_intensity
   - Test correlation: engagement vs market_demand

2. **Sector Analysis**
   - Calculate average scores per sector
   - Identify top sector by:
     - Average final score
     - Number of high-priority opportunities
     - Monetization potential
   - Compare sector distributions

3. **Top Contenders Report**
   - Extract top 20 opportunities per sector (120 total)
   - Include all dimension scores
   - Add submission metadata (title, subreddit, engagement)
   - Calculate "opportunity quality" score

4. **Insights Generation**
   - Identify scoring patterns
   - Highlight notable anomalies
   - Suggest validation priorities
   - Recommend development sequence

5. **Export Results**
   - JSON: Top 20 per sector with full metadata
   - CSV: Flattened format for spreadsheet analysis
   - Markdown: Insights report for documentation

Output files:
- generated/top_contenders_by_sector.json
- generated/top_contenders_export.csv
- docs/research/opportunity_insights_report.md

Use pandas, numpy, scipy for statistical analysis.
Add visualizations using matplotlib/seaborn (saved as PNG in docs/assets/).
```

**Expected Output:**
- `scripts/generate_opportunity_insights.py`
- JSON export with top 120 opportunities
- CSV export for spreadsheet analysis
- Insights markdown report
- Statistical validation charts (PNG)

**Test Command:**
```bash
cd /home/carlos/projects/redditharbor
source .venv/bin/activate
python scripts/generate_opportunity_insights.py
```

---

## Execution Plan

### Option A: Sequential Execution

Run each phase one at a time, verify results before proceeding:

```bash
# Phase 1: Create database schema
# (Launch data-engineer subagent)

# Verify table exists
docker exec supabase_db_carlos psql -U postgres -d postgres -c "\d opportunity_analysis"

# Phase 2: Run batch scoring
# (Launch python-pro subagent)

# Verify data written
docker exec supabase_db_carlos psql -U postgres -d postgres -c "SELECT COUNT(*) FROM opportunity_analysis"

# Phase 3: Create dashboard
# (Launch marimo-specialist subagent)

# Test dashboard
uv run marimo run marimo_notebooks/top_contenders_dashboard.py --port 8895

# Phase 4: Generate insights
# (Launch data-scientist subagent)

# Review outputs
ls -la generated/top_contenders*
cat docs/research/opportunity_insights_report.md
```

### Option B: Parallel Execution (Faster)

Launch Phase 1 & 2 simultaneously:

```bash
# Launch both subagents at once
# - data-engineer: Creates schema
# - python-pro: Builds script (can test with mock data)

# Once table exists, python-pro can write real data
# Then proceed with Phase 3 & 4 sequentially
```

---

## Validation Checklist

After each phase, verify:

### ✅ Phase 1 Complete
- [ ] Migration file created in `supabase/migrations/`
- [ ] Migration applied successfully
- [ ] Table `opportunity_analysis` exists in database
- [ ] Indexes created on key columns
- [ ] Foreign key constraint to `submission` table works

### ✅ Phase 2 Complete
- [ ] Script `scripts/batch_opportunity_scoring.py` exists
- [ ] Script runs without errors
- [ ] 6,127 opportunities scored (or close to it)
- [ ] Data written to `opportunity_analysis` table
- [ ] Progress logging works
- [ ] Error handling tested

### ✅ Phase 3 Complete
- [ ] Dashboard `marimo_notebooks/top_contenders_dashboard.py` exists
- [ ] Dashboard loads without errors
- [ ] All filters work reactively
- [ ] Charts render correctly
- [ ] Table displays opportunity data
- [ ] Export buttons work

### ✅ Phase 4 Complete
- [ ] Script `scripts/generate_opportunity_insights.py` exists
- [ ] JSON export created in `generated/`
- [ ] CSV export created in `generated/`
- [ ] Insights report in `docs/research/`
- [ ] Statistical validation charts saved
- [ ] Top 20 per sector identified

---

## Troubleshooting

### Issue: Supabase connection fails

**Solution:**
```bash
# Check Supabase is running
supabase status

# Start if not running
supabase start

# Verify connection
docker exec supabase_db_carlos psql -U postgres -d postgres -c "SELECT 1"
```

### Issue: OpportunityAnalyzerAgent import error

**Solution:**
```bash
# Ensure agent_tools/ is importable
cd /home/carlos/projects/redditharbor
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "from agent_tools.opportunity_analyzer_agent import OpportunityAnalyzerAgent; print('OK')"
```

### Issue: Marimo dashboard doesn't display

**Solution:**
- Check for anonymous function pattern: `def _(mo):`
- Ensure UI elements are last expression in cell
- Hard refresh browser: Ctrl+Shift+R
- Check marimo console for errors

### Issue: Batch scoring is slow

**Solution:**
- Reduce batch size from 100 to 50
- Add database connection pooling
- Use bulk insert instead of individual inserts
- Check Supabase resource usage

---

## Expected Timeline

| Phase | Subagent | Time Estimate | Can Run Parallel? |
|-------|----------|---------------|-------------------|
| Phase 1 | data-engineer | 10-15 min | Yes (with Phase 2) |
| Phase 2 | python-pro | 15-20 min | Yes (with Phase 1) |
| Phase 3 | marimo-specialist | 20-25 min | No (needs Phase 2) |
| Phase 4 | data-scientist | 15-20 min | No (needs Phase 2) |
| **Total** | | **60-80 min** | **40-50 min with parallel** |

---

## Success Criteria

✅ **Database:**
- opportunity_analysis table created with proper schema
- All indexes and constraints in place
- Table queryable from Supabase Studio

✅ **Batch Scoring:**
- All 6,127 submissions processed
- Success rate > 99%
- Average processing time < 0.3 sec/submission
- Results stored in database

✅ **Dashboard:**
- Loads in < 3 seconds
- All filters work reactively
- Charts render without errors
- Export functions produce valid files

✅ **Insights:**
- Top 120 opportunities identified (20 per sector)
- Statistical validation complete
- Insights report generated
- Recommendations actionable

---

## Next Steps After Implementation

1. **Review Top Contenders** - Manually review top 20 per sector
2. **Validate Methodology** - Compare scores to manual assessment
3. **Refine Scoring** - Adjust dimension weights if needed
4. **Agent SDK Deep Dive** - Use Agent SDK for top 50 detailed analysis
5. **Simplicity Enforcement** - Validate 1-3 function constraint
6. **Opportunity Selection** - Choose 3-5 for further validation
7. **Market Validation** - Cross-platform research (Twitter, LinkedIn)

---

## Related Documentation

- [Architecture Decision](../architecture/subagent-based-opportunity-scoring.md)
- [Monetizable App Methodology](../methodology/monetizable-app-research-methodology.md)
- [OpportunityAnalyzerAgent Reference](../../agent_tools/opportunity_analyzer_agent.py)
- [Marimo Integration](../../.serena/memories/redditharbor_marimo_integration_complete.md)
- [Enhanced Collection Implementation](../implementation/monetizable-collection-implementation.md)

---

## Questions?

If you encounter issues or have questions:

1. Check the troubleshooting section above
2. Review the architecture document
3. Verify prerequisites are met
4. Check Supabase and database connectivity
5. Review subagent output for specific errors
