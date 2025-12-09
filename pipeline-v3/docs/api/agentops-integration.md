# AgentOps Integration API

<span style="color:#FF6B35; font-weight:bold;">RedditHarbor Pipeline v3</span>
<span style="color:#004E89; font-size:0.9em;">AgentOps Integration API Documentation</span>

---

## Overview

The AgentOps Integration API provides comprehensive tracking, monitoring, and observability capabilities for AI agents and workflows. This integration enables detailed session management, operation tracking, error handling, and performance metrics collection for the Agno framework components.

## Key Features

- **Session Management**: Automatic session lifecycle tracking with unique identifiers
- **Operation Tracing**: Detailed function and method execution monitoring
- **Cost Tracking**: Real-time LLM usage cost calculation and aggregation
- **Error Monitoring**: Comprehensive error tracking with context preservation
- **Performance Metrics**: Latency measurement and performance analysis
- **Decorator-Based Integration**: Easy-to-use decorators for automatic tracking

---

## Core Components

### AgentOps Tracker

The central component providing AgentOps integration capabilities.

```python
from monitoring.agentops_tracker import get_tracker

# Get the singleton tracker instance
tracker = get_tracker()
```

#### Key Methods

##### `start_session(session_name: str, tags: list[str] | None = None) -> str | None`

Start a new AgentOps tracking session.

**Parameters:**
- `session_name` (str): Human-readable name for the session
- `tags` (list[str] | None): Optional tags for session categorization

**Returns:**
- `str | None`: Unique session identifier or None if tracking is disabled

**Example:**
```python
tracker = get_tracker()
session_id = tracker.start_session(
    session_name="Market Analysis Workflow",
    tags=["market-research", "reddit-data", "pipeline-v3"]
)
print(f"Started session: {session_id}")
```

##### `end_session(status: str = "success", metadata: dict[str, Any] | None = None) -> None`

End the current AgentOps session with final status.

**Parameters:**
- `status` (str): Session completion status ("success", "error", "timeout")
- `metadata` (dict[str, Any] | None): Optional metadata for session summary

**Example:**
```python
tracker.end_session(
    status="success",
    metadata={
        "analyses_completed": 15,
        "total_cost_usd": 0.0234,
        "execution_time_seconds": 45.2
    }
)
```

##### `track_operation_result(operation: str, success: bool, metadata: dict[str, Any] | None = None) -> None`

Track the result of an operation or function execution.

**Parameters:**
- `operation` (str): Name or identifier of the operation
- `success` (bool): Whether the operation completed successfully
- `metadata` (dict[str, Any] | None): Additional context and data

**Example:**
```python
tracker.track_operation_result(
    operation="data_extraction",
    success=True,
    metadata={
        "records_processed": 1250,
        "data_source": "reddit_api",
        "processing_time_ms": 2340
    }
)
```

##### `track_llm_call(model: str, tokens: int, cost: float, latency: float, success: bool, metadata: dict[str, Any] | None = None) -> None`

Track detailed LLM API call information for cost and usage analysis.

**Parameters:**
- `model` (str): Model identifier used for the call
- `tokens` (int): Number of tokens processed
- `cost` (float): Cost in USD for the call
- `latency` (float): Execution time in seconds
- `success` (bool): Whether the call was successful
- `metadata` (dict[str, Any] | None): Additional call context

**Example:**
```python
tracker.track_llm_call(
    model="anthropic/claude-3-haiku",
    tokens=1543,
    cost=0.0023,
    latency=1.24,
    success=True,
    metadata={
        "function": "analyze_sentiment",
        "prompt_type": "market_analysis",
        "response_format": "structured"
    }
)
```

---

## Decorators API

### `@trace` Decorator

Automatically trace function execution with comprehensive monitoring.

```python
from monitoring.agentops_decorators import trace
```

#### Signature

```python
def trace(
    name: str | None = None,
    tags: list[str] | None = None,
    track_args: bool = False,
    track_result: bool = False,
    include_timing: bool = True,
    track_errors: bool = True,
    timeout: float | None = None
) -> Callable
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str \| None` | `None` | Custom trace name (defaults to function name) |
| `tags` | `list[str] \| None` | `None` | Tags for categorizing the trace |
| `track_args` | `bool` | `False` | Whether to track function arguments |
| `track_result` | `bool` | `False` | Whether to track function return value |
| `include_timing` | `bool` | `True` | Include execution timing metrics |
| `track_errors` | `bool` | `True` | Automatically track exceptions |
| `timeout` | `float \| None` | `None` | Function timeout in seconds |

