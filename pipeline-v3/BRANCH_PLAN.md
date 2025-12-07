# Branch: feature/agentops-agno-integration

## 🎯 Objective
Implement comprehensive AgentOps integration for Agno agents using Agno skill best practices, bringing Agno observability up to LiteLLM standards.

## 📋 Implementation Plan

### Phase 1: Immediate Improvements (Quick Wins)

#### 1.1 Enable Agno Debug Mode
**Files to modify:**
- `transform/agno_analyzer.py` - Add debug mode initialization
- `transform/agno_agents.py` - Enable debug in BaseAgent

**Implementation:**
```python
# In AgnoOpportunityAnalyzer.__init__()
self.debug_mode = getattr(settings, 'agno_debug_mode', False)

# In BaseAgent.__init__()
agent.debug_mode = self.debug_mode
```

#### 1.2 Enhanced Session Management
**Files to modify:**
- `transform/agno_analyzer.py` - Implement proper session lifecycle

**Implementation:**
```python
def start_analysis_session(self, session_name: str, tags: List[str] = None):
    """Enhanced session management using Agno patterns"""
    if self.enable_agentops:
        self.agentops_tracker.start_session(session_name, tags=tags or [])

def end_analysis_session(self, status: str, message: str = None):
    """Proper session cleanup"""
    if self.enable_agentops and hasattr(self, 'agentops_tracker'):
        self.agentops_tracker.end_session(status, message)
```

### Phase 2: Agent-Level Tracking

#### 2.1 Enhanced BaseAgent with Tracking
**Files to modify:**
- `transform/agno_agents.py` - Enhance BaseAgent class

**Implementation:**
```python
class BaseAgent(Agent):
    def __init__(self, ..., enable_agentops=False, enable_debug=False):
        # ... existing code
        self.enable_agentops = enable_agentops
        self.enable_debug = enable_debug

        if self.enable_agentops:
            self.agentops_tracker = get_tracker()
            self.agent_name = self._get_agent_name()

    async def a_run(self, *args, **kwargs):
        """Enhanced run method with tracking"""
        if self.enable_agentops:
            start_time = time.time()

        try:
            result = await super().a_run(*args, **kwargs)

            if self.enable_agentops:
                duration = time.time() - start_time
                self._track_agent_completion(result, duration, "success")

            return result

        except Exception as e:
            if self.enable_agentops:
                duration = time.time() - start_time
                self._track_agent_completion(None, duration, "error", str(e))
            raise
```

#### 2.2 AgentOps Decorators
**New file:** `transform/agentops_decorators.py`

**Implementation:**
```python
from functools import wraps
from monitoring import get_tracker

def trace_agent(name: str, tags: List[str] = None):
    """Decorator for tracking agent execution"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracker = get_tracker()
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                tracker.track_event("agent_success", {
                    "agent": name,
                    "duration": duration,
                    "tags": tags or []
                })
                return result
            except Exception as e:
                duration = time.time() - start_time
                tracker.track_event("agent_error", {
                    "agent": name,
                    "duration": duration,
                    "error": str(e),
                    "tags": tags or []
                })
                raise
        return async_wrapper
    return decorator
```

### Phase 3: Cost Tracking Integration

#### 3.1 Enhanced Cost Tracking
**Files to modify:**
- `transform/agno_analyzer.py` - Add real cost tracking
- `transform/agno_agents.py` - Extract costs from API responses

**Implementation:**
```python
def extract_and_track_cost(self, response, agent_name: str):
    """Extract cost from Agno API response and track it"""
    try:
        # Extract cost from response
        cost = self._extract_cost_from_response(response)

        # Track with AgentOps
        if self.enable_agentops:
            self.agentops_tracker.track_llm_cost(cost, agent_name)

        return cost
    except Exception as e:
        logger.warning(f"Failed to extract cost for {agent_name}: {e}")
        return 0.0
```

#### 3.2 Cost Configuration
**Files to modify:**
- `models/cost_tracking.py` - Add Agno-specific cost models
- `config/settings.py` - Add Agno cost configuration

### Phase 4: Workflow Integration

#### 4.1 Tracked Workflow Class
**New file:** `transform/tracked_workflow.py`

