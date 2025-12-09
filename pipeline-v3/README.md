# Pipeline v3 - Clean Reddit Data Processing Pipeline

A minimal, type-safe Reddit data extraction and analysis pipeline following ELT pattern: **Extract → Transform → Load**.

## Features

- 🔍 **Reddit Data Extraction**: PRAW-based Reddit API client with robust error handling
- 🤖 **LLM Analysis**: OpenAI integration with Pydantic + Instructor for structured output validation
- 💾 **Unified Storage**: SQLAlchemy with pgvector embeddings in a single PostgreSQL database
- 🔒 **Type Safety**: Full Pydantic model validation throughout the pipeline
- ⚡ **Performance**: Batch processing and transaction safety
- 🧪 **Testing**: Comprehensive test coverage with pytest
- 📊 **AgentOps Integration**: Production monitoring and observability with comprehensive cost tracking
- 🔄 **Multi-Agent System**: Agno framework integration with enhanced session management
- 💰 **Cost Tracking**: Real-time LLM cost monitoring and analytics with category-based tracking
- 🎯 **Debug Mode**: Enhanced debugging capabilities for Agno agents with structured logging

## Architecture

```
pipeline-v3/
├── models/           # Pydantic data models
├── extract/          # Reddit data extraction (PRAW)
├── transform/        # LLM analysis (Instructor + Pydantic)
├── load/            # Database loading (SQLAlchemy + pgvector)
├── config/          # Pydantic settings management
├── monitoring/      # AgentOps integration and cost tracking
│   ├── agentops_tracker.py    # AgentOps session management
│   ├── agentops_decorators.py # Tracking decorators
│   └── cost_tracker.py        # Cost calculation models
├── workflows/       # Tracked workflow classes
├── docs/           # Documentation and guides
└── tests/           # Test suite
```

## AgentOps Quick Start

### Enable AgentOps Monitoring

```bash
# Add to .env.local
export AGENTOPS_API_KEY=your_agentops_key
export AGENTOPS_ENABLED=true
export AGNO_DEBUG_MODE=true
```

### Basic AgentOps Integration

```python
from transform.agno_agents import BaseAgent
from monitoring.cost_tracker import CostTracker

# Create agent with AgentOps tracking
agent = BaseAgent(
    name="research_agent",
    model="anthropic/claude-haiku-4.5",
    api_key="your_api_key",
    base_url="https://openrouter.ai/api/v1",
    enable_agentops=True
)

# Track costs
agent.cost_tracker.track_cost(0.05, "llm_call")
```

### View Monitoring Dashboard

Visit: https://app.agentops.ai to see real-time metrics

## Quick Start

### 1. Install Dependencies

```bash
cd pipeline-v3
uv sync
```

### 2. Configure Environment

Create `.env.local` file:

```bash
# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# AgentOps Configuration
AGENTOPS_API_KEY=your_agentops_api_key
AGENTOPS_ENABLED=true
AGENTOPS_TAGS=production,pipeline-v3

# Agno Configuration
AGNO_MODEL=anthropic/claude-haiku-4.5
AGNO_BASE_URL=https://openrouter.ai/api/v1
AGNO_ENABLE_AGENTOPS=true
AGNO_DEBUG_MODE=false

# Database (optional - defaults to local Supabase)
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

### 3. Run the Pipeline

```bash
# Basic usage
python -m pipeline_v3 --limit 10 --subreddits productivity

# Advanced usage with AgentOps tracking
python -m pipeline_v3 \
  --limit 25 \
  --subreddits productivity tools freelance \
  --sort-by top \
  --time-filter month \
  --min-score 70.0 \
  --min-confidence 60.0 \
  --validate-quality \
  --enable-agentops

# Test mode (mock data)
python -m pipeline_v3 --test-mode --limit 5

