# DSPy to Agno Migration Guide

This guide documents the migration from DSPy to Agno + LiteLLM + AgentOps for RedditHarbor's monetization analyzer.

## Overview

The migration replaces the DSPy-based monetization analyzer with a multi-agent architecture using:
- **Agno**: Multi-agent framework for coordinated analysis
- **LiteLLM**: Unified model management (already integrated)
- **AgentOps**: Comprehensive cost tracking and monitoring

## Key Improvements

### Architecture Changes
- **DSPy → Agno**: Single module → Multi-agent team
- **ChainOfThought → Specialized Agents**: One generic processor → Four specialized agents
- **Manual cost tracking → AgentOps**: No tracking → Built-in cost tracking
- **Synchronous only → Streaming support**: Static analysis → Real-time streaming

### New Features
1. **Multi-Agent Coordination**: Specialized agents for different analysis aspects
2. **Cost Tracking**: AgentOps integration for comprehensive cost monitoring
3. **Streaming Support**: Real-time analysis with intermediate results
4. **Better Error Handling**: Retry logic and graceful degradation
5. **Framework Selection**: Easy switching between DSPy and Agno implementations

## File Structure

### New Files
```
agent_tools/
├── monetization_agno_analyzer.py      # New Agno-based implementation
├── monetization_analyzer_factory.py   # Factory for framework selection
└── __init__.py                        # Module exports
```

### Existing Files (Preserved)
```
agent_tools/
└── monetization_llm_analyzer.py       # Original DSPy implementation
```

### Configuration Updates
```python
# config/settings.py - New configuration options
AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
MONETIZATION_FRAMEWORK = os.getenv("MONETIZATION_FRAMEWORK", "agno")
AGNO_TIMEOUT = int(os.getenv("AGNO_TIMEOUT", "30"))
AGNO_MAX_RETRIES = int(os.getenv("AGNO_MAX_RETRIES", "3"))
```

## Usage

### Basic Usage (Drop-in Replacement)
```python
from agent_tools.monetization_analyzer_factory import get_monetization_analyzer

# Automatically uses configured framework (defaults to "agno")
analyzer = get_monetization_analyzer()

# Same API as before
result = analyzer.analyze(
    text="Looking for a project management tool under $100/month",
    subreddit="projectmanagement"
)
```

### Framework Selection
```python
# Explicit framework selection
agno_analyzer = get_monetization_analyzer(framework="agno")
dspy_analyzer = get_monetization_analyzer(framework="dspy")

# Or use convenience functions
from agent_tools import create_agno_analyzer, create_dspy_analyzer

agno_analyzer = create_agno_analyzer()
dspy_analyzer = create_dspy_analyzer()
```

### Streaming Analysis
```python
import asyncio

async def stream_analysis():
    analyzer = create_agno_analyzer()

    async for chunk in analyzer.analyze_stream(text, subreddit):
        data = json.loads(chunk)
        step = data['step']
        # Process intermediate results
        if step == 'willingness_analysis':
            print(f"WTP Analysis: {data['result']}")
        elif step == 'final_analysis':
            print(f"Final Score: {data['result']['llm_monetization_score']}")

asyncio.run(stream_analysis())
```

### Cost Tracking
```python
analyzer = create_agno_analyzer(agentops_api_key="your-api-key")

# Run analysis
result = analyzer.analyze(text, subreddit)

# Get cost report
cost_report = analyzer.get_cost_report()
print(f"Session cost: ${cost_report['total_cost']}")
```

## Agent Architecture

### Specialized Agents
1. **WillingnessToPayAgent**: Analyzes sentiment and willingness to pay
2. **MarketSegmentAgent**: Classifies B2B vs B2C market segments
3. **PricePointAgent**: Extracts pricing information and budget signals
4. **PaymentBehaviorAgent**: Analyzes existing payment patterns

### Team Coordination
The agents work as a team to provide comprehensive analysis:
```python
team = Team(
    name="Monetization Analysis Team",
    agents=[wtp_agent, segment_agent, price_agent, behavior_agent]
)
```

## Configuration

### Environment Variables
```bash
# Required
OPENROUTER_API_KEY=your-openrouter-api-key

# Optional (for cost tracking)
AGENTOPS_API_KEY=your-agentops-api-key

# Framework selection
MONETIZATION_FRAMEWORK=agno  # or "dspy"

# Model configuration
MONETIZATION_LLM_MODEL=anthropic/claude-haiku-4.5
```

### Framework Comparison
| Feature | DSPy | Agno |
|---------|------|------|
| Architecture | Single module | Multi-agent team |
| Cost Tracking | Manual | AgentOps integration |
| Streaming | No | Yes |
| Error Handling | Basic | Advanced |
| Extensibility | Limited | High |
| Dependencies | Fewer | More |

## Migration Steps

### For Existing Code
1. **No immediate changes required** - Factory defaults to Agno
2. **Optional**: Explicitly specify framework if needed
3. **Optional**: Add AgentOps API key for cost tracking

### For New Development
1. Use factory pattern: `get_monetization_analyzer()`
2. Consider streaming for real-time analysis
3. Enable AgentOps for production cost tracking

## Backward Compatibility

The migration maintains full backward compatibility:
- Same `MonetizationAnalysis` dataclass output
- Same method signatures
- Same subreddit purchasing power multipliers
- Same scoring algorithms

## Testing

Run the migration test suite:
```bash
cd /home/carlos/projects/redditharbor
python test_agno_migration.py
```

Or test individual implementations:
```bash
# Test Agno implementation
python agent_tools/monetization_agno_analyzer.py

# Test factory pattern
python agent_tools/monetization_analyzer_factory.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install missing dependencies
   uv sync
   ```

2. **AgentOps Not Working**
   ```python
   # Check if AgentOps is enabled
   analyzer = create_agno_analyzer()
   print(f"AgentOps enabled: {analyzer.agentops_enabled}")
   ```

3. **Framework Not Available**
   ```python
   # Check available frameworks
   from agent_tools import list_available_frameworks
   print(list_available_frameworks())
   ```

### Performance Considerations

- **Agno** uses more memory due to multi-agent architecture
- **AgentOps** adds minimal overhead for cost tracking
- **Streaming** provides better user experience for long analyses

## Future Enhancements

### Planned Features
1. **Agent-specific cost tracking**: Track costs per agent
2. **Custom agent creation**: Add domain-specific agents
3. **Parallel processing**: Run agents in parallel for faster analysis
4. **Agent memory**: Maintain context across analyses
5. **Custom tool integration**: Add external tools for agents

### Extension Points
```python
# Create custom agents
class CustomAgent(Agent):
    def __init__(self, model: str):
        super().__init__(
            name="Custom Analyst",
            role="Custom analysis",
            instructions="Custom instructions...",
            model=OpenAIChat(model=model)
        )

# Extend existing teams
custom_team = Team(
    name="Enhanced Analysis Team",
    agents=[
        WillingnessToPayAgent(model),
        MarketSegmentAgent(model),
        CustomAgent(model)  # Add custom agent
    ]
)
```

## Support

For issues or questions:
1. Check the test suite: `python test_agno_migration.py`
2. Review framework comparison: `python agent_tools/monetization_analyzer_factory.py`
3. Enable debug logging for detailed error information