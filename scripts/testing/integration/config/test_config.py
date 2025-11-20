#!/usr/bin/env python3
"""
Test Configuration Loader

Loads configuration from JSON files for integration testing.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Get config directory
CONFIG_DIR = Path(__file__).parent


def load_service_config() -> Dict[str, Any]:
    """Load service configuration from service_config.json."""
    config_path = CONFIG_DIR / "service_config.json"
    with open(config_path, "r") as f:
        return json.load(f)


def load_submissions_config(config_file: str) -> Dict[str, Any]:
    """
    Load submission configuration from JSON file.

    Args:
        config_file: Name of config file (e.g., "submissions_single.json")

    Returns:
        Dictionary with submission configuration
    """
    config_path = CONFIG_DIR / config_file
    with open(config_path, "r") as f:
        return json.load(f)


def get_submission_ids(config_file: str) -> List[str]:
    """
    Get list of submission IDs from config file.

    Args:
        config_file: Name of config file

    Returns:
        List of submission IDs
    """
    config = load_submissions_config(config_file)
    return [sub["submission_id"] for sub in config.get("submissions", [])]


def is_service_enabled(service_name: str) -> bool:
    """
    Check if a service is enabled in configuration.

    Args:
        service_name: Name of service (profiler, opportunity, monetization, trust, market_validation)

    Returns:
        True if service is enabled
    """
    config = load_service_config()
    service_config = config.get("services", {}).get(service_name, {})
    return service_config.get("enabled", False)


def get_service_config(service_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific service.

    Args:
        service_name: Name of service

    Returns:
        Service configuration dictionary
    """
    config = load_service_config()
    return config.get("services", {}).get(service_name, {})


def get_observability_config() -> Dict[str, Any]:
    """Get observability configuration."""
    config = load_service_config()
    return config.get("observability", {})


def is_dlt_enabled() -> bool:
    """Check if DLT storage is enabled."""
    config = load_service_config()
    return config.get("storage", {}).get("dlt_enabled", False)


# Export commonly used configs
SERVICE_CONFIG = load_service_config()
OBSERVABILITY_CONFIG = get_observability_config()
