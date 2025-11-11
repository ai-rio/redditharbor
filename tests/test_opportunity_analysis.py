"""
Test Opportunity Analysis Functionality

Unit tests for the monetizable app opportunity research methodology
"""

import json
import sys
from pathlib import Path

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.research_monetizable_opportunities import OpportunityAnalyzer


class TestOpportunityAnalyzer:
    """Test the OpportunityAnalyzer class functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = OpportunityAnalyzer()

    def test_analyzer_initialization(self):
        """Test that analyzer initializes with correct configurations"""
        assert hasattr(self.analyzer, 'pain_indicators')
        assert hasattr(self.analyzer, 'solution_seekers')
        assert hasattr(self.analyzer, 'monetization_signals')
        assert hasattr(self.analyzer, 'market_segments')

        # Check that market segments are properly configured
        expected_segments = [
            "Health & Fitness",
            "Finance & Investing",
            "Education & Career",
            "Travel & Experiences",
            "Real Estate",
            "Technology & SaaS Productivity"
        ]
        for segment in expected_segments:
            assert segment in self.analyzer.market_segments

    def test_calculate_opportunity_score_basic(self):
        """Test basic opportunity scoring functionality"""
        text = "I'm frustrated with the current fitness apps. They are too expensive and complicated. Looking for alternatives."
        engagement_metrics = {
            'score': 500,  # Medium engagement
            'num_comments': 25
        }

        result = self.analyzer.calculate_opportunity_score(text, engagement_metrics)

        # Check that all required score components are present
        required_keys = [
            'total_score', 'market_demand_score', 'pain_intensity_score',
            'monetization_potential_score', 'solution_score',
            'pain_mentions', 'solution_mentions', 'monetization_mentions'
        ]
        for key in required_keys:
            assert key in result

        # Check that scores are within expected ranges
        assert 0 <= result['total_score'] <= 100
        assert 0 <= result['market_demand_score'] <= 100
        assert 0 <= result['pain_intensity_score'] <= 100
        assert 0 <= result['monetization_potential_score'] <= 100

        # Should detect pain indicators
        assert result['pain_mentions'] > 0

    def test_calculate_opportunity_score_with_pain_language(self):
        """Test scoring with strong pain indicators"""
        text = "This is terrible, frustrating, and completely broken. I hate this problem. It's so annoying and difficult."
        engagement_metrics = {'score': 100, 'num_comments': 10}

        result = self.analyzer.calculate_opportunity_score(text, engagement_metrics)

        # Should detect multiple pain indicators
        assert result['pain_mentions'] >= 3
        assert result['pain_intensity_score'] > 20  # Should be higher due to pain language

    def test_calculate_opportunity_score_with_monetization_signals(self):
        """Test scoring with monetization signals"""
        text = "I'm willing to pay for a premium version. A subscription would be worth it for this solution."
        engagement_metrics = {'score': 100, 'num_comments': 10}

        result = self.analyzer.calculate_opportunity_score(text, engagement_metrics)

        # Should detect monetization signals
        assert result['monetization_mentions'] > 0
        assert result['monetization_potential_score'] > 0

    def test_calculate_opportunity_score_with_solution_seeking(self):
        """Test scoring with solution seeking language"""
        text = "Looking for recommendations. Can anyone suggest alternatives? What do you use for this problem?"
        engagement_metrics = {'score': 100, 'num_comments': 10}

        result = self.analyzer.calculate_opportunity_score(text, engagement_metrics)

        # Should detect solution seeking language
        assert result['solution_mentions'] > 0
        assert result['solution_score'] > 0

    def test_categorize_opportunity(self):
        """Test opportunity categorization based on scores"""
        # Test high priority
        category = self.analyzer.categorize_opportunity(90)
        assert category == "High Priority - Immediate Development"

        # Test medium-high priority
        category = self.analyzer.categorize_opportunity(75)
        assert category == "Medium-High Priority - Strong Candidate"

        # Test medium priority
        category = self.analyzer.categorize_opportunity(60)
        assert category == "Medium Priority - Viable with Refinement"

        # Test low priority
        category = self.analyzer.categorize_opportunity(45)
        assert category == "Low Priority - Monitor for Future"

        # Test not recommended
        category = self.analyzer.categorize_opportunity(25)
        assert category == "Not Recommended"

    def test_analyze_segment_opportunities_valid_segment(self):
        """Test analyzing opportunities for a valid segment"""
        segment_name = "Technology & SaaS Productivity"

        result = self.analyzer.analyze_segment_opportunities(segment_name)

        # Check result structure
        assert "error" not in result
        assert result["segment_name"] == segment_name
        assert "subreddits_analyzed" in result
        assert "monetization_models" in result
        assert isinstance(result["subreddits_analyzed"], list)
        assert isinstance(result["monetization_models"], list)

    def test_analyze_segment_opportunities_invalid_segment(self):
        """Test analyzing opportunities for an invalid segment"""
        segment_name = "Invalid Segment"

        result = self.analyzer.analyze_segment_opportunities(segment_name)

        # Should return error
        assert "error" in result
        assert "Unknown segment" in result["error"]

    def test_generate_research_report_empty_analyses(self):
        """Test research report generation with no analyses"""
        analyses = []

        report = self.analyzer.generate_research_report(analyses)

        # Check report structure
        assert "research_date" in report
        assert "total_segments_analyzed" in report
        assert report["total_segments_analyzed"] == 0
        assert "summary" in report
        assert report["summary"]["total_opportunities_identified"] == 0

    def test_generate_research_report_with_analyses(self):
        """Test research report generation with sample analyses"""
        analyses = [
            {
                "segment_name": "Test Segment 1",
                "opportunities_identified": 5,
                "high_priority_opportunities": [1, 2]
            },
            {
                "segment_name": "Test Segment 2",
                "opportunities_identified": 3,
                "high_priority_opportunities": []
            }
        ]

        report = self.analyzer.generate_research_report(analyses)

        # Check report calculations
        assert report["total_segments_analyzed"] == 2
        assert report["summary"]["total_opportunities_identified"] == 8
        assert report["summary"]["high_priority_opportunities"] == 2
        assert report["summary"]["average_opportunities_per_segment"] == 4.0

    def test_market_segments_configuration(self):
        """Test that market segments are properly configured"""
        for segment_name, config in self.analyzer.market_segments.items():
            # Each segment should have required fields
            assert "subreddits" in config
            assert "monetization_models" in config
            assert isinstance(config["subreddits"], list)
            assert isinstance(config["monetization_models"], list)
            assert len(config["subreddits"]) > 0
            assert len(config["monetization_models"]) > 0

    def test_keyword_patterns_exist(self):
        """Test that keyword patterns are properly defined"""
        # Check that keyword lists are not empty
        assert len(self.analyzer.pain_indicators) > 0
        assert len(self.analyzer.solution_seekers) > 0
        assert len(self.analyzer.monetization_signals) > 0

        # Check that keywords are strings
        for indicator in self.analyzer.pain_indicators:
            assert isinstance(indicator, str)
            assert len(indicator) > 0

        for seeker in self.analyzer.solution_seekers:
            assert isinstance(seeker, str)
            assert len(seeker) > 0

        for signal in self.analyzer.monetization_signals:
            assert isinstance(signal, str)
            assert len(signal) > 0


class TestOpportunityScoringConfig:
    """Test opportunity scoring configuration"""

    def test_scoring_config_file_exists(self):
        """Test that scoring configuration file exists"""
        config_path = project_root / "config" / "opportunity_scoring_config.json"
        assert config_path.exists()

    def test_scoring_config_structure(self):
        """Test that scoring configuration has proper structure"""
        config_path = project_root / "config" / "opportunity_scoring_config.json"

        with open(config_path) as f:
            config = json.load(f)

        # Check main configuration sections
        required_sections = [
            "methodology_version", "scoring_weights", "opportunity_categories",
            "keyword_patterns", "market_segments", "quality_assurance"
        ]
        for section in required_sections:
            assert section in config

        # Check scoring weights structure
        scoring_weights = config["scoring_weights"]
        assert "market_demand" in scoring_weights
        assert "pain_intensity" in scoring_weights
        assert "monetization_potential" in scoring_weights

        # Check that weights sum to 1.0
        total_weight = sum(
            weight_config["weight"]
            for weight_config in scoring_weights.values()
        )
        assert abs(total_weight - 1.0) < 0.01  # Allow for small floating point errors

    def test_opportunity_categories_config(self):
        """Test opportunity categories configuration"""
        config_path = project_root / "config" / "opportunity_scoring_config.json"

        with open(config_path) as f:
            config = json.load(f)

        categories = config["opportunity_categories"]

        # Check that categories have required fields
        for category_name, category_config in categories.items():
            assert "min_score" in category_config
            assert "max_score" in category_config
            assert "label" in category_config
            assert "action" in category_config

            # Check score ranges are valid
            assert 0 <= category_config["min_score"] <= 100
            assert 0 <= category_config["max_score"] <= 100
            assert category_config["min_score"] <= category_config["max_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