#### Examples

**Basic Function Tracing:**
```python
@trace(tags=["data-processing", "reddit"])
def process_reddit_data(submissions: list[dict]) -> list[dict]:
    """Process Reddit submission data"""
    # Processing logic here
    return processed_data
```

**Advanced Tracing with Arguments and Results:**
```python
@trace(
    name="market-analysis",
    tags=["analysis", "market"],
    track_args=True,
    track_result=True,
    timeout=30.0
)
async def analyze_market_trends(data: dict, analysis_type: str) -> dict:
    """Analyze market trends from Reddit data"""
    # Complex analysis logic
    return {
        "trends": trends,
        "confidence": 0.85,
        "insights": insights
    }
```

### `@tool` Decorator

Mark and track tool usage with specialized monitoring.

```python
from monitoring.agentops_decorators import tool
```

#### Signature

```python
def tool(
    name: str | None = None,
    category: str | None = None,
    track_usage: bool = True,
    track_cost: bool = False,
    cost_callback: Callable[[], float] | None = None
) -> Callable
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str \| None` | `None` | Tool name (defaults to function name) |
| `category` | `str \| None` | `None` | Category for grouping tools |
| `track_usage` | `bool` | `True` | Track tool usage metrics |
| `track_cost` | `bool` | `False` | Track tool execution cost |
| `cost_callback` | `Callable[[], float] \| None` | `None` | Function to calculate tool cost |

#### Examples

**Basic Tool Tracking:**
```python
@tool(name="sentiment-analyzer", category="nlp")
def analyze_sentiment(text: str) -> dict:
    """Analyze text sentiment"""
    # NLP processing logic
    return {"sentiment": "positive", "score": 0.82}
```

**Tool with Cost Tracking:**
```python
def calculate_api_cost() -> float:
    """Calculate cost for external API call"""
    return 0.0012  # Cost per call

@tool(
    name="geolocation-service",
    category="external-apis",
    track_cost=True,
    cost_callback=calculate_api_cost
)
async def get_user_geolocation(ip_address: str) -> dict:
    """Get geolocation data for IP address"""
    # External API call
    return location_data
```

### `@llm_call` Decorator

Specialized decorator for LLM API calls with detailed cost tracking.

```python
from monitoring.agentops_decorators import llm_call
```

#### Signature

```python
def llm_call(
    model_name: str | None = None,
    track_cost: bool = True,
    track_tokens: bool = True,
    custom_cost_calculator: Callable | None = None
) -> Callable
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_name` | `str \| None` | `None` | LLM model identifier |
| `track_cost` | `bool` | `True` | Track API call cost |
| `track_tokens` | `bool` | `True` | Track token usage |
| `custom_cost_calculator` | `Callable \| None` | `None` | Custom cost calculation function |

#### Examples

**Basic LLM Call Tracking:**
```python
@llm_call(model_name="anthropic/claude-3-sonnet")
async def generate_analysis_prompt(context: dict) -> str:
    """Generate analysis prompt from context"""
    # LLM call implementation
    return response.content
```

**LLM Call with Custom Cost Calculator:**
```python
def custom_cost_calculator(model: str, tokens: int, response) -> float:
    """Custom cost calculation based on model and usage"""
    if "gpt-4" in model.lower():
        return (tokens / 1000) * 0.03  # $0.03 per 1K tokens
    return (tokens / 1000) * 0.001  # Default rate

@llm_call(
    model_name="openai/gpt-4-turbo",
    custom_cost_calculator=custom_cost_calculator
)
def generate_insights(data: list[str]) -> str:
    """Generate insights using GPT-4"""
    # Implementation with OpenAI API
    return insights
```

---

## Context Managers

### `AgentOpsTraceContext`

Manual context manager for custom tracing scenarios.

```python
from monitoring.agentops_decorators import trace_context, AgentOpsTraceContext
```

#### Usage Examples

