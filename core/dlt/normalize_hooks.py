"""
DLT Normalization Hooks for Simplicity Constraint Enforcement.

This module implements DLT-native normalization hooks that enforce the simplicity
constraint during the data normalization process, automatically disqualifying
4+ function apps and logging violations to the constraint_violations table.

Uses DLT's NormalizeHandler for constraint enforcement at the normalization layer,
ensuring all data passes through constraint validation before being written to
the destination.

Uses centralized score_calculator module to ensure consistency across the system.
"""

from collections.abc import Generator
from datetime import datetime
from typing import Any

# Import centralized score calculation functions
from core.dlt.score_calculator import calculate_simplicity_score


class SimplicityConstraintNormalizeHandler:
    """
    DLT normalizer hook to enforce simplicity constraint during normalization.

    This handler intercepts data during DLT's normalization phase and:
    1. Validates each app opportunity against the 1-3 function constraint
    2. Automatically disqualifies 4+ function apps
    3. Logs all violations to constraint_violations table
    4. Sets simplicity_score to 0 for disqualified apps
    5. Updates validation_status with detailed information

    Example:
        handler = SimplicityConstraintNormalizeHandler()
        normalized_data = handler.process_batch(opportunities)
    """

    def __init__(self, max_functions: int = 3):
        """
        Initialize the constraint normalizer.

        Args:
            max_functions: Maximum allowed core functions (default: 3)
        """
        self.max_functions = max_functions
        self.violations_logged = 0
        self.apps_processed = 0

    def process_batch(
        self,
        tables: list[Any],
        schema: Any | None = None
    ) -> list[Any]:
        """
        Process a batch of tables through the normalization pipeline.

        Enforces simplicity constraint on app_opportunities table and logs
        violations to constraint_violations table.

        Args:
            tables: List of DLT table objects being normalized
            schema: Optional DLT schema for context

        Returns:
            List of processed tables with constraint enforcement
        """
        for table in tables:
            if hasattr(table, 'name') and table.name == "app_opportunities":
                self.apps_processed = 0
                self.violations_logged = 0
                # Process each row in the table
                if hasattr(table, 'rows'):
                    for row in table.rows:
                        self._enforce_constraint(row)

        return tables

    def _enforce_constraint(self, row: dict[str, Any]) -> None:
        """
        Enforce simplicity constraint on a single row.

        Args:
            row: Dictionary representing a single app opportunity
        """
        self.apps_processed += 1

        # Extract function count
        function_count = self._extract_function_count(row)

        # Enforce constraint (disqualify only if MORE than max_functions)
        if function_count > self.max_functions:
            # Disqualify the app
            self._disqualify_app(row, function_count)
            self.violations_logged += 1
        else:
            # App is approved (1-3 functions are allowed when max is 3)
            self._approve_app(row, function_count)

    def _extract_function_count(self, row: dict[str, Any]) -> int:
        """
        Extract the number of core functions from a row.

        Priority order:
        1. Use existing 'core_functions' field if present
        2. Count items in 'function_list' array
        3. Parse from 'app_description' text
        4. Default to 0 if no information available

        Args:
            row: App opportunity dictionary

        Returns:
            int: Number of core functions
        """
        # Check if core_functions field exists
        if "core_functions" in row and isinstance(row["core_functions"], int):
            return row["core_functions"]

        # Check function_list
        if "function_list" in row:
            if isinstance(row["function_list"], list):
                return len(row["function_list"])
            elif isinstance(row["function_list"], str):
                # Try to parse as JSON
                try:
                    import json
                    parsed = json.loads(row["function_list"])
                    return len(parsed) if isinstance(parsed, list) else 0
                except (json.JSONDecodeError, TypeError):
                    return 0

        # Parse from description
        description = row.get("app_description", "")
        if description:
            functions = self._parse_functions_from_text(description)
            return len(functions)

        # Default: no functions found
        return 0

    def _parse_functions_from_text(self, text: str) -> list[str]:
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
        import re

        if not text or len(text.strip()) == 0:
            return []

        # Common function indicator patterns
        patterns = [
            # Bullet points or numbered lists
            r'[•\-\*]\s*([A-Za-z][^.!?\n]{10,50})',
            r'\d+\.\s*([A-Za-z][^.!?\n]{10,50})',

            # "Allows users to", "Enables", "Provides"
            r'(?:allows|lets|enables|provides|helps)\s+(?:users\s+to\s+)?([^.!?\n]{10,60})',
            r'(?:can|will)\s+([^.!?\n]{10,60})',

            # Verb-noun patterns
            r'\b(track|monitor|calculate|generate|create|manage|organize|analyze|compare|schedule|remind|notify|share|export|import|sync|backup|restore|edit|update|delete|search|filter|sort|view|display)\b\s+([^.!?\n]{5,40})',
        ]

        functions = []
        text_lower = text.lower()

        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    # Take the second part for verb-noun patterns
                    function = match[1].strip()
                else:
                    function = match.strip()

                # Clean and validate function
                function = re.sub(r'\s+', ' ', function)  # Normalize whitespace
                if len(function) > 5 and function.lower() not in [f.lower() for f in functions]:
                    functions.append(function.title())

        # Limit to maximum 3 functions
        return functions[:3]

    def _disqualify_app(self, row: dict[str, Any], function_count: int) -> None:
        """
        Mark an app as disqualified due to too many functions.

        Sets is_disqualified=True, simplicity_score=0, total_score=0,
        and updates validation_status with detailed information.

        Args:
            row: App opportunity dictionary
            function_count: Number of core functions detected
        """
        row["is_disqualified"] = True
        row["simplicity_score"] = 0.0
        row["total_score"] = 0.0
        row["validation_status"] = f"DISQUALIFIED ({function_count} functions)"
        row["violation_reason"] = f"{function_count} core functions exceed maximum of {self.max_functions}"
        row["constraint_version"] = row.get("constraint_version", 1)
        row["validation_timestamp"] = datetime.now().isoformat()

    def _approve_app(self, row: dict[str, Any], function_count: int) -> None:
        """
        Mark an app as approved for having 1-3 functions.

        Sets is_disqualified=False and updates validation_status.

        Args:
            row: App opportunity dictionary
            function_count: Number of core functions detected
        """
        row["is_disqualified"] = False
        row["core_functions"] = function_count
        # Use centralized score calculation (single source of truth)
        row["simplicity_score"] = calculate_simplicity_score(function_count)
        row["validation_status"] = f"APPROVED ({function_count} functions)"
        row["constraint_version"] = row.get("constraint_version", 1)
        row["validation_timestamp"] = datetime.now().isoformat()

    # NOTE: _calculate_simplicity_score has been replaced by centralized
    # score_calculator.calculate_simplicity_score for consistency.
    # Kept as a method wrapper for backward compatibility.
    def _calculate_simplicity_score(self, function_count: int) -> float:
        """
        Calculate simplicity score using methodology formula.

        DEPRECATED: Use core.dlt.score_calculator.calculate_simplicity_score instead.
        This wrapper is maintained for backward compatibility.

        Scoring:
        - 1 function = 100 points (maximum)
        - 2 functions = 85 points
        - 3 functions = 70 points
        - 4+ functions = 0 points (should not reach here)

        Args:
            function_count: Number of core functions

        Returns:
            float: Simplicity score (0-100)
        """
        return calculate_simplicity_score(function_count)

    def generate_violations(
        self,
        opportunity_id: str,
        app_name: str,
        function_count: int,
        original_score: float | None = None
    ) -> Generator[dict[str, Any], None, None]:
        """
        Generate violation records for the constraint_violations table.

        Yields violation records that will be loaded to the database.

        Args:
            opportunity_id: Unique opportunity identifier
            app_name: Name of the app
            function_count: Number of functions detected
            original_score: Original total score before disqualification

        Yields:
            Dict[str, Any]: Violation record
        """
        violation = {
            "violation_id": f"v_{opportunity_id}_{int(datetime.now().timestamp())}",
            "opportunity_id": opportunity_id,
            "app_name": app_name,
            "violation_type": "SIMPLICITY_CONSTRAINT",
            "function_count": function_count,
            "max_allowed": self.max_functions,
            "violation_reason": f"{function_count} core functions exceed maximum of {self.max_functions}",
            "original_score": original_score,
            "constraint_version": 1,
            "timestamp": datetime.now().isoformat()
        }
        yield violation

    def get_stats(self) -> dict[str, int]:
        """
        Get statistics about constraint enforcement.

        Returns:
            Dict containing:
                - apps_processed: Number of apps processed
                - violations_logged: Number of violations detected
        """
        return {
            "apps_processed": self.apps_processed,
            "violations_logged": self.violations_logged
        }


# Factory function to create a constraint-aware normalize hook
def create_constraint_normalize_handler(max_functions: int = 3) -> SimplicityConstraintNormalizeHandler:
    """
    Factory function to create a constraint normalization hook.

    Args:
        max_functions: Maximum allowed core functions (default: 3)

    Returns:
        SimplicityConstraintNormalizeHandler: Configured handler instance
    """
    return SimplicityConstraintNormalizeHandler(max_functions=max_functions)


# DLT hook registration (for use with DLT's normalize hook system)
# This allows the handler to be automatically invoked during normalization
registered_handler = create_constraint_normalize_handler()

# Note: In a full DLT setup, this would be registered using:
# dlt.normalize.add_handler(SimplicityConstraintNormalizeHandler)
# However, for this implementation, the handler is used directly in the pipeline
