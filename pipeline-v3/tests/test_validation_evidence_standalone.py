#!/usr/bin/env python3
"""
Standalone test runner for ValidationEvidence data structures
This bypasses the conftest.py issues and tests our implementation directly.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# Import our validation evidence module directly to avoid dependency issues
import importlib.util

spec = importlib.util.spec_from_file_location("validation_evidence", os.path.join(os.path.dirname(__file__), "..", "transform", "validation_evidence.py"))
validation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation_module)

ValidationEvidence = validation_module.ValidationEvidence
CompetitorPricing = validation_module.CompetitorPricing
MarketSizeData = validation_module.MarketSizeData
ProductLaunchData = validation_module.ProductLaunchData

def test_competitor_pricing_initialization():
    """Test CompetitorPricing can be initialized with all required fields"""
    print("Testing CompetitorPricing initialization...")

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
    print("✅ CompetitorPricing initialization test passed!")

def test_competitor_pricing_validation():
    """Test field validation for CompetitorPricing"""
    print("Testing CompetitorPricing validation...")

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

    # Test invalid confidence scores should raise validation error
    try:
        CompetitorPricing(
            company_name="Test Co",
            pricing_model="subscription",
            pricing_tiers=[],
            target_market="B2B",
            source_url="https://example.com",
            confidence=-1.0  # Invalid
        )
        assert False, "Should have raised ValueError for negative confidence"
    except ValueError:
        pass  # Expected

    print("✅ CompetitorPricing validation test passed!")

def test_competitor_pricing_serialization():
    """Test CompetitorPricing can serialize to/from JSON"""
    print("Testing CompetitorPricing serialization...")

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

    import json
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
    print("✅ CompetitorPricing serialization test passed!")

def test_market_size_data_initialization():
    """Test MarketSizeData can be initialized with all required fields"""
    print("Testing MarketSizeData initialization...")

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
    print("✅ MarketSizeData initialization test passed!")

def test_product_launch_data_initialization():
    """Test ProductLaunchData can be initialized with all required fields"""
    print("Testing ProductLaunchData initialization...")

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
    print("✅ ProductLaunchData initialization test passed!")

def test_validation_evidence_initialization():
    """Test ValidationEvidence with all fields populated"""
    print("Testing ValidationEvidence initialization...")

    # Create test data
    competitor_pricing = [
        CompetitorPricing(
            company_name="Asana",
            pricing_model="subscription",
            pricing_tiers=[{"name": "Pro", "price": "$24/mo"}],
            target_market="B2B",
            source_url="https://asana.com/pricing",
            confidence=85.0
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
        urls_fetched=["https://asana.com/pricing", "https://gartner.com/reports"],
        total_cost=0.0075
    )

    # Verify all fields are set correctly
    assert len(evidence.competitor_pricing) == 1
    assert evidence.competitor_pricing[0].company_name == "Asana"
    assert evidence.market_size.tam_value == "$50B"
    assert len(evidence.similar_launches) == 1
    assert evidence.validation_score == 78.5
    assert evidence.data_quality_score == 82.0
    assert len(evidence.search_queries_used) == 2
    assert len(evidence.urls_fetched) == 2
    assert evidence.total_cost == 0.0075
    print("✅ ValidationEvidence initialization test passed!")

def test_validation_evidence_serialization():
    """Test ValidationEvidence complete serialization roundtrip"""
    print("Testing ValidationEvidence serialization...")

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
        reasoning="Competitive analysis shows clear market opportunity.",
        search_queries_used=["project management software"],
        urls_fetched=["https://monday.com/pricing"],
        total_cost=0.0125
    )

    # Test to_json serialization
    json_data = original.to_json()
    assert isinstance(json_data, str)

    import json
    parsed = json.loads(json_data)
    assert "competitor_pricing" in parsed
    assert "market_size" in parsed
    assert "validation_score" in parsed

    # Test from_json deserialization
    restored = ValidationEvidence.from_json(json_data)

    # Verify restored object matches original
    assert restored.validation_score == original.validation_score
    assert restored.data_quality_score == original.data_quality_score
    assert len(restored.competitor_pricing) == len(original.competitor_pricing)
    assert restored.competitor_pricing[0].company_name == original.competitor_pricing[0].company_name
    print("✅ ValidationEvidence serialization test passed!")

def test_validation_evidence_utilities():
    """Test ValidationEvidence utility methods"""
    print("Testing ValidationEvidence utility methods...")

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
    assert summary["competitors_found"] == 2
    assert summary["market_data_available"] is True

    # Test validation level determination
    validation_level = evidence.get_validation_level()
    assert validation_level in ["LOW", "MEDIUM", "HIGH"]
    # Score 78.5 should be HIGH validation
    assert validation_level == "HIGH"

    # Test quality metrics
    quality_metrics = evidence.get_quality_metrics()
    assert quality_metrics["overall_quality"] == "HIGH"
    assert quality_metrics["source_diversity"] == "GOOD"
    assert quality_metrics["data_completeness"] == "COMPLETE"

    print("✅ ValidationEvidence utility methods test passed!")

def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Starting ValidationEvidence TDD Tests...")
    print("=" * 60)

    tests = [
        test_competitor_pricing_initialization,
        test_competitor_pricing_validation,
        test_competitor_pricing_serialization,
        test_market_size_data_initialization,
        test_product_launch_data_initialization,
        test_validation_evidence_initialization,
        test_validation_evidence_serialization,
        test_validation_evidence_utilities
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! GREEN phase complete!")
        return True
    else:
        print("💥 Some tests failed. Need to fix implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
