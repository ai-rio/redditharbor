"""Tests for trust score conversion utilities.

This test suite ensures 100% coverage of the trust_converters module,
testing all conversion functions with boundary values and edge cases.
"""

import pytest

from core.enrichment.trust_converters import (
    convert_all_trust_scores,
    get_ai_confidence_level,
    get_discussion_quality,
    get_engagement_level,
    get_problem_validity,
)


# ===========================
# get_engagement_level() Tests
# ===========================


def test_engagement_very_high():
    """Test VERY_HIGH engagement level (80-100)."""
    assert get_engagement_level(100.0) == "VERY_HIGH"
    assert get_engagement_level(85.0) == "VERY_HIGH"
    assert get_engagement_level(80.0) == "VERY_HIGH"


def test_engagement_high():
    """Test HIGH engagement level (60-79)."""
    assert get_engagement_level(79.9) == "HIGH"
    assert get_engagement_level(70.0) == "HIGH"
    assert get_engagement_level(60.0) == "HIGH"


def test_engagement_medium():
    """Test MEDIUM engagement level (40-59)."""
    assert get_engagement_level(59.9) == "MEDIUM"
    assert get_engagement_level(50.0) == "MEDIUM"
    assert get_engagement_level(40.0) == "MEDIUM"


def test_engagement_low():
    """Test LOW engagement level (20-39)."""
    assert get_engagement_level(39.9) == "LOW"
    assert get_engagement_level(30.0) == "LOW"
    assert get_engagement_level(20.0) == "LOW"


def test_engagement_minimal():
    """Test MINIMAL engagement level (0-19)."""
    assert get_engagement_level(19.9) == "MINIMAL"
    assert get_engagement_level(10.0) == "MINIMAL"
    assert get_engagement_level(0.0) == "MINIMAL"


def test_engagement_boundary_values():
    """Test exact boundary values for engagement levels."""
    # Test boundaries between levels
    assert get_engagement_level(79.99999) == "HIGH"
    assert get_engagement_level(80.00001) == "VERY_HIGH"

    assert get_engagement_level(59.99999) == "MEDIUM"
    assert get_engagement_level(60.00001) == "HIGH"

    assert get_engagement_level(39.99999) == "LOW"
    assert get_engagement_level(40.00001) == "MEDIUM"

    assert get_engagement_level(19.99999) == "MINIMAL"
    assert get_engagement_level(20.00001) == "LOW"


def test_engagement_negative_score():
    """Test engagement with negative score."""
    assert get_engagement_level(-10.0) == "MINIMAL"


def test_engagement_above_100():
    """Test engagement with score above 100."""
    assert get_engagement_level(150.0) == "VERY_HIGH"


# ===========================
# get_problem_validity() Tests
# ===========================


def test_validity_valid():
    """Test VALID problem validity (80-100)."""
    assert get_problem_validity(100.0) == "VALID"
    assert get_problem_validity(85.0) == "VALID"
    assert get_problem_validity(80.0) == "VALID"


def test_validity_potential():
    """Test POTENTIAL problem validity (60-79)."""
    assert get_problem_validity(79.9) == "POTENTIAL"
    assert get_problem_validity(70.0) == "POTENTIAL"
    assert get_problem_validity(60.0) == "POTENTIAL"


def test_validity_unclear():
    """Test UNCLEAR problem validity (40-59)."""
    assert get_problem_validity(59.9) == "UNCLEAR"
    assert get_problem_validity(50.0) == "UNCLEAR"
    assert get_problem_validity(40.0) == "UNCLEAR"


def test_validity_invalid():
    """Test INVALID problem validity (0-39)."""
    assert get_problem_validity(39.9) == "INVALID"
    assert get_problem_validity(20.0) == "INVALID"
    assert get_problem_validity(0.0) == "INVALID"


def test_validity_boundary_values():
    """Test exact boundary values for problem validity."""
    assert get_problem_validity(79.99999) == "POTENTIAL"
    assert get_problem_validity(80.00001) == "VALID"

    assert get_problem_validity(59.99999) == "UNCLEAR"
    assert get_problem_validity(60.00001) == "POTENTIAL"

    assert get_problem_validity(39.99999) == "INVALID"
    assert get_problem_validity(40.00001) == "UNCLEAR"


def test_validity_negative_score():
    """Test problem validity with negative score."""
    assert get_problem_validity(-10.0) == "INVALID"


def test_validity_above_100():
    """Test problem validity with score above 100."""
    assert get_problem_validity(150.0) == "VALID"


# ===========================
# get_discussion_quality() Tests
# ===========================


def test_discussion_excellent():
    """Test EXCELLENT discussion quality (80-100)."""
    assert get_discussion_quality(100.0) == "EXCELLENT"
    assert get_discussion_quality(85.0) == "EXCELLENT"
    assert get_discussion_quality(80.0) == "EXCELLENT"


