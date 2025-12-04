# Phase 2: Factory Pattern Integration

**Status**: Implementation Ready
**Phase**: 2 of 5
**Dependencies**: Phase 1 (Core Agno Integration)
**Estimated Duration**: 4 days

---

## Overview

Phase 2 introduces the factory pattern for creating Agno multi-agent analyzers, enabling seamless integration with Pipeline v3's existing analyzer infrastructure while maintaining full backward compatibility.

---

## Factory Pattern Integration

### File Location

**File**: `/pipeline-v3/transform/analyzer_factory.py`

### AgnoAnalyzerFactory Implementation

```python
class AgnoAnalyzerFactory(AnalyzerFactory):
    """
    Factory for creating Agno multi-agent analyzers

    New analyzer type for Pipeline v3 with backward compatibility
    """

    def create_analyzer(
        self,
        model: str = None,
        enable_agentops: bool = True,
        embedding_strategy: EmbeddingStrategy = None
    ) -> AgnoOpportunityAnalyzer:
        """Create Agno analyzer with Pipeline v3 configuration"""

        settings = get_settings()

        return AgnoOpportunityAnalyzer(
            model=model or settings.model_name,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            enable_agentops=enable_agentops,
            embedding_strategy=embedding_strategy
        )


# Usage in Pipeline v3
def get_analyzer(analyzer_type: str = "agno"):
    """Get analyzer instance based on type"""

    factories = {
        "simple": TestModeAnalyzerFactory(),
        "litellm": ProductionAnalyzerFactory(),
        "agno": AgnoAnalyzerFactory(),  # NEW
        "hybrid": HybridAnalyzerFactory()
    }

    return factories[analyzer_type].create_analyzer()
```

---

## Phase 2 Tasks

### Task List

1. **Add AgnoAnalyzerFactory** (1 day)
   - Create factory class in `analyzer_factory.py`
   - Implement `create_analyzer()` method
   - Add configuration parameter passing
   - Ensure settings integration

2. **Update Factory Provider** (1 day)
   - Modify `get_analyzer()` function
   - Add "agno" option to factory dictionary
   - Implement factory selection logic
   - Add default parameter handling

3. **Configuration Management** (1 day)
   - Define Agno-specific environment variables
   - Add configuration validation
   - Implement settings fallback mechanism
   - Document configuration options

4. **Integration Tests** (1 day)
   - Test factory creates Agno analyzer correctly
   - Verify configuration parameter passing
   - Test factory switching between analyzer types
   - Validate backward compatibility

### Deliverables

- Factory pattern support for Agno
- Configuration management system
- Comprehensive integration tests
- Updated documentation

---

## Configuration Integration

### Environment Variables

Add to `pipeline-v3/.env.local`:

```bash
# Agno Configuration
AGNO_ANALYZER_ENABLED=true
AGNO_ORCHESTRATION_MODE=sequential  # or "parallel"
AGNO_CONSENSUS_THRESHOLD=60.0  # Minimum confidence for consensus

# Model Configuration (reuse existing)
OPENROUTER_API_KEY=your_api_key
MONETIZATION_LLM_MODEL=anthropic/claude-haiku-4.5

# AgentOps Integration (already configured)
AGENTOPS_API_KEY=your_agentops_api_key
```

### Settings Schema

```python
# pipeline-v3/config/settings.py

class Settings(BaseSettings):
    # ... existing settings ...

    # Agno Configuration
    agno_analyzer_enabled: bool = Field(
        default=True,
        env="AGNO_ANALYZER_ENABLED"
    )
    agno_orchestration_mode: str = Field(
        default="sequential",
        env="AGNO_ORCHESTRATION_MODE"
    )
    agno_consensus_threshold: float = Field(
        default=60.0,
        env="AGNO_CONSENSUS_THRESHOLD"
    )
```

---

## Usage Examples

### Option 1: Explicit Agno Analyzer

