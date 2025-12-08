"""
Agno synthesis data structure for multi-agent analysis results
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class AgnoSynthesis:
    """Synthesized results from multi-agent analysis"""

    # Core metrics (0-100 scale)
    market_demand: float
    pain_intensity: float
    monetization_potential: float
    confidence_score: float

    # Detailed agent outputs
    agent_details: dict[str, Any]

    # Additional metadata
    subreddit_multiplier: float | None = 1.0
    raw_agent_outputs: dict[str, Any] | None = None