# Dry run (process but don't store)
python -m pipeline_v3 --dry-run --limit 10
```

## Configuration

All configuration is managed through Pydantic settings with environment variable support:

```python
# config/settings.py
class Settings(BaseSettings):
    # Reddit API
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str = "RedditHarbor Pipeline v3/1.0"

    # Database
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    # LLM
    openai_api_key: str
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.3

    # AgentOps Configuration
    agentops_enabled: bool = False
    agentops_api_key: str | None = None
    agentops_tags: list[str] = ["pipeline-v3"]

    # Agno Configuration
    agno_model: str = "anthropic/claude-haiku-4.5"
    agno_base_url: str = "https://openrouter.ai/api/v1"
    agno_enable_agentops: bool = True
    agno_debug_mode: bool = False
    agno_track_costs: bool = True

    # Pipeline
    default_subreddits: List[str] = ["productivity", "tools"]
    default_limit: int = 10
    batch_size: int = 5

    # pgvector
    embedding_dimension: int = 384
    similarity_threshold: float = 0.8
```

## Data Models

### Reddit Data
```python
class RedditSubmission(BaseModel):
    id: str
    title: str
    text: str
    author: str
    upvotes: int
    score: int
    comments_count: int
    subreddit: str
    created_utc: datetime
    permalink: str
