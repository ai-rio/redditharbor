# Cost Tracking API

<span style="color:#FF6B35; font-weight:bold;">RedditHarbor Pipeline v3</span>
<span style="color:#004E89; font-size:0.9em;">Cost Tracking and Management API Documentation</span>

---

## Overview

The Cost Tracking API provides comprehensive cost calculation, monitoring, and management capabilities for LLM operations within the RedditHarbor Pipeline v3. It supports multiple models, providers, and pricing structures with real-time cost aggregation and detailed usage analytics.

## Key Features

- **Real-time Cost Calculation**: Instant cost computation for LLM operations
- **Multi-Provider Support**: Compatible with OpenRouter, OpenAI, Anthropic, and other providers
- **Detailed Usage Tracking**: Token-level usage monitoring and cost attribution
- **Cost Aggregation**: Summarized costs across sessions, workflows, and time periods
- **Budget Management**: configurable spending limits and alerts
- **Pricing Configuration**: Flexible model pricing definitions

---

## Core Models

### `ModelCostConfig`

Defines cost configuration for different LLM models.

```python
from models.cost_tracking import ModelCostConfig
```

#### Model Definition

```python
class ModelCostConfig(BaseModel):
    model_name: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider name (openrouter, openai, etc.)")
    input_cost_per_million: float = Field(..., ge=0, description="Input token cost per 1M tokens")
    output_cost_per_million: float = Field(..., ge=0, description="Output token cost per 1M tokens")
    max_tokens: int | None = Field(None, description="Maximum tokens for model")
    supports_json_mode: bool = Field(default=True, description="Whether model supports JSON mode")
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_name` | `str` | ✅ | Unique model identifier (e.g., "anthropic/claude-3-haiku") |
| `provider` | `str` | ✅ | Provider name ("openrouter", "openai", "anthropic", etc.) |
| `input_cost_per_million` | `float` | ✅ | Cost per 1 million input tokens in USD |
| `output_cost_per_million` | `float` | ✅ | Cost per 1 million output tokens in USD |
| `max_tokens` | `int \| None` | ❌ | Maximum token limit for the model |
| `supports_json_mode` | `bool` | ❌ | Whether the model supports structured JSON output |

#### Example

```python
# Configure Claude 3 Haiku pricing
claude_haiku_config = ModelCostConfig(
    model_name="anthropic/claude-3-haiku",
    provider="openrouter",
    input_cost_per_million=0.25,    # $0.25 per 1M input tokens
    output_cost_per_million=1.25,   # $1.25 per 1M output tokens
    max_tokens=100000,
    supports_json_mode=True
)

# Configure GPT-4 Turbo pricing
gpt4_turbo_config = ModelCostConfig(
    model_name="openai/gpt-4-turbo-preview",
    provider="openrouter",
    input_cost_per_million=10.00,   # $10.00 per 1M input tokens
    output_cost_per_million=30.00,  # $30.00 per 1M output tokens
    max_tokens=128000,
    supports_json_mode=True
)
```

### `CostTracking`

Detailed cost tracking for individual LLM calls.

```python
from models.cost_tracking import CostTracking
```

#### Model Definition

