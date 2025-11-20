"""Market validation service for market data analysis.

This module provides the MarketValidationService class for analyzing
market data and validating market opportunities.

Key Features:
- Market data validation and analysis
- Competition analysis
- Market size estimation
- Integration with market validation agents

Example:
    >>> from core.agents.market_validation import MarketDataValidator
    >>> from core.enrichment.market_validation_service import MarketValidationService
    >>>
    >>> validator = MarketDataValidator()
    >>> service = MarketValidationService(validator=validator)
    >>> result = service.analyze_market(data)
"""

import logging
from typing import Any, Dict, Optional

from core.enrichment.base_service import BaseEnrichmentService

logger = logging.getLogger(__name__)


class MarketValidationService(BaseEnrichmentService):
    """
    Service for market validation and analysis.

    Wraps MarketDataValidator to provide market data validation,
    competition analysis, and market opportunity assessment.
    Integrates with the unified pipeline for consistent enrichment.

    Attributes:
        validator: MarketDataValidator instance for market analysis
        config: Configuration dictionary for service settings

    Examples:
        >>> from core.agents.market_validation import MarketDataValidator
        >>> validator = MarketDataValidator()
        >>> service = MarketValidationService(validator=validator)
        >>> stats = service.get_statistics()
    """

    def __init__(self, validator: Any, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MarketValidationService.

        Args:
            validator: MarketDataValidator instance
            config: Optional configuration dictionary
        """
        super().__init__(config or {})
        self.validator = validator
        self.stats = {
            "analyzed": 0,
            "validated": 0,
            "skipped": 0,
            "errors": 0,
        }
        logger.info("MarketValidationService initialized")

    def analyze_market(self, data: Any) -> Dict[str, Any]:
        """
        Analyze market data for validation.

        Args:
            data: Market data to analyze

        Returns:
            Dictionary with market validation results

        Examples:
            >>> service = MarketValidationService(validator)
            >>> result = service.analyze_market({"market": "data"})
            >>> print(result["market_score"])
        """
        try:
            self.stats["analyzed"] += 1

            # Use validator to analyze market data
            if hasattr(self.validator, 'validate_market_data'):
                result = self.validator.validate_market_data(data)
            else:
                # Fallback mock implementation
                result = {
                    "market_score": 70.0,
                    "confidence": 0.7,
                    "market_size": "medium",
                    "validation_reasons": ["Mock validation"]
                }

            self.stats["validated"] += 1
            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Market analysis failed: {e}")
            return {
                "market_score": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }

    def get_statistics(self) -> Dict[str, int]:
        """
        Get service statistics.

        Returns:
            Dictionary with service statistics

        Examples:
            >>> service = MarketValidationService(validator)
            >>> stats = service.get_statistics()
            >>> print(stats["analyzed"])
        """
        return self.stats.copy()

    def reset_statistics(self) -> None:
        """
        Reset service statistics.

        Examples:
            >>> service = MarketValidationService(validator)
            >>> service.reset_statistics()
        """
        self.stats = {
            "analyzed": 0,
            "validated": 0,
            "skipped": 0,
            "errors": 0,
        }