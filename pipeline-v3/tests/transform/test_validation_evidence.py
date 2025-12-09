"""
Comprehensive TDD Test Suite for ValidationEvidence Data Structures

Phase 3 Jina Market Research Integration - RED PHASE
These tests will FAIL initially and drive the implementation of ValidationEvidence models.

TDD Approach:
- RED: Write failing tests for all ValidationEvidence data structures
- GREEN: Implement minimal models to pass all tests
- REFACTOR: Optimize with Pydantic integration and serialization

Based on Phase 3 Jina Integration Documentation lines 366-427
"""

import json
import os

# Import the models directly by executing the module
# This bypasses the sqlalchemy dependency issues in the broader test suite
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    # Import by executing the module directly
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "validation_evidence",
        os.path.join(os.path.dirname(__file__), '..', 'transform', 'validation_evidence.py')
    )
    validation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validation_module)

    ValidationEvidence = validation_module.ValidationEvidence
    CompetitorPricing = validation_module.CompetitorPricing
    MarketSizeData = validation_module.MarketSizeData
    ProductLaunchData = validation_module.ProductLaunchData

except Exception as e:
    # Models don't exist yet - this is expected for RED phase
    print(f"Import failed: {e}")
    ValidationEvidence = None
    CompetitorPricing = None
    MarketSizeData = None
    ProductLaunchData = None


class TestCompetitorPricing:
    """Test suite for CompetitorPricing data structure"""

    def test_competitor_pricing_initialization(self):
        """Test CompetitorPricing can be initialized with all required fields"""
        if CompetitorPricing is None:
            pytest.skip("CompetitorPricing not implemented yet - RED phase")

        pricing = CompetitorPricing(
            company_name="Asana",
            pricing_model="subscription",
            pricing_tiers=[
                {"name": "Basic", "price": "$10/mo"},
                {"name": "Pro", "price": "$24/mo"},
                {"name": "Enterprise", "price": "Custom"}
            ],
            target_market="B2B",
            source_url="https://asana.com/pricing",
            confidence=85.5
        )

        assert pricing.company_name == "Asana"
        assert pricing.pricing_model == "subscription"
        assert len(pricing.pricing_tiers) == 3
        assert pricing.target_market == "B2B"
        assert pricing.source_url == "https://asana.com/pricing"
        assert pricing.confidence == 85.5

    def test_competitor_pricing_field_validation(self):
        """Test field validation for CompetitorPricing"""
        if CompetitorPricing is None:
            pytest.skip("CompetitorPricing not implemented yet - RED phase")

        # Test valid pricing models
        valid_models = ["subscription", "freemium", "one-time", "usage-based"]
        for model in valid_models:
            pricing = CompetitorPricing(
                company_name="Test Co",
                pricing_model=model,
                pricing_tiers=[],
                target_market="B2B",
                source_url="https://example.com",
                confidence=75.0
            )
            assert pricing.pricing_model == model

        # Test valid target markets
        valid_markets = ["B2B", "B2C", "Enterprise", "SMB", "B2B2C"]
        for market in valid_markets:
            pricing = CompetitorPricing(
                company_name="Test Co",
                pricing_model="subscription",
                pricing_tiers=[],
                target_market=market,
                source_url="https://example.com",
                confidence=75.0
            )
            assert pricing.target_market == market

    def test_competitor_pricing_confidence_bounds(self):
        """Test confidence score is within 0-100 bounds"""
        if CompetitorPricing is None:
            pytest.skip("CompetitorPricing not implemented yet - RED phase")

        # Test valid confidence scores
        valid_scores = [0.0, 50.5, 75.0, 99.9, 100.0]
        for score in valid_scores:
            pricing = CompetitorPricing(
                company_name="Test Co",
                pricing_model="subscription",
                pricing_tiers=[],
                target_market="B2B",
                source_url="https://example.com",
                confidence=score
            )
            assert pricing.confidence == score

        # Test invalid confidence scores should raise validation error
        invalid_scores = [-1.0, -10.5, 100.1, 150.0]
        for score in invalid_scores:
            with pytest.raises(ValueError):  # Expecting Pydantic validation
                CompetitorPricing(
                    company_name="Test Co",
                    pricing_model="subscription",
                    pricing_tiers=[],
                    target_market="B2B",
                    source_url="https://example.com",
                    confidence=score
                )

    def test_competitor_pricing_serialization(self):
        """Test CompetitorPricing can serialize to/from JSON"""
        if CompetitorPricing is None:
            pytest.skip("CompetitorPricing not implemented yet - RED phase")

        original = CompetitorPricing(
            company_name="Monday.com",
            pricing_model="freemium",
            pricing_tiers=[
                {"name": "Free", "price": "$0", "features": ["Up to 3 users"]},
                {"name": "Standard", "price": "$8/mo", "features": ["Unlimited users"]},
            ],
            target_market="B2B",
            source_url="https://monday.com/pricing",
            confidence=90.0
        )

        # Test to_json method
        json_data = original.to_json()
        assert isinstance(json_data, str)

        parsed = json.loads(json_data)
        assert parsed["company_name"] == "Monday.com"
        assert parsed["pricing_model"] == "freemium"
        assert len(parsed["pricing_tiers"]) == 2
        assert parsed["confidence"] == 90.0

        # Test from_json method
        restored = CompetitorPricing.from_json(json_data)
        assert restored.company_name == original.company_name
        assert restored.pricing_model == original.pricing_model
        assert restored.confidence == original.confidence

    def test_competitor_pricing_required_fields(self):
        """Test that required fields cannot be None or empty"""
        if CompetitorPricing is None:
            pytest.skip("CompetitorPricing not implemented yet - RED phase")

        # Test missing required fields
        with pytest.raises(ValueError):  # Expecting Pydantic validation
            CompetitorPricing(
                company_name="",  # Empty string should fail
                pricing_model="subscription",
                pricing_tiers=[],
                target_market="B2B",
                source_url="https://example.com",
                confidence=75.0
            )

        with pytest.raises(ValueError):
            CompetitorPricing(
                company_name="Test Co",
                pricing_model="subscription",
                pricing_tiers=[],
                target_market="B2B",
                source_url="",  # Empty URL should fail
                confidence=75.0
            )