```python
class CostTracking(BaseModel):
    model_used: str = Field(..., description="Model name used for the call")
    provider: str = Field(..., description="Provider used")
    prompt_tokens: int = Field(..., ge=0, description="Number of input tokens")
    completion_tokens: int = Field(..., ge=0, description="Number of output tokens")
    total_tokens: int = Field(..., ge=0, description="Total tokens used")
    input_cost_usd: float = Field(..., ge=0, description="Input token cost in USD")
    output_cost_usd: float = Field(..., ge=0, description="Output token cost in USD")
    total_cost_usd: float = Field(..., ge=0, description="Total cost in USD")
    latency_seconds: float = Field(..., ge=0, description="Request latency in seconds")
    prompt_length_chars: int = Field(..., ge=0, description="Prompt length in characters")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    model_pricing_per_m_tokens: dict[str, float] = Field(..., description="Model pricing info")
    request_success: bool = Field(..., description="Whether the request succeeded")
    error_message: str | None = Field(None, description="Error message if request failed")
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_used` | `str` | ✅ | Model identifier used for the call |
| `provider` | `str` | ✅ | API provider used |
| `prompt_tokens` | `int` | ✅ | Number of input tokens processed |
| `completion_tokens` | `int` | ✅ | Number of output tokens generated |
| `total_tokens` | `int` | ✅ | Total tokens used (prompt + completion) |
| `input_cost_usd` | `float` | ✅ | Cost for input tokens in USD |
| `output_cost_usd` | `float` | ✅ | Cost for output tokens in USD |
| `total_cost_usd` | `float` | ✅ | Total cost for the call in USD |
| `latency_seconds` | `float` | ✅ | Request execution time |
| `prompt_length_chars` | `int` | ✅ | Length of prompt in characters |
| `timestamp` | `datetime` | ❌ | When the call was made |
| `model_pricing_per_m_tokens` | `dict[str, float]` | ✅ | Pricing structure used |
| `request_success` | ✅ | Whether the call succeeded | |
| `error_message` | `str \| None` | ❌ | Error details if the call failed |

#### Cost Calculation Formula

```python
# Input token cost
input_cost = (prompt_tokens * input_cost_per_million) / 1_000_000

# Output token cost
output_cost = (completion_tokens * output_cost_per_million) / 1_000_000

# Total cost
total_cost = input_cost + output_cost
```

#### Example

```python
# Create cost tracking record
cost_record = CostTracking(
    model_used="anthropic/claude-3-haiku",
    provider="openrouter",
    prompt_tokens=1250,
    completion_tokens=340,
    total_tokens=1590,
    input_cost_usd=0.0003125,    # (1250 * 0.25) / 1_000_000
    output_cost_usd=0.000425,    # (340 * 1.25) / 1_000_000
    total_cost_usd=0.0007375,    # 0.0003125 + 0.000425
    latency_seconds=1.24,
    prompt_length_chars=5120,
    model_pricing_per_m_tokens={
        "input": 0.25,
        "output": 1.25
    },
    request_success=True
)
```

### `CostSummary`

Aggregated cost summary across multiple operations.

```python
from models.cost_tracking import CostSummary
```

#### Model Definition

```python
class CostSummary(BaseModel):
    total_cost_usd: float = Field(..., ge=0, description="Total cost across all analyses")
    total_tokens: int = Field(..., ge=0, description="Total tokens across all analyses")
    analysis_count: int = Field(..., ge=0, description="Number of analyses")
    avg_cost_per_analysis: float = Field(..., ge=0, description="Average cost per analysis")
    model_breakdown: dict[str, dict[str, Any]] = Field(..., description="Usage breakdown by model")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Summary timestamp")
```

#### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `total_cost_usd` | `float` | ✅ | Aggregate cost across all operations |
| `total_tokens` | `int` | ✅ | Total tokens processed across all operations |
| `analysis_count` | `int` | ✅ | Number of analyses/operations included |
| `avg_cost_per_analysis` | `float` | ✅ | Average cost per individual analysis |
| `model_breakdown` | `dict[str, dict[str, Any]]` | ✅ | Detailed breakdown by model |
| `timestamp` | `datetime` | ❌ | When the summary was generated |

#### Example

```python
# Create cost summary
summary = CostSummary(
    total_cost_usd=2.3456,
    total_tokens=125000,
    analysis_count=50,
    avg_cost_per_analysis=0.046912,
    model_breakdown={
        "anthropic/claude-3-haiku": {
            "calls": 30,
            "tokens": 75000,
            "cost": 0.9375,
            "avg_cost_per_call": 0.03125
        },
        "openai/gpt-4-turbo": {
            "calls": 20,
            "tokens": 50000,
            "cost": 1.4081,
            "avg_cost_per_call": 0.070405
        }
    }
)
```

---

## Cost Calculator Implementation

