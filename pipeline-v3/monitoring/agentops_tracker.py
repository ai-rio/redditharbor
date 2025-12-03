"""
AgentOps integration for Pipeline v3 monitoring and observability
Provides session management, cost tracking, and performance monitoring capabilities
"""

import os
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from functools import wraps
import asyncio
import threading

# AgentOps imports with fallback handling
try:
    import agentops
    AGENTOPS_AVAILABLE = True
except ImportError:
    AGENTOPS_AVAILABLE = False
    agentops = None

# Local imports
from models.cost_tracking import CostTracking, CostSummary

logger = logging.getLogger(__name__)


@dataclass
class AgentOpsConfig:
    """Configuration for AgentOps integration"""

    enabled: bool = True
    api_key: Optional[str] = None
    project_name: str = "pipeline-v3"
    auto_start_session: bool = True
    session_tags: List[str] = field(default_factory=lambda: ["production", "pipeline-v3"])
    instrument_llm_calls: bool = True  # Use manual tracking for better control
    max_retries: int = 3
    retry_delay: float = 1.0
    fallback_to_local_tracking: bool = True

    @classmethod
    def from_environment(cls) -> 'AgentOpsConfig':
        """Create configuration from environment variables"""
        return cls(
            enabled=os.getenv('AGENTOPS_ENABLED', 'true').lower() == 'true',
            api_key=os.getenv('AGENTOPS_API_KEY'),
            project_name=os.getenv('AGENTOPS_PROJECT_NAME', 'pipeline-v3'),
            auto_start_session=os.getenv('AGENTOPS_AUTO_START', 'true').lower() == 'true',
            session_tags=os.getenv('AGENTOPS_TAGS', 'production,pipeline-v3').split(','),
            instrument_llm_calls=os.getenv('AGENTOPS_INSTRUMENT_LLM', 'true').lower() == 'true',
            max_retries=int(os.getenv('AGENTOPS_MAX_RETRIES', '3')),
            retry_delay=float(os.getenv('AGENTOPS_RETRY_DELAY', '1.0')),
            fallback_to_local_tracking=os.getenv('AGENTOPS_FALLBACK', 'true').lower() == 'true'
        )


@dataclass
class SessionMetrics:
    """Metrics for a session"""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_cost: float = 0.0
    total_tokens: int = 0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_latency: float = 0.0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    agent_coordinations: List[Dict[str, Any]] = field(default_factory=list)
    workflow_steps: List[Dict[str, Any]] = field(default_factory=list)

    def get_success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100.0

    def get_avg_latency(self) -> float:
        """Calculate average latency in seconds"""
        if self.total_operations == 0:
            return 0.0
        return self.total_latency / self.total_operations

    def get_duration(self) -> Optional[float]:
        """Get session duration in seconds"""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()


