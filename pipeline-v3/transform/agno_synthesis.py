"""
Agno synthesis data structure for multi-agent analysis results
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AgnoSynthesis:
    """Synthesized results from multi-agent analysis"""

    # Core metrics (0-100 scale)
    market_demand: float
    pain_intensity: float
    monetization_potential: float
    confidence_score: float

    # Detailed agent outputs
    agent_details: Dict[str, Any]

    # Additional metadata
    subreddit_multiplier: Optional[float] = 1.0
    raw_agent_outputs: Optional[Dict[str, Any]] = None