"""
AgentOps integration module for Pipeline v3 monitoring

This module provides comprehensive observability and cost tracking capabilities
for the Pipeline v3 system through AgentOps integration.

Key components:
- AgentOpsTracker: Core tracking functionality with fallback support
- Decorators: @trace, @tool, @llm_call for easy integration
- Session management: Automatic and manual session lifecycle management
- Performance monitoring: Latency, success rates, error tracking
- Cost tracking: LLM usage cost monitoring and aggregation
- Multi-agent coordination: Cross-agent workflow tracking
"""

from .agentops_tracker import (
    AgentOpsTracker,
    AgentOpsConfig,
    SessionMetrics,
    get_tracker,
    track_llm_call,
    track_latency,
    track_error
)

from .agentops_decorators import (
    trace,
    tool,
    llm_call,
    trace_context,
    AgentOpsTraceContext,
    monitor_function,
    monitor_tool,
    monitor_llm_call
)

__version__ = "1.0.0"
__all__ = [
    # Core tracking
    "AgentOpsTracker",
    "AgentOpsConfig",
    "SessionMetrics",
    "get_tracker",

    # Convenience functions
    "track_llm_call",
    "track_latency",
    "track_error",

    # Decorators
    "trace",
    "tool",
    "llm_call",

    # Context manager
    "trace_context",
    "AgentOpsTraceContext",

    # Convenience decorators
    "monitor_function",
    "monitor_tool",
    "monitor_llm_call"
]