### Cost Calculator Class

Core cost calculation logic with model-specific pricing.

```python
from models.cost_tracking import ModelCostConfig, CostTracking, CostSummary

class CostCalculator:
    """Calculate and track LLM operation costs"""

    def __init__(self, model_configs: list[ModelCostConfig]):
        self.model_configs = {config.model_name: config for config in model_configs}

    def calculate_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_seconds: float = 0,
        prompt_length_chars: int = 0,
        success: bool = True,
        error_message: str | None = None
    ) -> CostTracking:
        """Calculate cost for a single LLM call"""

    def aggregate_costs(self, cost_records: list[CostTracking]) -> CostSummary:
        """Aggregate multiple cost records into summary"""

    def get_model_pricing(self, model_name: str) -> ModelCostConfig | None:
        """Get pricing configuration for a model"""
```

#### Usage Example

```python
# Initialize cost calculator with model configurations
calculator = CostCalculator([
    ModelCostConfig(
        model_name="anthropic/claude-3-haiku",
        provider="openrouter",
        input_cost_per_million=0.25,
        output_cost_per_million=1.25
    ),
    ModelCostConfig(
        model_name="openai/gpt-4-turbo",
        provider="openrouter",
        input_cost_per_million=10.00,
        output_cost_per_million=30.00
    )
])

# Calculate cost for a call
cost_record = calculator.calculate_cost(
    model_name="anthropic/claude-3-haiku",
    prompt_tokens=1250,
    completion_tokens=340,
    latency_seconds=1.24,
    prompt_length_chars=5120,
    success=True
)

print(f"Call cost: ${cost_record.total_cost_usd:.6f}")
```

---

## Integration with TrackedWorkflow

### Workflow Cost Tracking

The `TrackedWorkflow` class integrates cost tracking seamlessly:

```python
from workflows.tracked_workflow import TrackedWorkflow

class AnalysisWorkflow(TrackedWorkflow):
    def __init__(self, config: dict):
        super().__init__(
            name="Analysis Workflow",
            config=config,
            enable_agentops=True,
            cost_tracker=CostCalculator(model_configs)
        )

    def run(self):
        # Workflow execution with automatic cost tracking
        results = self.analyze_data()

        # Manual cost tracking
        self.track_cost(amount=0.0234, category="llm_calls")

        return results
```

### Cost Tracking Methods

#### `track_cost(amount: float, category: str = "general") -> None`

Track a cost amount within the workflow context.

**Parameters:**
- `amount` (float): Cost amount in USD
- `category` (str): Cost category for organization

**Example:**
```python
# Track different cost categories
workflow.track_cost(0.0156, category="llm_calls")
workflow.track_cost(0.0023, category="api_requests")
workflow.track_cost(0.0001, category="storage")
```

---

## Configuration

### Model Pricing Configuration

Set up model pricing in your configuration:

```python
# config/model_pricing.py
MODEL_PRICING = {
    "anthropic/claude-3-haiku": {
        "input_cost_per_million": 0.25,
        "output_cost_per_million": 1.25,
        "max_tokens": 100000
    },
    "anthropic/claude-3-sonnet": {
        "input_cost_per_million": 3.00,
        "output_cost_per_million": 15.00,
        "max_tokens": 100000
    },
    "openai/gpt-4-turbo": {
        "input_cost_per_million": 10.00,
        "output_cost_per_million": 30.00,
        "max_tokens": 128000
    },
    "openai/gpt-3.5-turbo": {
        "input_cost_per_million": 0.50,
        "output_cost_per_million": 1.50,
        "max_tokens": 4096
    }
}
```

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `COST_TRACKING_ENABLED` | `bool` | `True` | Enable/disable cost tracking |
| `COST_ALERT_THRESHOLD` | `float` | `10.0` | Alert threshold in USD |
| `COST_BUDGET_DAILY` | `float` | `100.0` | Daily budget limit in USD |

---

## Usage Examples

### Basic Cost Tracking

