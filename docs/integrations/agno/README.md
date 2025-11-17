# Agno Integration

Agno is the multi-agent LLM framework used for monetization analysis in RedditHarbor.

## Overview

Agno replaced DSPy as the primary LLM orchestration framework, providing:
- Multi-agent architecture for specialized analysis tasks
- Team-based coordination for complex reasoning
- Native OpenRouter compatibility for cost-effective inference

## Documentation

- [Migration Guide](./migration-guide.md) - Complete guide for DSPy to Agno migration

## Architecture

```
MonetizationAgnoAnalyzer
├── WillingnessToPayAgent (WTP analysis)
├── MarketSegmentAgent (B2B/B2C classification)
├── PricePointAgent (Price extraction)
└── PaymentBehaviorAgent (Payment pattern analysis)
```

## Key Components

### Main Analyzer
**File**: `agent_tools/monetization_agno_analyzer.py`

```python
from agno.agent import Agent
from agno.team import Team

class MonetizationAgnoAnalyzer:
    def __init__(self):
        self.team = Team(
            name="MonetizationAnalysisTeam",
            agents=[
                self.create_wtp_agent(),
                self.create_segment_agent(),
                self.create_price_agent(),
                self.create_behavior_agent()
            ]
        )
```

### Agent Factory
**File**: `agent_tools/monetization_analyzer_factory.py`

Provides factory pattern for switching between DSPy (backup) and Agno implementations.

## Usage

```python
from agent_tools.monetization_analyzer_factory import create_monetization_analyzer

analyzer = create_monetization_analyzer()  # Returns Agno analyzer
result = await analyzer.analyze(opportunity_data)
```

## Performance Benefits

- **Cost**: ~60% reduction vs DSPy (via OpenRouter)
- **Speed**: Parallel agent execution
- **Quality**: Specialized agents for each analysis dimension
- **Observability**: Native AgentOps integration

## Related Documentation

- [AgentOps Integration](../agentops/) - Observability for Agno agents
- [Jina Integration](../jina/) - Market validation for Agno evidence