class TestMarketSizeData:
    """Test suite for MarketSizeData data structure"""

    def test_market_size_data_initialization(self):
        """Test MarketSizeData can be initialized with all required fields"""
        if MarketSizeData is None:
            pytest.skip("MarketSizeData not implemented yet - RED phase")

        market_data = MarketSizeData(
            tam_value="$50B",
            sam_value="$5B",
            growth_rate="15% CAGR",
            source_name="Gartner 2024",
            source_url="https://gartner.com/reports/project-management-market",
            year=2024
        )

        assert market_data.tam_value == "$50B"
        assert market_data.sam_value == "$5B"
        assert market_data.growth_rate == "15% CAGR"
        assert market_data.source_name == "Gartner 2024"
        assert market_data.source_url == "https://gartner.com/reports/project-management-market"
        assert market_data.year == 2024

    def test_market_size_data_year_validation(self):
        """Test year field validation"""
        if MarketSizeData is None:
            pytest.skip("MarketSizeData not implemented yet - RED phase")

        # Test valid years
        valid_years = [2020, 2022, 2024, 2025]
        for year in valid_years:
            market_data = MarketSizeData(
                tam_value="$10B",
                sam_value="$1B",
                growth_rate="10% CAGR",
                source_name="Test Source",
                source_url="https://example.com",
                year=year
            )
            assert market_data.year == year

        # Test invalid years
        invalid_years = [1999, 1800, 2030, 2026]  # Too old or future
        for year in invalid_years:
            with pytest.raises(ValueError):  # Expecting Pydantic validation
                MarketSizeData(
                    tam_value="$10B",
                    sam_value="$1B",
                    growth_rate="10% CAGR",
                    source_name="Test Source",
                    source_url="https://example.com",
                    year=year
                )

    def test_market_size_data_format_patterns(self):
        """Test that value fields follow expected patterns"""
        if MarketSizeData is None:
            pytest.skip("MarketSizeData not implemented yet - RED phase")

        # Valid TAM/SAM formats
        valid_tam_formats = ["$50B", "$2.5B", "$100M", "$750K", "€30B", "¥1T"]
        valid_growth_formats = ["15% CAGR", "8.5% YoY", "12% annually", "25% growth rate"]

        for tam_format in valid_tam_formats:
            market_data = MarketSizeData(
                tam_value=tam_format,
                sam_value="$1B",
                growth_rate="10% CAGR",
                source_name="Test Source",
                source_url="https://example.com",
                year=2024
            )
            assert market_data.tam_value == tam_format

        for growth_format in valid_growth_formats:
            market_data = MarketSizeData(
                tam_value="$10B",
                sam_value="$1B",
                growth_rate=growth_format,
                source_name="Test Source",
                source_url="https://example.com",
                year=2024
            )
            assert market_data.growth_rate == growth_format

    def test_market_size_data_serialization(self):
        """Test MarketSizeData can serialize to/from JSON"""
        if MarketSizeData is None:
            pytest.skip("MarketSizeData not implemented yet - RED phase")

        original = MarketSizeData(
            tam_value="$45.2B",
            sam_value="$4.8B",
            growth_rate="18.5% CAGR",
            source_name="Grand View Research 2024",
            source_url="https://grandviewresearch.com/industry-analysis/project-management-market",
            year=2024
        )

        # Test serialization
        json_data = original.to_json()
        assert isinstance(json_data, str)

        parsed = json.loads(json_data)
        assert parsed["tam_value"] == "$45.2B"
        assert parsed["sam_value"] == "$4.8B"
        assert parsed["growth_rate"] == "18.5% CAGR"
        assert parsed["year"] == 2024

        # Test deserialization
        restored = MarketSizeData.from_json(json_data)
        assert restored.tam_value == original.tam_value
        assert restored.sam_value == original.sam_value
        assert restored.year == original.year

    def test_market_size_data_optional_fields(self):
        """Test that some fields can be optional"""
        if MarketSizeData is None:
            pytest.skip("MarketSizeData not implemented yet - RED phase")

        # SAM value might be optional
        market_data = MarketSizeData(
            tam_value="$25B",
            sam_value=None,  # Optional field
            growth_rate="12% CAGR",
            source_name="Statista 2024",
            source_url="https://statista.com/market-reports",
            year=2024
        )

        assert market_data.tam_value == "$25B"
        assert market_data.sam_value is None