class AgentOpsTracker:
    """
    AgentOps tracker for Pipeline v3 monitoring
    Provides comprehensive observability with fallback to local tracking
    """

    def __init__(self, config: Optional[AgentOpsConfig] = None):
        """
        Initialize AgentOps tracker

        Args:
            config: AgentOps configuration, defaults to environment variables
        """
        self.config = config or AgentOpsConfig.from_environment()
        self.agentops_available = AGENTOPS_AVAILABLE and self.config.enabled
        self.session_active = False
        self.current_session = None
        self.current_trace = None
        self.local_tracking_enabled = self.config.fallback_to_local_tracking

        # Local tracking data (fallback when AgentOps unavailable)
        self.local_sessions: Dict[str, SessionMetrics] = {}
        self.current_local_session = None

        # Thread safety
        self._lock = threading.RLock()

        # Performance optimizations
        self._batch_events = []  # Batch events for better performance
        self._batch_size = 10  # Process events in batches
        self._batch_timeout = 1.0  # Max seconds to wait before flushing batch
        self._last_batch_flush = time.time()

        # Async support
        self._async_event_queue = asyncio.Queue() if hasattr(asyncio, 'Queue') else None
        self._background_task = None

        # Initialize AgentOps if available
        try:
            if self.agentops_available and self.config.auto_start_session:
                self._initialize_agentops()
            elif not self.agentops_available:
                logger.warning("AgentOps not available, using local tracking fallback")
                if self.local_tracking_enabled:
                    logger.info("Local tracking enabled as fallback")
        except Exception as e:
            logger.error(f"Failed to initialize AgentOps: {e}")
            # Fallback to local tracking only
            self.agentops_available = False
            if self.local_tracking_enabled:
                logger.info("Falling back to local tracking only")

    def _initialize_agentops(self) -> bool:
        """Initialize AgentOps client"""
        if not AGENTOPS_AVAILABLE:
            return False

        try:
            with self._lock:
                agentops.init(
                    api_key=self.config.api_key,
                    auto_start_session=False,
                    tags=self.config.session_tags,
                    instrument_llm_calls=self.config.instrument_llm_calls
                )
                logger.info("AgentOps initialized successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to initialize AgentOps: {e}")
            if self.local_tracking_enabled:
                logger.info("Falling back to local tracking")
                return False
            raise

    def start_session(self, session_name: str, tags: Optional[List[str]] = None) -> Optional[str]:
        """
        Start a new tracking session

        Args:
            session_name: Name for the session
            tags: Additional tags for the session

        Returns:
            Session ID if successful, None otherwise
        """
        with self._lock:
            session_id = f"{session_name}_{int(time.time())}"

            # Create local session metrics
            session_metrics = SessionMetrics(
                session_id=session_id,
                start_time=datetime.utcnow()
            )

            self.current_local_session = session_id
            self.local_sessions[session_id] = session_metrics

            # Start AgentOps session if available
            if self.agentops_available:
                try:
                    self.current_trace = agentops.start_trace(
                        session_name,
                        tags=tags or self.config.session_tags
                    )
                    self.session_active = True
                    logger.info(f"AgentOps session started: {session_id}")
                    return session_id
                except Exception as e:
                    logger.error(f"Failed to start AgentOps session: {e}")
                    # Continue with local tracking only
            else:
                logger.info(f"Local tracking session started: {session_id}")

            return session_id

    def end_session(self, status: str = "success", metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        End current tracking session

        Args:
            status: Session completion status ("success", "error", "timeout")
            metadata: Additional metadata about the session

        Returns:
            Session summary if available
        """
        with self._lock:
            if not self.session_active and not self.current_local_session:
                logger.warning("No active session to end")
                return None

            session_summary = None

            # End AgentOps session
            if self.session_active and self.current_trace:
                try:
                    # Flush any remaining events before ending session
                    self._flush_event_batch()

                    agentops.end_trace(self.current_trace, status)
                    self.session_active = False
                    self.current_trace = None
                    logger.info("AgentOps session ended successfully")
                except Exception as e:
                    logger.error(f"Failed to end AgentOps session: {e}")

            # Update local session metrics
            if self.current_local_session and self.current_local_session in self.local_sessions:
                session_metrics = self.local_sessions[self.current_local_session]
                session_metrics.end_time = datetime.utcnow()

                # Generate session summary
                session_summary = self._generate_session_summary(session_metrics, status, metadata)

                self.current_local_session = None
                logger.info(f"Local session ended: {session_metrics.session_id}")

            return session_summary

    def _flush_event_batch(self) -> None:
        """Flush accumulated events to AgentOps for better performance"""
        if not self._batch_events or not self.agentops_available or not self.session_active:
            return

        try:
            events_to_process = self._batch_events.copy()
            self._batch_events.clear()
            self._last_batch_flush = time.time()

            # Process events in batch
            for event_name, event_data in events_to_process:
                try:
                    agentops.Event(event_name, event_data)
                except Exception as e:
                    logger.warning(f"Failed to process event {event_name}: {e}")
                    # Continue processing other events

            logger.debug(f"Flushed batch of {len(events_to_process)} events to AgentOps")

        except Exception as e:
            logger.error(f"Failed to flush event batch: {e}")

    def _should_flush_batch(self) -> bool:
        """Check if batch should be flushed"""
        return (
            len(self._batch_events) >= self._batch_size or
            time.time() - self._last_batch_flush >= self._batch_timeout
        )

    def _add_event_to_batch(self, event_name: str, event_data: Dict[str, Any]) -> None:
        """Add event to batch for processing"""
        self._batch_events.append((event_name, event_data))

        if self._should_flush_batch():
            self._flush_event_batch()

    def track_llm_call(self, model: str, tokens: int, cost: float,
                      latency: float, success: bool = True,
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track an LLM API call

        Args:
            model: Model name used
            tokens: Total tokens used
            cost: Cost in USD
            latency: Request latency in seconds
            success: Whether the call was successful
            metadata: Additional metadata

        Returns:
            True if tracking successful, False otherwise
        """
        # Update local tracking
        if self.current_local_session:
            session_metrics = self.local_sessions.get(self.current_local_session)
            if session_metrics:
                session_metrics.total_cost += cost
                session_metrics.total_tokens += tokens
                session_metrics.total_operations += 1
                session_metrics.total_latency += latency
                if success:
                    session_metrics.successful_operations += 1
                else:
                    session_metrics.failed_operations += 1

        # Track with AgentOps if available (using batching for performance)
        if self.agentops_available and self.session_active:
            try:
                event_data = {
                    "model": model,
                    "tokens": tokens,
                    "cost_usd": cost,
                    "latency_seconds": latency,
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat()
                }

                if metadata:
                    event_data.update(metadata)

                # Use batching for better performance
                self._add_event_to_batch("llm_call", event_data)
                return True
            except Exception as e:
                logger.error(f"Failed to track LLM call with AgentOps: {e}")
                return False

        return self.current_local_session is not None

    def track_cost_summary(self, cost_summary: CostSummary) -> bool:
        """
        Track a cost summary

        Args:
            cost_summary: Cost summary to track

        Returns:
            True if tracking successful, False otherwise
        """
        # Update local tracking
        if self.current_local_session:
            session_metrics = self.local_sessions.get(self.current_local_session)
            if session_metrics:
                session_metrics.total_cost += cost_summary.total_cost_usd
                session_metrics.total_tokens += cost_summary.total_tokens
                session_metrics.total_operations += cost_summary.analysis_count

        # Track with AgentOps if available
        if self.agentops_available and self.session_active:
            try:
                event_data = {
                    "type": "cost_summary",
                    "total_cost_usd": cost_summary.total_cost_usd,
                    "total_tokens": cost_summary.total_tokens,
                    "analysis_count": cost_summary.analysis_count,
                    "avg_cost_per_analysis": cost_summary.avg_cost_per_analysis,
                    "model_breakdown": cost_summary.model_breakdown,
                    "timestamp": datetime.utcnow().isoformat()
                }

                agentops.Event("cost_summary", event_data)
                return True
            except Exception as e:
                logger.error(f"Failed to track cost summary with AgentOps: {e}")
                return False

        return self.current_local_session is not None

    def track_latency(self, operation_name: str, latency: float,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track operation latency

        Args:
            operation_name: Name of the operation
            latency: Latency in seconds
            metadata: Additional metadata

        Returns:
            True if tracking successful, False otherwise
        """
        # Update local tracking
        if self.current_local_session:
            session_metrics = self.local_sessions.get(self.current_local_session)
            if session_metrics:
                session_metrics.total_operations += 1
                session_metrics.total_latency += latency
                session_metrics.successful_operations += 1  # Assume success for latency tracking

        # Track with AgentOps if available
        if self.agentops_available and self.session_active:
            try:
                event_data = {
                    "operation": operation_name,
                    "latency_seconds": latency,
                    "timestamp": datetime.utcnow().isoformat()
                }

                if metadata:
                    event_data.update(metadata)

                agentops.Event("latency", event_data)
                return True
            except Exception as e:
                logger.error(f"Failed to track latency with AgentOps: {e}")
                return False

        return self.current_local_session is not None

    def track_operation_result(self, operation_name: str, success: bool,
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track operation result (success/failure)

        Args:
            operation_name: Name of the operation
            success: Whether operation was successful
            metadata: Additional metadata

        Returns:
            True if tracking successful, False otherwise
        """
        # Update local tracking
        if self.current_local_session:
            session_metrics = self.local_sessions.get(self.current_local_session)
            if session_metrics:
                session_metrics.total_operations += 1
                if success:
                    session_metrics.successful_operations += 1
                else:
                    session_metrics.failed_operations += 1

        # Track with AgentOps if available
        if self.agentops_available and self.session_active:
            try:
                event_data = {
                    "operation": operation_name,
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat()
                }

                if metadata:
                    event_data.update(metadata)

                agentops.Event("operation_result", event_data)
                return True
            except Exception as e:
                logger.error(f"Failed to track operation result with AgentOps: {e}")
                return False

        return self.current_local_session is not None

    def track_error(self, error_type: str, error_message: str,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track an error

        Args:
            error_type: Type of error
            error_message: Error message
            metadata: Additional metadata

        Returns:
            True if tracking successful, False otherwise
        """
        # Update local tracking
        if self.current_local_session:
            session_metrics = self.local_sessions.get(self.current_local_session)
            if session_metrics:
                error_data = {
                    "type": error_type,
                    "message": error_message,
                    "timestamp": datetime.utcnow().isoformat()
                }
                if metadata:
                    error_data.update(metadata)
                session_metrics.errors.append(error_data)
                session_metrics.failed_operations += 1
                session_metrics.total_operations += 1

        # Track with AgentOps if available
        if self.agentops_available and self.session_active:
            try:
                event_data = {
                    "error_type": error_type,
                    "error_message": error_message,
                    "timestamp": datetime.utcnow().isoformat()
                }

                if metadata:
                    event_data.update(metadata)

                agentops.Event("error", event_data)
                return True
            except Exception as e:
                logger.error(f"Failed to track error with AgentOps: {e}")
                return False

        return self.current_local_session is not None

    def track_agent_coordination(self, primary_agent: str, coordinating_agent: str,
                                operation: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track multi-agent coordination

        Args:
            primary_agent: Name of primary agent
            coordinating_agent: Name of coordinating agent
            operation: Operation being performed
            metadata: Additional metadata

        Returns:
            True if tracking successful, False otherwise
        """
        # Update local tracking
        if self.current_local_session:
            session_metrics = self.local_sessions.get(self.current_local_session)
            if session_metrics:
                coordination_data = {
                    "primary_agent": primary_agent,
                    "coordinating_agent": coordinating_agent,
                    "operation": operation,
                    "timestamp": datetime.utcnow().isoformat()
                }
                if metadata:
                    coordination_data.update(metadata)
                session_metrics.agent_coordinations.append(coordination_data)

        # Track with AgentOps if available
        if self.agentops_available and self.session_active:
            try:
                event_data = {
                    "primary_agent": primary_agent,
                    "coordinating_agent": coordinating_agent,
                    "operation": operation,
                    "timestamp": datetime.utcnow().isoformat()
                }

                if metadata:
                    event_data.update(metadata)

                agentops.Event("agent_coordination", event_data)
                return True
            except Exception as e:
                logger.error(f"Failed to track agent coordination with AgentOps: {e}")
                return False

        return self.current_local_session is not None

    def track_workflow_step(self, agent_name: str, step_name: str,
                           step_status: str, step_duration: float,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Track workflow step across agents

        Args:
            agent_name: Name of the agent
            step_name: Name of the step
            step_status: Status of the step ("started", "completed", "failed")
            step_duration: Duration of the step in seconds
            metadata: Additional metadata

        Returns:
            True if tracking successful, False otherwise
        """
        # Update local tracking
        if self.current_local_session:
            session_metrics = self.local_sessions.get(self.current_local_session)
            if session_metrics:
                step_data = {
                    "agent_name": agent_name,
                    "step_name": step_name,
                    "status": step_status,
                    "duration_seconds": step_duration,
                    "timestamp": datetime.utcnow().isoformat()
                }
                if metadata:
                    step_data.update(metadata)
                session_metrics.workflow_steps.append(step_data)

        # Track with AgentOps if available
        if self.agentops_available and self.session_active:
            try:
                event_data = {
                    "agent_name": agent_name,
                    "step_name": step_name,
                    "step_status": step_status,
                    "step_duration": step_duration,
                    "timestamp": datetime.utcnow().isoformat()
                }

                if metadata:
                    event_data.update(metadata)

                agentops.Event("workflow_step", event_data)
                return True
            except Exception as e:
                logger.error(f"Failed to track workflow step with AgentOps: {e}")
                return False

        return self.current_local_session is not None

    def get_session_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get summary of current session

        Returns:
            Session summary if session active, None otherwise
        """
        if not self.current_local_session:
            return None

        session_metrics = self.local_sessions.get(self.current_local_session)
        if not session_metrics:
            return None

        return self._generate_session_summary(session_metrics, "active")

    def get_performance_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get performance summary of current session

        Returns:
            Performance summary if session active, None otherwise
        """
        if not self.current_local_session:
            return None

        session_metrics = self.local_sessions.get(self.current_local_session)
        if not session_metrics:
            return None

        return {
            "session_id": session_metrics.session_id,
            "avg_latency": session_metrics.get_avg_latency(),
            "success_rate": session_metrics.get_success_rate(),
            "total_operations": session_metrics.total_operations,
            "total_cost": session_metrics.total_cost,
            "total_tokens": session_metrics.total_tokens,
            "error_count": len(session_metrics.errors),
            "agent_coordinations": len(session_metrics.agent_coordinations),
            "workflow_steps": len(session_metrics.workflow_steps)
        }

    def _generate_session_summary(self, session_metrics: SessionMetrics,
                                 status: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate comprehensive session summary"""
        summary = {
            "session_id": session_metrics.session_id,
            "status": status,
            "start_time": session_metrics.start_time.isoformat(),
            "end_time": session_metrics.end_time.isoformat() if session_metrics.end_time else None,
            "duration_seconds": session_metrics.get_duration(),
            "total_cost_usd": round(session_metrics.total_cost, 6),
            "total_tokens": session_metrics.total_tokens,
            "total_operations": session_metrics.total_operations,
            "successful_operations": session_metrics.successful_operations,
            "failed_operations": session_metrics.failed_operations,
            "success_rate": session_metrics.get_success_rate(),
            "avg_latency_seconds": session_metrics.get_avg_latency(),
            "error_count": len(session_metrics.errors),
            "agent_coordinations": len(session_metrics.agent_coordinations),
            "workflow_steps": len(session_metrics.workflow_steps)
        }

        if metadata:
            summary["metadata"] = metadata

        # Include recent errors
        if session_metrics.errors:
            summary["recent_errors"] = session_metrics.errors[-5:]  # Last 5 errors

        return summary

    def track_llm_call_with_retry(self, model: str, tokens: int, cost: float,
                                 latency: float, success: bool = True,
                                 max_retries: Optional[int] = None) -> bool:
        """
        Track LLM call with retry mechanism

        Args:
            model: Model name used
            tokens: Total tokens used
            cost: Cost in USD
            latency: Request latency in seconds
            success: Whether the call was successful
            max_retries: Maximum retry attempts

        Returns:
            True if tracking successful, False otherwise
        """
        max_retries = max_retries or self.config.max_retries

        for attempt in range(max_retries + 1):
            try:
                return self.track_llm_call(model, tokens, cost, latency, success)
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Failed to track LLM call after {max_retries} retries: {e}")
                    return False

                logger.warning(f"Tracking attempt {attempt + 1} failed, retrying... ({e})")
                time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff

    def track_with_fallback(self, primary_tracking: Callable,
                          fallback_data: Dict[str, Any]) -> bool:
        """
        Track with fallback mechanism

        Args:
            primary_tracking: Primary tracking function
            fallback_data: Fallback data for local tracking

        Returns:
            True if any tracking successful, False otherwise
        """
        # Try primary tracking first
        try:
            if callable(primary_tracking):
                primary_tracking()
                return True
        except Exception as e:
            logger.warning(f"Primary tracking failed: {e}")

        # Use local tracking as fallback
        if self.current_local_session and fallback_data:
            try:
                # Implement basic local tracking based on fallback data
                session_metrics = self.local_sessions.get(self.current_local_session)
                if session_metrics:
                    if "cost" in fallback_data:
                        session_metrics.total_cost += fallback_data["cost"]
                    if "tokens" in fallback_data:
                        session_metrics.total_tokens += fallback_data["tokens"]
                    if "latency" in fallback_data:
                        session_metrics.total_latency += fallback_data["latency"]
                    session_metrics.total_operations += 1
                    session_metrics.successful_operations += 1
                return True
            except Exception as e:
                logger.error(f"Fallback tracking failed: {e}")

        return False


# Global tracker instance
_global_tracker: Optional[AgentOpsTracker] = None


def get_tracker() -> AgentOpsTracker:
    """Get or create global tracker instance"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = AgentOpsTracker()
    return _global_tracker


def track_llm_call(model: str, tokens: int, cost: float, latency: float,
                  success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to track LLM calls using global tracker"""
    return get_tracker().track_llm_call(model, tokens, cost, latency, success, metadata)


def track_latency(operation_name: str, latency: float,
                 metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to track latency using global tracker"""
    return get_tracker().track_latency(operation_name, latency, metadata)


def track_error(error_type: str, error_message: str,
               metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to track errors using global tracker"""
    return get_tracker().track_error(error_type, error_message, metadata)