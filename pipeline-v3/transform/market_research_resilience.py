"""
MarketResearchAgent Resilience and Error Handling

Production-grade resilience patterns, error handling, and recovery mechanisms
for Jina Market Research Integration Phase 3.7
"""

import asyncio
import json
import logging
import time
import random
from typing import Dict, Any, List, Optional, Callable, Union, TypeVar, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import traceback
from functools import wraps

# Import monitoring components
from transform.market_research_monitoring import get_monitor, CircuitBreaker

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better handling"""
    NETWORK = "network"
    API = "api"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    TIMEOUT = "timeout"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class ErrorContext:
    """Context information for errors"""
    operation: str
    component: str
    app_concept_id: Optional[str] = None
    target_market: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """Detailed error information"""
    exception: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    traceback_str: Optional[str] = None
    recovery_action: Optional[str] = None
    should_retry: bool = True
    retry_delay_seconds: float = 1.0
    max_retries: int = 3

    def __post_init__(self):
        if self.traceback_str is None:
            self.traceback_str = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return {
            'exception_type': type(self.exception).__name__,
            'exception_message': str(self.exception),
            'category': self.category.value,
            'severity': self.severity.value,
            'context': {
                'operation': self.context.operation,
                'component': self.context.component,
                'app_concept_id': self.context.app_concept_id,
                'target_market': self.context.target_market,
                'request_id': self.context.request_id,
                'retry_count': self.context.retry_count,
                'additional_data': self.context.additional_data
            },
            'recovery_action': self.recovery_action,
            'should_retry': self.should_retry,
            'retry_delay_seconds': self.retry_delay_seconds,
            'max_retries': self.max_retries,
            'timestamp': self.context.timestamp.isoformat()
        }


class DeadLetterQueue:
    """Dead letter queue for failed requests"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.failed_requests: deque = deque(maxlen=max_size)
        self.retry_intervals = [300, 900, 3600, 14400]  # 5min, 15min, 1hr, 4hr

    async def add_failed_request(
        self,
        request_data: Dict[str, Any],
        error_info: ErrorInfo,
        retry_after: Optional[datetime] = None
    ):
        """Add failed request to DLQ"""
        if retry_after is None:
            # Calculate retry delay based on error category and retry count
            interval_index = min(error_info.context.retry_count, len(self.retry_intervals) - 1)
            retry_delay = self.retry_intervals[interval_index]
            retry_after = datetime.now() + timedelta(seconds=retry_delay)

        dlq_entry = {
            'request_data': request_data,
            'error_info': error_info.to_dict(),
            'retry_after': retry_after.isoformat(),
            'added_at': datetime.now().isoformat(),
            'retry_count': error_info.context.retry_count
        }

        self.failed_requests.append(dlq_entry)
        logger.warning(
            f"Added request to DLQ - Operation: {error_info.context.operation}, "
            f"Retry after: {retry_after}, Retry count: {error_info.context.retry_count}"
        )

    async def get_retryable_requests(self) -> List[Dict[str, Any]]:
        """Get requests that are ready for retry"""
        now = datetime.now()
        retryable = []

        for entry in list(self.failed_requests):
            retry_after = datetime.fromisoformat(entry['retry_after'])
            if now >= retry_after:
                retryable.append(entry)
                self.failed_requests.remove(entry)

        return retryable

    def get_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics"""
        if not self.failed_requests:
            return {'total_failed': 0, 'oldest_failure': None, 'newest_failure': None}

        failures = list(self.failed_requests)
        return {
            'total_failed': len(failures),
            'oldest_failure': failures[0]['added_at'] if failures else None,
            'newest_failure': failures[-1]['added_at'] if failures else None,
            'queue_usage_percent': (len(failures) / self.max_size) * 100
        }


class ErrorHandler:
    """Centralized error handling and classification"""

    def __init__(self):
        self.error_patterns = {
            # Network errors
            'connection': (ErrorCategory.NETWORK, ErrorSeverity.HIGH),
            'timeout': (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),
            'dns': (ErrorCategory.NETWORK, ErrorSeverity.HIGH),

            # API errors
            '401': (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            '403': (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            '429': (ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM),
            '500': (ErrorCategory.API, ErrorSeverity.HIGH),
            '502': (ErrorCategory.API, ErrorSeverity.MEDIUM),
            '503': (ErrorCategory.API, ErrorSeverity.MEDIUM),
            '504': (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),

            # Business logic errors
            'validation': (ErrorCategory.VALIDATION, ErrorSeverity.LOW),
            'not found': (ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.LOW),
            'permission': (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),

            # System errors
            'memory': (ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
            'disk': (ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
            'file': (ErrorCategory.SYSTEM, ErrorSeverity.HIGH)
        }

        # Custom error handlers
        self.custom_handlers = {}

    def classify_error(
        self,
        exception: Exception,
        operation: str,
        component: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> ErrorInfo:
        """Classify error and create ErrorInfo"""
        error_message = str(exception).lower()
        exception_type = type(exception).__name__.lower()

        # Default classification
        category = ErrorCategory.SYSTEM
        severity = ErrorSeverity.MEDIUM

        # Pattern matching for classification
        for pattern, (cat, sev) in self.error_patterns.items():
            if pattern in error_message or pattern in exception_type:
                category = cat
                severity = sev
                break

        # Create context
        context = ErrorContext(
            operation=operation,
            component=component,
            additional_data=context_data or {}
        )

        # Determine retry strategy based on error
        should_retry, retry_delay, max_retries = self._determine_retry_strategy(category, error_message)

        return ErrorInfo(
            exception=exception,
            category=category,
            severity=severity,
            context=context,
            should_retry=should_retry,
            retry_delay_seconds=retry_delay,
            max_retries=max_retries
        )

    def _determine_retry_strategy(
        self,
        category: ErrorCategory,
        error_message: str
    ) -> tuple[bool, float, int]:
        """Determine if error should be retried and with what strategy"""
        if category == ErrorCategory.RATE_LIMIT:
            return True, 60.0, 5  # 1 minute delay, 5 retries
        elif category == ErrorCategory.TIMEOUT:
            return True, 30.0, 3  # 30 second delay, 3 retries
        elif category == ErrorCategory.NETWORK:
            return True, 5.0, 3   # 5 second delay, 3 retries
        elif category == ErrorCategory.API:
            if '503' in error_message or '502' in error_message:
                return True, 10.0, 3  # Temporary server errors
            return False, 0.0, 0  # Don't retry client errors
        elif category == ErrorCategory.AUTHENTICATION:
            return False, 0.0, 0  # Don't retry auth errors
        elif category == ErrorCategory.VALIDATION:
            return False, 0.0, 0  # Don't retry validation errors
        else:
            return True, 1.0, 1   # Default retry strategy

    async def handle_error(self, error_info: ErrorInfo) -> Optional[str]:
        """Handle error and return recovery action"""
        # Log error with appropriate level
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)

        logger.log(
            log_level,
            f"Error in {error_info.context.component}.{error_info.context.operation}: "
            f"{error_info.category.value} - {str(error_info.exception)}"
        )

        # Check for custom handlers
        handler_key = f"{error_info.context.component}.{error_info.context.operation}"
        if handler_key in self.custom_handlers:
            recovery_action = await self.custom_handlers[handler_key](error_info)
            if recovery_action:
                return recovery_action

        # Default recovery actions
        if error_info.category == ErrorCategory.RATE_LIMIT:
            return "Implement exponential backoff and retry"
        elif error_info.category == ErrorCategory.TIMEOUT:
            return "Increase timeout and retry with circuit breaker"
        elif error_info.category == ErrorCategory.AUTHENTICATION:
            return "Refresh API credentials and re-authenticate"
        elif error_info.category == ErrorCategory.NETWORK:
            return "Check network connectivity and retry"
        elif error_info.category == ErrorCategory.CIRCUIT_BREAKER:
            return "Wait for circuit breaker to recover"
        else:
            return "Log error and continue with degraded functionality"

    def register_custom_handler(
        self,
        component_operation: str,
        handler: Callable[[ErrorInfo], Awaitable[str]]
    ):
        """Register custom error handler for specific component/operation"""
        self.custom_handlers[component_operation] = handler


class RetryPolicy:
    """Configurable retry policy with exponential backoff and jitter"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_factor: float = 0.1
    ):
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_factor = jitter_factor

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        # Exponential backoff
        delay = self.base_delay_seconds * (self.exponential_base ** (attempt - 1))

        # Apply maximum delay limit
        delay = min(delay, self.max_delay_seconds)

        # Add jitter to prevent thundering herd
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)  # Ensure non-negative delay

    def should_retry(self, attempt: int, error_info: ErrorInfo) -> bool:
        """Determine if retry should be attempted"""
        if attempt >= self.max_attempts:
            return False

        if not error_info.should_retry:
            return False

        # Respect max_retries from error info
        if error_info.context.retry_count >= error_info.max_retries:
            return False

        return True


