"""
RedditHarbor Core Utilities Package

Provides shared utilities for logging, configuration, and common operations
across the RedditHarbor platform.

Author: Data Engineering Team
Date: 2025-11-18
Version: 1.0.0
"""

from .http_client_config import get_configured_httpx_client, initialize_http_clients
from .id_resolver import (
    REDDITHARBOR_NAMESPACE,
    ResolutionResult,
    extract_reddit_id_from_url,
    generate_deterministic_uuid,
    is_valid_uuid,
    resolve_submission_id,
)
from .logging import LoggerMixin, get_logger, setup_logging

__all__ = [
    'REDDITHARBOR_NAMESPACE',
    'LoggerMixin',
    'ResolutionResult',
    'extract_reddit_id_from_url',
    'generate_deterministic_uuid',
    'get_configured_httpx_client',
    'get_logger',
    'initialize_http_clients',
    'is_valid_uuid',
    'resolve_submission_id',
    'setup_logging',
]
