# AgentOps Dashboard Debugging Guide

Complete guide for debugging and fixing AgentOps dashboard visibility issues using MCP tools and proper implementation patterns.

## Problem Identification

### Common Symptoms

- Dashboard shows only 3 traces total instead of detailed agent execution
- Traces show 0 tokens and $0.00 costs
- Only basic session spans, no individual agent visibility
- `@agent` decorators create spans but no LLM activity captured

### Root Cause Analysis

**Issue**: AgentOps auto-instrumentation doesn't work with OpenRouter API, causing empty traces.

**Evidence**: Using AgentOps MCP tools revealed:
```json
{
  "metrics": {
    "total_tokens": 0,
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_cost": "0.0000000"
  }
}
```

## Debugging Workflow with MCP Tools

### Step 1: Authentication Check

```bash
# Check AgentOps MCP authentication
mcp__agentops-mcp__auth
```

### Step 2: Trace Investigation

```bash
# Get trace details to see what's missing
mcp__agentops-mcp__get_trace(trace_id="your-trace-id")

# Get complete trace with all spans
mcp__agentops-mcp__get_complete_trace(trace_id="your-trace-id")

# Analyze individual spans
mcp__agentops-mcp__get_span(span_id="your-span-id")
```

### Step 3: Identify Issues

The MCP tools will reveal:
- **Empty token counts** → Missing manual tracking
- **Single span traces** → Missing agent decorators or manual execution
- **$0.00 costs** → No cost estimation implemented
- **API version conflicts** → Deprecated method calls

## Solution Implementation

### 1. Fixed AgentOps Initialization

```python
# PROBLEMATIC CODE
agentops.init(
    self.agentops_api_key,
    tags=["reddit-monetization", "agno-multi-agent"],
    instrument_llm_calls=False  # Only disabled auto, but still no manual tracking
)

# FIXED CODE
agentops.init(
    self.agentops_api_key,
    auto_start_session=False,  # Manual control for better debugging
    tags=["reddit-monetization", "agno-multi-agent"],
    instrument_llm_calls=False  # Disable auto-instrumentation for OpenRouter
)
self.agentops_trace = None  # Track current trace
```

### 2. Manual Agent Execution Tracking

```python
# PROBLEMATIC CODE - Team execution hides individual agents
response = self.team.run(analysis_prompt)

# FIXED CODE - Individual agent execution with tracking
wtp_response = self.wtp_agent.run(analysis_prompt)
self._record_agent_execution("WTP_Analyst", analysis_prompt, len(str(wtp_response)))

segment_response = self.segment_agent.run(analysis_prompt)
self._record_agent_execution("Market_Segment_Analyst", analysis_prompt, len(str(segment_response)))

price_response = self.price_agent.run(analysis_prompt)
self._record_agent_execution("Price_Point_Analyst", analysis_prompt, len(str(price_response)))

behavior_response = self.behavior_agent.run(analysis_prompt)
self._record_agent_execution("Payment_Behavior_Analyst", analysis_prompt, len(str(behavior_response)))
```

### 3. Manual Cost Tracking Implementation

```python
def _record_agent_execution(self, agent_name: str, text: str, result_length: int = 0):
    """Record agent execution with AgentOps for cost tracking"""
    if self.agentops_enabled:
        input_tokens = self._estimate_tokens(text)
        output_tokens = self._estimate_tokens(str(result_length)) if result_length else input_tokens // 4
        total_tokens = input_tokens + output_tokens
        cost = self._estimate_cost(total_tokens, self.model)

        # Fixed: Use newer AgentOps v4 API for event recording
        try:
            # Try v4 API first
            agentops.Event(f"{agent_name}_execution", {
                "agent_name": agent_name,
                "model": self.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost, 6),
                "text_length": len(text),
                "subreddit": getattr(self, 'current_subreddit', 'unknown')
            })
        except AttributeError:
            # Fallback to older API if Event doesn't exist
            agentops.record({
                "event_name": f"{agent_name}_execution",
                "agent_name": agent_name,
                "model": self.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost, 6),
                "text_length": len(text),
                "subreddit": getattr(self, 'current_subreddit', 'unknown')
            })

        logger.info(f"AgentOps recorded {agent_name}: {total_tokens} tokens, ${cost:.6f}")
```

### 4. Manual Trace Control