class TestProductLaunchData:
    """Test suite for ProductLaunchData data structure"""

    def test_product_launch_data_initialization(self):
        """Test ProductLaunchData can be initialized with all required fields"""
        if ProductLaunchData is None:
            pytest.skip("ProductLaunchData not implemented yet - RED phase")

        launch_data = ProductLaunchData(
            product_name="TaskMaster Pro",
            launch_platform="Product Hunt",
            launch_date="2024-03-15",
            upvotes=542,
            comments=89,
            source_url="https://www.producthunt.com/posts/taskmaster-pro"
        )

        assert launch_data.product_name == "TaskMaster Pro"
        assert launch_data.launch_platform == "Product Hunt"
        assert launch_data.launch_date == "2024-03-15"
        assert launch_data.upvotes == 542
        assert launch_data.comments == 89
        assert launch_data.source_url == "https://www.producthunt.com/posts/taskmaster-pro"

    def test_product_launch_data_platform_validation(self):
        """Test launch platform validation"""
        if ProductLaunchData is None:
            pytest.skip("ProductLaunchData not implemented yet - RED phase")

        valid_platforms = [
            "Product Hunt", "Hacker News", "Reddit", "Indie Hackers",
            "BetaList", "AngelList", "TechCrunch", "YC Launch"
        ]

        for platform in valid_platforms:
            launch_data = ProductLaunchData(
                product_name="Test Product",
                launch_platform=platform,
                launch_date="2024-01-01",
                upvotes=100,
                comments=25,
                source_url="https://example.com"
            )
            assert launch_data.launch_platform == platform

    def test_product_launch_data_engagement_metrics(self):
        """Test engagement metrics validation"""
        if ProductLaunchData is None:
            pytest.skip("ProductLaunchData not implemented yet - RED phase")

        # Test valid metrics
        valid_upvotes = [0, 1, 50, 500, 5000, 10000]
        valid_comments = [0, 1, 20, 100, 500, 2000]

        for upvotes in valid_upvotes:
            launch_data = ProductLaunchData(
                product_name="Test Product",
                launch_platform="Product Hunt",
                launch_date="2024-01-01",
                upvotes=upvotes,
                comments=50,
                source_url="https://example.com"
            )
            assert launch_data.upvotes == upvotes
            assert launch_data.upvotes >= 0  # Should not be negative

        for comments in valid_comments:
            launch_data = ProductLaunchData(
                product_name="Test Product",
                launch_platform="Product Hunt",
                launch_date="2024-01-01",
                upvotes=100,
                comments=comments,
                source_url="https://example.com"
            )
            assert launch_data.comments == comments
            assert launch_data.comments >= 0  # Should not be negative

        # Test negative values should fail
        with pytest.raises(ValueError):
            ProductLaunchData(
                product_name="Test Product",
                launch_platform="Product Hunt",
                launch_date="2024-01-01",
                upvotes=-10,  # Negative should fail
                comments=50,
                source_url="https://example.com"
            )

    def test_product_launch_data_date_format(self):
        """Test launch date format validation"""
        if ProductLaunchData is None:
            pytest.skip("ProductLaunchData not implemented yet - RED phase")

        valid_dates = [
            "2024-03-15", "2023-12-01", "2025-01-31",
            "2024-03-15T10:30:00Z", "2024-03-15T14:30:00+00:00"
        ]

        for date_str in valid_dates:
            launch_data = ProductLaunchData(
                product_name="Test Product",
                launch_platform="Product Hunt",
                launch_date=date_str,
                upvotes=100,
                comments=25,
                source_url="https://example.com"
            )
            assert launch_data.launch_date == date_str

    def test_product_launch_data_serialization(self):
        """Test ProductLaunchData can serialize to/from JSON"""
        if ProductLaunchData is None:
            pytest.skip("ProductLaunchData not implemented yet - RED phase")

        original = ProductLaunchData(
            product_name="FlowState",
            launch_platform="Hacker News",
            launch_date="2024-02-28",
            upvotes=1250,
            comments=342,
            source_url="https://news.ycombinator.com/item?id=123456"
        )

        # Test serialization
        json_data = original.to_json()
        assert isinstance(json_data, str)

        parsed = json.loads(json_data)
        assert parsed["product_name"] == "FlowState"
        assert parsed["launch_platform"] == "Hacker News"
        assert parsed["upvotes"] == 1250
        assert parsed["comments"] == 342

        # Test deserialization
        restored = ProductLaunchData.from_json(json_data)
        assert restored.product_name == original.product_name
        assert restored.upvotes == original.upvotes