**Basic Context Tracing:**
```python
async def complex_workflow(data: dict):
    """Complex workflow requiring manual tracing control"""
    async with trace_context("data-pipeline", tags=["etl", "processing"]) as ctx:
        try:
            # Stage 1: Data extraction
            extracted = await extract_data(data)

            # Stage 2: Transformation
            transformed = await transform_data(extracted)

            # Stage 3: Loading
            await load_data(transformed)

        except Exception as e:
            # Context automatically tracks errors
            logger.error(f"Workflow failed: {e}")
            raise
```

**Manual Context Management:**
```python
def manual_tracing_example():
    """Example with manual context management"""
    ctx = AgentOpsTraceContext(
        name="custom-operation",
        tags=["manual", "custom"],
        metadata={"operation_type": "batch_processing"}
    )

    with ctx:
        # Custom tracing logic
        process_batch_data()

        # Update context metadata
        ctx.metadata["records_processed"] = 1000
        ctx.metadata["success_rate"] = 0.98
```

---

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AGENTOPS_API_KEY` | `str` | `None` | AgentOps API key for tracking |
| `AGNO_ENABLE_AGENTOPS` | `bool` | `False` | Enable AgentOps tracking for Agno agents |
| `AGENTOPS_LOG_LEVEL` | `str` | `"INFO"` | Logging level for AgentOps operations |

### Settings Configuration

```python
from config.settings import Settings

