"""Trust score conversion utilities.

This module provides utilities for converting numeric trust scores to categorical
levels. Extracted from scripts/dlt/dlt_trust_pipeline.py lines 423-471 to enable
code reuse across the pipeline.
"""

from typing import Any


def get_engagement_level(score: float) -> str:
    """
    Convert engagement score to categorical level.

    Categorizes engagement scores into 5 levels based on community interaction
    metrics. Extracted from dlt_trust_pipeline.py line 423.

    Args:
        score: Engagement score (0-100)

    Returns:
        str: Engagement level category:
            - "VERY_HIGH" (80-100): Exceptional community engagement
            - "HIGH" (60-79): Strong community engagement
            - "MEDIUM" (40-59): Moderate community engagement
            - "LOW" (20-39): Limited community engagement
            - "MINIMAL" (0-19): Minimal community engagement

    Examples:
        >>> get_engagement_level(85.0)
        'VERY_HIGH'
        >>> get_engagement_level(45.0)
        'MEDIUM'
        >>> get_engagement_level(10.0)
        'MINIMAL'
    """
    if score >= 80:
        return "VERY_HIGH"
    elif score >= 60:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    elif score >= 20:
        return "LOW"
    else:
        return "MINIMAL"


def get_problem_validity(score: float) -> str:
    """
    Convert problem validity score to categorical level.

    Categorizes problem validity scores into 4 levels based on how well the
    submission describes a real, actionable problem. Extracted from
    dlt_trust_pipeline.py line 437.

    Args:
        score: Problem validity score (0-100)

    Returns:
        str: Problem validity category:
            - "VALID" (80-100): Clearly valid problem
            - "POTENTIAL" (60-79): Potentially valid problem
            - "UNCLEAR" (40-59): Unclear problem validity
            - "INVALID" (0-39): Invalid or unclear problem

    Examples:
        >>> get_problem_validity(85.0)
        'VALID'
        >>> get_problem_validity(55.0)
        'UNCLEAR'
        >>> get_problem_validity(30.0)
        'INVALID'
    """
    if score >= 80:
        return "VALID"
    elif score >= 60:
        return "POTENTIAL"
    elif score >= 40:
        return "UNCLEAR"
    else:
        return "INVALID"


def get_discussion_quality(score: float) -> str:
    """
    Convert discussion quality score to categorical level.

    Categorizes discussion quality scores into 4 levels based on the depth
    and usefulness of comments. Extracted from dlt_trust_pipeline.py line 449.

    Args:
        score: Discussion quality score (0-100)

    Returns:
        str: Discussion quality category:
            - "EXCELLENT" (80-100): Excellent discussion quality
            - "GOOD" (60-79): Good discussion quality
            - "FAIR" (40-59): Fair discussion quality
            - "POOR" (0-39): Poor discussion quality

    Examples:
        >>> get_discussion_quality(85.0)
        'EXCELLENT'
        >>> get_discussion_quality(55.0)
        'FAIR'
        >>> get_discussion_quality(30.0)
        'POOR'
    """
    if score >= 80:
        return "EXCELLENT"
    elif score >= 60:
        return "GOOD"
    elif score >= 40:
        return "FAIR"
    else:
        return "POOR"


def get_ai_confidence_level(score: float) -> str:
    """
    Convert AI confidence score to categorical level.

    Categorizes AI confidence scores into 4 levels based on how confident
    the AI model is in its analysis. Extracted from dlt_trust_pipeline.py
    line 461.

    Args:
        score: AI confidence score (0-100)

    Returns:
        str: AI confidence category:
            - "VERY_HIGH" (80-100): Very high confidence
            - "HIGH" (60-79): High confidence
            - "MEDIUM" (40-59): Medium confidence
            - "LOW" (0-39): Low confidence

    Examples:
        >>> get_ai_confidence_level(85.0)
        'VERY_HIGH'
        >>> get_ai_confidence_level(55.0)
        'MEDIUM'
        >>> get_ai_confidence_level(30.0)
        'LOW'
    """
    if score >= 80:
        return "VERY_HIGH"
    elif score >= 60:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "LOW"


def convert_all_trust_scores(trust_data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert all numeric trust scores to categorical levels.

    Convenience function to apply all trust score converters to a trust data
    dictionary. Adds categorical level fields while preserving original scores.

    Args:
        trust_data: Dictionary containing trust scores with keys:
            - engagement_score: Numeric engagement score (optional)
            - problem_validity_score: Numeric problem validity score (optional)
            - discussion_quality_score: Numeric discussion quality score (optional)
            - ai_confidence_score: Numeric AI confidence score (optional)

    Returns:
        dict: Original trust_data with added categorical level fields:
            - engagement_level: Categorical engagement level
            - problem_validity: Categorical problem validity
            - discussion_quality: Categorical discussion quality
            - ai_confidence: Categorical AI confidence level
            All original scores are preserved.

    Examples:
        >>> data = {
        ...     'engagement_score': 85.0,
        ...     'problem_validity_score': 70.0,
        ...     'discussion_quality_score': 55.0,
        ...     'ai_confidence_score': 90.0
        ... }
        >>> result = convert_all_trust_scores(data)
        >>> assert result['engagement_level'] == 'VERY_HIGH'
        >>> assert result['problem_validity'] == 'POTENTIAL'
        >>> assert result['discussion_quality'] == 'FAIR'
        >>> assert result['ai_confidence'] == 'VERY_HIGH'
        >>> assert result['engagement_score'] == 85.0  # Original preserved
    """
    result = {**trust_data}  # Copy original data

    # Convert each score if present
    if "engagement_score" in trust_data and trust_data["engagement_score"] is not None:
        result["engagement_level"] = get_engagement_level(trust_data["engagement_score"])

    if "problem_validity_score" in trust_data and trust_data["problem_validity_score"] is not None:
        result["problem_validity"] = get_problem_validity(trust_data["problem_validity_score"])

    if "discussion_quality_score" in trust_data and trust_data["discussion_quality_score"] is not None:
        result["discussion_quality"] = get_discussion_quality(
            trust_data["discussion_quality_score"]
        )

    if "ai_confidence_score" in trust_data and trust_data["ai_confidence_score"] is not None:
        result["ai_confidence"] = get_ai_confidence_level(trust_data["ai_confidence_score"])

    return result