```

### Analysis Results
```python
class AppIdea(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    app_concept: str
    problem_statement: str
    target_audience: str
    core_functions: List[str] = Field(..., min_items=1, max_items=3)  # MAX 3!
```

### Database Storage
```python
class Opportunity(Base):
    id: UUID
    app_title: str
    final_score: float
    trust_level: str
    embedding: Vector(384)  # pgvector in same table
    created_at: datetime
```

## AgentOps Integration

### Session Management

The pipeline integrates AgentOps for comprehensive session tracking:

```python
from monitoring.agentops_tracker import get_tracker
from transform.agno_agents import WillingnessToPayAgent

# Start a tracked session
tracker = get_tracker()
session_id = tracker.start_session(
    session_name="market_analysis",
    tags=["research", "willingness-to-pay"]
)

# Create agent with automatic tracking
agent = WillingnessToPayAgent(
    model="anthropic/claude-haiku-4.5",
    api_key=api_key,
    base_url=base_url,
    enable_agentops=True
)

# All agent calls are automatically tracked
result = await agent.a_run(submission_text)

# End session with summary
tracker.end_session(status="success")
```

### Cost Tracking

Real-time cost calculation and tracking:

```python
from monitoring.cost_tracker import CostTracker
from models.cost_tracking import AgnoCostCalculator

# Initialize cost calculator
calculator = AgnoCostCalculator({
    "claude-haiku": ModelCostConfig(
        model_name="claude-haiku",
        provider="anthropic",
        input_cost_per_million=1.0,
        output_cost_per_million=5.0
    )
})

# Track costs automatically
tracker = CostTracker(calculator)

# Manual cost tracking
tracker.track_cost(
    cost=0.0035,
    category="llm_call",
    model="claude-haiku",
    tokens=1500,
    metadata={"agent": "wtp_analyzer"}
)
```

### Decorators for Easy Tracking

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

## Multi-Agent System with Agno

### Agent Orchestration

```python
from workflows.tracked_workflow import TrackedWorkflow
from transform.agno_agents import (
    WillingnessToPayAgent,
    MarketSegmentAgent,
    PricePointAgent,
    PaymentBehaviorAgent
)

class MarketAnalysisWorkflow(TrackedWorkflow):
    """Multi-agent market analysis workflow"""

    def __init__(self, config: dict):
        super().__init__(
            name="market_analysis",
            config=config,
            enable_agentops=True
        )

        # Initialize specialized agents
        self.agents = {
            'wtp': WillingnessToPayAgent(
                model=config['agno_model'],
                enable_agentops=True
            ),
            'segment': MarketSegmentAgent(
                model=config['agno_model'],
                enable_agentops=True
            ),
            'pricing': PricePointAgent(
                model=config['agno_model'],
                enable_agentops=True
            )
        }

    async def analyze_submission(self, submission: dict) -> dict:
        """Run comprehensive analysis with all agents"""
        results = {}

        # Track workflow start
        self.track_workflow_step(
            agent_name="workflow",
            step_name="multi_agent_analysis",
            step_status="started",
            metadata={"submission_id": submission.get('id')}
        )

        try:
            # Run agents in parallel
            async with asyncio.TaskGroup() as tg:
                tasks = {
                    name: tg.create_task(agent.a_run(submission['text']))
                    for name, agent in self.agents.items()
                }

            # Collect results
            for name, task in tasks.items():
                results[name] = task.result()

            # Track successful completion
            self.track_workflow_step(
                agent_name="workflow",
                step_name="multi_agent_analysis",
                step_status="completed",
                metadata={"agent_count": len(results)}
            )

            return results

        except Exception as e:
            # Track errors
            self.track_workflow_step(
                agent_name="workflow",
                step_name="multi_agent_analysis",
                step_status="failed",
                metadata={"error": str(e)}
            )
            raise
```

## Key Design Principles

### 1. Simplicity Over Complexity
- **Maximum 3 core functions** per app (enforced by Pydantic validation)
- Simple, focused tools preferred over complex platforms
- One clear responsibility per module

### 2. Type Safety Everywhere
- Pydantic models validate all data structures
- SQLAlchemy models match Pydantic 1:1
- Full type hints throughout codebase

### 3. Error Handling & Validation
- Reddit API errors with fallbacks
- LLM output validation with Instructor
- Database transaction safety with rollbacks
- AgentOps tracking with graceful degradation

### 4. Performance & Scalability
- Batch LLM processing
- Database connection pooling
- pgvector for efficient similarity search
- AgentOps event batching for minimal overhead

## Command Line Options

```bash
# Reddit extraction
--limit N                    # Max submissions to fetch
--subreddits a b c           # Subreddits to fetch from
--sort-by hot|top|new        # Sorting method
--time-filter hour|day|week  # Time filter for top posts

# Quality filtering
--min-score 70.0            # Minimum opportunity score
--min-confidence 60.0        # Minimum confidence score
--validate-quality           # Enable additional validation

# Processing
--batch-size N              # LLM batch size
--test-mode                 # Use mock data
--dry-run                   # Process but don't store

# AgentOps
--enable-agentops           # Enable AgentOps tracking
--agentops-tags "a,b,c"     # Custom AgentOps tags

# Output
--log-level DEBUG|INFO|...  # Logging level
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=models --cov=extract --cov=transform --cov=load --cov=monitoring

# Run specific tests
pytest tests/test_extract.py
pytest tests/test_models.py
pytest tests/test_agentops_integration.py

# Run AgentOps-specific tests
pytest tests/transform/test_agno_agentops_unit.py
pytest tests/test_agentops_integration.py
```

### Test Coverage

Current test coverage is being actively improved:
- **models/cost_tracking.py**: 100% coverage ✅
- **config/settings.py**: 92% coverage ✅
- **transform/agno_analyzer.py**: 32.87% coverage (improvement in progress)
- **Target**: 80%+ coverage across all modules

## Database Schema

The pipeline uses a single `opportunities` table with:

- **Reddit metadata**: submission_id, subreddit, upvotes, comments
- **App analysis**: title, concept, problem, core_functions (JSON)
- **Market metrics**: market_demand, pain_intensity, monetization_potential
- **Scoring**: final_score, confidence_score, trust_level
- **Search**: pgvector embedding for similarity search
- **AgentOps fields**: session_id, agent_costs, tracking_metadata

## Example Output

```
STEP 1: Extracting Reddit submissions
✓ Extracted 10 submissions in 2.34s

STEP 2: Analyzing submissions with LLM
✓ Analyzed 10 submissions in 45.67s

STEP 3: Validating analysis quality
✓ Filtered to 3 high-quality analyses in 0.12s

STEP 4: Storing analyses to database
✓ Stored 3 analyses in 0.89s

AGENTOPS SESSION SUMMARY
Session ID: session_abc123
Duration: 48.02s
Total Cost: $0.15
Tokens Used: 5,234
Agents Run: 5
Success Rate: 100%

PIPELINE COMPLETION SUMMARY
Total execution time: 48.02s

Step Results:
  1. Extract: 10 submissions
  2. Analyze: 10 analyses
  3. Filter: 3 high-quality
  4. Store: 3 stored, 0 skipped, 0 errors

Quality Metrics:
  - Validation rate: 90.0%
  - High score rate: 30.0%
  - Average score: 75.3
```

## Development

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy .
```

### Adding New Features
1. Add Pydantic models in `models/`
2. Implement extraction/transform/load logic
3. Add comprehensive tests
4. Update documentation
5. Add AgentOps tracking if applicable

## Comparison with Pipeline v2

| Feature | Pipeline v2 | Pipeline v3 |
|---------|-------------|------------|
| Architecture | Complex ETL with conflicts | Clean ELT pattern |
| Type Safety | Partial validation | Full Pydantic validation |
| LLM Integration | Disabled due to conflicts | Instructor + Pydantic |
| Database | DLT SQLAlchemy hybrid | SQLAlchemy only |
| pgvector | Available but unused | Fully integrated |
| Error Handling | Complex workarounds | Clean transaction safety |
| Testing | Limited | Comprehensive |
| Code Quality | Technical debt | Clean, maintainable |
| AgentOps | Not integrated | Full production monitoring |
| Cost Tracking | Basic | Real-time with analytics |
| Multi-Agent | Single agent | Agno framework integration |
| Debug Mode | Basic logging | Enhanced debugging for agents |

## Documentation

### 📚 Implementation & Research

- **[docs/implementation/BRANCH_PLAN.md](./docs/implementation/BRANCH_PLAN.md)** - Branch planning and development strategy
- **[docs/implementation/TDD_IMPLEMENTATION_GUIDE.md](./docs/implementation/TDD_IMPLEMENTATION_GUIDE.md)** - TDD methodology guide for AgentOps integration
- **[docs/implementation/IMPLEMENTATION_SUMMARY.md](./docs/implementation/IMPLEMENTATION_SUMMARY.md)** - AgentOps integration implementation summary

### 📊 Architecture & Dependencies

- **[docs/architecture/requirements.txt](./docs/architecture/requirements.txt)** - Project dependencies and requirements
- **[docs/architecture/test-agno-architecture-design.md](./docs/architecture/test-agno-architecture-design.md)** - Agno integration architecture

### 🔌 AgentOps & Agno Integration

- **[docs/guides/agentops-agno-implementation-guide.md](./docs/guides/agentops-agno-implementation-guide.md)** - Comprehensive AgentOps-Agno integration guide
- **[docs/integrations/agentops.md](./docs/integrations/agentops.md)** - AgentOps integration overview
- **[docs/api/agentops-integration.md](./docs/api/agentops-integration.md)** - AgentOps API reference

## Next Steps

1. **Add embedding generation** for semantic similarity search
2. **Implement deduplication** using pgvector similarity
3. **Expand LLM providers** (Anthropic, Gemini, etc.)
4. **Add API endpoints** for external access
5. **Implement advanced AgentOps analytics** and custom dashboards
6. **Achieve 80%+ test coverage** across all modules
7. **Add multi-region deployment** support

## Advanced Features

### Production Deployment

For production deployment with AgentOps:

```python
# production.py
from config.settings import ProductionSettings
from workflows.tracked_workflow import TrackedWorkflow

# Production configuration
settings = ProductionSettings()

# Create production workflow
workflow = MarketAnalysisWorkflow({
    "enable_agentops": True,
    "track_costs": True,
    "orchestration_mode": "sequential",
    "consensus_threshold": 70.0,
    "agno_model": settings.agno_model,
    "api_key": settings.openai_api_key,
    "base_url": settings.agno_base_url,
    "timeout": 60,
    "batch_size": 20
})

# Run with monitoring
await workflow.run_with_monitoring(submissions)
```

### Custom Metrics

```python
# Track custom business metrics
tracker = get_tracker()

tracker.track_custom_event(
    "market_opportunity_identified",
    {
        "opportunity_score": 85,
        "market_size": "$10M",
        "competition": "low",
        "monetization_potential": "high"
    }
)
```

## Support

- **Documentation**: [RedditHarbor Docs](https://docs.redditharbor.com)
- **Issues**: [GitHub Issues](https://github.com/redditharbor/redditharbor/issues)
- **Community**: [Discord Community](https://discord.gg/redditharbor)
- **AgentOps Support**: [AgentOps Docs](https://docs.agentops.ai)

---

<div align="center">

**Built with ❤️ by the RedditHarbor Team**

[<span style="color: #FF6B35;">#FF6B35</span>](https://imgur.com/placeholder-color-ff6b35) • [<span style="color: #004E89;">#004E89</span>](https://imgur.com/placeholder-color-004e89) • [<span style="color: #F7B801;">#F7B801</span>](https://imgur.com/placeholder-color-f7b801)

</div>