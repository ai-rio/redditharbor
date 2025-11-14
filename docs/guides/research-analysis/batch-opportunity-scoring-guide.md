# Batch Opportunity Scoring Guide

## Overview

The Batch Opportunity Scoring system processes Reddit submissions from the Supabase database and scores them using the 5-dimensional opportunity analysis methodology.

**Location**: `/home/carlos/projects/redditharbor/scripts/batch_opportunity_scoring.py`

## Features

- Processes 6,127+ submissions automatically
- Maps submissions to 6 business sectors
- Scores using 5-dimensional methodology (Market Demand, Pain Intensity, Monetization Potential, Market Gap, Technical Feasibility)
- Stores results in normalized database schema
- Provides comprehensive progress tracking and reporting
- Handles errors gracefully and continues processing

## Quick Start

### Prerequisites

1. Supabase instance running locally or remotely
2. Database populated with Reddit submissions
3. Python environment with required dependencies

### Running the Script

```bash
# Standard execution
python3 scripts/batch_opportunity_scoring.py

# Or with UV
uv run python3 scripts/batch_opportunity_scoring.py
```

### Running Tests

Before processing all submissions, validate the setup:

```bash
python3 scripts/test_batch_scoring.py
```

## Architecture

### Data Flow

```
submissions table
    ↓
fetch_submissions()
    ↓
format_submission_for_agent()
    ↓
OpportunityAnalyzerAgent.analyze_opportunity()
    ↓
create_opportunity_record()
    ↓
store_opportunity_score()
    ↓
opportunities + opportunity_scores tables
```

### Database Schema

#### Input: `submissions` Table

Fields used:
- `id` (UUID) - Primary key
- `submission_id` - Reddit ID
- `title` - Submission title
- `selftext` - Body text
- `subreddit` - Source subreddit
- `score` - Upvotes
- `num_comments` - Comment count
- `sentiment_score` - Pre-calculated sentiment
- `problem_keywords` - Identified problems
- `solution_mentions` - Mentioned solutions

#### Output: `opportunities` Table

Created records:
- `id` (UUID) - Generated
- `problem_statement` - Extracted from title
- `identified_from_submission_id` - Links to submission
- `market_segment` - Mapped sector
- `status` - "identified"
- `target_audience` - Subreddit name
- `last_reviewed_at` - Timestamp

#### Output: `opportunity_scores` Table

Scoring data:
- `opportunity_id` - Links to opportunity
- `market_demand_score` (0-100)
- `pain_intensity_score` (0-100)
- `monetization_potential_score` (0-100)
- `market_gap_score` (0-100)
- `technical_feasibility_score` (0-100)
- `simplicity_score` (0-100, default 70)
- `total_score` - Auto-calculated weighted score
- `score_date` - Timestamp
- `scoring_notes` - JSON metadata

## Business Sectors

### Sector Mapping

The script maps 78 subreddits to 6 business sectors:

1. **Health & Fitness** (20 subreddits)
   - fitness, loseit, bodyweightfitness, nutrition, keto, yoga, running, etc.

2. **Finance & Investing** (17 subreddits)
   - personalfinance, investing, stocks, bogleheads, fire, etc.

3. **Education & Career** (11 subreddits)
   - learnprogramming, cscareerquestions, careerguidance, jobs, etc.

4. **Travel & Experiences** (11 subreddits)
   - travel, solotravel, digitalnomad, backpacking, etc.

5. **Real Estate** (10 subreddits)
   - realestate, firsttimehomebuyer, homeimprovement, landlord, etc.

6. **Technology & SaaS** (9 subreddits + default)
   - saas, indiehackers, microsaas, nocode, webdev, etc.

**Default**: Unmapped subreddits default to "Technology & SaaS"

## Scoring Methodology

### 5-Dimensional Scoring

1. **Market Demand** (20% weight)
   - Discussion Volume: Upvotes analysis
   - Engagement Rate: Comments/upvotes ratio
   - Trend Velocity: Growth keywords
   - Audience Size: Subreddit popularity

