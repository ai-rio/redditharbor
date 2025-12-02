#!/usr/bin/env python3
"""
RedditHarbor Monetization Analyzer Factory

Factory module for selecting between DSPy and Agno implementations.
Provides backward compatibility and allows framework switching via configuration.

Usage:
    from agent_tools.monetization_analyzer_factory import get_monetization_analyzer

    # Automatically selects framework based on MONETIZATION_FRAMEWORK setting
    analyzer = get_monetization_analyzer()

    # Or explicitly specify framework
    analyzer = get_monetization_analyzer(framework="agno")
"""

import os
import sys
from pathlib import Path
from typing import Union

# Add project root to path - ensure we're adding the correct root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import centralized configuration
try:
    import config.settings as settings
except ImportError:
    # Fallback for standalone usage
    class Settings:
        MONETIZATION_FRAMEWORK = os.getenv("MONETIZATION_FRAMEWORK", "agno")
        MONETIZATION_LLM_MODEL = os.getenv(
            "MONETIZATION_LLM_MODEL", "anthropic/claude-haiku-4.5"
        )
        AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")

    settings = Settings()

# Import both implementations
try:
    from .llm_analyzer import MonetizationLLMAnalyzer

    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    MonetizationLLMAnalyzer = None

try:
    from .agno_analyzer import MonetizationAgnoAnalyzer

    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    MonetizationAgnoAnalyzer = None


def get_monetization_analyzer(
    framework: str | None = None, model: str | None = None, **kwargs
) -> Union["MonetizationLLMAnalyzer", "MonetizationAgnoAnalyzer"]:
    """
    Get monetization analyzer instance based on configuration.

    Args:
        framework: Optional framework override ("dspy" or "agno")
                  If not provided, uses settings.MONETIZATION_FRAMEWORK
        model: Optional model override. If not provided,
               uses settings.MONETIZATION_LLM_MODEL
        **kwargs: Additional arguments passed to the analyzer constructor

    Returns:
        Analyzer instance (either DSPy or Agno implementation)

    Raises:
        ValueError: If specified framework is not available
        ImportError: If neither framework is available
    """
    # Determine which framework to use
    if framework is None:
        framework = getattr(settings, "MONETIZATION_FRAMEWORK", "agno")

    framework = framework.lower()

    # Use provided model or fallback to settings
    if model is None:
        model = getattr(
            settings, "MONETIZATION_LLM_MODEL", "anthropic/claude-haiku-4.5"
        )

    # Return appropriate analyzer
    if framework == "dspy":
        if not DSPY_AVAILABLE:
            raise ValueError(
                "DSPy framework requested but not available. "
                "Install with: pip install dspy-ai"
            )

        # Extract relevant kwargs for DSPy
        dspy_kwargs = {k: v for k, v in kwargs.items() if k in ["model"]}
        dspy_kwargs["model"] = model

        return MonetizationLLMAnalyzer(**dspy_kwargs)

    elif framework == "agno":
        if not AGNO_AVAILABLE:
            raise ValueError(
                "Agno framework requested but not available. "
                "Install with: pip install agno agentops"
            )

        # Extract relevant kwargs for Agno
        agno_kwargs = {
            k: v for k, v in kwargs.items() if k in ["model", "agentops_api_key"]
        }
        agno_kwargs["model"] = model

        # Add AgentOps API key from settings if not provided
        if "agentops_api_key" not in agno_kwargs:
            agno_kwargs["agentops_api_key"] = getattr(
                settings, "AGENTOPS_API_KEY", None
            )

        return MonetizationAgnoAnalyzer(**agno_kwargs)

    else:
        raise ValueError(f"Unknown framework: {framework}. Use 'dspy' or 'agno'")


def list_available_frameworks() -> dict:
    """
    List available monetization analyzer frameworks.

    Returns:
        Dict with framework availability status
    """
    return {
        "dspy": {
            "available": DSPY_AVAILABLE,
            "class": MonetizationLLMAnalyzer.__name__ if DSPY_AVAILABLE else None,
            "description": "Original DSPy-based implementation",
        },
        "agno": {
            "available": AGNO_AVAILABLE,
            "class": MonetizationAgnoAnalyzer.__name__ if AGNO_AVAILABLE else None,
            "description": "New multi-agent architecture with cost tracking",
        },
    }


