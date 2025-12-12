"""
Loader Factory Pattern Implementation
Provides clean abstraction and decoupling for database loaders following SOLID principles.
"""

import logging

from config.settings import Settings, get_settings
from load.base import BaseLoader

logger = logging.getLogger(__name__)


def get_loader(
    settings: Settings = None, loader_override: BaseLoader = None
) -> BaseLoader:
    """
    Factory function to create and return the unified OpportunityLoader instance.

    This factory provides dependency injection support for testing while
    defaulting to the production OpportunityLoader implementation.

    Args:
        settings: Application settings (uses global settings if None)
        loader_override: Optional loader instance for dependency injection/testing

    Returns:
        An instance of a BaseLoader implementation

    Raises:
        RuntimeError: If loader initialization fails
    """
    # Allow dependency injection for testing
    if loader_override is not None:
        logger.debug("Using injected loader instance")
        return loader_override

    # Use provided settings or get global settings
    settings = settings or get_settings()

    try:
        logger.info("Factory creating OpportunityLoader")
        from load.loader import OpportunityLoader

        return OpportunityLoader(settings)

    except ImportError as e:
        logger.error(f"Failed to import loader module: {e}")
        raise RuntimeError(f"Loader module import failed: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize loader: {e}")
        raise RuntimeError(f"Loader initialization failed: {e}")
