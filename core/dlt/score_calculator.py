"""
Centralized Score Calculation Module for DLT Compliance.

This module provides a single source of truth for all score calculations used across
the RedditHarbor system. It ensures consistency between:
- Constraint validation (resource layer)
- Normalization hooks (normalization layer)
- Application scripts (application layer)

DLT Compliance Features:
- Deterministic scoring (no floating point issues)
- Audit trail for score modifications
- Type-safe score calculations
- Constraint enforcement with score zeroing

Usage:
    from core.dlt.score_calculator import (
        calculate_simplicity_score,
        calculate_total_score,
        apply_constraint_to_score
    )

    # Calculate simplicity score
    simplicity = calculate_simplicity_score(function_count=2)  # Returns 85.0

    # Calculate weighted total score
    total = calculate_total_score(opportunity, weights)

    # Apply constraint validation with audit trail
    validated_opp = apply_constraint_to_score(opportunity, function_count=4)
"""

from datetime import datetime
from typing import Any


def calculate_simplicity_score(function_count: int) -> float:
    """
    Calculate simplicity score using the established methodology formula.

    This is the single source of truth for simplicity scoring across the entire
    RedditHarbor system. The formula enforces the 1-3 core function constraint:

    Scoring:
    - 1 function = 100 points (maximum simplicity)
    - 2 functions = 85 points
    - 3 functions = 70 points (minimum approved score)
    - 4+ functions = 0 points (automatic disqualification)

    Args:
        function_count: Number of core functions in the app (integer >= 0)

    Returns:
        float: Simplicity score ranging from 0.0 to 100.0

    Raises:
        TypeError: If function_count is not an integer
        ValueError: If function_count is negative

    Examples:
        >>> calculate_simplicity_score(1)
        100.0
        >>> calculate_simplicity_score(2)
        85.0
        >>> calculate_simplicity_score(3)
        70.0
        >>> calculate_simplicity_score(4)
        0.0
    """
    if not isinstance(function_count, int):
        raise TypeError(f"function_count must be int, got {type(function_count).__name__}")

    if function_count < 0:
        raise ValueError(f"function_count must be >= 0, got {function_count}")

    # Deterministic scoring table (DLT-safe)
    if function_count == 1:
        return 100.0
    elif function_count == 2:
        return 85.0
    elif function_count == 3:
        return 70.0
    else:
        # 0 functions or 4+ functions = disqualified
        return 0.0


def calculate_total_score(
    opportunity: dict[str, Any],
    weights: dict[str, float] | None = None
) -> float:
    """
    Calculate weighted total score for an opportunity.

    Uses the established 5-dimensional scoring methodology with customizable weights:
    - Market Demand (default 20%)
    - Pain Intensity (default 25%)
    - Monetization Potential (default 20%)
    - Market Gap (default 10%)
    - Technical Feasibility (default 5%)
    - Simplicity Score (default 20%)

    Args:
        opportunity: Dictionary containing all dimension scores
        weights: Optional custom weights dictionary (default: standard weights)

    Returns:
        float: Weighted total score (0-100), rounded to 2 decimal places

    Raises:
        KeyError: If required dimension scores are missing
        ValueError: If weights don't sum to 1.0 (within tolerance)

    Examples:
        >>> opp = {
        ...     "market_demand_score": 80,
        ...     "pain_intensity_score": 85,
        ...     "monetization_potential_score": 78,
        ...     "market_gap_score": 72,
        ...     "technical_feasibility_score": 95,
        ...     "simplicity_score": 100
        ... }
        >>> calculate_total_score(opp)
        84.95
    """
    # Default weights from methodology
    if weights is None:
        weights = {
            "market_demand_score": 0.20,
            "pain_intensity_score": 0.25,
            "monetization_potential_score": 0.20,
            "market_gap_score": 0.10,
            "technical_feasibility_score": 0.05,
            "simplicity_score": 0.20
        }

    # Validate weights sum to 1.0 (allow small floating point tolerance)
    weight_sum = sum(weights.values())
    if abs(weight_sum - 1.0) > 0.001:
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    # Extract dimension scores (raise KeyError if missing)
    required_dimensions = [
        "market_demand_score",
        "pain_intensity_score",
        "monetization_potential_score",
        "market_gap_score",
        "technical_feasibility_score",
        "simplicity_score"
    ]

    # Calculate weighted sum
    total_score = 0.0
    for dimension in required_dimensions:
        if dimension not in opportunity:
            raise KeyError(f"Missing required dimension: {dimension}")

        score = float(opportunity[dimension])
        weight = weights.get(dimension, 0.0)
        total_score += score * weight

    # Round to 2 decimal places for DLT stability
    return round(total_score, 2)


