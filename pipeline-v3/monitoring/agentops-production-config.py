"""
AgentOps Production Configuration for RedditHarbor Phase 5
===========================================================

This module provides production-ready configuration for AgentOps monitoring
including comprehensive session management, cost tracking, and performance metrics.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

# AgentOps imports (with fallback)
try:
    import agentops
    AGENTOPS_AVAILABLE = True
except ImportError:
    AGENTOPS_AVAILABLE = False
    logging.warning("AgentOps not available, using local tracking fallback")

# Local imports
from .agentops_decorators import trace
from .agentops_tracker import AgentOpsConfig, AgentOpsTracker

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class AgentOpsProductionConfig:
    """Production configuration for AgentOps"""

    # Basic configuration
    api_key: str
    project_name: str = "reddit-harbor-phase5"
    environment: Environment = Environment.PRODUCTION

    # Session configuration
    session_auto_start: bool = True
    session_max_duration: int = 3600  # 1 hour
    session_auto_end: bool = True

    # Event configuration
    event_batch_size: int = 10
    event_flush_interval: int = 1  # second
    event_max_retries: int = 3
    event_retry_delay: int = 1  # second

    # Tags for all events
    default_tags: list[str] = None

    # Cost tracking
    enable_cost_tracking: bool = True
    cost_daily_budget: float = 1000.0  # USD
    cost_hourly_budget: float = 50.0   # USD
    cost_alert_threshold: float = 0.8   # 80% of budget

    # Performance tracking
    enable_performance_tracking: bool = True
    latency_warning_threshold: float = 5000  # ms
    latency_critical_threshold: float = 10000  # ms
    success_rate_warning_threshold: float = 0.95
    success_rate_critical_threshold: float = 0.90

    # Local fallback
    enable_local_fallback: bool = True
    local_storage_path: str = "/var/log/agentops"
    local_max_events: int = 10000

    def __post_init__(self):
        """Post-initialization setup"""
        if self.default_tags is None:
            self.default_tags = ["production", "phase5", "agno-analyzer"]

        # Add environment to tags
        self.default_tags.append(self.environment.value)


class AgentOpsProductionManager:
    """Production manager for AgentOps with comprehensive monitoring"""

    def __init__(self, config: AgentOpsProductionConfig):
        self.config = config
        self.tracker: AgentOpsTracker | None = None
        self.session_id: str | None = None
        self.metrics: dict[str, Any] = {
            "sessions": {},
            "costs": {"hourly": {}, "daily": {}},
            "performance": {"latencies": [], "success_rates": []},
            "errors": []
        }
        self._lock = asyncio.Lock()

        # Initialize components
        self._initialize_tracker()
        self._setup_local_storage()

    def _initialize_tracker(self):
        """Initialize the AgentOps tracker"""
        try:
            agentops_config = AgentOpsConfig(
                api_key=self.config.api_key,
                project_name=self.config.project_name,
                environment=self.config.environment.value,
                tags=self.config.default_tags,
                auto_start_session=self.config.session_auto_start,
                enable_local_fallback=self.config.enable_local_fallback,
                local_storage_path=self.config.local_storage_path
            )

            self.tracker = AgentOpsTracker(agentops_config)
            logger.info(f"AgentOps tracker initialized for {self.config.environment.value}")

        except Exception as e:
            logger.error(f"Failed to initialize AgentOps tracker: {e}")
            if not self.config.enable_local_fallback:
                raise

    def _setup_local_storage(self):
        """Setup local storage for fallback"""
        if self.config.enable_local_fallback:
            os.makedirs(self.config.local_storage_path, exist_ok=True)
            logger.info(f"Local storage setup at {self.config.local_storage_path}")

    async def start_session(self, session_name: str = None, metadata: dict = None) -> str:
        """Start a new monitoring session"""
        if not self.tracker:
            logger.warning("No tracker available, session not started")
            return None

        try:
            async with self._lock:
                session_name = session_name or f"session-{int(time.time())}"
                metadata = metadata or {}

                # Add production metadata
                metadata.update({
                    "environment": self.config.environment.value,
                    "version": os.getenv("APP_VERSION", "unknown"),
                    "deployment_time": os.getenv("DEPLOYMENT_TIME", "unknown"),
                    "node_name": os.getenv("NODE_NAME", "unknown"),
                    "pod_name": os.getenv("POD_NAME", "unknown")
                })

                self.session_id = await self.tracker.start_session(session_name, metadata)

                # Track session
                self.metrics["sessions"][self.session_id] = {
                    "name": session_name,
                    "start_time": datetime.now().isoformat(),
                    "metadata": metadata,
                    "events": 0,
                    "errors": 0
                }

                logger.info(f"Started AgentOps session: {self.session_id}")
                return self.session_id

        except Exception as e:
            logger.error(f"Failed to start AgentOps session: {e}")
            return None

    async def end_session(self, status: str = "success", reason: str = None) -> dict:
        """End the current monitoring session"""
        if not self.tracker or not self.session_id:
            logger.warning("No active session to end")
            return {}

        try:
            async with self._lock:
                # Update session metrics
                if self.session_id in self.metrics["sessions"]:
                    session_data = self.metrics["sessions"][self.session_id]
                    session_data.update({
                        "end_time": datetime.now().isoformat(),
                        "status": status,
                        "reason": reason
                    })

                # End session
                summary = await self.tracker.end_session(status, reason)

                logger.info(f"Ended AgentOps session: {self.session_id} with status: {status}")
                self.session_id = None

                return summary

        except Exception as e:
            logger.error(f"Failed to end AgentOps session: {e}")
            return {}

    async def track_llm_call(self,
                          provider: str,
                          model: str,
                          prompt: str,
                          response: str,
                          tokens_used: int,
                          cost: float,
                          latency_ms: float,
                          success: bool = True,
                          error: str = None) -> None:
        """Track an LLM API call with comprehensive metrics"""
        if not self.tracker:
            return

        try:
            event_data = {
                "event_type": "llm_call",
                "provider": provider,
                "model": model,
                "tokens_used": tokens_used,
                "cost": cost,
                "latency_ms": latency_ms,
                "success": success,
                "error": error,
                "prompt_length": len(prompt),
                "response_length": len(response),
                "timestamp": datetime.now().isoformat()
            }

            # Track with AgentOps
            await self.tracker.track_event("llm_call", event_data)

            # Update local metrics
            if self.config.enable_cost_tracking:
                await self._update_cost_metrics(provider, model, cost)

            if self.config.enable_performance_tracking:
                await self._update_performance_metrics(latency_ms, success)

            # Update session
            if self.session_id and self.session_id in self.metrics["sessions"]:
                self.metrics["sessions"][self.session_id]["events"] += 1
                if not success:
                    self.metrics["sessions"][self.session_id]["errors"] += 1

        except Exception as e:
            logger.error(f"Failed to track LLM call: {e}")

    async def track_agent_execution(self,
                                  agent_name: str,
                                  input_data: dict,
                                  output_data: dict,
                                  execution_time_ms: float,
                                  success: bool = True,
                                  error: str = None) -> None:
        """Track agent execution"""
        if not self.tracker:
            return

        try:
            event_data = {
                "event_type": "agent_execution",
                "agent_name": agent_name,
                "execution_time_ms": execution_time_ms,
                "success": success,
                "error": error,
                "input_size": len(json.dumps(input_data)),
                "output_size": len(json.dumps(output_data)),
                "timestamp": datetime.now().isoformat()
            }

            await self.tracker.track_event("agent_execution", event_data)

            # Update performance metrics
            if self.config.enable_performance_tracking:
                await self._update_performance_metrics(execution_time_ms, success)

        except Exception as e:
            logger.error(f"Failed to track agent execution: {e}")

    async def track_submission_analysis(self,
                                     submission_id: str,
                                     subreddit: str,
                                     analysis_results: dict,
                                     total_time_ms: float,
                                     costs: dict[str, float],
                                     success: bool = True) -> None:
        """Track complete submission analysis"""
        if not self.tracker:
            return

        try:
            total_cost = sum(costs.values())

            event_data = {
                "event_type": "submission_analysis",
                "submission_id": submission_id,
                "subreddit": subreddit,
                "total_time_ms": total_time_ms,
                "total_cost": total_cost,
                "cost_breakdown": costs,
                "success": success,
                "analysis_quality": analysis_results.get("quality_score", 0),
                "timestamp": datetime.now().isoformat()
            }

            await self.tracker.track_event("submission_analysis", event_data)

            # Update metrics
            if self.config.enable_cost_tracking:
                await self._update_cost_metrics("total", "analysis", total_cost)

        except Exception as e:
            logger.error(f"Failed to track submission analysis: {e}")

    async def _update_cost_metrics(self, provider: str, model: str, cost: float):
        """Update cost tracking metrics"""
        now = datetime.now()

        # Hourly tracking
        hour_key = now.strftime("%Y-%m-%d-%H")
        if hour_key not in self.metrics["costs"]["hourly"]:
            self.metrics["costs"]["hourly"][hour_key] = 0
        self.metrics["costs"]["hourly"][hour_key] += cost

        # Daily tracking
        day_key = now.strftime("%Y-%m-%d")
        if day_key not in self.metrics["costs"]["daily"]:
            self.metrics["costs"]["daily"][day_key] = 0
        self.metrics["costs"]["daily"][day_key] += cost

        # Check budget alerts
        await self._check_budget_alerts()

    async def _update_performance_metrics(self, latency_ms: float, success: bool):
        """Update performance tracking metrics"""
        # Track latencies (keep last 1000)
        self.metrics["performance"]["latencies"].append(latency_ms)
        if len(self.metrics["performance"]["latencies"]) > 1000:
            self.metrics["performance"]["latencies"] = self.metrics["performance"]["latencies"][-1000:]

        # Track success rates (keep last 1000)
        self.metrics["performance"]["success_rates"].append(1 if success else 0)
        if len(self.metrics["performance"]["success_rates"]) > 1000:
            self.metrics["performance"]["success_rates"] = self.metrics["performance"]["success_rates"][-1000:]

        # Check performance alerts
        await self._check_performance_alerts(latency_ms)

    async def _check_budget_alerts(self):
        """Check if budgets are exceeded and send alerts"""
        now = datetime.now()

        # Check hourly budget
        hour_key = now.strftime("%Y-%m-%d-%H")
        hourly_cost = self.metrics["costs"]["hourly"].get(hour_key, 0)

        if hourly_cost > self.config.cost_hourly_budget * self.config.cost_alert_threshold:
            await self._send_alert(
                alert_type="budget_warning",
                message=f"Hourly cost alert: ${hourly_cost:.2f} (budget: ${self.config.cost_hourly_budget:.2f})",
                severity="warning",
                metadata={
                    "type": "hourly",
                    "current": hourly_cost,
                    "budget": self.config.cost_hourly_budget,
                    "percentage": (hourly_cost / self.config.cost_hourly_budget) * 100
                }
            )

        # Check daily budget
        day_key = now.strftime("%Y-%m-%d")
        daily_cost = self.metrics["costs"]["daily"].get(day_key, 0)

        if daily_cost > self.config.cost_daily_budget * self.config.cost_alert_threshold:
            await self._send_alert(
                alert_type="budget_warning",
                message=f"Daily cost alert: ${daily_cost:.2f} (budget: ${self.config.cost_daily_budget:.2f})",
                severity="warning",
                metadata={
                    "type": "daily",
                    "current": daily_cost,
                    "budget": self.config.cost_daily_budget,
                    "percentage": (daily_cost / self.config.cost_daily_budget) * 100
                }
            )

    async def _check_performance_alerts(self, latency_ms: float):
        """Check performance thresholds and send alerts"""
        # Latency alert
        if latency_ms > self.config.latency_critical_threshold:
            await self._send_alert(
                alert_type="performance_critical",
                message=f"Critical latency: {latency_ms:.0f}ms (threshold: {self.config.latency_critical_threshold}ms)",
                severity="critical",
                metadata={
                    "type": "latency",
                    "value": latency_ms,
                    "threshold": self.config.latency_critical_threshold
                }
            )
        elif latency_ms > self.config.latency_warning_threshold:
            await self._send_alert(
                alert_type="performance_warning",
                message=f"High latency: {latency_ms:.0f}ms (threshold: {self.config.latency_warning_threshold}ms)",
                severity="warning",
                metadata={
                    "type": "latency",
                    "value": latency_ms,
                    "threshold": self.config.latency_warning_threshold
                }
            )

    async def _send_alert(self, alert_type: str, message: str, severity: str, metadata: dict = None):
        """Send alert through various channels"""
        alert_data = {
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "environment": self.config.environment.value,
            "project": self.config.project_name,
            "metadata": metadata or {}
        }

        # Track alert in metrics
        self.metrics["errors"].append(alert_data)

        # Log alert
        if severity == "critical":
            logger.critical(message)
        elif severity == "warning":
            logger.warning(message)
        else:
            logger.info(message)

        # Send to AgentOps if available
        if self.tracker:
            try:
                await self.tracker.track_event("alert", alert_data)
            except Exception as e:
                logger.error(f"Failed to send alert to AgentOps: {e}")

        # TODO: Add integration with PagerDuty, Slack, etc.
        # This would be implemented based on your alerting infrastructure

    def get_metrics_summary(self) -> dict:
        """Get comprehensive metrics summary"""
        now = datetime.now()

        # Calculate current metrics
        recent_latencies = self.metrics["performance"]["latencies"][-100:]
        recent_success_rates = self.metrics["performance"]["success_rates"][-100:]

        # Calculate P95 latency
        sorted_latencies = sorted(recent_latencies)
        p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0

        # Calculate success rate
        success_rate = sum(recent_success_rates) / len(recent_success_rates) if recent_success_rates else 1.0

        # Current costs
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")
        current_hourly_cost = self.metrics["costs"]["hourly"].get(hour_key, 0)
        current_daily_cost = self.metrics["costs"]["daily"].get(day_key, 0)

        return {
            "timestamp": now.isoformat(),
            "environment": self.config.environment.value,
            "session_id": self.session_id,
            "active_session": self.session_id is not None,

            # Performance metrics
            "performance": {
                "p95_latency_ms": p95_latency,
                "avg_latency_ms": sum(recent_latencies) / len(recent_latencies) if recent_latencies else 0,
                "success_rate": success_rate,
                "recent_requests": len(recent_latencies)
            },

            # Cost metrics
            "costs": {
                "current_hourly": current_hourly_cost,
                "current_daily": current_daily_cost,
                "hourly_budget": self.config.cost_hourly_budget,
                "daily_budget": self.config.cost_daily_budget,
                "hourly_budget_remaining": self.config.cost_hourly_budget - current_hourly_cost,
                "daily_budget_remaining": self.config.cost_daily_budget - current_daily_cost
            },

            # Session metrics
            "sessions": {
                "total_sessions": len(self.metrics["sessions"]),
                "active_sessions": sum(1 for s in self.metrics["sessions"].values() if "end_time" not in s),
                "total_events": sum(s.get("events", 0) for s in self.metrics["sessions"].values()),
                "total_errors": sum(s.get("errors", 0) for s in self.metrics["sessions"].values())
            },

            # Recent alerts
            "recent_alerts": self.metrics["errors"][-10:]  # Last 10 alerts
        }

    async def cleanup_old_data(self, days_to_keep: int = 7):
        """Clean up old metrics data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        # Clean up old cost metrics
        for key in list(self.metrics["costs"]["hourly"].keys()):
            if datetime.strptime(key, "%Y-%m-%d-%H") < cutoff_date:
                del self.metrics["costs"]["hourly"][key]

        for key in list(self.metrics["costs"]["daily"].keys()):
            if datetime.strptime(key, "%Y-%m-%d") < cutoff_date:
                del self.metrics["costs"]["daily"][key]

        # Clean up old sessions
        for session_id in list(self.metrics["sessions"].keys()):
            session = self.metrics["sessions"][session_id]
            if "end_time" in session:
                end_time = datetime.fromisoformat(session["end_time"])
                if end_time < cutoff_date:
                    del self.metrics["sessions"][session_id]

        logger.info(f"Cleaned up data older than {days_to_keep} days")