```python
from models.cost_tracking import ModelCostConfig, CostCalculator

# Set up pricing
configs = [
    ModelCostConfig(
        model_name="anthropic/claude-3-haiku",
        provider="openrouter",
        input_cost_per_million=0.25,
        output_cost_per_million=1.25
    )
]

# Initialize calculator
calculator = CostCalculator(configs)

# Track costs throughout application
costs = []
for analysis in analyses:
    cost = calculator.calculate_cost(
        model_name="anthropic/claude-3-haiku",
        prompt_tokens=analysis.input_tokens,
        completion_tokens=analysis.output_tokens,
        latency_seconds=analysis.duration
    )
    costs.append(cost)

# Generate summary
summary = calculator.aggregate_costs(costs)
print(f"Total cost: ${summary.total_cost_usd:.4f}")
print(f"Average per analysis: ${summary.avg_cost_per_analysis:.6f}")
```

### Advanced Cost Tracking with AgentOps

```python
from monitoring.agentops_decorators import llm_call
from monitoring.agentops_tracker import get_tracker

@llm_call(model_name="anthropic/claude-3-haiku", track_cost=True)
async def analyze_with_cost_tracking(text: str) -> dict:
    """Analyze text with automatic cost tracking"""
    # LLM call implementation
    response = await claude_client.messages.create(
        model="claude-3-haiku",
        messages=[{"role": "user", "content": text}]
    )
    return response

# Usage with cost tracking
tracker = get_tracker()
result = await analyze_with_cost_tracking(sample_text)

# Cost is automatically tracked and available in AgentOps dashboard
```

### Cost Monitoring and Alerts

```python
class CostMonitor:
    def __init__(self, daily_budget: float, alert_threshold: float):
        self.daily_budget = daily_budget
        self.alert_threshold = alert_threshold
        self.daily_spend = 0.0

    def track_cost(self, cost_record: CostTracking):
        """Track cost and check for alerts"""
        self.daily_spend += cost_record.total_cost_usd

        # Check if we're approaching budget
        if self.daily_spend >= self.daily_budget:
            self.send_alert(f"Daily budget exceeded: ${self.daily_spend:.2f}")
        elif self.daily_spend >= self.alert_threshold:
            self.send_alert(f"Approaching alert threshold: ${self.daily_spend:.2f}")

    def send_alert(self, message: str):
        """Send cost alert notification"""
        # Integration with notification system
        logger.warning(f"Cost Alert: {message}")

# Usage
monitor = CostMonitor(daily_budget=50.0, alert_threshold=40.0)
monitor.track_cost(cost_record)
```

---

## Performance Considerations

### Optimization Strategies

1. **Model Selection**: Choose cost-effective models for different tasks
2. **Token Optimization**: Minimize prompt and response lengths
3. **Batch Processing**: Group requests to reduce overhead
4. **Caching**: Cache responses when appropriate

### Cost Analysis

```python
def analyze_cost_efficiency(cost_records: list[CostTracking]) -> dict:
    """Analyze cost efficiency across models"""

    model_stats = {}
    for record in cost_records:
        model = record.model_used
        if model not in model_stats:
            model_stats[model] = {
                "total_cost": 0,
                "total_tokens": 0,
                "calls": 0,
                "avg_latency": 0
            }

        stats = model_stats[model]
        stats["total_cost"] += record.total_cost_usd
        stats["total_tokens"] += record.total_tokens
        stats["calls"] += 1
        stats["avg_latency"] += record.latency_seconds

    # Calculate averages and efficiency metrics
    for model, stats in model_stats.items():
        stats["avg_cost_per_call"] = stats["total_cost"] / stats["calls"]
        stats["cost_per_1k_tokens"] = (stats["total_cost"] / stats["total_tokens"]) * 1000
        stats["avg_latency"] = stats["avg_latency"] / stats["calls"]

    return model_stats
```

---

## Error Handling

### Cost Tracking Failures

