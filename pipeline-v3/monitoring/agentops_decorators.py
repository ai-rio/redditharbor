"""
AgentOps decorators for easy integration with Pipeline v3 components
Provides @trace and @tool decorators for automatic tracking
"""

import functools
import inspect
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from .agentops_tracker import get_tracker, track_error, track_latency

# Type hints for decorator functions
F = Callable[..., Any]
AsyncF = Callable[..., Any]


def trace(name: str | None = None, tags: list[str] | None = None,
         track_args: bool = False, track_result: bool = False,
         include_timing: bool = True, track_errors: bool = True) -> Callable:
    """
    Decorator to trace function execution with AgentOps

    Args:
        name: Name for the trace (defaults to function name)
        tags: Additional tags for the trace
        track_args: Whether to track function arguments
        track_result: Whether to track function result
        include_timing: Whether to include timing information
        track_errors: Whether to track errors automatically

    Returns:
        Decorated function with AgentOps tracing
    """
    def decorator(func: F) -> F:
        # Get function name if not provided
        trace_name = name or f"{func.__module__}.{func.__name__}"

        # Determine if function is async
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                tracker = get_tracker()
                start_time = time.time()
                operation_name = trace_name

                # Prepare metadata
                metadata = {
                    "function": trace_name,
                    "module": func.__module__,
                    "tags": tags or []
                }

                if track_args:
                    try:
                        # Serialize args safely (handle non-serializable objects)
                        safe_args = []
                        for arg in args:
                            if hasattr(arg, '__dict__'):
                                safe_args.append(str(type(arg).__name__))
                            else:
                                safe_args.append(str(arg)[:100])  # Limit length

                        safe_kwargs = {k: str(v)[:100] for k, v in kwargs.items()}
                        metadata["args"] = {"args": safe_args, "kwargs": safe_kwargs}
                    except Exception as e:
                        metadata["args_error"] = str(e)

                # Start trace if AgentOps available
                trace_id = None
                try:
                    trace_id = tracker.current_trace
                except:
                    pass  # Continue even if AgentOps not available

                try:
                    # Execute function
                    result = await func(*args, **kwargs)

                    # Calculate timing
                    if include_timing:
                        execution_time = time.time() - start_time
                        metadata["execution_time_seconds"] = execution_time
                        track_latency(operation_name, execution_time, metadata)

                    # Track result if requested
                    if track_result:
                        try:
                            if hasattr(result, '__dict__'):
                                metadata["result_type"] = type(result).__name__
                                metadata["result_summary"] = str(result)[:200]
                            else:
                                metadata["result"] = str(result)[:200]
                        except Exception as e:
                            metadata["result_error"] = str(e)

                    # Track successful execution
                    tracker.track_operation_result(
                        operation_name,
                        success=True,
                        metadata=metadata
                    )

                    return result

                except Exception as e:
                    # Handle errors
                    execution_time = time.time() - start_time

                    if track_errors:
                        error_metadata = {
                            **metadata,
                            "execution_time_seconds": execution_time,
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                        track_error(type(e).__name__, str(e), error_metadata)
                    else:
                        tracker.track_operation_result(
                            operation_name,
                            success=False,
                            metadata={**metadata, "execution_time_seconds": execution_time}
                        )

                    # Re-raise the exception
                    raise

            return async_wrapper  # type: ignore

        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                tracker = get_tracker()
                start_time = time.time()
                operation_name = trace_name

                # Prepare metadata
                metadata = {
                    "function": trace_name,
                    "module": func.__module__,
                    "tags": tags or []
                }

                if track_args:
                    try:
                        # Serialize args safely
                        safe_args = []
                        for arg in args:
                            if hasattr(arg, '__dict__'):
                                safe_args.append(str(type(arg).__name__))
                            else:
                                safe_args.append(str(arg)[:100])  # Limit length

                        safe_kwargs = {k: str(v)[:100] for k, v in kwargs.items()}
                        metadata["args"] = {"args": safe_args, "kwargs": safe_kwargs}
                    except Exception as e:
                        metadata["args_error"] = str(e)

                # Start trace if AgentOps available
                trace_id = None
                try:
                    trace_id = tracker.current_trace
                except:
                    pass  # Continue even if AgentOps not available

                try:
                    # Execute function
                    result = func(*args, **kwargs)

                    # Calculate timing
                    if include_timing:
                        execution_time = time.time() - start_time
                        metadata["execution_time_seconds"] = execution_time
                        track_latency(operation_name, execution_time, metadata)

                    # Track result if requested
                    if track_result:
                        try:
                            if hasattr(result, '__dict__'):
                                metadata["result_type"] = type(result).__name__
                                metadata["result_summary"] = str(result)[:200]
                            else:
                                metadata["result"] = str(result)[:200]
                        except Exception as e:
                            metadata["result_error"] = str(e)

                    # Track successful execution
                    tracker.track_operation_result(
                        operation_name,
                        success=True,
                        metadata=metadata
                    )

                    return result

                except Exception as e:
                    # Handle errors
                    execution_time = time.time() - start_time

                    if track_errors:
                        error_metadata = {
                            **metadata,
                            "execution_time_seconds": execution_time,
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                        track_error(type(e).__name__, str(e), error_metadata)
                    else:
                        tracker.track_operation_result(
                            operation_name,
                            success=False,
                            metadata={**metadata, "execution_time_seconds": execution_time}
                        )

                    # Re-raise the exception
                    raise

            return sync_wrapper

    return decorator


def tool(name: str | None = None, category: str | None = None,
        track_usage: bool = True, track_cost: bool = False,
        cost_callback: Callable[[], float] | None = None) -> Callable:
    """
    Decorator to mark and track tool usage

    Args:
        name: Tool name (defaults to function name)
        category: Tool category for grouping
        track_usage: Whether to track tool usage metrics
        track_cost: Whether to track tool cost
        cost_callback: Function to get tool cost

    Returns:
        Decorated function with tool tracking
    """
    def decorator(func: F) -> F:
        tool_name = name or func.__name__

        # Determine if function is async
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_tool_wrapper(*args, **kwargs) -> Any:
                tracker = get_tracker()
                start_time = time.time()

                # Prepare tool metadata
                metadata = {
                    "tool_name": tool_name,
                    "tool_category": category or "general",
                    "tool_function": f"{func.__module__}.{func.__name__}",
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Track tool usage start
                if track_usage:
                    try:
                        # Track tool invocation
                        tracker.track_operation_result(
                            f"tool:{tool_name}",
                            success=True,
                            metadata={**metadata, "event": "tool_invoked"}
                        )
                    except:
                        pass  # Continue even if tracking fails

                try:
                    # Execute tool function
                    result = await func(*args, **kwargs)

                    # Calculate execution time
                    execution_time = time.time() - start_time
                    metadata["execution_time_seconds"] = execution_time

                    # Track cost if requested
                    if track_cost and cost_callback:
                        try:
                            cost = cost_callback()
                            metadata["tool_cost_usd"] = cost
                            tracker.track_llm_call(
                                model=f"tool:{tool_name}",
                                tokens=0,  # Tokens not applicable for tools
                                cost=cost,
                                latency=execution_time,
                                success=True,
                                metadata=metadata
                            )
                        except:
                            pass

                    # Track successful tool completion
                    if track_usage:
                        try:
                            tracker.track_operation_result(
                                f"tool:{tool_name}",
                                success=True,
                                metadata={**metadata, "event": "tool_completed"}
                            )
                        except:
                            pass

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time
                    metadata["execution_time_seconds"] = execution_time
                    metadata["error_type"] = type(e).__name__
                    metadata["error_message"] = str(e)

                    # Track tool error
                    if track_usage:
                        try:
                            tracker.track_error(
                                f"tool_error:{tool_name}",
                                str(e),
                                {**metadata, "event": "tool_failed"}
                            )
                        except:
                            pass

                    # Re-raise the exception
                    raise

            return async_tool_wrapper  # type: ignore

        else:
            @functools.wraps(func)
            def sync_tool_wrapper(*args, **kwargs) -> Any:
                tracker = get_tracker()
                start_time = time.time()

                # Prepare tool metadata
                metadata = {
                    "tool_name": tool_name,
                    "tool_category": category or "general",
                    "tool_function": f"{func.__module__}.{func.__name__}",
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Track tool usage start
                if track_usage:
                    try:
                        tracker.track_operation_result(
                            f"tool:{tool_name}",
                            success=True,
                            metadata={**metadata, "event": "tool_invoked"}
                        )
                    except:
                        pass  # Continue even if tracking fails

                try:
                    # Execute tool function
                    result = func(*args, **kwargs)

                    # Calculate execution time
                    execution_time = time.time() - start_time
                    metadata["execution_time_seconds"] = execution_time

                    # Track cost if requested
                    if track_cost and cost_callback:
                        try:
                            cost = cost_callback()
                            metadata["tool_cost_usd"] = cost
                            tracker.track_llm_call(
                                model=f"tool:{tool_name}",
                                tokens=0,  # Tokens not applicable for tools
                                cost=cost,
                                latency=execution_time,
                                success=True,
                                metadata=metadata
                            )
                        except:
                            pass

                    # Track successful tool completion
                    if track_usage:
                        try:
                            tracker.track_operation_result(
                                f"tool:{tool_name}",
                                success=True,
                                metadata={**metadata, "event": "tool_completed"}
                            )
                        except:
                            pass

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time
                    metadata["execution_time_seconds"] = execution_time
                    metadata["error_type"] = type(e).__name__
                    metadata["error_message"] = str(e)

                    # Track tool error
                    if track_usage:
                        try:
                            tracker.track_error(
                                f"tool_error:{tool_name}",
                                str(e),
                                {**metadata, "event": "tool_failed"}
                            )
                        except:
                            pass

                    # Re-raise the exception
                    raise

            return sync_tool_wrapper

    return decorator


def llm_call(model_name: str | None = None,
            track_cost: bool = True, track_tokens: bool = True,
            custom_cost_calculator: Callable | None = None) -> Callable:
    """
    Decorator specifically for LLM API calls with detailed cost tracking

    Args:
        model_name: Name of the model being used
        track_cost: Whether to track cost
        track_tokens: Whether to track token usage
        custom_cost_calculator: Custom function to calculate cost

    Returns:
        Decorated function with LLM call tracking
    """
    def decorator(func: F) -> F:
        # Determine if function is async
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_llm_wrapper(*args, **kwargs) -> Any:
                tracker = get_tracker()
                start_time = time.time()

                try:
                    # Execute LLM call
                    result = await func(*args, **kwargs)

                    # Extract cost/token information from result
                    execution_time = time.time() - start_time
                    cost = 0.0
                    tokens = 0
                    model = model_name

                    # Try to extract usage information from result
                    if hasattr(result, 'usage'):
                        usage = result.usage
                        if hasattr(usage, 'prompt_tokens'):
                            tokens += usage.prompt_tokens
                        if hasattr(usage, 'completion_tokens'):
                            tokens += usage.completion_tokens
                        if hasattr(usage, 'total_tokens'):
                            tokens = usage.total_tokens

                    # Try to extract model from result
                    if hasattr(result, 'model'):
                        model = result.model

                    # Calculate cost
                    if track_cost:
                        if custom_cost_calculator:
                            try:
                                cost = custom_cost_calculator(model, tokens, result)
                            except:
                                cost = 0.0
                        else:
                            # Use default cost estimation (will be improved in integration)
                            cost = tokens * 0.000001  # $1 per 1M tokens default

                    # Track the LLM call
                    if track_cost or track_tokens:
                        metadata = {
                            "model": model,
                            "function": f"{func.__module__}.{func.__name__}",
                            "timestamp": datetime.utcnow().isoformat()
                        }

                        success = True
                        tracker.track_llm_call(
                            model=model or "unknown",
                            tokens=tokens if track_tokens else 0,
                            cost=cost if track_cost else 0.0,
                            latency=execution_time,
                            success=success,
                            metadata=metadata
                        )

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time

                    # Track failed LLM call
                    if track_cost:
                        tracker.track_llm_call(
                            model=model_name or "unknown",
                            tokens=0,
                            cost=0.0,
                            latency=execution_time,
                            success=False,
                            metadata={
                                "function": f"{func.__module__}.{func.__name__}",
                                "error": str(e),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )

                    # Re-raise the exception
                    raise

            return async_llm_wrapper  # type: ignore

        else:
            @functools.wraps(func)
            def sync_llm_wrapper(*args, **kwargs) -> Any:
                tracker = get_tracker()
                start_time = time.time()

                try:
                    # Execute LLM call
                    result = func(*args, **kwargs)

                    # Extract cost/token information from result
                    execution_time = time.time() - start_time
                    cost = 0.0
                    tokens = 0
                    model = model_name

                    # Try to extract usage information from result
                    if hasattr(result, 'usage'):
                        usage = result.usage
                        if hasattr(usage, 'prompt_tokens'):
                            tokens += usage.prompt_tokens
                        if hasattr(usage, 'completion_tokens'):
                            tokens += usage.completion_tokens
                        if hasattr(usage, 'total_tokens'):
                            tokens = usage.total_tokens

                    # Try to extract model from result
                    if hasattr(result, 'model'):
                        model = result.model

                    # Calculate cost
                    if track_cost:
                        if custom_cost_calculator:
                            try:
                                cost = custom_cost_calculator(model, tokens, result)
                            except:
                                cost = 0.0
                        else:
                            # Use default cost estimation (will be improved in integration)
                            cost = tokens * 0.000001  # $1 per 1M tokens default

                    # Track the LLM call
                    if track_cost or track_tokens:
                        metadata = {
                            "model": model,
                            "function": f"{func.__module__}.{func.__name__}",
                            "timestamp": datetime.utcnow().isoformat()
                        }

                        success = True
                        tracker.track_llm_call(
                            model=model or "unknown",
                            tokens=tokens if track_tokens else 0,
                            cost=cost if track_cost else 0.0,
                            latency=execution_time,
                            success=success,
                            metadata=metadata
                        )

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time

                    # Track failed LLM call
                    if track_cost:
                        tracker.track_llm_call(
                            model=model_name or "unknown",
                            tokens=0,
                            cost=0.0,
                            latency=execution_time,
                            success=False,
                            metadata={
                                "function": f"{func.__module__}.{func.__name__}",
                                "error": str(e),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )

                    # Re-raise the exception
                    raise

            return sync_llm_wrapper

    return decorator


class AgentOpsTraceContext:
    """Context manager for manual AgentOps tracing"""

    def __init__(self, name: str, tags: list[str] | None = None,
                 metadata: dict[str, Any] | None = None):
        self.name = name
        self.tags = tags or []
        self.metadata = metadata or {}
        self.tracker = get_tracker()
        self.session_id = None
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.session_id = self.tracker.start_session(self.name, self.tags)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time if self.start_time else 0

        status = "success"
        if exc_type is not None:
            status = "error"
            if exc_val:
                self.metadata["error_type"] = exc_type.__name__
                self.metadata["error_message"] = str(exc_val)

        self.metadata["execution_time_seconds"] = execution_time

        self.tracker.end_session(status, self.metadata)


def trace_context(name: str, tags: list[str] | None = None,
                  metadata: dict[str, Any] | None = None) -> AgentOpsTraceContext:
    """
    Create a trace context manager

    Args:
        name: Name for the trace
        tags: Additional tags
        metadata: Additional metadata

    Returns:
        AgentOpsTraceContext instance
    """
    return AgentOpsTraceContext(name, tags, metadata)


# Convenience functions for common patterns
def monitor_function(func: F) -> F:
    """Simple decorator for basic function monitoring"""
    return trace(name=f"{func.__module__}.{func.__name__}", include_timing=True)(func)


def monitor_tool(tool_name: str, category: str = "general") -> Callable:
    """Simple decorator for tool monitoring"""
    return tool(name=tool_name, category=category, track_usage=True)


def monitor_llm_call(model: str) -> Callable:
    """Simple decorator for LLM call monitoring"""
    return llm_call(model_name=model, track_cost=True, track_tokens=True)
