"""
OpenTelemetry tracing for Pipeline v3
Provides distributed tracing for end-to-end pipeline monitoring
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from functools import wraps

# Check if OpenTelemetry is available
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.trace import SpanAttributes
    from opentelemetry.propagate import inject, extract
    from opentelemetry.context import Context
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

logger = logging.getLogger(__name__)


class PipelineTracer:
    """
    OpenTelemetry tracing for Pipeline v3
    Provides distributed tracing with automatic span management
    """

    def __init__(
        self,
        service_name: str = "pipeline-v3",
        service_version: str = "3.0.0",
        environment: str = "development",
        jaeger_endpoint: Optional[str] = None,
        otlp_endpoint: Optional[str] = None
    ):
        """
        Initialize pipeline tracer

        Args:
            service_name: Name of the service
            service_version: Service version
            environment: Environment (development, staging, production)
            jaeger_endpoint: Jaeger collector endpoint
            otlp_endpoint: OTLP collector endpoint
        """
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available - tracing disabled")
            self.enabled = False
            return

        self.enabled = True
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

        try:
            # Set up tracer provider
            self._setup_tracing(jaeger_endpoint, otlp_endpoint)
            logger.info("OpenTelemetry tracing initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            self.enabled = False

    def _setup_tracing(self, jaeger_endpoint: Optional[str], otlp_endpoint: Optional[str]):
        """Set up OpenTelemetry tracing configuration"""
        # Create resource with service metadata
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": self.service_version,
            "service.namespace": "reddit-data-pipeline",
            "deployment.environment": self.environment,
            "service.instance.id": str(uuid.uuid4())
        })

        # Set up tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(self.tracer_provider)

        # Configure exporters
        exporters = []

        # Jaeger exporter (if configured)
        if jaeger_endpoint:
            try:
                jaeger_exporter = JaegerExporter(
                    endpoint=jaeger_endpoint,
                    collector_endpoint=jaeger_endpoint
                )
                exporters.append(jaeger_exporter)
                logger.info("Jaeger exporter configured")
            except Exception as e:
                logger.warning(f"Failed to configure Jaeger exporter: {e}")

        # OTLP exporter (if configured)
        if otlp_endpoint:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                exporters.append(otlp_exporter)
                logger.info("OTLP exporter configured")
            except Exception as e:
                logger.warning(f"Failed to configure OTLP exporter: {e}")

        # Add processors for each exporter
        for exporter in exporters:
            span_processor = BatchSpanProcessor(exporter)
            self.tracer_provider.add_span_processor(span_processor)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

        # Store exporters for cleanup
        self.exporters = exporters

    def get_tracer(self, name: str = None) -> trace.Tracer:
        """Get tracer instance"""
        if not self.enabled:
            return None
        return trace.get_tracer(name or __name__)

    def create_span(
        self,
        name: str,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ) -> trace.Span:
        """
        Create a new span

        Args:
            name: Span name
            kind: Span kind
            attributes: Span attributes

        Returns:
            Span instance
        """
        if not self.enabled:
            return None

        span = self.tracer.start_span(name, kind=kind)

        # Set standard attributes
        span.set_attribute(SpanAttributes.SERVICE_NAME, self.service_name)
        span.set_attribute(SpanAttributes.SERVICE_VERSION, self.service_version)

        # Set custom attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    def create_pipeline_span(
        self,
        pipeline_id: str,
        subreddits: List[str],
        limit: int,
        test_mode: bool = False
    ) -> trace.Span:
        """Create pipeline execution span"""
        if not self.enabled:
            return None

        span = self.create_span(
            f"pipeline-execute-{pipeline_id}",
            kind=trace.SpanKind.SERVER,
            attributes={
                "pipeline.id": pipeline_id,
                "pipeline.subreddits": ",".join(subreddits),
                "pipeline.limit": limit,
                "pipeline.test_mode": test_mode,
                "pipeline.stage": "execution"
            }
        )
        return span

    def create_stage_span(
        self,
        stage: str,
        pipeline_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> trace.Span:
        """Create pipeline stage span"""
        if not self.enabled:
            return None

        attributes = {
            "pipeline.id": pipeline_id,
            "pipeline.stage": stage
        }

        if metadata:
            attributes.update(metadata)

        span = self.create_span(
            f"pipeline-{stage}-{pipeline_id}",
            kind=trace.SpanKind.INTERNAL,
            attributes=attributes
        )
        return span

    def create_reddit_api_span(
        self,
        endpoint: str,
        subreddit: str,
        pipeline_id: str
    ) -> trace.Span:
        """Create Reddit API span"""
        if not self.enabled:
            return None

        span = self.create_span(
            f"reddit-api-{endpoint}-{subreddit}",
            kind=trace.SpanKind.CLIENT,
            attributes={
                "pipeline.id": pipeline_id,
                "api.service": "reddit",
                "api.endpoint": endpoint,
                "api.subreddit": subreddit,
                "api.operation": "fetch_submissions"
            }
        )
        return span

    def create_llm_span(
        self,
        model: str,
        operation: str,
        pipeline_id: str
    ) -> trace.Span:
        """Create LLM processing span"""
        if not self.enabled:
            return None

        span = self.create_span(
            f"llm-{operation}-{model}",
            kind=trace.SpanKind.CLIENT,
            attributes={
                "pipeline.id": pipeline_id,
                "llm.service": "openrouter",
                "llm.model": model,
                "llm.operation": operation
            }
        )
        return span

    def create_database_span(
        self,
        operation: str,
        table: str,
        pipeline_id: str
    ) -> trace.Span:
        """Create database operation span"""
        if not self.enabled:
            return None

        span = self.create_span(
            f"database-{operation}-{table}",
            kind=trace.SpanKind.CLIENT,
            attributes={
                "pipeline.id": pipeline_id,
                "db.service": "postgresql",
                "db.operation": operation,
                "db.table": table
            }
        )
        return span

    def add_error(self, span: trace.Span, error: Exception):
        """Add error information to span"""
        if not self.enabled or not span:
            return

        span.set_status(
            trace.Status(
                status_code=trace.StatusCode.ERROR,
                description=str(error)
            )
        )

        span.record_exception(
            exception=error,
            attributes={
                "error.type": type(error).__name__,
                "error.message": str(error)
            }
        )

    def finish_span(self, span: trace.Span, success: bool = True):
        """Finish span with status"""
        if not self.enabled or not span:
            return

        if success:
            span.set_status(trace.Status(trace.StatusCode.OK))
        else:
            span.set_status(
                trace.Status(
                    status_code=trace.StatusCode.ERROR,
                    description="Operation failed"
                )
            )

        span.end()

    def cleanup(self):
        """Cleanup tracer resources"""
        if self.enabled and hasattr(self, 'tracer_provider'):
            for exporter in self.exporters:
                try:
                    exporter.shutdown()
                except Exception as e:
                    logger.warning(f"Error shutting down exporter: {e}")


# Global tracer instance
_tracer: Optional[PipelineTracer] = None


def get_tracer() -> PipelineTracer:
    """Get global pipeline tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = PipelineTracer()
    return _tracer


