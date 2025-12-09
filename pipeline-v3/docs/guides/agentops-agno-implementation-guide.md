# AgentOps-Agno Integration Implementation Guide

<div align="center">

![CueTimer Logo](https://imgur.com/placeholder-logo)
<!-- TODO: Add CueTimer logo -->

**A comprehensive guide to integrating AgentOps with Agno for multi-agent monitoring and cost tracking**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](https://github.com/redditharbor/redditharbor)
[![Status](https://img.shields.io/badge/status-production--ready-green.svg)](#)

</div>

## Table of Contents

1. [Overview and Architecture](#overview-and-architecture)
2. [Prerequisites and Dependencies](#prerequisites-and-dependencies)
3. [Step-by-Step Implementation](#step-by-step-implementation)
4. [Code Examples](#code-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Configuration](#advanced-configuration)
8. [Migration Guide](#migration-guide)

---

## Overview and Architecture

### Purpose and Benefits

The AgentOps-Agno integration provides comprehensive observability for multi-agent systems by combining:

- **AgentOps**: Advanced AI agent monitoring platform with session tracking, cost analysis, and performance metrics
- **Agno**: Multi-agent orchestration framework for complex workflows and agent coordination
- **RedditHarbor Pipeline v3**: Production environment for Reddit data analysis and market research

**Key Benefits:**
- 📊 **Real-time Cost Tracking**: Monitor token usage and costs per agent, per workflow
- 🔍 **Session Management**: Track complete workflow lifecycles with unique session IDs
- 📈 **Performance Analytics**: Identify bottlenecks and optimize agent performance
- 🛡️ **Error Recovery**: Comprehensive error tracking with fallback mechanisms
- 🔧 **Debug Mode**: Detailed logging for development and troubleshooting

### Architecture Overview

```mermaid
graph TB
    subgraph "RedditHarbor Pipeline v3"
        A[Reddit API] --> B[Data Collection]
        B --> C[Agno Workflow]
        C --> D[Agent Orchestrator]

        subgraph "Agno Agents"
            D --> E[WillingnessToPayAgent]
            D --> F[MarketSegmentAgent]
            D --> G[PricePointAgent]
            D --> H[PaymentBehaviorAgent]
            D --> I[MarketResearchAgent]
        end

        subgraph "Monitoring Layer"
            J[AgentOps Decorators]
            K[AgentOps Tracker]
            L[Cost Calculator]
            M[Session Manager]
        end

        E --> J
        F --> J
        G --> J
        H --> J
        I --> J

        J --> K
        K --> L
        K --> M

        K --> N[AgentOps Dashboard]
        L --> O[Cost Reports]
        M --> P[Session Analytics]
    end

    style RedditHarbor fill:#FF6B35,stroke:#004E89,stroke-width:4px
    style AgentOps fill:#004E89,stroke:#FF6B35,stroke-width:2px
    style Agno fill:#F7B801,stroke:#004E89,stroke-width:2px
```

### Component Interactions

1. **BaseAgent** (`transform/agno_agents.py`):
   - Enhanced with AgentOps tracking capabilities
   - Session management with unique IDs
   - Debug mode for detailed logging
   - Automatic cost tracking integration

2. **TrackedWorkflow** (`workflows/tracked_workflow.py`):
   - Workflow-level session management
   - Multi-agent coordination tracking
   - Cost aggregation across agents
   - Performance metrics collection

3. **AgentOps Decorators** (`monitoring/agentops_decorators.py`):
   - `@trace`: Function execution tracking
   - `@tool`: Tool usage monitoring
   - `@llm_call`: LLM API call tracking
   - Context managers for manual tracing

4. **Cost Tracking** (`models/cost_tracking.py`):
   - `AgnoCostModel`: Cost calculation models
   - `AgnoCostCalculator`: Per-token cost computation
   - `CostTracking`: Individual call tracking
   - `CostSummary`: Aggregate cost reporting

---

## Prerequisites and Dependencies

### System Requirements

- Python 3.11+
- PostgreSQL 13+ with pgvector extension
- Redis 6+ (for caching)
- OpenRouter API account
- AgentOps API key (optional, falls back to local tracking)

### Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/redditharbor/redditharbor.git
   cd pipeline-v3
   ```

2. **Install Dependencies**:
   ```bash
   # Using UV (recommended)
   uv sync

   # Or using pip
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create `.env.local` with the following configuration:
   ```env
   # Reddit API Configuration
   REDDIT_PUBLIC=your_reddit_client_id
   REDDIT_SECRET=your_reddit_client_secret

   # OpenRouter API Configuration
   OPENROUTER_API_KEY=your_openrouter_api_key
   OPENROUTER_MODEL=openai/gpt-4o-mini

   # Agno Configuration
   AGNO_MODEL=anthropic/claude-haiku-4.5
   AGNO_BASE_URL=https://openrouter.ai/api/v1
   AGNO_ENABLE_AGENTOPS=true
   AGNO_DEBUG_MODE=false

   # AgentOps Configuration
   AGENTOPS_API_KEY=your_agentops_api_key
   AGENTOPS_ENABLED=true
   AGENTOPS_TAGS=production,pipeline-v3,agno

   # Database Configuration
   DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54331/postgres

   # Logging
   LOG_LEVEL=INFO
   ```

### Installing AgentOps

```bash
# Install AgentOps SDK
pip install agentops

# Or add to requirements.txt
echo "agentops>=0.1.0" >> requirements.txt
```

### Cost Configuration

Configure model pricing in `config/settings.py`:

```python
# Example cost configuration (USD per million tokens)
AGNO_CLAUDE_COST_PER_MILLION_INPUT_TOKENS=3.0
AGNO_CLAUDE_COST_PER_MILLION_OUTPUT_TOKENS=15.0
AGNO_GPT4O_COST_PER_MILLION_INPUT_TOKENS=5.0
AGNO_GPT4O_COST_PER_MILLION_OUTPUT_TOKENS=15.0
AGNO_HAIKU_COST_PER_MILLION_INPUT_TOKENS=1.0
AGNO_HAIKU_COST_PER_MILLION_OUTPUT_TOKENS=5.0
```

---

## Step-by-Step Implementation

### 1. Base Agent Enhancement

The `BaseAgent` class in `transform/agno_agents.py` is enhanced with AgentOps tracking:

```python
class BaseAgent(Agent):
    """Base agent class with AgentOps integration"""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        output_schema: type[BaseModel] | None = None,
        debug_mode: bool = False,
        enable_agentops: bool = False,
        instructions: list[str] | None = None,
        name: str | None = None
    ):
        # Store AgentOps configuration
        self.enable_agentops = enable_agentops
        self.agentops_tracker = None

        # Initialize AgentOps if enabled
        if self.enable_agentops:
            self.agentops_tracker = get_tracker()
            self.agentops_tracker.start_session(
                f"{self._get_agent_name()}_session",
                tags=["agent", "agno", self._get_agent_name()]
            )
```

**Key Features:**
- Automatic session initialization
- Agent-specific tagging
- Debug mode toggle
- Graceful fallback if AgentOps unavailable

### 2. Cost Tracking Integration

Implement the cost calculation model:

```python
from models.cost_tracking import ModelCostConfig, CostTracking

class AgnoCostCalculator:
    """Calculate costs for Agno agent operations"""

    def __init__(self, model_configs: dict[str, ModelCostConfig]):
        self.model_configs = model_configs

    def calculate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate total cost for an LLM call"""
        config = self.model_configs.get(model_name)
        if not config:
            return 0.0

        input_cost = (input_tokens * config.input_cost_per_million) / 1_000_000
        output_cost = (output_tokens * config.output_cost_per_million) / 1_000_000

        return input_cost + output_cost
```

**Cost Formula:**
```python
# For each model
total_cost = (tokens * cost_per_million) / 1_000_000

# Example: 1000 input tokens with Claude Haiku
input_cost = (1000 * 1.0) / 1_000_000 = $0.001
output_cost = (500 * 5.0) / 1_000_000 = $0.0025
total_cost = $0.0035
```

### 3. Workflow Integration

Create tracked workflows with `TrackedWorkflow`:

```python
from workflows.tracked_workflow import TrackedWorkflow

class MarketAnalysisWorkflow(TrackedWorkflow):
    """Market analysis workflow with AgentOps tracking"""

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(
            name="market_analysis_workflow",
            config=config,
            enable_agentops=config.get('enable_agentops', True),
            cost_tracker=get_tracker() if config.get('enable_agentops') else None
        )

        # Initialize agents
        self.wtp_agent = WillingnessToPayAgent(
            model=config['agno_model'],
            api_key=config['api_key'],
            base_url=config['base_url'],
            enable_agentops=True
        )

        self.market_agent = MarketSegmentAgent(
            model=config['agno_model'],
            api_key=config['api_key'],
            base_url=config['base_url'],
            enable_agentops=True
        )

    async def analyze_submission(self, submission: dict) -> dict:
        """Analyze a Reddit submission with all agents"""
        results = {}

        # Track workflow step
        self.track_workflow_step(
            agent_name="workflow",
            step_name="submission_analysis",
            step_status="started",
            step_duration=0,
            metadata={"submission_id": submission.get('id')}
        )

        start_time = time.time()

        try:
            # Run agents sequentially or in parallel
            if self.config.get('orchestration_mode') == 'parallel':
                results = await self._run_agents_parallel(submission)
            else:
                results = await self._run_agents_sequential(submission)

            # Track successful completion
            duration = time.time() - start_time
            self.track_workflow_step(
                agent_name="workflow",
                step_name="submission_analysis",
                step_status="completed",
                step_duration=duration,
                metadata={"agent_count": len(results)}
            )

            return results

        except Exception as e:
            # Track error
            duration = time.time() - start_time
            self.track_workflow_step(
                agent_name="workflow",
                step_name="submission_analysis",
                step_status="failed",
                step_duration=duration,
                metadata={"error": str(e)}
            )
            raise
```

### 4. Decorator Implementation

Use decorators for automatic tracking:

```python
from monitoring.agentops_decorators import trace, tool, llm_call

@trace(
    name="analyze_market_willingness",
    tags=["market-analysis", "willingness-to-pay"],
    track_args=True,
    track_result=True
)
async def analyze_willingness_to_pay(submission_text: str) -> WillingnessToPayResult:
    """Analyze willingness to pay with automatic tracking"""
    # Function implementation
    pass

@tool(
    name="price_calculator",
    category="pricing",
    track_usage=True,
    track_cost=True
)
def calculate_optimal_price(
    willingness_score: float,
    market_size: float,
    budget_range: str
) -> float:
    """Calculate optimal price point"""
    # Implementation
    pass

@llm_call(
    model_name="anthropic/claude-haiku-4.5",
    track_cost=True,
    track_tokens=True
)
async def call_llm_for_analysis(prompt: str) -> str:
    """LLM call with automatic cost tracking"""
    # Implementation
    pass
```

### 5. Testing Strategy

Following TDD methodology:

```python
import pytest
from unittest.mock import Mock, patch

class TestAgentOpsIntegration:
    """Test suite for AgentOps-Agno integration"""

    @pytest.fixture
    def mock_agentops_tracker(self):
        """Mock AgentOps tracker for testing"""
        with patch('monitoring.agentops_tracker.get_tracker') as mock:
            tracker = Mock()
            tracker.start_session.return_value = "test_session_123"
            tracker.track_llm_call.return_value = True
            tracker.end_session.return_value = {"status": "success"}
            mock.return_value = tracker
            yield tracker

    @pytest.fixture
    def test_agent(self, mock_agentops_tracker):
        """Create test agent with mocked AgentOps"""
        return WillingnessToPayAgent(
            model="test-model",
            api_key="test-key",
            base_url="https://test.com",
            enable_agentops=True,
            debug_mode=True
        )

    async def test_agent_session_tracking(self, test_agent, mock_agentops_tracker):
        """Test that agent sessions are tracked correctly"""
        # Verify session was started
        mock_agentops_tracker.start_session.assert_called_once()

        # Run agent analysis
        result = await test_agent.a_run("Test submission text")

        # Verify tracking calls
        assert mock_agentops_tracker.track_llm_call.called
        assert isinstance(result, WillingnessToPayResult)

    def test_cost_calculation(self):
        """Test cost calculation accuracy"""
        calculator = AgnoCostCalculator({
            "claude-haiku": ModelCostConfig(
                model_name="claude-haiku",
                provider="anthropic",
                input_cost_per_million=1.0,
                output_cost_per_million=5.0
            )
        })

        # Test with 1000 input, 500 output tokens
        cost = calculator.calculate_cost("claude-haiku", 1000, 500)
        expected = (1000 * 1.0 / 1_000_000) + (500 * 5.0 / 1_000_000)
        assert abs(cost - expected) < 0.000001

    async def test_workflow_cost_tracking(self):
        """Test workflow-level cost aggregation"""
        workflow = MarketAnalysisWorkflow({
            "enable_agentops": True,
            "agno_model": "test-model",
            "api_key": "test-key",
            "base_url": "https://test.com"
        })

        # Run workflow
        results = await workflow.analyze_submission({
            "id": "test123",
            "title": "Test",
            "text": "Test submission"
        })

        # Verify costs were tracked
        assert workflow.session_metrics.total_cost > 0
        assert workflow.session_metrics.total_tokens > 0
```

---

## Code Examples

### Basic Agent Setup

```python
from transform.agno_agents import WillingnessToPayAgent
from config.settings import get_settings

settings = get_settings()

# Create agent with AgentOps tracking
agent = WillingnessToPayAgent(
    model=settings.agno_model,
    api_key=settings.openai_api_key,
    base_url=settings.agno_base_url,
    debug_mode=settings.agno_debug_mode,
    enable_agentops=settings.agno_enable_agentops
)

# Run analysis
result = await agent.a_run("""
"I'm looking for a project management tool that can handle my team of 15 people.
We currently use Trello but it's not scaling well. Our budget is around $200/month.
We're willing to pay for something that saves us time."
""")

print(f"WTP Score: {result.wtp_score}")
print(f"Price Range: {result.price_range}")
print(f"Budget Mentioned: {result.budget_mentioned}")
```

### Advanced Workflow Orchestration

```python
from workflows.tracked_workflow import TrackedWorkflow
from monitoring.agentops_tracker import get_tracker
import asyncio

class ComprehensiveMarketAnalysis(TrackedWorkflow):
    """Complete market analysis with multiple agents"""

    def __init__(self, config: dict):
        super().__init__(
            name="comprehensive_market_analysis",
            config=config,
            enable_agentops=True
        )

        # Initialize all agents
        self.agents = {
            'wtp': WillingnessToPayAgent(...),
            'segment': MarketSegmentAgent(...),
            'pricing': PricePointAgent(...),
            'behavior': PaymentBehaviorAgent(...),
            'research': MarketResearchAgent(...)
        }

    async def analyze_opportunity(self, submission: dict) -> dict:
        """Run comprehensive analysis"""
        session_id = self.start_session(
            session_name=f"analysis_{submission['id']}",
            tags=["market-analysis", "comprehensive"]
        )

        try:
            # Step 1: Parallel agent analysis
            async with asyncio.TaskGroup() as tg:
                tasks = {
                    name: tg.create_task(
                        agent.a_run(submission['text']),
                        name=name
                    )
                    for name, agent in self.agents.items()
                }

            # Collect results
            results = {}
            for name, task in tasks.items():
                results[name] = task.result()

                # Track agent coordination
                self.track_agent_coordination(
                    primary_agent="workflow",
                    coordinating_agent=name,
                    operation="analyze",
                    metadata={
                        "submission_id": submission['id'],
                        "success": True
                    }
                )

            # Step 2: Synthesize results
            synthesis = await self.synthesize_results(results)

            # Track total cost
            total_cost = sum(
                r.get('cost', 0) for r in results.values()
            )
            self.track_cost(total_cost, "agent_analysis")

            return {
                "submission_id": submission['id'],
                "agent_results": results,
                "synthesis": synthesis,
                "total_cost": total_cost,
                "session_id": session_id
            }

        finally:
            self.end_session(
                status="success",
                metadata={
                    "submission_id": submission['id'],
                    "agents_run": len(self.agents)
                }
            )
```

### Custom Decorator Implementation

```python
from monitoring.agentops_decorators import trace_context
import time

def custom_agent_tracing(agent_name: str):
    """Custom decorator for agent-specific tracing"""
    def decorator(func):
        @trace(
            name=f"agent.{agent_name}.{func.__name__}",
            tags=["agent", agent_name],
            track_args=True,
            track_result=True
        )
        async def wrapper(*args, **kwargs):
            # Custom pre-processing
            start_time = time.time()

            # Extract submission ID for tracking
            submission_id = None
            if args and hasattr(args[0], 'get'):
                submission_id = args[0].get('id')

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Custom post-processing
                duration = time.time() - start_time

                # Track agent-specific metrics
                get_tracker().track_latency(
                    f"{agent_name}.{func.__name__}",
                    duration,
                    metadata={
                        "agent": agent_name,
                        "submission_id": submission_id,
                        "success": True
                    }
                )

                return result

            except Exception as e:
                # Track error
                duration = time.time() - start_time
                get_tracker().track_error(
                    f"{agent_name}.{func.__name__}",
                    str(e),
                    metadata={
                        "agent": agent_name,
                        "submission_id": submission_id,
                        "duration": duration
                    }
                )
                raise

        return wrapper
    return decorator

# Usage
@custom_agent_tracing("willingness_analyzer")
async def analyze_willingness(submission: dict) -> dict:
    """Custom traced willingness analysis"""
    # Implementation
    pass
```

### Production-Ready Configuration

```python
# config/production.py
from config.settings import Settings

class ProductionSettings(Settings):
    """Production configuration with AgentOps enabled"""

    # Enable AgentOps in production
    agentops_enabled: bool = True
    agentops_api_key: str = Field(..., env="AGENTOPS_API_KEY")
    agno_enable_agentops: bool = True

    # Production logging
    log_level: str = "INFO"

    # Performance optimizations
    batch_size: int = 20
    agno_timeout: int = 60

    # Cost tracking
    agno_track_costs: bool = True

    # Model cost settings (production rates)
    agno_claude_cost_per_million_input_tokens: float = 3.0
    agno_claude_cost_per_million_output_tokens: float = 15.0

    # Workflow settings
    agno_orchestration_mode: str = "sequential"  # More predictable costs
    agno_consensus_threshold: float = 70.0  # Higher threshold for production

# Usage
def create_production_workflow() -> TrackedWorkflow:
    """Create workflow with production settings"""
    config = ProductionSettings()

    return MarketAnalysisWorkflow({
        "enable_agentops": config.agno_enable_agentops,
        "track_costs": config.agno_track_costs,
        "orchestration_mode": config.agno_orchestration_mode,
        "consensus_threshold": config.agno_consensus_threshold,
        "agno_model": config.agno_model,
        "api_key": config.openai_api_key,
        "base_url": config.agno_base_url,
        "timeout": config.agno_timeout,
        "batch_size": config.batch_size
    })
```

---

## Best Practices

### Performance Optimization

1. **Batch Processing**:
   ```python
   # Process submissions in batches to reduce overhead
   async def process_batch(submissions: list[dict]) -> list[dict]:
       batch_results = []

       # Start single session for batch
       session_id = tracker.start_session("batch_processing")

       try:
           for batch in chunked(submissions, batch_size=10):
               # Process batch concurrently
               tasks = [
                   analyze_submission(s) for s in batch
               ]
               batch_results.extend(await asyncio.gather(*tasks))

       finally:
           tracker.end_session("success", {"processed": len(batch_results)})

       return batch_results
   ```

2. **Event Batching**:
   ```python
   # AgentOps tracker automatically batches events
   # Configure batch size in AgentOpsConfig
   config = AgentOpsConfig(
       batch_size=50,  # Process 50 events at once
       batch_timeout=2.0  # Or flush every 2 seconds
   )
   ```

3. **Async Operations**:
   ```python
   # Use async for all agent operations
   async def parallel_agent_analysis(submission: dict) -> dict:
       async with asyncio.TaskGroup() as tg:
           tasks = {
               'wtp': tg.create_task(wtp_agent.a_run(submission)),
               'segment': tg.create_task(segment_agent.a_run(submission)),
               'pricing': tg.create_task(pricing_agent.a_run(submission))
           }

       return {name: task.result() for name, task in tasks.items()}
   ```

### Error Handling Patterns

1. **Graceful Degradation**:
   ```python
   class RobustAgentOpsTracker:
       """AgentOps tracker with fallback"""

       def __init__(self):
           self.primary_tracker = get_tracker()
           self.local_fallback = LocalTracker()
           self.using_fallback = False

       def track_llm_call(self, *args, **kwargs):
           try:
               if not self.using_fallback:
                   self.primary_tracker.track_llm_call(*args, **kwargs)
               else:
                   self.local_fallback.track_llm_call(*args, **kwargs)
           except Exception as e:
               logger.warning(f"AgentOps tracking failed: {e}")
               self.using_fallback = True
               self.local_fallback.track_llm_call(*args, **kwargs)
   ```

2. **Retry Mechanism**:
   ```python
   @retry(
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=4, max=10),
       retry=retry_if_exception_type(ConnectionError)
   )
   async def track_with_retry(tracker_func: Callable, *args, **kwargs):
       """Retry tracking operations"""
       return await tracker_func(*args, **kwargs)
   ```

3. **Circuit Breaker Pattern**:
   ```python
   class CircuitBreakerTracker:
       """Circuit breaker for AgentOps tracking"""

       def __init__(self, failure_threshold: int = 5, timeout: int = 60):
           self.failure_threshold = failure_threshold
           self.timeout = timeout
           self.failure_count = 0
           self.last_failure = None
           self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

       def track(self, func: Callable, *args, **kwargs):
           if self.state == "OPEN":
               if time.time() - self.last_failure > self.timeout:
                   self.state = "HALF_OPEN"
               else:
                   return None  # Skip tracking

           try:
               result = func(*args, **kwargs)
               if self.state == "HALF_OPEN":
                   self.state = "CLOSED"
                   self.failure_count = 0
               return result
           except Exception:
               self.failure_count += 1
               self.last_failure = time.time()
               if self.failure_count >= self.failure_threshold:
                   self.state = "OPEN"
               return None
   ```

### Monitoring Strategies

1. **Key Metrics to Track**:
   - Cost per analysis
   - Token efficiency
   - Agent success rate
   - Workflow completion time
   - Error frequency by type

2. **Dashboard Configuration**:
   ```python
   # Custom metrics for AgentOps dashboard
   def setup_custom_metrics():
       tracker = get_tracker()

       # Custom events for business metrics
       tracker.track_custom_event(
           "market_opportunity_score",
           {
               "score": 85,
               "market_size": "$10M",
               "competition": "low",
               "timestamp": datetime.utcnow().isoformat()
           }
       )

       # Agent performance comparison
       tracker.track_agent_performance({
           "claude_haiku": {
               "avg_cost_per_analysis": 0.05,
               "avg_tokens_per_analysis": 1500,
               "success_rate": 98.5
           },
           "gpt_4o": {
               "avg_cost_per_analysis": 0.12,
               "avg_tokens_per_analysis": 2000,
               "success_rate": 99.2
           }
       })
   ```

3. **Alert Configuration**:
   ```python
   # Alert on cost thresholds
   COST_ALERT_THRESHOLD = 100.0  # $100 per hour
   ERROR_ALERT_THRESHOLD = 10  # 10 errors per minute

   def check_and_alert():
       summary = tracker.get_session_summary()

       if summary["total_cost_usd"] > COST_ALERT_THRESHOLD:
           send_alert(f"High cost alert: ${summary['total_cost_usd']:.2f}")

       if len(summary["recent_errors"]) > ERROR_ALERT_THRESHOLD:
           send_alert(f"High error rate: {len(summary['recent_errors'])} errors")
   ```

### Security Considerations

1. **API Key Management**:
   ```python
   # Never hardcode API keys
   from config.settings import get_settings

   settings = get_settings()
   agentops_key = settings.agentops_api_key

   # Use environment variables in production
   # Rotate keys regularly
   # Implement key-scoped permissions
   ```

2. **Data Privacy**:
   ```python
   # Anonymize sensitive data before tracking
   def anonymize_submission_data(submission: dict) -> dict:
       """Remove PII before tracking"""
       anonymized = submission.copy()

       # Remove user identifiers
       anonymized.pop("author", None)
       anonymized.pop("author_id", None)

       # Hash content for deduplication
       anonymized["content_hash"] = hash_content(
           anonymized.get("text", "")
       )

       return anonymized
   ```

3. **Rate Limiting**:
   ```python
   from ratelimit import limits, sleep_and_retry

   @sleep_and_retry
   @limits(calls=100, period=60)  # 100 calls per minute
   async def track_with_limit(tracker_func: Callable, *args, **kwargs):
       """Rate-limited tracking"""
       return await tracker_func(*args, **kwargs)
   ```

---

## Troubleshooting

### Common Issues

1. **AgentOps Initialization Fails**:
   ```python
   # Check if AgentOps is available
   try:
       import agentops
       print(f"AgentOps version: {agentops.__version__}")
   except ImportError:
       print("AgentOps not installed. Install with: pip install agentops")

   # Check API key configuration
   from config.settings import get_settings
   settings = get_settings()

   if not settings.agentops_api_key:
       print("AGENTOPS_API_KEY not configured")
       print("Set environment variable or add to .env.local")
   ```

2. **Sessions Not Tracking**:
   ```python
   # Verify session is started correctly
   tracker = get_tracker()

   if not tracker.agentops_available:
       print("AgentOps not available, using local tracking")

   # Check session state
   if not tracker.current_local_session:
       print("No active session. Call start_session() first")

   # Test tracking
   success = tracker.track_llm_call(
       model="test-model",
       tokens=100,
       cost=0.001,
       latency=0.5
   )
   print(f"Tracking successful: {success}")
   ```

3. **Cost Calculation Errors**:
   ```python
   # Verify model configuration
   from models.cost_tracking import ModelCostConfig

   # Check if model has cost config
   calculator = AgnoCostCalculator({
       "claude-haiku": ModelCostConfig(
           model_name="claude-haiku",
           provider="anthropic",
           input_cost_per_million=1.0,
           output_cost_per_million=5.0
       )
   })

   # Test calculation
   cost = calculator.calculate_cost("claude-haiku", 1000, 500)
   print(f"Calculated cost: ${cost:.6f}")
   ```

### Debug Mode

Enable debug mode for detailed logging:

```python
# In agent initialization
agent = WillingnessToPayAgent(
    model=settings.agno_model,
    api_key=settings.openai_api_key,
    base_url=settings.agno_base_url,
    debug_mode=True  # Enable debug logging
)

# Or in environment
# AGNO_DEBUG_MODE=true
```

Debug output includes:
- Session IDs and lifecycle events
- Cost calculations
- Agent coordination details
- Error stack traces

### Performance Issues

1. **High Latency**:
   - Check batch size configuration
   - Verify AgentOps event batching
   - Monitor network connectivity

2. **Memory Usage**:
   - Session data accumulates in memory
   - Implement session cleanup:
   ```python
   # Clean up old sessions
   def cleanup_old_sessions(tracker: AgentOpsTracker, max_age_hours: int = 24):
       cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

       for session_id, metrics in list(tracker.local_sessions.items()):
           if metrics.start_time < cutoff:
               del tracker.local_sessions[session_id]
               logger.info(f"Cleaned up session: {session_id}")
   ```

3. **Cost Spikes**:
   - Monitor token usage per agent
   - Set cost limits:
   ```python
   class CostLimitedTracker:
       def __init__(self, daily_limit: float = 10.0):
           self.daily_limit = daily_limit
           self.daily_cost = 0.0
           self.last_reset = datetime.utcnow().date()

       def track_llm_call(self, model: str, cost: float, **kwargs):
           # Reset daily counter
           if datetime.utcnow().date() > self.last_reset:
               self.daily_cost = 0.0
               self.last_reset = datetime.utcnow().date()

           # Check limit
           if self.daily_cost + cost > self.daily_limit:
               logger.warning(f"Daily cost limit exceeded: ${self.daily_cost:.2f}")
               raise CostLimitExceeded(f"${self.daily_limit:.2f}")

           # Track the call
           self.daily_cost += cost
           return super().track_llm_call(model, cost, **kwargs)
   ```

---

## Advanced Configuration

### Custom Cost Models

```python
class DynamicCostModel:
    """Dynamic pricing based on market conditions"""

    def __init__(self, base_costs: dict[str, float]):
        self.base_costs = base_costs
        self.multipliers = {
            "peak_hours": 1.2,
            "off_hours": 0.8,
            "weekend": 0.9
        }

    def get_cost_multiplier(self) -> float:
        """Calculate current cost multiplier"""
        now = datetime.utcnow()

        # Peak hours: 9 AM - 5 PM UTC
        if 9 <= now.hour <= 17:
            return self.multipliers["peak_hours"]

        # Weekend discount
        if now.weekday() >= 5:
            return self.multipliers["weekend"]

        return self.multipliers["off_hours"]

    def calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost with dynamic multiplier"""
        base_cost = (tokens * self.base_costs.get(model, 0)) / 1_000_000
        return base_cost * self.get_cost_multiplier()
```

### Multi-Region Deployment

```python
class RegionalAgentOpsTracker:
    """AgentOps tracker for multi-region deployment"""

    def __init__(self, region: str, config: AgentOpsConfig):
        self.region = region
        self.config = config
        self.primary_tracker = self._get_region_tracker()
        self.backup_tracker = self._get_backup_tracker()

    def _get_region_tracker(self):
        """Get tracker for current region"""
        if self.region == "us-east-1":
            return AgentOpsTracker(self.config)
        elif self.region == "eu-west-1":
            return AgentOpsTracker(
                self.config.with_endpoint("https://api.agentops.eu")
            )
        else:
            return AgentOpsTracker(self.config)

    def track_with_fallback(self, *args, **kwargs):
        """Track with region failover"""
        try:
            return self.primary_tracker.track_llm_call(*args, **kwargs)
        except Exception:
            # Fallback to backup region
            return self.backup_tracker.track_llm_call(*args, **kwargs)
```

### Custom Event Types

```python
# Define custom event schemas
class MarketOpportunityEvent(BaseModel):
    event_type: str = "market_opportunity"
    opportunity_score: float
    market_size_usd: float
    competition_level: str
    timestamp: datetime

    def to_dict(self) -> dict:
        return self.model_dump()

# Track custom events
def track_market_opportunity(opportunity_data: dict):
    tracker = get_tracker()

    event = MarketOpportunityEvent(
        opportunity_score=opportunity_data["score"],
        market_size_usd=opportunity_data["size"],
        competition_level=opportunity_data["competition"],
        timestamp=datetime.utcnow()
    )

    tracker.track_custom_event(
        "market_opportunity",
        event.to_dict()
    )
```

### Integration with External Monitoring

```python
class PrometheusMetricsExporter:
    """Export AgentOps metrics to Prometheus"""

    def __init__(self, tracker: AgentOpsTracker):
        self.tracker = tracker
        self.metrics = {
            "agentops_total_cost": Gauge(
                "agentops_total_cost_usd",
                "Total cost tracked by AgentOps"
            ),
            "agentops_total_tokens": Counter(
                "agentops_total_tokens",
                "Total tokens tracked by AgentOps",
                ["model"]
            ),
            "agentops_session_count": Counter(
                "agentops_sessions_total",
                "Total AgentOps sessions"
            )
        }

    def update_metrics(self):
        """Update Prometheus metrics from AgentOps data"""
        summary = self.tracker.get_session_summary()

        if summary:
            self.metrics["agentops_total_cost"].set(
                summary["total_cost_usd"]
            )

            # Update token counts by model
            for model, data in summary.get("model_breakdown", {}).items():
                self.metrics["agentops_total_tokens"].labels(
                    model=model
                ).inc(data.get("tokens", 0))
```

---

## Migration Guide

### From Basic Agno to AgentOps-Enabled

1. **Update Agent Initialization**:
   ```python
   # Before
   agent = WillingnessToPayAgent(
       model="claude-haiku",
       api_key=key,
       base_url=url
   )

   # After
   agent = WillingnessToPayAgent(
       model="claude-haiku",
       api_key=key,
       base_url=url,
       enable_agentops=True,  # Add this
       debug_mode=False       # Optional
   )
   ```

2. **Add Cost Tracking**:
   ```python
   # Before
   result = await agent.a_run(prompt)

   # After
   with trace_context("analysis", tags=["wtp", "market"]):
       result = await agent.a_run(prompt)

       # Costs automatically tracked
   ```

3. **Update Workflow**:
   ```python
   # Before
   class MarketAnalysis:
       async def analyze(self, data):
           return await self.agent.a_run(data)

   # After
   class MarketAnalysis(TrackedWorkflow):
       async def analyze(self, data):
           return await super().run()  # Automatically tracked
   ```

### Data Migration

```python
# Migrate existing cost data
def migrate_cost_data():
    """Migrate from old cost tracking to AgentOps"""

    # Read old cost records
    old_costs = read_old_cost_records()

    # Create batch events for AgentOps
    tracker = get_tracker()
    session_id = tracker.start_session("migration")

    try:
        for cost_record in old_costs:
            tracker.track_llm_call(
                model=cost_record["model"],
                tokens=cost_record["tokens"],
                cost=cost_record["cost"],
                latency=cost_record["latency"],
                metadata={
                    "migrated": True,
                    "original_timestamp": cost_record["timestamp"]
                }
            )
    finally:
        tracker.end_session("migration_complete")
```

### Rollback Strategy

```python
class AgentOpsRollbackManager:
    """Handle graceful rollback from AgentOps"""

    def __init__(self):
        self.tracker = get_tracker()
        self.local_backup = LocalTracker()
        self.rollback_mode = False

    def track_with_rollback(self, *args, **kwargs):
        """Track with automatic rollback capability"""
        if self.rollback_mode:
            return self.local_backup.track(*args, **kwargs)

        try:
            result = self.tracker.track(*args, **kwargs)
            # Also track locally for backup
            self.local_backup.track(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"AgentOps tracking failed: {e}")
            self.rollback_mode = True
            return self.local_backup.track(*args, **kwargs)
```

---

## Conclusion

The AgentOps-Agno integration provides a comprehensive solution for monitoring and optimizing multi-agent systems in production. By following this implementation guide, you can:

1. **Gain Full Observability**: Track every agent interaction, cost, and performance metric
2. **Optimize Costs**: Understand and control your LLM spending at granular levels
3. **Improve Reliability**: Implement robust error handling and recovery mechanisms
4. **Scale Confidently**: Deploy with production-ready configurations and monitoring

### Next Steps

1. **Setup Your Environment**: Follow the prerequisites section to configure your development environment
2. **Implement Basic Tracking**: Start with simple agent tracking using decorators
3. **Enable Workflows**: Migrate to `TrackedWorkflow` for comprehensive monitoring
4. **Configure Dashboards**: Set up custom metrics and alerts in AgentOps
5. **Optimize and Scale**: Use performance data to optimize your agent configurations

### Support

- **Documentation**: [RedditHarbor Docs](https://docs.redditharbor.com)
- **Issues**: [GitHub Issues](https://github.com/redditharbor/redditharbor/issues)
- **Community**: [Discord Community](https://discord.gg/redditharbor)
- **AgentOps Support**: [AgentOps Docs](https://docs.agentops.ai)

---

<div align="center">

**Built with ❤️ by the RedditHarbor Team**

[<span style="color: #FF6B35;">#FF6B35</span>](#) • [<span style="color: #004E89;">#004E89</span>](#) • [<span style="color: #F7B801;">#F7B801</span>](#)

</div>