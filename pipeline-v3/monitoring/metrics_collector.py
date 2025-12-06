"""
Metrics Collection Module
Integrates with Pipeline v3 to track execution metrics for live testing

Usage:
    from monitoring.metrics_collector import MetricsCollector, track_execution

    # Automatic tracking with decorator
    @track_execution(phase="transform", agent_name="wtp")
    def analyze_willingness_to_pay(submission):
        ...

    # Manual tracking
    collector = MetricsCollector()
    with collector.track("transform", "market", opportunity_id="opp-123"):
        result = agent.execute()
"""

import time
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from functools import wraps
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and stores pipeline execution metrics"""

    def __init__(self, database_url: Optional[str] = None, enabled: bool = True):
        """
        Initialize metrics collector

        Args:
            database_url: PostgreSQL connection string (uses settings if None)
            enabled: Whether metrics collection is enabled (default: True)
        """
        self.enabled = enabled
        self.database_url = database_url
        self._conn = None

        if enabled and not database_url:
            # Import settings only if needed
            from config import get_settings
            settings = get_settings()
            self.database_url = settings.database_url

    def _get_connection(self):
        """Get or create database connection"""
        if not self.enabled:
            return None

        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(self.database_url)
            except Exception as e:
                logger.error(f"Failed to connect to metrics database: {e}")
                self.enabled = False
                return None

        return self._conn

    def record_metric(
        self,
        phase: str,
        duration_seconds: float,
        success: bool,
        agent_name: Optional[str] = None,
        opportunity_id: Optional[str] = None,
        api_cost_usd: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a single metric to database

        Args:
            phase: Pipeline phase ('extract', 'transform', 'load', 'end_to_end')
            duration_seconds: Execution duration
            success: Whether execution succeeded
            agent_name: Optional agent name ('wtp', 'segment', 'price', 'payment', 'market')
            opportunity_id: Optional opportunity identifier
            api_cost_usd: Optional API cost in USD
            error_message: Optional error message if failed
            metadata: Optional additional context (JSON)
        """
        if not self.enabled:
            return

        conn = self._get_connection()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO pipeline_metrics (
                        opportunity_id,
                        phase,
                        agent_name,
                        duration_seconds,
                        api_cost_usd,
                        success,
                        error_message,
                        metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    opportunity_id,
                    phase,
                    agent_name,
                    duration_seconds,
                    api_cost_usd,
                    success,
                    error_message,
                    psycopg2.extras.Json(metadata) if metadata else None
                ))
            conn.commit()

        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            conn.rollback()

    @contextmanager
    def track(
        self,
        phase: str,
        agent_name: Optional[str] = None,
        opportunity_id: Optional[str] = None
    ):
        """
        Context manager for automatic execution tracking

        Usage:
            with collector.track("transform", "wtp", "opp-123"):
                # Your code here
                result = perform_analysis()

        Args:
            phase: Pipeline phase
            agent_name: Optional agent name
            opportunity_id: Optional opportunity ID

        Yields:
            Dict containing tracking context (can be updated with cost, metadata)
        """
        start_time = time.time()
        context = {
            "api_cost_usd": None,
            "metadata": {}
        }

        success = True
        error_message = None

        try:
            yield context
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            duration = time.time() - start_time

            self.record_metric(
                phase=phase,
                agent_name=agent_name,
                opportunity_id=opportunity_id,
                duration_seconds=duration,
                success=success,
                api_cost_usd=context.get("api_cost_usd"),
                error_message=error_message,
                metadata=context.get("metadata")
            )

    def close(self):
        """Close database connection"""
        if self._conn and not self._conn.closed:
            self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global collector instance
_global_collector = None


def get_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def track_execution(
    phase: str,
    agent_name: Optional[str] = None,
    opportunity_id_param: str = "opportunity_id"
):
    """
    Decorator for automatic function execution tracking

    Usage:
        @track_execution(phase="transform", agent_name="wtp")
        def analyze_willingness(submission, opportunity_id):
            # Function code
            return result

    Args:
        phase: Pipeline phase
        agent_name: Optional agent name
        opportunity_id_param: Name of function parameter containing opportunity_id
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            collector = get_collector()

            # Try to extract opportunity_id from function params
            opportunity_id = kwargs.get(opportunity_id_param)

            with collector.track(phase, agent_name, opportunity_id) as context:
                result = func(*args, **kwargs)

                # If result contains cost info, record it
                if isinstance(result, dict):
                    if "api_cost" in result:
                        context["api_cost_usd"] = result["api_cost"]
                    if "metadata" in result:
                        context["metadata"] = result["metadata"]

                return result

        return wrapper
    return decorator


# Example usage in pipeline code:
"""
# In transform/agno_analyzer.py:

from monitoring.metrics_collector import track_execution

class WillingnessToPayAgent:

    @track_execution(phase="transform", agent_name="wtp")
    def analyze(self, submission: dict, opportunity_id: str) -> dict:
        # Agent analysis code
        result = self._perform_analysis(submission)

        return {
            "analysis": result,
            "api_cost": 0.001,  # Will be automatically tracked
            "metadata": {"model": "gpt-4", "tokens": 150}
        }


# In orchestration/pipeline_orchestrator.py:

from monitoring.metrics_collector import MetricsCollector

class PipelineOrchestrator:

    def __init__(self):
        self.metrics = MetricsCollector()

    async def process_submission(self, submission: dict) -> dict:
        opportunity_id = f"opp-{submission['id']}"

        # Track entire pipeline execution
        with self.metrics.track("end_to_end", opportunity_id=opportunity_id):

            # Extract
            with self.metrics.track("extract", opportunity_id=opportunity_id):
                data = await self.extract(submission)

            # Transform
            with self.metrics.track("transform", opportunity_id=opportunity_id) as ctx:
                analysis = await self.transform(data)
                ctx["api_cost_usd"] = analysis.get("total_cost")

            # Load
            with self.metrics.track("load", opportunity_id=opportunity_id):
                await self.load(analysis)

        return analysis
"""