```python
from transform.analyzer_factory import get_analyzer

analyzer = get_analyzer(analyzer_type="agno")
result = analyzer.analyze_submission(submission)
```

### Option 2: Via Main Pipeline with CLI Flag

```bash
python -m pipeline_v3 \
  --analyzer-type agno \
  --limit 25 \
  --subreddits productivity tools
```

### Option 3: Hybrid Mode (Fallback to LiteLLM)

```python
analyzer = get_analyzer(analyzer_type="hybrid")
results = analyzer.analyze_batch(submissions)
```

### Option 4: Custom Configuration

```python
from transform.analyzer_factory import AgnoAnalyzerFactory
from transform.embedding import EmbeddingStrategy

factory = AgnoAnalyzerFactory()
analyzer = factory.create_analyzer(
    model="anthropic/claude-haiku-4.5",
    enable_agentops=True,
    embedding_strategy=EmbeddingStrategy(...)
)
```

---

## Integration Tests

### File Location

**File**: `/tests/integration/test_agno_pipeline_integration.py`

### Test Suite

```python
import pytest
from transform.analyzer_factory import (
    get_analyzer,
    AgnoAnalyzerFactory,
    TestModeAnalyzerFactory,
    ProductionAnalyzerFactory
)
from transform.agno_analyzer import AgnoOpportunityAnalyzer
from transform.litellm_analyzer import LiteLLMAnalyzer
from models.submission import RedditSubmission
from models.analysis import AnalysisResult


def test_analyzer_factory_agno_creation():
    """Test factory creates Agno analyzer correctly"""
    factory = AgnoAnalyzerFactory()
    analyzer = factory.create_analyzer()

    assert isinstance(analyzer, AgnoOpportunityAnalyzer)
    assert analyzer.team is not None
    assert len(analyzer.team.agents) == 5  # 4 core + 1 market research


def test_get_analyzer_agno_type():
    """Test get_analyzer returns Agno analyzer for 'agno' type"""
    analyzer = get_analyzer(analyzer_type="agno")

    assert isinstance(analyzer, AgnoOpportunityAnalyzer)


def test_get_analyzer_litellm_type():
    """Test get_analyzer returns LiteLLM analyzer for 'litellm' type"""
    analyzer = get_analyzer(analyzer_type="litellm")

    assert isinstance(analyzer, LiteLLMAnalyzer)


def test_factory_switching_between_types():
    """Test switching between analyzer types via factory"""
    agno_analyzer = get_analyzer(analyzer_type="agno")
    litellm_analyzer = get_analyzer(analyzer_type="litellm")

    assert type(agno_analyzer) != type(litellm_analyzer)
    assert isinstance(agno_analyzer, AgnoOpportunityAnalyzer)
    assert isinstance(litellm_analyzer, LiteLLMAnalyzer)


def test_agno_factory_custom_parameters():
    """Test factory accepts custom configuration parameters"""
    factory = AgnoAnalyzerFactory()
    analyzer = factory.create_analyzer(
        model="anthropic/claude-opus-4",
        enable_agentops=False
    )

    assert analyzer.team.agents[0].model.model == "anthropic/claude-opus-4"
    assert analyzer.agentops_tracker is None


def test_backward_compatibility_with_existing_code():
    """Test existing pipeline code works with Agno analyzer"""
    analyzer = get_analyzer(analyzer_type="agno")

    # Test API compatibility
    submission = RedditSubmission(
        id="test123",
        title="Looking for project management tool",
        selftext="Need tool for B2B team collaboration",
        subreddit="SaaS",
        score=150,
        num_comments=45,
        created_utc=1234567890
    )

    # Should work with same API as LiteLLM analyzer
    result = analyzer.analyze_submission(submission)

    assert isinstance(result, AnalysisResult)
    assert result.submission_id == submission.id
    assert result.final_score >= 0 and result.final_score <= 100


def test_agno_analyzer_in_full_pipeline():
    """Test Agno analyzer works in complete pipeline"""
    from extract.reddit_client import RedditClient
    from load.database_writer import DatabaseWriter

    # Extract phase
    reddit = RedditClient()
    submissions = reddit.fetch_submissions(subreddit="SaaS", limit=5)

    # Transform phase with Agno
    analyzer = get_analyzer(analyzer_type="agno")
    results = [analyzer.analyze_submission(sub) for sub in submissions]

    # Load phase
    writer = DatabaseWriter()
    success = writer.save_opportunities(results)

    assert success
    assert len(results) == len(submissions)

    # Verify database storage
    for result in results:
        stored = writer.get_opportunity_by_id(result.id)
        assert stored is not None
        assert stored.agno_wtp_score is not None  # Agno-specific field


def test_agno_factory_configuration_validation():
    """Test factory validates configuration correctly"""
    factory = AgnoAnalyzerFactory()

    # Should raise error for invalid configuration
    with pytest.raises(ValueError):
        factory.create_analyzer(model="invalid_model_name")


def test_agno_analyzer_agentops_integration():
    """Test Agno analyzer integrates with AgentOps tracking"""
    analyzer = get_analyzer(analyzer_type="agno")

    submission = RedditSubmission(
        id="test456",
        title="Looking for automation tool",
        selftext="Need to automate repetitive tasks",
        subreddit="productivity",
        score=200,
        num_comments=60,
        created_utc=1234567890
    )

    result = analyzer.analyze_submission(submission)

    # Verify AgentOps tracking occurred
    assert analyzer.agentops_tracker is not None
    # AgentOps should have logged the analysis session
```

