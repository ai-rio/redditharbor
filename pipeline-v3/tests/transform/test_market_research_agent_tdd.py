"""
TDD Unit Tests for MarketResearchAgent

Following Test-Driven Development methodology:
1. RED - Write failing tests first
2. GREEN - Implement minimal code to pass tests
3. REFACTOR - Clean up and improve the code

This suite tests MarketResearchAgent functionality in isolation:
- Validation score calculation
- Cost tracking
- Error handling
- Configuration validation
- Data quality assessment
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timezone

# Import the module to test
from transform.market_research_agent import MarketResearchAgent


class TestMarketResearchAgentTDD:
    """TDD Unit Tests for MarketResearchAgent"""

    @pytest.fixture
    def mock_agent(self):
        """Create a MarketResearchAgent with mocked dependencies"""
        with patch('transform.market_research_agent.JINA_AVAILABLE', True):
            with patch('transform.market_research_agent.JinaClient'):
                with patch('transform.market_research_agent.get_jina_cache'):
                    agent = MarketResearchAgent(
                        validation_threshold=70.0,
                        max_competitors=5,
                        max_launches=3,
                        enable_cost_tracking=True,
                        use_real_jina=False  # Use mock implementation for tests
                    )
                    return agent

    @pytest.fixture
    def sample_evidence_data(self):
        """Sample validation evidence data for testing"""
        return {
            "competitor_pricing": [
                {
                    "company_name": "CompetitorA",
                    "pricing_model": "subscription",
                    "pricing_tiers": [
                        {"name": "Basic", "price": "$9/mo"},
                        {"name": "Pro", "price": "$29/mo"}
                    ],
                    "target_market": "SMB",
                    "source_url": "https://competitora.com/pricing",
                    "confidence": 85.0
                },
                {
                    "company_name": "CompetitorB",
                    "pricing_model": "freemium",
                    "pricing_tiers": [
                        {"name": "Free", "price": "$0"},
                        {"name": "Premium", "price": "$19/mo"}
                    ],
                    "target_market": "SMB",
                    "source_url": "https://competitorb.com/pricing",
                    "confidence": 90.0
                }
            ],
            "market_size": {
                "tam_value": "$45B",
                "sam_value": "$4.5B",
                "growth_rate": "18% CAGR",
                "source_name": "Industry Research 2024",
                "source_url": "https://industryresearch.com/report",
                "year": 2024
            },
            "similar_launches": [
                {
                    "product_name": "SimilarApp",
                    "launch_platform": "Product Hunt",
                    "launch_date": "2024-02-15",
                    "upvotes": 1250,
                    "comments": 340,
                    "source_url": "https://producthunt.com/posts/similarapp"
                }
            ]
        }


    class TestValidationScoreCalculation:
        """Test validation score calculation logic"""

        @pytest.mark.asyncio
        async def test_high_validation_score_with_all_evidence(self, mock_agent, sample_evidence_data):
            """Test high validation score when all evidence types are present"""
            # RED Test: This should pass with proper scoring algorithm
            score = mock_agent._calculate_validation_score(
                competitor_pricing=sample_evidence_data["competitor_pricing"],
                market_size=sample_evidence_data["market_size"],
                similar_launches=sample_evidence_data["similar_launches"]
            )

            # Should be high score (80-100) with all evidence types
            assert score >= 80.0, f"Expected high score with all evidence, got {score}"
            assert score <= 100.0, "Score should not exceed 100"

        @pytest.mark.asyncio
        async def test_moderate_validation_score_with_partial_evidence(self, mock_agent, sample_evidence_data):
            """Test moderate validation score with only competitors"""
            score = mock_agent._calculate_validation_score(
                competitor_pricing=sample_evidence_data["competitor_pricing"],
                market_size=None,
                similar_launches=[]
            )

            # Should be moderate (50-80) with only competitor data
            assert 50.0 <= score <= 80.0, f"Expected moderate score with partial evidence, got {score}"

        @pytest.mark.asyncio
        async def test_zero_validation_score_with_no_evidence(self, mock_agent):
            """Test zero validation score when no evidence is present"""
            score = mock_agent._calculate_validation_score(
                competitor_pricing=[],
                market_size=None,
                similar_launches=[]
            )

            assert score == 0.0, "Score should be 0 with no evidence"

        @pytest.mark.asyncio
        async def test_score_weights_applied_correctly(self, mock_agent, sample_evidence_data):
            """Test that evidence is weighted correctly"""
            # Calculate individual contributions
            score_competitors_only = mock_agent._calculate_validation_score(
                competitor_pricing=sample_evidence_data["competitor_pricing"],
                market_size=None,
                similar_launches=[]
            )

            score_market_only = mock_agent._calculate_validation_score(
                competitor_pricing=[],
                market_size=sample_evidence_data["market_size"],
                similar_launches=[]
            )

            score_launches_only = mock_agent._calculate_validation_score(
                competitor_pricing=[],
                market_size=None,
                similar_launches=sample_evidence_data["similar_launches"]
            )

            # Verify weighting is working (billion-dollar markets should have highest score)
            # Sample data includes $45B market, which should score higher than competitors
            assert score_market_only >= score_competitors_only
            assert score_competitors_only >= score_launches_only

        @pytest.mark.asyncio
        async def test_billion_dollar_market_boost(self, mock_agent):
            """Test that billion-dollar markets get score boost"""
            billion_dollar_market = {
                "tam_value": "$100B",
                "sam_value": "$10B",
                "source_name": "Gartner"
            }

            million_dollar_market = {
                "tam_value": "$100M",
                "sam_value": "$10M",
                "source_name": "Unknown"
            }

            score_billion = mock_agent._calculate_validation_score(
                competitor_pricing=[],
                market_size=billion_dollar_market,
                similar_launches=[]
            )

            score_million = mock_agent._calculate_validation_score(
                competitor_pricing=[],
                market_size=million_dollar_market,
                similar_launches=[]
            )

            assert score_billion > score_million, "Billion-dollar market should get higher score"


    class TestDataQualityScore:
        """Test data quality score calculation"""

        @pytest.mark.asyncio
        async def test_high_quality_score_with_reputable_sources(self, mock_agent, sample_evidence_data):
            """Test high quality score with reputable sources"""
            # Add reputable market research source
            sample_evidence_data["market_size"]["source_name"] = "Gartner Research"

            quality_score = mock_agent._calculate_data_quality_score(
                competitor_pricing=sample_evidence_data["competitor_pricing"],
                market_size=sample_evidence_data["market_size"],
                similar_launches=sample_evidence_data["similar_launches"]
            )

            assert quality_score >= 80.0, f"Expected high quality with reputable sources, got {quality_score}"

        @pytest.mark.asyncio
        async def test_medium_quality_score_with_mixed_sources(self, mock_agent, sample_evidence_data):
            """Test medium quality score with mixed source credibility"""
            # Use lower quality market source
            sample_evidence_data["market_size"]["source_name"] = "Random Blog"

            # Reduce competitor confidence
            sample_evidence_data["competitor_pricing"][0]["confidence"] = 60.0
            sample_evidence_data["competitor_pricing"][1]["confidence"] = 65.0

            quality_score = mock_agent._calculate_data_quality_score(
                competitor_pricing=sample_evidence_data["competitor_pricing"],
                market_size=sample_evidence_data["market_size"],
                similar_launches=sample_evidence_data["similar_launches"]
            )

            assert 50.0 <= quality_score <= 80.0, f"Expected medium quality with mixed sources, got {quality_score}"

        @pytest.mark.asyncio
        async def test_zero_quality_score_with_no_data(self, mock_agent):
            """Test zero quality score with no evidence"""
            quality_score = mock_agent._calculate_data_quality_score(
                competitor_pricing=[],
                market_size=None,
                similar_launches=[]
            )

            assert quality_score == 0.0, "Quality score should be 0 with no data"

        @pytest.mark.asyncio
        async def test_launch_engagement_quality_calculation(self, mock_agent):
            """Test that launch engagement affects quality score"""
            high_engagement_launch = {
                "product_name": "PopularApp",
                "launch_platform": "Product Hunt",
                "upvotes": 5000,
                "comments": 1000,
                "source_url": "https://producthunt.com/posts/popularapp"
            }

            low_engagement_launch = {
                "product_name": "NicheApp",
                "launch_platform": "Product Hunt",
                "upvotes": 50,
                "comments": 10,
                "source_url": "https://producthunt.com/posts/nicheapp"
            }

            quality_high = mock_agent._calculate_data_quality_score(
                competitor_pricing=[],
                market_size=None,
                similar_launches=[high_engagement_launch]
            )

            quality_low = mock_agent._calculate_data_quality_score(
                competitor_pricing=[],
                market_size=None,
                similar_launches=[low_engagement_launch]
            )

            assert quality_high > quality_low, "Higher engagement should increase quality score"


    class TestCostTracking:
        """Test cost tracking functionality"""

        @pytest.mark.asyncio
        async def test_cost_tracking_initialization(self, mock_agent):
            """Test that cost tracking is properly initialized"""
            assert mock_agent.enable_cost_tracking is True
            assert mock_agent.total_cost == 0.0
            assert mock_agent.validation_count == 0

        @pytest.mark.asyncio
        async def test_cost_accumulation(self, mock_agent):
            """Test that costs accumulate correctly"""
            # Simulate multiple validations
            mock_agent.total_cost = 0.01  # $0.01
            mock_agent.validation_count = 2

            # Add another validation cost
            mock_agent.total_cost += 0.005
            mock_agent.validation_count += 1

            summary = mock_agent.get_cost_summary()

            assert summary["total_cost"] == 0.015
            assert summary["validation_count"] == 3
            assert summary["average_cost_per_validation"] == 0.005

        @pytest.mark.asyncio
        async def test_cost_tracking_disabled(self):
            """Test behavior when cost tracking is disabled"""
            with patch('transform.market_research_agent.JINA_AVAILABLE', False):
                agent = MarketResearchAgent(
                    enable_cost_tracking=False,
                    use_real_jina=False
                )

                summary = agent.get_cost_summary()
                assert summary["cost_tracking_enabled"] is False

        @pytest.mark.asyncio
        async def test_cost_summary_division_by_zero(self, mock_agent):
            """Test cost summary handles zero validation count"""
            summary = mock_agent.get_cost_summary()

            assert summary["validation_count"] == 0
            assert summary["average_cost_per_validation"] == 0.0
            assert "division" not in str(mock_agent.get_cost_summary).lower()

        @pytest.mark.asyncio
        async def test_reset_cost_tracking(self, mock_agent):
            """Test that cost tracking can be reset"""
            # Add some costs
            mock_agent.total_cost = 0.05
            mock_agent.validation_count = 10

            # Reset
            mock_agent.reset_cost_tracking()

            assert mock_agent.total_cost == 0.0
            assert mock_agent.validation_count == 0

        @pytest.mark.asyncio
        async def test_mock_cost_calculation(self, mock_agent):
            """Test that mock validation calculates costs correctly"""
            # Mock the helper methods
            mock_agent._search_competitor_pricing = AsyncMock(return_value=[{}, {}])
            mock_agent._search_market_size = AsyncMock(return_value={})
            mock_agent._search_product_launches = AsyncMock(return_value=[{}])

            # Run mock validation
            evidence = await mock_agent._perform_mock_market_validation(
                app_concept="Test App",
                target_market="Test Market",
                problem_description="Test Problem"
            )

            # Verify mock cost calculation
            # 3 searches * $0.0001 + 3 URLs * $0.0002 = $0.0009
            expected_cost = 3 * 0.0001 + 3 * 0.0002
            assert evidence.total_cost == expected_cost


    class TestConfigurationValidation:
        """Test agent configuration and validation"""

        @pytest.mark.asyncio
        async def test_custom_validation_threshold(self):
            """Test custom validation threshold configuration"""
            custom_threshold = 85.0
            agent = MarketResearchAgent(
                validation_threshold=custom_threshold,
                use_real_jina=False
            )

            assert agent.validation_threshold == custom_threshold

            # Test threshold logic
            assert agent.should_validate_opportunity(90.0) is True
            assert agent.should_validate_opportunity(80.0) is False

        @pytest.mark.asyncio
        async def test_max_competitors_configuration(self):
            """Test max competitors configuration"""
            agent = MarketResearchAgent(
                max_competitors=3,
                use_real_jina=False
            )

            assert agent.max_competitors == 3

            # Test the actual implementation returns at most max_competitors
            competitors = await agent._search_competitor_pricing("Test", "Market")
            assert len(competitors) <= 3

        @pytest.mark.asyncio
        async def test_max_launches_configuration(self):
            """Test max launches configuration"""
            agent = MarketResearchAgent(
                max_launches=5,
                use_real_jina=False
            )

            assert agent.max_launches == 5

        @pytest.mark.asyncio
        async def test_real_jina_detection(self):
            """Test real Jina API availability detection"""
            # With Jina available and API key
            with patch('transform.market_research_agent.JINA_AVAILABLE', True):
                agent = MarketResearchAgent(
                    jina_api_key="test-key",
                    use_real_jina=None  # Auto-detect
                )
                assert agent.use_real_jina is True

            # Without Jina available
            with patch('transform.market_research_agent.JINA_AVAILABLE', False):
                agent = MarketResearchAgent(
                    jina_api_key="test-key",
                    use_real_jina=None  # Auto-detect
                )
                assert agent.use_real_jina is False

        @pytest.mark.asyncio
        async def test_force_mock_implementation(self):
            """Test forcing mock implementation"""
            with patch('transform.market_research_agent.JINA_AVAILABLE', True):
                agent = MarketResearchAgent(
                    jina_api_key="test-key",
                    use_real_jina=False  # Force mock
                )
                assert agent.use_real_jina is False


    class TestErrorHandling:
        """Test error handling and edge cases"""

        @pytest.mark.asyncio
        async def test_missing_input_data(self, mock_agent):
            """Test handling of missing input data"""
            # Empty input
            result = await mock_agent.run({})

            assert "error" in result or "validation_score" in result
            assert isinstance(result, dict)

        @pytest.mark.asyncio
        async def test_none_input_fields(self, mock_agent):
            """Test handling of None input fields"""
            result = await mock_agent.run({
                "app_concept": None,
                "target_market": None,
                "problem_description": None
            })

            assert isinstance(result, dict)

        @pytest.mark.asyncio
        async def test_exception_in_market_validation(self, mock_agent):
            """Test handling of exceptions in market validation"""
            # Mock _perform_market_validation to raise exception
            with patch.object(mock_agent, '_perform_market_validation',
                             side_effect=Exception("Test error")):
                result = await mock_agent.run({
                    "app_concept": "Test App",
                    "target_market": "Test Market"
                })

                assert "error" in result
                assert "Test error" in result["reasoning"]

        @pytest.mark.asyncio
        async def test_jina_client_initialization_failure(self):
            """Test graceful fallback when Jina client fails to initialize"""
            with patch('transform.market_research_agent.JINA_AVAILABLE', True):
                with patch('transform.market_research_agent.JinaClient',
                          side_effect=Exception("Failed to initialize")):
                    with patch('transform.market_research_agent.get_settings'):
                        agent = MarketResearchAgent(
                            jina_api_key="test-key",
                            use_real_jina=None
                        )

                        # Should fall back to mock
                        assert agent.use_real_jina is False
                        assert agent.jina_client is None

        @pytest.mark.asyncio
        async def test_async_context_manager(self):
            """Test async context manager functionality"""
            with patch('transform.market_research_agent.JINA_AVAILABLE', False):
                agent = MarketResearchAgent(use_real_jina=False)

                async with agent as a:
                    assert a is agent

                # Should not raise any errors

        @pytest.mark.asyncio
        async def test_close_with_no_jina_client(self, mock_agent):
            """Test close method when no Jina client exists"""
            # Should not raise error
            await mock_agent.close()


    class TestReasoningGeneration:
        """Test reasoning generation from evidence"""

        @pytest.mark.asyncio
        async def test_comprehensive_reasoning_with_all_evidence(self, mock_agent, sample_evidence_data):
            """Test comprehensive reasoning with all evidence types"""
            reasoning = mock_agent._generate_reasoning(
                competitor_pricing=sample_evidence_data["competitor_pricing"],
                market_size=sample_evidence_data["market_size"],
                similar_launches=sample_evidence_data["similar_launches"],
                validation_score=85.0
            )

            # Should mention all evidence types
            assert "competitors" in reasoning.lower()
            assert "market size" in reasoning.lower()
            assert "launch" in reasoning.lower()
            assert "strong" in reasoning.lower()

        @pytest.mark.asyncio
        async def test_reasoning_with_competitors_only(self, mock_agent, sample_evidence_data):
            """Test reasoning with only competitor evidence"""
            reasoning = mock_agent._generate_reasoning(
                competitor_pricing=sample_evidence_data["competitor_pricing"],
                market_size=None,
                similar_launches=[],
                validation_score=65.0
            )

            assert "competitors" in reasoning.lower()
            assert "moderate" in reasoning.lower()

        @pytest.mark.asyncio
        async def test_reasoning_with_no_evidence(self, mock_agent):
            """Test reasoning with no evidence"""
            reasoning = mock_agent._generate_reasoning(
                competitor_pricing=[],
                market_size=None,
                similar_launches=[],
                validation_score=0.0
            )

            assert "limited" in reasoning.lower()

        @pytest.mark.asyncio
        async def test_reasoning_includes_confidence_scores(self, mock_agent, sample_evidence_data):
            """Test that reasoning includes confidence scores"""
            reasoning = mock_agent._generate_reasoning(
                competitor_pricing=sample_evidence_data["competitor_pricing"],
                market_size=None,
                similar_launches=[],
                validation_score=70.0
            )

            # Should mention average confidence
            assert "confidence" in reasoning.lower()
            assert "%" in reasoning


    class TestDataConversion:
        """Test data format conversion methods"""

        @pytest.mark.asyncio
        async def test_evidence_to_dict_conversion(self, mock_agent, sample_evidence_data):
            """Test conversion of ValidationEvidence to dict"""
            # Create a mock ValidationEvidence
            mock_evidence = Mock()
            mock_evidence.competitor_pricing = []
            mock_evidence.market_size = None
            mock_evidence.similar_launches = []
            mock_evidence.validation_score = 75.0
            mock_evidence.data_quality_score = 80.0
            mock_evidence.reasoning = "Test reasoning"
            mock_evidence.urls_fetched = ["url1", "url2"]
            mock_evidence.search_queries_used = ["query1"]
            mock_evidence.total_cost = 0.01

            # Convert to dict
            result = mock_agent._convert_evidence_to_dict(mock_evidence)

            assert isinstance(result, dict)
            assert result["validation_score"] == 75.0
            assert result["data_quality_score"] == 80.0
            assert result["reasoning"] == "Test reasoning"
            assert result["evidence_urls"] == ["url1", "url2"]
            assert result["search_queries"] == ["query1"]
            assert result["jina_cost"] == 0.01

        @pytest.mark.asyncio
        async def test_competitor_pricing_dict_format(self, mock_agent):
            """Test competitor pricing dictionary format"""
            mock_comp = Mock()
            mock_comp.company_name = "TestCo"
            mock_comp.pricing_model = "subscription"
            mock_comp.pricing_tiers = [{"name": "Pro", "price": "$29/mo"}]
            mock_comp.target_market = "SMB"
            mock_comp.source_url = "https://testco.com"
            mock_comp.confidence = 85.0

            mock_evidence = Mock()
            mock_evidence.competitor_pricing = [mock_comp]
            mock_evidence.market_size = None
            mock_evidence.similar_launches = []
            mock_evidence.validation_score = 0
            mock_evidence.data_quality_score = 0
            mock_evidence.reasoning = ""
            mock_evidence.urls_fetched = []
            mock_evidence.search_queries_used = []
            mock_evidence.total_cost = 0

            result = mock_agent._convert_evidence_to_dict(mock_evidence)

            comp = result["competitor_pricing"][0]
            assert comp["company"] == "TestCo"
            assert comp["pricing_model"] == "subscription"
            assert comp["target"] == "SMB"
            assert comp["url"] == "https://testco.com"
            assert comp["confidence"] == 85.0

        @pytest.mark.asyncio
        async def test_error_result_format(self, mock_agent):
            """Test error result format"""
            error_result = mock_agent._create_error_result("Test error message")

            assert error_result["competitor_pricing"] == []
            assert error_result["market_size"] is None
            assert error_result["similar_launches"] == []
            assert error_result["validation_score"] == 0.0
            assert error_result["data_quality_score"] == 0.0
            assert "Test error message" in error_result["reasoning"]
            assert error_result["error"] == "Test error message"
            assert error_result["evidence_urls"] == []
            assert error_result["search_queries"] == []
            assert error_result["jina_cost"] == 0.0


class TestMarketResearchAgentIntegrationVCR:
    """VCR.py Integration Tests for MarketResearchAgent"""

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def test_real_web_search_and_extraction(self):
        """Test actual web search and content extraction with VCR"""
        # This test would be recorded once and replayed
        # It would test real Jina API interactions
        pass

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def test_caching_behavior_with_redis(self):
        """Test caching behavior with Redis backend"""
        # Test that repeated requests hit cache
        pass

    @pytest.mark.vcr
    @pytest.mark.asyncio
    async def test_rate_limiting_and_retry_logic(self):
        """Test rate limiting and retry logic"""
        # Test that failed requests are retried
        pass