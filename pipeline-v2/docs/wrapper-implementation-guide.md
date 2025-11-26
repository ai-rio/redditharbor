# Pipeline-v2 AI Agent Wrapper Implementation Guide

## Overview

This document describes the implementation of thin wrapper modules in `pipeline-v2/analysis/` that provide clean interfaces to AI agents extracted from `core/agents/`. The wrappers maintain full backward compatibility while enabling the new pipeline-v2 architecture.

## Architecture

The wrapper modules follow a consistent thin-wrapper pattern:

1. **Import Core Module**: Import from existing `core/agents/` modules
2. **Fallback Implementation**: Provide fallback classes when core modules unavailable
3. **Thin Wrapper**: Delegate to core implementation with minimal overhead
4. **Interface Preservation**: Maintain identical method signatures and return types

## Wrapper Modules

### 1. Opportunity Analyzer Wrapper

**File**: `pipeline-v2/analysis/opportunity.py`

**Purpose**: Wrapper for `core.agents.interactive.opportunity_analyzer.OpportunityAnalyzerAgent`

**Key Features**:
- 5-dimensional scoring methodology
- Market demand, pain intensity, monetization potential, market gap, technical feasibility
- Batch processing capabilities
- Validation reporting
- Business metrics tracking

**Interface**:
```python
class OpportunityAnalyzer:
    def __init__(self)
    def analyze_opportunity(self, submission_data: Dict[str, Any]) -> Dict[str, Any]
    def batch_analyze_opportunities(self, submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]
    def generate_validation_report(self, opportunity_id: str) -> Dict[str, Any]
    def track_business_metrics(self) -> Dict[str, Any]
    def continuous_analysis(self, duration_minutes: int) -> Dict[str, Any]
```

**Methodology Weights**:
```python
{
    "market_demand": 0.20,
    "pain_intensity": 0.25,
    "monetization_potential": 0.20,
    "market_gap": 0.10,
    "technical_feasibility": 0.05,
    "simplicity_score": 0.20
}
```

### 2. Monetization Analyzer Wrapper

**File**: `pipeline-v2/analysis/monetization.py`

**Purpose**: Wrapper for `core.agents.monetization.agno_analyzer.MonetizationAgnoAnalyzer`

**Key Features**:
- Multi-agent architecture with 4 specialized agents
- AgentOps cost tracking integration
- Subreddit purchasing power multipliers
- Streaming analysis support
- Consensus calculation from multiple agents

**Multi-Agent Architecture**:
- `WillingnessToPayAgent`: Sentiment and willingness analysis
- `MarketSegmentAgent`: B2B vs B2C classification
- `PricePointAgent`: Budget and pricing extraction
- `PaymentBehaviorAgent`: Current spending analysis

**Interface**:
```python
class MonetizationAnalyzer:
    def __init__(self, model: str = None, agentops_api_key: str = None)
    def analyze(self, text: str, subreddit: str, keyword_monetization_score: float = None) -> MonetizationAnalysis
    async def analyze_stream(self, text: str, subreddit: str) -> AsyncGenerator[str, None]
    def get_cost_report(self) -> Dict[str, Any]
```

**Subreddit Multipliers**:
```python
SUBREDDIT_PURCHASING_POWER = {
    "entrepreneur": 1.5,    # High purchasing power
    "business": 1.5,
    "startups": 1.4,
    "frugal": 0.6,          # Lower purchasing power
    "students": 0.7,
    # Default: 1.0
}
```

### 3. App Profiler Wrapper

**File**: `pipeline-v2/analysis/profiler.py`

**Purpose**: Wrapper for `core.agents.profiler.enhanced_profiler.EnhancedLLMProfiler`

**Key Features**:
- AI-powered app profile generation
- Cost tracking via LiteLLM
- Evidence-based profiling with Agno integration
- JSON parsing and repair mechanisms
- 1-3 core function constraint enforcement

**Interface**:
```python
class AppProfiler:
    def __init__(self)
    def generate_app_profile(self, text: str, title: str, subreddit: str, score: float) -> Dict[str, Any]
    def generate_app_profile_with_costs(self, text: str, title: str, subreddit: str, score: float, agno_analysis: Dict[str, Any] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]
    def generate_app_profile_with_evidence(self, text: str, title: str, subreddit: str, score: float, agno_analysis: Dict[str, Any] = None) -> Dict[str, Any]
    def get_cost_summary(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]
```

**Profile Structure**:
```python
{
    "app_name": str,                    # 1-3 words, problem-specific
    "problem_description": str,         # 1-2 sentences
    "app_concept": str,                 # 2-3 sentences
    "core_functions": List[str],        # 1-3 functions with clear boundaries
    "value_proposition": str,           # 1-2 sentences
    "target_user": str,                 # 1 sentence
    "monetization_model": str,          # 1 sentence with pricing
    "app_category": str,                # 1 word from predefined list
    "profession": str,                  # 1-2 words, job role
    "core_problems": List[str]          # 1-3 specific problems
}
```

