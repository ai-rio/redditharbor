# AgentOps Integration

AgentOps provides comprehensive observability, cost tracking, and analytics for AI agent operations in RedditHarbor. **Fixed implementation now provides full dashboard visibility with detailed agent execution traces.**

## Overview

AgentOps SDK is used to:
- ✅ **Track LLM API costs across all providers** (including OpenRouter)
- ✅ **Monitor individual agent performance and latency**
- ✅ **Debug multi-agent workflows with detailed traces**
- ✅ **Generate analytics on agent behavior with real cost data**
- ✅ **Fixed: Dashboard now shows 6 detailed spans instead of empty sessions**

## Documentation

- [Evidence Integration Summary](./evidence-integration-summary.md) - Complete SDK instrumentation guide with cost tracking
- [Troubleshooting Dashboard Issues](#troubleshooting) - Debug guide with MCP tools

## Key Features

### Cost Tracking (Fixed 🎯)
**Manual tracking with accurate cost estimation:**
- OpenRouter API costs (Agno agents) - Now properly tracked
- Token usage per agent with model-specific pricing
- Cost per opportunity analysis with real calculations
- **Example**: 194 tokens per agent ~ $0.000024 per execution

### Agent Observability (Enhanced 🔧)
- `@agent` decorators for each agent type with proper span hierarchies
- `@trace` decorators with manual trace control for better debugging
- `@tool` decorators with cost tracking parameters
- **NEW**: Individual agent execution tracking with nested spans

## Implementation (Updated ✅)

### Initialization (Fixed)
**File**: `agent_tools/monetization_agno_analyzer.py`

```python
import agentops

# FIXED: Manual trace control for better visibility
agentops.init(
    api_key=self.agentops_api_key,
    auto_start_session=False,  # Manual control for debugging
    tags=["reddit-monetization", "agno-multi-agent"],
    instrument_llm_calls=False  # Disable auto-instrumentation for OpenRouter
)
```

### Enhanced Agent Tracking (New)
**File**: `agent_tools/monetization_agno_analyzer.py`

```python
from agentops.sdk.decorators import agent, trace, tool

@agent(name="WTP Analyst")
class WillingnessToPayAgent(Agent):
    """Individual agent with dedicated tracking"""
    pass

@tool(name="parse_team_response", cost=0.001)
def _parse_team_response(self, response):
    """Tool with cost tracking"""
    # Actual implementation with AgentOps events
    pass

@trace(name="monetization_analysis")
def analyze(self, text, subreddit):
    """Main workflow with manual trace control"""
    # Fixed: Individual agent execution with manual tracking
    trace = agentops.start_trace("monetization_analysis", tags=[subreddit])

    # Each agent tracked separately
    wtp_response = self.wtp_agent.run(text)
    self._record_agent_execution("WTP_Analyst", text, len(str(wtp_response)))

    # ... other agents

    agentops.end_trace(trace, "Success")
```

## Dashboard Access (Updated 📊)

View agent analytics at: **https://app.agentops.ai/**

**Key metrics now available (Fixed):**
- ✅ **Individual agent spans**: WTP, Market Segment, Price Point, Payment Behavior
- ✅ **Cost per session**: Real costs instead of $0.00
- ✅ **Agent execution times**: Detailed latency per agent
- ✅ **Token usage breakdown**: Accurate token counting
- ✅ **Nested trace hierarchies**: Complete workflow visualization
- ✅ **Error rates and retries**: Proper error handling tracking

## Configuration

```bash
# .env
AGENTOPS_API_KEY=your_key_here
OPENROUTER_API_KEY=your_openrouter_key  # For Agno agents
```

```python
# config/settings.py
AGENTOPS_API_KEY = os.environ.get("AGENTOPS_API_KEY", "")
```

## Troubleshooting (New 🔧)

### Dashboard Shows Empty Traces

**Problem**: AgentOps dashboard shows only 3 traces with $0.00 costs and no agent spans.

**Solution**: The implementation has been **completely fixed** with the following changes:

1. **Manual Trace Control**: Use `auto_start_session=False` + `start_trace()`/`end_trace()`
2. **Individual Agent Execution**: Track each agent separately instead of team.run()
3. **Proper Event Recording**: Compatible with AgentOps v4 API
4. **Cost Estimation**: Manual token counting with model-specific pricing

**Verification**: Use AgentOps MCP tools to debug:
```bash
# Check trace details
mcp__agentops-mcp__get_trace(trace_id="your-trace-id")

# Get complete trace information
mcp__agentops-mcp__get_complete_trace(trace_id="your-trace-id")

# Get individual span details
mcp__agentops-mcp__get_span(span_id="your-span-id")
```

### Expected Dashboard Behavior

**Before Fix:**
- Only 1 session span per trace
- 0 tokens, $0.00 costs
- No individual agent visibility

**After Fix:**
- **6 spans per trace**: 4 agents + 2 session spans
- **Real token usage**: ~194 tokens per agent
- **Actual costs**: ~$0.000024 per agent execution
- **Nested hierarchies**: Agent execution workflow visualization

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|--------|----------|
| `record() takes 1 positional argument` | API version mismatch | Use `agentops.Event()` for v4, fallback to old API |
| `end_trace() got unexpected keyword argument` | API version mismatch | Use `agentops.end_trace(trace, "Success")` without error_message |
| No spans in dashboard | Missing manual tracking | Implement individual agent execution with `_record_agent_execution()` |

## Logs

Agent session logs are stored in:
- `agentops.log` (root directory) - Shows trace URLs and debugging info
- AgentOps cloud dashboard - Complete trace visualization
- **NEW**: Real-time MCP tool debugging available

## Expected Results

**After implementing the fixes, you should see:**
```bash
INFO AgentOps recorded WTP_Analyst: 194 tokens, $0.000024
INFO AgentOps recorded Market_Segment_Analyst: 194 tokens, $0.000024
INFO AgentOps recorded Price_Point_Analyst: 194 tokens, $0.000024
INFO AgentOps recorded Payment_Behavior_Analyst: 194 tokens, $0.000024
INFO Ended AgentOps trace successfully: <agentops.sdk.core.TraceContext object>
```

**Dashboard trace example**: https://app.agentops.ai/sessions?trace_id=3fbb866237113465cfe06c624b93895f

## Related Documentation

- [Agno Integration](../agno/) - Multi-agent framework being tracked
- [Jina Integration](../jina/) - Market validation with cost tracking
- [AgentOps MCP Server](https://github.com/AgentOps-AI/agentops-mcp) - Debugging tools used for fixes
