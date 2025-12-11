"""
Loader Factory Pattern Implementation
Provides clean abstraction and decoupling for database loaders following SOLID principles.
"""

from abc import ABC, abstractmethod
from typing import Union
import logging

from models.analysis import Opportunity
from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class BaseLoader(ABC):
    """
    Abstract base class defining the interface for all database loaders.

    This establishes the contract that all loaders must follow, enabling
    dependency injection and clean separation of concerns.
    """

    @abstractmethod
    def save_opportunity(self, opportunity: Opportunity) -> bool:
        """
        Save an Opportunity to the database.

        Args:
            opportunity: The Opportunity instance to save

        Returns:
            True if saved successfully, False if duplicate was skipped

        Raises:
            ValueError: If opportunity data is invalid
            RuntimeError: If database operation fails
        """
        pass

    @abstractmethod
    def save_analysis(self, analysis) -> bool:
        """
        Convert AnalysisResult to Opportunity and save it.

        Args:
            analysis: AnalysisResult object to convert and save

        Returns:
            True if saved successfully, False if duplicate was skipped

        Raises:
            ValueError: If analysis data is invalid
            RuntimeError: If database operation fails
        """
        pass

    def close(self):
        """
        Close any resources (connections, etc.).

        Default implementation does nothing - concrete classes can override
        if they need to clean up resources.
        """
        pass


def get_loader(settings: Settings = None, loader_override: BaseLoader = None) -> BaseLoader:
    """
    Factory function to create and return the appropriate loader instance.

    This factory encapsulates the creation logic and provides a single point
    of configuration for loader selection, following the Factory Pattern.

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
        # Determine which loader to instantiate based on feature flag
        if settings.use_sqlmodel_loader:
            logger.info("Factory creating SQLModel loader")
            from load.sqlmodel_loader import SQLModelLoader
            return SQLModelLoader(settings)
        else:
            logger.info("Factory creating PostgreSQL loader")
            from load.postgres_loader import PostgresLoader
            return PostgresLoader(settings)

    except ImportError as e:
        logger.error(f"Failed to import loader module: {e}")
        raise RuntimeError(f"Loader module import failed: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize loader: {e}")
        raise RuntimeError(f"Loader initialization failed: {e}")


class LoaderType:
    """
    Enumeration of available loader types for type safety.

    This provides compile-time safety and clearer intent when specifying
    loader types in configuration or tests.
    """
    POSTGRES = "postgres"
    SQLMODEL = "sqlmodel"

    @classmethod
    def all_types(cls) -> list[str]:
        """Get all available loader types"""
        return [cls.POSTGRES, cls.SQLMODEL]

    @classmethod
    def is_valid(cls, loader_type: str) -> bool:
        """Check if a loader type is valid"""
        return loader_type in cls.all_types()


def create_loader_by_type(loader_type: str, settings: Settings = None) -> BaseLoader:
    """
    Create a loader by type string instead of feature flag.

    This method provides an alternative way to specify which loader to use,
    useful for configuration systems that prefer explicit type specification.

    Args:
        loader_type: The type of loader to create ("postgres" or "sqlmodel")
        settings: Application settings (uses global settings if None)

    Returns:
        An instance of the requested loader type

    Raises:
        ValueError: If loader_type is invalid
        RuntimeError: If loader creation fails
    """
    if not LoaderType.is_valid(loader_type):
        raise ValueError(f"Invalid loader type: {loader_type}. Valid types: {LoaderType.all_types()}")

    settings = settings or get_settings()

    try:
        if loader_type == LoaderType.SQLMODEL:
            logger.info(f"Creating SQLModel loader by type request")
            from load.sqlmodel_loader import SQLModelLoader
            return SQLModelLoader(settings)
        else:  # POSTGRES
            logger.info(f"Creating PostgreSQL loader by type request")
            from load.postgres_loader import PostgresLoader
            return PostgresLoader(settings)

    except ImportError as e:
        logger.error(f"Failed to import loader module: {e}")
        raise RuntimeError(f"Loader module import failed: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize loader: {e}")
        raise RuntimeError(f"Loader initialization failed: {e}")