# Configure AgentOps in settings
settings = Settings(
    agno_enable_agentops=True,  # Enable tracking
    # ... other settings
)
```

---

## Integration with Agno Workflows

### TrackedWorkflow Class

Enhanced workflow class with built-in AgentOps integration.

```python
from workflows.tracked_workflow import TrackedWorkflow
```

#### Constructor

```python
def __init__(
    name: str,
    config: dict[str, Any] | None = None,
    enable_agentops: bool = False,
    cost_tracker=None
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Workflow name for tracking |
| `config` | `dict[str, Any] \| None` | `None` | Workflow configuration |
| `enable_agentops` | `bool` | `False` | Enable AgentOps tracking |
| `cost_tracker` | `CostTracker \| None` | `None` | Cost tracking instance |

#### Example Usage

```python
# Create tracked workflow
workflow = TrackedWorkflow(
    name="Reddit Market Analysis",
    config={"max_analyses": 100},
    enable_agentops=True,
    cost_tracker=cost_calculator
)

# Run workflow with automatic tracking
results = workflow.run()

# Manual cost tracking
workflow.track_cost(0.0234, category="llm_calls")
```

### BaseAgent Integration

Enhanced agent class with AgentOps capabilities.

```python
from transform.agno_agents import BaseAgent
```

#### Constructor with AgentOps Support

```python
def __init__(
    model: str,
    api_key: str,
    base_url: str,
    output_schema: type[BaseModel] | None = None,
    debug_mode: bool = False,
    enable_agentops: bool = False,
    instructions: list[str] | None = None,
    name: str | None = None
)
```

#### Example

```python
# Create agent with AgentOps tracking
agent = WillingnessToPayAgent(
    model="anthropic/claude-3-haiku",
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
    debug_mode=True,
    enable_agentops=True  # Enable tracking
)

# Run agent with automatic tracking
result = await agent.a_run("Analyze willingness to pay for this product...")
```

---

## Error Handling

### Automatic Error Tracking

The AgentOps integration automatically tracks and reports errors with full context:

```python
@trace(track_errors=True, track_args=True)
def risky_operation(data: dict) -> dict:
    """Operation that might fail"""
    if not data.get("required_field"):
        raise ValueError("Missing required field")
    return process_data(data)
```

### Manual Error Reporting

For custom error handling scenarios:

```python
from monitoring.agentops_tracker import track_error

try:
    # Custom operation
    result = perform_custom_operation()
except CustomError as e:
    # Track error with context
    track_error(
        error_type="CustomError",
        error_message=str(e),
        metadata={
            "operation": "custom_processing",
            "input_size": len(data),
            "error_code": e.code
        }
    )
    raise
```

---

## Best Practices

### 1. Consistent Naming

Use consistent naming conventions for traces and operations:

```python
# Good: Descriptive and consistent
@trace(name="reddit-data-extraction", tags=["reddit", "extraction"])
def extract_reddit_data(): ...

# Good: Clear categorization
@tool(name="sentiment-analyzer", category="nlp")
def analyze_sentiment(): ...

# Avoid: Vague names
@trace(name="process_data")  # Too generic
def generic_function(): ...
```

### 2. Metadata Enrichment

Include relevant metadata for better observability:

```python
@trace(track_args=True, track_result=True)
def analyze_subreddit(subreddit: str, time_range: str) -> dict:
    """Analyze subreddit with rich metadata"""
    # AgentOps automatically captures:
    # - Function arguments
    # - Execution timing
    # - Return values
    # - Error information
    return analysis_results
```

### 3. Cost Awareness

Always enable cost tracking for LLM operations:

```python
@llm_call(model_name="anthropic/claude-3-opus", track_cost=True)
async def expensive_analysis(data: dict) -> dict:
    """Track expensive LLM calls"""
    return await claude_opus_analyze(data)
```

### 4. Session Management

Use appropriate session lifecycles:

```python
# Workflow-level session
with trace_context("market-analysis-workflow"):
    # Multiple operations within single session
    extract_data()
    analyze_data()
    generate_report()
```

### 5. Error Context

Provide rich error context for debugging:

```python
try:
    result = process_reddit_data(submissions)
except RedditAPIError as e:
    track_error(
        "RedditAPIError",
        str(e),
        metadata={
            "endpoint": e.endpoint,
            "rate_limit_remaining": e.rate_limit_remaining,
            "retry_after": e.retry_after,
            "subreddit": subreddit,
            "request_id": e.request_id
        }
    )
    raise
```

---

## Troubleshooting

### Common Issues

1. **Missing AgentOps API Key**
   ```
   Solution: Set AGENTOPS_API_KEY environment variable
   ```

2. **Tracking Not Enabled**
   ```
   Solution: Set agno_enable_agentops=True in settings
   ```

3. **High Overhead**
   ```
   Solution: Disable track_args and track_result for high-frequency functions
   ```

4. **Timeout Issues**
   ```
   Solution: Increase timeout values for long-running operations
   ```

### Debug Mode

Enable debug logging for detailed AgentOps information:

```python
import logging
logging.getLogger("monitoring.agentops_tracker").setLevel(logging.DEBUG)
```

---

## Performance Considerations

- **Tracking Overhead**: Minimal (<1ms per operation)
- **Metadata Size**: Keep metadata under 1KB per operation
- **Batch Operations**: Use session-level tracking for batch processes
- **Async Support**: Full async/await support with proper context handling

---

## Integration Examples

### Complete Workflow Example

```python
from workflows.tracked_workflow import TrackedWorkflow
from transform.agno_agents import WillingnessToPayAgent
from monitoring.agentops_decorators import trace, tool

class MarketAnalysisWorkflow(TrackedWorkflow):
    """Complete market analysis workflow with AgentOps tracking"""

    def __init__(self, config: dict):
        super().__init__(
            name="Market Analysis Workflow",
            config=config,
            enable_agentops=True
        )

        # Initialize agents with tracking
        self.wtp_agent = WillingnessToPayAgent(
            model="anthropic/claude-3-haiku",
            api_key=self.config["api_key"],
            base_url=self.config["base_url"],
            enable_agentops=True
        )

    @trace(tags=["workflow", "market-analysis"])
    async def run_analysis(self, reddit_data: dict) -> dict:
        """Run complete market analysis"""
        results = {}

        # Track individual analysis steps
        wtp_result = await self.wtp_agent.a_run(
            f"Analyze willingness to pay: {reddit_data}"
        )
        results["willingness_to_pay"] = wtp_result

        # Track workflow completion
        self.track_cost(
            amount=self.calculate_total_cost(results),
            category="market_analysis"
        )

        return results
```

---

## API Reference Summary

### Key Classes

- `AgentOpsTracker`: Core tracking functionality
- `TrackedWorkflow`: Enhanced workflow with tracking
- `BaseAgent`: Agent class with AgentOps integration
- `AgentOpsTraceContext`: Manual tracing context manager

### Key Decorators

- `@trace`: Function execution tracing
- `@tool`: Tool usage tracking
- `@llm_call`: LLM call monitoring

### Key Functions

- `get_tracker()`: Get singleton tracker instance
- `trace_context()`: Create tracing context
- `track_error()`: Manual error tracking
- `track_latency()`: Performance metric tracking

For more detailed information, see the individual component documentation and integration guides.