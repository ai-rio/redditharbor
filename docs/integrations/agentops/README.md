# AgentOps Integration

AgentOps provides observability, cost tracking, and analytics for AI agent operations in RedditHarbor.

## Overview

AgentOps SDK is used to:
- Track LLM API costs across all providers
- Monitor agent performance and latency
- Debug multi-agent workflows
- Generate analytics on agent behavior

## Documentation

- [Evidence Integration Summary](./evidence-integration-summary.md) - Complete SDK instrumentation guide with cost tracking

## Key Features

### Cost Tracking
Automatic tracking of:
- OpenRouter API costs (Agno agents)
- Token usage per agent
- Cost per opportunity analysis

### Agent Observability
- `@agent` decorators for each agent type
- `@trace` decorators for workflow tracking
- `@tool` decorators for utility functions

## Implementation

### Initialization
**File**: `scripts/core/batch_opportunity_scoring.py`

```python
import agentops

# Initialize with API key
agentops.init(
    api_key=os.environ.get("AGENTOPS_API_KEY"),
    default_tags=["redditharbor", "monetization-analysis"]
)
```

### Agent Decorators
**File**: `agent_tools/monetization_agno_analyzer.py`

```python
from agentops import agent, trace, tool

@agent(name="WTP Analyst")
class WillingnessToPayAgent:
    pass

@trace(name="monetization_analysis")
async def analyze(self, data):
    pass

@tool(name="calculate_scores")
def calculate_scores(self, evidence):
    pass
```

## Dashboard Access

View agent analytics at: https://app.agentops.ai/

Key metrics available:
- Cost per session
- Agent execution times
- Token usage breakdown
- Error rates and retries

## Configuration

```bash
# .env
AGENTOPS_API_KEY=your_key_here
```

```python
# config/settings.py
AGENTOPS_API_KEY = os.environ.get("AGENTOPS_API_KEY", "")
```

## Logs

Agent session logs are stored in:
- `agentops.log` (root directory)
- AgentOps cloud dashboard

## Related Documentation

- [Agno Integration](../agno/) - Multi-agent framework being tracked
- [Jina Integration](../jina/) - Market validation with cost tracking
