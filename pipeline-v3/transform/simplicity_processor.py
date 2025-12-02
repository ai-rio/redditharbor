"""
Simplicity-driven score processor - Legacy agent approach

Implements the proven methodology from agent_tools/opportunity_analyzer_agent.py:
- Simplicity score as a separate 20% weighted dimension
- Score-driven function count adjustment (not prompt-driven)
- Natural bias toward simpler apps for lower scores
"""

import logging
from typing import List
from models import AnalysisResult, AppIdea

logger = logging.getLogger(__name__)


class SimplicityProcessor:
    """
    Post-processes LLM analysis results to apply simplicity scoring and adjust function counts
    based on the proven legacy agent methodology.
    """

    def __init__(self):
        # Legacy agent weights (agent_tools/opportunity_analyzer_agent.py:54-61)
        self.methodology_weights = {
            "market_demand": 0.20,
            "pain_intensity": 0.25,
            "monetization_potential": 0.20,
            "market_gap": 0.10,
            "technical_feasibility": 0.05,
            "simplicity_score": 0.20  # Separate dimension, not a bonus
        }

    def process_analysis(self, analysis: AnalysisResult) -> AnalysisResult:
        """
        Apply simplicity scoring and adjust core functions based on score.

        This implements the legacy agent's score-driven approach:
        1. Calculate simplicity score based on function count
        2. Recalculate final_score using weighted formula
        3. Adjust core_functions based on the new score

        Args:
            analysis: Raw LLM analysis result

        Returns:
            AnalysisResult with adjusted scoring and functions
        """
        # Step 1: Calculate simplicity score based on current function count
        function_count = len(analysis.app_idea.core_functions)
        simplicity_score = self._calculate_simplicity_score(function_count)

        logger.debug(f"Initial function count: {function_count}, simplicity_score: {simplicity_score}")

        # Step 2: Recalculate final_score using legacy agent formula
        original_score = analysis.final_score
        adjusted_score = self._calculate_weighted_score(
            market_demand=analysis.market_metrics.market_demand,
            pain_intensity=analysis.market_metrics.pain_intensity,
            monetization_potential=analysis.market_metrics.monetization_potential,
            market_gap=analysis.market_metrics.competition_level,
            technical_feasibility=analysis.market_metrics.technical_feasibility,
            simplicity_score=simplicity_score
        )

        # Step 3: Adjust core_functions based on score (legacy agent logic)
        adjusted_functions = self._adjust_functions_by_score(
            core_functions=analysis.app_idea.core_functions,
            final_score=adjusted_score
        )

        # Recalculate simplicity score with adjusted function count
        new_function_count = len(adjusted_functions)
        final_simplicity_score = self._calculate_simplicity_score(new_function_count)
        final_score = self._calculate_weighted_score(
            market_demand=analysis.market_metrics.market_demand,
            pain_intensity=analysis.market_metrics.pain_intensity,
            monetization_potential=analysis.market_metrics.monetization_potential,
            market_gap=analysis.market_metrics.competition_level,
            technical_feasibility=analysis.market_metrics.technical_feasibility,
            simplicity_score=final_simplicity_score
        )

        logger.info(
            f"Simplicity adjustment: {function_count}→{new_function_count} functions, "
            f"score: {original_score:.1f}→{final_score:.1f}"
        )

        # Create updated analysis with adjusted values
        updated_app_idea = AppIdea(
            title=analysis.app_idea.title,
            app_concept=analysis.app_idea.app_concept,
            problem_statement=analysis.app_idea.problem_statement,
            target_audience=analysis.app_idea.target_audience,
            core_functions=adjusted_functions
        )

        analysis.app_idea = updated_app_idea
        analysis.final_score = final_score

        return analysis

    def _calculate_simplicity_score(self, function_count: int) -> float:
        """
        Calculate simplicity score based on function count.

        Legacy agent scale (inferred from default of 70 for 3 functions):
        - 1 function = 100 points (perfect simplicity)
        - 2 functions = 85 points (good simplicity)
        - 3 functions = 70 points (baseline)

        Args:
            function_count: Number of core functions

        Returns:
            Simplicity score (0-100)
        """
        if function_count == 1:
            return 100.0
        elif function_count == 2:
            return 85.0
        elif function_count == 3:
            return 70.0
        else:
            # Penalize 4+ functions (shouldn't happen due to validation)
            return max(0.0, 70.0 - ((function_count - 3) * 15.0))

    def _calculate_weighted_score(
        self,
        market_demand: float,
        pain_intensity: float,
        monetization_potential: float,
        market_gap: float,
        technical_feasibility: float,
        simplicity_score: float
    ) -> float:
        """
        Calculate weighted final score using legacy agent formula.

        Legacy agent implementation (agent_tools/opportunity_analyzer_agent.py:64-73)

        Args:
            market_demand: Market demand score (0-100)
            pain_intensity: Pain intensity score (0-100)
            monetization_potential: Monetization potential score (0-100)
            market_gap: Market gap score (0-100)
            technical_feasibility: Technical feasibility score (0-100)
            simplicity_score: Simplicity score (0-100)

        Returns:
            Weighted final score (0-100)
        """
        final = (
            market_demand * self.methodology_weights["market_demand"] +
            pain_intensity * self.methodology_weights["pain_intensity"] +
            monetization_potential * self.methodology_weights["monetization_potential"] +
            market_gap * self.methodology_weights["market_gap"] +
            technical_feasibility * self.methodology_weights["technical_feasibility"] +
            simplicity_score * self.methodology_weights["simplicity_score"]
        )
        return round(final, 2)

    def _adjust_functions_by_score(
        self,
        core_functions: List[str],
        final_score: float
    ) -> List[str]:
        """
        Adjust core functions based on opportunity score.

        Legacy agent logic (agent_tools/opportunity_analyzer_agent.py:330-346):
        - Always keep primary function (most important)
        - Add 2nd function only if score >= 70 (high-scoring opportunities)
        - Add 3rd function only if score >= 60 (medium-high scoring)

        This creates natural bias toward simpler apps for lower scores.

        Args:
            core_functions: List of core functions from LLM
            final_score: Calculated opportunity score

        Returns:
            Adjusted list of 1-3 core functions
        """
        if not core_functions:
            return ["Core functionality"]

        # Always keep the first (primary) function
        adjusted = [core_functions[0]]

        # Add second function only for high-scoring opportunities (>= 70)
        if final_score >= 70.0 and len(core_functions) >= 2:
            adjusted.append(core_functions[1])

        # Add third function only for medium-high scoring (>= 60)
        if final_score >= 60.0 and len(core_functions) >= 3:
            adjusted.append(core_functions[2])

        logger.debug(
            f"Function adjustment: score={final_score:.1f}, "
            f"{len(core_functions)}→{len(adjusted)} functions"
        )

        return adjusted
