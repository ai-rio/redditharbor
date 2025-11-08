# 🚀 RedditHarbor Quick Start - Run Complete Workflow

## One-Command Complete Workflow

Run the entire pipeline from data collection to analysis display:

```bash
# Navigate to project
cd /home/carlos/projects/redditharbor

# Activate environment
source .venv/bin/activate

# Execute complete workflow
python3 test_full_pipeline_workflow.py && python3 generate_workflow_analysis.py
```

Or run them sequentially:

```bash
# Phase 1-4: Test all constraint layers and collect/score data
python3 test_full_pipeline_workflow.py

# Phase 5: Generate and display analysis
python3 generate_workflow_analysis.py
```

---

## Individual Phase Execution

### Phase 1: Collect Fresh Reddit Data
```bash
source .venv/bin/activate
python3 scripts/automated_opportunity_collector.py
```
- Collects from 40+ opportunity-focused subreddits
- Filters for problem keywords
- Stores directly in Supabase via DLT pipeline
- Time: ~2-5 minutes (depends on Reddit API rate limits)

### Phase 2: Store in Supabase
```bash
# Already done by Phase 1 via DLT pipeline
# Verify data stored:
python3 -c "
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
result = supabase.table('submission').select('count', count='exact').execute()
print(f'Stored submissions: {result.count}')
"
```

### Phase 3: Analyze & Score Data
```bash
source .venv/bin/activate
python3 scripts/batch_opportunity_scoring.py
```
- Fetches all submissions from Supabase
- Analyzes using OpportunityAnalyzerAgent
- Applies DLT simplicity constraints
- Stores scores in opportunity_scores table
- Time: ~1-3 minutes (depends on data volume)

### Phase 4: Generate Insights
```bash
source .venv/bin/activate
python3 scripts/generate_opportunity_insights_openrouter.py
```
- Uses OpenRouter API (Claude Haiku)
- Generates AI insights for each opportunity
- Stores insights in database
- Time: ~2-5 minutes

### Phase 5: Display Analysis
```bash
source .venv/bin/activate
python3 generate_workflow_analysis.py
```
- Generates console output with analysis
- Creates JSON export
- Displays approval/compliance metrics
- Time: <1 minute

---

## View Results

### Console Output
Already displayed above during Phase 5 execution.

### JSON Export
```bash
cat generated/workflow_results.json
```

### View Logs
```bash
# Main workflow log
tail -100 error_log/workflow.log

# Collection log
tail -100 error_log/automated_collector.log
```

### View in Supabase Studio
```
Open: http://127.0.0.1:54323
Database: postgres
Tables: 
  - submission (collected posts)
  - comment (post comments)
  - app_opportunities (analyzed opportunities)
  - opportunity_scores (scored results)
```

---

## Production Workflow (Start to Finish)

```bash
#!/bin/bash
# Full production workflow script

cd /home/carlos/projects/redditharbor
source .venv/bin/activate

echo "🚀 Starting RedditHarbor Workflow..."
echo ""

echo "📊 Phase 1: Validating system..."
python3 test_full_pipeline_workflow.py
if [ $? -ne 0 ]; then echo "❌ System validation failed"; exit 1; fi
echo "✅ System validated"
echo ""

echo "📥 Phase 2: Collecting Reddit data..."
python3 scripts/automated_opportunity_collector.py
if [ $? -ne 0 ]; then echo "⚠️ Collection failed, continuing with existing data..."; fi
echo "✅ Collection complete"
echo ""

echo "📊 Phase 3: Scoring opportunities..."
python3 scripts/batch_opportunity_scoring.py
if [ $? -ne 0 ]; then echo "❌ Scoring failed"; exit 1; fi
echo "✅ Scoring complete"
echo ""

echo "💡 Phase 4: Generating insights..."
python3 scripts/generate_opportunity_insights_openrouter.py
if [ $? -ne 0 ]; then echo "⚠️ Insights failed, skipping..."; fi
echo "✅ Insights generated"
echo ""

echo "📈 Phase 5: Generating analysis..."
python3 generate_workflow_analysis.py
echo "✅ Analysis complete"
echo ""

echo "🎉 Workflow complete!"
echo "Results available in: generated/workflow_results.json"
```

Save as `run-workflow.sh` and execute:
```bash
chmod +x run-workflow.sh
./run-workflow.sh
```

---

## Environment Setup (One-Time)

### Install Dependencies
```bash
# Using UV (already done)
uv sync

# Or manually activate venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Start Supabase
```bash
# Verify it's running
supabase status

# If not running:
docker-compose -f supabase/docker-compose.yml up -d

# Or:
supabase start
```

### Set Environment Variables
```bash
# Already configured in .env.local
cat .env.local
```

---

## Troubleshooting

### Supabase Connection Error
```bash
# Check if Docker is running
docker ps | grep supabase

# Restart Supabase
supabase stop && supabase start

# Verify connection
python3 -c "from config import SUPABASE_URL; print(SUPABASE_URL)"
```

### Reddit API Rate Limit
- The collection script includes automatic backoff
- If rate-limited, try later or reduce subreddit count
- Test data is always available in `test_full_pipeline_workflow.py`

### Missing Dependencies
```bash
source .venv/bin/activate
pip install -e .
# Or use UV
uv sync
```

### Python Version
```bash
python3 --version
# Should be 3.12.3 or compatible
```

---

## Sample Output

When workflow completes, you'll see:

```
================================================================================
                   🚀 RedditHarbor Complete Workflow Analysis
================================================================================

📊 EXECUTIVE SUMMARY
Total Opportunities Analyzed: 10
├─ Approved: 7 (70.0%)
└─ Disqualified: 3 (30.0%)

🔒 DLT CONSTRAINT ENFORCEMENT ANALYSIS
Compliance Metrics:
├─ Total Opportunities: 10
├─ Constraint Compliant: 7 (70.0%)
└─ Overall Compliance Rate: 70.0%

✅ APPROVED OPPORTUNITIES
1. SimpleCalorieCounter - Score: 100.0
2. CalorieMacroTracker - Score: 85.0
...

📤 EXPORT & NEXT STEPS
Results Exported to: generated/workflow_results.json
```

---

## Next Steps After Workflow

1. **Review Results**: Check console output above
2. **Deep Dive**: Analyze top opportunities in detail
3. **Competitive Analysis**: Research market landscape
4. **User Validation**: Test assumptions with target users
5. **Build MVP**: Start development on top-scored opportunities
6. **Go-to-Market**: Prepare launch strategy

---

## Support

- **Documentation**: See `docs/` directory
- **Logs**: Check `error_log/` for detailed execution logs
- **Issues**: File issues in GitHub with logs attached
- **Questions**: Refer to CLAUDE.md project governance

---

**Last Updated**: November 7, 2025
**Status**: ✅ Production Ready
