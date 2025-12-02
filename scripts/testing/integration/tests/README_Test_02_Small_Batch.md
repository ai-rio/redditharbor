# Test 02: Small Batch Validation

## Overview

Test 02 is a comprehensive small batch validation test for the RedditHarbor unified pipeline refactoring. It processes 5 submissions with varied quality levels to validate consistent behavior, cost-effective model performance, and proper error handling.

## Purpose

- **Batch Processing**: Validate that the pipeline can handle multiple submissions sequentially
- **Quality Variation**: Test behavior across high, medium, low quality submissions and edge cases
- **Cost Optimization**: Use cost-effective models and track actual costs
- **Memory Monitoring**: Ensure memory usage stays within acceptable limits
- **Consistency**: Verify consistent field coverage and service execution across submissions
- **Error Handling**: Test graceful degradation for problematic submissions

## Configuration

### Test Configuration File
- **Location**: `config/submissions_small_batch.json`
- **Contains**: 5 varied submissions with quality levels and expected outcomes

### Submission Types
1. **High Quality**: Good engagement, sufficient text content
2. **Medium Quality**: Moderate engagement, decent text
3. **Low Quality**: Minimal engagement, limited text
4. **Edge Case - Long Text**: Very long text content to test processing limits
5. **Edge Case - Minimal Data**: Minimal data to test validation scenarios

## Usage

### Basic Usage
```bash
# Run with basic settings (no monetization)
./run_test_02_small_batch.sh

# Or directly with Python
source .venv/bin/activate
python scripts/testing/integration/tests/test_02_small_batch.py
```

### Advanced Usage
```bash
# Enable MonetizationService (increases cost)
./run_test_02_small_batch.sh --monetization

# Update configuration with real submission IDs from database
./run_test_02_small_batch.sh --update-config

# Verbose logging for debugging
./run_test_02_small_batch.sh --verbose

# Continue even if memory limit is exceeded
./run_test_02_small_batch.sh --continue-on-memory-warning

# Combine options
./run_test_02_small_batch.sh --monetization --update-config --verbose
```

## Performance Optimizations

### Cost-Effective Settings
- **Model**: `meta-llama/llama-3.1-8b-instruct:floor` via OpenRouter
- **Market Validation**: Reduced search count (5 instead of 10)
- **Timeouts**: Optimized for batch processing (15s HTTP, 30s Agno)
- **Processing**: Sequential (not concurrent) for better monitoring

### Memory Management
- **Limit**: 1GB memory usage for batch processing
- **Monitoring**: Real-time memory tracking with psutil
- **Warnings**: Alerts when approaching memory limits
- **Cleanup**: Resource cleanup between submissions

## Success Criteria

### Primary Metrics
- **Completion Rate**: 100% (all submissions processed)
- **Average Field Coverage**: 75%+
- **Total Cost**: $0.50-$1.00
- **Processing Time**: 15 minutes max
- **Memory Usage**: Under 1GB

### Quality-Level Targets
- **High Quality**: 90%+ field coverage
- **Medium Quality**: 70-90% field coverage
- **Low Quality**: 50-70% field coverage
- **Edge Cases**: Graceful handling with appropriate error messages

## Output

### Console Output
- Real-time progress updates
- Per-submission processing results
- Memory usage monitoring
- Success/failure indicators
- Quality level analysis

### JSON Reports
- **Location**: `results/test_02_small_batch/run_YYYY-MM-DD_HH-MM-SS.json`
- **Contains**:
  - Complete batch metrics
  - Individual submission results
  - Service execution details
  - Cost breakdown
  - Memory usage summary
  - Success criteria evaluation

### Key Report Sections
```json
{
  "batch_summary": {
    "total_submissions": 5,
    "successful_submissions": 5,
    "success_rate": 100.0,
    "total_cost": 0.75,
    "avg_field_coverage": 82.5,
    "batch_processing_time": 245.7,
    "memory_summary": {
      "peak_memory_mb": 512.3,
      "within_limit": true
    }
  },
  "quality_analysis": {
    "high": { "count": 2, "successful": 2, "avg_coverage": 91.2 },
    "medium": { "count": 1, "successful": 1, "avg_coverage": 78.5 },
    "low": { "count": 1, "successful": 1, "avg_coverage": 65.3 },
    "edge": { "count": 1, "successful": 1, "avg_coverage": 70.1 }
  }
}
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Verify dependencies
python -c "from supabase import create_client; print('OK')"
```

#### Database Connection
```bash
# Check Supabase is running
docker ps | grep supabase

# Test database connection
docker exec -i supabase_db_redditharbor-core-functions-fix psql -U postgres -d postgres -c "SELECT COUNT(*) FROM submissions;"
```

#### Memory Issues
- Use `--continue-on-memory-warning` if memory limit is too restrictive
- Monitor memory usage during execution
- Consider reducing batch size if consistently hitting limits

#### Cost Overruns
- Run without `--monetization` flag to reduce costs
- Check OpenRouter API usage and limits
- Verify model pricing in configuration

### Debug Mode
```bash
# Enable verbose logging for detailed troubleshooting
./run_test_02_small_batch.sh --verbose

# Check environment variables
env | grep -E "(OPENROUTER|SUPABASE|LITELLM)"
```

## Database Integration

### Configuration Update
The `--update-config` flag queries the database for real submissions matching quality criteria:
- High quality: Submissions with good scores and substantial text
- Medium quality: Submissions with moderate engagement
- Low quality: Submissions with minimal data
- Edge cases: Submissions with unusual characteristics

### Query Logic
```sql
-- High quality example
SELECT submission_id, title, subreddit, reddit_score, num_comments, content
FROM submissions
WHERE reddit_score >= 20 AND content IS NOT NULL
ORDER BY reddit_score DESC LIMIT 5;
```

## Cost Analysis

### Expected Costs (per run)
- **Basic run** (no monetization): $0.50-$0.75
- **With monetization**: $0.75-$1.00
- **Cost breakdown**:
  - Profiler Service: ~$0.15 per submission
  - Opportunity Service: ~$0.05 per submission
  - Trust Service: ~$0.03 per submission
  - Market Validation: ~$0.08 per submission
  - Monetization Service: ~$0.25 per submission (if enabled)

### Cost Control
- Uses floor pricing model via OpenRouter
- Reduced search counts for market validation
- Sequential processing to avoid concurrent API calls
- Optional monetization service for cost savings

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run Test 02 Small Batch
  run: |
    cd scripts/testing/integration
    ./run_test_02_small_batch.sh --update-config
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
```

### Quality Gates
- Must meet all success criteria for pipeline to pass
- Automatic report generation for review
- Cost tracking to prevent overruns
- Memory limits to prevent resource exhaustion

## Next Steps

1. **Baseline Establishment**: Run test to establish performance baseline
2. **Comparison**: Compare results with Test 01 single submission metrics
3. **Optimization**: Tune configuration based on batch results
4. **Scaling**: Use insights for larger batch processing
5. **Monitoring**: Set up ongoing batch processing monitoring

## Related Files

- `test_01_single_submission_optimized.py` - Single submission test
- `config/submissions_small_batch.json` - Batch configuration
- `../utils/` - Testing utilities and metrics
- `../config/` - Service and observability configurations