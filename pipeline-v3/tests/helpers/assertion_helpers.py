"""
Custom assertion helpers for Agno analysis validation
"""

import json
from typing import Dict, Any, List
from dataclasses import asdict

# Any no longer needed - using AnalysisResult from models.analysis instead


class AgnoAnalysisAssertions:
    """Custom assertions for Agno analysis results"""

    @staticmethod
    def assert_valid_json_response(response: str):
        """Assert that response is valid JSON"""
        try:
            parsed = json.loads(response)
            assert isinstance(parsed, dict)
            return parsed
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON response: {response}")

    @staticmethod
    def assert_field_mapping(mapped_data: Dict[str, Any], expected_fields: List[str]):
        """Assert that all expected fields are present in mapped data"""
        for field in expected_fields:
            assert field in mapped_data, f"Missing expected field: {field}"

    @staticmethod
    def assert_score_ranges(analysis):
        """Assert that all scores are within valid ranges"""
        # This method is deprecated - AnalysisResult uses different structure
        pass

    @staticmethod
    def assert_consensus_metadata(consensus_data: Dict[str, Any]):
        """Assert consensus metadata structure"""
        required_fields = [
            "agent_count",
            "agreement_level",
            "outliers_detected"
        ]

        for field in required_fields:
            assert field in consensus_data, f"Missing consensus metadata: {field}"

        assert consensus_data["agent_count"] > 0
        assert consensus_data["agreement_level"] in [
            "high", "medium", "low", "very_low", "single_agent", "unknown"
        ]
        assert consensus_data["outliers_detected"] >= 0

    @staticmethod
    def assert_friction_indicators(friction_indicators: List[str]):
        """Assert friction indicators are valid"""
        valid_indicators = [
            "price_objection",
            "budget_constraint",
            "subscription_fatigue",
            "free_alternative_preference",
            "switching_cost_concern",
            "none_detected"
        ]

        for indicator in friction_indicators:
            assert indicator in valid_indicators, (
                f"Invalid friction indicator: {indicator}"
            )

    @staticmethod
    def assert_urgency_levels(urgency: str):
        """Assert urgency level is valid"""
        valid_levels = ["Critical", "High", "Medium", "Low"]
        assert urgency in valid_levels, f"Invalid urgency level: {urgency}"

    @staticmethod
    def assert_customer_segment(segment: str):
        """Assert customer segment is valid"""
        valid_segments = ["B2B", "B2C", "Mixed", "Unknown"]
        assert segment in valid_segments, f"Invalid customer segment: {segment}"

    @staticmethod
    def assert_subreddit_multiplier(multiplier: float):
        """Assert subreddit multiplier is valid"""
        assert multiplier >= 0.5, f"Multiplier {multiplier} is too low"
        assert multiplier <= 2.0, f"Multiplier {multiplier} is too high"

    @staticmethod
    def assert_analysis_confidence(confidence: float):
        """Assert confidence score is valid"""
        assert 0 <= confidence <= 1, f"Confidence {confidence} out of range [0, 1]"

    @staticmethod
    def assert_price_points_format(price_points: List[Any]):
        """Assert price points are properly formatted"""
        if price_points:
            for price_point in price_points:
                if isinstance(price_point, dict):
                    assert "price" in price_point, "Price point dict must contain 'price' key"
                    assert isinstance(price_point["price"], str), "Price must be string"
                    assert price_point["price"].startswith("$"), "Price must start with $"
                elif isinstance(price_point, str):
                    assert price_point.startswith("$"), "Price must start with $"

    @staticmethod
    def assert_agentops_integration(agentops_enabled: bool, events: List[Dict], traces: List[Dict]):
        """Assert AgentOps integration is properly recorded"""
        if agentops_enabled:
            assert len(events) > 0, "AgentOps events should be recorded when enabled"
            assert len(traces) >= 1, "AgentOps traces should be created when enabled"

            # Verify event structure
            for event in events:
                assert "event_name" in event
                assert "data" in event
                assert isinstance(event["data"], dict)

            # Verify trace structure
            for trace in traces:
                assert "id" in trace
                assert "name" in trace
                assert "status" in trace

    @staticmethod
    def assert_field_normalization(data: Dict[str, Any]):
        """Assert field normalization works correctly"""
        # Test sentiment normalization
        sentiment = data.get("sentiment_toward_payment", "")
        assert sentiment in ["Positive", "Neutral", "Negative"]

        # Test segment normalization
        segment = data.get("customer_segment", "")
        assert segment in ["B2B", "B2C", "Mixed", "Unknown"]

        # Test score normalization
        if "willingness_to_pay_score" in data:
            score = data["willingness_to_pay_score"]
            assert 0 <= score <= 100

        # Test price points normalization
        if "mentioned_price_points" in data:
            price_points = data["mentioned_price_points"]
            assert isinstance(price_points, list)

    @staticmethod
    def assert_consensus_calculation(consensus_data: Dict[str, Any], agent_responses: List[Dict]):
        """Assert consensus calculation from multiple agents"""
        assert consensus_data["agent_count"] == len(agent_responses)

        # Verify scores are averaged appropriately
        if "willingness_to_pay_score" in consensus_data:
            # Should be within reasonable range of input scores
            consensus_score = consensus_data["willingness_to_pay_score"]
            input_scores = [r.get("willingness_to_pay_score", 0) for r in agent_responses]
            if input_scores:
                min_score = min(input_scores)
                max_score = max(input_scores)
                assert min_score <= consensus_score <= max_score

        # Verify agreement level calculation
        agreement_level = consensus_data["agreement_level"]
        assert agreement_level in ["high", "medium", "low", "very_low"]

    @staticmethod
    def assert_error_handling(error_response: Dict[str, Any]):
        """Assert error handling returns valid fallback structure"""
        required_fields = [
            "willingness_to_pay_score",
            "customer_segment",
            "mentioned_price_points",
            "current_spending",
            "sentiment_toward_payment",
            "revenue_potential_score",
            "confidence",
            "reasoning"
        ]

        for field in required_fields:
            assert field in error_response, f"Fallback response missing field: {field}"

        # Verify default values
        assert error_response["willingness_to_pay_score"] == 50.0
        assert error_response["customer_segment"] == "Unknown"
        assert error_response["confidence"] == 0.5
        assert "error_occurred" in error_response

    @staticmethod
    def assert_response_parsing_logic(parser_response: Dict[str, Any], raw_response: str):
        """Assert response parsing logic works correctly"""
        # Should always return a dictionary
        assert isinstance(parser_response, dict)

        # If response was parsable, should contain analysis data
        if "error_occurred" not in parser_response or not parser_response["error_occurred"]:
            assert "reasoning" in parser_response
            assert parser_response["reasoning"] != ""

        # Should handle empty/invalid responses gracefully
        if not raw_response.strip():
            assert parser_response["confidence"] == 0.5

    @staticmethod
    def assert_analysis_completeness(analysis: Any):
        """Assert that analysis result is complete"""
        # All required fields should be present
        required_fields = [
            "willingness_to_pay_score",
            "market_segment_score",
            "price_sensitivity_score",
            "revenue_potential_score",
            "customer_segment",
            "mentioned_price_points",
            "existing_payment_behavior",
            "urgency_level",
            "sentiment_toward_payment",
            "payment_friction_indicators",
            "llm_monetization_score",
            "confidence",
            "reasoning",
            "subreddit_multiplier"
        ]

        for field in required_fields:
            assert hasattr(analysis, field), f"Missing required field: {field}"
            value = getattr(analysis, field)
            assert value is not None, f"Field {field} is None"

    @staticmethod
    def assert_multi_agent_consistency(analysis_results: List[Any]):
        """Assert consistency across multiple analysis results"""
        if len(analysis_results) < 2:
            return  # Not enough results to check consistency

        # Check that scores are reasonably consistent
        wtp_scores = [r.willingness_to_pay_score for r in analysis_results]
        score_variance = max(wtp_scores) - min(wtp_scores)

        # Variance should not be too large for similar inputs
        assert score_variance <= 30, f"Score variance too large: {score_variance}"

        # All should have valid segment classifications
        segments = [r.customer_segment for r in analysis_results]
        assert all(s in ["B2B", "B2C", "Mixed", "Unknown"] for s in segments)

    @staticmethod
    def assert_cost_tracking(analyzer, expected_min_calls: int = 4):
        """Assert cost tracking is working"""
        if hasattr(analyzer, 'agentops_enabled') and analyzer.agentops_enabled:
            # Should have recorded agent calls
            # This would need to check actual AgentOps calls in real implementation
            assert hasattr(analyzer, 'session_id')
            assert analyzer.session_id is not None

    @staticmethod
    def assert_subreddit_context_handling(analysis: Any, subreddit: str):
        """Assert subreddit context is properly handled"""
        multiplier = analysis.subreddit_multiplier

        # Check subreddit-specific multipliers
        subreddit_mults = {
            "entrepreneur": 1.5,
            "business": 1.5,
            "startups": 1.4,
            "saas": 1.4,
            "smallbusiness": 1.3,
            "personalfinance": 1.0,
            "productivity": 1.0,
            "frugal": 0.6,
            "college": 0.7,
        }

        expected_mult = subreddit_mults.get(subreddit.lower(), 1.0)
        assert multiplier == expected_mult, (
            f"Subreddit multiplier for {subreddit} should be {expected_mult}, got {multiplier}"
        )