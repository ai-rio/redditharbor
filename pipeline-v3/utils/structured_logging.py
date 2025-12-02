"""
Structured logging with correlation IDs for Pipeline v3
"""

import json
import logging
import uuid
import time
import threading
import traceback
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from contextlib import contextmanager
from functools import wraps

from config import get_settings


class CorrelationContext:
    """Thread-safe context for correlation IDs and pipeline execution metadata"""

    def __init__(self):
        self._local = threading.local()

    def get_correlation_id(self) -> str:
        """Get current correlation ID, create one if none exists"""
        if not hasattr(self._local, 'correlation_id'):
            self._local.correlation_id = str(uuid.uuid4())
        return self._local.correlation_id

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID"""
        self._local.correlation_id = correlation_id

    def get_pipeline_run_id(self) -> Optional[str]:
        """Get current pipeline run ID"""
        return getattr(self._local, 'pipeline_run_id', None)

    def set_pipeline_run_id(self, run_id: str) -> None:
        """Set pipeline run ID"""
        self._local.pipeline_run_id = run_id

    def get_stage_context(self) -> Dict[str, Any]:
        """Get current stage context"""
        return getattr(self._local, 'stage_context', {})

    def set_stage_context(self, context: Dict[str, Any]) -> None:
        """Set stage context"""
        self._local.stage_context = context

    def clear(self) -> None:
        """Clear all context"""
        self._local.correlation_id = str(uuid.uuid4())
        self._local.pipeline_run_id = None
        self._local.stage_context = {}

    def get_all_context(self) -> Dict[str, Any]:
        """Get all context information"""
        return {
            'correlation_id': self.get_correlation_id(),
            'pipeline_run_id': self.get_pipeline_run_id(),
            'stage_context': self.get_stage_context()
        }


# Global correlation context
_correlation_context = CorrelationContext()


class StructuredLogger:
    """
    Structured logger with correlation IDs and consistent JSON formatting
    """

    def __init__(self, name: str, service: str = "pipeline-v3"):
        """
        Initialize structured logger

        Args:
            name: Logger name
            service: Service name for log entries
        """
        self.logger = logging.getLogger(name)
        self.service = service
        self.settings = get_settings()

    def _create_log_entry(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create structured log entry"""
        context = _correlation_context.get_all_context()

        log_entry = {
            '@timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level.upper(),
            'message': message,
            'service': self.service,
            'environment': getattr(self.settings, 'environment', 'development'),
            **context
        }

        # Add extra fields
        if extra:
            log_entry.update(extra)

        return log_entry

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log message with structured format"""
        if not kwargs.get('structured', True):
            # Use standard logging for non-structured messages
            getattr(self.logger, level.lower())(message)
            return

        log_entry = self._create_log_entry(level, message, kwargs)
        json_message = json.dumps(log_entry, default=str)

        # Log using standard Python logging
        getattr(self.logger, level.lower())(json_message)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self._log('debug', message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self._log('info', message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self._log('warning', message, **kwargs)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with optional exception details"""
        if error:
            kwargs.update({
                'error': {
                    'type': type(error).__name__,
                    'message': str(error),
                    'stacktrace': traceback.format_exc()
                }
            })

        self._log('error', message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        self._log('critical', message, **kwargs)

    def pipeline_start(self, config: Dict[str, Any]) -> None:
        """Log pipeline start"""
        self.info(
            "Pipeline started",
            event_type='pipeline_start',
            config=config,
            **_correlation_context.get_stage_context()
        )

    def pipeline_complete(self, results: Dict[str, Any]) -> None:
        """Log pipeline completion"""
        self.info(
            "Pipeline completed",
            event_type='pipeline_complete',
            results=results,
            **_correlation_context.get_stage_context()
        )

    def stage_start(self, stage: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log stage start"""
        stage_context = {'stage': stage}
        if metadata:
            stage_context.update(metadata)

        _correlation_context.set_stage_context(stage_context)

        self.info(
            f"Stage started: {stage}",
            event_type='stage_start',
            stage=stage,
            metadata=metadata or {}
        )

    def stage_complete(self, stage: str, duration: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log stage completion"""
        stage_context = _correlation_context.get_stage_context()
        stage_context.update({
            'stage': stage,
            'duration': duration,
            'metadata': metadata or {}
        })

        self.info(
            f"Stage completed: {stage}",
            event_type='stage_complete',
            stage=stage,
            duration=duration,
            metadata=metadata or {}
        )

    def reddit_api_call(
        self,
        endpoint: str,
        subreddit: str,
        duration: float,
        status: str = 'success',
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log Reddit API call"""
        self.info(
            f"Reddit API call: {endpoint}",
            event_type='reddit_api_call',
            endpoint=endpoint,
            subreddit=subreddit,
            duration=duration,
            status=status,
            metadata=metadata or {}
        )

    def llm_request(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration: float,
        status: str = 'success'
    ) -> None:
        """Log LLM request"""
        self.info(
            f"LLM request: {model}",
            event_type='llm_request',
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration=duration,
            status=status
        )

    def database_operation(
        self,
        operation: str,
        table: str,
        records_affected: int,
        duration: float,
        status: str = 'success'
    ) -> None:
        """Log database operation"""
        self.info(
            f"Database operation: {operation}",
            event_type='database_operation',
            operation=operation,
            table=table,
            records_affected=records_affected,
            duration=duration,
            status=status
        )

    def quality_metrics(
        self,
        validation_rate: float,
        average_score: float,
        high_score_rate: float,
        trust_distribution: Dict[str, int]
    ) -> None:
        """Log quality metrics"""
        self.info(
            "Quality metrics recorded",
            event_type='quality_metrics',
            validation_rate=validation_rate,
            average_score=average_score,
            high_score_rate=high_score_rate,
            trust_distribution=trust_distribution
        )

    def error_occurred(
        self,
        stage: str,
        error_type: str,
        error_message: str,
        recoverable: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log error occurrence"""
        self.error(
            f"Error in {stage}: {error_type}",
            event_type='pipeline_error',
            stage=stage,
            error_type=error_type,
            error_message=error_message,
            recoverable=recoverable,
            metadata=metadata or {}
        )


def get_structured_logger(name: str) -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger(name)


@contextmanager
def pipeline_context(run_id: Optional[str] = None):
    """Context manager for pipeline execution with correlation IDs"""
    if run_id:
        _correlation_context.set_pipeline_run_id(run_id)
    else:
        _correlation_context.set_pipeline_run_id(str(uuid.uuid4()))

    correlation_id = _correlation_context.get_correlation_id()

    try:
        yield correlation_id
    finally:
        _correlation_context.clear()


@contextmanager
def stage_context(stage: str, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for stage execution with structured logging"""
    stage_metadata = {'stage': stage}
    if metadata:
        stage_metadata.update(metadata)

    start_time = time.time()

    # Log stage start
    logger = get_structured_logger(__name__)
    logger.stage_start(stage, stage_metadata)

    try:
        yield
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Stage failed: {stage}",
            error=e,
            event_type='stage_error',
            stage=stage,
            duration=duration
        )
        raise
    else:
        duration = time.time() - start_time
        logger.stage_complete(stage, duration, stage_metadata)


def log_execution(stage: str, include_args: bool = False):
    """Decorator for automatic execution logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_structured_logger(func.__module__)

            start_time = time.time()
            metadata = {
                'function': func.__name__,
                'module': func.__module__
            }

            if include_args:
                # Only include safe args (exclude passwords, keys, etc.)
                safe_args = {}
                for k, v in kwargs.items():
                    if any(sensitive in k.lower() for sensitive in ['password', 'key', 'secret', 'token']):
                        safe_args[k] = '[REDACTED]'
                    else:
                        safe_args[k] = str(v)[:100]  # Limit length
                metadata['args'] = safe_args

            with stage_context(stage, metadata):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    logger.error(f"Function execution failed: {func.__name__}", error=e)
                    raise

        return wrapper
    return decorator


def get_correlation_id() -> str:
    """Get current correlation ID"""
    return _correlation_context.get_correlation_id()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID"""
    _correlation_context.set_correlation_id(correlation_id)


def setup_structured_logging():
    """Set up structured logging for the application"""
    settings = get_settings()

    # Create structured logger formatter
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            # Try to parse as JSON, fallback to standard formatting
            try:
                # If it's already a structured log entry, use as-is
                json.loads(record.getMessage())
                return record.getMessage()
            except (json.JSONDecodeError, AttributeError):
                # Standard log message, format with timestamp
                return f"{datetime.utcnow().isoformat()}Z - {record.name} - {record.levelname} - {record.getMessage()}"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # File handler
    try:
        from pathlib import Path
        log_path = settings.project_root / "logs"
        log_path.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_path / "structured.log")
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to set up file logging: {e}")

    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('prawcore').setLevel(logging.WARNING)

    logging.getLogger("structured_logging").info("Structured logging initialized")