def initialize_tracing(
    service_name: str = "pipeline-v3",
    service_version: str = "3.0.0",
    environment: str = "development",
    jaeger_endpoint: Optional[str] = None,
    otlp_endpoint: Optional[str] = None
) -> PipelineTracer:
    """
    Initialize global tracing

    Args:
        service_name: Service name
        service_version: Service version
        environment: Environment
        jaeger_endpoint: Jaeger endpoint
        otlp_endpoint: OTLP endpoint

    Returns:
        PipelineTracer instance
    """
    global _tracer
    _tracer = PipelineTracer(
        service_name=service_name,
        service_version=service_version,
        environment=environment,
        jaeger_endpoint=jaeger_endpoint,
        otlp_endpoint=otlp_endpoint
    )
    return _tracer


@contextmanager
def trace_pipeline_execution(
    pipeline_id: str,
    subreddits: List[str],
    limit: int,
    test_mode: bool = False
):
    """Context manager for tracing pipeline execution"""
    tracer = get_tracer()
    if not tracer.enabled:
        yield
        return

    span = tracer.create_pipeline_span(pipeline_id, subreddits, limit, test_mode)

    try:
        yield span
        tracer.finish_span(span, success=True)
    except Exception as e:
        tracer.add_error(span, e)
        tracer.finish_span(span, success=False)
        raise


@contextmanager
def trace_stage(stage: str, pipeline_id: str, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for tracing pipeline stages"""
    tracer = get_tracer()
    if not tracer.enabled:
        yield
        return

    span = tracer.create_stage_span(stage, pipeline_id, metadata)

    try:
        yield span
        tracer.finish_span(span, success=True)
    except Exception as e:
        tracer.add_error(span, e)
        tracer.finish_span(span, success=False)
        raise


@contextmanager
def trace_reddit_api(endpoint: str, subreddit: str, pipeline_id: str):
    """Context manager for tracing Reddit API calls"""
    tracer = get_tracer()
    if not tracer.enabled:
        yield
        return

    span = tracer.create_reddit_api_span(endpoint, subreddit, pipeline_id)

    try:
        yield span
        tracer.finish_span(span, success=True)
    except Exception as e:
        tracer.add_error(span, e)
        tracer.finish_span(span, success=False)
        raise


@contextmanager
def trace_llm_request(model: str, operation: str, pipeline_id: str):
    """Context manager for tracing LLM requests"""
    tracer = get_tracer()
    if not tracer.enabled:
        yield
        return

    span = tracer.create_llm_span(model, operation, pipeline_id)

    try:
        yield span
        tracer.finish_span(span, success=True)
    except Exception as e:
        tracer.add_error(span, e)
        tracer.finish_span(span, success=False)
        raise


@contextmanager
def trace_database_operation(operation: str, table: str, pipeline_id: str):
    """Context manager for tracing database operations"""
    tracer = get_tracer()
    if not tracer.enabled:
        yield
        return

    span = tracer.create_database_span(operation, table, pipeline_id)

    try:
        yield span
        tracer.finish_span(span, success=True)
    except Exception as e:
        tracer.add_error(span, e)
        tracer.finish_span(span, success=False)
        raise


def trace_function(operation: str, span_kind: trace.SpanKind = trace.SpanKind.INTERNAL):
    """Decorator for automatic function tracing"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer.enabled:
                return func(*args, **kwargs)

            # Create span
            span = tracer.create_span(
                name=f"{operation}-{func.__name__}",
                kind=span_kind,
                attributes={
                    "function.name": func.__name__,
                    "function.module": func.__module__
                }
            )

            try:
                result = func(*args, **kwargs)
                tracer.finish_span(span, success=True)
                return result
            except Exception as e:
                tracer.add_error(span, e)
                tracer.finish_span(span, success=False)
                raise

        return wrapper
    return decorator


def add_span_attributes(attributes: Dict[str, Any]):
    """Add attributes to current span"""
    if not OPENTELEMETRY_AVAILABLE:
        return

    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, value)


def set_span_error(error: Exception, message: Optional[str] = None):
    """Set current span as error"""
    if not OPENTELEMETRY_AVAILABLE:
        return

    current_span = trace.get_current_span()
    if current_span:
        if message:
            current_span.set_attribute("error.message", message)

        current_span.set_status(
            trace.Status(
                status_code=trace.StatusCode.ERROR,
                description=str(error)
            )
        )

        current_span.record_exception(error)