def test_discussion_good():
    """Test GOOD discussion quality (60-79)."""
    assert get_discussion_quality(79.9) == "GOOD"
    assert get_discussion_quality(70.0) == "GOOD"
    assert get_discussion_quality(60.0) == "GOOD"


def test_discussion_fair():
    """Test FAIR discussion quality (40-59)."""
    assert get_discussion_quality(59.9) == "FAIR"
    assert get_discussion_quality(50.0) == "FAIR"
    assert get_discussion_quality(40.0) == "FAIR"


def test_discussion_poor():
    """Test POOR discussion quality (0-39)."""
    assert get_discussion_quality(39.9) == "POOR"
    assert get_discussion_quality(20.0) == "POOR"
    assert get_discussion_quality(0.0) == "POOR"


def test_discussion_boundary_values():
    """Test exact boundary values for discussion quality."""
    assert get_discussion_quality(79.99999) == "GOOD"
    assert get_discussion_quality(80.00001) == "EXCELLENT"

    assert get_discussion_quality(59.99999) == "FAIR"
    assert get_discussion_quality(60.00001) == "GOOD"

    assert get_discussion_quality(39.99999) == "POOR"
    assert get_discussion_quality(40.00001) == "FAIR"


def test_discussion_negative_score():
    """Test discussion quality with negative score."""
    assert get_discussion_quality(-10.0) == "POOR"


def test_discussion_above_100():
    """Test discussion quality with score above 100."""
    assert get_discussion_quality(150.0) == "EXCELLENT"


# ===========================
# get_ai_confidence_level() Tests
# ===========================


def test_confidence_very_high():
    """Test VERY_HIGH AI confidence (80-100)."""
    assert get_ai_confidence_level(100.0) == "VERY_HIGH"
    assert get_ai_confidence_level(85.0) == "VERY_HIGH"
    assert get_ai_confidence_level(80.0) == "VERY_HIGH"


def test_confidence_high():
    """Test HIGH AI confidence (60-79)."""
    assert get_ai_confidence_level(79.9) == "HIGH"
    assert get_ai_confidence_level(70.0) == "HIGH"
    assert get_ai_confidence_level(60.0) == "HIGH"


def test_confidence_medium():
    """Test MEDIUM AI confidence (40-59)."""
    assert get_ai_confidence_level(59.9) == "MEDIUM"
    assert get_ai_confidence_level(50.0) == "MEDIUM"
    assert get_ai_confidence_level(40.0) == "MEDIUM"


def test_confidence_low():
    """Test LOW AI confidence (0-39)."""
    assert get_ai_confidence_level(39.9) == "LOW"
    assert get_ai_confidence_level(20.0) == "LOW"
    assert get_ai_confidence_level(0.0) == "LOW"


def test_confidence_boundary_values():
    """Test exact boundary values for AI confidence."""
    assert get_ai_confidence_level(79.99999) == "HIGH"
    assert get_ai_confidence_level(80.00001) == "VERY_HIGH"

    assert get_ai_confidence_level(59.99999) == "MEDIUM"
    assert get_ai_confidence_level(60.00001) == "HIGH"

    assert get_ai_confidence_level(39.99999) == "LOW"
    assert get_ai_confidence_level(40.00001) == "MEDIUM"


def test_confidence_negative_score():
    """Test AI confidence with negative score."""
    assert get_ai_confidence_level(-10.0) == "LOW"


def test_confidence_above_100():
    """Test AI confidence with score above 100."""
    assert get_ai_confidence_level(150.0) == "VERY_HIGH"


# ===========================
# convert_all_trust_scores() Tests
# ===========================


def test_convert_all_complete_data():
    """Test converting all scores with complete data."""
    trust_data = {
        "engagement_score": 85.0,
        "problem_validity_score": 70.0,
        "discussion_quality_score": 55.0,
        "ai_confidence_score": 90.0,
    }

    result = convert_all_trust_scores(trust_data)

    # Check categorical levels added
    assert result["engagement_level"] == "VERY_HIGH"
    assert result["problem_validity"] == "POTENTIAL"
    assert result["discussion_quality"] == "FAIR"
    assert result["ai_confidence"] == "VERY_HIGH"

    # Check original scores preserved
    assert result["engagement_score"] == 85.0
    assert result["problem_validity_score"] == 70.0
    assert result["discussion_quality_score"] == 55.0
    assert result["ai_confidence_score"] == 90.0


