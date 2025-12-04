#!/usr/bin/env python3
"""
Integration Tests for ValidationEvidence with Pipeline v3 Components

This tests the complete integration of ValidationEvidence data structures with:
- MarketResearchAgent
- AnalysisResultWithJina
- Enhanced Pydantic models
- Real workflow scenarios

Phase 3 Jina Integration - Integration Testing
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

def test_market_research_agent_integration():
    """Test MarketResearchAgent integration with ValidationEvidence"""
    print("Testing MarketResearchAgent integration...")

    try:
        # Import MarketResearchAgent directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("market_research_agent", "transform/market_research_agent.py")
        agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_module)

        MarketResearchAgent = agent_module.MarketResearchAgent

        # Create agent
        agent = MarketResearchAgent(
            model="anthropic/claude-haiku-4.5",
            validation_threshold=70.0,
            max_competitors=3,
            max_launches=2
        )

        # Test validation trigger
        assert agent.should_validate_opportunity(80.0) == True
        assert agent.should_validate_opportunity(60.0) == False
        print("✅ Validation threshold working")

        # Test async run (using asyncio.run for sync test)
        input_data = {
            "app_concept": "AI-powered project management tool",
            "target_market": "B2B software teams",
            "problem_description": "Teams struggle with task coordination and deadline tracking"
        }

        # Run the agent
        async def test_agent_run():
            result = await agent.run(input_data)
            return result

        result = asyncio.run(test_agent_run())

        # Validate result structure
        assert "competitor_pricing" in result
        assert "validation_score" in result
        assert "data_quality_score" in result
        assert "reasoning" in result
        assert "evidence_urls" in result
        assert "jina_cost" in result

        # Validate data quality
        assert result["validation_score"] >= 0
        assert result["validation_score"] <= 100
        assert result["data_quality_score"] >= 0
        assert result["data_quality_score"] <= 100
        assert len(result["reasoning"]) > 0

        # Validate cost tracking
        assert result["jina_cost"] >= 0
        cost_summary = agent.get_cost_summary()
        assert cost_summary["validation_count"] == 1
        assert cost_summary["total_cost"] > 0

        print("✅ MarketResearchAgent integration successful")
        return True

    except Exception as e:
        print(f"❌ MarketResearchAgent integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analysis_result_enhanced_integration():
    """Test AnalysisResultWithJina integration"""
    print("Testing AnalysisResultWithJina integration...")

    try:
        # Import enhanced models
        import importlib.util
        spec = importlib.util.spec_from_file_location("analysis_enhanced", "models/analysis_enhanced.py")
        enhanced_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(enhanced_module)

        AnalysisResultWithJina = enhanced_module.AnalysisResultWithJina
        create_enhanced_result_from_agno = enhanced_module.create_enhanced_result_from_agno

        # Create mock ValidationEvidence data
        validation_evidence = {
            "competitor_pricing": [
                {
                    "company": "TestCorp",
                    "pricing_model": "subscription",
                    "tiers": [{"name": "Pro", "price": "$29/mo"}],
                    "target": "B2B",
                    "url": "https://testcorp.com/pricing",
                    "confidence": 85.0
                }
            ],
            "market_size": {
                "tam_value": "$25B",
                "growth_rate": "15% CAGR",
                "source_name": "Test Research"
            },
            "similar_launches": [
                {
                    "product": "TestProduct",
                    "platform": "Product Hunt",
                    "upvotes": 500,
                    "url": "https://producthunt.com/posts/testproduct"
                }
            ],
            "validation_score": 78.0,
            "data_quality_score": 82.0,
            "reasoning": "Strong competitive landscape with established pricing",
            "evidence_urls": ["https://testcorp.com/pricing"],
            "total_cost": 0.008
        }

        # Create mock Agno result
        agno_result = {
            "submission_id": "test_123",
            "final_score": 75.5,
            "confidence_score": 80.0,
            "trust_level": "HIGH",
            "app_title": "Test Application",
            "app_concept": "AI-powered solution for testing",
            "problem_statement": "Testing is hard and time-consuming",
            "core_functions": ["Automated testing", "Test generation"],
            "target_audience": "Software development teams",
            "market_demand": 70.0,
            "pain_intensity": 65.0,
            "monetization_potential": 75.0,
            "competition_level": 60.0,
            "technical_feasibility": 85.0,
            "content_quality_score": 88.0
        }

        # Create enhanced result
        enhanced_result = create_enhanced_result_from_agno(
            agno_result=agno_result,
            validation_evidence=validation_evidence
        )

        # Validate enhanced fields
        assert enhanced_result.jina_validation_score == 78.0
        assert enhanced_result.jina_data_quality_score == 82.0
        assert enhanced_result.jina_competitor_count == 1
        assert enhanced_result.jina_market_size_tam == "$25B"
        assert enhanced_result.jina_market_size_growth == "15% CAGR"
        assert len(enhanced_result.jina_evidence_urls) == 1
        assert enhanced_result.jina_api_cost_usd == 0.008

        # Test helper methods
        assert enhanced_result.has_jina_validation() == True
        quality_rating = enhanced_result.get_validation_quality_rating()
        assert quality_rating in ["HIGH_QUALITY", "MEDIUM_QUALITY", "LOW_QUALITY"]

        # Test summary
        summary = enhanced_result.get_enhanced_summary()
        assert "jina_research" in summary
        assert summary["jina_research"]["jina_validation_score"] == 78.0

        # Test market insights
        insights = enhanced_result.get_market_insights()
        assert "competitors" in insights
        assert "market_size" in insights
        assert "product_launches" in insights

        print("✅ AnalysisResultWithJina integration successful")
        return True

    except Exception as e:
        print(f"❌ AnalysisResultWithJina integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation_evidence_workflow():
    """Test complete ValidationEvidence workflow"""
    print("Testing complete ValidationEvidence workflow...")

    try:
        # Import ValidationEvidence
        import importlib.util
        spec = importlib.util.spec_from_file_location("validation_evidence_pydantic", "transform/validation_evidence_pydantic.py")
        pydantic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pydantic_module)

        ValidationEvidence = pydantic_module.ValidationEvidence
        create_validation_evidence = pydantic_module.create_validation_evidence

        # Create comprehensive validation evidence
        evidence = create_validation_evidence(
            competitor_pricing=[
                {
                    "company_name": "Asana",
                    "pricing_model": "subscription",
                    "pricing_tiers": [
                        {"name": "Basic", "price": "$10/mo", "users": "15"},
                        {"name": "Premium", "price": "$24.99/mo", "users": "Unlimited"}
                    ],
                    "target_market": "B2B",
                    "source_url": "https://asana.com/pricing",
                    "confidence": 92.0
                },
                {
                    "company_name": "Monday.com",
                    "pricing_model": "freemium",
                    "pricing_tiers": [
                        {"name": "Free", "price": "$0", "users": "3"},
                        {"name": "Pro", "price": "$8/mo", "users": "Unlimited"}
                    ],
                    "target_market": "B2B",
                    "source_url": "https://monday.com/pricing",
                    "confidence": 88.0
                }
            ],
            market_size={
                "tam_value": "$65.5B",
                "sam_value": "$8.2B",
                "growth_rate": "22.3% CAGR",
                "source_name": "Forrester Research 2024",
                "source_url": "https://forrester.com/reports/project-management",
                "year": 2024
            },
            similar_launches=[
                {
                    "product_name": "TaskFlow AI",
                    "launch_platform": "Product Hunt",
                    "launch_date": "2024-03-15",
                    "upvotes": 1850,
                    "comments": 320,
                    "source_url": "https://producthunt.com/posts/taskflow-ai"
                },
                {
                    "product_name": "SyncMaster",
                    "launch_platform": "Product Hunt",
                    "launch_date": "2024-02-01",
                    "upvotes": 920,
                    "comments": 150,
                    "source_url": "https://producthunt.com/posts/syncmaster"
                }
            ],
            validation_score=85.5,
            data_quality_score=89.0,
            reasoning="Strong competitive landscape with established players showing clear market demand. Multiple competitors with proven business models and successful product launches indicate significant market opportunity.",
            search_queries_used=[
                "project management software competitors 2024",
                "AI productivity tools market size",
                "team collaboration SaaS pricing models"
            ],
            urls_fetched=[
                "https://asana.com/pricing",
                "https://monday.com/pricing",
                "https://forrester.com/reports/project-management",
                "https://producthunt.com/posts/taskflow-ai",
                "https://producthunt.com/posts/syncmaster"
            ],
            total_cost=0.0185
        )

        # Test ValidationEvidence methods
        summary = evidence.get_summary()
        assert summary["competitors_found"] == 2
        assert summary["market_data_available"] == True
        assert summary["launches_analyzed"] == 2
        assert summary["total_sources"] == 5

        validation_level = evidence.get_validation_level()
        assert validation_level.value in ["HIGH", "MEDIUM", "LOW"]
        # Score 85.5 should be HIGH
        assert validation_level.value == "HIGH"

        # Test database compatibility
        db_dict = evidence.to_database_dict()
        assert "competitor_pricing" in db_dict
        assert "market_size" in db_dict
        assert "validation_score" in db_dict

        restored = ValidationEvidence.from_database_dict(db_dict)
        assert restored.validation_score == evidence.validation_score

        # Test AnalysisResult format conversion
        ar_format = evidence.to_analysis_result_format()
        assert "jina_validation_score" in ar_format
        assert "jina_competitor_count" in ar_format
        assert "validation_level" in ar_format

        # Test cost analysis
        cost_analysis = evidence.get_cost_analysis()
        assert cost_analysis["total_cost"] == 0.0185
        assert cost_analysis["cost_per_competitor"] == 0.0185 / 2
        assert cost_analysis["cost_per_source"] == 0.0185 / 5

        print("✅ ValidationEvidence workflow successful")
        return True

    except Exception as e:
        print(f"❌ ValidationEvidence workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_end_to_end_integration():
    """Test end-to-end integration from Reddit submission to enhanced result"""
    print("Testing end-to-end integration...")

    try:
        # Import components
        import importlib.util

        # MarketResearchAgent
        agent_spec = importlib.util.spec_from_file_location("market_research_agent", "transform/market_research_agent.py")
        agent_module = importlib.util.module_from_spec(agent_spec)
        agent_spec.loader.exec_module(agent_module)
        MarketResearchAgent = agent_module.MarketResearchAgent

        # Enhanced AnalysisResult
        enhanced_spec = importlib.util.spec_from_file_location("analysis_enhanced", "models/analysis_enhanced.py")
        enhanced_module = importlib.util.module_from_spec(enhanced_spec)
        enhanced_module.spec.loader.exec_module(enhanced_module)
        AnalysisResultWithJina = enhanced_module.AnalysisResultWithJina

        # Mock Reddit submission data
        reddit_submission = {
            "submission_id": "t3_abc123",
            "title": "Looking for better project management solution",
            "text": "Our team of 15 developers is struggling with task management across multiple projects. We need something that can handle dependencies, deadlines, and resource allocation automatically.",
            "subreddit": "programming",
            "author": "dev_team_lead",
            "score": 450,
            "num_comments": 87
        }

        # Mock Agno analyzer result
        agno_result = {
            "submission_id": reddit_submission["submission_id"],
            "final_score": 82.5,
            "confidence_score": 88.0,
            "trust_level": "HIGH",
            "app_title": "Intelligent Task Management Platform",
            "app_concept": "AI-powered project management tool that automates task allocation, tracks dependencies, and predicts timeline risks",
            "problem_statement": "Development teams struggle with task coordination, dependency management, and deadline tracking across multiple projects",
            "core_functions": ["AI Task Assignment", "Dependency Tracking", "Risk Prediction"],
            "target_audience": "Software development teams and project managers",
            "market_demand": 85.0,
            "pain_intensity": 78.0,
            "monetization_potential": 82.0,
            "competition_level": 65.0,
            "technical_feasibility": 90.0,
            "content_quality_score": 92.0
        }

        # Step 1: Check if validation should be triggered
        agent = MarketResearchAgent(validation_threshold=70.0)
        assert agent.should_validate_opportunity(agno_result["final_score"]) == True

        # Step 2: Run market research
        async def run_research():
            market_input = {
                "app_concept": agno_result["app_concept"],
                "target_market": agno_result["target_audience"],
                "problem_description": agno_result["problem_statement"]
            }
            return await agent.run(market_input)

        validation_result = asyncio.run(run_research())

        # Step 3: Create enhanced AnalysisResult
        enhanced_result = AnalysisResultWithJina.from_base_analysis_result(
            base_result=enhanced_module.AnalysisResult(
                submission_id=agno_result["submission_id"],
                app_idea=enhanced_module.AppIdea(
                    title=agno_result["app_title"],
                    app_concept=agno_result["app_concept"],
                    problem_statement=agno_result["problem_statement"],
                    core_functions=agno_result["core_functions"],
                    target_audience=agno_result["target_audience"]
                ),
                market_metrics=enhanced_module.MarketMetrics(
                    market_demand=agno_result["market_demand"],
                    pain_intensity=agno_result["pain_intensity"],
                    monetization_potential=agno_result["monetization_potential"],
                    competition_level=agno_result["competition_level"],
                    technical_feasibility=agno_result["technical_feasibility"]
                ),
                final_score=agno_result["final_score"],
                content_quality_score=agno_result["content_quality_score"],
                confidence_score=agno_result["confidence_score"],
                trust_level=agno_result["trust_level"],
                is_spam=False,
                spam_indicators=[]
            ),
            validation_evidence=validation_result
        )

        # Step 4: Validate final result
        assert enhanced_result.jina_validation_score == validation_result["validation_score"]
        assert enhanced_result.has_jina_validation() == True
        assert enhanced_result.get_validation_quality_rating() in ["HIGH_QUALITY", "MEDIUM_QUALITY", "LOW_QUALITY"]

        # Step 5: Test comprehensive summary
        summary = enhanced_result.get_enhanced_summary()
        assert "jina_research" in summary
        assert summary["jina_research"]["jina_competitor_count"] >= 0

        print("✅ End-to-end integration successful")
        return True

    except Exception as e:
        print(f"❌ End-to-end integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🔗 Starting ValidationEvidence Integration Tests...")
    print("=" * 60)

    tests = [
        test_validation_evidence_workflow,
        test_market_research_agent_integration,
        test_analysis_result_enhanced_integration,
        test_end_to_end_integration
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
    print(f"📊 Integration Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All integration tests passed! Phase 3 Jina Integration complete!")
        return True
    else:
        print("💥 Some integration tests failed. Need to fix integration issues.")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)