```python
try:
    cost_record = calculator.calculate_cost(
        model_name="unknown-model",
        prompt_tokens=1000,
        completion_tokens=500
    )
except ValueError as e:
    # Handle unknown model error
    logger.error(f"Model not configured: {e}")
    # Fallback to default pricing
    cost_record = calculator.calculate_cost_with_defaults(...)
```

### Data Validation

```python
from pydantic import ValidationError

try:
    cost_record = CostTracking(
        model_used="claude-3-haiku",
        provider="openrouter",
        prompt_tokens=-100,  # Invalid negative value
        completion_tokens=200,
        total_tokens=100,
        input_cost_usd=0.001,
        output_cost_usd=0.002,
        total_cost_usd=0.003,
        latency_seconds=1.0,
        prompt_length_chars=1000,
        model_pricing_per_m_tokens={"input": 0.25, "output": 1.25},
        request_success=True
    )
except ValidationError as e:
    # Handle validation errors
    logger.error(f"Invalid cost tracking data: {e}")
```

---

## Best Practices

### 1. Consistent Model Naming

Use consistent model identifiers across your application:

```python
# Good: Use full model names from provider
MODEL_MAPPING = {
    "claude-haiku": "anthropic/claude-3-haiku",
    "claude-sonnet": "anthropic/claude-3-sonnet",
    "gpt4-turbo": "openai/gpt-4-turbo-preview"
}
```

### 2. Granular Cost Tracking

Track costs at appropriate granularity:

```python
# Track individual operations
for task in tasks:
    cost = calculator.calculate_cost(
        model_name=task.model,
        prompt_tokens=task.input_tokens,
        completion_tokens=task.output_tokens
    )
    task.cost = cost.total_cost_usd

# Aggregate by category
category_costs = {}
for task in tasks:
    category = task.category
    if category not in category_costs:
        category_costs[category] = 0
    category_costs[category] += task.cost
```

### 3. Regular Cost Reviews

Implement periodic cost analysis:

```python
def daily_cost_report():
    """Generate daily cost analysis report"""
    yesterday = datetime.now() - timedelta(days=1)
    costs = get_costs_for_date(yesterday)

    summary = calculator.aggregate_costs(costs)

    report = f"""
    Daily Cost Report for {yesterday.date()}:
    - Total Cost: ${summary.total_cost_usd:.4f}
    - Total Tokens: {summary.total_tokens:,}
    - Analyses: {summary.analysis_count}
    - Avg Cost per Analysis: ${summary.avg_cost_per_analysis:.6f}

    Model Breakdown:
    """

    for model, stats in summary.model_breakdown.items():
        report += f"- {model}: ${stats['cost']:.4f} ({stats['calls']} calls)\n"

    send_report(report)
```

### 4. Budget Management

Implement budget controls:

```python
class BudgetManager:
    def __init__(self, monthly_budget: float):
        self.monthly_budget = monthly_budget
        self.current_spend = 0.0

    def can_spend(self, amount: float) -> bool:
        """Check if we can spend the specified amount"""
        return (self.current_spend + amount) <= self.monthly_budget

    def record_spend(self, amount: float):
        """Record actual spending"""
        self.current_spend += amount

    def get_remaining_budget(self) -> float:
        """Get remaining budget"""
        return self.monthly_budget - self.current_spend
```

---

## API Reference Summary

### Core Classes

- `ModelCostConfig`: Model pricing configuration
- `CostTracking`: Individual call cost tracking
- `CostSummary`: Aggregated cost summary
- `CostCalculator`: Cost calculation logic

### Key Methods

- `calculate_cost()`: Calculate cost for individual calls
- `aggregate_costs()`: Summarize multiple cost records
- `track_cost()`: Track cost within workflows
- `get_model_pricing()`: Retrieve model pricing info

### Integration Points

- `TrackedWorkflow`: Workflow-level cost tracking
- `@llm_call` decorator: Automatic LLM call cost tracking
- `AgentOpsTracker`: Cost integration with observability

For additional details on configuration and advanced usage patterns, see the integration examples and best practices sections.