def test_convert_all_partial_data():
    """Test converting with only some scores present."""
    trust_data = {
        "engagement_score": 45.0,
        "discussion_quality_score": 62.0,
        # problem_validity_score and ai_confidence_score missing
    }

    result = convert_all_trust_scores(trust_data)

    # Check present scores converted
    assert result["engagement_level"] == "MEDIUM"
    assert result["discussion_quality"] == "GOOD"

    # Check missing scores don't create levels
    assert "problem_validity" not in result
    assert "ai_confidence" not in result

    # Check original scores preserved
    assert result["engagement_score"] == 45.0
    assert result["discussion_quality_score"] == 62.0


def test_convert_all_empty_data():
    """Test converting with empty dictionary."""
    trust_data = {}

    result = convert_all_trust_scores(trust_data)

    # Should return empty dict (no levels added)
    assert result == {}


def test_convert_all_none_values():
    """Test converting with None score values."""
    trust_data = {
        "engagement_score": None,
        "problem_validity_score": 70.0,
        "discussion_quality_score": None,
        "ai_confidence_score": 80.0,
    }

    result = convert_all_trust_scores(trust_data)

    # Only non-None scores should be converted
    assert "engagement_level" not in result
    assert result["problem_validity"] == "POTENTIAL"
    assert "discussion_quality" not in result
    assert result["ai_confidence"] == "VERY_HIGH"

    # Check all original values preserved
    assert result["engagement_score"] is None
    assert result["problem_validity_score"] == 70.0
    assert result["discussion_quality_score"] is None
    assert result["ai_confidence_score"] == 80.0


def test_convert_all_preserves_extra_fields():
    """Test that extra fields in trust_data are preserved."""
    trust_data = {
        "engagement_score": 50.0,
        "extra_field_1": "value1",
        "extra_field_2": 123,
    }

    result = convert_all_trust_scores(trust_data)

    # Check conversion happened
    assert result["engagement_level"] == "MEDIUM"

    # Check extra fields preserved
    assert result["extra_field_1"] == "value1"
    assert result["extra_field_2"] == 123


def test_convert_all_zero_scores():
    """Test converting with zero scores."""
    trust_data = {
        "engagement_score": 0.0,
        "problem_validity_score": 0.0,
        "discussion_quality_score": 0.0,
        "ai_confidence_score": 0.0,
    }

    result = convert_all_trust_scores(trust_data)

    # All should convert to lowest level
    assert result["engagement_level"] == "MINIMAL"
    assert result["problem_validity"] == "INVALID"
    assert result["discussion_quality"] == "POOR"
    assert result["ai_confidence"] == "LOW"


def test_convert_all_boundary_scores():
    """Test converting with exact boundary scores."""
    trust_data = {
        "engagement_score": 80.0,  # Boundary for VERY_HIGH
        "problem_validity_score": 60.0,  # Boundary for POTENTIAL
        "discussion_quality_score": 40.0,  # Boundary for FAIR
        "ai_confidence_score": 80.0,  # Boundary for VERY_HIGH
    }

    result = convert_all_trust_scores(trust_data)

    assert result["engagement_level"] == "VERY_HIGH"
    assert result["problem_validity"] == "POTENTIAL"
    assert result["discussion_quality"] == "FAIR"
    assert result["ai_confidence"] == "VERY_HIGH"


def test_convert_all_max_scores():
    """Test converting with maximum scores."""
    trust_data = {
        "engagement_score": 100.0,
        "problem_validity_score": 100.0,
        "discussion_quality_score": 100.0,
        "ai_confidence_score": 100.0,
    }

    result = convert_all_trust_scores(trust_data)

    assert result["engagement_level"] == "VERY_HIGH"
    assert result["problem_validity"] == "VALID"
    assert result["discussion_quality"] == "EXCELLENT"
    assert result["ai_confidence"] == "VERY_HIGH"


def test_convert_all_doesnt_modify_original():
    """Test that convert_all_trust_scores doesn't modify the original dict."""
    trust_data = {
        "engagement_score": 85.0,
    }

    result = convert_all_trust_scores(trust_data)

    # Original should not have the new level
    assert "engagement_level" not in trust_data

    # Result should have the new level
    assert "engagement_level" in result


def test_convert_all_with_integer_scores():
    """Test converting with integer scores (should work)."""
    trust_data = {
        "engagement_score": 85,  # Integer instead of float
        "problem_validity_score": 70,
        "discussion_quality_score": 55,
        "ai_confidence_score": 90,
    }

    result = convert_all_trust_scores(trust_data)

    # Should still convert correctly
    assert result["engagement_level"] == "VERY_HIGH"
    assert result["problem_validity"] == "POTENTIAL"
    assert result["discussion_quality"] == "FAIR"
    assert result["ai_confidence"] == "VERY_HIGH"


def test_convert_all_returns_dict():
    """Test that convert_all_trust_scores always returns a dict."""
    result1 = convert_all_trust_scores({})
    result2 = convert_all_trust_scores({"engagement_score": 50.0})

    assert isinstance(result1, dict)
    assert isinstance(result2, dict)
