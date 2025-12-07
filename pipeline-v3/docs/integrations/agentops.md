# AgentOps Integration

## Overview

AgentOps has been successfully integrated into the RedditHarbor platform to provide comprehensive observability, monitoring, and cost tracking for AI agents and workflows. This integration enables detailed tracking of agent operations, tool usage, LLM calls, and associated costs.

## Key Features

### 1. AgentOps Tracking in Agents

All Agno agents now support AgentOps tracking through the `enable_agentops` parameter:

```python
from transform.agno_agents import BaseAgent

# AgentOps-enabled agent
agent = BaseAgent(
    name="research_agent",
    enable_agentops=True  # Enables AgentOps tracking
)
```

### 2. Enhanced AgnoOpportunityAnalyzer

The `AgnoOpportunityAnalyzer` now includes a dedicated `start_analysis_session` method:

```python
from transform.agno_analyzer import AgnoOpportunityAnalyzer

analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)

# Start a named analysis session with optional tags
analyzer.start_analysis_session(
    session_name="market_research",
    tags=["reddit_analysis", "sentiment", "trending"]
)
```

### 3. Cost Tracking Integration

Comprehensive cost tracking has been implemented to monitor API usage:

```python
from monitoring.cost_tracker import CostTracker

# Initialize cost tracker
cost_tracker = CostTracker()

# Track costs by category
cost_tracker.track_cost(0.05, "llm_call")
cost_tracker.track_cost(0.01, "embedding")
cost_tracker.track_cost(0.02, "api_request")

# Get total tracked cost
total_cost = cost_tracker.get_total_cost()
print(f"Total cost: ${total_cost:.4f}")
```

### 4. Tracked Workflows

The `TrackedWorkflow` class combines AgentOps and cost tracking:

```python
from workflows.tracked_workflow import TrackedWorkflow

# Workflow with both AgentOps and cost tracking
workflow = TrackedWorkflow(
    name="data_collection_workflow",
    enable_agentops=True,
    cost_tracker=CostTracker()
)

# Track costs within workflow
workflow.track_cost(0.03, "data_processing")
```

## Implementation Details

### AgentOps Decorators

The integration leverages AgentOps decorators for automatic tracking:

- `@trace` - Traces function calls and their results
- `@tool` - Tracks tool usage and parameters
- `@llm_call` - Monitors LLM interactions and costs

### Configuration

AgentOps integration is controlled by the `AGENTOPS_KEY` environment variable. Ensure your `.env` file contains:

```env
AGENTOPS_KEY=your_agentops_api_key_here
```

### Test Coverage

Comprehensive tests have been implemented:

- `test_base_agent_tdd.py` - BaseAgent AgentOps integration
- `test_tdd_step.py` - Analyzer session management
- `test_cost_tracking.py` - CostTracker functionality
- `test_workflow_tracking.py` - Basic workflow creation
- `test_workflow_agentops.py` - Workflow AgentOps integration
- `test_workflow_cost.py` - Workflow cost tracking

## Usage Examples

### 1. Research Agent with Tracking

```python
from transform.agno_agents import ResearchAgent
from monitoring.cost_tracker import CostTracker

# Set up tracked research agent
research_agent = ResearchAgent(
    name="reddit_research_agent",
    enable_agentops=True,
    cost_tracker=CostTracker()
)

# Start analysis session
research_agent.start_analysis_session(
    "market_trends_analysis",
    tags=["reddit", "market_research", "trending"]
)

# Perform research (automatically tracked)
analysis = research_agent.analyze_reddit_trends()

# Get costs tracked
print(f"Research cost: ${research_agent.cost_tracker.get_total_cost():.4f}")
```

### 2. Multi-Agent Workflow

```python
from workflows.tracked_workflow import TrackedWorkflow
from monitoring.cost_tracker import CostTracker

# Create multi-agent workflow
workflow = TrackedWorkflow(
    name="multi_agent_research",
    enable_agentops=True,
    cost_tracker=CostTracker()
)

# Add agents to workflow (simplified example)
workflow.add_agent(DataCollectionAgent())
workflow.add_agent(SentimentAnalysisAgent())
workflow.add_agent(TrendReporterAgent())

# Execute workflow with tracking
workflow.execute()
total_cost = workflow.cost_tracker.get_total_cost()
```

## Monitoring and Debugging

### Enhanced Logging

AgentOps integration provides enhanced logging:

```python
import logging

# Enable debug logging for AgentOps
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("agentops")

# AgentOps operations will be logged
agent = BaseAgent(name="debug_agent", enable_agentops=True)
```

### Cost Monitoring

Monitor costs in real-time:

```python
# Check current cost total
current_cost = cost_tracker.get_total_cost()

# Reset cost tracker if needed
cost_tracker.reset()

# Track costs by category for analysis
cost_by_category = cost_tracker.get_costs_by_category()
```

## Performance Considerations

### Lightweight Integration

The AgentOps integration is designed to be lightweight:
- Minimal performance overhead
- Automatic tracking with decorators
- Conditional activation based on configuration

### Memory Efficiency

Cost tracking is memory-efficient:
- Optimized for long-running workflows
- Automatic cleanup of old tracking data
- Configurable retention policies

## Troubleshooting

### Common Issues

1. **AgentOps not tracking**
   - Verify `AGENTOPS_KEY` environment variable
   - Check network connectivity
   - Enable debug logging for detailed information

2. **Cost tracking discrepancies**
   - Verify cost calculation logic
   - Check API pricing documentation
   - Monitor for duplicate tracking calls

3. **Session management issues**
   - Ensure proper session lifecycle
   - Avoid multiple simultaneous sessions
   - Use proper session naming conventions

### Debug Mode

Enable Agno debug mode for enhanced debugging:

```python
# Enable debug mode in all agents
agent = BaseAgent(
    name="debug_agent",
    enable_agentops=True,
    debug_mode=True
)
```

## Future Enhancements

1. **Advanced Cost Analytics**
   - Cost breakdown by agent
   - Historical cost trends
   - Predictive cost modeling

2. **Enhanced Session Management**
   - Persistent session storage
   - Session cloning and templates
   - Advanced session analytics

3. **Integration with Monitoring Dashboards**
   - Real-time cost dashboards
   - Performance metrics integration
   - Alerting system for cost thresholds

## Migration Guide

### From Previous Versions

If upgrading from a previous version:

1. Enable the `enable_agentops` parameter in agent initialization
2. Replace manual tracking with decorator-based tracking
3. Implement cost tracking using the new `CostTracker` class
4. Update tests to include AgentOps assertions

### Backward Compatibility

The integration maintains backward compatibility:
- Existing agents continue to work without AgentOps
- Cost tracking is optional and opt-in
- No breaking changes to existing APIs