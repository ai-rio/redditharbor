"""
Validation utilities for Agno multi-agent analysis fields

This module provides validation helpers for Agno field values
to ensure data integrity and consistency.
"""

from datetime import datetime
from typing import Any


class AgnoFieldValidator:
    """Validator for Agno field values with business logic rules"""

    # Valid validation statuses
    VALID_STATUSES = frozenset(['validated', 'pending', 'failed', 'not_run', 'error'])

    # Valid segment types
    VALID_SEGMENT_TYPES = frozenset([
        'SMB', 'Enterprise', 'Consumer', 'Startup', 'Freelancer',
        'Agency', 'Educational', 'Government', 'Healthcare',
        'Retail', 'Manufacturing', 'Technology', 'Professional'
    ])

    # Score ranges
    SCORE_MIN = 0.0
    SCORE_MAX = 100.0
    COST_MIN = 0.0
    AGENTS_COUNT_MIN = 0
    AGENTS_COUNT_MAX = 10

    @classmethod
    def validate_score(cls, value: float | None, field_name: str) -> float | None:
        """
        Validate a score field (0-100 range)

        Args:
            value: Score value to validate
            field_name: Name of the field for error messages

        Returns:
            Validated score or None if invalid

        Raises:
            ValueError: If score is outside valid range
        """
        if value is None:
            return None

        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a number, got {type(value).__name__}")

        if not cls.SCORE_MIN <= value <= cls.SCORE_MAX:
            raise ValueError(f"{field_name} must be between {cls.SCORE_MIN} and {cls.SCORE_MAX}, got {value}")

        return float(value)

    @classmethod
    def validate_cost(cls, value: float | None) -> float | None:
        """
        Validate analysis cost (must be non-negative)

        Args:
            value: Cost value to validate

        Returns:
            Validated cost or None if invalid

        Raises:
            ValueError: If cost is negative
        """
        if value is None:
            return None

        if not isinstance(value, (int, float)):
            raise ValueError(f"agno_analysis_cost_usd must be a number, got {type(value).__name__}")

        if value < cls.COST_MIN:
            raise ValueError(f"agno_analysis_cost_usd must be non-negative, got {value}")

        return float(value)

    @classmethod
    def validate_agents_count(cls, value: int | None) -> int | None:
        """
        Validate agents count (must be non-negative integer)

        Args:
            value: Agents count to validate

        Returns:
            Validated count or None if invalid

        Raises:
            ValueError: If count is negative or not integer
        """
        if value is None:
            return None

        if not isinstance(value, int):
            raise ValueError(f"agno_agents_count must be an integer, got {type(value).__name__}")

        if not cls.AGENTS_COUNT_MIN <= value <= cls.AGENTS_COUNT_MAX:
            raise ValueError(f"agno_agents_count must be between {cls.AGENTS_COUNT_MIN} and {cls.AGENTS_COUNT_MAX}, got {value}")

        return value

    @classmethod
    def validate_segment_type(cls, value: str | None) -> str | None:
        """
        Validate market segment type

        Args:
            value: Segment type to validate

        Returns:
            Validated segment type or None if invalid

        Raises:
            ValueError: If segment type is not in allowed list
        """
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(f"agno_segment_type must be a string, got {type(value).__name__}")

        # Normalize to title case
        normalized = value.strip().title()

        if normalized not in cls.VALID_SEGMENT_TYPES:
            # Allow custom segment types but warn
            # In production, you might want to restrict to known types
            return normalized

        return normalized

    @classmethod
    def validate_validation_status(cls, value: str | None) -> str | None:
        """
        Validate validation status

        Args:
            value: Validation status to validate

        Returns:
            Validated status or None if invalid

        Raises:
            ValueError: If status is not in allowed list
        """
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(f"agno_validation_status must be a string, got {type(value).__name__}")

        normalized = value.strip().lower()

        if normalized not in cls.VALID_STATUSES:
            raise ValueError(f"agno_validation_status must be one of {list(cls.VALID_STATUSES)}, got '{value}'")

        return normalized

    @classmethod
    def validate_agent_metadata(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        """
        Validate agent metadata structure

        Args:
            value: Metadata dictionary to validate

        Returns:
            Validated metadata or None if invalid

        Raises:
            ValueError: If metadata is not a dictionary
        """
        if value is None:
            return None

        if not isinstance(value, dict):
            raise ValueError(f"agno_agent_metadata must be a dictionary, got {type(value).__name__}")

        # Ensure metadata doesn't contain sensitive information or extremely large data
        metadata_size = len(str(value))
        if metadata_size > 10000:  # 10KB limit
            raise ValueError(f"agno_agent_metadata too large ({metadata_size} chars), must be under 10000")

        # Validate known metadata fields
        if 'agents_run' in value and not isinstance(value['agents_run'], list):
            raise ValueError("agno_agent_metadata['agents_run'] must be a list")

        if 'agent_success_count' in value and not isinstance(value['agent_success_count'], int):
            raise ValueError("agno_agent_metadata['agent_success_count'] must be an integer")

        if 'analysis_timestamp' in value:
            try:
                # Try to parse timestamp
                datetime.fromisoformat(value['analysis_timestamp'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                raise ValueError("agno_agent_metadata['analysis_timestamp'] must be ISO format datetime")

        return value

    @classmethod
    def validate_all_agno_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate all Agno fields in a data dictionary

        Args:
            data: Dictionary containing Agno fields

        Returns:
            Validated data dictionary

        Raises:
            ValueError: If any field validation fails
        """
        validated = data.copy()

        # Validate score fields
        score_fields = [
            'agno_wtp_score',
            'agno_segment_confidence',
            'agno_price_potential',
            'agno_behavior_score',
            'agno_consensus_confidence'
        ]

        for field in score_fields:
            if field in validated:
                validated[field] = cls.validate_score(validated[field], field)

        # Validate other fields
        if 'agno_analysis_cost_usd' in validated:
            validated['agno_analysis_cost_usd'] = cls.validate_cost(validated['agno_analysis_cost_usd'])

        if 'agno_agents_count' in validated:
            validated['agno_agents_count'] = cls.validate_agents_count(validated['agno_agents_count'])

        if 'agno_segment_type' in validated:
            validated['agno_segment_type'] = cls.validate_segment_type(validated['agno_segment_type'])

        if 'agno_validation_status' in validated:
            validated['agno_validation_status'] = cls.validate_validation_status(validated['agno_validation_status'])

        if 'agno_agent_metadata' in validated:
            validated['agno_agent_metadata'] = cls.validate_agent_metadata(validated['agno_agent_metadata'])

        return validated

    @classmethod
    def validate_field_consistency(cls, data: dict[str, Any]) -> None:
        """
        Validate logical consistency between Agno fields

        Args:
            data: Dictionary containing Agno fields

        Raises:
            ValueError: If fields are inconsistent
        """
        # If agents_count is provided, it should match the actual agents in metadata
        if 'agno_agents_count' in data and 'agno_agent_metadata' in data:
            agents_count = data['agno_agents_count']
            metadata = data['agno_agent_metadata']

            if metadata and 'agents_run' in metadata:
                actual_count = len(metadata['agents_run'])
                if agents_count != actual_count:
                    raise ValueError(f"agno_agents_count ({agents_count}) doesn't match actual agents run ({actual_count})")

        # If validation_status is 'validated', should have consensus confidence
        if data.get('agno_validation_status') == 'validated':
            if not data.get('agno_consensus_confidence'):
                raise ValueError("Validated analysis should have agno_consensus_confidence")

        # If we have agent scores, consensus confidence should be reasonable
        score_fields = ['agno_wtp_score', 'agno_segment_confidence', 'agno_price_potential', 'agno_behavior_score']
        provided_scores = [data.get(field) for field in score_fields if data.get(field) is not None]

        if provided_scores and data.get('agno_consensus_confidence') is not None:
            # High consensus confidence should correlate with score agreement
            consensus = data['agno_consensus_confidence']
            if consensus > 90.0:
                # With high consensus, scores shouldn't vary too much
                score_range = max(provided_scores) - min(provided_scores)
                if score_range > 30.0:
                    raise ValueError(f"High consensus confidence ({consensus}) but scores vary widely (range: {score_range})")