def apply_constraint_to_score(
    opportunity: dict[str, Any],
    function_count: int
) -> dict[str, Any]:
    """
    Apply simplicity constraint to opportunity score with audit trail.

    This function enforces the 1-3 core function constraint by:
    1. Calculating simplicity score
    2. If function_count >= 4, zero out all scores and add audit trail
    3. If function_count <= 3, calculate normal scores

    The audit trail preserves the original score before disqualification,
    enabling compliance auditing and analysis.

    Args:
        opportunity: Dictionary containing opportunity data and scores
        function_count: Number of core functions detected

    Returns:
        Dict[str, Any]: Opportunity with constraint enforcement applied

    Side Effects:
        - Modifies opportunity dictionary in-place
        - Adds "simplicity_score" field
        - For violations: sets "total_score" to 0, adds "_score_audit"

    Examples:
        >>> opp = {"app_name": "Test", "total_score": 85.0}
        >>> result = apply_constraint_to_score(opp, function_count=4)
        >>> result["total_score"]
        0.0
        >>> result["_score_audit"]["original_score"]
        85.0
        >>> result["_score_audit"]["reason"]
        'simplicity_constraint_violation'
    """
    # Calculate simplicity score
    simplicity_score = calculate_simplicity_score(function_count)
    opportunity["simplicity_score"] = simplicity_score

    # Apply constraint enforcement
    if function_count >= 4:
        # Preserve original score for audit trail
        original_total_score = opportunity.get("total_score", 0.0)

        # Add comprehensive audit trail
        opportunity["_score_audit"] = {
            "original_score": float(original_total_score),
            "reason": "simplicity_constraint_violation",
            "disqualified_at": datetime.now().isoformat(),
            "function_count": function_count,
            "max_allowed_functions": 3,
            "constraint_version": 1
        }

        # Zero out scores (disqualification)
        opportunity["total_score"] = 0.0
        opportunity["simplicity_score"] = 0.0

    return opportunity


def recalculate_scores_after_validation(
    opportunity: dict[str, Any],
    weights: dict[str, float] | None = None
) -> dict[str, Any]:
    """
    Recalculate total score AFTER constraint validation has been applied.

    This function should be used in the correct order:
    1. Apply constraint validation first (may zero scores)
    2. Then recalculate total score (for approved opportunities)

    This prevents the vulnerability where scores are calculated before validation.

    Args:
        opportunity: Dictionary with all dimension scores
        weights: Optional custom weights (default: standard methodology weights)

    Returns:
        Dict[str, Any]: Opportunity with recalculated total_score

    Raises:
        KeyError: If required dimension scores are missing

    Examples:
        >>> opp = {
        ...     "market_demand_score": 80,
        ...     "pain_intensity_score": 85,
        ...     "monetization_potential_score": 78,
        ...     "market_gap_score": 72,
        ...     "technical_feasibility_score": 95,
        ...     "simplicity_score": 100,
        ...     "is_disqualified": False
        ... }
        >>> result = recalculate_scores_after_validation(opp)
        >>> result["total_score"]
        84.95
    """
    # Only recalculate if not disqualified
    if opportunity.get("is_disqualified", False):
        # Disqualified apps should already have total_score = 0
        opportunity["total_score"] = 0.0
    else:
        # Calculate weighted total score for approved opportunities
        total_score = calculate_total_score(opportunity, weights)
        opportunity["total_score"] = total_score

    return opportunity


# Validation helpers

def validate_score_range(score: float, min_val: float = 0.0, max_val: float = 100.0) -> bool:
    """
    Validate that a score is within the expected range.

    Args:
        score: Score to validate
        min_val: Minimum allowed value (default: 0.0)
        max_val: Maximum allowed value (default: 100.0)

    Returns:
        bool: True if score is in range, False otherwise

    Examples:
        >>> validate_score_range(50.0)
        True
        >>> validate_score_range(150.0)
        False
        >>> validate_score_range(-10.0)
        False
    """
    return min_val <= score <= max_val


def get_score_audit_summary(opportunity: dict[str, Any]) -> dict[str, Any] | None:
    """
    Extract score audit summary from opportunity.

    Args:
        opportunity: Opportunity dictionary (may contain _score_audit)

    Returns:
        Optional[Dict[str, Any]]: Audit summary if available, None otherwise

    Examples:
        >>> opp = {"_score_audit": {"original_score": 85.0, "reason": "violation"}}
        >>> get_score_audit_summary(opp)
        {'original_score': 85.0, 'reason': 'violation'}
    """
    return opportunity.get("_score_audit")


def is_disqualified(opportunity: dict[str, Any]) -> bool:
    """
    Check if an opportunity has been disqualified.

    Args:
        opportunity: Opportunity dictionary

    Returns:
        bool: True if disqualified, False otherwise

    Examples:
        >>> is_disqualified({"is_disqualified": True})
        True
        >>> is_disqualified({"is_disqualified": False})
        False
        >>> is_disqualified({})
        False
    """
    return opportunity.get("is_disqualified", False)
