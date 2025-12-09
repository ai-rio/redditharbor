# AgentOps Integration Guide

This guide provides comprehensive instructions for implementing AgentOps integration in the RedditHarbor Pipeline v3 system.

## Prerequisites

- Python 3.10+
- AgentOps API key
- Existing RedditHarbor Pipeline v3 installation

## Quick Start

### 1. Installation

Install the AgentOps package:

```bash
pip install agentops
```

### 2. Configuration

Set up your environment variables:

```bash
export AGENTOPS_API_KEY=your_agentops_api_key_here
export AGENTOPS_PROJECT_NAME=pipeline-v3-production
```

### 3. Basic Usage

Enable AgentOps in your agents:

```python
from transform.agno_agents import BaseAgent

# Create an AgentOps-enabled agent
agent = BaseAgent(
    name="reddit_research_agent",
    enable_agentops=True  # This enables AgentOps tracking
)
```

## Detailed Implementation

### 1. Agent Creation

#### BaseAgent with AgentOps

```python
from transform.agno_agents import BaseAgent
from monitoring.cost_tracker import CostTracker

# Agent with both AgentOps and cost tracking
agent = BaseAgent(
    name="comprehensive_agent",
    enable_agentops=True,           # Enable AgentOps tracking
    cost_tracker=CostTracker(),      # Optional: Add cost tracking
    debug_mode=True                  # Optional: Enable debug logging
)
```

#### Custom Agent Integration

```python
from transform.agno_agents import BaseAgent

class RedditAnalysisAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(
            name="reddit_analysis_agent",
            enable_agentops=True,  # Enable AgentOps tracking
            *args,
            **kwargs
        )

    def analyze_reddit_posts(self, posts):
        # This will be automatically tracked by AgentOps
        return self.process_posts(posts)
```

### 2. Session Management

#### Starting Analysis Sessions

```python
from transform.agno_analyzer import AgnoOpportunityAnalyzer

# Create analyzer with AgentOps
analyzer = AgnoOpportunityAnalyzer(enable_agentops=True)

# Start a named analysis session
analyzer.start_analysis_session(
    session_name="market_trends_analysis",
    tags=["reddit", "market_research", "trending"]
)

# Perform analysis (automatically tracked)
results = analyzer.analyze_opportunities()

# End session will be handled automatically
```

#### Manual Session Management

```python
from transform.agno_agents import BaseAgent

agent = BaseAgent(
    name="manual_session_agent",
    enable_agentops=True
)

# Manual session start
agent.agentops_tracker.start_session(
    "manual_analysis",
    tags=["manual", "detailed"]
)

# Perform operations
agent.process_data()

# Manual session end
agent.agentops_tracker.end_session("success", "Manual analysis completed")
```

### 3. Cost Tracking

#### Using CostTracker

```python
from monitoring.cost_tracker import CostTracker

# Initialize cost tracker
cost_tracker = CostTracker()

# Track costs by category
cost_tracker.track_cost(0.05, "llm_call")        # LLM API call
cost_tracker.track_cost(0.01, "embedding")       # Embedding generation
cost_tracker.track_cost(0.02, "api_request")     # External API call
cost_tracker.track_cost(0.03, "data_processing")  # Data processing

# Get total cost
total_cost = cost_tracker.get_total_cost()
print(f"Total cost: ${total_cost:.4f}")

# Reset tracker
cost_tracker.reset()
```

#### Cost Tracking in Workflows

```python
from workflows.tracked_workflow import TrackedWorkflow
from monitoring.cost_tracker import CostTracker

# Create workflow with cost tracking
workflow = TrackedWorkflow(
    name="cost_tracked_workflow",
    enable_agentops=True,           # Enable AgentOps
    cost_tracker=CostTracker()      # Enable cost tracking
)

# Track costs during workflow execution
workflow.track_cost(0.10, "initial_analysis")
workflow.track_cost(0.15, "deep_analysis")

# Get workflow costs
total_cost = workflow.cost_tracker.get_total_cost()
```

### 4. Decorator-Based Tracking

#### Available Decorators

```python
from monitoring.agentops_decorators import trace, tool, llm_call

@trace("function_execution", tags=["reddit_analysis"])
def analyze_reddit_post(post_data):
    """Function that will be traced by AgentOps"""
    return process_with_ai(post_data)

@tool("reddit_data_collection")
def collect_reddit_data(subreddit, limit=100):
    """Tool usage that will be tracked"""
    return fetch_reddit_posts(subreddit, limit)

@llm_call(track_cost=True)
def generate_research_summary(posts):
    """LLM call that will track costs"""
    return llm_client.generate(posts)
```

#### Combining Decorators

```python
@trace("reddit_analysis_workflow", tags=["production"])
@tool("sentiment_analysis")
@llm_call(track_cost=True)
def analyze_sentiment(text):
    """Combined decorator example"""
    return analyze_with_ai(text)
```

## Advanced Features

### 1. Custom Events

```python
from transform.agno_agents import BaseAgent

agent = BaseAgent(name="custom_event_agent", enable_agentops=True)

# Log custom events
agent.agentops_tracker.log_event(
    "reddit_data_processed",
    {"posts_count": 1000, "processing_time": 2.5}
)
```

### 2. Error Tracking

```python
try:
    # AgentOps-enabled operation
    result = agent.risky_operation()
except Exception as e:
    # Track error with AgentOps
    agent.agentops_tracker.log_error(
        "operation_failed",
        str(e),
        {"error_type": type(e).__name__}
    )
    raise
```

### 3. Performance Monitoring

