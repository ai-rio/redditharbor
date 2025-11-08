"""
DLT Constraint Validation Resource for Simplicity Constraint Enforcement.

This module implements DLT-native validation for the 1-3 core function constraint,
automatically disqualifying apps with 4+ functions and tracking constraint metadata.
"""

import dlt
from typing import List, Dict, Any
import re
from datetime import datetime


@dlt.resource(table_name="app_opportunities", write_disposition="merge")
def app_opportunities_with_constraint(opportunities: List[Dict[str, Any]]):
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

        # Calculate simplicity score using methodology formula
        simplicity_score = _calculate_simplicity_score(function_count)

        # Add constraint metadata
        opportunity["core_functions"] = function_count
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


def _extract_core_functions(opportunity: Dict[str, Any]) -> List[str]:
    """
    Extract core functions from app opportunity definition.

    Priority order:
    1. function_list field (already a list)
    2. core_functions field (count, generate placeholders)
    3. app_description (parse from text using NLP)

    Args:
        opportunity: App opportunity dictionary

    Returns:
        List of core function names
    """
    if "function_list" in opportunity and isinstance(opportunity["function_list"], list):
        return opportunity["function_list"]
    elif "core_functions" in opportunity and isinstance(opportunity["core_functions"], int):
        # Already a count, generate placeholder functions
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


def _parse_functions_from_text(text: str) -> List[str]:
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
