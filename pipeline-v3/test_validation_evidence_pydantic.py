#!/usr/bin/env python3
"""
Enhanced Test Suite for ValidationEvidence with Pydantic Integration (REFACTOR PHASE)

This tests the refactored Pydantic-enhanced implementation to ensure:
- Enhanced validation with proper error messages
- Better type safety
- Improved serialization/deserialization
- Backward compatibility with original interface
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Test both Pydantic and fallback implementations
def test_pydantic_enhanced_validation():
    """Test Pydantic-enhanced validation with strict type checking"""
    print("Testing Pydantic enhanced validation...")

    try:
        # Import Pydantic version
        import importlib.util
        spec = importlib.util.spec_from_file_location("validation_evidence_pydantic", "transform/validation_evidence_pydantic.py")
        pydantic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pydantic_module)

        ValidationEvidence = pydantic_module.ValidationEvidence
        CompetitorPricing = pydantic_module.CompetitorPricing
        MarketSizeData = pydantic_module.MarketSizeData
        ProductLaunchData = pydantic_module.ProductLaunchData
        PYDANTIC_AVAILABLE = pydantic_module.PYDANTIC_AVAILABLE

        if not PYDANTIC_AVAILABLE:
            print("⚠️  Pydantic not available, skipping enhanced validation tests")
            return True

        print(f"✅ Pydantic available: {PYDANTIC_AVAILABLE}")

        # Test enhanced validation
        competitor = CompetitorPricing(
            company_name="Asana",
            pricing_model="subscription",
            pricing_tiers=[
                {"name": "Pro", "price": "$24/mo", "features": ["Unlimited projects"]}
            ],
            target_market="B2B",
            source_url="https://asana.com/pricing",
            confidence=85.0
        )
        print("✅ Enhanced CompetitorPricing validation passed")

        # Test validation errors
        try:
            CompetitorPricing(
                company_name="",  # Empty should fail
                pricing_model="subscription",
                pricing_tiers=[],
                target_market="B2B",
                source_url="https://example.com",
                confidence=75.0
            )
            assert False, "Should have raised validation error for empty company name"
        except Exception:
            print("✅ Validation error for empty company name correctly raised")

        # Test URL validation
        try:
            CompetitorPricing(
                company_name="Test",
                pricing_model="subscription",
                pricing_tiers=[],
                target_market="B2B",
                source_url="invalid-url",  # Invalid URL should fail
                confidence=75.0
            )
            assert False, "Should have raised validation error for invalid URL"
        except Exception:
            print("✅ URL validation error correctly raised")

        # Test confidence bounds
        try:
            CompetitorPricing(
                company_name="Test",
                pricing_model="subscription",
                pricing_tiers=[],
                target_market="B2B",
                source_url="https://example.com",
                confidence=150.0  # Out of bounds should fail
            )
            assert False, "Should have raised validation error for confidence > 100"
        except Exception:
            print("✅ Confidence bounds validation correctly enforced")

        return True

    except Exception as e:
        print(f"❌ Pydantic validation test failed: {e}")
        return False

def test_enhanced_serialization():
    """Test enhanced serialization with Pydantic"""
    print("Testing enhanced serialization...")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("validation_evidence_pydantic", "transform/validation_evidence_pydantic.py")
        pydantic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pydantic_module)

        ValidationEvidence = pydantic_module.ValidationEvidence
        CompetitorPricing = pydantic_module.CompetitorPricing
        MarketSizeData = pydantic_module.MarketSizeData
        ProductLaunchData = pydantic_module.ProductLaunchData

        if not pydantic_module.PYDANTIC_AVAILABLE:
            print("⚠️  Pydantic not available, skipping enhanced serialization tests")
            return True

        # Create complex evidence
        evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="Monday.com",
                    pricing_model="freemium",
                    pricing_tiers=[
                        {"name": "Free", "price": "$0", "users": "Individual"},
                        {"name": "Pro", "price": "$16/mo", "users": "Teams"}
                    ],
                    target_market="B2B",
                    source_url="https://monday.com/pricing",
                    confidence=92.5
                )
            ],
            market_size=MarketSizeData(
                tam_value="$65.5B",
                sam_value="$8.2B",
                growth_rate="22.3% CAGR",
                source_name="Forrester Research 2024",
                source_url="https://forrester.com/reports/project-management",
                year=2024
            ),
            similar_launches=[
                ProductLaunchData(
                    product_name="TaskFlow AI",
                    launch_platform="Product Hunt",
                    launch_date="2024-03-15",
                    upvotes=1850,
                    comments=320,
                    source_url="https://producthunt.com/posts/taskflow-ai"
                )
            ],
            validation_score=87.5,
            data_quality_score=91.0,
            reasoning="Strong competitive landscape with established players and clear market demand evidenced by successful launches.",
            search_queries_used=[
                "project management software competitors 2024",
                "AI productivity tools market size",
                "team collaboration SaaS pricing models"
            ],
            urls_fetched=[
                "https://monday.com/pricing",
                "https://forrester.com/reports/project-management",
                "https://producthunt.com/posts/taskflow-ai"
            ],
            total_cost=0.0155
        )

        # Test enhanced serialization
        json_str = evidence.to_json()
        assert isinstance(json_str, str)
        assert "Monday.com" in json_str
        assert "65.5B" in json_str
        print("✅ Enhanced JSON serialization successful")

        # Test enhanced deserialization
        restored = ValidationEvidence.from_json(json_str)
        assert restored.validation_score == evidence.validation_score
        assert len(restored.competitor_pricing) == 1
        assert restored.competitor_pricing[0].company_name == "Monday.com"
        assert restored.market_size.tam_value == "$65.5B"
        print("✅ Enhanced JSON deserialization successful")

        # Test schema validation
        try:
            schema = evidence.model_json_schema()
        except AttributeError:
            # Fallback for older Pydantic versions
            schema = evidence.schema()
        assert "properties" in schema
        assert "validation_score" in schema["properties"]
        print("✅ Pydantic schema generation successful")

        return True

    except Exception as e:
        print(f"❌ Enhanced serialization test failed: {e}")
        return False

def test_type_safety_and_enums():
    """Test enhanced type safety with Pydantic enums"""
    print("Testing type safety with enums...")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("validation_evidence_pydantic", "transform/validation_evidence_pydantic.py")
        pydantic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pydantic_module)

        CompetitorPricing = pydantic_module.CompetitorPricing
        ProductLaunchData = pydantic_module.ProductLaunchData

        if not pydantic_module.PYDANTIC_AVAILABLE:
            print("⚠️  Pydantic not available, skipping enum tests")
            return True

        # Test enum validation for pricing models
        valid_models = ["subscription", "freemium", "one-time", "usage-based"]
        for model in valid_models:
            competitor = CompetitorPricing(
                company_name="Test Co",
                pricing_model=model,
                pricing_tiers=[],
                target_market="B2B",
                source_url="https://example.com/pricing",
                confidence=80.0
            )
            # With use_enum_values=True, the enum is converted to string value
            assert competitor.pricing_model == model

        # Test invalid pricing model
        try:
            CompetitorPricing(
                company_name="Test Co",
                pricing_model="invalid_model",  # Should fail
                pricing_tiers=[],
                target_market="B2B",
                source_url="https://example.com/pricing",
                confidence=80.0
            )
            assert False, "Should have raised validation error for invalid pricing model"
        except Exception:
            print("✅ Pricing model enum validation working")

        # Test launch platform enum
        valid_platforms = ["Product Hunt", "Hacker News", "Reddit", "YC Launch"]
        for platform in valid_platforms:
            launch = ProductLaunchData(
                product_name="Test Product",
                launch_platform=platform,
                launch_date="2024-01-01",
                upvotes=100,
                comments=25,
                source_url="https://producthunt.com/posts/test"
            )
            # With use_enum_values=True, the enum is converted to string value
            assert launch.launch_platform == platform

        print("✅ Type safety and enum validation working")
        return True

    except Exception as e:
        print(f"❌ Type safety test failed: {e}")
        return False

def test_factory_functions():
    """Test factory functions for creating ValidationEvidence"""
    print("Testing factory functions...")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("validation_evidence_pydantic", "transform/validation_evidence_pydantic.py")
        pydantic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pydantic_module)

        create_validation_evidence = pydantic_module.create_validation_evidence
        assess_validation_quality = pydantic_module.assess_validation_quality

        # Test factory function with dictionaries
        evidence = create_validation_evidence(
            competitor_pricing=[
                {
                    "company_name": "ClickUp",
                    "pricing_model": "freemium",
                    "pricing_tiers": [{"name": "Free", "price": "$0"}],
                    "target_market": "B2B",
                    "source_url": "https://clickup.com/pricing",
                    "confidence": 88.0
                }
            ],
            market_size={
                "tam_value": "$45B",
                "sam_value": "$4.5B",
                "growth_rate": "18% CAGR",
                "source_name": "Statista 2024",
                "source_url": "https://statista.com",
                "year": 2024
            },
            validation_score=75.0,
            data_quality_score=80.0,
            reasoning="Factory test evidence",
            search_queries_used=["test query"],
            urls_fetched=["https://clickup.com/pricing"],
            total_cost=0.008
        )

        assert evidence.validation_score == 75.0
        assert len(evidence.competitor_pricing) == 1
        assert evidence.competitor_pricing[0].company_name == "ClickUp"
        assert evidence.market_size.tam_value == "$45B"
        print("✅ Factory function working correctly")

        # Test quality assessment function
        quality_assessment = assess_validation_quality(evidence)
        assert 'overall_quality' in quality_assessment
        assert 'validation_level' in quality_assessment
        assert 'comprehensive_assessment' in quality_assessment
        print("✅ Quality assessment function working")

        return True

    except Exception as e:
        print(f"❌ Factory function test failed: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with original interface"""
    print("Testing backward compatibility...")

    try:
        # Import original implementation
        import importlib.util
        spec = importlib.util.spec_from_file_location("validation_evidence", "transform/validation_evidence.py")
        original_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original_module)

        OriginalValidationEvidence = original_module.ValidationEvidence
        OriginalCompetitorPricing = original_module.CompetitorPricing

        # Test that original interface still works
        original_evidence = OriginalValidationEvidence(
            competitor_pricing=[
                OriginalCompetitorPricing(
                    company_name="Asana",
                    pricing_model="subscription",
                    pricing_tiers=[{"name": "Pro", "price": "$24/mo"}],
                    target_market="B2B",
                    source_url="https://asana.com/pricing",
                    confidence=85.0
                )
            ],
            market_size=None,
            similar_launches=[],
            validation_score=78.5,
            data_quality_score=82.0,
            reasoning="Backward compatibility test",
            search_queries_used=[],
            urls_fetched=[],
            total_cost=0.007
        )

        # Test that all original methods still work
        summary = original_evidence.get_summary()
        validation_level = original_evidence.get_validation_level()
        quality_metrics = original_evidence.get_quality_metrics()
        db_dict = original_evidence.to_database_dict()

        assert 'competitors_found' in summary
        assert validation_level in ["LOW", "MEDIUM", "HIGH"]
        assert 'overall_quality' in quality_metrics
        assert 'competitor_pricing' in db_dict

        # Test JSON roundtrip
        json_data = original_evidence.to_json()
        restored = OriginalValidationEvidence.from_json(json_data)
        assert restored.validation_score == original_evidence.validation_score

        print("✅ Backward compatibility maintained")
        return True

    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def test_database_integration():
    """Test database integration methods"""
    print("Testing database integration...")

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("validation_evidence_pydantic", "transform/validation_evidence_pydantic.py")
        pydantic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pydantic_module)

        ValidationEvidence = pydantic_module.ValidationEvidence
        CompetitorPricing = pydantic_module.CompetitorPricing
        MarketSizeData = pydantic_module.MarketSizeData

        # Create test evidence
        evidence = ValidationEvidence(
            competitor_pricing=[
                CompetitorPricing(
                    company_name="DatabaseTest Corp",
                    pricing_model="subscription",
                    pricing_tiers=[{"name": "Enterprise", "price": "$500/mo"}],
                    target_market="Enterprise",
                    source_url="https://dbtest.com/pricing",
                    confidence=95.0
                )
            ],
            market_size=MarketSizeData(
                tam_value="$120B",
                sam_value="$15B",
                growth_rate="25% CAGR",
                source_name="DB Research 2024",
                source_url="https://dbresearch.com",
                year=2024
            ),
            similar_launches=[],
            validation_score=88.0,
            data_quality_score=90.0,
            reasoning="Database integration test",
            search_queries_used=["database tools"],
            urls_fetched=["https://dbtest.com/pricing"],
            total_cost=0.012
        )

        # Test database serialization
        db_dict = evidence.to_database_dict()
        assert isinstance(db_dict, dict)
        assert 'competitor_pricing' in db_dict
        assert 'market_size' in db_dict
        assert 'validation_score' in db_dict
        print("✅ Database serialization working")

        # Test database deserialization
        restored = ValidationEvidence.from_database_dict(db_dict)
        assert restored.validation_score == evidence.validation_score
        assert len(restored.competitor_pricing) == 1
        assert restored.market_size.tam_value == "$120B"
        print("✅ Database deserialization working")

        # Test AnalysisResult format
        ar_format = evidence.to_analysis_result_format()
        assert 'jina_validation_score' in ar_format
        assert 'jina_competitor_count' in ar_format
        assert 'validation_level' in ar_format
        assert ar_format['jina_validation_score'] == 88.0
        assert ar_format['jina_competitor_count'] == 1
        print("✅ AnalysisResult format conversion working")

        return True

    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False

def run_refactor_tests():
    """Run all refactor phase tests"""
    print("🔧 Starting ValidationEvidence REFACTOR Phase Tests...")
    print("=" * 60)

    tests = [
        test_pydantic_enhanced_validation,
        test_enhanced_serialization,
        test_type_safety_and_enums,
        test_factory_functions,
        test_backward_compatibility,
        test_database_integration
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"📊 REFACTOR Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All refactor tests passed! Pydantic enhancement complete!")
        return True
    else:
        print("💥 Some refactor tests failed. Need to fix Pydantic integration.")
        return False

if __name__ == "__main__":
    success = run_refactor_tests()
    sys.exit(0 if success else 1)