```python
import time
from transform.agno_agents import BaseAgent

agent = BaseAgent(name="performance_agent", enable_agentops=True)

start_time = time.time()
result = agent.process_large_dataset()
duration = time.time() - start_time

# Track performance metrics
agent.agentops_tracker.log_event(
    "performance_metrics",
    {
        "duration": duration,
        "dataset_size": len(result),
        "throughput": len(result) / duration
    }
)
```

## Testing

### Running Tests

```bash
# Run all AgentOps-related tests
pytest tests/transform/test_agno_agentops_unit.py

# Run specific tests
pytest test_cost_tracking.py
pytest test_workflow_tracking.py
pytest test_workflow_agentops.py
pytest test_workflow_cost.py
```

### Writing New Tests

```python
import pytest
from transform.agno_agents import BaseAgent

def test_agentops_enabled():
    """Test that AgentOps is properly enabled"""
    agent = BaseAgent(name="test_agent", enable_agentops=True)
    assert hasattr(agent, 'agentops_tracker')
    assert agent.agentops_tracker is not None

def test_cost_tracking():
    """Test cost tracking functionality"""
    from monitoring.cost_tracker import CostTracker
    tracker = CostTracker()

    tracker.track_cost(0.05, "test_category")
    assert tracker.get_total_cost() == 0.05
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENTOPS_API_KEY` | Your AgentOps API key | Required |
| `AGENTOPS_PROJECT_NAME` | Project name in AgentOps | "pipeline-v3" |
| `AGENTOPS_ENABLED` | Enable/disable AgentOps | "true" |
| `AGENTOPS_TAGS` | Default tags for sessions | "" |

### Configuration File

You can also configure AgentOps through a configuration file:

```python
# config/agentops_config.py
from typing import Dict, Any, Optional

class AgentOpsConfig:
    def __init__(
        self,
        api_key: str,
        project_name: str = "pipeline-v3",
        enabled: bool = True,
        tags: Optional[list] = None
    ):
        self.api_key = api_key
        self.project_name = project_name
        self.enabled = enabled
        self.tags = tags or []

    @classmethod
    def from_environment(cls):
        """Create config from environment variables"""
        import os
        return cls(
            api_key=os.getenv("AGENTOPS_API_KEY"),
            project_name=os.getenv("AGENTOPS_PROJECT_NAME", "pipeline-v3"),
            enabled=os.getenv("AGENTOPS_ENABLED", "true").lower() == "true",
            tags=os.getenv("AGENTOPS_TAGS", "").split(",") if os.getenv("AGENTOPS_TAGS") else []
        )
```

## Troubleshooting

### Common Issues

1. **AgentOps Not Tracking**
   ```bash
   # Check environment variable
   echo $AGENTOPS_API_KEY

   # Verify network connectivity
   curl -I https://api.agentops.ai
   ```

2. **Cost Tracking Issues**
   ```python
   # Debug cost tracking
   from monitoring.cost_tracker import CostTracker
   tracker = CostTracker()
   print(f"Current cost: {tracker.get_total_cost()}")
   ```

3. **Session Management Problems**
   ```python
   # Check session status
   if hasattr(agent, 'agentops_tracker'):
       print(f"Session active: {agent.agentops_tracker.session_id}")
   ```

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("agentops")

# Agent with debug mode
agent = BaseAgent(
    name="debug_agent",
    enable_agentops=True,
    debug_mode=True
)
```

## Best Practices

### 1. Session Management

- Use descriptive session names
- Add relevant tags for categorization
- End sessions properly when operations complete

```python
# Good session management
analyzer.start_analysis_session(
    "reddit_sentiment_q4_2024",
    tags=["sentiment", "q4", "2024", "reddit"]
)

# Perform analysis
results = analyzer.analyze_sentiment()

# End session
if hasattr(analyzer, 'agentops_tracker'):
    analyzer.agentops_tracker.end_session("success", "Analysis completed")
```

### 2. Cost Optimization

- Track costs by category for better insights
- Monitor costs in real-time
- Set budgets and alerts

```python
# Cost monitoring best practices
cost_tracker = CostTracker()

# Track costs immediately
cost_tracker.track_cost(0.05, "llm_call")

# Periodic checks
if cost_tracker.get_total_cost() > budget:
    alert_budget_exceeded()
```

### 3. Error Handling

- Always wrap operations in try-catch blocks
- Log errors with AgentOps
- Provide meaningful error context

```python
try:
    result = agent.analyze_complex_dataset()
except Exception as e:
    # Log with AgentOps
    agent.agentops_tracker.log_error(
        "analysis_failed",
        str(e),
        {"dataset_size": dataset_size}
    )
    # Handle error appropriately
    handle_error(e)
```

## Migration from Previous Versions

### If upgrading from an older version:

1. **Enable AgentOps in Agent Creation**
   ```python
   # Old way
   agent = BaseAgent(name="old_agent")

   # New way
   agent = BaseAgent(name="new_agent", enable_agentops=True)
   ```

2. **Add Cost Tracking**
   ```python
   # Add cost tracker to existing workflows
   workflow = TrackedWorkflow(
       name="existing_workflow",
       enable_agentops=True,
       cost_tracker=CostTracker()  # Add this
   )
   ```

3. **Update Session Management**
   ```python
   # Old manual session management
   session_id = agent.start_session("analysis")

   # New automatic session management
   # Session starts automatically when enable_agentops=True
   ```

## Resources

- [AgentOps Documentation](https://agentops.ai/docs)
- [RedditHarbor Pipeline v3 Documentation](https://github.com/Goldziher/redditharbor)
- [Issue Tracker](https://github.com/Goldziher/redditharbor/issues)

## Support

If you encounter issues with AgentOps integration:

1. Check the troubleshooting section
2. Verify your configuration
3. Review the test examples
4. Open an issue on GitHub

---

*Last Updated: December 7, 2025*