class ResilienceManager:
    """
    Central resilience management for MarketResearchAgent

    Coordinates:
    - Retry policies
    - Circuit breakers
    - Dead letter queue
    - Error handling
    - Graceful degradation
    """

    def __init__(self):
        self.monitor = get_monitor()
        self.error_handler = ErrorHandler()
        self.dead_letter_queue = DeadLetterQueue()
        self.retry_policies = {}
        self.circuit_breakers = {}

        # Default retry policy
        self.default_retry_policy = RetryPolicy(
            max_attempts=3,
            base_delay_seconds=1.0,
            max_delay_seconds=30.0,
            exponential_base=2.0,
            jitter=True
        )

    def get_retry_policy(self, component: str, operation: str) -> RetryPolicy:
        """Get retry policy for component/operation"""
        key = f"{component}.{operation}"
        return self.retry_policies.get(key, self.default_retry_policy)

    def set_retry_policy(
        self,
        component: str,
        operation: str,
        policy: RetryPolicy
    ):
        """Set custom retry policy for component/operation"""
        key = f"{component}.{operation}"
        self.retry_policies[key] = policy

    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = self.monitor.get_circuit_breaker(service_name)
        return self.circuit_breakers[service_name]

    async def execute_with_resilience(
        self,
        func: Callable[..., Awaitable[T]],
        component: str,
        operation: str,
        *args,
        context_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> T:
        """
        Execute function with full resilience patterns

        Args:
            func: Async function to execute
            component: Component name for tracking
            operation: Operation name for tracking
            *args: Function arguments
            context_data: Additional context data
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries exhausted
        """
        retry_policy = self.get_retry_policy(component, operation)
        attempt = 0
        last_error = None

        while True:
            attempt += 1

            try:
                # Check circuit breaker if applicable
                circuit_breaker_name = f"{component}_api"
                circuit_breaker = self.get_circuit_breaker(circuit_breaker_name)

                if not circuit_breaker.can_execute():
                    error_info = ErrorInfo(
                        exception=Exception(f"Circuit breaker OPEN for {circuit_breaker_name}"),
                        category=ErrorCategory.CIRCUIT_BREAKER,
                        severity=ErrorSeverity.HIGH,
                        context=ErrorContext(
                            operation=operation,
                            component=component,
                            retry_count=attempt - 1,
                            additional_data=context_data or {}
                        ),
                        should_retry=False
                    )

                    recovery_action = await self.error_handler.handle_error(error_info)
                    logger.error(f"Circuit breaker open: {recovery_action}")
                    raise error_info.exception

                # Execute function
                result = await func(*args, **kwargs)

                # Record success
                circuit_breaker.record_success()
                return result

            except Exception as e:
                # Classify and handle error
                error_info = self.error_handler.classify_error(
                    e, operation, component, context_data
                )
                error_info.context.retry_count = attempt - 1

                # Record failure in circuit breaker
                circuit_breaker.record_failure()

                # Handle error
                recovery_action = await self.error_handler.handle_error(error_info)

                # Determine if retry should be attempted
                if not retry_policy.should_retry(attempt, error_info):
                    # Add to dead letter queue if appropriate
                    if error_info.should_retry and attempt <= error_info.max_retries:
                        await self.dead_letter_queue.add_failed_request(
                            request_data={
                                'args': args,
                                'kwargs': kwargs,
                                'context_data': context_data
                            },
                            error_info=error_info
                        )
                    raise e

                # Wait before retry
                delay = retry_policy.get_delay(attempt)
                logger.info(
                    f"Retrying {component}.{operation} in {delay:.2f}s "
                    f"(attempt {attempt}/{retry_policy.max_attempts}) - {recovery_action}"
                )
                await asyncio.sleep(delay)

                last_error = e

    def with_resilience(
        self,
        component: str,
        operation: str,
        retry_policy: Optional[RetryPolicy] = None
    ):
        """
        Decorator for adding resilience to functions

        Args:
            component: Component name
            operation: Operation name
            retry_policy: Custom retry policy (optional)
        """
        def decorator(func: Callable[..., Awaitable[T]]):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Use custom retry policy if provided
                if retry_policy:
                    original_policy = self.retry_policies.get(
                        f"{component}.{operation}", self.default_retry_policy
                    )
                    self.set_retry_policy(component, operation, retry_policy)

                try:
                    return await self.execute_with_resilience(
                        func, component, operation, *args, **kwargs
                    )
                finally:
                    # Restore original policy if we changed it
                    if retry_policy:
                        self.retry_policies[f"{component}.{operation}"] = original_policy

            return wrapper
        return decorator

    async def process_dead_letter_queue(self, processor_func: Callable):
        """Process retryable requests from dead letter queue"""
        retryable_requests = await self.dead_letter_queue.get_retryable_requests()

        if not retryable_requests:
            return

        logger.info(f"Processing {len(retryable_requests)} requests from DLQ")

        for entry in retryable_requests:
            try:
                request_data = entry['request_data']
                error_info_dict = entry['error_info']

                # Recreate ErrorInfo
                error_info = ErrorInfo(
                    exception=Exception(error_info_dict['exception_message']),
                    category=ErrorCategory(error_info_dict['category']),
                    severity=ErrorSeverity(error_info_dict['severity']),
                    context=ErrorContext(
                        operation=error_info_dict['context']['operation'],
                        component=error_info_dict['context']['component'],
                        retry_count=entry['retry_count']
                    )
                )

                # Process the request
                await processor_func(
                    request_data['args'],
                    request_data['kwargs'],
                    request_data.get('context_data')
                )

                logger.info(f"Successfully processed DLQ request for {error_info.context.operation}")

            except Exception as e:
                logger.error(f"Failed to process DLQ request: {e}")
                # Re-add to DLQ with increased retry count
                await self.dead_letter_queue.add_failed_request(
                    request_data=entry['request_data'],
                    error_info=error_info,
                    retry_after=datetime.now() + timedelta(hours=1)  # 1 hour delay
                )

    def get_resilience_stats(self) -> Dict[str, Any]:
        """Get comprehensive resilience statistics"""
        stats = {
            'circuit_breakers': {
                name: breaker.get_stats()
                for name, breaker in self.circuit_breakers.items()
            },
            'dead_letter_queue': self.dead_letter_queue.get_stats(),
            'retry_policies': {
                key: {
                    'max_attempts': policy.max_attempts,
                    'base_delay_seconds': policy.base_delay_seconds,
                    'max_delay_seconds': policy.max_delay_seconds
                }
                for key, policy in self.retry_policies.items()
            }
        }

        return stats


# Global resilience manager instance
_resilience_manager: Optional[ResilienceManager] = None


def get_resilience_manager() -> ResilienceManager:
    """Get or create global resilience manager"""
    global _resilience_manager
    if _resilience_manager is None:
        _resilience_manager = ResilienceManager()
    return _resilience_manager


# Convenience decorators
def resilient(
    component: str,
    operation: str,
    max_attempts: int = 3,
    base_delay_seconds: float = 1.0,
    max_delay_seconds: float = 30.0
):
    """
    Decorator for making functions resilient

    Args:
        component: Component name
        operation: Operation name
        max_attempts: Maximum retry attempts
        base_delay_seconds: Base delay between retries
        max_delay_seconds: Maximum delay between retries
    """
    def decorator(func: Callable[..., Awaitable[T]]):
        resilience_manager = get_resilience_manager()
        retry_policy = RetryPolicy(
            max_attempts=max_attempts,
            base_delay_seconds=base_delay_seconds,
            max_delay_seconds=max_delay_seconds
        )
        return resilience_manager.with_resilience(component, operation, retry_policy)(func)
    return decorator


def circuit_breaker_protected(service_name: str):
    """
    Decorator for circuit breaker protection
    """
    def decorator(func: Callable[..., Awaitable[T]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            resilience_manager = get_resilience_manager()
            circuit_breaker = resilience_manager.get_circuit_breaker(service_name)

            if not circuit_breaker.can_execute():
                raise Exception(f"Circuit breaker OPEN for {service_name}")

            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise e

        return wrapper
    return decorator