# Production instance factory
def create_production_manager() -> AgentOpsProductionManager:
    """Create a production AgentOps manager from environment variables"""

    # Get configuration from environment
    config = AgentOpsProductionConfig(
        api_key=os.getenv("AGENTOPS_API_KEY", ""),
        project_name=os.getenv("AGENTOPS_PROJECT_NAME", "reddit-harbor-phase5"),
        environment=Environment(os.getenv("ENVIRONMENT", "production")),

        # Session configuration
        session_auto_start=os.getenv("AGENTOPS_AUTO_START", "true").lower() == "true",
        session_max_duration=int(os.getenv("AGENTOPS_SESSION_DURATION", "3600")),

        # Event configuration
        event_batch_size=int(os.getenv("AGENTOPS_BATCH_SIZE", "10")),
        event_flush_interval=int(os.getenv("AGENTOPS_FLUSH_INTERVAL", "1")),

        # Cost tracking
        enable_cost_tracking=os.getenv("AGENTOPS_COST_TRACKING", "true").lower() == "true",
        cost_daily_budget=float(os.getenv("AGENTOPS_DAILY_BUDGET", "1000.0")),
        cost_hourly_budget=float(os.getenv("AGENTOPS_HOURLY_BUDGET", "50.0")),

        # Performance tracking
        enable_performance_tracking=os.getenv("AGENTOPS_PERFORMANCE_TRACKING", "true").lower() == "true",
        latency_warning_threshold=float(os.getenv("AGENTOPS_LATENCY_WARNING", "5000")),
        latency_critical_threshold=float(os.getenv("AGENTOPS_LATENCY_CRITICAL", "10000")),

        # Local fallback
        enable_local_fallback=os.getenv("AGENTOPS_LOCAL_FALLBACK", "true").lower() == "true",
        local_storage_path=os.getenv("AGENTOPS_LOCAL_PATH", "/var/log/agentops")
    )

    return AgentOpsProductionManager(config)


# Decorator for automatic tracking
def track_submission_function(func):
    """Decorator to automatically track function execution"""
    @trace("submission_processing")
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            # Get manager if available
            manager = getattr(wrapper, '_agentops_manager', None)
            if manager and hasattr(result, 'get'):
                await manager.track_submission_analysis(
                    submission_id=result.get('submission_id', 'unknown'),
                    subreddit=result.get('subreddit', 'unknown'),
                    analysis_results=result,
                    total_time_ms=execution_time,
                    costs=result.get('costs', {}),
                    success=True
                )

            return result

        except Exception:
            execution_time = (time.time() - start_time) * 1000

            manager = getattr(wrapper, '_agentops_manager', None)
            if manager:
                await manager.track_submission_analysis(
                    submission_id='unknown',
                    subreddit='unknown',
                    analysis_results={},
                    total_time_ms=execution_time,
                    costs={},
                    success=False
                )

            raise

    return wrapper