def get_framework_info(framework: str) -> dict:
    """
    Get information about a specific framework.

    Args:
        framework: Framework name ("dspy" or "agno")

    Returns:
        Dict with framework information
    """
    frameworks = list_available_frameworks()
    framework = framework.lower()

    if framework not in frameworks:
        raise ValueError(f"Unknown framework: {framework}")

    info = frameworks[framework].copy()
    info["selected"] = (
        getattr(settings, "MONETIZATION_FRAMEWORK", "agno").lower() == framework
    )

    return info


def compare_frameworks() -> dict:
    """
    Compare available frameworks and show differences.

    Returns:
        Dict with comparison information
    """
    return {
        "available": list_available_frameworks(),
        "current_selection": getattr(settings, "MONETIZATION_FRAMEWORK", "agno"),
        "comparison": {
            "dspy": {
                "pros": [
                    "Mature and stable implementation",
                    "Lower dependency overhead",
                    "Simpler architecture",
                ],
                "cons": [
                    "No built-in cost tracking",
                    "Single-agent architecture",
                    "Less flexible for complex analysis",
                ],
            },
            "agno": {
                "pros": [
                    "Multi-agent architecture",
                    "AgentOps cost tracking",
                    "Better error handling",
                    "Streaming support",
                    "More extensible",
                ],
                "cons": ["More dependencies", "Newer framework", "Higher memory usage"],
            },
        },
    }


# =============================================================================
# CONVENIENCE FUNCTIONS FOR BACKWARD COMPATIBILITY
# =============================================================================


def create_dspy_analyzer(model: str | None = None, **kwargs):
    """Create DSPy analyzer (convenience function)"""
    return get_monetization_analyzer(framework="dspy", model=model, **kwargs)


def create_agno_analyzer(
    model: str | None = None, agentops_api_key: str | None = None, **kwargs
):
    """Create Agno analyzer (convenience function)"""
    return get_monetization_analyzer(
        framework="agno", model=model, agentops_api_key=agentops_api_key, **kwargs
    )


class MonetizationAnalyzerFactory:
    """Factory class for creating monetization analyzers.

    Provides a class-based interface for creating monetization analyzers
    with different frameworks and configurations.
    """

    @staticmethod
    def create_analyzer(framework: str | None = None, model: str | None = None, **kwargs):
        """Create a monetization analyzer instance.

        Args:
            framework: Framework to use ('dspy' or 'agno')
            model: Model name to use
            **kwargs: Additional arguments for the analyzer

        Returns:
            Monetization analyzer instance
        """
        return get_monetization_analyzer(framework=framework, model=model, **kwargs)

    @staticmethod
    def list_frameworks():
        """List available frameworks."""
        return list_available_frameworks()

    @staticmethod
    def compare_frameworks():
        """Compare available frameworks."""
        return compare_frameworks()


# =============================================================================
# DEMO FUNCTIONS
# =============================================================================


def demo_framework_selection():
    """Demo framework selection and comparison"""
    print("\n" + "=" * 80)
    print("MONETIZATION ANALYZER FRAMEWORK SELECTION")
    print("=" * 80 + "\n")

    # Show available frameworks
    print("\n--- Available Frameworks ---")
    frameworks = list_available_frameworks()
    for name, info in frameworks.items():
        status = "✅ Available" if info["available"] else "❌ Not Available"
        print(f"{name}: {status}")
        if info["available"]:
            print(f"  Class: {info['class']}")
            print(f"  Description: {info['description']}")

    # Show current selection
    print("\n--- Current Selection ---")
    print(f"Framework: {getattr(settings, 'MONETIZATION_FRAMEWORK', 'agno')}")

    # Show comparison
    print("\n--- Framework Comparison ---")
    comparison = compare_frameworks()["comparison"]
    for framework, info in comparison.items():
        print(f"\n{framework.upper()}:")
        print("  Pros:")
        for pro in info["pros"]:
            print(f"    • {pro}")
        print("  Cons:")
        for con in info["cons"]:
            print(f"    • {con}")

    # Create analyzer with current selection
    print("\n--- Creating Analyzer ---")
    try:
        analyzer = get_monetization_analyzer()
        print(f"✅ Created analyzer: {analyzer.__class__.__name__}")

        # Test with a simple example
        print("\n--- Quick Test ---")
        result = analyzer.analyze(
            text="Looking for a project management tool under $100/month for our team.",
            subreddit="projectmanagement",
        )
        print("✅ Analysis successful")
        print(f"Score: {result.llm_monetization_score:.1f}/100")
        print(f"Segment: {result.customer_segment}")

    except Exception as e:
        print(f"❌ Error creating analyzer: {e}")


if __name__ == "__main__":
    demo_framework_selection()
