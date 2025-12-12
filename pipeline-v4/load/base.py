"""
Base Loader Interface
Defines the abstract interface that all database loaders must implement.
"""

from abc import ABC, abstractmethod


class BaseLoader(ABC):
    """
    Abstract base class defining the interface for all database loaders.

    This establishes the contract that all loaders must follow, enabling
    dependency injection and clean separation of concerns.
    """

    @abstractmethod
    def save_opportunity(self, opportunity) -> bool:
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
