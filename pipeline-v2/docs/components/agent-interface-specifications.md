# AI Agent Interface Specifications

Phase 3: AI Agent Wrappers Extraction - Interface Documentation

This document provides comprehensive interface specifications for extracting AI agents from `core/agents/` to `pipeline-v2/`. These specifications are derived from characterization tests and represent the current behavior that must be preserved.

## Overview

The AI agent extraction involves moving sophisticated analysis agents from the core module to the new pipeline-v2 architecture while maintaining full compatibility and functionality. This is a critical refactoring that requires careful interface preservation.

## Agent Modules Characterized

### 1. OpportunityAnalyzerAgent
**Location**: `core/agents/interactive/opportunity_analyzer.py`

**Purpose**: Automated opportunity analysis using 5-dimensional scoring methodology

#### Core Interface

```python
class OpportunityAnalyzerAgent:
    def __init__(self) -> None:
        """Initialize with Supabase client and methodology weights."""

    def analyze_opportunity(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single opportunity using 5-dimensional scoring.

        Args:
            submission_data: Dict containing text, engagement, subreddit info

        Returns:
            Dict with dimension_scores, final_score, priority, core_functions
        """

    def batch_analyze_opportunities(self, submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple opportunities with error handling."""

    def generate_validation_report(self, opportunity_id: str) -> Dict[str, Any]:
        """Generate validation status tracking."""

    def track_business_metrics(self) -> Dict[str, Any]:
        """Return current business KPI metrics."""

    def continuous_analysis(self, duration_minutes: int) -> Dict[str, Any]:
        """Run continuous analysis for specified duration."""
```

#### 5-Dimensional Scoring Methodology

```python
methodology_weights = {
    "market_demand": 0.20,        # Based on engagement and trending
    "pain_intensity": 0.25,       # Based on pain words and sentiment
    "monetization_potential": 0.20, # Based on payment signals
    "market_gap": 0.10,           # Based on competition analysis
    "technical_feasibility": 0.05, # Based on complexity indicators
    "simplicity_score": 0.20      # Based on function count constraint
}
```

#### Data Structures

```python
@dataclass
class OpportunityScore:
    opportunity_id: str
    market_demand: float          # 0-100
    pain_intensity: float        # 0-100
    monetization_potential: float # 0-100
    market_gap: float            # 0-100
    technical_feasibility: float # 0-100
    final_score: float
    priority: str                # 🔥 High Priority, ⚡ Med-High, etc.
    timestamp: str

@dataclass
class ValidationStatus:
    opportunity_id: str
    cross_platform: str          # Completed, In Progress, Planning
    market_research: str
    technical_assessment: str
    willingness_to_pay: str
    overall_confidence: float    # 0-1
```

### 2. MonetizationAgnoAnalyzer
**Location**: `core/agents/monetization/agno_analyzer.py`

**Purpose**: Multi-agent monetization analysis with cost tracking

#### Multi-Agent Architecture

```python
class MonetizationAgnoAnalyzer:
    def __init__(self, model: str = None, agentops_api_key: str = None):
        """
        Initialize 4 specialized agents with AgentOps cost tracking.

        Agents:
        - WillingnessToPayAgent: Sentiment and willingness analysis
        - MarketSegmentAgent: B2B vs B2C classification
        - PricePointAgent: Budget and pricing extraction
        - PaymentBehaviorAgent: Current spending analysis
        """

    def analyze(self, text: str, subreddit: str,
                keyword_monetization_score: float = None) -> MonetizationAnalysis:
        """
        Run coordinated multi-agent analysis.

        Returns MonetizationAnalysis with consensus from all agents.
        """

    async def analyze_stream(self, text: str, subreddit: str) -> AsyncGenerator[str, None]:
        """Stream analysis results with step-by-step reasoning."""

    def get_cost_report(self) -> Dict[str, Any]:
        """Retrieve AgentOps cost tracking data."""
```

