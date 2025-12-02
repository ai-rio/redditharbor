"""
DLT Constraint Validation Resource for Simplicity Constraint Enforcement.

This module implements DLT-native validation for the 1-3 core function constraint,
automatically disqualifying apps with 4+ functions and tracking constraint metadata.
"""

import re
from datetime import datetime
from typing import Any

import dlt

# Import core functions serialization utilities for format compatibility
from core.utils.core_functions_serialization import deserialize_core_functions


def _validate_function_consistency(opportunity: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure function_count matches len(function_list).
    Auto-corrects minor mismatches, raises on structural errors.

    Phase 1: Early warning system for function count/list mismatches.
    This catches schema inconsistencies before they propagate to downstream systems.

    Args:
        opportunity: App opportunity dictionary

    Returns:
        Dict[str, Any]: Opportunity with corrected function data

    Raises:
        ValueError: If function_list is not a list or opportunity has empty function_list
    """
    function_list = opportunity.get("function_list", [])
    function_count = opportunity.get("core_functions", 0)

    # Type check: function_list must be a list
    if not isinstance(function_list, list):
        raise ValueError(
            f"function_list must be list, got {type(function_list).__name__}: {function_list}"
        )

    # Count mismatch detection and auto-correction
    actual_count = len(function_list)
    if actual_count != function_count:
        opp_id = opportunity.get('opportunity_id', 'unknown')
        print(
            f"⚠️  MISMATCH in {opp_id}: "
            f"core_functions={function_count} but function_list={actual_count}"
        )
        opportunity["function_count"] = actual_count  # Auto-correct
        opportunity["core_functions"] = actual_count

    # Emptiness check
    if actual_count == 0:
        opp_id = opportunity.get('opportunity_id', 'unknown')
        raise ValueError(f"Opportunity {opp_id} has empty function_list")

    return opportunity


@dlt.resource(
    table_name="workflow_results",
    write_disposition="merge",
    columns={
        "opportunity_id": {"data_type": "text", "nullable": False, "unique": True},
        "app_name": {"data_type": "text", "nullable": False},
        "function_count": {"data_type": "bigint", "nullable": False},
        "function_list": {"data_type": "json", "nullable": True},
        "original_score": {"data_type": "double", "nullable": False},
        "final_score": {"data_type": "double", "nullable": False},
        "status": {"data_type": "text", "nullable": False},
        "constraint_applied": {"data_type": "bool", "nullable": True},
        "ai_insight": {"data_type": "text", "nullable": True},
        "processed_at": {"data_type": "timestamp", "nullable": True},
        "market_demand": {"data_type": "decimal", "precision": 5, "scale": 2, "nullable": True},
        "pain_intensity": {"data_type": "decimal", "precision": 5, "scale": 2, "nullable": True},
        "monetization_potential": {"data_type": "decimal", "precision": 5, "scale": 2, "nullable": True},
        "market_gap": {"data_type": "decimal", "precision": 5, "scale": 2, "nullable": True},
        "technical_feasibility": {"data_type": "decimal", "precision": 5, "scale": 2, "nullable": True},
        "core_functions": {"data_type": "bigint", "nullable": True},
        "simplicity_score": {"data_type": "double", "nullable": True},
        "is_disqualified": {"data_type": "bool", "nullable": True},
        "constraint_version": {"data_type": "bigint", "nullable": True},
        "validation_timestamp": {"data_type": "timestamp", "nullable": True},
        "violation_reason": {"data_type": "text", "nullable": True},
        "validation_status": {"data_type": "text", "nullable": True},
    }
)
def app_opportunities_with_constraint(opportunities: list[dict[str, Any]]):
    """
    DLT resource that validates simplicity constraint before loading.

    Enforces 1-3 core function rule with automatic disqualification for 4+ functions.
    Adds constraint metadata including core_functions count, simplicity_score,
    is_disqualified flag, and validation_timestamp.

    Args:
        opportunities: List of app opportunity dictionaries

    Yields:
        Dict[str, Any]: Opportunity with constraint metadata added
    """
    for opportunity in opportunities:
        # Extract core functions
        core_functions = _extract_core_functions(opportunity)
        function_count = len(core_functions)

        # Add function_list to opportunity for consistency validation
        opportunity["function_list"] = core_functions
        opportunity["core_functions"] = function_count

        # Phase 1: Validate function consistency before processing
        try:
            opportunity = _validate_function_consistency(opportunity)
        except ValueError as e:
            # Log validation error and skip this opportunity
            print(f"❌ Validation error: {e}")
            continue

        # Calculate simplicity score using methodology formula
        simplicity_score = _calculate_simplicity_score(function_count)

        # Add constraint metadata
        opportunity["simplicity_score"] = simplicity_score
        opportunity["is_disqualified"] = function_count >= 4
        opportunity["constraint_version"] = 1
        opportunity["validation_timestamp"] = datetime.now().isoformat()

        # Add constraint violation details if disqualified
        if function_count >= 4:
            opportunity["violation_reason"] = f"{function_count} core functions exceed maximum of 3"
            opportunity["total_score"] = 0
            opportunity["validation_status"] = f"DISQUALIFIED ({function_count} functions)"
        else:
            opportunity["validation_status"] = f"APPROVED ({function_count} functions)"

        # Yield opportunity (DLT will normalize and load)
        yield opportunity


def _extract_core_functions(opportunity: dict[str, Any]) -> list[str]:
    """
    Extract core functions from app opportunity definition.

    Priority order:
    1. function_list field (already a list)
    2. core_functions field (JSON string - standardized format)
    3. core_functions field (integer count, legacy format)
    4. app_description (parse from text using NLP)

    Args:
        opportunity: App opportunity dictionary

    Returns:
        List of core function names
    """
    # Priority 1: function_list field (already a list)
    if "function_list" in opportunity and isinstance(opportunity["function_list"], list):
        return opportunity["function_list"]

    # Priority 2: core_functions field (JSON string - standardized format)
    elif "core_functions" in opportunity and isinstance(opportunity["core_functions"], str):
        # Standardized JSON format
        return deserialize_core_functions(opportunity["core_functions"])

    # Priority 3: core_functions field (integer count - legacy format)
    elif "core_functions" in opportunity and isinstance(opportunity["core_functions"], int):
        # Legacy integer count, generate placeholder functions
        return [f"function_{i+1}" for i in range(opportunity["core_functions"])]

    else:
        # Fallback: extract from description
        text = opportunity.get("app_description", "")
        return _parse_functions_from_text(text)


def _calculate_simplicity_score(function_count: int) -> float:
    """
    Calculate simplicity score using methodology formula.

    Scoring:
    - 1 function = 100 points (maximum)
    - 2 functions = 85 points
    - 3 functions = 70 points
    - 4+ functions = 0 points (automatic disqualification)

    Args:
        function_count: Number of core functions

    Returns:
        float: Simplicity score (0-100)
    """
    if function_count == 1:
        return 100.0
    elif function_count == 2:
        return 85.0
    elif function_count == 3:
        return 70.0
    else:
        return 0.0  # Automatic disqualification for 4+ functions


def _parse_functions_from_text(text: str) -> list[str]:
    """
    Parse core functions from app description text using NLP patterns.

    Identifies function descriptions using common patterns:
    - Action verbs followed by objects
    - Bullet points or numbered lists
    - "allows users to", "enables", "provides" patterns

    Args:
        text: App description text

    Returns:
        List of extracted function names
    """
    if not text or len(text.strip()) == 0:
        return []

    # Common function indicator patterns
    patterns = [
        # Bullet points or numbered lists
        r'[•\-\*]\s*([A-Z][^.!?]{10,50})',
        r'\d+\.\s*([A-Z][^.!?]{10,50})',

        # "Allows users to", "Enables", "Provides"
        r'(?:allows|lets|enables|provides|helps)\s+(?:users\s+to\s+)?([^.!?]{10,60})',
        r'(?:can|will)\s+([^.!?]{10,60})',

        # Verb-noun patterns
        r'\b(track|monitor|track|calculate|generate|create|manage|organize|analyze|calculate|compare|schedule|remind|notify|share|export|import|sync|backup|restore|edit|update|delete|search|filter|sort|view|display)\b\s+([^.!?]{5,40})',
    ]

    functions = []
    text_lower = text.lower()

    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Take the second part for verb-noun patterns
                function = match[1].strip()
            else:
                function = match.strip()

            # Clean and validate function
            function = re.sub(r'\s+', ' ', function)  # Normalize whitespace
            if len(function) > 5 and function not in [f.lower() for f in functions]:
                functions.append(function.title())

    # If no functions found, return empty list
    if not functions:
        return []

    # Limit to maximum 3 functions (anything more will be disqualified)
    return functions[:3]
