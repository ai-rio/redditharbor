# Agno Cost Tracking Setup Guide

## Overview

This guide explains how to configure cost tracking for Agno agents in the RedditHarbor Pipeline v3. Cost tracking integration with AgentOps provides visibility into agent operation costs and helps optimize resource usage.

## Required Configuration

To enable cost tracking for Agno agents, ensure the following configurations are set in your environment:

### 1. AGNO_TRACK_COSTS

**Purpose**: Controls whether cost tracking is enabled for Agno agent operations

**Configuration in settings.py**:
```python
agno_track_costs: bool = Field(
    default=True,
    alias="AGNO_TRACK_COSTS",
    description="Enable cost tracking for Agno agent operations"
)
```

**Environment Variable**:
```bash
# Enable cost tracking (default)
export AGNO_TRACK_COSTS=true

# Disable cost tracking
export AGNO_TRACK_COSTS=false
```

### 2. AGNO_ENABLE_AGENTOPS

**Purpose**: Enables AgentOps integration for comprehensive observability

**Configuration in settings.py**:
```python
agno_enable_agentops: bool = Field(
    default=False,
    alias="AGNO_ENABLE_AGENTOPS",
    description="Enable AgentOps tracking for Agno agents"
)
```

**Environment Variable**:
```bash
# Enable AgentOps tracking
export AGNO_ENABLE_AGENTOPS=true
```

### 3. AGNO_DEBUG_MODE

**Purpose**: Enables detailed logging for debugging Agno agent operations

**Configuration in settings.py**:
```python
agno_debug_mode: bool = Field(
    default=False,
    alias="AGNO_DEBUG_MODE",
    description="Enable debug mode for enhanced Agno agent logging"
)
```

**Environment Variable**:
```bash
# Enable debug mode
export AGNO_DEBUG_MODE=true
```

## Complete Configuration Example

Create or update your `.env.local` file with the following configurations:

```bash
# AgentOps and Cost Tracking Configuration
AGENTOPS_API_KEY=your_agentops_api_key_here
AGENTOPS_PROJECT_NAME=redditharbor-agno
AGENTOPS_ENABLED=true

# Agno Agent Configuration
AGNO_ENABLE_AGENTOPS=true
AGNO_TRACK_COSTS=true
AGNO_DEBUG_MODE=true

# OpenRouter Configuration (for cost-optimized LLM calls)
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=anthropic/claude-haiku-4.5
```

## Cost Tracking Features

When `AGNO_TRACK_COSTS=true`, the system will:

1. **Track Agent Operation Costs**: Monitor the cost of each agent execution
2. **Aggregate Cost Data**: Sum costs across multiple operations
3. **Provide Cost Breakdowns**: Show costs by agent type and operation
4. **Integrate with AgentOps**: Send cost data to AgentOps dashboard
5. **Generate Cost Reports**: Create detailed cost analysis reports

## Usage in Code

### Checking Cost Tracking Status

```python
from config.settings import get_settings

settings = get_settings()

# Check if cost tracking is enabled
if settings.agno_track_costs:
    print("Cost tracking is enabled for Agno agents")
else:
    print("Cost tracking is disabled")
```

### Initializing Agno Analyzer with Cost Tracking

```python
from transform.agno_analyzer import AgnoOpportunityAnalyzer

analyzer = AgnoOpportunityAnalyzer(
    enable_agentops=True,  # Enable AgentOps integration
    track_costs=True      # Enable cost tracking
)

# The analyzer will now track costs for all operations
results = analyzer.analyze_submissions(submissions)

# Get cost summary
cost_summary = analyzer.get_cost_summary()
print(f"Total cost: ${cost_summary.total_cost:.4f}")
```

### Cost Monitoring

```python
# Monitor costs during operation
from monitoring.cost_tracker import CostTracker

cost_tracker = CostTracker()

# Track individual costs
cost_tracker.track_cost(0.05, "willingness_to_pay_agent")
cost_tracker.track_cost(0.04, "market_segment_agent")
cost_tracker.track_cost(0.03, "price_point_agent")
cost_tracker.track_cost(0.04, "payment_behavior_agent")

# Get total cost
total_cost = cost_tracker.get_total_cost()
print(f"Total analysis cost: ${total_cost:.4f}")
```

## Cost Optimization

The system provides several ways to optimize costs:

1. **Model Selection**: Use cost-effective models via OpenRouter
   - Claude Haiku 4.5: ~$0.0004 per agent
   - GPT-4o-mini: ~$0.0003 per agent
   - Gemini Flash 1.5: ~$0.0002 per agent

2. **Selective Deployment**: Only run full analysis on high-confidence submissions
3. **Batch Processing**: Process submissions in batches for efficiency
4. **Caching**: Cache results for repeated queries (especially with Jina integration)

## Troubleshooting

### Cost Tracking Not Working

1. **Verify Configuration**:
   ```bash
   echo $AGNO_TRACK_COSTS
   # Should output: true
   ```

2. **Check Settings**:
   ```python
   from config.settings import get_settings
   settings = get_settings()
   print(f"AGNO_TRACK_COSTS: {settings.agno_track_costs}")
   ```

3. **Enable Debug Mode**:
   ```bash
   export AGNO_DEBUG_MODE=true
   # Check logs for cost tracking messages
   ```

### High Costs

1. **Check Model Configuration**:
   - Ensure you're using OpenRouter, not direct OpenAI API
   - Verify model selection (Haiku vs Sonnet vs Opus)

2. **Review Agent Usage**:
   - Check if all agents are necessary for each analysis
   - Consider selective deployment for low-value submissions

3. **Monitor in AgentOps Dashboard**:
   - Identify expensive operations
   - Track cost trends over time

## Best Practices

1. **Always enable cost tracking** in production environments
2. **Set daily cost limits** to prevent unexpected expenses
3. **Review cost reports** weekly to identify optimization opportunities
4. **Use debug mode** when investigating cost issues
5. **Keep AgentOps integration** enabled for comprehensive monitoring

## Related Documentation

- [AgentOps Integration Guide](../guides/agentops-integration-guide.md)
- [Cost Optimization Guide](../agno-integration/configuration/cost-optimization.md)
- [Agno Integration Architecture](../agno-integration/implementation/phase-1-core-agno.md)
- [Environment Setup Guide](../agno-integration/configuration/environment-setup.md)