#### MonetizationAnalysis Structure

```python
@dataclass
class MonetizationAnalysis:
    # Core scores (0-100)
    willingness_to_pay_score: float
    market_segment_score: float
    price_sensitivity_score: float
    revenue_potential_score: float

    # Extracted insights
    customer_segment: str           # B2B, B2C, Mixed, Unknown
    mentioned_price_points: List[str]
    existing_payment_behavior: str
    urgency_level: str              # Critical, High, Medium, Low
    sentiment_toward_payment: str   # Positive, Neutral, Negative
    payment_friction_indicators: List[str]

    # Composite score and metadata
    llm_monetization_score: float  # 0-100
    confidence: float               # 0-1
    reasoning: str
    subreddit_multiplier: float
```

#### Subreddit Purchasing Power Multipliers

```python
SUBREDDIT_PURCHASING_POWER = {
    # High purchasing power
    "entrepreneur": 1.5, "business": 1.5, "startups": 1.4, "saas": 1.4,

    # Medium purchasing power (baseline)
    "personalfinance": 1.0, "productivity": 1.0,

    # Lower purchasing power
    "frugal": 0.6, "students": 0.7, "college": 0.7,
}
```

### 3. LLMProfiler & EnhancedLLMProfiler
**Location**: `core/agents/profiler/`

**Purpose**: AI-powered app profile generation from Reddit posts

#### Base LLMProfiler Interface

```python
class LLMProfiler:
    def __init__(self) -> None:
        """Initialize with OpenRouter API and generic names blacklist."""

    def generate_app_profile(self, text: str, title: str, subreddit: str,
                           score: float) -> Dict[str, Any]:
        """
        Generate complete app profile using LLM analysis.

        Returns structured profile with 1-3 core functions.
        """
```

#### EnhancedLLMProfiler Interface

```python
class EnhancedLLMProfiler:
    def __init__(self) -> None:
        """Initialize with cost tracking and evidence integration."""

    def generate_app_profile_with_costs(self, text: str, title: str,
                                      subreddit: str, score: float,
                                      agno_analysis: Dict[str, Any] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate profile with comprehensive cost tracking.

        Returns (profile_data, cost_tracking_data)
        """

    def generate_app_profile_with_evidence(self, text: str, title: str,
                                         subreddit: str, score: float,
                                         agno_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate evidence-based profile with Agno integration."""

    def get_cost_summary(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate cost summary for multiple profiles."""
```

#### Profile Structure Requirements

```python
profile_structure = {
    # Core fields (required)
    "app_name": str,                    # 1-3 words, problem-specific
    "problem_description": str,         # 1-2 sentences
    "app_concept": str,                 # 2-3 sentences
    "core_functions": List[str],        # 1-3 functions with clear boundaries
    "value_proposition": str,           # 1-2 sentences
    "target_user": str,                 # 1 sentence
    "monetization_model": str,          # 1 sentence with pricing

    # Enhanced fields (required for EnhancedLLMProfiler)
    "app_category": str,                # 1 word from predefined list
    "profession": str,                  # 1-2 words, job role
    "core_problems": List[str],         # 1-3 specific problems

    # Metadata fields
    "cost_tracking": Dict[str, Any],    # Cost and usage data
    "ai_profile": Dict[str, Any],       # Comprehensive analysis
    "evidence_based": bool,             # Whether Agno evidence used
    "evidence_validation": Dict[str, Any]  # Evidence alignment scoring
}
```

### 4. MonetizationAnalyzerFactory
**Location**: `core/agents/monetization/factory.py`

**Purpose**: Framework selection and analyzer creation with backward compatibility

#### Factory Interface

