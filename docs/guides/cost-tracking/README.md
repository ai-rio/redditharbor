# Cost Tracking Documentation

Comprehensive guides for monitoring and analyzing LLM API costs in RedditHarbor's AI enrichment pipeline.

## Overview

RedditHarbor implements cost tracking for all LLM operations through:
- LiteLLM unified API integration
- AgentOps observability layer
- Database-persisted cost metrics
- Analytics views and queries

## Documentation

- **[Deployment Guide](./deployment-guide.md)** - Complete setup and deployment instructions
- **[Analytics Guide](./analytics-guide.md)** - Cost monitoring and analysis patterns
- **[SQL Queries](./sql-queries.md)** - Ready-to-use queries for cost analysis

## Key Features

### Real-time Tracking
- Token usage per request
- Cost calculation per model
- Provider-specific pricing

### Analytics
- Daily/weekly/monthly cost summaries
- Cost per opportunity analysis
- Model performance comparisons
- Budget monitoring and alerts

### Database Schema

Cost data is stored in the `workflow_results` table with additional columns:
- `tokens_input` - Input tokens used
- `tokens_output` - Output tokens generated
- `cost_usd` - Total cost in USD
- `model_used` - LLM model identifier
- `provider` - API provider (OpenRouter, etc.)

## Quick Start

```sql
-- View daily costs
SELECT * FROM cost_tracking_daily_summary;

-- Get cost per opportunity
SELECT * FROM cost_per_opportunity_analysis;

-- Monitor budget usage
SELECT * FROM cost_budget_monitoring;
```

## Related Documentation

- [AgentOps Integration](../../integrations/agentops/) - Agent observability and tracking
- [Architecture Overview](../../architecture/) - System design decisions