2. **Pain Intensity** (25% weight)
   - Negative Sentiment: Frustration keywords
   - Emotional Language: Urgency indicators
   - Repetition Rate: Comment complaints
   - Workaround Complexity: Manual process indicators

3. **Monetization Potential** (30% weight)
   - Willingness to Pay: Payment signals
   - Commercial Gaps: Market gap indicators
   - B2B vs B2C: Business model hints
   - Revenue Model: Subscription/pricing signals

4. **Market Gap** (15% weight)
   - Competition Density: Existing solutions
   - Solution Inadequacy: Feature gaps
   - Innovation Opportunities: Unmet needs

5. **Technical Feasibility** (10% weight)
   - Development Complexity: Technical requirements
   - Simple Solution Indicators: Easy to build signals
   - API Integration Needs: External dependencies

### Priority Classification

- **High Priority** (85+): Immediate pursuit
- **Med-High Priority** (70-84): Strong candidate
- **Medium Priority** (55-69): Worth exploring
- **Low Priority** (40-54): Low potential
- **Not Recommended** (<40): Skip

## Performance

### Processing Rates

- **Batch Size**: 100 submissions per batch
- **Expected Rate**: 2-5 submissions/second
- **Total Time**: ~20-50 minutes for 6,127 submissions

### Progress Tracking

The script provides:
- Real-time progress bar with tqdm
- Batch-by-batch processing status
- Error logging without stopping execution
- Incremental database storage (per batch)

## Output Report

### Summary Statistics

```
Processing Statistics:
  Total Submissions:     6,127
  Successfully Scored:   6,100
  Failed:                27
  Success Rate:          99.6%
  Total Time:            1,234.56 seconds
  Average Time/Item:     0.201 seconds
  Processing Rate:       4.96 items/second
```

### Score Distribution

```
Score Distribution:
  High Priority (85+):   234 (3.8%)
  Med-High (70-84):      891 (14.6%)
  Medium (55-69):        1,456 (23.9%)
  Low (40-54):           2,134 (35.0%)
  Not Recommended (<40): 1,385 (22.7%)
```

### Dimension Averages

```
Average Dimension Scores:
  Market Demand:         52.3/100
  Pain Intensity:        45.7/100
  Monetization:          38.9/100
  Market Gap:            48.2/100
  Technical Feasibility: 65.4/100
  Final Score:           48.1/100
```

### Sector Breakdown

```
Opportunities by Sector:
  Finance & Investing     2,145 (35.2%)
  Health & Fitness        1,823 (29.9%)
  Technology & SaaS       987 (16.2%)
  Education & Career      654 (10.7%)
  Real Estate            312 (5.1%)
  Travel & Experiences   179 (2.9%)
```

### Top Opportunities

```
Top 10 Opportunities:
   1. [92.3] r/personalfinance     Simple budgeting app for tracking irregular income
   2. [91.8] r/fitness              Workout form checker using phone camera
   3. [89.5] r/investing            Real-time portfolio rebalancing tool
   ...
```

## Error Handling

### Error Types

1. **Submission Processing Errors**
   - Logged but don't stop execution
   - Error entry added to results with score 0
   - Batch continues with remaining items

2. **Database Errors**
   - Opportunity creation failures logged
   - Score storage failures logged
   - Script continues with next submission

3. **Connection Errors**
   - Fatal errors stop execution immediately
   - Clear error messages with troubleshooting hints

### Error Recovery

- Each batch is independent
- Failed submissions can be reprocessed
- Upsert logic prevents duplicates

## Querying Results

### Get Top Opportunities

```sql
SELECT
    o.problem_statement,
    o.market_segment,
    os.total_score,
    os.market_demand_score,
    os.pain_intensity_score,
    os.monetization_potential_score
FROM opportunities o
JOIN opportunity_scores os ON o.id = os.opportunity_id
WHERE os.total_score >= 70
ORDER BY os.total_score DESC
LIMIT 10;
```

### Sector Analysis

```sql
SELECT
    market_segment,
    COUNT(*) as opportunity_count,
    AVG(os.total_score) as avg_score,
    MAX(os.total_score) as max_score
FROM opportunities o
JOIN opportunity_scores os ON o.id = os.opportunity_id
GROUP BY market_segment
ORDER BY avg_score DESC;
```