**Implementation:**
```python
from agno.workflow.workflow import Workflow

class TrackedWorkflow(Workflow):
    """Enhanced workflow with AgentOps tracking"""

    def __init__(self, *args, enable_agentops=False, **kwargs):
        self.enable_agentops = enable_agentops
        super().__init__(*args, **kwargs)

    async def run(self, *args, **kwargs):
        if self.enable_agentops:
            start_time = time.time()
            session_id = f"workflow_{self.__class__.__name__}"
            tracker = get_tracker()
            tracker.start_session(session_id)

        try:
            result = await super().run(*args, **kwargs)

            if self.enable_agentops:
                duration = time.time() - start_time
                tracker.track_event("workflow_success", {
                    "workflow": self.__class__.__name__,
                    "duration": duration
                })
                tracker.end_session("success")

            return result

        except Exception as e:
            if self.enable_agentops:
                duration = time.time() - start_time
                tracker.track_event("workflow_error", {
                    "workflow": self.__class__.__name__,
                    "duration": duration,
                    "error": str(e)
                })
                tracker.end_session("error", str(e))
            raise
```

### Phase 5: Testing and Validation

#### 5.1 Enhanced Test Suite
**New files:**
- `tests/transform/test_agno_agentops_integration.py`
- `tests/transform/test_agno_cost_tracking.py`

#### 5.2 Performance Benchmarking
**Update:** `scripts/benchmark_agno_performance.py`

### Phase 6: Documentation

#### 6.1 Implementation Guide
**New file:** `docs/agno-integration/implementation/agentops-integration-guide.md`

#### 6.2 Configuration Reference
**Update:** `config/settings.py` documentation

## 🔧 Environment Setup

### Required Environment Variables
```bash
# AgentOps Configuration
AGENTOPS_API_KEY=your_agentops_key
AGENTOPS_PROJECT_NAME=redditharbor-agno
AGENTOPS_ENABLED=true

# Agno Configuration
AGNO_ENABLE_AGENTOPS=true
AGNO_DEBUG_MODE=true
AGNO_TRACK_COSTS=true

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_key
```

### Testing Commands
```bash
# Run AgentOps integration tests
python -m pytest tests/transform/test_agno_agentops_integration.py -v

# Run with AgentOps enabled
AGNO_ENABLE_AGENTOPS=true python -m pytest tests/transform/test_agno_analyzer.py -v

# Benchmark performance with tracking
python scripts/benchmark_agno_performance.py --with-agentops
```

## 📊 Success Metrics

### Observable Metrics
- ✅ **AgentOps Sessions**: Proper session lifecycle management
- ✅ **Agent Tracking**: Individual agent execution tracking
- ✅ **Cost Tracking**: Real cost extraction and tracking
- ✅ **Error Tracking**: Classified error tracking
- ✅ **Performance Metrics**: Latency and success rate monitoring

### Quality Metrics
- ✅ **Test Coverage**: >90% test coverage for new features
- ✅ **Documentation**: Complete implementation guides
- ✅ **Backward Compatibility**: No breaking changes
- ✅ **Performance**: No performance degradation

## 🎯 Expected Outcomes

### Short Term (Phase 1-2)
- Debug visibility improved by 10x
- Basic AgentOps tracking for all agents
- Proper session management

### Long Term (Phase 3-5)
- Complete feature parity with LiteLLM integration
- Comprehensive cost tracking
- Advanced error classification
- Production-ready observability

## 🔍 Risk Assessment

### Low Risk
- Enabling debug mode
- Session management improvements
- Basic tracking decorators

### Medium Risk
- Cost tracking modifications
- Performance monitoring overhead
- API response parsing changes

### Mitigation Strategies
- Implement feature flags for new tracking
- Maintain backward compatibility
- Comprehensive testing before deployment

## 📅 Timeline Estimate

- **Phase 1**: 1-2 days (Quick wins)
- **Phase 2**: 2-3 days (Agent-level tracking)
- **Phase 3**: 1-2 days (Cost tracking)
- **Phase 4**: 2-3 days (Workflow integration)
- **Phase 5**: 2-3 days (Testing)
- **Phase 6**: 1 day (Documentation)

**Total Estimated Time**: 9-14 days

---

## 🚀 Getting Started

1. **Verify branch**: `git checkout feature/agentops-agno-integration`
2. **Install dependencies**: `source .venv/bin/activate && pip install -e .`
3. **Set environment**: Copy `.env.template` to `.env` and configure
4. **Run tests**: `python -m pytest tests/transform/test_agno_analyzer.py -v`

**Ready to begin implementation!**