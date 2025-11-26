#!/usr/bin/env python3
"""
Opportunity Analysis Wrapper

Thin wrapper for core.agents.interactive.opportunity_analyzer.OpportunityAnalyzerAgent
Provides clean interface while maintaining full backward compatibility.
"""

from typing import Any, Dict, List
import sys
from pathlib import Path

# Add project root to path for core imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from existing core module with fallback
try:
    from core.agents.interactive.opportunity_analyzer import (
        OpportunityAnalyzerAgent,
        OpportunityScore,
        ValidationStatus
    )
    CORE_AGENT_AVAILABLE = True
except ImportError:
    CORE_AGENT_AVAILABLE = False
    # Fallback classes for type hints
    class OpportunityScore: pass
    class ValidationStatus: pass

    class OpportunityAnalyzerAgent:
        def __init__(self):
            self.methodology_weights = {"market_demand": 0.20, "pain_intensity": 0.25,
                                       "monetization_potential": 0.20, "market_gap": 0.10,
                                       "technical_feasibility": 0.05, "simplicity_score": 0.20}
            self.supabase = None

        def analyze_opportunity(self, submission_data): return {"opportunity_id": "fallback", "final_score": 50.0}
        def batch_analyze_opportunities(self, submissions): return [self.analyze_opportunity(s) for s in submissions]
        def generate_validation_report(self, opportunity_id): return {"opportunity_id": opportunity_id}
        def track_business_metrics(self): return {"opportunities_identified": 0}
        def continuous_analysis(self, duration_minutes): return {"duration_minutes": duration_minutes}


class OpportunityAnalyzer:
    """Thin wrapper for OpportunityAnalyzerAgent from core/agents/."""

    def __init__(self):
        """Initialize wrapper with core OpportunityAnalyzerAgent."""
        self._agent = OpportunityAnalyzerAgent()
        self._fallback_mode = not CORE_AGENT_AVAILABLE

    def analyze_opportunity(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single opportunity using 5-dimensional scoring methodology."""
        return self._agent.analyze_opportunity(submission_data)

    def batch_analyze_opportunities(self, submissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple opportunities with error handling."""
        return self._agent.batch_analyze_opportunities(submissions)

    def generate_validation_report(self, opportunity_id: str) -> Dict[str, Any]:
        """Generate validation status tracking for an opportunity."""
        return self._agent.generate_validation_report(opportunity_id)

    def track_business_metrics(self) -> Dict[str, Any]:
        """Return current business KPI metrics."""
        return self._agent.track_business_metrics()

    def continuous_analysis(self, duration_minutes: int) -> Dict[str, Any]:
        """Run continuous analysis for specified duration."""
        return self._agent.continuous_analysis(duration_minutes)

    @property
    def methodology_weights(self) -> Dict[str, float]:
        """Get the 5-dimensional methodology weights."""
        return self._agent.methodology_weights

    @property
    def supabase(self):
        """Access to the Supabase client for direct database operations."""
        return self._agent.supabase


# Export key classes for backward compatibility
__all__ = ["OpportunityAnalyzer", "OpportunityScore", "ValidationStatus"]