class TestValidationEvidence:
    """Test suite for ValidationEvidence main data structure"""

    def test_validation_evidence_complete_initialization(self):
        """Test ValidationEvidence with all fields populated"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        # Create test data
        competitor_pricing = [
            CompetitorPricing(
                company_name="Asana",
                pricing_model="subscription",
                pricing_tiers=[{"name": "Pro", "price": "$24/mo"}],
                target_market="B2B",
                source_url="https://asana.com/pricing",
                confidence=85.0
            ),
            CompetitorPricing(
                company_name="Trello",
                pricing_model="freemium",
                pricing_tiers=[{"name": "Free", "price": "$0"}],
                target_market="B2B",
                source_url="https://trello.com/pricing",
                confidence=90.0
            )
        ]

        market_size = MarketSizeData(
            tam_value="$50B",
            sam_value="$5B",
            growth_rate="15% CAGR",
            source_name="Gartner 2024",
            source_url="https://gartner.com/reports",
            year=2024
        )

        similar_launches = [
            ProductLaunchData(
                product_name="TaskFlow",
                launch_platform="Product Hunt",
                launch_date="2024-01-15",
                upvotes=750,
                comments=120,
                source_url="https://producthunt.com/posts/taskflow"
            )
        ]

        evidence = ValidationEvidence(
            competitor_pricing=competitor_pricing,
            market_size=market_size,
            similar_launches=similar_launches,
            validation_score=78.5,
            data_quality_score=82.0,
            reasoning="Strong competitive landscape with clear pricing models and substantial market size.",
            search_queries_used=["project management tool pricing", "PM software market size"],
            urls_fetched=["https://asana.com/pricing", "https://trello.com/pricing", "https://gartner.com/reports"],
            total_cost=0.0075
        )

        # Verify all fields are set correctly
        assert len(evidence.competitor_pricing) == 2
        assert evidence.competitor_pricing[0].company_name == "Asana"
        assert evidence.market_size.tam_value == "$50B"
        assert len(evidence.similar_launches) == 1
        assert evidence.validation_score == 78.5
        assert evidence.data_quality_score == 82.0
        assert "Strong competitive landscape" in evidence.reasoning
        assert len(evidence.search_queries_used) == 2
        assert len(evidence.urls_fetched) == 3
        assert evidence.total_cost == 0.0075

    def test_validation_evidence_minimal_initialization(self):
        """Test ValidationEvidence with minimal required fields"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        evidence = ValidationEvidence(
            competitor_pricing=[],
            market_size=None,
            similar_launches=[],
            validation_score=50.0,
            data_quality_score=60.0,
            reasoning="Minimal test evidence",
            search_queries_used=[],
            urls_fetched=[],
            total_cost=0.0
        )

        assert evidence.competitor_pricing == []
        assert evidence.market_size is None
        assert evidence.similar_launches == []
        assert evidence.validation_score == 50.0
        assert evidence.data_quality_score == 60.0

    def test_validation_evidence_score_bounds(self):
        """Test validation and data quality scores are within 0-100 bounds"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        # Test valid scores
        valid_scores = [0.0, 25.5, 50.0, 75.0, 99.9, 100.0]
        for validation_score in valid_scores:
            for data_quality_score in valid_scores:
                evidence = ValidationEvidence(
                    competitor_pricing=[],
                    market_size=None,
                    similar_launches=[],
                    validation_score=validation_score,
                    data_quality_score=data_quality_score,
                    reasoning="Test",
                    search_queries_used=[],
                    urls_fetched=[],
                    total_cost=0.0
                )
                assert evidence.validation_score == validation_score
                assert evidence.data_quality_score == data_quality_score

        # Test invalid scores should raise validation error
        invalid_scores = [-1.0, -10.5, 100.1, 150.0]
        for score in invalid_scores:
            with pytest.raises(ValueError):
                ValidationEvidence(
                    competitor_pricing=[],
                    market_size=None,
                    similar_launches=[],
                    validation_score=score,  # Invalid score
                    data_quality_score=50.0,
                    reasoning="Test",
                    search_queries_used=[],
                    urls_fetched=[],
                    total_cost=0.0
                )

            with pytest.raises(ValueError):
                ValidationEvidence(
                    competitor_pricing=[],
                    market_size=None,
                    similar_launches=[],
                    validation_score=50.0,
                    data_quality_score=score,  # Invalid score
                    reasoning="Test",
                    search_queries_used=[],
                    urls_fetched=[],
                    total_cost=0.0
                )

    def test_validation_evidence_cost_tracking(self):
        """Test cost tracking validation"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        # Test valid costs
        valid_costs = [0.0, 0.001, 0.005, 0.01, 0.05, 0.10]
        for cost in valid_costs:
            evidence = ValidationEvidence(
                competitor_pricing=[],
                market_size=None,
                similar_launches=[],
                validation_score=75.0,
                data_quality_score=80.0,
                reasoning="Test",
                search_queries_used=[],
                urls_fetched=[],
                total_cost=cost
            )
            assert evidence.total_cost == cost

        # Test negative costs should fail
        invalid_costs = [-0.001, -0.01, -1.0]
        for cost in invalid_costs:
            with pytest.raises(ValueError):
                ValidationEvidence(
                    competitor_pricing=[],
                    market_size=None,
                    similar_launches=[],
                    validation_score=75.0,
                    data_quality_score=80.0,
                    reasoning="Test",
                    search_queries_used=[],
                    urls_fetched=[],
                    total_cost=cost  # Negative cost should fail
                )

    def test_validation_evidence_serialization_roundtrip(self):
        """Test ValidationEvidence complete serialization roundtrip"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        # Create complex evidence
        original = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="Monday.com",
                    pricing_model="subscription",
                    pricing_tiers=[
                        {"name": "Basic", "price": "$8/mo"},
                        {"name": "Pro", "price": "$16/mo"}
                    ],
                    target_market="B2B",
                    source_url="https://monday.com/pricing",
                    confidence=88.5
                )
            ],
            market_size=MarketSizeData(
                tam_value="$65B",
                sam_value="$8B",
                growth_rate="22% CAGR",
                source_name="Forrester 2024",
                source_url="https://forrester.com/reports",
                year=2024
            ),
            similar_launches=[
                ProductLaunchData(
                    product_name="TeamSync",
                    launch_platform="Product Hunt",
                    launch_date="2024-02-01",
                    upvotes=1200,
                    comments=280,
                    source_url="https://producthunt.com/posts/teamsync"
                )
            ],
            validation_score=82.5,
            data_quality_score=88.0,
            reasoning="Competitive analysis shows clear market opportunity with established pricing models and strong growth trajectory.",
            search_queries_used=[
                "project management software market size",
                "competitor analysis tools pricing",
                "team collaboration SaaS competitors"
            ],
            urls_fetched=[
                "https://monday.com/pricing",
                "https://forrester.com/reports",
                "https://producthunt.com/posts/teamsync"
            ],
            total_cost=0.0125
        )

        # Test to_json serialization
        json_data = original.to_json()
        assert isinstance(json_data, str)

        # Verify JSON structure
        parsed = json.loads(json_data)
        assert "competitor_pricing" in parsed
        assert "market_size" in parsed
        assert "similar_launches" in parsed
        assert "validation_score" in parsed
        assert "data_quality_score" in parsed
        assert "reasoning" in parsed
        assert "search_queries_used" in parsed
        assert "urls_fetched" in parsed
        assert "total_cost" in parsed

        # Test from_json deserialization
        restored = ValidationEvidence.from_json(json_data)

        # Verify restored object matches original
        assert restored.validation_score == original.validation_score
        assert restored.data_quality_score == original.data_quality_score
        assert restored.reasoning == original.reasoning
        assert len(restored.competitor_pricing) == len(original.competitor_pricing)
        assert restored.competitor_pricing[0].company_name == original.competitor_pricing[0].company_name
        assert restored.market_size.tam_value == original.market_size.tam_value
        assert len(restored.similar_launches) == len(original.similar_launches)
        assert restored.total_cost == original.total_cost

    def test_validation_evidence_partial_data_handling(self):
        """Test ValidationEvidence with partial/missing data"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        # Test with only competitor pricing
        evidence_pricing_only = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="Solo competitor",
                    pricing_model="subscription",
                    pricing_tiers=[{"name": "Pro", "price": "$20/mo"}],
                    target_market="B2B",
                    source_url="https://example.com",
                    confidence=75.0
                )
            ],
            market_size=None,
            similar_launches=[],
            validation_score=60.0,
            data_quality_score=65.0,
            reasoning="Only competitor data available",
            search_queries_used=["competitor pricing"],
            urls_fetched=["https://example.com"],
            total_cost=0.003
        )

        assert len(evidence_pricing_only.competitor_pricing) == 1
        assert evidence_pricing_only.market_size is None
        assert evidence_pricing_only.similar_launches == []

        # Test with only market size data
        evidence_market_only = ValidationEvidence(
            competitor_pricing=[],
            market_size=MarketSizeData(
                tam_value="$30B",
                sam_value=None,
                growth_rate="12% CAGR",
                source_name="Test Report",
                source_url="https://test.com",
                year=2024
            ),
            similar_launches=[],
            validation_score=70.0,
            data_quality_score=75.0,
            reasoning="Only market size data available",
            search_queries_used=["market size"],
            urls_fetched=["https://test.com"],
            total_cost=0.002
        )

        assert evidence_market_only.competitor_pricing == []
        assert evidence_market_only.market_size is not None
        assert evidence_market_only.market_size.tam_value == "$30B"

    def test_validation_evidence_summary_methods(self):
        """Test ValidationEvidence summary and utility methods"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="Asana",
                    pricing_model="subscription",
                    pricing_tiers=[{"name": "Pro", "price": "$24/mo"}],
                    target_market="B2B",
                    source_url="https://asana.com/pricing",
                    confidence=85.0
                ),
                CompetitorPricing(
                    company_name="Trello",
                    pricing_model="freemium",
                    pricing_tiers=[{"name": "Free", "price": "$0"}],
                    target_market="B2B",
                    source_url="https://trello.com/pricing",
                    confidence=90.0
                )
            ],
            market_size=MarketSizeData(
                tam_value="$50B",
                sam_value="$5B",
                growth_rate="15% CAGR",
                source_name="Gartner 2024",
                source_url="https://gartner.com",
                year=2024
            ),
            similar_launches=[
                ProductLaunchData(
                    product_name="TaskFlow",
                    launch_platform="Product Hunt",
                    launch_date="2024-01-15",
                    upvotes=750,
                    comments=120,
                    source_url="https://producthunt.com/posts/taskflow"
                )
            ],
            validation_score=78.5,
            data_quality_score=82.0,
            reasoning="Strong market evidence found",
            search_queries_used=["query1", "query2"],
            urls_fetched=["https://url1.com", "https://url2.com", "https://url3.com"],
            total_cost=0.008
        )

        # Test summary methods
        summary = evidence.get_summary()
        assert "competitors_found" in summary
        assert "market_data_available" in summary
        assert "launches_analyzed" in summary
        assert "total_sources" in summary
        assert summary["competitors_found"] == 2
        assert summary["market_data_available"] is True
        assert summary["launches_analyzed"] == 1
        assert summary["total_sources"] == 3

        # Test validation level determination
        validation_level = evidence.get_validation_level()
        assert validation_level in ["LOW", "MEDIUM", "HIGH"]
        # Score 78.5 should be HIGH validation
        assert validation_level == "HIGH"

    def test_validation_evidence_quality_metrics(self):
        """Test ValidationEvidence quality assessment methods"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        # High quality evidence
        high_quality = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="Enterprise Corp",
                    pricing_model="subscription",
                    pricing_tiers=[{"name": "Enterprise", "price": "$500/mo"}],
                    target_market="Enterprise",
                    source_url="https://enterprise.com/pricing",
                    confidence=95.0
                )
            ],
            market_size=MarketSizeData(
                tam_value="$100B",
                sam_value="$10B",
                growth_rate="25% CAGR",
                source_name="McKinsey 2024",
                source_url="https://mckinsey.com/reports",
                year=2024
            ),
            similar_launches=[
                ProductLaunchData(
                    product_name="SuccessStory",
                    launch_platform="Product Hunt",
                    launch_date="2024-03-01",
                    upvotes=2000,
                    comments=500,
                    source_url="https://producthunt.com/posts/successstory"
                )
            ],
            validation_score=90.0,
            data_quality_score=95.0,
            reasoning="High-quality sources with strong evidence",
            search_queries_used=["enterprise project management", "corporate PM tools"],
            urls_fetched=["https://enterprise.com/pricing", "https://mckinsey.com/reports"],
            total_cost=0.015
        )

        quality_metrics = high_quality.get_quality_metrics()
        assert quality_metrics["overall_quality"] == "HIGH"
        assert quality_metrics["source_diversity"] == "GOOD"
        assert quality_metrics["data_completeness"] == "COMPLETE"

        # Low quality evidence
        low_quality = ValidationEvidence(
            competitor_pricing=[],
            market_size=None,
            similar_launches=[],
            validation_score=30.0,
            data_quality_score=25.0,
            reasoning="Limited data available",
            search_queries_used=[],
            urls_fetched=[],
            total_cost=0.001
        )

        quality_metrics = low_quality.get_quality_metrics()
        assert quality_metrics["overall_quality"] == "LOW"
        assert quality_metrics["source_diversity"] == "POOR"
        assert quality_metrics["data_completeness"] == "MINIMAL"

    def test_validation_evidence_database_compatibility(self):
        """Test ValidationEvidence database serialization compatibility"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="TestCorp",
                    pricing_model="subscription",
                    pricing_tiers=[{"name": "Pro", "price": "$29/mo"}],
                    target_market="B2B",
                    source_url="https://testcorp.com/pricing",
                    confidence=80.0
                )
            ],
            market_size=MarketSizeData(
                tam_value="$25B",
                sam_value="$2.5B",
                growth_rate="18% CAGR",
                source_name="Test Research",
                source_url="https://test-research.com",
                year=2024
            ),
            similar_launches=[],
            validation_score=75.0,
            data_quality_score=78.0,
            reasoning="Test database compatibility",
            search_queries_used=["test query"],
            urls_fetched=["https://testcorp.com/pricing"],
            total_cost=0.005
        )

        # Test database serialization
        db_dict = evidence.to_database_dict()
        assert isinstance(db_dict, dict)
        assert "competitor_pricing" in db_dict
        assert "market_size" in db_dict
        assert "similar_launches" in db_dict

        # Test database deserialization
        restored = ValidationEvidence.from_database_dict(db_dict)
        assert restored.validation_score == evidence.validation_score
        assert len(restored.competitor_pricing) == len(evidence.competitor_pricing)


# Integration-style tests for the complete validation evidence workflow
class TestValidationEvidenceWorkflow:
    """Test validation evidence creation and workflow integration"""

    def test_complete_validation_evidence_creation_workflow(self):
        """Test creating ValidationEvidence through realistic workflow"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        # Simulate realistic market research data
        competitor_data = [
            {
                "company_name": "ClickUp",
                "pricing_model": "freemium",
                "pricing_tiers": [
                    {"name": "Free", "price": "$0", "users": "Unlimited"},
                    {"name": "Unlimited", "price": "$7/mo", "users": "Unlimited"},
                    {"name": "Business", "price": "$12/mo", "users": "Unlimited"},
                    {"name": "Enterprise", "price": "Custom", "users": "Custom"}
                ],
                "target_market": "B2B",
                "source_url": "https://clickup.com/pricing",
                "confidence": 92.0
            },
            {
                "company_name": "Notion",
                "pricing_model": "freemium",
                "pricing_tiers": [
                    {"name": "Personal", "price": "$0", "users": "Individual"},
                    {"name": "Plus", "price": "$8/mo", "users": "Small groups"},
                    {"name": "Business", "price": "$16/mo", "users": "Teams"},
                    {"name": "Enterprise", "price": "Custom", "users": "Large organizations"}
                ],
                "target_market": "B2B",
                "source_url": "https://notion.so/pricing",
                "confidence": 95.0
            }
        ]

        market_research = {
            "tam_value": "$58.3B",
            "sam_value": "$6.7B",
            "growth_rate": "21.8% CAGR",
            "source_name": "Fortune Business Insights 2024",
            "source_url": "https://fortunebusinessinsights.com/project-management-market",
            "year": 2024
        }

        launch_benchmarks = [
            {
                "product_name": "Motion",
                "launch_platform": "Product Hunt",
                "launch_date": "2023-11-15",
                "upvotes": 3420,
                "comments": 485,
                "source_url": "https://producthunt.com/posts/motion"
            },
            {
                "product_name": "Reclaim.ai",
                "launch_platform": "Product Hunt",
                "launch_date": "2023-09-20",
                "upvotes": 2180,
                "comments": 290,
                "source_url": "https://producthunt.com/posts/reclaim-ai"
            }
        ]

        # Create ValidationEvidence with realistic data
        evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(**data) for data in competitor_data
            ],
            market_size=MarketSizeData(**market_research),
            similar_launches=[
                ProductLaunchData(**data) for data in launch_benchmarks
            ],
            validation_score=88.5,
            data_quality_score=91.0,
            reasoning="Strong competitive landscape with 2+ major competitors, substantial market size ($58B TAM), and successful product launches demonstrating clear market demand.",
            search_queries_used=[
                "project management software competitors pricing",
                "task management market size 2024",
                "AI productivity tools Product Hunt launches"
            ],
            urls_fetched=[
                "https://clickup.com/pricing",
                "https://notion.so/pricing",
                "https://fortunebusinessinsights.com/project-management-market",
                "https://producthunt.com/posts/motion",
                "https://producthunt.com/posts/reclaim-ai"
            ],
            total_cost=0.0145
        )

        # Verify the evidence is comprehensive and realistic
        assert len(evidence.competitor_pricing) == 2
        assert evidence.competitor_pricing[0].confidence >= 90.0
        assert evidence.market_size.tam_value.startswith("$")
        assert "B" in evidence.market_size.tam_value
        assert evidence.market_size.growth_rate.endswith("%")
        assert len(evidence.similar_launches) == 2
        assert all(launch.upvotes > 1000 for launch in evidence.similar_launches)
        assert evidence.validation_score >= 85.0
        assert evidence.data_quality_score >= 90.0
        assert len(evidence.urls_fetched) == 5
        assert evidence.total_cost > 0.01

        # Test that it can be serialized for database storage
        db_data = evidence.to_database_dict()
        assert "competitor_pricing" in db_data
        assert "market_size" in db_data
        assert "similar_launches" in db_data

        # Test that it can be converted to AnalysisResult format
        analysis_data = evidence.to_analysis_result_format()
        assert "jina_validation_score" in analysis_data
        assert "jina_data_quality_score" in analysis_data
        assert "jina_competitor_count" in analysis_data
        assert analysis_data["jina_validation_score"] == evidence.validation_score
        assert analysis_data["jina_competitor_count"] == len(evidence.competitor_pricing)

    def test_validation_evidence_edge_cases(self):
        """Test ValidationEvidence edge cases and error conditions"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        # Test empty evidence
        empty_evidence = ValidationEvidence(
            competitor_pricing=[],
            market_size=None,
            similar_launches=[],
            validation_score=0.0,
            data_quality_score=0.0,
            reasoning="No data available",
            search_queries_used=[],
            urls_fetched=[],
            total_cost=0.0
        )

        summary = empty_evidence.get_summary()
        assert summary["competitors_found"] == 0
        assert summary["market_data_available"] is False
        assert summary["launches_analyzed"] == 0
        assert summary["total_sources"] == 0
        assert empty_evidence.get_validation_level() == "LOW"

        # Test very large numbers
        large_evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="MegaCorp",
                    pricing_model="subscription",
                    pricing_tiers=[{"name": "Enterprise", "price": "$10000/mo"}],
                    target_market="Enterprise",
                    source_url="https://megacorp.com/pricing",
                    confidence=99.9
                )
            ] * 20,  # 20 competitors
            market_size=MarketSizeData(
                tam_value="$1000B",  # Trillion dollar market
                sam_value="$100B",
                growth_rate="50% CAGR",
                source_name="MegaResearch",
                source_url="https://megaresearch.com",
                year=2024
            ),
            similar_launches=[
                ProductLaunchData(
                    product_name=f"Product{i}",
                    launch_platform="Product Hunt",
                    launch_date="2024-01-01",
                    upvotes=10000 + i * 1000,
                    comments=1000 + i * 100,
                    source_url=f"https://producthunt.com/posts/product{i}"
                )
                for i in range(10)
            ],
            validation_score=95.0,
            data_quality_score=98.0,
            reasoning="Extensive market data collected",
            search_queries_used=[f"query{i}" for i in range(10)],
            urls_fetched=[f"https://example{i}.com" for i in range(30)],
            total_cost=0.1
        )

        assert len(large_evidence.competitor_pricing) == 20
        assert len(large_evidence.similar_launches) == 10
        assert len(large_evidence.urls_fetched) == 30
        assert large_evidence.get_validation_level() == "HIGH"

    def test_validation_evidence_cost_optimization_tracking(self):
        """Test cost optimization features and tracking"""
        if ValidationEvidence is None:
            pytest.skip("ValidationEvidence not implemented yet - RED phase")

        # Test cost calculation based on API usage
        cost_breakdown = {
            "jina_search_calls": 3,
            "jina_reader_calls": 8,
            "llm_extraction_calls": 5,
            "jina_search_cost": 0.0003,  # $0.0001 per search
            "jina_reader_cost": 0.0016,  # $0.0002 per read
            "llm_extraction_cost": 0.003,  # $0.0006 per extraction
            "total_cost": 0.0049
        }

        evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="BudgetTracker",
                    pricing_model="subscription",
                    pricing_tiers=[{"name": "Pro", "price": "$15/mo"}],
                    target_market="B2B",
                    source_url="https://budgettracker.com/pricing",
                    confidence=75.0
                )
            ],
            market_size=None,
            similar_launches=[],
            validation_score=65.0,
            data_quality_score=70.0,
            reasoning="Cost-optimized validation with single competitor",
            search_queries_used=["budget software pricing"],
            urls_fetched=["https://budgettracker.com/pricing"],
            total_cost=cost_breakdown["total_cost"]
        )

        # Test cost analysis
        cost_analysis = evidence.get_cost_analysis()
        assert cost_analysis["total_cost"] == cost_breakdown["total_cost"]
        assert cost_analysis["cost_per_competitor"] == cost_breakdown["total_cost"] / len(evidence.competitor_pricing)
        assert "cost_breakdown_available" in cost_analysis

        # Test cost optimization recommendations
        recommendations = evidence.get_cost_optimization_recommendations()
        assert isinstance(recommendations, list)
        assert any("cache" in rec.lower() for rec in recommendations)
        assert any("selective" in rec.lower() for rec in recommendations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
