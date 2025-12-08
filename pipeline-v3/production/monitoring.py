"""
Production monitoring module

Provides PrometheusMetrics class as an alias for the monitoring functionality
in transform.market_research_monitoring.
"""

from transform.market_research_monitoring import PrometheusMetricsCollector

# Create the expected PrometheusMetrics class as an alias
PrometheusMetrics = PrometheusMetricsCollector

__all__ = ['PrometheusMetrics']