---

## API Compatibility Matrix

| Component | Current API | Agno Integration | Breaking Changes |
|-----------|------------|------------------|------------------|
| `analyze_submission()` | ✅ | ✅ Maintained | None |
| `analyze_batch_with_costs()` | ✅ | ✅ Enhanced | None |
| `AnalysisResult` | ✅ | ✅ Extended | None (additive) |
| `CostTracking` | ✅ | ✅ Enhanced | None |
| Factory Pattern | ✅ | ✅ New option | None |

### Migration Path

Add `analyzer_type="agno"` to factory calls. All existing code continues to work.

---

## Success Criteria

### Phase 2 Completion Checklist

- [ ] `AgnoAnalyzerFactory` class implemented
- [ ] `get_analyzer()` updated with "agno" option
- [ ] Configuration settings defined and documented
- [ ] All integration tests passing (100% success rate)
- [ ] Backward compatibility verified
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Performance benchmarks established

### Quality Metrics

- **Test Coverage**: >90% for factory pattern code
- **Integration Tests**: All 10+ tests passing
- **API Compatibility**: 100% backward compatible
- **Configuration Validation**: All edge cases covered

---

## Next Steps

After Phase 2 completion:

1. **Phase 3**: Jina market research integration
2. **Phase 4**: Database schema extensions
3. **Phase 5**: Production testing and optimization

---

## References

### Related Documentation

- [AGNO_INTEGRATION_ARCHITECTURE.md](/pipeline-v3/docs/AGNO_INTEGRATION_ARCHITECTURE.md) - Complete architecture
- [Phase 1: Core Agno Integration](/pipeline-v3/docs/agno-integration/implementation/phase-1-core-agno.md)
- [Phase 4: Database Schema Extensions](/pipeline-v3/docs/agno-integration/implementation/phase-4-database-schema.md)

### Code Files

- `/pipeline-v3/transform/analyzer_factory.py` - Factory implementation
- `/pipeline-v3/transform/agno_analyzer.py` - Agno analyzer (Phase 1)
- `/tests/integration/test_agno_pipeline_integration.py` - Integration tests

---

**Document Version**: 1.0
**Created**: 2025-12-03
**Last Updated**: 2025-12-03
**Status**: Implementation Ready