### Find High-Priority by Dimension

```sql
SELECT
    o.problem_statement,
    os.total_score,
    os.monetization_potential_score as monetization
FROM opportunities o
JOIN opportunity_scores os ON o.id = os.opportunity_id
WHERE os.monetization_potential_score >= 70
ORDER BY monetization DESC
LIMIT 20;
```

## Troubleshooting

### Common Issues

1. **"No submissions found"**
   - Verify database connection
   - Check submissions table has data
   - Confirm SUPABASE_URL and SUPABASE_KEY in config

2. **Import errors**
   - Run from project root directory
   - Verify all dependencies installed: `uv sync`
   - Check Python path includes project root

3. **Slow processing**
   - Normal for large datasets
   - Check network connection to Supabase
   - Consider running on server with better connection

4. **tqdm not found**
   - Script auto-installs on first run
   - Or manually: `pip install tqdm`

### Debug Mode

To debug specific submissions:

```python
# In batch_opportunity_scoring.py
# Add print statements in process_batch():
print(f"Processing submission: {submission.get('submission_id')}")
print(f"Formatted data: {formatted}")
print(f"Analysis result: {analysis}")
```

## Extending the Script

### Adding New Sectors

Edit `SECTOR_MAPPING` dictionary:

```python
SECTOR_MAPPING = {
    # ... existing mappings ...
    "newsubreddit": "New Sector Name",
}
```

### Custom Filtering

Add filtering in `fetch_submissions()`:

```python
# Filter by date
query = query.gte("created_utc", "2024-01-01")

# Filter by subreddit
query = query.in_("subreddit", ["fitness", "personalfinance"])

# Filter by engagement
query = query.gte("score", 50)
```

### Batch Size Tuning

Adjust for your system:

```python
# Larger batches = fewer database calls, more memory
batch_size = 200  # Default is 100

# Smaller batches = more database calls, less memory
batch_size = 50
```

## Integration

### With Marimo Dashboard

Results automatically available in:
- `/home/carlos/projects/redditharbor/analysis/marimo_dashboard.py`
- Query opportunity_scores table
- Filter by sector, score ranges, etc.

### With Research Templates

Use scored opportunities in:
- `core/templates.py` research workflows
- Filter high-priority opportunities
- Generate validation reports

### With Agent Tools

Results feed into:
- `agent_tools/opportunity_analyzer_agent.py`
- `agent_tools/market_validator_agent.py`
- Cross-platform validation workflows

## Best Practices

1. **Run Tests First**: Always run `test_batch_scoring.py` before full batch
2. **Monitor Progress**: Keep terminal visible to track progress
3. **Review Errors**: Check error logs after completion
4. **Validate Results**: Spot-check high-priority opportunities
5. **Rerun as Needed**: Script uses upsert - safe to rerun

## Next Steps

After scoring:

1. **Review Top Opportunities**
   ```sql
   SELECT * FROM opportunity_scores WHERE total_score >= 85;
   ```

2. **Analyze by Sector**
   - Identify strongest sectors
   - Focus validation efforts

3. **Cross-Platform Validation**
   - Use Market Validator Agent
   - Check Twitter, LinkedIn, Product Hunt

4. **Create Research Briefs**
   - Use high-priority opportunities
   - Generate detailed analysis reports

5. **Track Metrics**
   - Monitor validation success rates
   - Measure time-to-market
   - Track revenue potential

## Related Documentation

- [OpportunityAnalyzerAgent Documentation](../api/opportunity-analyzer-agent.md)
- [Database Schema Guide](../architecture/database-schema.md)
- [Research Methodology](../architecture/research-methodology.md)
- [Marimo Dashboard Guide](./marimo-dashboard-guide.md)

## Support

For issues or questions:
- Check logs in `error_log/` directory
- Review test output from `test_batch_scoring.py`
- Verify database schema matches expectations
- Consult project maintainers

---

**Last Updated**: 2025-11-05
**Script Version**: 1.0
**Compatible with**: RedditHarbor v1.0.0
