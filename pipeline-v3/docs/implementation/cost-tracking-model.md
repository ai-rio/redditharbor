# Cost Tracking Model and Pricing Calculations

<span style="color:#FF6B35; font-weight:bold;">RedditHarbor Pipeline v3</span>
<span style="color:#004E89; font-size:0.9em;">Comprehensive Cost Tracking Architecture and Implementation Guide</span>

---

## Table of Contents

1. [Overview and Architecture](#overview-and-architecture)
2. [Cost Model Implementation](#cost-model-implementation)
3. [Cost Calculation Logic](#cost-calculation-logic)
4. [Cost Optimization Strategies](#cost-optimization-strategies)
5. [Reporting and Analytics](#reporting-and-analytics)
6. [Integration Points](#integration-points)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting and Best Practices](#troubleshooting-and-best-practices)

---

## Overview and Architecture

### Cost Tracking Architecture

The RedditHarbor Pipeline v3 implements a comprehensive cost tracking system designed to monitor, calculate, and optimize LLM operation costs across multiple models, providers, and usage patterns. The architecture is built around three core principles:

1. **Real-time Calculation**: Costs are computed immediately after each LLM operation
2. **Granular Tracking**: Token-level attribution with detailed metadata
3. **Flexible Aggregation**: Support for multiple aggregation strategies and reporting levels

### Core Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Cost Tracking System                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │    Models   │    │ Calculator  │    │ Aggregator  │     │
│  │             │    │             │    │             │     │
│  │ • ModelCost │    │ • Token     │    │ • Session   │     │
│  │   Config    │    │   Math      │    │   Level     │     │
│  │ • CostTrack │    │ • Provider  │    │ • Agent     │     │
│  │   ing       │    │   Logic     │    │   Level     │     │
│  │ • CostSum   │    │ • Pricing   │    │ • Time      │     │
│  │   mary      │    │   Tables    │    │   Based     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Integration Layer                          │ │
│  │                                                         │ │
│  │ • LiteLLM Integration      • AgentOps Tracking         │ │
│  │ • Database Persistence     • Workflow Integration      │ │
│  │ • Configuration Manager    • Alert System              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

1. **LLM Call Initiation**
   - Request captured with metadata (model, provider, parameters)
   - Token counting begins
   - Timer starts for latency measurement

2. **Cost Calculation**
   - Token counts extracted from API response
   - Cost computed using model-specific pricing
   - Record created with full context

3. **Storage and Aggregation**
   - Individual cost records stored in database
   - Real-time aggregation for summaries
   - Updates to session/agent/workflow totals

4. **Reporting and Alerts**
   - Cost summaries generated
   - Threshold checks performed
   - Notifications sent if needed

### Pricing Model Structure

The cost tracking system supports a flexible pricing model that accommodates:

- **Provider-specific pricing**: Different rates for OpenRouter, OpenAI, Anthropic, etc.
- **Token-based billing**: Separate pricing for input and output tokens
- **Volume discounts**: Tiered pricing based on usage volume
- **Special rates**: Custom pricing for specific models or use cases

---

## Cost Model Implementation

### ModelCostConfig Class

The `ModelCostConfig` class defines the pricing structure for each LLM model:

```python
from models.cost_tracking import ModelCostConfig

class ModelCostConfig(BaseModel):
    model_name: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider name (openrouter, openai, etc.)")
    input_cost_per_million: float = Field(..., ge=0, description="Input token cost per 1M tokens")
    output_cost_per_million: float = Field(..., ge=0, description="Output token cost per 1M tokens")
    max_tokens: int | None = Field(None, description="Maximum tokens for model")
    supports_json_mode: bool = Field(default=True, description="Whether model supports JSON mode")
```

#### Model Pricing Configuration

Current model pricing configurations in the system:

```python
MODEL_PRICING = {
    "anthropic/claude-haiku-4.5": ModelCostConfig(
        model_name="anthropic/claude-haiku-4.5",
        provider="openrouter",
        input_cost_per_million=1.0,      # $1.00 per 1M input tokens
        output_cost_per_million=5.0,     # $5.00 per 1M output tokens
        max_tokens=200000,
        supports_json_mode=True
    ),
    "anthropic/claude-3.5-sonnet": ModelCostConfig(
        model_name="anthropic/claude-3.5-sonnet",
        provider="openrouter",
        input_cost_per_million=3.0,      # $3.00 per 1M input tokens
        output_cost_per_million=15.0,    # $15.00 per 1M output tokens
        max_tokens=200000,
        supports_json_mode=True
    ),
    "openai/gpt-4o-mini": ModelCostConfig(
        model_name="openai/gpt-4o-mini",
        provider="openrouter",
        input_cost_per_million=0.15,     # $0.15 per 1M input tokens
        output_cost_per_million=0.60,    # $0.60 per 1M output tokens
        max_tokens=128000,
        supports_json_mode=True
    ),
    "meta-llama/llama-3.1-8b-instruct:floor": ModelCostConfig(
        model_name="meta-llama/llama-3.1-8b-instruct:floor",
        provider="openrouter",
        input_cost_per_million=0.10,     # $0.10 per 1M input tokens
        output_cost_per_million=0.10,    # $0.10 per 1M output tokens
        max_tokens=128000,
        supports_json_mode=True
    )
}
```

### CostTracking Class

The `CostTracking` class captures detailed cost information for individual LLM calls:

```python
from models.cost_tracking import CostTracking

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

### AgnoCostCalculator Class Implementation

The cost calculator implements the core pricing logic:

```python
class AgnoCostCalculator:
    """
    Calculate and track costs for Agno multi-agent operations
    """

    def __init__(self, model_configs: dict[str, ModelCostConfig]):
        self.model_configs = model_configs
        self.cost_history: list[CostTracking] = []

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
        """
        Calculate cost for a single LLM call using the formula:
        cost = (tokens * cost_per_million) / 1_000_000

        Args:
            model_name: Name of the model used
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            latency_seconds: Request execution time
            prompt_length_chars: Length of prompt in characters
            success: Whether the request succeeded
            error_message: Error details if failed

        Returns:
            CostTracking object with detailed cost information
        """
        model_config = self.model_configs.get(model_name)

        if not model_config:
            # Use default pricing for unknown models
            model_config = ModelCostConfig(
                model_name=model_name,
                provider="unknown",
                input_cost_per_million=1.0,
                output_cost_per_million=5.0
            )

        # Calculate costs using the formula
        input_cost = (prompt_tokens * model_config.input_cost_per_million) / 1_000_000
        output_cost = (completion_tokens * model_config.output_cost_per_million) / 1_000_000
        total_cost = input_cost + output_cost

        # Create cost tracking record
        cost_record = CostTracking(
            model_used=model_name,
            provider=model_config.provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            input_cost_usd=round(input_cost, 6),
            output_cost_usd=round(output_cost, 6),
            total_cost_usd=round(total_cost, 6),
            latency_seconds=round(latency_seconds, 3),
            prompt_length_chars=prompt_length_chars,
            model_pricing_per_m_tokens={
                "input": model_config.input_cost_per_million,
                "output": model_config.output_cost_per_million
            },
            request_success=success,
            error_message=error_message
        )

        # Store in history
        self.cost_history.append(cost_record)

        return cost_record
```

---

## Cost Calculation Logic

### Core Calculation Formula

The cost calculation follows a precise formula:

```python
# Basic cost calculation
input_cost = (prompt_tokens * input_cost_per_million) / 1_000_000
output_cost = (completion_tokens * output_cost_per_million) / 1_000_000
total_cost = input_cost + output_cost
```

### Token-based Pricing Examples

#### Example 1: Claude Haiku Analysis
```python
# Model: anthropic/claude-haiku-4.5
# Pricing: $1.00 per 1M input tokens, $5.00 per 1M output tokens
# Usage: 2,500 input tokens, 800 output tokens

prompt_tokens = 2500
completion_tokens = 800
input_cost_per_million = 1.0
output_cost_per_million = 5.0

# Calculation
input_cost = (2500 * 1.0) / 1_000_000 = 0.0025  # $0.0025
output_cost = (800 * 5.0) / 1_000_000 = 0.0040  # $0.0040
total_cost = 0.0025 + 0.0040 = 0.0065           # $0.0065 total
```

#### Example 2: GPT-4o Mini Batch Processing
```python
# Model: openai/gpt-4o-mini
# Pricing: $0.15 per 1M input tokens, $0.60 per 1M output tokens
# Batch: 100 analyses, average 1,500 input tokens, 400 output tokens each

batch_size = 100
avg_prompt_tokens = 1500
avg_completion_tokens = 400
input_cost_per_million = 0.15
output_cost_per_million = 0.60

# Per analysis cost
per_analysis_input_cost = (1500 * 0.15) / 1_000_000 = 0.000225
per_analysis_output_cost = (400 * 0.60) / 1_000_000 = 0.000240
per_analysis_total = 0.000225 + 0.000240 = 0.000465

# Batch total
batch_total_cost = 100 * 0.000465 = 0.0465  # $0.0465 for 100 analyses
```

### Category-based Cost Tracking

The system categorizes costs into different types for better analysis:

```python
COST_CATEGORIES = {
    "llm_calls": {
        "description": "Direct LLM API calls",
        "models": ["anthropic/claude-haiku-4.5", "openai/gpt-4o-mini", "meta-llama/llama-3.1-8b-instruct"],
        "typical_cost_range": "$0.0001 - $0.10 per call"
    },
    "embeddings": {
        "description": "Text embedding generation",
        "models": ["text-embedding-ada-002", "text-embedding-3-small"],
        "typical_cost_range": "$0.00002 - $0.00010 per 1K tokens"
    },
    "api_requests": {
        "description": "External API calls (Jina, Reddit, etc.)",
        "models": ["jina-reader", "reddit-api"],
        "typical_cost_range": "$0.001 - $0.05 per request"
    },
    "tool_usage": {
        "description": "Tool invocation and execution",
        "models": ["various-tools"],
        "typical_cost_range": "$0.0001 - $0.01 per tool use"
    },
    "agent_coordination": {
        "description": "Multi-agent orchestration overhead",
        "models": ["agno-orchestrator"],
        "typical_cost_range": "$0.01 - $0.10 per coordination step"
    }
}
```

### Aggregation Strategies

#### Session-level Aggregation
```python
def aggregate_session_costs(session_id: str) -> CostSummary:
    """
    Aggregate all costs within a session
    """
    session_costs = [
        cost for cost in cost_history
        if cost.session_id == session_id
    ]

    return calculate_cost_summary(session_costs)
```

#### Agent-level Aggregation
```python
def aggregate_agent_costs(agent_name: str, time_window: timedelta) -> CostSummary:
    """
    Aggregate costs for a specific agent within a time window
    """
    cutoff_time = datetime.utcnow() - time_window
    agent_costs = [
        cost for cost in cost_history
        if cost.agent_name == agent_name and cost.timestamp >= cutoff_time
    ]

    return calculate_cost_summary(agent_costs)
```

#### Workflow-level Aggregation
```python
def aggregate_workflow_costs(workflow_id: str) -> CostSummary:
    """
    Aggregate costs for an entire workflow
    """
    workflow_costs = [
        cost for cost in cost_history
        if cost.workflow_id == workflow_id
    ]

    # Group by step
    step_costs = {}
    for cost in workflow_costs:
        step = cost.workflow_step
        if step not in step_costs:
            step_costs[step] = []
        step_costs[step].append(cost)

    return {
        "total": calculate_cost_summary(workflow_costs),
        "by_step": {step: calculate_cost_summary(costs)
                   for step, costs in step_costs.items()}
    }
```

### Context Window Considerations

When calculating costs, the system considers context window limitations:

```python
def calculate_optimal_batch_size(
    model_name: str,
    avg_prompt_tokens: int,
    avg_completion_tokens: int,
    max_batch_cost: float = 0.10
) -> int:
    """
    Calculate optimal batch size based on model constraints and cost limits
    """
    model_config = model_costs[model_name]

    # Cost constraint
    cost_per_request = (
        (avg_prompt_tokens * model_config.input_cost_per_million) +
        (avg_completion_tokens * model_config.output_cost_per_million)
    ) / 1_000_000

    max_batch_by_cost = int(max_batch_cost / cost_per_request)

    # Context window constraint
    max_batch_by_tokens = model_config.max_tokens // (avg_prompt_tokens + avg_completion_tokens)

    # Return the conservative estimate
    return min(max_batch_by_cost, max_batch_by_tokens, 10)  # Max 10 for reliability
```

### Batch Processing Discounts

The system applies volume discounts for high-volume processing:

```python
VOLUME_DISCOUNTS = {
    "monthly_tokens": {
        100_000: 0.05,      # 5% discount for 100K+ tokens
        1_000_000: 0.10,    # 10% discount for 1M+ tokens
        10_000_000: 0.20,   # 20% discount for 10M+ tokens
        100_000_000: 0.30   # 30% discount for 100M+ tokens
    }
}

def apply_volume_discount(base_cost: float, monthly_token_usage: int) -> float:
    """
    Apply volume discount based on monthly usage
    """
    discount = 0.0
    for threshold, discount_rate in VOLUME_DISCOUNTS["monthly_tokens"].items():
        if monthly_token_usage >= threshold:
            discount = max(discount, discount_rate)

    return base_cost * (1 - discount)
```

---

## Cost Optimization Strategies

### Model Selection Optimization

#### Cost vs. Performance Matrix

| Model | Cost/1M Input | Cost/1M Output | Performance | Best Use Case |
|-------|---------------|----------------|-------------|---------------|
| Claude Haiku 4.5 | $1.00 | $5.00 | High | Simple analyses, high volume |
| Claude 3.5 Sonnet | $3.00 | $15.00 | Very High | Complex reasoning, critical tasks |
| GPT-4o Mini | $0.15 | $0.60 | Medium | Batch processing, general use |
| Llama 3.1 8B | $0.10 | $0.10 | Medium | Cost-sensitive applications |

#### Model Routing Strategy

```python
class ModelRouter:
    """
    Intelligent model routing based on task complexity and cost constraints
    """

    def __init__(self):
        self.complexity_thresholds = {
            "simple": 0.3,      # Use cheapest models
            "medium": 0.7,      # Use mid-range models
            "complex": 1.0      # Use best models
        }

        self.model_mapping = {
            "simple": "meta-llama/llama-3.1-8b-instruct:floor",
            "medium": "openai/gpt-4o-mini",
            "complex": "anthropic/claude-3.5-sonnet"
        }

    def select_model(
        self,
        task_complexity: float,
        budget_constraint: float | None = None
    ) -> str:
        """
        Select optimal model based on task complexity and budget
        """
        if budget_constraint is not None:
            # Budget-constrained selection
            affordable_models = [
                model for model, pricing in MODEL_PRICING.items()
                if pricing.input_cost_per_million <= budget_constraint * 1_000_000
            ]
            if affordable_models:
                return affordable_models[0]

        # Complexity-based selection
        if task_complexity <= self.complexity_thresholds["simple"]:
            return self.model_mapping["simple"]
        elif task_complexity <= self.complexity_thresholds["medium"]:
            return self.model_mapping["medium"]
        else:
            return self.model_mapping["complex"]
```

### Token Optimization

#### Prompt Optimization Techniques

1. **Efficient Prompt Design**
```python
def optimize_prompt_template(template: str) -> str:
    """
    Optimize prompt templates for minimal token usage
    """
    # Remove redundant phrases
    template = re.sub(r'\b(please|kindly|could you)\b', '', template, flags=re.IGNORECASE)

    # Use shorter alternatives
    replacements = {
        "provide me with": "give",
        "explain in detail": "explain",
        "list all of": "list",
        "what is the": "what's",
        "you are to": "you're to"
    }

    for old, new in replacements.items():
        template = template.replace(old, new)

    # Remove extra whitespace
    template = re.sub(r'\s+', ' ', template).strip()

    return template
```

2. **Response Caching**
```python
class ResponseCache:
    """
    Cache LLM responses to avoid duplicate calls
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 24 * 60 * 60  # 24 hours

    def get_cache_key(self, model: str, prompt: str) -> str:
        """Generate cache key for prompt-model pair"""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get_cached_response(self, model: str, prompt: str) -> dict | None:
        """Retrieve cached response if available"""
        cache_key = self.get_cache_key(model, prompt)
        cached = await self.redis.get(cache_key)

        if cached:
            return json.loads(cached)
        return None

    async def cache_response(
        self,
        model: str,
        prompt: str,
        response: dict,
        cost: float
    ) -> None:
        """Cache successful response with cost metadata"""
        cache_key = self.get_cache_key(model, prompt)
        data = {
            "response": response,
            "cost": cost,
            "cached_at": datetime.utcnow().isoformat()
        }

        await self.redis.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(data)
        )
```

3. **Batch Processing**
```python
async def process_batch_optimized(
    items: list[dict],
    model: str,
    max_batch_size: int = 10,
    max_context_tokens: int = 100000
) -> list[dict]:
    """
    Process items in optimal batches to minimize cost
    """
    results = []

    # Sort by item size for better packing
    sorted_items = sorted(items, key=lambda x: len(str(x)), reverse=True)

    while sorted_items:
        batch = []
        batch_tokens = 0

        # Greedy bin packing
        for item in sorted_items[:]:
            item_tokens = estimate_tokens(str(item))

            if (len(batch) < max_batch_size and
                batch_tokens + item_tokens <= max_context_tokens):
                batch.append(item)
                batch_tokens += item_tokens
                sorted_items.remove(item)

        if batch:
            # Process batch
            batch_result = await process_batch_items(batch, model)
            results.extend(batch_result)

    return results
```

### Monitoring and Alerts

#### Real-time Cost Monitoring

```python
class CostMonitor:
    """
    Real-time cost monitoring with intelligent alerts
    """

    def __init__(self, config: dict):
        self.daily_budget = config.get("daily_budget", 100.0)
        self.hourly_budget = self.daily_budget / 24
        self.alert_thresholds = config.get("alert_thresholds", [0.5, 0.8, 0.95])
        self.current_spend = {"daily": 0.0, "hourly": 0.0}
        self.last_reset = {"daily": datetime.now().date(), "hourly": datetime.now().hour}

    def track_cost(self, cost_record: CostTracking) -> None:
        """
        Track cost and trigger alerts if necessary
        """
        # Reset counters if needed
        self._reset_counters_if_needed()

        # Update spend
        self.current_spend["daily"] += cost_record.total_cost_usd
        self.current_spend["hourly"] += cost_record.total_cost_usd

        # Check alerts
        self._check_alerts()

        # Log significant costs
        if cost_record.total_cost_usd > 0.01:
            logger.info(
                f"Significant cost: ${cost_record.total_cost_usd:.6f} "
                f"for {cost_record.model_used} "
                f"({cost_record.total_tokens} tokens)"
            )

    def _check_alerts(self) -> None:
        """Check if alerts should be triggered"""
        daily_ratio = self.current_spend["daily"] / self.daily_budget
        hourly_ratio = self.current_spend["hourly"] / self.hourly_budget

        for threshold in self.alert_thresholds:
            if daily_ratio >= threshold:
                self._send_alert(
                    f"Daily spend at {daily_ratio:.1%} of budget "
                    f"(${self.current_spend['daily']:.2f}/${self.daily_budget:.2f})"
                )
                break

        if hourly_ratio > 1.5:  # Hourly overspend alert
            self._send_alert(
                f"Hourly spend exceeded by {hourly_ratio:.1%} "
                f"(${self.current_spend['hourly']:.2f}/${self.hourly_budget:.2f})"
            )
```

#### Predictive Cost Analysis

```python
class CostPredictor:
    """
    Predict future costs based on historical patterns
    """

    def __init__(self, historical_window_days: int = 30):
        self.historical_window = timedelta(days=historical_window_days)

    def predict_monthly_spend(self, current_spend: float, days_in_month: int) -> dict:
        """
        Predict monthly spend based on current trajectory
        """
        today = datetime.now()
        days_passed = today.day
        avg_daily_spend = current_spend / days_passed

        predicted_monthly = avg_daily_spend * days_in_month
        remaining_budget = self.monthly_budget - current_spend
        recommended_daily_limit = remaining_budget / (days_in_month - days_passed)

        return {
            "predicted_monthly_spend": predicted_monthly,
            "predicted_vs_budget": predicted_monthly - self.monthly_budget,
            "recommended_daily_limit": recommended_daily_limit,
            "on_track": predicted_monthly <= self.monthly_budget * 1.1  # 10% tolerance
        }

    def detect_cost_anomalies(self, recent_costs: list[CostTracking]) -> list[dict]:
        """
        Detect anomalous cost patterns
        """
        if len(recent_costs) < 10:
            return []

        # Calculate baseline
        baseline_costs = [c.total_cost_usd for c in recent_costs[:-5]]
        recent_values = [c.total_cost_usd for c in recent_costs[-5:]]

        baseline_mean = statistics.mean(baseline_costs)
        baseline_std = statistics.stdev(baseline_costs)

        anomalies = []
        for i, cost_record in enumerate(recent_costs[-5:]):
            z_score = (cost_record.total_cost_usd - baseline_mean) / baseline_std

            if abs(z_score) > 3:  # 3 standard deviations
                anomalies.append({
                    "record": cost_record,
                    "z_score": z_score,
                    "reason": f"Cost {z_score:.1f}σ from baseline",
                    "severity": "high" if abs(z_score) > 5 else "medium"
                })

        return anomalies
```

---

## Reporting and Analytics

### Cost Reports Generation

#### Daily Cost Report
```python
def generate_daily_cost_report(date: datetime.date) -> dict:
    """
    Generate comprehensive daily cost report
    """
    costs = get_costs_for_date(date)
    summary = calculate_cost_summary(costs)

    # Hourly breakdown
    hourly_breakdown = {}
    for cost in costs:
        hour = cost.timestamp.hour
        if hour not in hourly_breakdown:
            hourly_breakdown[hour] = {"count": 0, "cost": 0.0, "tokens": 0}

        hourly_breakdown[hour]["count"] += 1
        hourly_breakdown[hour]["cost"] += cost.total_cost_usd
        hourly_breakdown[hour]["tokens"] += cost.total_tokens

    # Model efficiency analysis
    model_efficiency = {}
    for model_name in set(c.model_used for c in costs):
        model_costs = [c for c in costs if c.model_used == model_name]
        avg_latency = statistics.mean(c.latency_seconds for c in model_costs)
        cost_per_1k_tokens = (
            sum(c.total_cost_usd for c in model_costs) /
            sum(c.total_tokens for c in model_costs) * 1000
        )

        model_efficiency[model_name] = {
            "calls": len(model_costs),
            "total_cost": sum(c.total_cost_usd for c in model_costs),
            "avg_latency": avg_latency,
            "cost_per_1k_tokens": cost_per_1k_tokens,
            "tokens_per_dollar": 1000 / cost_per_1k_tokens if cost_per_1k_tokens > 0 else 0
        }

    return {
        "date": date.isoformat(),
        "summary": {
            "total_cost": summary.total_cost_usd,
            "total_calls": summary.analysis_count,
            "total_tokens": summary.total_tokens,
            "avg_cost_per_call": summary.avg_cost_per_analysis,
            "avg_tokens_per_call": summary.total_tokens / summary.analysis_count if summary.analysis_count > 0 else 0
        },
        "hourly_breakdown": hourly_breakdown,
        "model_efficiency": model_efficiency,
        "top_expensive_calls": sorted(costs, key=lambda c: c.total_cost_usd, reverse=True)[:10],
        "cost_savings": calculate_cost_savings(costs)
    }
```

#### Weekly and Monthly Summaries
```python
def generate_period_summary(
    start_date: datetime.date,
    end_date: datetime.date
) -> dict:
    """
    Generate summary for a date range (week/month)
    """
    costs = get_costs_for_date_range(start_date, end_date)
    summary = calculate_cost_summary(costs)

    # Trend analysis
    daily_costs = {}
    for date in daterange(start_date, end_date):
        daily_costs[date] = get_costs_for_date(date)

    # Growth rates
    costs_by_day = [sum(c.total_cost_usd for c in daily_costs[date]) for date in daily_costs]
    if len(costs_by_day) > 1:
        daily_trend = (costs_by_day[-1] - costs_by_day[0]) / len(costs_by_day)
    else:
        daily_trend = 0

    # Cost projection
    avg_daily_cost = statistics.mean(costs_by_day) if costs_by_day else 0
    days_in_period = (end_date - start_date).days + 1
    projected_monthly = avg_daily_cost * 30

    return {
        "period": f"{start_date} to {end_date}",
        "summary": summary,
        "trends": {
            "daily_average": avg_daily_cost,
            "daily_trend": daily_trend,
            "weekly_growth": calculate_growth_rate(costs_by_day, period=7),
            "monthly_projection": projected_monthly
        },
        "cost_distribution": calculate_cost_distribution(costs),
        "efficiency_metrics": calculate_efficiency_metrics(costs),
        "recommendations": generate_cost_recommendations(summary, daily_trend)
    }
```

### Performance Metrics

#### Cost Per Analysis
```python
def calculate_cost_per_analysis(costs: list[CostTracking], category: str) -> dict:
    """
    Calculate cost metrics for different analysis types
    """
    category_costs = [c for c in costs if c.analysis_category == category]

    if not category_costs:
        return {}

    total_cost = sum(c.total_cost_usd for c in category_costs)
    total_tokens = sum(c.total_tokens for c in category_costs)
    total_analyses = len(category_costs)

    return {
        "category": category,
        "total_cost": total_cost,
        "cost_per_analysis": total_cost / total_analyses,
        "cost_per_1k_tokens": (total_cost / total_tokens) * 1000 if total_tokens > 0 else 0,
        "tokens_per_analysis": total_tokens / total_analyses,
        "analyses_per_dollar": total_analyses / total_cost if total_cost > 0 else 0,
        "efficiency_score": calculate_efficiency_score(category_costs)
    }
```

#### ROI Calculations
```python
def calculate_analysis_roi(
    costs: list[CostTracking],
    outcomes: list[dict],
    business_value_per_opportunity: float = 1000.0
) -> dict:
    """
    Calculate return on investment for analysis operations
    """
    # Total investment
    total_cost = sum(c.total_cost_usd for c in costs)

    # Count successful opportunities identified
    successful_opportunities = sum(
        1 for outcome in outcomes
        if outcome.get("final_score", 0) > 70  # High-scoring opportunities
    )

    # Calculate ROI
    estimated_value = successful_opportunities * business_value_per_opportunity
    roi = (estimated_value - total_cost) / total_cost if total_cost > 0 else 0

    # Efficiency metrics
    opportunities_per_dollar = successful_opportunities / total_cost if total_cost > 0 else 0
    cost_per_opportunity = total_cost / successful_opportunities if successful_opportunities > 0 else 0

    return {
        "total_investment": total_cost,
        "opportunities_identified": successful_opportunities,
        "estimated_business_value": estimated_value,
        "roi_percentage": roi * 100,
        "roi_ratio": estimated_value / total_cost if total_cost > 0 else 0,
        "cost_per_opportunity": cost_per_opportunity,
        "opportunities_per_dollar": opportunities_per_dollar,
        "break_even_opportunities": total_cost / business_value_per_opportunity
    }
```

### Integration Points

#### LiteLLM Integration
```python
class LiteLLMCostTracker:
    """
    Integrate cost tracking with LiteLLM calls
    """

    def __init__(self, cost_calculator: AgnoCostCalculator):
        self.cost_calculator = cost_calculator

    async def tracked_completion(
        self,
        model: str,
        messages: list[dict],
        **kwargs
    ) -> tuple[dict, CostTracking]:
        """
        Execute LiteLLM completion with automatic cost tracking
        """
        start_time = time.time()

        # Make the API call
        response = await litellm.acompletion(
            model=f"openrouter/{model}",
            messages=messages,
            **kwargs
        )

        # Extract usage information
        usage = response.usage or {}
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens

        # Calculate cost
        latency = time.time() - start_time
        cost_tracking = self.cost_calculator.calculate_cost(
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_seconds=latency,
            prompt_length_chars=len(str(messages))
        )

        return response, cost_tracking
```

#### AgentOps Integration
```python
class AgentOpsCostIntegration:
    """
    Integrate cost tracking with AgentOps monitoring
    """

    def __init__(self, agentops_tracker, cost_calculator):
        self.agentops_tracker = agentops_tracker
        self.cost_calculator = cost_calculator

    def track_llm_call_with_cost(
        self,
        cost_record: CostTracking,
        metadata: dict | None = None
    ) -> None:
        """
        Track LLM call cost in AgentOps
        """
        self.agentops_tracker.track_llm_call(
            model=cost_record.model_used,
            tokens=cost_record.total_tokens,
            cost=cost_record.total_cost_usd,
            latency=cost_record.latency_seconds,
            success=cost_record.request_success,
            metadata={
                **metadata,
                "prompt_tokens": cost_record.prompt_tokens,
                "completion_tokens": cost_record.completion_tokens,
                "provider": cost_record.provider
            }
        )

    def track_session_cost_summary(self, session_costs: list[CostTracking]) -> None:
        """
        Track aggregated session costs
        """
        summary = self.cost_calculator.aggregate_costs(session_costs)

        self.agentops_tracker.track_event(
            "session_cost_summary",
            {
                "total_cost": summary.total_cost_usd,
                "total_tokens": summary.total_tokens,
                "call_count": summary.analysis_count,
                "model_breakdown": summary.model_breakdown,
                "avg_cost_per_call": summary.avg_cost_per_analysis
            }
        )
```

#### Database Persistence
```python
class CostDatabaseManager:
    """
    Persist cost tracking data to database
    """

    def __init__(self, db_session):
        self.db = db_session

    async def store_cost_record(self, cost_record: CostTracking) -> None:
        """
        Store individual cost record
        """
        query = """
        INSERT INTO cost_tracking (
            model_used, provider, prompt_tokens, completion_tokens,
            total_tokens, input_cost_usd, output_cost_usd, total_cost_usd,
            latency_seconds, prompt_length_chars, timestamp,
            model_pricing_per_m_tokens, request_success, error_message,
            session_id, agent_name, workflow_id, analysis_category
        ) VALUES (
            :model_used, :provider, :prompt_tokens, :completion_tokens,
            :total_tokens, :input_cost_usd, :output_cost_usd, :total_cost_usd,
            :latency_seconds, :prompt_length_chars, :timestamp,
            :model_pricing_per_m_tokens, :request_success, :error_message,
            :session_id, :agent_name, :workflow_id, :analysis_category
        )
        """

        await self.db.execute(query, cost_record.dict())
        await self.db.commit()

    async def get_cost_history(
        self,
        start_date: datetime,
        end_date: datetime,
        model_name: str | None = None,
        agent_name: str | None = None
    ) -> list[CostTracking]:
        """
        Retrieve cost history with filters
        """
        query = "SELECT * FROM cost_tracking WHERE timestamp BETWEEN :start_date AND :end_date"
        params = {"start_date": start_date, "end_date": end_date}

        if model_name:
            query += " AND model_used = :model_name"
            params["model_name"] = model_name

        if agent_name:
            query += " AND agent_name = :agent_name"
            params["agent_name"] = agent_name

        query += " ORDER BY timestamp DESC"

        results = await self.db.fetch_all(query, params)
        return [CostTracking(**result) for result in results]
```

---

## Performance Considerations

### Optimizing Cost Tracking Performance

1. **Async Cost Calculation**
```python
async def calculate_cost_async(
    cost_calculator: AgnoCostCalculator,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int
) -> CostTracking:
    """
    Asynchronous cost calculation to avoid blocking main thread
    """
    loop = asyncio.get_event_loop()

    # Run calculation in thread pool
    cost_record = await loop.run_in_executor(
        None,
        cost_calculator.calculate_cost,
        model_name,
        prompt_tokens,
        completion_tokens
    )

    return cost_record
```

2. **Batch Database Inserts**
```python
async def batch_store_costs(cost_records: list[CostTracking], batch_size: int = 100) -> None:
    """
    Store cost records in batches for better performance
    """
    for i in range(0, len(cost_records), batch_size):
        batch = cost_records[i:i + batch_size]

        # Convert to dict format
        values = [record.dict() for record in batch]

        # Bulk insert
        query = """
        INSERT INTO cost_tracking (
            model_used, provider, prompt_tokens, completion_tokens,
            total_tokens, input_cost_usd, output_cost_usd, total_cost_usd,
            latency_seconds, prompt_length_chars, timestamp,
            model_pricing_per_m_tokens, request_success, error_message
        ) VALUES (:model_used, :provider, :prompt_tokens, :completion_tokens,
                 :total_tokens, :input_cost_usd, :output_cost_usd, :total_cost_usd,
                 :latency_seconds, :prompt_length_chars, :timestamp,
                 :model_pricing_per_m_tokens, :request_success, :error_message)
        """

        await db.execute_many(query, values)
        await db.commit()
```

3. **Memory-efficient Aggregation**
```python
def aggregate_costs_streaming(
    cost_generator: AsyncIterator[CostTracking]
) -> CostSummary:
    """
    Aggregate costs with minimal memory usage
    """
    total_cost = 0.0
    total_tokens = 0
    count = 0
    model_breakdown = defaultdict(lambda: {"count": 0, "cost": 0.0, "tokens": 0})

    async for cost in cost_generator:
        total_cost += cost.total_cost_usd
        total_tokens += cost.total_tokens
        count += 1

        # Update model breakdown
        model = cost.model_used
        model_breakdown[model]["count"] += 1
        model_breakdown[model]["cost"] += cost.total_cost_usd
        model_breakdown[model]["tokens"] += cost.total_tokens

    # Convert defaultdict to regular dict
    model_breakdown = dict(model_breakdown)

    return CostSummary(
        total_cost_usd=total_cost,
        total_tokens=total_tokens,
        analysis_count=count,
        avg_cost_per_analysis=total_cost / count if count > 0 else 0,
        model_breakdown=model_breakdown,
        timestamp=datetime.utcnow()
    )
```

---

## Troubleshooting and Best Practices

### Common Issues and Solutions

#### 1. Token Count Discrepancies
```python
def validate_token_counts(cost_record: CostTracking, api_response: dict) -> bool:
    """
    Validate that tracked tokens match API response
    """
    api_usage = api_response.get("usage", {})
    api_prompt = api_usage.get("prompt_tokens", 0)
    api_completion = api_usage.get("completion_tokens", 0)

    # Allow small discrepancies due to different counting methods
    tolerance = 0.05  # 5%

    prompt_diff = abs(cost_record.prompt_tokens - api_prompt) / api_prompt
    completion_diff = abs(cost_record.completion_tokens - api_completion) / api_completion

    if prompt_diff > tolerance or completion_diff > tolerance:
        logger.warning(
            f"Token count discrepancy detected. "
            f"Tracked: {cost_record.prompt_tokens}/{cost_record.completion_tokens}, "
            f"API: {api_prompt}/{api_completion}"
        )
        return False

    return True
```

#### 2. Cost Calculation Errors
```python
def debug_cost_calculation(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    expected_cost: float
) -> None:
    """
    Debug cost calculation discrepancies
    """
    model_config = MODEL_PRICING.get(model_name)

    if not model_config:
        logger.error(f"Model {model_name} not found in pricing configuration")
        return

    calculated_cost = (
        (prompt_tokens * model_config.input_cost_per_million) +
        (completion_tokens * model_config.output_cost_per_million)
    ) / 1_000_000

    logger.info(f"""
Cost Calculation Debug:
- Model: {model_name}
- Prompt tokens: {prompt_tokens} @ ${model_config.input_cost_per_million}/1M
- Completion tokens: {completion_tokens} @ ${model_config.output_cost_per_million}/1M
- Expected cost: ${expected_cost:.6f}
- Calculated cost: ${calculated_cost:.6f}
- Difference: ${abs(calculated_cost - expected_cost):.6f}
    """)
```

### Best Practices

1. **Always Track Costs Early**
   - Implement cost tracking at the API call level
   - Track costs before any business logic to ensure completeness

2. **Use Consistent Model Naming**
   - Establish a canonical model naming convention
   - Map internal names to provider names consistently

3. **Set Reasonable Alert Thresholds**
   - Start with conservative thresholds
   - Adjust based on actual usage patterns

4. **Regular Cost Reviews**
   - Review costs weekly and monthly
   - Look for unexpected spikes or trends

5. **Document Cost Decisions**
   - Document why certain models were chosen
   - Record cost-benefit analyses

6. **Test Cost Calculations**
   - Include cost calculation tests in CI/CD
   - Validate against provider billing when possible

### Configuration Template

```yaml
# config/cost_tracking.yml
cost_tracking:
  enabled: true
  storage:
    database_url: "${DATABASE_URL}"
    retention_days: 365

  monitoring:
    daily_budget: 100.0
    hourly_budget: 4.17
    alert_thresholds:
      - 0.5  # 50% of budget
      - 0.8  # 80% of budget
      - 0.95 # 95% of budget

    notifications:
      email:
        enabled: true
        recipients: ["admin@example.com"]
      slack:
        enabled: true
        webhook_url: "${SLACK_WEBHOOK_URL}"

  optimization:
    enable_caching: true
    cache_ttl: 86400  # 24 hours
    batch_processing: true
    max_batch_size: 10

  models:
    default: "anthropic/claude-haiku-4.5"
    routing:
      enabled: true
      complexity_thresholds:
        simple: 0.3
        medium: 0.7
        complex: 1.0

  reporting:
    daily_reports: true
    weekly_reports: true
    monthly_reports: true
    report_recipients: ["finance@example.com", "engineering@example.com"]
```

---

## Conclusion

The RedditHarbor Pipeline v3 cost tracking system provides comprehensive monitoring and optimization capabilities for LLM operations. By implementing the strategies and best practices outlined in this guide, you can:

1. **Accurately track costs** at granular levels across all operations
2. **Optimize spending** through intelligent model selection and token management
3. **Monitor usage** in real-time with configurable alerts and thresholds
4. **Generate detailed reports** for financial analysis and budgeting
5. **Integrate seamlessly** with existing monitoring and observability tools

The modular design ensures that the cost tracking system can evolve with your needs while maintaining accuracy and performance. Regular reviews and optimizations will help maximize the value derived from your LLM investments while keeping costs predictable and manageable.

For specific implementation questions or advanced use cases, refer to the API documentation and integration examples provided in the accompanying guides.