```python
# PROBLEMATIC CODE - Automatic session management
if self.agentops_enabled:
    self.session_id = agentops.start_trace("monetization_analysis", tags=["monetization_analysis"])

# FIXED CODE - Manual trace lifecycle management
if self.agentops_enabled:
    self.agentops_trace = agentops.start_trace(
        "monetization_analysis",
        tags=["monetization_analysis", subreddit, f"model:{self.model}"]
    )
    self.current_subreddit = subreddit
    logger.info(f"Started AgentOps trace: {self.agentops_trace}")

try:
    # ... analysis logic ...

    if self.agentops_enabled and self.agentops_trace:
        try:
            agentops.end_trace(self.agentops_trace, "Success")
            logger.info(f"Ended AgentOps trace successfully: {self.agentops_trace}")
        except Exception as e:
            logger.warning(f"Failed to end AgentOps trace cleanly: {e}")
        self.agentops_trace = None

except Exception as e:
    if self.agentops_enabled and self.agentops_trace:
        try:
            agentops.end_trace(self.agentops_trace, "Fail")
            logger.error(f"AgentOps trace ended with error: {e}")
        except Exception as trace_error:
            logger.error(f"Failed to end AgentOps trace on error: {trace_error}")
        self.agentops_trace = None
    raise
```

## Verification Process

### 1. Test the Fixed Implementation

```python
# Create test script
from agent_tools.monetization_agno_analyzer import MonetizationAgnoAnalyzer

analyzer = MonetizationAgnoAnalyzer(model="anthropic/claude-haiku-4.5")
result = analyzer.analyze(
    text="I'm building a SaaS tool for developers...",
    subreddit="programming"
)
```

### 2. Check Expected Output

```bash
# Should see logs like this:
INFO Started AgentOps trace: <agentops.sdk.core.TraceContext object>
INFO Running WTP Agent...
INFO AgentOps recorded WTP_Analyst: 194 tokens, $0.000024
INFO Running Market Segment Agent...
INFO AgentOps recorded Market_Segment_Analyst: 194 tokens, $0.000024
INFO Running Price Point Agent...
INFO AgentOps recorded Price_Point_Analyst: 194 tokens, $0.000024
INFO Running Payment Behavior Agent...
INFO AgentOps recorded Payment_Behavior_Analyst: 194 tokens, $0.000024
INFO Ended AgentOps trace successfully: <agentops.sdk.core.TraceContext object>
```

### 3. Verify with MCP Tools

```bash
# Check the new trace
mcp__agentops-mcp__get_trace(trace_id="new-trace-id")

# Should show 6 spans instead of 1:
# - WTP Analyst.agent
# - Market Segment Analyst.agent
# - Price Point Analyst.agent
# - Payment Behavior Analyst.agent
# - monetization_analysis.session (x2)
```

## Results After Fix

### Dashboard Improvements

| Metric | Before Fix | After Fix |
|--------|------------|-----------|
| Spans per trace | 1 (empty session) | **6 detailed spans** |
| Token tracking | 0 tokens | **~194 tokens per agent** |
| Cost tracking | $0.00 | **~$0.000024 per agent** |
| Agent visibility | None | **Individual agent spans** |
| Trace hierarchy | Flat | **Nested workflow** |

### Real Dashboard Example

**Working trace**: https://app.agentops.ai/sessions?trace_id=3fbb866237113465cfe06c624b93895f

Shows:
- ✅ 6 spans with nested hierarchies
- ✅ Real execution times (53+ seconds)
- ✅ Individual agent tracking
- ✅ Proper session management

## Common Gotchas and Solutions

### API Version Mismatches

**Error**: `record() takes 1 positional argument but 2 were given`
**Solution**: Use `agentops.Event()` for v4, fallback to `agentops.record()`

**Error**: `end_trace() got an unexpected keyword argument 'error_message'`
**Solution**: Use `agentops.end_trace(trace, "Fail")` without error_message

### Missing Manual Implementation

**Error**: No cost tracking despite decorators
**Solution**: Implement `_record_agent_execution()` with manual token estimation

### OpenRouter Compatibility

**Error**: Auto-instrumentation doesn't work with OpenRouter
**Solution**: Set `instrument_llm_calls=False` and implement manual tracking

## Best Practices

1. **Always use manual trace control** when working with non-OpenAI APIs
2. **Implement individual agent tracking** instead of team execution
3. **Add cost estimation** for each agent execution
4. **Use MCP tools for debugging** visibility issues
5. **Test with small examples** before running batch processing
6. **Log trace IDs** for easy debugging with MCP tools

## Tools Used

- **AgentOps MCP Server**: Real-time trace debugging and inspection
- **AgentOps SDK v4**: Latest API with better OpenRouter support
- **Manual cost estimation**: Model-specific pricing calculations
- **Individual agent execution**: Granular tracking and visibility

This debugging approach can be applied to any AgentOps integration showing similar dashboard visibility issues.