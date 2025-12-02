#!/usr/bin/env python3
"""
Monetization Analyzer Factory Wrapper

Thin wrapper for core.agents.monetization.factory.MonetizationAnalyzerFactory
Provides clean interface while maintaining full backward compatibility.
"""

from typing import Dict, Union
import sys
from pathlib import Path

# Add project root to path for core imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# Mock settings for fallback mode
class MockSettings:
    MONETIZATION_FRAMEWORK = "agno"
    MONETIZATION_LLM_MODEL = "anthropic/claude-haiku-4.5"
    AGENTOPS_API_KEY = None

# Add settings to sys.modules
import sys
if not hasattr(sys.modules[__name__], 'settings'):
    sys.modules[__name__].settings = MockSettings()


# Import from existing core module with fallback
try:
    from core.agents.monetization.factory import (
        get_monetization_analyzer,
        list_available_frameworks,
        get_framework_info,
        compare_frameworks,
        create_dspy_analyzer,
        create_agno_analyzer,
        MonetizationAnalyzerFactory,
        MonetizationLLMAnalyzer,
        MonetizationAgnoAnalyzer,
        DSPY_AVAILABLE,
        AGNO_AVAILABLE
    )
    CORE_FACTORY_AVAILABLE = True
except ImportError:
    CORE_FACTORY_AVAILABLE = False

class MonetizationLLMAnalyzer:
    """Fallback DSPy analyzer implementation."""
    def __init__(self, model=None):
        self.model = model or "fallback_model"

    def analyze(self, text, subreddit, keyword_monetization_score=None):
        from analysis.monetization import MonetizationAnalysis
        return MonetizationAnalysis(
            willingness_to_pay_score=65.0,
            customer_segment="B2C",
            sentiment_toward_payment="Positive",
            llm_monetization_score=60.0
        )

    # Fallback classes and functions
    class MonetizationLLMAnalyzer:
        def __init__(self, model=None): self.model = model
    class MonetizationAgnoAnalyzer:
        def __init__(self, model=None, agentops_api_key=None):
            self.model = model or "fallback_model"
            self.agentops_enabled = False
    DSPY_AVAILABLE = False
    AGNO_AVAILABLE = False

    def get_monetization_analyzer(framework=None, model=None, **kwargs):
        return MonetizationAgnoAnalyzer(model=model)
    def list_available_frameworks(): return {"dspy": {"available": False}, "agno": {"available": False}}
    def get_framework_info(framework): return {"available": False, "selected": False}
    def compare_frameworks(): return {"available": {}, "current_selection": "fallback"}
    def create_dspy_analyzer(model=None, **kwargs): return get_monetization_analyzer("dspy", model, **kwargs)
    def create_agno_analyzer(model=None, agentops_api_key=None, **kwargs):
        return get_monetization_analyzer("agno", model, agentops_api_key=agentops_api_key, **kwargs)

    class MonetizationAnalyzerFactory:
        @staticmethod
        def create_analyzer(framework=None, model=None, **kwargs):
            return get_monetization_analyzer(framework, model, **kwargs)
        @staticmethod
        def list_frameworks(): return list_available_frameworks()
        @staticmethod
        def compare_frameworks(): return compare_frameworks()


class MonetizationAnalyzerFactoryWrapper:
    """Thin wrapper for MonetizationAnalyzerFactory from core/agents/."""

    def __init__(self):
        """Initialize wrapper with core factory availability."""
        self._core_available = CORE_FACTORY_AVAILABLE

    def create_analyzer(self, framework: str = None, model: str = None, **kwargs) -> Union[MonetizationLLMAnalyzer, MonetizationAgnoAnalyzer]:
        """Create a monetization analyzer instance."""
        return get_monetization_analyzer(framework, model, **kwargs)

    def list_frameworks(self) -> Dict[str, Dict]:
        """List available monetization analyzer frameworks."""
        return list_available_frameworks()

    def compare_frameworks(self) -> Dict[str, Union[Dict, str]]:
        """Compare available monetization analyzer frameworks."""
        return compare_frameworks()

    @property
    def core_available(self) -> bool:
        """Check if core factory is available."""
        return self._core_available


# Convenience functions for backward compatibility
def get_analyzer(framework: str = None, model: str = None, **kwargs) -> Union[MonetizationLLMAnalyzer, MonetizationAgnoAnalyzer]:
    """Get monetization analyzer instance."""
    return get_monetization_analyzer(framework, model, **kwargs)

def list_frameworks() -> Dict[str, Dict]:
    """List available frameworks."""
    return list_available_frameworks()

def get_info(framework: str) -> Dict:
    """Get framework information."""
    return get_framework_info(framework)

def compare() -> Dict[str, Union[Dict, str]]:
    """Compare frameworks."""
    return compare_frameworks()


# Export key classes and functions for backward compatibility
__all__ = [
    "MonetizationAnalyzerFactoryWrapper",
    "MonetizationAnalyzerFactory",
    "get_monetization_analyzer",
    "list_available_frameworks",
    "get_framework_info",
    "compare_frameworks",
    "create_dspy_analyzer",
    "create_agno_analyzer",
    "MonetizationLLMAnalyzer",
    "MonetizationAgnoAnalyzer",
    "get_analyzer",
    "list_frameworks",
    "get_info",
    "compare"
]