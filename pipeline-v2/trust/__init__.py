#!/usr/bin/env python3
"""
Pipeline-v2 Trust Validation Module

Extracted trust validation logic from scripts/dlt/dlt_trust_pipeline.py and core/trust/
to provide a clean, dedicated trust validation system for the pipeline-v2 architecture.

This module implements:
- 6-dimensional trust scoring algorithm
- Badge system (GOLD, SILVER, BRONZE, BASIC + secondary badges)
- TrustIndicators dataclass with 20+ trust fields
- Database integration patterns for app_opportunities table
- Configuration constants and thresholds

Main Components:
- TrustValidator: Main trust validation class
- TrustIndicators: Dataclass for trust metrics
- TrustLevel: Enum for trust levels
- TrustBadge: Enum for badge types

Integration Strategy:
- NEW STRATEGY: Use OpportunityAnalyzer from ..analysis (relative import)
- Direct core imports for other agents (MonetizationAgnoAnalyzer, EnhancedLLMProfiler)
- Backward compatibility with existing TrustLayerValidator interface
"""

from .validator import (
    TrustValidator,
    TrustIndicators,
    TrustLevel,
    TrustBadge,
    TrustValidationConfig,
    TrustWeights,
    create_trust_validator,
    validate_opportunity_trust
)

__all__ = [
    "TrustValidator",
    "TrustIndicators",
    "TrustLevel",
    "TrustBadge",
    "TrustValidationConfig",
    "TrustWeights",
    "create_trust_validator",
    "validate_opportunity_trust"
]