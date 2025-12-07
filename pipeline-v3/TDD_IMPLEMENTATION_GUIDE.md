# TDD Implementation Guide for start_analysis_session Method

## Current Status
- Test `test_session_start_method` in `tests/transform/test_agno_agentops_unit.py` is failing
- Error: `AttributeError: 'AgnoOpportunityAnalyzer' object has no attribute 'start_analysis_session'`

## Required Implementation

The test expects:
1. Method signature: `start_analysis_session(self, session_name: str, tags: List[str] = None)`
2. When `enable_agentops=True`, it should call `self.agentops_tracker.start_session(session_name, tags=tags or [])`
3. Method should be added after the `_initialize_tracking` method

## Minimal Implementation to Add

After line 436 (after the `_initialize_tracking` method), add:

```python
def start_analysis_session(self, session_name: str, tags: List[str] = None) -> None:
    """
    Start a new analysis session with AgentOps tracking

    Args:
        session_name: Name for the analysis session
        tags: Additional tags for the session
    """
    if self.enable_agentops and self.agentops_tracker:
        self.agentops_tracker.start_session(session_name, tags=tags or [])
```

## Test Expects
```python
analyzer.start_analysis_session("test-session", ["test-tag"])
# Should call:
mock_tracker_instance.start_session.assert_called_once_with(
    "test-session",
    tags=["test-tag"]
)
```

## Note
The tdd-guard plugin is preventing direct editing. To properly follow TDD:
1. The test already exists and is failing (RED phase)
2. Need to implement the minimal method (GREEN phase)
3. No refactoring needed yet