```python
def get_monetization_analyzer(framework: str = None, model: str = None,
                            **kwargs) -> Union[MonetizationLLMAnalyzer, MonetizationAgnoAnalyzer]:
    """
    Create analyzer with automatic framework selection.

    Frameworks:
    - 'agno': Multi-agent architecture with cost tracking (default)
    - 'dspy': Original DSPy-based implementation
    """

def list_available_frameworks() -> Dict[str, Dict[str, Any]]:
    """Return availability status of both frameworks."""

def compare_frameworks() -> Dict[str, Any]:
    """Comprehensive comparison of framework capabilities."""

class MonetizationAnalyzerFactory:
    @staticmethod
    def create_analyzer(framework: str = None, model: str = None, **kwargs):
        """Class-based factory interface."""
```

## Wrapper Implementation Requirements

### 1. Interface Compatibility

All wrappers MUST maintain identical public interfaces:

- **Method signatures**: Same parameters, types, and return structures
- **Error handling**: Same exception types and error messages
- **Configuration**: Same environment variables and settings
- **Data structures**: Same field names, types, and constraints

### 2. Behavioral Preservation

Wrappers MUST preserve current behavior:

- **Scoring algorithms**: Same calculation methods and weights
- **Prompt engineering**: Same prompt structure and requirements
- **Consensus logic**: Same multi-agent coordination
- **Cost tracking**: Same token estimation and pricing
- **Validation rules**: Same field validation and constraints

### 3. Configuration Management

Wrappers MUST handle configuration identically:

- **Environment variables**: Same variable names and fallbacks
- **Settings integration**: Same centralized configuration
- **API keys**: Same key management and validation
- **Model selection**: Same default models and overrides

### 4. Error Handling

Wrappers MUST maintain error handling patterns:

- **Graceful degradation**: Same fallback mechanisms
- **Structured errors**: Same error response formats
- **Validation messages**: Same validation feedback
- **API failures**: Same retry logic and error reporting

## Implementation Phases

### RED Phase (Current)
- ✅ Characterization tests written and documented
- ✅ Interface specifications defined
- ✅ Current behavior captured in tests

### GREEN Phase (Next)
- 🔄 Implement wrapper interfaces
- 🔄 Pass all characterization tests
- 🔄 Maintain full backward compatibility

### REFACTOR Phase (Final)
- ⏳ Update imports throughout codebase
- ⏳ Remove original core/agents/ implementations
- ⏳ Update documentation and examples

## Testing Strategy

### Characterization Tests
- Document current behavior with comprehensive test suites
- Test initialization, method signatures, return structures
- Validate error handling and edge cases
- Ensure all configuration scenarios covered

### Compatibility Tests
- Verify wrapper produces identical outputs
- Test all framework combinations and configurations
- Validate cost tracking accuracy
- Ensure evidence integration works correctly

### Integration Tests
- Test wrapper within pipeline-v2 workflows
- Verify integration with existing pipeline components
- Validate performance and resource usage
- Test error recovery and resilience

## Migration Considerations

### Breaking Changes
- None planned - full backward compatibility required
- All existing code must continue to work unchanged
- Configuration and environment variables preserved

### Performance Impact
- Monitor for any performance regression
- Ensure cost tracking doesn't impact analysis speed
- Validate memory usage with multi-agent architecture

### Dependencies
- Maintain same external dependencies
- Handle optional dependencies gracefully (AgentOps, Agno)
- Preserve fallback mechanisms for missing dependencies

## Success Criteria

### Functional Requirements
- [ ] All characterization tests pass against wrappers
- [ ] Identical outputs for all input scenarios
- [ ] Full backward compatibility maintained
- [ ] All configuration options preserved

### Quality Requirements
- [ ] Code coverage maintained at 80%+
- [ ] All error scenarios handled gracefully
- [ ] Documentation complete and accurate
- [ ] Performance benchmarks met or exceeded

### Integration Requirements
- [ ] Seamless integration with pipeline-v2
- [ ] No breaking changes to existing code
- [ ] Configuration management preserved
- [ ] Monitoring and observability maintained