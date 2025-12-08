"""
Prometheus metrics collection for Pipeline v3 monitoring
"""

import logging
import time
from contextlib import contextmanager
from functools import wraps

try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Registry,
        generate_latest,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.getLogger(__name__).warning("prometheus_client not available - metrics disabled")

logger = logging.getLogger(__name__)


class PipelineMetrics:
    """
    Prometheus metrics collection for Pipeline v3
    Thread-safe metrics collection with pipeline-specific monitoring
    """

    def __init__(self, registry: CollectorRegistry | None = None):
        """
        Initialize pipeline metrics

        Args:
            registry: Prometheus registry (uses default if None)
        """
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus metrics disabled - prometheus_client not installed")
            self.enabled = False
            return

        self.enabled = True
        self.registry = registry or CollectorRegistry()

        # Pipeline execution metrics
        self.pipeline_duration = Histogram(
            'pipeline_execution_duration_seconds',
            'Total pipeline execution time',
            ['subreddits', 'sort_by', 'test_mode'],
            registry=self.registry
        )

        self.pipeline_runs_total = Counter(
            'pipeline_runs_total',
            'Total number of pipeline runs',
            ['status', 'test_mode'],
            registry=self.registry
        )

        # Stage-specific metrics
        self.stage_duration = Histogram(
            'pipeline_stage_duration_seconds',
            'Duration of individual pipeline stages',
            ['stage', 'subreddit_count'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0],
            registry=self.registry
        )

        # Reddit API metrics
        self.reddit_api_requests_total = Counter(
            'reddit_api_requests_total',
            'Total Reddit API requests',
            ['endpoint', 'status', 'subreddit'],
            registry=self.registry
        )

        self.reddit_api_duration = Histogram(
            'reddit_api_request_duration_seconds',
            'Reddit API request duration',
            ['endpoint', 'subreddit'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )

        self.reddit_submissions_extracted = Counter(
            'reddit_submissions_extracted_total',
            'Number of Reddit submissions extracted',
            ['subreddit', 'sort_by'],
            registry=self.registry
        )

        # LLM processing metrics
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total LLM processing requests',
            ['model', 'status'],
            registry=self.registry
        )

        self.llm_duration = Histogram(
            'llm_request_duration_seconds',
            'LLM request processing duration',
            ['model'],
            buckets=[1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0],
            registry=self.registry
        )

        self.llm_tokens_used = Counter(
            'llm_tokens_used_total',
            'Total LLM tokens used',
            ['model', 'type'],  # type: input, output
            registry=self.registry
        )

        self.llm_analyses_generated = Counter(
            'llm_analyses_generated_total',
            'Number of LLM analyses generated',
            ['quality_level'],  # high, medium, low
            registry=self.registry
        )

        # Database metrics
        self.database_operations_total = Counter(
            'database_operations_total',
            'Total database operations',
            ['operation', 'status'],
            registry=self.registry
        )

        self.database_duration = Histogram(
            'database_operation_duration_seconds',
            'Database operation duration',
            ['operation'],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
            registry=self.registry
        )

        self.database_records_stored = Counter(
            'database_records_stored_total',
            'Number of records stored in database',
            ['table', 'status'],
            registry=self.registry
        )

        # Quality metrics
        self.analysis_scores = Histogram(
            'analysis_score_distribution',
            'Distribution of analysis scores',
            buckets=[10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
            registry=self.registry
        )

        self.analysis_confidence = Histogram(
            'analysis_confidence_distribution',
            'Distribution of analysis confidence scores',
            buckets=[10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
            registry=self.registry
        )

        self.validation_rate = Gauge(
            'analysis_validation_rate',
            'Current analysis validation rate',
            registry=self.registry
        )

        # Staging metrics
        self.staging_batch_size = Histogram(
            'staging_batch_size_distribution',
            'Distribution of staging batch sizes',
            buckets=[1, 5, 10, 25, 50, 100, 250],
            registry=self.registry
        )

        self.deduplication_rate = Gauge(
            'deduplication_rate',
            'Current deduplication rate',
            registry=self.registry
        )

        # Error metrics
        self.pipeline_errors_total = Counter(
            'pipeline_errors_total',
            'Total pipeline errors',
            ['stage', 'error_type'],
            registry=self.registry
        )

        # Resource usage metrics
        self.active_operations = Gauge(
            'active_operations',
            'Number of currently active operations',
            ['operation_type'],
            registry=self.registry
        )

        logger.info("Pipeline metrics initialized successfully")

    def record_pipeline_start(
        self,
        subreddits: list[str],
        sort_by: str,
        test_mode: bool = False
    ) -> float:
        """Record pipeline start time"""
        start_time = time.time()
        if self.enabled:
            # Increment active operations
            self.active_operations.labels(operation_type='pipeline').inc()

        return start_time

    def record_pipeline_completion(
        self,
        start_time: float,
        subreddits: list[str],
        sort_by: str,
        test_mode: bool = False,
        success: bool = True
    ) -> None:
        """Record pipeline completion"""
        if not self.enabled:
            return

        duration = time.time() - start_time
        status = 'success' if success else 'failure'
        test_mode_str = 'true' if test_mode else 'false'

        # Record metrics
        self.pipeline_duration.labels(
            subreddits=','.join(subreddits),
            sort_by=sort_by,
            test_mode=test_mode_str
        ).observe(duration)

        self.pipeline_runs_total.labels(
            status=status,
            test_mode=test_mode_str
        ).inc()

        # Decrement active operations
        self.active_operations.labels(operation_type='pipeline').dec()

    def record_stage_duration(
        self,
        stage: str,
        duration: float,
        subreddit_count: int = 1
    ) -> None:
        """Record stage execution duration"""
        if self.enabled:
            self.stage_duration.labels(
                stage=stage,
                subreddit_count=subreddit_count
            ).observe(duration)

    def record_reddit_api_request(
        self,
        endpoint: str,
        subreddit: str,
        duration: float,
        status: str = 'success'
    ) -> None:
        """Record Reddit API request"""
        if self.enabled:
            self.reddit_api_requests_total.labels(
                endpoint=endpoint,
                status=status,
                subreddit=subreddit
            ).inc()

            self.reddit_api_duration.labels(
                endpoint=endpoint,
                subreddit=subreddit
            ).observe(duration)

    def record_submissions_extracted(
        self,
        count: int,
        subreddit: str,
        sort_by: str
    ) -> None:
        """Record submissions extracted from Reddit"""
        if self.enabled:
            self.reddit_submissions_extracted.labels(
                subreddit=subreddit,
                sort_by=sort_by
            ).inc(count)

    def record_llm_request(
        self,
        model: str,
        duration: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        success: bool = True
    ) -> None:
        """Record LLM processing request"""
        if self.enabled:
            status = 'success' if success else 'failure'

            self.llm_requests_total.labels(
                model=model,
                status=status
            ).inc()

            self.llm_duration.labels(model=model).observe(duration)

            if input_tokens > 0:
                self.llm_tokens_used.labels(
                    model=model,
                    type='input'
                ).inc(input_tokens)

            if output_tokens > 0:
                self.llm_tokens_used.labels(
                    model=model,
                    type='output'
                ).inc(output_tokens)

    def record_analyses_generated(
        self,
        count: int,
        quality_level: str = 'medium'
    ) -> None:
        """Record analyses generated by LLM"""
        if self.enabled:
            self.llm_analyses_generated.labels(
                quality_level=quality_level
            ).inc(count)

    def record_database_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True
    ) -> None:
        """Record database operation"""
        if self.enabled:
            status = 'success' if success else 'failure'

            self.database_operations_total.labels(
                operation=operation,
                status=status
            ).inc()

            self.database_duration.labels(operation=operation).observe(duration)

    def record_records_stored(
        self,
        count: int,
        table: str,
        success: bool = True
    ) -> None:
        """Record records stored in database"""
        if self.enabled:
            status = 'success' if success else 'failure'

            self.database_records_stored.labels(
                table=table,
                status=status
            ).inc(count)

    def record_analysis_scores(self, scores: list[float]) -> None:
        """Record distribution of analysis scores"""
        if self.enabled:
            for score in scores:
                self.analysis_scores.observe(score)

    def record_analysis_confidence(self, confidences: list[float]) -> None:
        """Record distribution of confidence scores"""
        if self.enabled:
            for confidence in confidences:
                self.analysis_confidence.observe(confidence)

    def update_validation_rate(self, rate: float) -> None:
        """Update current validation rate"""
        if self.enabled:
            self.validation_rate.set(rate)

    def record_staging_batch_size(self, batch_size: int) -> None:
        """Record staging batch size"""
        if self.enabled:
            self.staging_batch_size.observe(batch_size)

    def update_deduplication_rate(self, rate: float) -> None:
        """Update deduplication rate"""
        if self.enabled:
            self.deduplication_rate.set(rate)

    def record_pipeline_error(self, stage: str, error_type: str) -> None:
        """Record pipeline error"""
        if self.enabled:
            self.pipeline_errors_total.labels(
                stage=stage,
                error_type=error_type
            ).inc()

    def increment_active_operations(self, operation_type: str) -> None:
        """Increment active operations counter"""
        if self.enabled:
            self.active_operations.labels(operation_type=operation_type).inc()

    def decrement_active_operations(self, operation_type: str) -> None:
        """Decrement active operations counter"""
        if self.enabled:
            self.active_operations.labels(operation_type=operation_type).dec()

    def get_metrics(self) -> str:
        """Get Prometheus metrics text format"""
        if not self.enabled:
            return "# Metrics disabled - prometheus_client not installed\n"

        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return "# Error generating metrics\n"


# Global metrics instance
_metrics: PipelineMetrics | None = None


def get_metrics() -> PipelineMetrics:
    """Get global pipeline metrics instance"""
    global _metrics
    if _metrics is None:
        _metrics = PipelineMetrics()
    return _metrics


def measure_pipeline_stage(stage: str):
    """Decorator to measure pipeline stage execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                get_metrics().record_stage_duration(stage, duration)
        return wrapper
    return decorator


@contextmanager
def measure_operation(operation_type: str):
    """Context manager to measure operation duration"""
    metrics = get_metrics()
    try:
        metrics.increment_active_operations(operation_type)
        start_time = time.time()
        yield start_time
    finally:
        duration = time.time() - start_time
        metrics.decrement_active_operations(operation_type)
        logger.debug(f"Operation {operation_type} completed in {duration:.2f}s")


def record_error(stage: str, error_type: str):
    """Record pipeline error"""
    get_metrics().record_pipeline_error(stage, error_type)
