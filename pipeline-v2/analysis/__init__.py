#!/usr/bin/env python3
"""
Pipeline-v2 Analysis Module

Thin wrapper modules for AI agents extracted from core/agents/ to pipeline-v2.
Provides clean interfaces while maintaining full backward compatibility.

Modules:
- opportunity: Wrapper for OpportunityAnalyzerAgent
- monetization: Wrapper for MonetizationAgnoAnalyzer
- profiler: Wrapper for EnhancedLLMProfiler
"""

from .opportunity import OpportunityAnalyzer
from .monetization import MonetizationAnalyzer
from .profiler import AppProfiler

__all__ = [
    "OpportunityAnalyzer",
    "MonetizationAnalyzer",
    "AppProfiler"
]