## Fallback Implementation

Each wrapper includes comprehensive fallback implementations that activate when core modules are unavailable. This ensures:

1. **Graceful Degradation**: System continues to function with basic capabilities
2. **Type Safety**: All type hints remain valid with fallback classes
3. **Interface Compatibility**: Method signatures stay identical
4. **Testing Support**: Enables testing without full dependency stack

**Fallback Strategy**:
- Detect import failures for core modules
- Create minimal fallback classes with required interfaces
- Provide reasonable default values and behaviors
- Maintain all method signatures and return types

## Usage Examples

### Basic Opportunity Analysis

```python
from pipeline_v2.analysis import OpportunityAnalyzer

# Initialize analyzer
analyzer = OpportunityAnalyzer()

# Analyze single opportunity
submission_data = {
    "id": "opp_123",
    "title": "Need better project management tool",
    "text": "Current tools are too expensive and don't sync properly",
    "subreddit": "productivity",
    "engagement": {"upvotes": 100, "num_comments": 25}
}

result = analyzer.analyze_opportunity(submission_data)
print(f"Score: {result['final_score']}")
print(f"Priority: {result['priority']}")
```

### Monetization Analysis

```python
from pipeline_v2.analysis import MonetizationAnalyzer

# Initialize analyzer
analyzer = MonetizationAnalyzer(model="anthropic/claude-haiku-4.5")

# Analyze monetization potential
text = "Our team pays $300/month for Asana, looking for alternatives under $150/month"
result = analyzer.analyze(text, "projectmanagement")

print(f"WTP Score: {result.willingness_to_pay_score}")
print(f"Segment: {result.customer_segment}")
print(f"Sentiment: {result.sentiment_toward_payment}")
```

### App Profile Generation

```python
from pipeline_v2.analysis import AppProfiler

# Initialize profiler
profiler = AppProfiler()

# Generate app profile
profile = profiler.generate_app_profile(
    text="Need simple budgeting app that doesn't cost $15/month",
    title="Budget app alternatives",
    subreddit="personalfinance",
    score=75.0
)

print(f"App: {profile['app_name']}")
print(f"Functions: {profile['core_functions']}")
print(f"Monetization: {profile['monetization_model']}")
```

## Module Exports

The `pipeline_v2/analysis/__init__.py` module exports the main wrapper classes:

```python
from .opportunity import OpportunityAnalyzer
from .monetization import MonetizationAnalyzer
from .profiler import AppProfiler

__all__ = [
    "OpportunityAnalyzer",
    "MonetizationAnalyzer",
    "AppProfiler"
]
```

## Error Handling

The wrappers implement robust error handling:

1. **Import Failures**: Fallback classes activate automatically
2. **Core Agent Errors**: Errors are logged and propagated with context
3. **Method Validation**: Input parameters validated before delegation
4. **Graceful Failures**: Safe fallback values returned when possible

## Performance Considerations

- **Thin Overhead**: Wrappers add minimal computational overhead
- **Direct Delegation**: Most method calls delegate directly to core agents
- **Memory Efficiency**: No unnecessary data copying or transformation
- **Lazy Loading**: Core modules loaded only when needed

## Testing Strategy

The wrapper implementation includes comprehensive test coverage:

1. **Unit Tests**: Individual wrapper method testing
2. **Integration Tests**: End-to-end wrapper functionality
3. **Fallback Tests**: Validation of fallback implementations
4. **Characterization Tests**: Behavior preservation validation

## Migration Path

The wrappers enable gradual migration:

1. **Phase 1**: Deploy wrappers alongside existing core agents
2. **Phase 2**: Update imports to use wrapper interfaces
3. **Phase 3**: Remove direct core agent dependencies
4. **Phase 4**: Optimize wrappers for pipeline-v2 architecture

## Future Enhancements

Planned improvements to wrapper modules:

1. **Enhanced Caching**: Result caching for repeated analyses
2. **Async Support**: Full async interface for all methods
3. **Configuration Management**: Centralized wrapper configuration
4. **Performance Monitoring**: Built-in performance metrics
5. **Hot-swapping**: Runtime switching between core and fallback implementations

## Dependencies

**Required Dependencies**:
- Python 3.8+
- Type hints support

**Optional Dependencies** (for full functionality):
- Core agents from `core/agents/`
- External APIs (OpenRouter, AgentOps, etc.)
- Database connectivity (Supabase)

**Development Dependencies**:
- pytest for testing
- mypy for type checking
- ruff for linting and formatting

## Troubleshooting

**Common Issues**:

1. **Import Errors**: Check Python path and dependency installation
2. **Fallback Mode**: Verify core modules are available if needed
3. **Performance**: Monitor wrapper overhead in production
4. **Type Errors**: Ensure proper type hints in calling code

**Debug Information**:
- Wrapper logs import status and fallback activation
- Method delegation includes context in error messages
- Fallback mode can be checked via wrapper properties