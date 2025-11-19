"""
RedditHarbor Logging Utilities
Provides standardized logging configuration for all RedditHarbor components.

Author: Data Engineering Team
Date: 2025-11-18
Version: 1.0.0
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(
    name: str | None = None,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: str = "logs"
) -> logging.Logger:
    """
    Set up standardized logging configuration.

    Args:
        name: Logger name (defaults to calling module name)
        level: Logging level (default: INFO)
        log_to_file: Whether to log to file (default: True)
        log_dir: Directory for log files (default: "logs")

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        # Ensure log directory exists
        Path(log_dir).mkdir(exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = Path(log_dir) / f"redditharbor_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with standard configuration.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return setup_logging(name)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return get_logger(self.__class__.__module__ + '.' + self.__class__.__name__)
