"""
Performance monitoring and metrics collection for Pipeline v3
"""

import time
import logging
import functools
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation"""
    operation_name: str
    duration: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


class PerformanceMonitor:
    """
    Performance monitoring with metrics collection and analysis
    Thread-safe for concurrent operations
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize performance monitor

        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self._metrics: deque = deque(maxlen=max_history)
        self._operation_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0,
            'success_count': 0,
            'error_count': 0
        })
        self._lock = threading.Lock()

    def record_metric(
        self,
        operation_name: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Record a performance metric

        Args:
            operation_name: Name of the operation
            duration: Duration in seconds
            metadata: Optional metadata about the operation
            success: Whether the operation was successful
            error_message: Error message if operation failed
        """
        metric = PerformanceMetrics(
            operation_name=operation_name,
            duration=duration,
            timestamp=time.time(),
            metadata=metadata or {},
            success=success,
            error_message=error_message
        )

        with self._lock:
            self._metrics.append(metric)
            self._update_operation_stats(metric)

    def _update_operation_stats(self, metric: PerformanceMetrics) -> None:
        """Update operation statistics"""
        stats = self._operation_stats[metric.operation_name]
        stats['count'] += 1
        stats['total_duration'] += metric.duration
        stats['min_duration'] = min(stats['min_duration'], metric.duration)
        stats['max_duration'] = max(stats['max_duration'], metric.duration)

        if metric.success:
            stats['success_count'] += 1
        else:
            stats['error_count'] += 1

    def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific operation

        Args:
            operation_name: Name of the operation

        Returns:
            Dictionary with operation statistics
        """
        with self._lock:
            stats = self._operation_stats[operation_name].copy()

        if stats['count'] > 0:
            stats['avg_duration'] = stats['total_duration'] / stats['count']
            stats['success_rate'] = stats['success_count'] / stats['count']
            stats['error_rate'] = stats['error_count'] / stats['count']
        else:
            stats['avg_duration'] = 0.0
            stats['success_rate'] = 0.0
            stats['error_rate'] = 0.0

        return stats

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations"""
        with self._lock:
            return {
                op_name: self.get_operation_stats(op_name)
                for op_name in self._operation_stats.keys()
            }

    def get_recent_metrics(self, count: int = 100, operation_name: Optional[str] = None) -> list[PerformanceMetrics]:
        """
        Get recent metrics

        Args:
            count: Number of recent metrics to return
            operation_name: Filter by operation name (optional)

        Returns:
            List of recent metrics
        """
        with self._lock:
            metrics = list(self._metrics)
            if operation_name:
                metrics = [m for m in metrics if m.operation_name == operation_name]

        return metrics[-count:] if count > 0 else metrics

    def clear_metrics(self) -> None:
        """Clear all stored metrics"""
        with self._lock:
            self._metrics.clear()
            self._operation_stats.clear()

    def timer(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Decorator to time function execution

        Args:
            operation_name: Name for the operation
            metadata: Optional metadata to include

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_message = None

                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_message = str(e)
                    raise
                finally:
                    duration = time.time() - start_time
                    self.record_metric(
                        operation_name=operation_name,
                        duration=duration,
                        metadata=metadata,
                        success=success,
                        error_message=error_message
                    )

            return wrapper
        return decorator

    def context_timer(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for timing operations

        Args:
            operation_name: Name for the operation
            metadata: Optional metadata to include

        Returns:
            Context manager
        """
        class TimerContext:
            def __init__(self, monitor, op_name, meta):
                self.monitor = monitor
                self.operation_name = op_name
                self.metadata = meta
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                success = exc_type is None
                error_message = str(exc_val) if exc_val else None

                self.monitor.record_metric(
                    operation_name=self.operation_name,
                    duration=duration,
                    metadata=self.metadata,
                    success=success,
                    error_message=error_message
                )

        return TimerContext(self, operation_name, metadata)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of overall performance metrics"""
        with self._lock:
            all_stats = self.get_all_stats()
            total_operations = sum(stats['count'] for stats in all_stats.values())
            total_duration = sum(stats['total_duration'] for stats in all_stats.values())
            total_errors = sum(stats['error_count'] for stats in all_stats.values())

        return {
            'total_operations': total_operations,
            'total_duration': total_duration,
            'average_duration': total_duration / total_operations if total_operations > 0 else 0,
            'overall_success_rate': (total_operations - total_errors) / total_operations if total_operations > 0 else 0,
            'total_errors': total_errors,
            'operations_count': len(all_stats),
            'operations': all_stats
        }


# Global performance monitor instance
_performance_monitor = None
_monitor_lock = threading.Lock()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def monitor_performance(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Decorator for monitoring function performance"""
    return get_performance_monitor().timer(operation_name, metadata)


def performance_timer(operation_name: str, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for timing operations"""
    return get_performance_monitor().context_timer(operation_name, metadata)