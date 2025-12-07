"""
Utility functions for Agno multi-agent analysis field handling

This module provides helper functions for extracting, transforming,
and formatting Agno field data for persistence and analysis.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json
import logging

from .agno_validators import AgnoFieldValidator

logger = logging.getLogger(__name__)


class AgnoFieldExtractor:
    """Extracts Agno field values from agent results"""

    # Score key mappings for different agent types
    SCORE_KEY_MAPPINGS = {
        'wtp': ['wtp_score', 'payment_willingness', 'willingness_to_pay'],
        'segment': ['market_demand_score', 'segment_confidence', 'market_potential'],
        'price': ['monetization_score', 'price_sensitivity_score', 'pricing_potential'],
        'behavior': ['pain_intensity_score', 'payment_behavior_score', 'behavior_analysis']
    }

    # Default scores when agent data is missing
    DEFAULT_SCORE = 50.0

    @classmethod
    def extract_score(cls, agent_data: Dict[str, Any], agent_type: str) -> float:
        """
        Extract score from agent data using key mappings

        Args:
            agent_data: Raw agent response data
            agent_type: Type of agent (wtp, segment, price, behavior)

        Returns:
            Extracted score or default value
        """
        if not agent_data or agent_data.get('error'):
            return cls.DEFAULT_SCORE

        # Try possible score keys for this agent type
        score_keys = cls.SCORE_KEY_MAPPINGS.get(agent_type, [f'{agent_type}_score'])

        for key in score_keys:
            if key in agent_data:
                try:
                    score = float(agent_data[key])
                    # Validate score range
                    if 0.0 <= score <= 100.0:
                        return score
                    else:
                        logger.warning(f"Score {score} out of range for {agent_type} agent, using default")
                        return cls.DEFAULT_SCORE
                except (ValueError, TypeError):
                    continue

        logger.debug(f"No valid score found for {agent_type} agent, using default")
        return cls.DEFAULT_SCORE

    @classmethod
    def extract_segment_type(cls, agent_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract segment type from agent data

        Args:
            agent_data: Raw agent response data

        Returns:
            Extracted segment type or None
        """
        if not agent_data or agent_data.get('error'):
            return None

        # Try possible field names
        for key in ['segment_type', 'market_segment', 'target_segment', 'audience_type']:
            if key in agent_data and agent_data[key]:
                return str(agent_data[key]).strip().title()

        return None

    @classmethod
    def extract_validation_status(cls, market_research_data: Dict[str, Any]) -> str:
        """
        Extract validation status from market research agent

        Args:
            market_research_data: Market research agent response

        Returns:
            Validation status string
        """
        if not market_research_data or market_research_data.get('error'):
            return 'not_run'

        # Check for explicit validation status
        for key in ['validation_status', 'status', 'validation_result']:
            if key in market_research_data:
                return str(market_research_data[key]).lower()

        # Determine status from other fields
        if market_research_data.get('validation_score', 0) >= 70:
            return 'validated'
        elif market_research_data.get('validation_score', 0) > 0:
            return 'pending'
        else:
            return 'failed'

    @classmethod
    def build_agent_metadata(cls, agent_results: Dict[str, Dict], analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build structured metadata from agent results

        Args:
            agent_results: Dictionary of all agent responses
            analysis_config: Configuration used for analysis

        Returns:
            Structured metadata dictionary
        """
        metadata = {
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'agents_run': list(agent_results.keys()),
            'agent_success_count': sum(1 for agent in agent_results.values() if not agent.get('error')),
            'model_used': analysis_config.get('model', 'unknown'),
            'subreddit_multiplier': analysis_config.get('subreddit_multiplier', 1.0)
        }

        # Add market research info if available
        market_research = agent_results.get('market_research', {})
        if market_research and not market_research.get('error'):
            metadata['market_research'] = {
                'validation_score': market_research.get('validation_score', 0.0),
                'competitors_analyzed': len(market_research.get('competitor_pricing', [])),
                'market_size_found': 'market_size' in market_research,
                'market_validation': cls.extract_validation_status(market_research)
            }

        # Add error summary if any agents failed
        failed_agents = [agent for agent, data in agent_results.items() if data.get('error')]
        if failed_agents:
            metadata['failed_agents'] = failed_agents

        return metadata


class AgnoFieldTransformer:
    """Transforms Agno fields between different formats"""

    @classmethod
    def prepare_for_db_storage(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare Agno fields for database storage

        Args:
            data: Raw Agno field data

        Returns:
            Data ready for database insertion
        """
        prepared = data.copy()

        # Convert metadata to JSON if present
        if 'agno_agent_metadata' in prepared and prepared['agno_agent_metadata']:
            if isinstance(prepared['agno_agent_metadata'], dict):
                prepared['agno_agent_metadata'] = json.dumps(prepared['agno_agent_metadata'])
            elif isinstance(prepared['agno_agent_metadata'], str):
                # Already a string, ensure it's valid JSON
                try:
                    json.loads(prepared['agno_agent_metadata'])
                except json.JSONDecodeError:
                    # Invalid JSON, convert to string representation
                    prepared['agno_agent_metadata'] = json.dumps(str(prepared['agno_agent_metadata']))

        # Handle None values for database compatibility
        agno_fields = [
            'agno_wtp_score', 'agno_segment_confidence', 'agno_price_potential',
            'agno_behavior_score', 'agno_consensus_confidence',
            'agno_segment_type', 'agno_agents_count', 'agno_analysis_cost_usd',
            'agno_validation_status', 'agno_agent_metadata'
        ]

        for field in agno_fields:
            if field not in prepared or prepared[field] == '':
                prepared[field] = None

        return prepared

    @classmethod
    def prepare_for_api_response(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare Agno fields for API response

        Args:
            data: Raw Agno field data from database

        Returns:
            Data ready for API response
        """
        prepared = data.copy()

        # Parse JSON metadata if present
        if 'agno_agent_metadata' in prepared and prepared['agno_agent_metadata']:
            if isinstance(prepared['agno_agent_metadata'], str):
                try:
                    prepared['agno_agent_metadata'] = json.loads(prepared['agno_agent_metadata'])
                except json.JSONDecodeError:
                    prepared['agno_agent_metadata'] = {'error': 'Invalid JSON in metadata'}

        # Round score fields for cleaner output
        score_fields = [
            'agno_wtp_score', 'agno_segment_confidence', 'agno_price_potential',
            'agno_behavior_score', 'agno_consensus_confidence'
        ]

        for field in score_fields:
            if field in prepared and prepared[field] is not None:
                prepared[field] = round(float(prepared[field]), 1)

        # Round cost field
        if 'agno_analysis_cost_usd' in prepared and prepared['agno_analysis_cost_usd'] is not None:
            prepared['agno_analysis_cost_usd'] = round(float(prepared['agno_analysis_cost_usd']), 6)

        return prepared


class AgnoConsensusCalculator:
    """Calculates consensus metrics from agent results"""

    @classmethod
    def calculate_variance_confidence(cls, scores: List[float]) -> float:
        """
        Calculate confidence based on score variance

        Args:
            scores: List of agent scores

        Returns:
            Confidence score (0-100)
        """
        if not scores:
            return 0.0

        if len(scores) == 1:
            return 100.0  # Perfect confidence with single score

        # Calculate variance
        mean = sum(scores) / len(scores)
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)

        # Convert variance to confidence (lower variance = higher confidence)
        # Map variance (0-2500) to confidence (100-0)
        max_variance = 2500  # Max possible variance for scores 0-100
        confidence = max(0, min(100, 100 - (variance / max_variance) * 100))

        return round(confidence, 1)

    @classmethod
    def calculate_agreement_score(cls, scores: List[float], tolerance: float = 10.0) -> float:
        """
        Calculate agreement score based on how close scores are to each other

        Args:
            scores: List of agent scores
            tolerance: Maximum acceptable difference for agreement

        Returns:
            Agreement score (0-100)
        """
        if not scores or len(scores) == 1:
            return 100.0

        # Count pairs that agree within tolerance
        agreements = 0
        total_pairs = len(scores) * (len(scores) - 1) // 2

        for i in range(len(scores)):
            for j in range(i + 1, len(scores)):
                if abs(scores[i] - scores[j]) <= tolerance:
                    agreements += 1

        return round((agreements / total_pairs) * 100, 1) if total_pairs > 0 else 0.0

    @classmethod
    def calculate_weighted_consensus(cls, agent_scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """
        Calculate weighted consensus from agent scores

        Args:
            agent_scores: Dictionary of agent scores
            weights: Dictionary of agent weights

        Returns:
            Weighted consensus score (0-100)
        """
        if not agent_scores:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for agent_type, score in agent_scores.items():
            weight = weights.get(agent_type, 1.0)
            total_weight += weight
            weighted_sum += score * weight

        if total_weight == 0.0:
            return 0.0

        return round(weighted_sum / total_weight, 1)


def extract_agno_fields_from_agent_results(agent_results: Dict[str, Dict], analysis_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all Agno fields from raw agent results

    Args:
        agent_results: Dictionary of agent responses
        analysis_config: Analysis configuration

    Returns:
        Dictionary of extracted Agno fields
    """
    extractor = AgnoFieldExtractor()
    validator = AgnoFieldValidator()

    # Extract individual agent scores
    agno_fields = {
        'agno_wtp_score': extractor.extract_score(agent_results.get('wtp', {}), 'wtp'),
        'agno_segment_confidence': extractor.extract_score(agent_results.get('segment', {}), 'segment'),
        'agno_price_potential': extractor.extract_score(agent_results.get('price', {}), 'price'),
        'agno_behavior_score': extractor.extract_score(agent_results.get('behavior', {}), 'behavior'),
        'agno_segment_type': extractor.extract_segment_type(agent_results.get('segment', {})),
        'agno_validation_status': extractor.extract_validation_status(agent_results.get('market_research', {}))
    }

    # Calculate consensus metrics
    score_fields = ['agno_wtp_score', 'agno_segment_confidence', 'agno_price_potential', 'agno_behavior_score']
    scores = [agno_fields[field] for field in score_fields if agno_fields[field] is not None]

    if scores:
        consensus_calc = AgnoConsensusCalculator()
        agno_fields['agno_consensus_confidence'] = consensus_calc.calculate_variance_confidence(scores)

    # Count successful agents
    agno_fields['agno_agents_count'] = sum(1 for agent in agent_results.values() if not agent.get('error'))

    # Extract cost
    agno_fields['agno_analysis_cost_usd'] = analysis_config.get('cost_usd', 0.002)

    # Build metadata
    agno_fields['agno_agent_metadata'] = extractor.build_agent_metadata(agent_results, analysis_config)

    # Validate all fields
    try:
        agno_fields = validator.validate_all_agno_fields(agno_fields)
        validator.validate_field_consistency(agno_fields)
    except ValueError as e:
        logger.warning(f"Agno field validation failed: {e}")
        # Continue with validation errors, but log them

    return agno_fields